"""
Modelos de datos para el módulo de plantas.
"""

from dataclasses import dataclass, field


@dataclass
class PlantaCrear:
    """Datos necesarios para crear una nueva planta."""
    nombre: str
    tipo: str       # Tipo de planta, por ahora solo "orquidea"
    fk_user_id: int


@dataclass
class PlantaRespuesta:
    """Estado completo de una planta."""
    id_plant: int
    plant_name: str
    plant_type: str
    water_level: float
    light_level: float
    humidity_level: float
    health: float
    growth_stage: str
    total_care_actions: int
    creation_date_plant: str
    fk_user_id: int
    ventilation_level: float = 50.0   # nivel de ventilación ambiental (0–100)
    substrate_name: str = "mixto"     # nombre del sustrato asignado
    is_dead: bool = False             # True cuando la salud llegó a 0


@dataclass
class AccionRiego:
    """Datos de una acción de riego."""
    plant_id: int
    cantidad_ml: float


@dataclass
class AccionLuz:
    """Datos de un ajuste de intensidad de luz."""
    plant_id: int
    intensidad: float    # 0–100


@dataclass
class AccionVentilacion:
    """Datos de un ajuste de ventilación ambiental."""
    plant_id: int
    nivel: float         # 0–100


# ---------------------------------------------------------------------------
# Sustrato
# ---------------------------------------------------------------------------

@dataclass
class TipoSustrato:
    """Catálogo de tipos de sustrato."""
    id_substrate_type: int
    name: str
    description: str
    water_retention: float    # multiplicador de agua absorbida por riego (0.5–2.0)
    nutrient_release: float   # factor de liberación de nutrientes relativo
    drainage_factor: float    # velocidad de drenaje (1.0 = normal)


# ---------------------------------------------------------------------------
# Maceta
# ---------------------------------------------------------------------------

@dataclass
class Maceta:
    """Información física de la maceta asociada a una planta."""
    id_pot: int
    material: str             # plastico, ceramica, terracota, vidrio
    size_cm: int              # diámetro en cm (por ahora tamaño único: 15)
    drainage_level: float     # nivel de drenaje estructural (0–100)
    ventilation_level: float  # ventilación física de la maceta (huecos/ranuras, 0–100)
    fk_plant_id: int


# ---------------------------------------------------------------------------
# Historial de cuidados
# ---------------------------------------------------------------------------

@dataclass
class HistorialAccion:
    """Registro de una acción de cuidado."""
    id_history: int
    fk_plant_id: int
    action_type: str    # riego | luz | ventilacion | sustrato | maceta
    value: float        # valor principal (ml, intensidad, etc.)
    extra_info: str     # información adicional en texto libre
    created_at: str
