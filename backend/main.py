"""
Punto de entrada de la API REST.

Correr con:
    uvicorn backend.main:app --reload

Documentación interactiva disponible en:
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
import re

from auth.register import registrar_usuario
from auth.models import UsuarioRegistro
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
            "creado": u.creado,
        },
    }


@app.get("/auth/users", summary="Listar usuarios registrados")
def list_users():
    """
    Retorna la lista de todos los usuarios registrados.

    No incluye la contraseña.
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, nombre, correo, creado FROM usuarios ORDER BY creado DESC"
    ).fetchall()
    conn.close()
    return {"usuarios": [dict(row) for row in rows]}
