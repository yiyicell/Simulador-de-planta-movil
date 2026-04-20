"""
Decaimiento periódico de las plantas.

Cada INTERVALO_MINUTOS minutos el scheduler ejecuta calcular_decaimiento().
El cálculo es proporcional al tiempo real transcurrido desde el último tick,
por lo que funciona correctamente aunque el servidor se reinicie.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tasas de referencia (por intervalo de 5 min, sustrato mixto, luz óptima)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Agua base:    -0.03 pts / intervalo
  Humedad base: -0.02 pts / intervalo

Efecto del sustrato (water_retention):
  corteza (0.7)       → agua  -0.043 / intervalo → muerte sin riego ≈ 2.9 días
  mixto   (1.0)       → agua  -0.030 / intervalo → muerte sin riego ≈ 3.5 días
  musgo   (1.5)       → agua  -0.020 / intervalo → muerte sin riego ≈ 5.2 días
  perlita (0.5)       → agua  -0.060 / intervalo → muerte sin riego ≈ 2.1 días

Efecto de la luz (por encima del óptimo, 70 %):
  Cada punto extra de luz acelera la evaporación del agua y la humedad.
  Ejemplo luz=90 → +0.04 pts de agua extra / intervalo (total ≈ 0.07).

Exceso de agua (encharcamiento ≥ 90 %):
  El sustrato drena más rápido (+0.10 pts/intervalo) para simular drenaje.
  La humedad sube levemente (+0.04 pts/intervalo): raíces encharcadas.
  calcular_salud() ya penaliza la salud cuando water ≥ critico_alto (95).

Dormir 8 horas (96 intervalos, sustrato mixto, luz óptima):
  Agua: −2.9 pts (de 30 → 27)   Salud resultante: ~75 ("Buena") ✓

Muerte:
  Cuando la salud calculada cae a ≤ UMBRAL_MUERTE, la planta se marca
  is_dead = TRUE, growth_stage = 'muerta', health = 0.
"""

from datetime import datetime, timezone

try:
    from backend.database import get_connection
    from backend.plant.growth import calcular_salud, obtener_etapa
except ModuleNotFoundError:
    from database import get_connection
    from plant.growth import calcular_salud, obtener_etapa

# ---------------------------------------------------------------------------
# Configuración de decaimiento
# ---------------------------------------------------------------------------

INTERVALO_MINUTOS = 5           # cada cuántos minutos corre el job

# Decaimiento base por intervalo (se divide por water_retention del sustrato)
AGUA_DECAY_BASE    = 0.03       # pts de agua / intervalo con sustrato mixto
HUMEDAD_DECAY_BASE = 0.02       # pts de humedad / intervalo base

# Sin agua el sustrato también pierde humedad más rápido (agua ≤ 20)
HUMEDAD_DECAY_EXTRA_SIN_AGUA = 0.03

# La luz por encima del óptimo (70 %) acelera la evaporación
LUZ_UMBRAL_EVAPORACION   = 70.0
LUZ_FACTOR_AGUA_EVAP     = 0.002   # pts agua extra por punto de luz > 70 / intervalo
LUZ_FACTOR_HUMEDAD_EVAP  = 0.0010  # pts humedad extra por punto de luz > 70 / intervalo

# Encharcamiento: water > 90 %
AGUA_UMBRAL_ENCHARCAMIENTO    = 90.0
AGUA_DRENAJE_EXTRA            = 0.10   # el exceso drena → agua baja más rápido
HUMEDAD_EXTRA_ENCHARCAMIENTO  = 0.04   # raíces encharcadas → sube la humedad del entorno

# La planta muere cuando la salud calculada cae a este umbral
UMBRAL_MUERTE = 20.0


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def calcular_decaimiento() -> None:
    """
    Recorre todas las plantas vivas, aplica el decaimiento proporcional al
    tiempo transcurrido y marca como muertas las que superan el umbral.

    Puede llamarse manualmente para forzar un tick (tests, notebooks).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT p.id_plant, p.water_level, p.light_level, p.humidity_level,
                   p.ventilation_level, p.total_care_actions, p.plant_type,
                   p.last_decay_at,
                   COALESCE(st.water_retention, 1.0)
            FROM plant p
            LEFT JOIN substrate_type st ON st.id_substrate_type = p.fk_substrate_type
            WHERE p.is_dead = FALSE
            """
        )
        plantas = cursor.fetchall()
        ahora = datetime.now(timezone.utc)

        for row in plantas:
            (plant_id, water, light, humidity, ventilation,
             total_acciones, tipo, last_decay_at, water_retention) = row

            # ── Intervalos transcurridos ──────────────────────────────────
            if last_decay_at is None:
                intervalos = 1.0
            else:
                if last_decay_at.tzinfo is None:
                    last_decay_at = last_decay_at.replace(tzinfo=timezone.utc)
                minutos = (ahora - last_decay_at).total_seconds() / 60.0
                intervalos = minutos / INTERVALO_MINUTOS

            if intervalos < 0.5:
                continue  # aún no ha pasado medio intervalo, esperar

            water      = water    or 0.0
            light      = light    or 40.0
            humidity   = humidity or 0.0
            ventilation = ventilation or 50.0
            water_retention = water_retention or 1.0

            # ── Decaimiento de agua ───────────────────────────────────────
            # El sustrato con mayor retención pierde agua más lentamente
            decay_agua_base = AGUA_DECAY_BASE / water_retention

            # La luz alta acelera la evaporación del sustrato
            luz_extra = max(0.0, light - LUZ_UMBRAL_EVAPORACION)
            decay_agua_luz = luz_extra * LUZ_FACTOR_AGUA_EVAP

            # Encharcamiento: el exceso drena más rápido
            decay_agua_drenaje = (
                AGUA_DRENAJE_EXTRA if water > AGUA_UMBRAL_ENCHARCAMIENTO else 0.0
            )

            decay_agua_total = decay_agua_base + decay_agua_luz + decay_agua_drenaje
            nuevo_water = max(0.0, water - decay_agua_total * intervalos)

            # ── Decaimiento de humedad ────────────────────────────────────
            # Sin agua el sustrato también se seca
            humedad_extra_sequia = (
                HUMEDAD_DECAY_EXTRA_SIN_AGUA if nuevo_water <= 20.0 else 0.0
            )

            # La luz alta también evapora la humedad del entorno
            decay_humedad_luz = luz_extra * LUZ_FACTOR_HUMEDAD_EVAP

            # Encharcamiento: el entorno de raíces acumula humedad
            humedad_extra_encharcamiento = (
                HUMEDAD_EXTRA_ENCHARCAMIENTO if water > AGUA_UMBRAL_ENCHARCAMIENTO else 0.0
            )

            decay_humedad_total = (
                HUMEDAD_DECAY_BASE
                + humedad_extra_sequia
                + decay_humedad_luz
                - humedad_extra_encharcamiento   # negativo: sube humedad
            )
            # Clamp: humedad siempre entre 0 y 100
            nueva_humidity = max(0.0, min(100.0, humidity - decay_humedad_total * intervalos))

            # ── Recalcular salud ──────────────────────────────────────────
            nueva_salud = calcular_salud(
                nuevo_water, light, nueva_humidity, ventilation
            )

            # ── ¿Murió la planta? ─────────────────────────────────────────
            if nueva_salud <= UMBRAL_MUERTE:
                cursor.execute(
                    """
                    UPDATE plant
                    SET water_level    = %s,
                        humidity_level = %s,
                        health         = 0.0,
                        growth_stage   = 'muerta',
                        is_dead        = TRUE,
                        last_decay_at  = %s
                    WHERE id_plant = %s
                    """,
                    (nuevo_water, nueva_humidity, ahora, plant_id),
                )
            else:
                nueva_etapa = obtener_etapa(total_acciones, tipo or "", nueva_salud)
                cursor.execute(
                    """
                    UPDATE plant
                    SET water_level    = %s,
                        humidity_level = %s,
                        health         = %s,
                        growth_stage   = %s,
                        last_decay_at  = %s
                    WHERE id_plant = %s
                    """,
                    (nuevo_water, nueva_humidity, nueva_salud, nueva_etapa, ahora, plant_id),
                )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

