"""
Punto de entrada de la API REST.

Correr con:
    uvicorn backend.main:app --reload

Documentación interactiva disponible en:`
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from apscheduler.schedulers.background import BackgroundScheduler

from auth.login import autenticar_usuario
from auth.register import registrar_usuario
from auth.logout import cerrar_sesion
from auth.password_reset import solicitar_recuperacion, restablecer_password
from auth.models import UsuarioLogin, UsuarioRegistro
from database import init_db, get_connection
from plant.create import crear_planta, contar_plantas_usuario
from plant.care import regar_planta, ajustar_luz, ajustar_ventilacion
from plant.status import obtener_estado
from plant.models import PlantaCrear
from plant.substrate import obtener_tipos_sustrato, asignar_sustrato
from plant.pot import obtener_maceta, actualizar_maceta
from plant.history import obtener_historial
from plant.decay import calcular_decaimiento, INTERVALO_MINUTOS

app = FastAPI(
    title="Simulador de Planta Móvil — API",
    version="0.1.0",
)

# Permitir peticiones desde cualquier origen (frontend en cualquier red)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Esquema de entrada (validado automáticamente por FastAPI/Pydantic)
# ---------------------------------------------------------------------------

class RegistroRequest(BaseModel):
    nombre: str
    correo: str
    password: str

    @field_validator("nombre", "correo", "password")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El campo no puede estar vacío")
        return v


class LoginRequest(BaseModel):
    correo: str
    password: str

    @field_validator("correo", "password")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El campo no puede estar vacío")
        return v


class SolicitudRecuperacionRequest(BaseModel):
    correo: str

    @field_validator("correo")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El campo no puede estar vacío")
        return v


class RestablecerPasswordRequest(BaseModel):
    correo: str
    token: str
    nueva_password: str
    confirmar_password: str

    @field_validator("correo", "token", "nueva_password", "confirmar_password")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El campo no puede estar vacío")
        return v


# Modelos Pydantic para plantas
class CrearPlantaRequest(BaseModel):
    nombre: str
    tipo: str = "orquidea"
    user_id: int

    @field_validator("nombre", "tipo")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El campo no puede estar vacío")
        return v


class RegarRequest(BaseModel):
    cantidad_ml: float


class LuzRequest(BaseModel):
    intensidad: float


class VentilacionRequest(BaseModel):
    nivel: float


class SubstratoRequest(BaseModel):
    substrate_type_id: int


class MacetaRequest(BaseModel):
    material: str | None = None
    drainage_level: float | None = None
    ventilation_level: float | None = None


class EtapaRequest(BaseModel):
    etapa: str

    @field_validator("etapa")
    @classmethod
    def etapa_valida(cls, v: str) -> str:
        from plant.growth import DESCRIPCION_ETAPAS
        if v not in DESCRIPCION_ETAPAS:
            raise ValueError(f"Etapa inválida. Válidas: {list(DESCRIPCION_ETAPAS.keys())}")
        return v


# ---------------------------------------------------------------------------
# Eventos de ciclo de vida
# ---------------------------------------------------------------------------

@app.on_event("startup")
def startup():
    """Crea las tablas si no existen e inicia el scheduler de decaimiento."""
    init_db()
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        calcular_decaimiento,
        trigger="interval",
        minutes=INTERVALO_MINUTOS,
        id="decay_job",
        replace_existing=True,
    )
    scheduler.start()
    app.state.scheduler = scheduler


@app.on_event("shutdown")
def shutdown():
    """Detiene el scheduler al cerrar el servidor."""
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown(wait=False)


# ---------------------------------------------------------------------------
# Endpoints de autenticación
# ---------------------------------------------------------------------------

@app.post("/auth/register", summary="Registrar nuevo usuario")
def register(datos: RegistroRequest):
    """
    Registra un nuevo usuario en el sistema.

    - **nombre**: nombre completo del usuario
    - **correo**: correo electrónico (debe ser único)
    - **password**: contraseña (mínimo 8 caracteres)
    """
    resultado = registrar_usuario(
        UsuarioRegistro(
            nombre=datos.nombre,
            correo=datos.correo,
            password=datos.password,
        )
    )

    if not resultado["exito"]:
        return JSONResponse(status_code=400, content={"mensaje": resultado["mensaje"]})

    u = resultado["usuario"]
    return {
        "mensaje": resultado["mensaje"],
        "usuario": {
            "id": u.id,
            "nombre": u.nombre,
            "correo": u.correo,
            "online": u.online,
            "rol_admin": u.rol_admin,
            "creado": u.creado,
        },
    }


@app.post("/auth/login", summary="Iniciar sesión")
def login(datos: LoginRequest):
    """
    Autentica a un usuario registrado con correo y contraseña.

    - **correo**: correo electrónico del usuario
    - **password**: contraseña en texto plano para validación
    """
    resultado = autenticar_usuario(
        UsuarioLogin(
            correo=datos.correo,
            password=datos.password,
        )
    )

    if not resultado["exito"]:
        status_code = 400
        if resultado["mensaje"] == "Correo o contraseña incorrectos.":
            status_code = 401
        return JSONResponse(status_code=status_code, content={"mensaje": resultado["mensaje"]})

    u = resultado["usuario"]
    return {
        "mensaje": resultado["mensaje"],
        "usuario": {
            "id": u.id,
            "nombre": u.nombre,
            "correo": u.correo,
            "online": u.online,
            "rol_admin": u.rol_admin,
            "creado": u.creado,
        },
    }


@app.post("/auth/logout/{user_id}", summary="Cerrar sesión")
def logout(user_id: int):
    """
    Cierra la sesión del usuario marcando `online = false`.

    - **user_id**: ID del usuario que cierra sesión
    """
    resultado = cerrar_sesion(user_id)
    if not resultado["exito"]:
        status_code = 400 if "inválido" in resultado["mensaje"] else 404
        return JSONResponse(status_code=status_code, content={"mensaje": resultado["mensaje"]})
    return {"mensaje": resultado["mensaje"]}


@app.post("/auth/forgot-password", summary="Solicitar recuperación de contraseña")
def forgot_password(datos: SolicitudRecuperacionRequest):
    """
    Genera un token de recuperación y lo envía al correo indicado.

    Por seguridad, siempre retorna el mismo mensaje sin importar
    si el correo está registrado o no (anti-enumeración).

    - **correo**: correo electrónico asociado a la cuenta
    """
    resultado = solicitar_recuperacion(datos.correo)
    if not resultado["exito"]:
        return JSONResponse(status_code=400, content={"mensaje": resultado["mensaje"]})
    return {"mensaje": resultado["mensaje"]}


@app.post("/auth/reset-password", summary="Restablecer contraseña con token")
def reset_password(datos: RestablecerPasswordRequest):
    """
    Valida el token recibido por correo y actualiza la contraseña.

    - **correo**: correo electrónico de la cuenta
    - **token**: token de 64 caracteres recibido por correo
    - **nueva_password**: nueva contraseña (mínimo 8 caracteres)
    - **confirmar_password**: debe coincidir con nueva_password
    """
    resultado = restablecer_password(
        correo=datos.correo,
        token=datos.token,
        nueva_password=datos.nueva_password,
        confirmar_password=datos.confirmar_password,
    )
    if not resultado["exito"]:
        return JSONResponse(status_code=400, content={"mensaje": resultado["mensaje"]})
    return {"mensaje": resultado["mensaje"]}


@app.get("/auth/users", summary="Listar usuarios registrados")
def list_users():
    """
    Retorna la lista de todos los usuarios registrados.

    No incluye la contraseña.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT user_id, name, email, online, rol_admin, creation_date FROM "user" ORDER BY creation_date DESC'
    )
    cols = [desc[0] for desc in cursor.description]
    rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return {"usuarios": rows}


# ---------------------------------------------------------------------------
# Endpoints de plantas
# ---------------------------------------------------------------------------

@app.get("/plants/user/{user_id}", summary="Consultar plantas del usuario")
def get_plantas_usuario(user_id: int):
    """
    Retorna todas las plantas del usuario y su cantidad.
    Si count == 0, el usuario es nuevo y debe crear su primera planta.
    """
    resultado = contar_plantas_usuario(user_id)
    if not resultado["exito"]:
        return JSONResponse(status_code=500, content={"mensaje": resultado.get("mensaje", "Error interno.")})

    plantas_serializadas = [
        {
            "id_plant":           p.id_plant,
            "plant_name":         p.plant_name,
            "plant_type":         p.plant_type,
            "water_level":        p.water_level,
            "light_level":        p.light_level,
            "humidity_level":     p.humidity_level,
            "health":             p.health,
            "growth_stage":       p.growth_stage,
            "total_care_actions": p.total_care_actions,
            "creation_date_plant": p.creation_date_plant,
            "fk_user_id":         p.fk_user_id,
            "is_dead":            p.is_dead,
        }
        for p in resultado["plantas"]
    ]
    return {
        "count":   resultado["count"],
        "plantas": plantas_serializadas,
        "es_nuevo": resultado["count"] == 0,
    }


@app.post("/plants", summary="Crear nueva planta")
def post_crear_planta(datos: CrearPlantaRequest):
    """
    Crea la primera (o siguiente) planta del usuario.
    Por ahora el único tipo disponible es 'orquidea'.

    - **nombre**: nombre personalizado de la planta
    - **tipo**: tipo de planta (por defecto 'orquidea')
    - **user_id**: ID del usuario dueño
    """
    resultado = crear_planta(PlantaCrear(
        nombre=datos.nombre,
        tipo=datos.tipo,
        fk_user_id=datos.user_id,
    ))
    if not resultado["exito"]:
        return JSONResponse(status_code=400, content={"mensaje": resultado["mensaje"]})

    p = resultado["planta"]
    return {
        "mensaje": resultado["mensaje"],
        "planta": {
            "id_plant":           p.id_plant,
            "plant_name":         p.plant_name,
            "plant_type":         p.plant_type,
            "water_level":        p.water_level,
            "light_level":        p.light_level,
            "humidity_level":     p.humidity_level,
            "health":             p.health,
            "growth_stage":       p.growth_stage,
            "total_care_actions": p.total_care_actions,
            "creation_date_plant": p.creation_date_plant,
            "fk_user_id":         p.fk_user_id,
            "is_dead":            p.is_dead,
        },
    }


@app.post("/plants/{plant_id}/water", summary="Regar la planta")
def post_regar(plant_id: int, datos: RegarRequest):
    """
    Registra un riego sobre la planta.
    El agua efectiva depende del sustrato asignado (water_retention factor).
    El frontend debe mostrar la animación de llenado antes de confirmar esta llamada.
    """
    resultado = regar_planta(plant_id, datos.cantidad_ml)
    if not resultado["exito"]:
        return JSONResponse(status_code=400, content={"mensaje": resultado["mensaje"]})

    p = resultado["planta"]
    return {
        "mensaje": resultado["mensaje"],
        "planta": {
            "id_plant":           p.id_plant,
            "plant_name":         p.plant_name,
            "water_level":        p.water_level,
            "humidity_level":     p.humidity_level,
            "health":             p.health,
            "growth_stage":       p.growth_stage,
            "total_care_actions": p.total_care_actions,
            "substrate_name":     p.substrate_name,
        },
    }


@app.post("/plants/{plant_id}/light", summary="Ajustar intensidad de luz")
def post_luz(plant_id: int, datos: LuzRequest):
    """
    Ajusta la intensidad de la lámpara (0–100).
    Luz > 70% seca el sustrato.
    """
    resultado = ajustar_luz(plant_id, datos.intensidad)
    if not resultado["exito"]:
        return JSONResponse(status_code=400, content={"mensaje": resultado["mensaje"]})

    p = resultado["planta"]
    return {
        "mensaje": resultado["mensaje"],
        "planta": {
            "id_plant":           p.id_plant,
            "plant_name":         p.plant_name,
            "light_level":        p.light_level,
            "humidity_level":     p.humidity_level,
            "health":             p.health,
            "growth_stage":       p.growth_stage,
            "total_care_actions": p.total_care_actions,
        },
    }


@app.post("/plants/{plant_id}/ventilation", summary="Ajustar ventilación ambiental")
def post_ventilacion(plant_id: int, datos: VentilacionRequest):
    """
    Ajusta el nivel de ventilación ambiental de la planta (0–100).
    La ventilación afecta directamente la salud de las raíces.
    Ventilación > 75 genera un leve secado del sustrato.
    """
    resultado = ajustar_ventilacion(plant_id, datos.nivel)
    if not resultado["exito"]:
        return JSONResponse(status_code=400, content={"mensaje": resultado["mensaje"]})

    p = resultado["planta"]
    return {
        "mensaje": resultado["mensaje"],
        "planta": {
            "id_plant":           p.id_plant,
            "plant_name":         p.plant_name,
            "ventilation_level":  p.ventilation_level,
            "water_level":        p.water_level,
            "health":             p.health,
            "growth_stage":       p.growth_stage,
            "total_care_actions": p.total_care_actions,
        },
    }


@app.get("/plants/{plant_id}/status", summary="Consultar estado actual de la planta")
def get_estado(plant_id: int):
    """
    Retorna el estado completo de la planta:
    índices de cuidado (agua, luz, humedad, ventilación), sustrato asignado,
    salud calculada con etiqueta, etapa de crecimiento y alertas activas.
    """
    resultado = obtener_estado(plant_id)
    if not resultado["exito"]:
        status = 404 if "no encontrada" in resultado["mensaje"] else 500
        return JSONResponse(status_code=status, content={"mensaje": resultado["mensaje"]})

    p = resultado["planta"]
    return {
        "planta": {
            "id_plant":            p.id_plant,
            "plant_name":          p.plant_name,
            "plant_type":          p.plant_type,
            "water_level":         p.water_level,
            "light_level":         p.light_level,
            "humidity_level":      p.humidity_level,
            "ventilation_level":   p.ventilation_level,
            "health":              p.health,
            "growth_stage":        p.growth_stage,
            "total_care_actions":  p.total_care_actions,
            "creation_date_plant": p.creation_date_plant,
            "substrate_name":      p.substrate_name,
        },
        "salud_etiqueta":    resultado["salud_etiqueta"],
        "etapa_descripcion": resultado["etapa_descripcion"],
        "alertas":           resultado["alertas"],
    }


# ---------------------------------------------------------------------------
# Endpoints de sustrato
# ---------------------------------------------------------------------------

@app.get("/plants/substrates", summary="Catálogo de tipos de sustrato")
def get_sustratos():
    """
    Lista todos los tipos de sustrato disponibles con su factor de retención de agua.
    """
    resultado = obtener_tipos_sustrato()
    if not resultado["exito"]:
        return JSONResponse(status_code=500, content={"mensaje": resultado.get("mensaje", "Error interno.")})
    return {
        "sustratos": [
            {
                "id_substrate_type": s.id_substrate_type,
                "name":              s.name,
                "description":       s.description,
                "water_retention":   s.water_retention,
                "nutrient_release":  s.nutrient_release,
                "drainage_factor":   s.drainage_factor,
            }
            for s in resultado["sustratos"]
        ]
    }


@app.put("/plants/{plant_id}/substrate", summary="Cambiar sustrato de la planta")
def put_sustrato(plant_id: int, datos: SubstratoRequest):
    """
    Asigna un nuevo tipo de sustrato a la planta.
    El sustrato modifica la absorción efectiva de agua en futuros riegos.
    """
    resultado = asignar_sustrato(plant_id, datos.substrate_type_id)
    if not resultado["exito"]:
        return JSONResponse(status_code=400, content={"mensaje": resultado["mensaje"]})
    s = resultado["sustrato"]
    return {
        "mensaje": resultado["mensaje"],
        "sustrato": {
            "id_substrate_type": s.id_substrate_type,
            "name":              s.name,
            "water_retention":   s.water_retention,
            "drainage_factor":   s.drainage_factor,
        },
    }


# ---------------------------------------------------------------------------
# Endpoints de maceta
# ---------------------------------------------------------------------------

@app.get("/plants/{plant_id}/pot", summary="Consultar maceta de la planta")
def get_maceta(plant_id: int):
    """Retorna la información física de la maceta asociada a la planta."""
    resultado = obtener_maceta(plant_id)
    if not resultado["exito"]:
        status = 404 if "no encontrada" in resultado["mensaje"] else 500
        return JSONResponse(status_code=status, content={"mensaje": resultado["mensaje"]})
    m = resultado["maceta"]
    return {
        "maceta": {
            "id_pot":            m.id_pot,
            "material":          m.material,
            "size_cm":           m.size_cm,
            "drainage_level":    m.drainage_level,
            "ventilation_level": m.ventilation_level,
            "fk_plant_id":       m.fk_plant_id,
        }
    }


@app.put("/plants/{plant_id}/pot", summary="Actualizar propiedades de la maceta")
def put_maceta(plant_id: int, datos: MacetaRequest):
    """
    Actualiza el material, drenaje o ventilación estructural de la maceta.
    Materiales válidos: plastico, ceramica, terracota, vidrio.
    """
    resultado = actualizar_maceta(
        plant_id,
        material=datos.material,
        drainage_level=datos.drainage_level,
        ventilation_level=datos.ventilation_level,
    )
    if not resultado["exito"]:
        return JSONResponse(status_code=400, content={"mensaje": resultado["mensaje"]})
    m = resultado["maceta"]
    return {
        "mensaje": resultado["mensaje"],
        "maceta": {
            "id_pot":            m.id_pot,
            "material":          m.material,
            "size_cm":           m.size_cm,
            "drainage_level":    m.drainage_level,
            "ventilation_level": m.ventilation_level,
        },
    }


# ---------------------------------------------------------------------------
# Endpoints de historial
# ---------------------------------------------------------------------------

@app.get("/plants/{plant_id}/history", summary="Historial de acciones de cuidado")
def get_historial(plant_id: int, limit: int = 50):
    """
    Retorna el historial de acciones de cuidado de la planta, del más reciente al más antiguo.

    - **limit**: cantidad máxima de registros (1–200, por defecto 50)
    """
    resultado = obtener_historial(plant_id, limit)
    if not resultado["exito"]:
        return JSONResponse(status_code=500, content={"mensaje": resultado.get("mensaje", "Error interno.")})
    return {
        "total": resultado["total"],
        "historial": [
            {
                "id_history":   h.id_history,
                "action_type":  h.action_type,
                "value":        h.value,
                "extra_info":   h.extra_info,
                "created_at":   h.created_at,
            }
            for h in resultado["historial"]
        ],
    }


# ---------------------------------------------------------------------------
# Endpoint de demostración: cambio directo de etapa
# ---------------------------------------------------------------------------

# Acciones mínimas necesarias para cada etapa (para ambos tipos de planta)
_ACCIONES_POR_ETAPA: dict[str, int] = {
    "germinacion":         0,
    "enraizamiento":       3,
    "plantula":            8,
    "crecimiento":         15,
    "floracion":           25,
    "fructificacion":      35,
    "vara_floral":         25,
    "botones_florales":    32,
    "crecimiento_botones": 40,
    "apertura_petalos":    50,
}


@app.put("/plants/{plant_id}/stage", summary="[Demo] Cambiar etapa de crecimiento directamente")
def put_etapa(plant_id: int, datos: EtapaRequest):
    """
    **Solo para demostración.** Establece la etapa de crecimiento de la planta
    de forma directa, ajustando también `total_care_actions` al mínimo necesario
    para dicha etapa.

    Etapas válidas (orquídea): germinacion, enraizamiento, plantula, crecimiento,
    vara_floral, botones_florales, crecimiento_botones, apertura_petalos.

    Etapas válidas (general): germinacion, enraizamiento, plantula, crecimiento,
    floracion, fructificacion.
    """
    from plant.growth import DESCRIPCION_ETAPAS

    acciones = _ACCIONES_POR_ETAPA.get(datos.etapa, 0)
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id_plant FROM plant WHERE id_plant = %s",
            (plant_id,),
        )
        if cursor.fetchone() is None:
            return JSONResponse(status_code=404, content={"mensaje": "Planta no encontrada."})

        cursor.execute(
            """
            UPDATE plant
            SET growth_stage = %s, total_care_actions = %s
            WHERE id_plant = %s
            """,
            (datos.etapa, acciones, plant_id),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "mensaje": f"Etapa cambiada a '{datos.etapa}'.",
        "etapa": datos.etapa,
        "etapa_descripcion": DESCRIPCION_ETAPAS[datos.etapa],
        "total_care_actions": acciones,
    }
