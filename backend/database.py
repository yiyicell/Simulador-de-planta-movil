"""
Módulo de conexión y configuración de la base de datos SQLite.
Más adelante se puede migrar a PostgreSQL/MySQL conectado a FastAPI.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "simulador.db")


def get_connection() -> sqlite3.Connection:
    """Retorna una conexión activa a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acceder columnas por nombre
    return conn


def init_db() -> None:
    """Crea las tablas necesarias si no existen."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre   TEXT    NOT NULL,
            correo   TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            creado   DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
