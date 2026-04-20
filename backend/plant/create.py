"""
Lógica para crear una nueva planta.

Pasos:
  1. Validar campos
  2. Verificar que el usuario exista
  3. Calcular salud inicial
  4. Insertar en la tabla plant con valores iniciales
  5. Retornar la planta creada
"""

from datetime import date

try:
    from backend.database import get_connection
    from backend.plant.models import PlantaCrear, PlantaRespuesta
    from backend.plant.growth import calcular_salud, obtener_etapa
    from backend.plant.pot import crear_maceta_default
except ModuleNotFoundError:
    from database import get_connection
    from plant.models import PlantaCrear, PlantaRespuesta
    from plant.growth import calcular_salud, obtener_etapa
    from plant.pot import crear_maceta_default

# Valores iniciales de cuidado al crear una planta
AGUA_INICIAL         = 30.0
LUZ_INICIAL          = 40.0
HUMEDAD_INICIAL      = 60.0
VENTILACION_INICIAL  = 50.0
TIPOS_VALIDOS        = {"orquidea"}


def _validar_datos(datos: PlantaCrear) -> None:
    if not datos.nombre.strip():
        raise ValueError("El nombre de la planta no puede estar vacío.")
    if datos.tipo.strip().lower() not in TIPOS_VALIDOS:
        raise ValueError(f"Tipo de planta no válido. Tipos disponibles: {', '.join(TIPOS_VALIDOS)}.")
    if not isinstance(datos.fk_user_id, int) or datos.fk_user_id <= 0:
        raise ValueError("El ID de usuario no es válido.")


def _usuario_existe(user_id: int, conn) -> bool:
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM "user" WHERE user_id = %s', (user_id,))
    return cursor.fetchone() is not None


def crear_planta(datos: PlantaCrear) -> dict:
    """
    Crea una nueva planta para el usuario indicado.

    Retorna:
        dict con:
          - "exito" (bool)
          - "mensaje" (str)
          - "planta" (PlantaRespuesta | None)
    """
    try:
        _validar_datos(datos)
    except ValueError as e:
        return {"exito": False, "mensaje": str(e), "planta": None}

    conn = get_connection()
    try:
        if not _usuario_existe(datos.fk_user_id, conn):
            return {"exito": False, "mensaje": "Usuario no encontrado.", "planta": None}

        salud_inicial = calcular_salud(AGUA_INICIAL, LUZ_INICIAL, HUMEDAD_INICIAL, VENTILACION_INICIAL)
        etapa_inicial = obtener_etapa(0, datos.tipo.strip().lower(), salud_inicial)

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO plant (
                plant_name, plant_type,
                water_level, light_level, humidity_level, health,
                growth_stage, total_care_actions,
                creation_date_plant, fk_user_id, ventilation_level,
                is_dead, last_decay_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, NOW())
            RETURNING id_plant
            """,
            (
                datos.nombre.strip(),
                datos.tipo.strip().lower(),
                AGUA_INICIAL,
                LUZ_INICIAL,
                HUMEDAD_INICIAL,
                salud_inicial,
                etapa_inicial,
                0,
                date.today(),
                datos.fk_user_id,
                VENTILACION_INICIAL,
            ),
        )
        plant_id = cursor.fetchone()[0]

        # Crear maceta por defecto y asignar sustrato mixto por defecto
        crear_maceta_default(plant_id, conn)
        cursor.execute(
            """
            UPDATE plant SET fk_substrate_type = (
                SELECT id_substrate_type FROM substrate_type WHERE name = 'mixto' LIMIT 1
            ) WHERE id_plant = %s
            """,
            (plant_id,),
        )

        conn.commit()

        # Recuperar la planta con JOIN de sustrato
        cursor.execute(
            """
            SELECT p.id_plant, p.plant_name, p.plant_type,
                   p.water_level, p.light_level, p.humidity_level, p.health,
                   p.growth_stage, p.total_care_actions,
                   p.creation_date_plant, p.fk_user_id,
                   COALESCE(p.ventilation_level, 50.0),
                   COALESCE(st.name, 'mixto'),
                   COALESCE(p.is_dead, FALSE)
            FROM plant p
            LEFT JOIN substrate_type st ON st.id_substrate_type = p.fk_substrate_type
            WHERE p.id_plant = %s
            """,
            (plant_id,),
        )
        row = cursor.fetchone()

        planta = PlantaRespuesta(
            id_plant=row[0],
            plant_name=row[1],
            plant_type=row[2],
            water_level=row[3],
            light_level=row[4],
            humidity_level=row[5],
            health=row[6],
            growth_stage=row[7],
            total_care_actions=row[8],
            creation_date_plant=str(row[9]),
            fk_user_id=row[10],
            ventilation_level=row[11] or 50.0,
            substrate_name=row[12] or "mixto",
            is_dead=bool(row[13]),
        )
        return {
            "exito": True,
            "mensaje": f"Planta '{planta.plant_name}' creada exitosamente.",
            "planta": planta,
        }

    except Exception as e:
        conn.rollback()
        return {"exito": False, "mensaje": f"Error al crear la planta: {e}", "planta": None}
    finally:
        conn.close()


def contar_plantas_usuario(user_id: int) -> dict:
    """
    Cuenta las plantas del usuario. Útil para detectar si es un usuario nuevo (count == 0).

    Retorna:
        dict con:
          - "exito" (bool)
          - "count" (int)
          - "plantas" (list[PlantaRespuesta])
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT p.id_plant, p.plant_name, p.plant_type,
                   p.water_level, p.light_level, p.humidity_level, p.health,
                   p.growth_stage, p.total_care_actions,
                   p.creation_date_plant, p.fk_user_id,
                   COALESCE(p.ventilation_level, 50.0),
                   COALESCE(st.name, 'mixto'),
                   COALESCE(p.is_dead, FALSE)
            FROM plant p
            LEFT JOIN substrate_type st ON st.id_substrate_type = p.fk_substrate_type
            WHERE p.fk_user_id = %s AND COALESCE(p.is_dead, FALSE) = FALSE
            ORDER BY p.creation_date_plant ASC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        plantas = [
            PlantaRespuesta(
                id_plant=r[0],
                plant_name=r[1],
                plant_type=r[2],
                water_level=r[3] or 0.0,
                light_level=r[4] or 0.0,
                humidity_level=r[5] or 0.0,
                health=r[6] or 0.0,
                growth_stage=r[7] or "germinacion",
                total_care_actions=r[8] or 0,
                creation_date_plant=str(r[9]),
                fk_user_id=r[10],
                ventilation_level=r[11] or 50.0,
                substrate_name=r[12] or "mixto",
                is_dead=bool(r[13]),
            )
            for r in rows
        ]
        return {"exito": True, "count": len(plantas), "plantas": plantas}
    except Exception as e:
        return {"exito": False, "count": 0, "plantas": [], "mensaje": str(e)}
    finally:
        conn.close()
