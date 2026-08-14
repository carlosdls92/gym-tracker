# CLAUDE.md — gym-tracker

## Stack y puertos

| Componente | Detalle |
|---|---|
| Runtime | Python 3.12 / FastAPI / Uvicorn |
| Puerto | **:8095** |
| Base de datos | MongoDB `gym_tracker` (Motor async) |
| Contenedor | Docker — imagen `python:3.12-slim` |

La app corre en `http://192.168.0.23:8095/` en el servidor omvdls.

## Estructura de ficheros

```
app/
├── main.py           # FastAPI app, todos los endpoints, lógica offline HTML
├── seed.py           # EXERCISES, PLANS, WORKOUT_DAYS + seed idempotente
├── offline_app.js    # JS embebido en el HTML offline (no se sirve como estático)
└── static/
    ├── index.html    # Shell SPA — solo tabs-bar y #root, sin contenido hardcodeado
    ├── app.js        # Toda la lógica frontend: selector de planes, tabs, cards, progreso
    └── day.css       # Estilos — dark theme, Bebas Neue + DM Sans vía Google Fonts
```

## MongoDB — colecciones

### `exercises`
```json
{
  "_id": "press-pecho",
  "name": "Press de pecho",
  "type": "regular",          // "regular" | "cardio"
  "muscle_badge": "Pectorales",
  "technique": "...",
  "tags": ["Barra", "Compuesto"],
  "meta": null,               // solo en cardio
  "duration": null,           // solo en cardio (ej. "12'")
  "gifs": [
    {"label": "Movimiento", "accent": false},
    {"label": "Variante",   "accent": true}
  ],
  "gif_data": [Binary, Binary]   // bytes del GIF — NO incluir en respuestas API
}
```

### `workout_plans`
```json
{"_id": "iniciacion", "name": "Iniciación", "sort_order": 1}
```
Planes existentes: `iniciacion`, `hipertrofia-5`.

### `workout_days`
```json
{
  "plan": "hipertrofia-5",
  "day_num": 1,
  "day_label": "L",
  "title": "PECHO Y TRÍCEPS",
  "subtitle": "Pectorales · Tríceps · Hombro anterior",
  "muscle_tags": ["Pectorales", "Tríceps"],
  "has_cardio": false,
  "total": 8,
  "exercises": [
    {"id": "press-pecho", "sets": 4, "reps": "8"},
    {"id": "extension-v", "sets": 4, "reps": "15"}
  ]
}
```
El campo `exercises` es siempre un array de objetos `{id, sets, reps}` (nunca strings planos desde la última migración; el API soporta ambos formatos por compatibilidad).

## Endpoints

| Ruta | Descripción |
|---|---|
| `GET /` | Sirve `app/static/index.html` |
| `GET /api/plans` | Lista planes con días (sin gif_data) |
| `GET /api/plan/{slug}/day/{n}` | Día n del plan — incluye `sets` y `reps` en cada ejercicio |
| `GET /api/plan/{slug}/offline` | HTML auto-contenido con GIFs en base64 para uso offline |
| `GET /api/gif/{exercise_id}/{index}` | Binario GIF, caché 7 días |

## Seed — reglas importantes

`seed_if_empty()` se llama en el lifespan de FastAPI (bloquea el arranque hasta completar):

1. Busca los IDs de ejercicios ya en la colección.
2. Solo descarga GIFs para ejercicios **nuevos** (los que no están en la colección).
3. Hace `replace_one(..., upsert=True)` en `workout_plans` y `workout_days` — siempre actualiza.
4. Los GIFs se descargan del CDN `https://cdn.jsdelivr.net/gh/JahelCuadrado/ExerciseGymGifsDB@v1.1.0/`.

Para añadir un plan nuevo o modificar días existentes: editar `seed.py` y reiniciar el contenedor. Los días se reescriben automáticamente vía upsert.

Para añadir ejercicios nuevos: añadir a la lista `EXERCISES` en `seed.py`. Si el ejercicio ya está en MongoDB (mismo `_id`), no se re-descarga.

Si hay que re-descargar un ejercicio existente (path de GIF erróneo): borrar ese documento de MongoDB y reiniciar el contenedor.

## Frontend — flujo SPA

```
Arranque
  └── init() en app.js
        ├── Si localStorage tiene gym-last-plan + gym-last-day → carga ese plan/día
        └── Si no → showPlanSelector()

showPlanSelector()
  └── GET /api/plans
        └── renderiza plan cards con botón ↓ (descarga offline)

selectPlan(slug)
  └── renderTabs(slug, days)  ← inyecta en #tabs-bar: ← + día1..N + ↓
  └── loadDay(slug, days[0].day_num)

loadDay(plan, dayNum)
  └── GET /api/plan/{plan}/day/{dayNum}
        └── renderDay(data) → inyecta en #root
```

El progreso se guarda en `localStorage` con clave `gym-p-{plan}-{day}` como array JSON de IDs completados.

## Modo offline

El endpoint `GET /api/plan/{slug}/offline` genera un único fichero HTML (~20 MB) que contiene:

- CSS de `day.css` inlineado, con Google Fonts reemplazados por fuentes del sistema.
- Variables JS: `PLAN_NAME`, `PLAN_SLUG`, `DAYS` (JSON), `GIFS` (base64 data URIs).
- El fichero `app/offline_app.js` embebido tal cual.

El JS offline usa las mismas claves de `localStorage` que el online, por lo que el progreso es compartido entre ambas versiones.

**No editar** `app/offline_app.js` sin entender que es idéntico funcionalmente a `app/static/app.js` pero sin fetch ni plan selector. Cualquier cambio de lógica que afecte a ambas versiones debe duplicarse.

## Variables de entorno

```env
MONGODB_URL=mongodb://admin:admin@host.docker.internal:27017/gym_tracker?authSource=admin
```

El docker-compose tiene este valor como default. En producción se inyecta vía `.env` en el servidor.

## Deploy

Workflow: `.github/workflows/deploy.yml` — solo `workflow_dispatch`, nunca push trigger.

El deploy hace:
1. `rsync` del código al servidor (excluyendo `.git`, `__pycache__`, `.pyc`).
2. `docker compose down --remove-orphans`
3. `docker compose build --no-cache`
4. `docker compose up -d`
5. Health check: `curl http://localhost:8095/` hasta 40 intentos × 5s.

El runner se llama `omv` y está en el servidor omvdls. El seed puede tardar varios minutos la primera vez (descarga de GIFs), el health check lo tiene en cuenta.

## Reglas de código

- No añadir endpoints sin actualizar esta documentación y el README.
- El campo `gif_data` nunca debe incluirse en respuestas JSON de la API — eliminarlo siempre con `ex.pop("gif_data", None)` o no proyectarlo en la query.
- Los ejercicios de tipo `cardio` no tienen panel de técnica expandible — ver `buildCardioCard` vs `buildExCard`.
- Los GIFs del CDN a veces no existen en `v1.1.0`. Si un path da 404, se almacena `b""` en MongoDB. Corregir el path en `seed.py`, borrar el documento de MongoDB y reiniciar.
- El campo `sets` en los dots de la UI es dinámico — viene del API, no está hardcodeado.
