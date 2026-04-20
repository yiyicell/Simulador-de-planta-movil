# Simulador de Planta Móvil

Proyecto académico para **Ingeniería de Software I** — Universidad Antonio Nariño.

Sistema compuesto por un backend REST en **FastAPI** conectado a **PostgreSQL**, y una aplicación móvil en **React Native / Expo**.

---

## Estructura del proyecto

```
├── backend/                  # API REST (FastAPI + PostgreSQL)
│   ├── main.py               # Punto de entrada, definición de endpoints
│   ├── database.py           # Conexión y creación de tablas (psycopg2)
│   ├── tunnel.py             # Túnel público con ngrok (desarrollo)
│   ├── requirements.txt      # Dependencias Python
│   ├── .env                  # Credenciales PostgreSQL (no versionar)
│   └── auth/
│       ├── models.py         # Modelos Pydantic (Usuario, respuestas)
│       ├── register.py       # Lógica de registro
│       ├── login.py          # Lógica de autenticación
│       └── logout.py         # Lógica de cierre de sesión
├── mobile-app/               # Aplicación Expo (React Native + TypeScript)
│   └── app/
│       ├── index.tsx         # Pantalla de bienvenida
│       ├── login.tsx         # Pantalla de inicio de sesión
│       ├── register.tsx      # Pantalla de registro
│       └── (tabs)/           # Navegación con pestañas (home, etc.)
├── examples/
│   ├── registro_usuarios.ipynb      # Demo de registro vía API
│   └── demo_login_logout.ipynb      # Demo de login / logout
└── iniciar_backend_y_tunel.bat      # Script para levantar backend + ngrok
```

---

## Base de datos

PostgreSQL remoto (accedido vía **Tailscale**).

| Campo             | Tipo         | Descripción                          |
|-------------------|-------------|--------------------------------------|
| `user_id`         | SERIAL PK   | Identificador único                  |
| `name`            | VARCHAR(50) | Nombre del usuario                   |
| `email`           | TEXT        | Correo electrónico                   |
| `hashed_password` | TEXT        | Contraseña hasheada con bcrypt       |
| `online`          | BOOLEAN     | `true` luego del login, `false` tras logout |
| `rol_admin`       | BOOLEAN     | `true` si tiene permisos de administrador |
| `creation_date`   | DATE        | Fecha de creación del registro       |

Configurar las credenciales en `backend/.env`:

```env
PG_HOST=<ip_tailscale>
PG_PORT=5432
PG_DATABASE=Plantastic
PG_USER=postgres
PG_PASSWORD=<contraseña>
```

---

## Endpoints de la API

| Método | Ruta                        | Descripción                                      |
|--------|-----------------------------|--------------------------------------------------|
| POST   | `/auth/register`            | Registra un nuevo usuario                        |
| POST   | `/auth/login`               | Autentica al usuario y marca `online = true`     |
| POST   | `/auth/logout/{user_id}`    | Cierra la sesión y marca `online = false`        |
| GET    | `/auth/users`               | Lista todos los usuarios (sin contraseña)        |

Documentación interactiva disponible en `http://localhost:8000/docs` con el servidor corriendo.

---

## Instalación y ejecución del backend

```bash
# 1. Crear y activar entorno virtual
python -m venv .venv313
.venv313\Scripts\activate

# 2. Instalar dependencias
pip install -r backend/requirements.txt

# 3. Levantar servidor (desde la raíz del proyecto)
uvicorn backend.main:app --reload
```

O usar el script que también abre el túnel ngrok:

```bat
iniciar_backend_y_tunel.bat
```

---

## Aplicación móvil

```bash
cd mobile-app
npm install
npx expo start
```

---

## Tecnologías

| Capa       | Tecnología                        |
|------------|-----------------------------------|
| Backend    | Python 3.13, FastAPI, psycopg2    |
| Base datos | PostgreSQL (Tailscale)            |
| Móvil      | React Native, Expo, TypeScript    |
| Seguridad  | bcrypt (hash de contraseñas)      |
| Túnel dev  | ngrok                             |

