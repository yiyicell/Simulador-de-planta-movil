"""
Lógica de registro de usuarios.

Pasos que implementa:
  1. Validar que no haya campos vacíos
  2. Verificar si el correo ya existe en la base de datos
  3. Encriptar la contraseña con bcrypt
  4. Guardar el usuario en la base de datos
  5. Retornar respuesta de éxito o error

Cuando se integre FastAPI, la función `registrar_usuario` se llama
directamente desde el endpoint POST /auth/register.
"""

import re
import bcrypt
import psycopg2

try:
    from backend.database import get_connection, init_db
    from backend.auth.models import UsuarioRegistro, UsuarioRespuesta
except ModuleNotFoundError:
    from database import get_connection, init_db
    from auth.models import UsuarioRegistro, UsuarioRespuesta


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

def _validar_campos(datos: UsuarioRegistro) -> None:
    """Lanza ValueError si algún campo está vacío o el correo es inválido."""
    if not datos.nombre.strip():
        raise ValueError("El nombre no puede estar vacío.")
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

    if len(datos.password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")


def _correo_existe(correo: str, conn) -> bool:
    """Retorna True si el correo ya está registrado en la base de datos."""
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM \"user\" WHERE email = %s", (correo.strip().lower(),))
    return cursor.fetchone() is not None


def _encriptar_password(password: str) -> str:
    """Genera el hash bcrypt de la contraseña. El salt se genera automáticamente."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


# ---------------------------------------------------------------------------
# Función principal (punto de entrada del módulo)
# ---------------------------------------------------------------------------

def registrar_usuario(datos: UsuarioRegistro) -> dict:
    """
    Registra un nuevo usuario en la base de datos.

    Parámetros:
        datos: UsuarioRegistro con nombre, correo y password.

    Retorna:
        dict con:
          - "exito" (bool)
          - "mensaje" (str)
          - "usuario" (UsuarioRespuesta | None)

    Ejemplo de uso:
        from auth.register import registrar_usuario
        from auth.models import UsuarioRegistro

        datos = UsuarioRegistro(nombre="Ana", correo="ana@mail.com", password="segura123")
        resultado = registrar_usuario(datos)
    """
    # Paso 1: Validar campos
    try:
        _validar_campos(datos)
    except ValueError as e:
        return {"exito": False, "mensaje": str(e), "usuario": None}

    # Conectar a la BD (y crearla si no existe)
    init_db()
    conn = get_connection()

    try:
        # Paso 2: Verificar si el correo ya existe
        if _correo_existe(datos.correo, conn):
            return {
                "exito": False,
                "mensaje": "El correo ya está registrado.",
                "usuario": None,
            }

        # Paso 3: Encriptar contraseña
        password_hash = _encriptar_password(datos.password)

        # Paso 4: Guardar en base de datos
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO "user" (name, email, hashed_password, online, rol_admin, creation_date)
            VALUES (%s, %s, %s, FALSE, FALSE, CURRENT_DATE)
            RETURNING user_id, name, email, online, rol_admin, creation_date
            """,
            (datos.nombre.strip(), datos.correo.strip().lower(), password_hash),
        )
        conn.commit()

        fila = cursor.fetchone()

        usuario_respuesta = UsuarioRespuesta(
            id=fila[0],
            nombre=fila[1],
            correo=fila[2],
            online=fila[3],
            rol_admin=fila[4],
            creado=str(fila[5]),
        )

        # Paso 5: Respuesta de éxito
        return {
            "exito": True,
            "mensaje": "Usuario registrado exitosamente.",
            "usuario": usuario_respuesta,
        }

    except psycopg2.Error as e:
        conn.rollback()
        return {
            "exito": False,
            "mensaje": f"Error en la base de datos: {e}",
            "usuario": None,
        }
    finally:
        conn.close()
