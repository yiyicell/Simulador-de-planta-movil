"""
Modelos de datos para el módulo de autenticación.
Se usan dataclasses para representar los datos sin depender aún de FastAPI/Pydantic.
Cuando se integre FastAPI, estos se reemplazarán por modelos Pydantic (BaseModel).
"""

from dataclasses import dataclass


@dataclass
class UsuarioRegistro:
    """Datos que llegan al endpoint de registro."""
    nombre: str
    correo: str
    password: str


@dataclass
class UsuarioLogin:
    """Credenciales que llegan al endpoint de inicio de sesión."""
    correo: str
    password: str


@dataclass
class UsuarioRespuesta:
    """Datos públicos del usuario que se devuelven (sin password)."""
    id: int
    nombre: str
    correo: str
    creado: str
