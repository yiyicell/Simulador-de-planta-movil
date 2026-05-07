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
    online: bool
    rol_admin: bool
    creado: str


@dataclass
class SolicitudRecuperacion:
    """Correo al que se enviará el token de recuperación."""
    correo: str


@dataclass
class RestablecerPassword:
    """Datos que el usuario envía para cambiar su contraseña."""
    correo: str
    token: str
    nueva_password: str
    confirmar_password: str
