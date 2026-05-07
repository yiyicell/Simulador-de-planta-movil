"""
Lógica de acciones de cuidado: regar, ajustar luz y ajustar ventilación.

Conversiones y reglas:
  Riego:
    - efectivo_agua = cantidad_ml * ML_A_PUNTOS_AGUA * sustrato.water_retention
    - También sube levemente la humedad: cantidad_ml * ML_A_PUNTOS_HUMEDAD
    - Límites: [10, 600] ml por acción

  Luz:
    - light_level se asigna directamente a la intensidad (0–100)
    - Luz > 70 deseca el sustrato: (intensidad - 70) * 0.30 pts de humedad menos

  Ventilación ambiental:
    - ventilation_level se asigna directamente (0–100)
    - Ventilación > 75 acelera el secado: (nivel - 75) * 0.20 pts de agua menos

Cada acción suma 1 a total_care_actions y se registra en care_history.
"""

try:
    from backend.database import get_connection
    from backend.plant.models import PlantaRespuesta
    from backend.plant.growth import (
        calcular_salud,
        obtener_etapa,
        LUZ_FACTOR_SECADO,
        REGLAS_AGUA,
        REGLAS_LUZ,
        REGLAS_HUMEDAD,
        REGLAS_VENTILACION,
    )
    from backend.plant.history import registrar_accion
    from backend.economy import sumar_coins_por_cuidado, RECOMPENSA_CUIDADO_OPTIMO
except ModuleNotFoundError:
    from database import get_connection
    from plant.models import PlantaRespuesta
    from plant.growth import (
        calcular_salud,
        obtener_etapa,
        LUZ_FACTOR_SECADO,
        REGLAS_AGUA,
        REGLAS_LUZ,
        REGLAS_HUMEDAD,
        REGLAS_VENTILACION,
    )
    from plant.history import registrar_accion
    from economy import sumar_coins_por_cuidado, RECOMPENSA_CUIDADO_OPTIMO

# Constantes de riego
ML_MIN = 10.0
ML_MAX = 600.0
ML_A_PUNTOS_AGUA    = 0.20
ML_A_PUNTOS_HUMEDAD = 0.04

# Factor de secado por ventilación excesiva
VENTILACION_UMBRAL_SECADO = 75.0
VENTILACION_FACTOR_SECADO = 0.20


# ---------------------------------------------------------------------------
# Query base de planta (incluye sustrato por JOIN)
# ---------------------------------------------------------------------------

_SELECT_PLANTA = """
    SELECT p.id_plant, p.plant_name, p.plant_type,
           p.water_level, p.light_level, p.humidity_level, p.health,
           p.growth_stage, p.total_care_actions,
           p.creation_date_plant, p.fk_user_id,
           COALESCE(p.ventilation_level, 50.0),
           COALESCE(st.water_retention, 1.0),
           COALESCE(st.name, 'mixto')
    FROM plant p
    LEFT JOIN substrate_type st ON st.id_substrate_type = p.fk_substrate_type
    WHERE p.id_plant = %s
"""
# Índices: [0]id [1]name [2]type [3]water [4]light [5]humidity [6]health
#          [7]stage [8]acciones [9]date [10]user [11]ventilation [12]retention [13]substrate_name


def _obtener_planta(plant_id: int, conn):
    cursor = conn.cursor()
    cursor.execute(_SELECT_PLANTA, (plant_id,))
    return cursor.fetchone()


def _actualizar_planta(plant_id: int, campos: dict, conn) -> None:
    """Actualiza los campos indicados de la planta."""
    set_clause = ", ".join(f"{k} = %s" for k in campos)
    valores = list(campos.values()) + [plant_id]
    conn.cursor().execute(
        f"UPDATE plant SET {set_clause} WHERE id_plant = %s",
        valores,
    )


def _fila_a_respuesta(row) -> PlantaRespuesta:
    return PlantaRespuesta(
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
        substrate_name=row[13] or "mixto",
    )


def _es_cuidado_optimo(water_level: float, light_level: float, humidity_level: float, ventilation: float, health: float) -> bool:
    return (
        REGLAS_AGUA["optimo_bajo"] <= water_level <= REGLAS_AGUA["optimo_alto"]
        and REGLAS_LUZ["optimo_bajo"] <= light_level <= REGLAS_LUZ["optimo_alto"]
        and REGLAS_HUMEDAD["optimo_bajo"] <= humidity_level <= REGLAS_HUMEDAD["optimo_alto"]
        and REGLAS_VENTILACION["optimo_bajo"] <= ventilation <= REGLAS_VENTILACION["optimo_alto"]
        and health >= 80.0
    )


def regar_planta(plant_id: int, cantidad_ml: float) -> dict:
    """
    Aplica un riego a la planta.

    - El agua efectiva = cantidad_ml * 0.20 * sustrato.water_retention.
    - Sube levemente la humedad.
    - Recalcula salud (con ventilación) y etapa de crecimiento.
    - Registra la acción en el historial.
    """
    if cantidad_ml < ML_MIN or cantidad_ml > ML_MAX:
        return {
            "exito": False,
            "mensaje": f"La cantidad debe estar entre {ML_MIN:.0f} ml y {ML_MAX:.0f} ml.",
            "planta": None,
        }

    conn = get_connection()
    try:
        row = _obtener_planta(plant_id, conn)
        if not row:
            return {"exito": False, "mensaje": "Planta no encontrada.", "planta": None}

        water_retention = row[12]
        pts_agua = cantidad_ml * ML_A_PUNTOS_AGUA * water_retention

        water_level    = min(100.0, (row[3] or 0.0) + pts_agua)
        humidity_level = min(100.0, (row[5] or 0.0) + cantidad_ml * ML_A_PUNTOS_HUMEDAD)
        light_level    = row[4] or 0.0
        ventilation    = row[11] or 50.0
        total_acciones = (row[8] or 0) + 1

        nueva_salud = calcular_salud(water_level, light_level, humidity_level, ventilation)
        nueva_etapa = obtener_etapa(total_acciones, row[2], nueva_salud)

        _actualizar_planta(plant_id, {
            "water_level":        round(water_level, 2),
            "humidity_level":     round(humidity_level, 2),
            "health":             nueva_salud,
            "growth_stage":       nueva_etapa,
            "total_care_actions": total_acciones,
        }, conn)

        sustrato_nombre = row[13] or "mixto"
        registrar_accion(
            plant_id=plant_id,
            action_type="riego",
            value=cantidad_ml,
            extra_info=f"+{pts_agua:.1f} pts agua (sustrato: {sustrato_nombre}, retención: {water_retention:.2f}x)",
            conn=conn,
        )

        coins_ganadas = 0
        if _es_cuidado_optimo(water_level, light_level, humidity_level, ventilation, nueva_salud):
            coins_ganadas = RECOMPENSA_CUIDADO_OPTIMO
            sumar_coins_por_cuidado(user_id=row[10], plant_id=plant_id, coins=coins_ganadas, conn=conn)

        conn.commit()

        row_actualizado = _obtener_planta(plant_id, conn)
        return {
            "exito": True,
            "mensaje": (
                f"Riego aplicado: {cantidad_ml:.0f} ml → "
                f"+{pts_agua:.1f} pts de agua (sustrato: {sustrato_nombre})."
            ),
            "planta": _fila_a_respuesta(row_actualizado),
            "coins_ganadas": coins_ganadas,
        }
    except Exception as e:
        conn.rollback()
        return {"exito": False, "mensaje": f"Error al regar la planta: {e}", "planta": None}
    finally:
        conn.close()


def ajustar_luz(plant_id: int, intensidad: float) -> dict:
    """
    Ajusta la intensidad de la lámpara (0–100).
    Luz > 70 deseca el sustrato.
    """
    if not (0.0 <= intensidad <= 100.0):
        return {"exito": False, "mensaje": "La intensidad debe estar entre 0 y 100.", "planta": None}

    conn = get_connection()
    try:
        row = _obtener_planta(plant_id, conn)
        if not row:
            return {"exito": False, "mensaje": "Planta no encontrada.", "planta": None}

        light_level    = intensidad
        humidity_level = row[5] or 0.0
        water_level    = row[3] or 0.0
        ventilation    = row[11] or 50.0

        if intensidad > 70.0:
            penalizacion = (intensidad - 70.0) * LUZ_FACTOR_SECADO
            humidity_level = max(0.0, humidity_level - penalizacion)

        total_acciones = (row[8] or 0) + 1
        nueva_salud    = calcular_salud(water_level, light_level, humidity_level, ventilation)
        nueva_etapa    = obtener_etapa(total_acciones, row[2], nueva_salud)

        _actualizar_planta(plant_id, {
            "light_level":        round(light_level, 2),
            "humidity_level":     round(humidity_level, 2),
            "health":             nueva_salud,
            "growth_stage":       nueva_etapa,
            "total_care_actions": total_acciones,
        }, conn)

        registrar_accion(
            plant_id=plant_id,
            action_type="luz",
            value=intensidad,
            extra_info=f"Intensidad: {intensidad:.0f}%",
            conn=conn,
        )

        coins_ganadas = 0
        if _es_cuidado_optimo(water_level, light_level, humidity_level, ventilation, nueva_salud):
            coins_ganadas = RECOMPENSA_CUIDADO_OPTIMO
            sumar_coins_por_cuidado(user_id=row[10], plant_id=plant_id, coins=coins_ganadas, conn=conn)

        conn.commit()

        row_actualizado = _obtener_planta(plant_id, conn)
        return {
            "exito": True,
            "mensaje": f"Intensidad de luz ajustada a {intensidad:.0f}%.",
            "planta": _fila_a_respuesta(row_actualizado),
            "coins_ganadas": coins_ganadas,
        }
    except Exception as e:
        conn.rollback()
        return {"exito": False, "mensaje": f"Error al ajustar la luz: {e}", "planta": None}
    finally:
        conn.close()


def ajustar_ventilacion(plant_id: int, nivel: float) -> dict:
    """
    Ajusta el nivel de ventilación ambiental de la planta (0–100).
    Ventilación > 75 genera un leve secado del sustrato.
    """
    if not (0.0 <= nivel <= 100.0):
        return {"exito": False, "mensaje": "El nivel de ventilación debe estar entre 0 y 100.", "planta": None}

    conn = get_connection()
    try:
        row = _obtener_planta(plant_id, conn)
        if not row:
            return {"exito": False, "mensaje": "Planta no encontrada.", "planta": None}

        ventilation    = nivel
        water_level    = row[3] or 0.0
        light_level    = row[4] or 0.0
        humidity_level = row[5] or 0.0

        if nivel > VENTILACION_UMBRAL_SECADO:
            secado = (nivel - VENTILACION_UMBRAL_SECADO) * VENTILACION_FACTOR_SECADO
            water_level = max(0.0, water_level - secado)

        total_acciones = (row[8] or 0) + 1
        nueva_salud    = calcular_salud(water_level, light_level, humidity_level, ventilation)
        nueva_etapa    = obtener_etapa(total_acciones, row[2], nueva_salud)

        _actualizar_planta(plant_id, {
            "ventilation_level":  round(ventilation, 2),
            "water_level":        round(water_level, 2),
            "health":             nueva_salud,
            "growth_stage":       nueva_etapa,
            "total_care_actions": total_acciones,
        }, conn)

        registrar_accion(
            plant_id=plant_id,
            action_type="ventilacion",
            value=nivel,
            extra_info=f"Ventilación ajustada a {nivel:.0f}%",
            conn=conn,
        )

        coins_ganadas = 0
        if _es_cuidado_optimo(water_level, light_level, humidity_level, ventilation, nueva_salud):
            coins_ganadas = RECOMPENSA_CUIDADO_OPTIMO
            sumar_coins_por_cuidado(user_id=row[10], plant_id=plant_id, coins=coins_ganadas, conn=conn)

        conn.commit()

        row_actualizado = _obtener_planta(plant_id, conn)
        return {
            "exito": True,
            "mensaje": f"Ventilación ambiental ajustada a {nivel:.0f}%.",
            "planta": _fila_a_respuesta(row_actualizado),
            "coins_ganadas": coins_ganadas,
        }
    except Exception as e:
        conn.rollback()
        return {"exito": False, "mensaje": f"Error al ajustar la ventilación: {e}", "planta": None}
    finally:
        conn.close()
