"""
Lógica de recuperación de contraseña en dos pasos:

  Paso 1 — solicitar_recuperacion(correo)
    · Verifica que el correo exista en la base de datos.
    · Genera un token seguro de 64 caracteres hex (32 bytes).
    · Lo almacena en la tabla `token` con 10 min de vigencia
    (expiration = NOW + 10 min, available = TRUE, active = TRUE).
    · Envía el token al correo del usuario vía SMTP.

  Paso 2 — restablecer_password(correo, token, nueva_password, confirmar_password)
    · Verifica que el token exista, active = TRUE, available = TRUE
      y expiration > NOW.
    · Comprueba que las dos contraseñas sean iguales y válidas.
    · Actualiza el hash en la tabla `user`.
    · Marca el token como active = FALSE, available = FALSE.
"""

import re
import secrets
import smtplib
import ssl
import os
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import bcrypt
import psycopg2

try:
    from backend.database import get_connection
except ModuleNotFoundError:
    from database import get_connection

# ---------------------------------------------------------------------------
# Configuración SMTP (leída desde variables de entorno)
# ---------------------------------------------------------------------------

SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER     = os.getenv("SMTP_USER", "")          # correo remitente
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")      # contraseña / app-password
SMTP_FROM     = os.getenv("SMTP_FROM", SMTP_USER)   # nombre "De:"

TOKEN_EXPIRY_MINUTES = 10


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

def _validar_correo(correo: str) -> None:
    """Lanza ValueError si el correo tiene formato inválido."""
    correo = correo.strip()
    patron = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(patron, correo):
        raise ValueError("El formato del correo no es válido.")
    local, dominio = correo.split("@", 1)
    if (
        ".." in correo
        or local.startswith(".")
        or local.endswith(".")
        or dominio.startswith(".")
        or dominio.endswith(".")
    ):
        raise ValueError("El formato del correo no es válido.")


def _obtener_usuario_por_correo(correo: str, conn) -> tuple | None:
    """Retorna (user_id, name, email) o None."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT user_id, name, email FROM "user" WHERE email = %s',
        (correo.strip().lower(),),
    )
    return cursor.fetchone()


def _guardar_token(user_id: int, token: str, conn) -> None:
    """Inserta el token en la tabla token con 10 min de vigencia."""
    expiration = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO token (fk_user_id, token, expiration, available, active)
        VALUES (%s, %s, %s, TRUE, TRUE)
        """,
        (user_id, token, expiration),
    )
    conn.commit()


def _enviar_correo(destino: str, nombre: str, token: str) -> None:
    """Envía el token de recuperación al correo del usuario."""
    if not SMTP_USER or not SMTP_PASSWORD:
        # En entornos sin SMTP configurado, se registra el token en consola
        print(f"[PASSWORD RESET] Token para {destino}: {token}")
        return

    asunto = "Recuperación de contraseña — Plantastic"
    cuerpo_html = f"""
    <html><body>
    <p>Hola <strong>{nombre}</strong>,</p>
    <p>Recibiste este correo porque solicitaste recuperar tu contraseña en <b>Plantastic</b>.</p>
    <p>Tu token de recuperación (válido por {TOKEN_EXPIRY_MINUTES} minutos) es:</p>
    <h2 style="letter-spacing:4px; font-family:monospace;">{token}</h2>
    <p>Ingresa tu correo y este token en la aplicación para establecer una nueva contraseña.</p>
    <p>Si no solicitaste esto, ignora este mensaje.</p>
    </body></html>
    """
    cuerpo_texto = (
        f"Hola {nombre},\n\n"
        f"Tu token de recuperación (válido {TOKEN_EXPIRY_MINUTES} min): {token}\n\n"
        "Si no solicitaste esto, ignora este mensaje."
    )

    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"]    = SMTP_FROM
    mensaje["To"]      = destino
    mensaje.attach(MIMEText(cuerpo_texto, "plain"))
    mensaje.attach(MIMEText(cuerpo_html, "html"))

    contexto = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=contexto) as servidor:
        servidor.login(SMTP_USER, SMTP_PASSWORD)
        servidor.sendmail(SMTP_FROM, destino, mensaje.as_string())


def _obtener_token_valido(correo: str, token: str, conn) -> tuple | None:
    """
    Busca un token válido para el correo dado.
    Un token es válido si: active = TRUE, available = TRUE y expiration > NOW().
    Retorna (id, fk_user_id) o None si no cumple las condiciones.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT prt.token_id, prt.fk_user_id
        FROM token prt
        JOIN "user" u ON u.user_id = prt.fk_user_id
        WHERE u.email    = %s
          AND prt.token  = %s
          AND prt.active    = TRUE
          AND prt.available = TRUE
          AND prt.expiration::timestamptz > NOW()
        ORDER BY prt.expiration DESC
        LIMIT 1
        """,
        (correo.strip().lower(), token.strip()),
    )
    return cursor.fetchone()


def _actualizar_password(user_id: int, nueva_password: str, conn) -> None:
    """Reemplaza el hash de contraseña del usuario."""
    nuevo_hash = bcrypt.hashpw(
        nueva_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE "user" SET hashed_password = %s WHERE user_id = %s',
        (nuevo_hash, user_id),
    )


def _marcar_token_usado(token_id: int, conn) -> None:
    """Desactiva el token: active = FALSE y available = FALSE."""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE token SET active = FALSE, available = FALSE WHERE token_id = %s",
        (token_id,),
    )


# ---------------------------------------------------------------------------
# Funciones públicas
# ---------------------------------------------------------------------------

def solicitar_recuperacion(correo: str) -> dict:
    """
    Paso 1: genera y envía un token de recuperación al correo indicado.

    Retorna:
        dict con "exito" (bool) y "mensaje" (str).
    """
    try:
        _validar_correo(correo)
    except ValueError as e:
        return {"exito": False, "mensaje": str(e)}

    conn = get_connection()
    try:
        fila = _obtener_usuario_por_correo(correo, conn)
        if fila is None:
            # No revelamos si el correo existe o no (seguridad anti-enumeración)
            return {
                "exito": True,
                "mensaje": (
                    "Si el correo está registrado, recibirás un mensaje "
                    "con el token de recuperación."
                ),
            }

        user_id, nombre, email = fila
        import string
        # Elimina cualquier token anterior de este usuario
        cursor = conn.cursor()
        cursor.execute('DELETE FROM token WHERE fk_user_id = %s', (user_id,))
        conn.commit()  # Confirma la eliminación antes de insertar el nuevo token
        token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(6))  # 6 caracteres alfanuméricos
        _guardar_token(user_id, token, conn)

        try:
            _enviar_correo(email, nombre, token)
        except Exception as mail_err:
            # El token ya está guardado; el fallo de correo no deshace la operación
            print(f"[PASSWORD RESET] Error al enviar correo a {email}: {mail_err}")
            return {
                "exito": False,
                "mensaje": "No se pudo enviar el correo. Verifica la configuración SMTP.",
            }

        return {
            "exito": True,
            "mensaje": (
                "Si el correo está registrado, recibirás un mensaje "
                "con el token de recuperación."
            ),
        }

    except psycopg2.Error as e:
        conn.rollback()
        return {"exito": False, "mensaje": f"Error en la base de datos: {e}"}
    finally:
        conn.close()


def restablecer_password(
    correo: str,
    token: str,
    nueva_password: str,
    confirmar_password: str,
) -> dict:
    """
    Paso 2: valida el token y actualiza la contraseña.

    Retorna:
        dict con "exito" (bool) y "mensaje" (str).
    """
    # Validaciones básicas
    try:
        _validar_correo(correo)
    except ValueError as e:
        return {"exito": False, "mensaje": str(e)}

    if not token.strip():
        return {"exito": False, "mensaje": "El token no puede estar vacío."}
    if not nueva_password or not confirmar_password:
        return {"exito": False, "mensaje": "La contraseña no puede estar vacía."}
    if nueva_password != confirmar_password:
        return {"exito": False, "mensaje": "Las contraseñas no coinciden."}
    if len(nueva_password) < 8:
        return {"exito": False, "mensaje": "La contraseña debe tener al menos 8 caracteres."}

    conn = get_connection()
    try:
        fila = _obtener_token_valido(correo, token, conn)
        if fila is None:
            return {
                "exito": False,
                "mensaje": "Token inválido, expirado o ya utilizado.",
            }

        token_id, user_id = fila
        _actualizar_password(user_id, nueva_password, conn)
        _marcar_token_usado(token_id, conn)
        conn.commit()

        return {"exito": True, "mensaje": "Contraseña actualizada correctamente. Ya puedes iniciar sesión."}

    except psycopg2.Error as e:
        conn.rollback()
        return {"exito": False, "mensaje": f"Error en la base de datos: {e}"}
    finally:
        conn.close()
