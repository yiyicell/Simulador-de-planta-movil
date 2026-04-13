"""
Lógica de autenticación de usuarios.

Pasos que implementa:
  1. Validar las credenciales recibidas
  2. Buscar el usuario por correo
  3. Verificar la contraseña contra el hash almacenado
  4. Retornar respuesta de éxito o error
"""

import re
import sqlite3
import bcrypt

from database import get_connection, init_db
from auth.models import UsuarioLogin, UsuarioRespuesta


def _validar_credenciales(datos: UsuarioLogin) -> None:
    """Lanza ValueError si las credenciales son inválidas."""
    if not datos.correo.strip():
        raise ValueError("El correo no puede estar vacío.")
    if not datos.password.strip():
        raise ValueError("La contraseña no puede estar vacía.")

    patron_correo = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(patron_correo, datos.correo.strip()):
        raise ValueError("El formato del correo no es válido.")


def _obtener_usuario_por_correo(
    correo: str, conn: sqlite3.Connection
) -> sqlite3.Row | None:
    """Recupera el usuario por correo o None si no existe."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nombre, correo, password, creado FROM usuarios WHERE correo = ?",
        (correo.strip().lower(),),
    )
    return cursor.fetchone()


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

        if fila is None or not _verificar_password(datos.password, fila["password"]):
            return {
                "exito": False,
                "mensaje": "Correo o contraseña incorrectos.",
                "usuario": None,
            }

        usuario_respuesta = UsuarioRespuesta(
            id=fila["id"],
            nombre=fila["nombre"],
            correo=fila["correo"],
            creado=fila["creado"],
        )

        return {
            "exito": True,
            "mensaje": "Inicio de sesión exitoso.",
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