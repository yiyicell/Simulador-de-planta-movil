"""
Lógica de cierre de sesión de usuarios.

Marca el campo `online = FALSE` en la tabla de usuarios.
"""

import psycopg2

try:
    from backend.database import get_connection
except ModuleNotFoundError:
    from database import get_connection


def cerrar_sesion(user_id: int) -> dict:
    """
    Marca al usuario como desconectado (online = FALSE).

    Parámetros:
        user_id: ID del usuario que cierra sesión.

    Retorna:
        dict con:
          - "exito" (bool)
          - "mensaje" (str)
    """
    if not isinstance(user_id, int) or user_id <= 0:
        return {"exito": False, "mensaje": "ID de usuario inválido."}

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE \"user\" SET online = FALSE WHERE user_id = %s RETURNING user_id",
            (user_id,),
        )
        conn.commit()

        if cursor.fetchone() is None:
            return {"exito": False, "mensaje": "Usuario no encontrado."}

        return {"exito": True, "mensaje": "Sesión cerrada correctamente."}

    except psycopg2.Error as e:
        conn.rollback()
        return {"exito": False, "mensaje": f"Error en la base de datos: {e}"}
    finally:
        conn.close()
