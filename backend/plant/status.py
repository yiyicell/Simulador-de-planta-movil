"""
Consulta del estado actual de la planta.

El estado incluye:
  - Todos los índices de cuidado (agua, luz, humedad)
  - Salud calculada y su etiqueta descriptiva
  - Etapa de crecimiento actual y su descripción
  - Alertas activas si algún factor está fuera del rango óptimo
"""

try:
    from backend.database import get_connection
    from backend.plant.models import PlantaRespuesta
    from backend.plant.growth import (
        calcular_salud,
        obtener_etapa,
        etiqueta_salud,
        alertas_cuidado,
        DESCRIPCION_ETAPAS,
    )
except ModuleNotFoundError:
    from database import get_connection
    from plant.models import PlantaRespuesta
    from plant.growth import (
        calcular_salud,
        obtener_etapa,
        etiqueta_salud,
        alertas_cuidado,
        DESCRIPCION_ETAPAS,
    )


def obtener_estado(plant_id: int) -> dict:
    """
    Retorna el estado completo de la planta.

    Retorna:
        dict con:
          - "exito" (bool)
          - "mensaje" (str)
          - "planta" (PlantaRespuesta)
          - "salud_etiqueta" (str)       — "Excelente", "Buena", "Regular", "Muy baja", "Crítica"
          - "etapa_descripcion" (str)    — descripción de la etapa actual
          - "alertas" (list[str])        — mensajes de alerta por factores fuera de rango
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
            WHERE p.id_plant = %s
            """,
            (plant_id,),
        )
        row = cursor.fetchone()
        if not row:
            return {"exito": False, "mensaje": "Planta no encontrada.", "planta": None}

        water_level    = row[3] or 0.0
        light_level    = row[4] or 0.0
        humidity_level = row[5] or 0.0
        growth_stage   = row[7] or "germinacion"
        total_acciones = row[8] or 0
        tipo_planta    = row[2] or ""
        ventilation    = row[11] or 50.0
        substrate_name = row[12] or "mixto"
        is_dead        = bool(row[13])

        # Si la planta está muerta devolvemos su último estado sin recalcular
        if is_dead:
            planta = PlantaRespuesta(
                id_plant=row[0],
                plant_name=row[1],
                plant_type=tipo_planta,
                water_level=water_level,
                light_level=light_level,
                humidity_level=humidity_level,
                health=0.0,
                growth_stage="muerta",
                total_care_actions=total_acciones,
                creation_date_plant=str(row[9]),
                fk_user_id=row[10],
                ventilation_level=ventilation,
                substrate_name=substrate_name,
                is_dead=True,
            )
            return {
                "exito":             True,
                "mensaje":           "La planta ha muerto.",
                "planta":            planta,
                "salud_etiqueta":    "Muerta",
                "etapa_descripcion": "La planta no recibió los cuidados necesarios y falleció.",
                "alertas":           ["💀 Esta planta ha muerto. Debes crear una nueva planta."],
            }

        salud_actual = calcular_salud(water_level, light_level, humidity_level, ventilation)
        etapa_actual = obtener_etapa(total_acciones, tipo_planta, salud_actual)

        planta = PlantaRespuesta(
            id_plant=row[0],
            plant_name=row[1],
            plant_type=tipo_planta,
            water_level=water_level,
            light_level=light_level,
            humidity_level=humidity_level,
            health=salud_actual,
            growth_stage=etapa_actual,
            total_care_actions=total_acciones,
            creation_date_plant=str(row[9]),
            fk_user_id=row[10],
            ventilation_level=ventilation,
            substrate_name=substrate_name,
            is_dead=False,
        )

        return {
            "exito":             True,
            "mensaje":           "Estado obtenido correctamente.",
            "planta":            planta,
            "salud_etiqueta":    etiqueta_salud(salud_actual),
            "etapa_descripcion": DESCRIPCION_ETAPAS.get(etapa_actual, etapa_actual),
            "alertas":           alertas_cuidado(water_level, light_level, humidity_level, ventilation),
        }
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al consultar el estado: {e}", "planta": None}
    finally:
        conn.close()
