"""
Lógica de autenticación de usuarios.

Pasos que implementa:
  1. Validar las credenciales recibidas
  2. Buscar el usuario por correo
  3. Verificar la contraseña contra el hash almacenado
  4. Retornar respuesta de éxito o error
"""

import re
import bcrypt
import psycopg2

try:
    from backend.database import get_connection, init_db
    from backend.auth.models import UsuarioLogin, UsuarioRespuesta
except ModuleNotFoundError:
    from database import get_connection, init_db
    from auth.models import UsuarioLogin, UsuarioRespuesta


def _validar_credenciales(datos: UsuarioLogin) -> None:
    """Lanza ValueError si las credenciales son inválidas."""
    if not datos.correo.strip():
        raise ValueError("El correo no puede estar vacío.")
    if not datos.password.strip():
        raise ValueError("La contraseña no puede estar vacía.")

    correo = datos.correo.strip()
    patron_correo = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(patron_correo, correo):
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
    """Recupera el usuario por correo o None si no existe."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, name, email, hashed_password, online, rol_admin, creation_date FROM \"user\" WHERE email = %s",
        (correo.strip().lower(),),
    )
    return cursor.fetchone()


def _marcar_online(user_id: int, conn) -> None:
    """Establece online=TRUE para el usuario dado."""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE \"user\" SET online = TRUE WHERE user_id = %s",
        (user_id,),
    )
    conn.commit()


def _verificar_password(password: str, password_hash: str) -> bool:
    """Compara una contraseña en texto plano contra el hash almacenado."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def autenticar_usuario(datos: UsuarioLogin) -> dict:
    """
    Valida las credenciales de un usuario registrado.

    Retorna:
        dict con:
          - "exito" (bool)
          - "mensaje" (str)
          - "usuario" (UsuarioRespuesta | None)
    """
    try:
        _validar_credenciales(datos)
    except ValueError as e:
        return {"exito": False, "mensaje": str(e), "usuario": None}

    init_db()
    conn = get_connection()

    try:
        fila = _obtener_usuario_por_correo(datos.correo, conn)

        # fila: (id, nombre, correo, password, online, rol_admin, creado)
        if fila is None or not _verificar_password(datos.password, fila[3]):
            return {
                "exito": False,
                "mensaje": "Correo o contraseña incorrectos.",
                "usuario": None,
            }

        _marcar_online(fila[0], conn)

        usuario_respuesta = UsuarioRespuesta(
            id=fila[0],
            nombre=fila[1],
            correo=fila[2],
            online=True,
            rol_admin=fila[5],
            creado=str(fila[6]),
        )

        return {
            "exito": True,
            "mensaje": "Inicio de sesión exitoso.",
            "usuario": usuario_respuesta,
        }
    except psycopg2.Error as e:
        return {
            "exito": False,
            "mensaje": f"Error en la base de datos: {e}",
            "usuario": None,
        }
    finally:
        conn.close()