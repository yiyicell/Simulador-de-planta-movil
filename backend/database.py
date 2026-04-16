"""
Módulo de conexión y configuración de la base de datos PostgreSQL.
"""

import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

PG_HOST     = os.getenv("PG_HOST", "100.68.116.64")
PG_PORT     = int(os.getenv("PG_PORT", "5432"))
PG_DATABASE = os.getenv("PG_DATABASE", "Plantastic")
PG_USER     = os.getenv("PG_USER", "postgre")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")


def get_connection() -> psycopg2.extensions.connection:
    """Retorna una conexión activa a PostgreSQL."""
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
    )
    conn.autocommit = False
    return conn


def init_db() -> None:
    """Crea las tablas necesarias si no existen."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "user" (
            user_id        SERIAL PRIMARY KEY,
            name           CHARACTER VARYING(50) NOT NULL,
            email          TEXT        NOT NULL UNIQUE,
            hashed_password TEXT       NOT NULL,
            online         BOOLEAN     NOT NULL DEFAULT FALSE,
            rol_admin      BOOLEAN     NOT NULL DEFAULT FALSE,
            creation_date  DATE        NOT NULL DEFAULT CURRENT_DATE
        )
    """)

    conn.commit()
    conn.close()
