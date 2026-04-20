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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plant (
            id_plant            SERIAL PRIMARY KEY,
            plant_name          CHARACTER VARYING(100) NOT NULL,
            plant_type          CHARACTER VARYING(50),
            water_level         DOUBLE PRECISION DEFAULT 30.0,
            light_level         DOUBLE PRECISION DEFAULT 40.0,
            humidity_level      DOUBLE PRECISION DEFAULT 60.0,
            health              DOUBLE PRECISION DEFAULT 0.0,
            growth_stage        CHARACTER VARYING(50) DEFAULT 'germinacion',
            total_care_actions  INTEGER DEFAULT 0,
            creation_date_plant DATE DEFAULT CURRENT_DATE,
            fk_user_id          INTEGER NOT NULL REFERENCES "user"(user_id),
            is_dead             BOOLEAN DEFAULT FALSE,
            last_decay_at       TIMESTAMP DEFAULT NOW()
        )
    """)

    # Migración segura: agrega columnas nuevas si la tabla ya existía sin ellas
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'plant' AND column_name = 'growth_stage'
            ) THEN
                ALTER TABLE plant ADD COLUMN growth_stage CHARACTER VARYING(50) DEFAULT 'germinacion';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'plant' AND column_name = 'total_care_actions'
            ) THEN
                ALTER TABLE plant ADD COLUMN total_care_actions INTEGER DEFAULT 0;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'plant' AND column_name = 'ventilation_level'
            ) THEN
                ALTER TABLE plant ADD COLUMN ventilation_level DOUBLE PRECISION DEFAULT 50.0;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'plant' AND column_name = 'fk_substrate_type'
            ) THEN
                ALTER TABLE plant ADD COLUMN fk_substrate_type INTEGER;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'plant' AND column_name = 'is_dead'
            ) THEN
                ALTER TABLE plant ADD COLUMN is_dead BOOLEAN DEFAULT FALSE;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'plant' AND column_name = 'last_decay_at'
            ) THEN
                ALTER TABLE plant ADD COLUMN last_decay_at TIMESTAMP DEFAULT NOW();
            END IF;
        END$$;
    """)

    # Catálogo de tipos de sustrato
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS substrate_type (
            id_substrate_type  SERIAL PRIMARY KEY,
            name               CHARACTER VARYING(50) NOT NULL UNIQUE,
            description        TEXT,
            water_retention    DOUBLE PRECISION DEFAULT 1.0,
            nutrient_release   DOUBLE PRECISION DEFAULT 1.0,
            drainage_factor    DOUBLE PRECISION DEFAULT 1.0
        )
    """)

    # Pre-cargar tipos de sustrato (ON CONFLICT DO NOTHING para idempotencia)
    cursor.execute("""
        INSERT INTO substrate_type (name, description, water_retention, nutrient_release, drainage_factor)
        VALUES
            ('corteza',        'Corteza de pino. Excelente drenaje, poca retención. Ideal para orquídeas.', 0.7, 0.8, 1.4),
            ('musgo_sphagnum', 'Musgo sphagnum. Alta retención de humedad y agua.',                         1.5, 1.2, 0.6),
            ('perlita',        'Perlita volcánica. Drenaje máximo, retención mínima.',                      0.5, 0.5, 1.8),
            ('mixto',          'Mezcla balanceada para uso general.',                                       1.0, 1.0, 1.0)
        ON CONFLICT (name) DO NOTHING
    """)

    # Maceta (1:1 con planta)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pot (
            id_pot             SERIAL PRIMARY KEY,
            material           CHARACTER VARYING(50) DEFAULT 'plastico',
            size_cm            INTEGER DEFAULT 15,
            drainage_level     DOUBLE PRECISION DEFAULT 60.0,
            ventilation_level  DOUBLE PRECISION DEFAULT 50.0,
            fk_plant_id        INTEGER NOT NULL UNIQUE REFERENCES plant(id_plant)
        )
    """)

    # Historial de acciones de cuidado
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS care_history (
            id_history   SERIAL PRIMARY KEY,
            fk_plant_id  INTEGER NOT NULL REFERENCES plant(id_plant),
            action_type  CHARACTER VARYING(50) NOT NULL,
            value        DOUBLE PRECISION,
            extra_info   TEXT,
            created_at   TIMESTAMP DEFAULT NOW()
        )
    """)

    conn.commit()
    conn.close()
