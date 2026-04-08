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
import sqlite3
import bcrypt

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

    patron_correo = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(patron_correo, datos.correo.strip()):
        raise ValueError("El formato del correo no es válido.")

    if len(datos.password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")


def _correo_existe(correo: str, conn: sqlite3.Connection) -> bool:
    """Retorna True si el correo ya está registrado en la base de datos."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE correo = ?", (correo.strip().lower(),))
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
            "INSERT INTO usuarios (nombre, correo, password) VALUES (?, ?, ?)",
            (datos.nombre.strip(), datos.correo.strip().lower(), password_hash),
        )
        conn.commit()

        # Recuperar el usuario recién creado para la respuesta
        cursor.execute(
            "SELECT id, nombre, correo, creado FROM usuarios WHERE id = ?",
            (cursor.lastrowid,),
        )
        fila = cursor.fetchone()

        usuario_respuesta = UsuarioRespuesta(
            id=fila["id"],
            nombre=fila["nombre"],
            correo=fila["correo"],
            creado=fila["creado"],
        )

        # Paso 5: Respuesta de éxito
        return {
            "exito": True,
            "mensaje": "Usuario registrado exitosamente.",
            "usuario": usuario_respuesta,
        }

    except sqlite3.Error as e:
        return {
            "exito": False,
            "mensaje": f"Error en la base de datos: {e}",
            "usuario": None,
        }
    finally:
        conn.close()
