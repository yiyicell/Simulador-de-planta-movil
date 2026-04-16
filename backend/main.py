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

from auth.login import autenticar_usuario
from auth.register import registrar_usuario
from auth.logout import cerrar_sesion
from auth.models import UsuarioLogin, UsuarioRegistro
from database import init_db, get_connection

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


# ---------------------------------------------------------------------------
# Eventos de ciclo de vida
# ---------------------------------------------------------------------------

@app.on_event("startup")
def startup():
    """Crea las tablas si no existen al iniciar el servidor."""
    init_db()


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
