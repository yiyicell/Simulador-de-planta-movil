# Simulador de Planta Móvil

Proyecto académico para **Ingeniería de Software I** — Universidad Antonio Nariño.

Sistema compuesto por un backend REST en **FastAPI** conectado a **PostgreSQL**, y una aplicación móvil en **React Native / Expo**.

---

## Estructura del proyecto

```
├── backend/                  # API REST (FastAPI + PostgreSQL)
│   ├── main.py               # Punto de entrada, definición de endpoints
│   ├── database.py           # Conexión y creación de tablas (psycopg2)
│   ├── economy.py            # Lógica de economía, tienda e inventario
│   ├── tunnel.py             # Túnel público con localhost.run (desarrollo)
│   ├── requirements.txt      # Dependencias Python
│   ├── .env                  # Credenciales PostgreSQL (no versionar)
│   ├── auth/
│   │   ├── models.py         # Modelos Pydantic (Usuario, respuestas)
│   │   ├── register.py       # Lógica de registro
│   │   ├── login.py          # Lógica de autenticación
│   │   ├── logout.py         # Lógica de cierre de sesión
│   │   └── password_reset.py # Recuperación de contraseña
│   └── plant/
│       ├── models.py         # Modelos de planta
│       ├── growth.py         # Reglas de salud, etapas y umbrales
│       ├── decay.py          # Decaimiento automático (APScheduler)
│       ├── create.py         # Crear y listar plantas
│       ├── care.py           # Cuidados: riego, luz, ventilación
│       ├── status.py         # Estado completo de la planta
│       ├── substrate.py      # Catálogo de sustratos
│       ├── pot.py            # Maceta
│       └── history.py        # Historial de cuidados
├── mobile-app/               # Aplicación Expo (React Native + TypeScript)
│   └── app/
│       ├── index.tsx         # Pantalla de bienvenida
│       ├── login.tsx         # Pantalla de inicio de sesión
│       ├── register.tsx      # Pantalla de registro
│       └── (tabs)/           # Navegación con pestañas (home, etc.)
├── examples/
│   ├── registro_usuarios.ipynb       # Demo de registro vía API
│   ├── demo_login_logout.ipynb       # Demo de login / logout
│   ├── pipeline_cuidado_planta.ipynb # Demo de ciclo de cuidados
│   ├── visualizar_etapas.ipynb       # Demo de etapas de crecimiento
│   └── economia_y_tienda.ipynb       # Demo de coins, tienda e inventario
└── iniciar_backend_y_tunel.bat       # Script para levantar backend + túnel
```

---

## Base de datos

PostgreSQL remoto (accedido vía **Tailscale**).

### Tabla `user`

| Campo             | Tipo         | Descripción                                    |
|-------------------|--------------|------------------------------------------------|
| `user_id`         | SERIAL PK    | Identificador único                            |
| `name`            | VARCHAR(50)  | Nombre del usuario                             |
| `email`           | TEXT         | Correo electrónico                             |
| `hashed_password` | TEXT         | Contraseña hasheada con bcrypt                 |
| `online`          | BOOLEAN      | `true` tras login, `false` tras logout         |
| `rol_admin`       | BOOLEAN      | `true` si tiene permisos de administrador      |
| `creation_date`   | DATE         | Fecha de creación del registro                 |
| `coins`           | BIGINT       | Saldo de Plantastic Coins (default 0)          |

### Tabla `plant`

| Campo          | Tipo    | Descripción                            |
|----------------|---------|----------------------------------------|
| `plant_id`     | SERIAL PK | Identificador único                  |
| `fk_user_id`   | FK      | Usuario propietario                    |
| `water_level`  | REAL    | Nivel de agua (0–100 %)                |
| `light_level`  | REAL    | Nivel de luz (0–100 %)                 |
| `humidity_level` | REAL  | Humedad (0–100 %)                      |
| `ventilation_level` | REAL | Ventilación (0–100 %)               |
| `health`       | REAL    | Salud global (0–100 %)                 |
| `growth_stage` | TEXT    | Etapa de crecimiento                   |
| `is_dead`      | BOOLEAN | `true` si la planta murió              |

### Tabla `shop_item`

| Campo         | Tipo    | Descripción                                    |
|---------------|---------|------------------------------------------------|
| `id_item`     | SERIAL PK | Identificador único                          |
| `item_name`   | TEXT UNIQUE | Nombre del ítem                            |
| `item_type`   | TEXT    | Categoría: `maceta`, `fondo`, `decoracion`     |
| `price_coins` | INTEGER | Precio en Plantastic Coins                     |
| `rarity`      | TEXT    | Rareza: `common`, `rare`, `epic`               |
| `active`      | BOOLEAN | `true` si está disponible en tienda            |

### Tabla `user_inventory`

| Campo         | Tipo    | Descripción                          |
|---------------|---------|--------------------------------------|
| `fk_user_id`  | FK      | Usuario propietario                  |
| `fk_item_id`  | FK      | Ítem comprado                        |
| `quantity`    | INTEGER | Cantidad acumulada                   |
| `acquired_at` | TIMESTAMP | Fecha de primera adquisición       |

### Tabla `coin_transaction`

| Campo              | Tipo    | Descripción                                |
|--------------------|---------|--------------------------------------------|
| `id`               | SERIAL PK | Identificador único                      |
| `fk_user_id`       | FK      | Usuario involucrado                        |
| `amount`           | INTEGER | Monto (positivo = crédito, negativo = débito) |
| `movement_type`    | TEXT    | `credito` o `debito`                       |
| `reason`           | TEXT    | Motivo del movimiento                      |
| `related_plant_id` | FK      | Planta relacionada (si aplica)             |
| `related_item_id`  | FK      | Ítem relacionado (si aplica)               |
| `created_at`       | TIMESTAMP | Fecha del movimiento                     |

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

### Autenticación

| Método | Ruta                           | Descripción                                   |
|--------|--------------------------------|-----------------------------------------------|
| POST   | `/auth/register`               | Registra un nuevo usuario                     |
| POST   | `/auth/login`                  | Autentica al usuario                          |
| POST   | `/auth/logout/{user_id}`       | Cierra la sesión                              |
| GET    | `/auth/users`                  | Lista todos los usuarios                      |
| POST   | `/auth/password-reset/request` | Solicita recuperación de contraseña           |
| POST   | `/auth/password-reset/confirm` | Confirma nueva contraseña con token           |

### Planta

| Método | Ruta                           | Descripción                                   |
|--------|--------------------------------|-----------------------------------------------|
| POST   | `/plants`                      | Crear nueva planta                            |
| GET    | `/plants/user/{user_id}`       | Listar plantas vivas de un usuario            |
| GET    | `/plants/{plant_id}/status`    | Estado completo de la planta                  |
| POST   | `/plants/{plant_id}/water`     | Regar la planta                               |
| POST   | `/plants/{plant_id}/light`     | Ajustar la luz                                |
| POST   | `/plants/{plant_id}/ventilation` | Ajustar la ventilación                      |
| GET    | `/plants/{plant_id}/history`   | Historial de cuidados                         |
| GET    | `/plants/substrates`           | Catálogo de sustratos disponibles             |
| GET    | `/plants/{plant_id}/pot`       | Información de maceta                         |

### Economía

| Método | Ruta                              | Descripción                                |
|--------|-----------------------------------|--------------------------------------------|
| GET    | `/economy/users/{user_id}/wallet` | Consultar saldo de Plantastic Coins        |

### Tienda

| Método | Ruta                              | Descripción                                |
|--------|-----------------------------------|--------------------------------------------|
| GET    | `/shop/items`                     | Listar ítems activos (filtro por tipo)     |
| POST   | `/shop/purchase`                  | Comprar un ítem (valida saldo)             |
| GET    | `/shop/users/{user_id}/inventory` | Ver inventario del usuario                 |

### Notas importantes (economia + planta)

- El endpoint `GET /plants/{plant_id}/status` devuelve los valores de cuidado dentro de `planta`, no en la raiz del JSON.
- Campos reales de estado: `water_level`, `light_level`, `humidity_level`, `ventilation_level`, `health`.
- Payloads correctos de cuidado:
	- `POST /plants/{plant_id}/water` -> `{ "cantidad_ml": <numero> }`
	- `POST /plants/{plant_id}/light` -> `{ "intensidad": <numero> }`
	- `POST /plants/{plant_id}/ventilation` -> `{ "nivel": <numero> }`
- Para ganar `coins_ganadas` por cuidado optimo se deben cumplir todas al mismo tiempo:
	- `water_level` entre 40 y 80
	- `light_level` entre 40 y 80
	- `humidity_level` entre 40 y 70
	- `ventilation_level` entre 30 y 70
	- `health >= 80`
- Si falla al menos una condicion, `coins_ganadas` sera `0`.

Documentación interactiva disponible en `http://localhost:8000/docs` con el servidor corriendo.

---

## Instalación y ejecución del backend

```bash
# 1. Instalar dependencias (Python 3.13)
pip install -r backend/requirements.txt

# 2. Configurar credenciales
# Crear backend/.env con los valores de la DB

# 3. Levantar servidor con túnel público
iniciar_backend_y_tunel.bat
```

El script abre dos ventanas:
- **Backend Uvicorn** — API corriendo en `http://127.0.0.1:8000`
- **LocalTunnel** — URL pública para conectar desde el celular (ej. `https://xxxx.loca.lt`)

---

## Aplicación móvil

```bash
cd mobile-app
npm install
npx expo start
```

---

## Tecnologías

| Capa       | Tecnología                                     |
|------------|------------------------------------------------|
| Backend    | Python 3.13, FastAPI, psycopg2                 |
| Base datos | PostgreSQL (Tailscale)                         |
| Móvil      | React Native, Expo, TypeScript                 |
| Seguridad  | bcrypt (hash de contraseñas)                   |
| Scheduler  | APScheduler (decaimiento automático de planta) |
| Túnel dev  | localhost.run (SSH, sin instalación)           |

