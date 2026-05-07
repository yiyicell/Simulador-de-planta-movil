"""
Reglas de crecimiento, etapas y límites de cuidado para las plantas.

Cuadro de factores:
┌─────────────┬──────────────────┬────────────────────────┬──────────────────────────────────────────────────────────┐
│ Factor      │ Rango óptimo     │ Rango bajo / excesivo  │ Efecto (hojas, raíces, tallo, salud)                    │
├─────────────┼──────────────────┼────────────────────────┼──────────────────────────────────────────────────────────┤
│ Agua        │ 40 – 80 %        │ < 20: sequía           │ Bajo: marchitamiento hojas, estrés raíces               │
│             │                  │ > 90: encharcamiento   │ Alto: pudrición raíces, hongos en sustrato              │
├─────────────┼──────────────────┼────────────────────────┼──────────────────────────────────────────────────────────┤
│ Luz         │ 30 – 70 %        │ < 15: poca luz         │ Bajo: etiolación tallo, hojas pálidas y débiles         │
│             │                  │ > 85: exceso de luz    │ Alto: quemaduras hojas, desecación rápida sustrato      │
├─────────────┼──────────────────┼────────────────────────┼──────────────────────────────────────────────────────────┤
│ Humedad     │ 50 – 80 %        │ < 30: ambiente seco    │ Bajo: raíces deshidratadas, hojas enrolladas            │
│             │                  │ > 92: ambiente húmedo  │ Alto: pudrición fúngica raíces y sustrato               │
└─────────────┴──────────────────┴────────────────────────┴──────────────────────────────────────────────────────────┘
"""

# ---------------------------------------------------------------------------
# Etapas de crecimiento
# ---------------------------------------------------------------------------

# Etapas generales: (umbral_acciones, nombre_etapa)
UMBRALES_GENERALES: list[tuple[int, str]] = [
    (0,  "germinacion"),
    (3,  "enraizamiento"),
    (8,  "plantula"),
    (15, "crecimiento"),
    (25, "floracion"),
    (35, "fructificacion"),
]

# Etapas específicas de la orquídea (floración tiene sus propias sub-etapas)
UMBRALES_ORQUIDEA: list[tuple[int, str]] = [
    (0,  "germinacion"),
    (3,  "enraizamiento"),
    (8,  "plantula"),
    (15, "crecimiento"),
    (25, "vara_floral"),        # La orquídea produce una vara floral antes de florecer
    (32, "botones_florales"),   # Aparecen los botones en la vara
    (40, "crecimiento_botones"), # Los botones se desarrollan
    (50, "apertura_petalos"),   # Los pétalos se abren completamente
]

# Descripción de cada etapa para mostrar al usuario
DESCRIPCION_ETAPAS: dict[str, str] = {
    "germinacion":         "La semilla ha germinado. La planta está iniciando su vida.",
    "enraizamiento":       "Se están formando las primeras raíces y un pequeño tallo.",
    "plantula":            "La plántula ha desarrollado sus primeras hojas.",
    "crecimiento":         "La planta crece en altura y fortaleza.",
    "floracion":           "La planta está lista para florecer.",
    "fructificacion":      "La planta produce frutos con semillas.",
    "vara_floral":         "La orquídea ha generado una vara floral.",
    "botones_florales":    "Los botones florales han aparecido en la vara.",
    "crecimiento_botones": "Los botones florales están creciendo y madurando.",
    "apertura_petalos":    "¡Los pétalos se están abriendo! La orquídea está en plena floración.",
}

# ---------------------------------------------------------------------------
# Reglas de cuidado (límites por factor)
# ---------------------------------------------------------------------------

REGLAS_AGUA = {
    "optimo_bajo":  40.0,
    "optimo_alto":  80.0,
    "critico_bajo": 10.0,
    "critico_alto": 95.0,
    "efecto_bajo":  "Marchitamiento de hojas, raíces en estrés hídrico.",
    "efecto_alto":  "Pudrición de raíces, crecimiento de hongos en sustrato.",
}

REGLAS_LUZ = {
    "optimo_bajo":  30.0,
    "optimo_alto":  70.0,
    "critico_bajo":  5.0,
    "critico_alto": 90.0,
    "efecto_bajo":  "Etiolación del tallo, hojas pálidas y débiles.",
    "efecto_alto":  "Quemaduras en hojas, desecación acelerada del sustrato.",
}

REGLAS_HUMEDAD = {
    "optimo_bajo":  50.0,
    "optimo_alto":  80.0,
    "critico_bajo": 20.0,
    "critico_alto": 92.0,
    "efecto_bajo":  "Raíces deshidratadas, hojas enrolladas.",
    "efecto_alto":  "Pudrición fúngica en raíces y sustrato.",
}

REGLAS_VENTILACION = {
    "optimo_bajo":  40.0,
    "optimo_alto":  75.0,
    "critico_bajo": 10.0,
    "critico_alto": 95.0,
    "efecto_bajo":  "Raíces sin oxígeno, riesgo de pudrición radicular.",
    "efecto_alto":  "Sustrato se seca demasiado rápido, raíces deshidratadas.",
}

# Factor de desecación de humedad por cada punto de luz por encima del óptimo (70)
# Ejemplo: luz=90 → penalización = (90-70) * 0.3 = 6 puntos de humedad menos
LUZ_FACTOR_SECADO = 0.30

# ---------------------------------------------------------------------------
# Funciones de cálculo
# ---------------------------------------------------------------------------

def _puntaje_factor(valor: float, reglas: dict) -> float:
    """Retorna un puntaje 0–100 para un factor de cuidado según sus reglas."""
    ob = reglas["optimo_bajo"]
    oa = reglas["optimo_alto"]
    cb = reglas["critico_bajo"]
    ca = reglas["critico_alto"]

    if ob <= valor <= oa:
        return 100.0
    if valor <= cb or valor >= ca:
        return 0.0
    if valor < ob:
        rango = ob - cb
        return 50.0 * (valor - cb) / rango if rango > 0 else 0.0
    # valor > oa
    rango = ca - oa
    return 50.0 * (ca - valor) / rango if rango > 0 else 0.0


def calcular_salud(
    water_level: float,
    light_level: float,
    humidity_level: float,
    ventilation_level: float = 50.0,
) -> float:
    """
    Calcula la salud general de la planta (0–100) como promedio ponderado.
    Pesos: agua 35 %, luz 25 %, humedad 25 %, ventilación 15 %.
    ventilation_level tiene default 50.0 (óptimo) para compatibilidad.

    Penalizaciones por condición extrema:
      Deshidratación severa (agua ≤ critico_bajo = 10):
        La planta no puede realizar fotosíntesis. Multiplicador ×0.35.
        → Permite que la salud llegue a 0 cuando agua=0 y humedad=0.

      Encharcamiento severo (agua ≥ critico_alto = 95):
        Las raíces no pueden respirar ni absorber nutrientes por pudrición.
        Multiplicador ×0.50. Más recuperable que la sequía (basta con
        mejorar el drenaje / sustrato).
    """
    pw = _puntaje_factor(water_level,       REGLAS_AGUA)
    pl = _puntaje_factor(light_level,       REGLAS_LUZ)
    ph = _puntaje_factor(humidity_level,    REGLAS_HUMEDAD)
    pv = _puntaje_factor(ventilation_level, REGLAS_VENTILACION)
    salud = pw * 0.35 + pl * 0.25 + ph * 0.25 + pv * 0.15

    if water_level <= REGLAS_AGUA["critico_bajo"]:
        salud *= 0.35
    elif water_level >= REGLAS_AGUA["critico_alto"]:
        salud *= 0.50

    return round(salud, 2)


def obtener_etapa(total_acciones: int, tipo_planta: str, health: float = 100.0) -> str:
    """
    Determina la etapa de crecimiento según las acciones de cuidado acumuladas
    y la salud actual de la planta.

    Penalizaciones por salud deficiente:
      - health >= 50 : crecimiento normal
      - 30 <= health < 50 : crecimiento ralentizado (60 % de las acciones cuentan)
      - health < 30 : crecimiento severamente afectado (25 % de las acciones cuentan)
                      La planta puede retroceder etapas por pudrición/daño grave.
    """
    if health < 30.0:
        acciones_efectivas = max(0, int(total_acciones * 0.25))
    elif health < 50.0:
        acciones_efectivas = max(0, int(total_acciones * 0.60))
    else:
        acciones_efectivas = total_acciones

    umbrales = UMBRALES_ORQUIDEA if tipo_planta == "orquidea" else UMBRALES_GENERALES
    etapa = umbrales[0][1]
    for umbral, nombre in umbrales:
        if acciones_efectivas >= umbral:
            etapa = nombre
    return etapa


def etiqueta_salud(health: float) -> str:
    """Convierte el valor numérico de salud en una etiqueta descriptiva."""
    if health >= 80:
        return "Excelente"
    if health >= 60:
        return "Buena"
    if health >= 40:
        return "Regular"
    if health >= 20:
        return "Muy baja"
    return "Crítica"


def alertas_cuidado(
    water_level: float,
    light_level: float,
    humidity_level: float,
    ventilation_level: float = 50.0,
) -> list[str]:
    """Retorna una lista de alertas activas según el estado de los factores."""
    alertas = []

    if water_level < REGLAS_AGUA["critico_bajo"]:
        alertas.append(f"⚠️ AGUA CRÍTICA: {REGLAS_AGUA['efecto_bajo']}")
    elif water_level < REGLAS_AGUA["optimo_bajo"]:
        alertas.append(f"💧 Agua baja ({water_level:.1f}%): {REGLAS_AGUA['efecto_bajo']}")
    elif water_level > REGLAS_AGUA["critico_alto"]:
        alertas.append(f"⚠️ AGUA EXCESIVA: {REGLAS_AGUA['efecto_alto']}")
    elif water_level > REGLAS_AGUA["optimo_alto"]:
        alertas.append(f"💧 Agua elevada ({water_level:.1f}%): {REGLAS_AGUA['efecto_alto']}")

    if light_level < REGLAS_LUZ["critico_bajo"]:
        alertas.append(f"⚠️ LUZ CRÍTICA: {REGLAS_LUZ['efecto_bajo']}")
    elif light_level < REGLAS_LUZ["optimo_bajo"]:
        alertas.append(f"☀️ Luz baja ({light_level:.1f}%): {REGLAS_LUZ['efecto_bajo']}")
    elif light_level > REGLAS_LUZ["critico_alto"]:
        alertas.append(f"⚠️ LUZ EXCESIVA: {REGLAS_LUZ['efecto_alto']}")
    elif light_level > REGLAS_LUZ["optimo_alto"]:
        alertas.append(f"☀️ Luz elevada ({light_level:.1f}%): {REGLAS_LUZ['efecto_alto']}")

    if humidity_level < REGLAS_HUMEDAD["critico_bajo"]:
        alertas.append(f"⚠️ HUMEDAD CRÍTICA: {REGLAS_HUMEDAD['efecto_bajo']}")
    elif humidity_level < REGLAS_HUMEDAD["optimo_bajo"]:
        alertas.append(f"🌫️ Humedad baja ({humidity_level:.1f}%): {REGLAS_HUMEDAD['efecto_bajo']}")
    elif humidity_level > REGLAS_HUMEDAD["critico_alto"]:
        alertas.append(f"⚠️ HUMEDAD EXCESIVA: {REGLAS_HUMEDAD['efecto_alto']}")
    elif humidity_level > REGLAS_HUMEDAD["optimo_alto"]:
        alertas.append(f"🌫️ Humedad elevada ({humidity_level:.1f}%): {REGLAS_HUMEDAD['efecto_alto']}")

    if ventilation_level < REGLAS_VENTILACION["critico_bajo"]:
        alertas.append(f"⚠️ VENTILACIÓN CRÍTICA: {REGLAS_VENTILACION['efecto_bajo']}")
    elif ventilation_level < REGLAS_VENTILACION["optimo_bajo"]:
        alertas.append(f"💨 Ventilación baja ({ventilation_level:.1f}%): {REGLAS_VENTILACION['efecto_bajo']}")
    elif ventilation_level > REGLAS_VENTILACION["critico_alto"]:
        alertas.append(f"⚠️ VENTILACIÓN EXCESIVA: {REGLAS_VENTILACION['efecto_alto']}")
    elif ventilation_level > REGLAS_VENTILACION["optimo_alto"]:
        alertas.append(f"💨 Ventilación elevada ({ventilation_level:.1f}%): {REGLAS_VENTILACION['efecto_alto']}")

    # Alerta combinada: ventilación baja + humedad alta = riesgo de pudrición radicular
    if ventilation_level < 30.0 and humidity_level > 75.0:
        alertas.append("⚠️ RIESGO RADICULAR: Humedad alta con ventilación insuficiente favorece pudrición de raíces.")

    return alertas
