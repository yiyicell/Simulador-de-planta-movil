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
            coins          BIGINT      NOT NULL DEFAULT 0,
            online         BOOLEAN     NOT NULL DEFAULT FALSE,
            rol_admin      BOOLEAN     NOT NULL DEFAULT FALSE,
            creation_date  DATE        NOT NULL DEFAULT CURRENT_DATE
        )
    """)

    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user' AND column_name = 'coins'
            ) THEN
                ALTER TABLE "user" ADD COLUMN coins BIGINT NOT NULL DEFAULT 0;
            END IF;
        END$$;
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

    # Historial de movimientos de coins
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coin_transaction (
            id_transaction   SERIAL PRIMARY KEY,
            fk_user_id       INTEGER NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
            amount           INTEGER NOT NULL,
            movement_type    CHARACTER VARYING(20) NOT NULL,
            reason           CHARACTER VARYING(120),
            related_plant_id INTEGER REFERENCES plant(id_plant),
            related_item_id  INTEGER,
            created_at       TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    # Catálogo de ítems de tienda
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shop_item (
            id_item       SERIAL PRIMARY KEY,
            item_name     CHARACTER VARYING(80) NOT NULL UNIQUE,
            item_type     CHARACTER VARYING(30) NOT NULL,
            price_coins   INTEGER NOT NULL,
            rarity        CHARACTER VARYING(20) DEFAULT 'common',
            active        BOOLEAN NOT NULL DEFAULT TRUE
        )
    """)

    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'shop_item_item_name_key'
            ) THEN
                ALTER TABLE shop_item
                ADD CONSTRAINT shop_item_item_name_key UNIQUE (item_name);
            END IF;
        END$$;
    """)

    # Inventario del usuario
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_inventory (
            id_inventory  SERIAL PRIMARY KEY,
            fk_user_id    INTEGER NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
            fk_item_id    INTEGER NOT NULL REFERENCES shop_item(id_item),
            quantity      INTEGER NOT NULL DEFAULT 1,
            acquired_at   TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE (fk_user_id, fk_item_id)
        )
    """)

    # Seed de ítems iniciales de tienda
    cursor.execute("""
        INSERT INTO shop_item (item_name, item_type, price_coins, rarity, active)
        VALUES
            ('Maceta de barro clásica', 'maceta', 25, 'common', TRUE),
            ('Maceta minimalista blanca', 'maceta', 45, 'rare', TRUE),
            ('Fondo Bosque de Niebla', 'fondo', 30, 'common', TRUE),
            ('Fondo Atardecer Andino', 'fondo', 60, 'epic', TRUE),
            ('Roca decorativa musgo', 'decoracion', 20, 'common', TRUE),
            ('Luciérnagas mágicas', 'decoracion', 75, 'epic', TRUE)
        ON CONFLICT DO NOTHING
    """)

    # Tokens de recuperación de contraseña
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS token (
            token_id    SERIAL PRIMARY KEY,
            fk_user_id  INTEGER NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
            token       CHARACTER VARYING(64) NOT NULL UNIQUE,
            expiration  TIMESTAMP NOT NULL,
            available   BOOLEAN NOT NULL DEFAULT TRUE,
            active      BOOLEAN NOT NULL DEFAULT TRUE
        )
    """)

    conn.commit()
    conn.close()
