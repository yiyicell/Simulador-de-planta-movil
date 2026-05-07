# Backend — Simulador de Planta Móvil

API REST construida con **FastAPI + PostgreSQL**.  
Corre con `uvicorn backend.main:app --reload` desde la raíz del proyecto.

---

## Estructura del módulo `plant/`

```
backend/plant/
├── models.py      # Dataclasses (PlantaRespuesta, AccionRiego, Maceta, …)
├── growth.py      # Reglas de salud, etapas y umbrales críticos
├── decay.py       # Decaimiento automático con el tiempo real (APScheduler)
├── create.py      # Crear planta y listar plantas vivas del usuario
├── care.py        # Acciones: regar, ajustar luz, ajustar ventilación
├── status.py      # Consulta del estado completo de una planta
├── substrate.py   # Catálogo de sustratos y asignación
├── pot.py         # Maceta: consulta y actualización
└── history.py     # Historial de acciones de cuidado
```

---

## Ciclo de vida de una planta

```
CREAR → [viva, germinación] ──cuidados──► etapas de crecimiento
                                │
                          sin cuidados
                                │
                         decay automático
                          (cada 5 min)
                                │
                       salud ≤ 20 → MUERTA
                                │
                        usuario crea nueva planta
```

---

## Factores de cuidado

Cada planta tiene cuatro indicadores (0–100 %) que determinan su salud.

### Agua (`water_level`)

| Zona | Rango | Efecto |
|------|-------|--------|
| Óptima | 40 – 80 % | Salud = 100 pts para este factor |
| Sub-óptima baja | 20 – 40 % | Marchitamiento de hojas, estrés radicular |
| Sub-óptima alta | 80 – 90 % | Riesgo de encharcamiento |
| Crítica baja | < 10 % | **Penalización severa: salud total × 0.35** |
| Crítica alta | > 95 % | **Penalización severa: salud total × 0.50** |

> La penalización crítica baja simula que sin agua la planta no puede realizar fotosíntesis ni absorber nutrientes, independientemente de los demás factores.

### Luz (`light_level`)

| Zona | Rango | Efecto |
|------|-------|--------|
| Óptima | 30 – 70 % | Salud = 100 pts para este factor |
| Sub-óptima baja | 15 – 30 % | Etiolación del tallo, hojas pálidas |
| Sub-óptima alta | 70 – 85 % | Desecación acelerada del sustrato |
| Crítica baja | < 5 % | Salud = 0 pts para este factor |
| Crítica alta | > 90 % | Quemaduras en hojas, salud = 0 pts |

> **Efecto sobre el decay:** cada punto de luz por encima de 70 % acelera la evaporación del agua (+0.002 pts/intervalo) y de la humedad (+0.001 pts/intervalo).

### Humedad (`humidity_level`)

| Zona | Rango | Efecto |
|------|-------|--------|
| Óptima | 50 – 80 % | Salud = 100 pts para este factor |
| Sub-óptima baja | 30 – 50 % | Raíces deshidratadas, hojas enrolladas |
| Sub-óptima alta | 80 – 92 % | Riesgo de pudrición fúngica |
| Crítica baja | < 20 % | Salud = 0 pts para este factor |
| Crítica alta | > 92 % | Pudrición fúngica radical |

### Ventilación (`ventilation_level`)

| Zona | Rango | Efecto |
|------|-------|--------|
| Óptima | 40 – 75 % | Salud = 100 pts para este factor |
| Crítica baja | < 10 % | Raíces sin oxígeno, pudrición radicular |
| Crítica alta | > 95 % | Sustrato se seca demasiado rápido |

---

## Fórmula de salud

```
salud = agua×35% + luz×25% + humedad×25% + ventilación×15%

Si agua ≤ 10%  → salud × 0.35   (deshidratación severa)
Si agua ≥ 95%  → salud × 0.50   (encharcamiento severo)
```

Cada factor aporta entre 0 y 100 puntos según su posición relativa a los rangos:
- Dentro del óptimo → 100 pts
- En zona de peligro → interpolación lineal 0–50 pts
- En zona crítica → 0 pts

### Etiquetas de salud

| Valor | Etiqueta |
|-------|---------|
| ≥ 80 | Excelente |
| 60–79 | Buena |
| 40–59 | Regular |
| 20–39 | Muy baja |
| < 20 | Crítica |

---

## Etapas de crecimiento

Las etapas avanzan según `total_care_actions` (acciones de cuidado acumuladas).  
La salud penaliza las acciones efectivas que se cuentan:

| Salud | Acciones efectivas |
|-------|--------------------|
| ≥ 50 % | 100 % (crecimiento normal) |
| 30–49 % | 60 % (crecimiento lento) |
| < 30 % | 25 % (crecimiento revertido) |

### Orquídea

| Acciones mín. | Etapa | Descripción |
|--------------|-------|-------------|
| 0 | `germinacion` | La semilla ha germinado. La planta está iniciando su vida. |
| 3 | `enraizamiento` | Se están formando las primeras raíces y un pequeño tallo. |
| 8 | `plantula` | La plántula ha desarrollado sus primeras hojas. |
| 15 | `crecimiento` | La planta crece en altura y fortaleza. |
| 25 | `vara_floral` | La orquídea ha generado una vara floral. |
| 32 | `botones_florales` | Los botones florales han aparecido en la vara. |
| 40 | `crecimiento_botones` | Los botones florales están creciendo y madurando. |
| 50 | `apertura_petalos` | ¡Los pétalos se están abriendo! La orquídea está en plena floración. |

### General (otras plantas)

| Acciones mín. | Etapa |
|--------------|-------|
| 0 | `germinacion` |
| 3 | `enraizamiento` |
| 8 | `plantula` |
| 15 | `crecimiento` |
| 25 | `floracion` |
| 35 | `fructificacion` |

---

## Decaimiento automático con el tiempo real

El servidor ejecuta `calcular_decaimiento()` cada **5 minutos** usando APScheduler.  
El cálculo es proporcional al tiempo real transcurrido, así que si el servidor se reinicia recalcula correctamente al volver.

### Tasas base (sustrato mixto, luz óptima)

| Recurso | Decay / intervalo (5 min) | Decay / hora | Decay / día |
|---------|--------------------------|-------------|-------------|
| Agua | −0.030 pts | −0.36 pts | −8.6 pts |
| Humedad | −0.020 pts | −0.24 pts | −5.8 pts |

### Modificadores del decay

| Condición | Efecto |
|-----------|--------|
| Sustrato con alta retención (`water_retention > 1`) | Agua decae más lento (`decay ÷ water_retention`) |
| Luz > 70 % | +0.002 pts agua + 0.001 pts humedad por cada % de luz por encima de 70, por intervalo |
| Agua ≤ 20 % (sequía) | +0.030 pts humedad extra / intervalo |
| Agua > 90 % (encharcamiento) | +0.100 pts agua extra / intervalo (drenaje natural) |

### Tiempo de vida sin ningún cuidado (agua inicial = 30)

| Sustrato | `water_retention` | Muerte aproximada |
|----------|--------------------|-------------------|
| Perlita  | 0.5× | ~2.1 días |
| Corteza  | 0.7× | ~2.9 días |
| Mixto    | 1.0× | ~3.5 días |
| Musgo sphagnum | 1.5× | ~5.2 días |

### Muerte

Cuando `calcular_salud()` devuelve un valor **≤ 20**, la planta se marca como:
```
is_dead       = TRUE
growth_stage  = 'muerta'
health        = 0
```

La planta **no** vuelve a ser actualizada por el scheduler ni aparece en el listado activo del usuario (`GET /plants/user/{id}`). El usuario debe crear una nueva planta para continuar.

---

## Sustratos

El sustrato afecta la cantidad de agua que absorbe la planta por cada acción de riego y la velocidad de secado.

| Sustrato | `water_retention` | `drainage_factor` | Uso recomendado |
|----------|-------------------|-------------------|-----------------|
| `perlita` | 0.5× | 1.8 | Drenaje máximo, difícil encharcar |
| `corteza` | 0.7× | 1.4 | Ideal para orquídeas (drenaje rápido) |
| `mixto`   | 1.0× | 1.0 | Uso general, equilibrado |
| `musgo_sphagnum` | 1.5× | 0.6 | Alta retención — cuidado con exceso de riego |

---

## Maceta

La maceta tiene propiedades físicas independientes del sustrato:

| Campo | Descripción | Valores posibles |
|-------|-------------|-----------------|
| `material` | Material de la maceta | `plastico`, `ceramica`, `terracota`, `vidrio` |
| `size_cm` | Diámetro en cm | 15 (único por ahora) |
| `drainage_level` | Capacidad de drenaje estructural | 0–100 |
| `ventilation_level` | Ventilación física (huecos) | 0–100 |

---

## Endpoints principales del módulo plant

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/plants` | Crear nueva planta |
| `GET` | `/plants/user/{user_id}` | Listar plantas vivas del usuario |
| `GET` | `/plants/{plant_id}/status` | Estado completo (salud, etapa, alertas, is_dead) |
| `POST` | `/plants/{plant_id}/water` | Regar la planta |
| `POST` | `/plants/{plant_id}/light` | Ajustar intensidad de luz |
| `POST` | `/plants/{plant_id}/ventilation` | Ajustar ventilación ambiental |
| `GET` | `/plants/substrates` | Catálogo de sustratos |
| `PUT` | `/plants/{plant_id}/substrate` | Asignar sustrato |
| `GET` | `/plants/{plant_id}/pot` | Ver maceta |
| `PUT` | `/plants/{plant_id}/pot` | Actualizar maceta |
| `GET` | `/plants/{plant_id}/history` | Historial de acciones |

### Respuesta de estado (`GET /plants/{id}/status`)

```json
{
  "exito": true,
  "mensaje": "Estado obtenido correctamente.",
  "planta": {
    "id_plant": 1,
    "plant_name": "Orquídea Dendrobium",
    "water_level": 55.0,
    "light_level": 50.0,
    "humidity_level": 65.0,
    "ventilation_level": 55.0,
    "health": 91.25,
    "growth_stage": "enraizamiento",
    "total_care_actions": 4,
    "is_dead": false
  },
  "salud_etiqueta": "Excelente",
  "etapa_descripcion": "Se están formando las primeras raíces y un pequeño tallo.",
  "alertas": []
}
```

Cuando la planta ha muerto:

```json
{
  "exito": true,
  "mensaje": "La planta ha muerto.",
  "planta": {
    "health": 0,
    "growth_stage": "muerta",
    "is_dead": true
  },
  "salud_etiqueta": "Muerta",
  "alertas": ["💀 Esta planta ha muerto. Debes crear una nueva planta."]
}
```

---

## Condiciones óptimas para el buen desarrollo

Para que una orquídea alcance `apertura_petalos` (50 acciones efectivas):

| Factor | Valor recomendado | Motivo |
|--------|------------------|--------|
| Agua | 50–70 % | Centro del rango óptimo, margen seguro |
| Luz | 40–60 % | Evita desecación sin privar de luz |
| Humedad | 60–75 % | Ambiente húmedo sin encharcamiento fúngico |
| Ventilación | 50–65 % | Oxigena raíces sin secar demasiado |
| Sustrato | `corteza` | Drena rápido, evita encharcamiento crónico |
| Maceta | `terracota` | Transpira, regula temperatura de raíces |

Con estas condiciones la planta mantiene **salud ≥ 80** ("Excelente") de forma estable y alcanza `apertura_petalos` con ~50 acciones de cuidado bien distribuidas.
