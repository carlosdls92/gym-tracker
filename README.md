# gym-tracker

App web de seguimiento de entrenamiento para uso personal. Permite cargar planes de entrenamiento con ejercicios, ver GIFs de técnica y marcar el progreso por sesión.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12 / FastAPI / Uvicorn |
| Base de datos | MongoDB (Motor async) |
| Frontend | HTML + CSS + JS vanilla (SPA) |
| Contenedor | Docker / Docker Compose |
| CI/CD | GitHub Actions (self-hosted runner en omvdls) |

## Estructura

```
gym-tracker/
├── app/
│   ├── main.py           # FastAPI app + endpoints
│   ├── seed.py           # Catálogo de ejercicios y planes + seed de MongoDB
│   ├── offline_app.js    # JS auto-contenido embebido en HTML offline
│   └── static/
│       ├── index.html    # SPA shell
│       ├── app.js        # Lógica frontend (selector de planes, tabs, cards)
│       └── day.css       # Estilos
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .github/workflows/deploy.yml
```

## Planes de entrenamiento

### Iniciación (3 días)
Plan full-body para principiantes. Cada ejercicio: 4×12.

| Día | Grupos musculares |
|---|---|
| DÍA 1 | Cuádriceps · Espalda baja · Pecho · Dorsal · Hombros · Bíceps · Tríceps · Core |
| DÍA 2 | Femoral · Cuádriceps · Espalda · Pecho · Hombros · Bíceps · Tríceps · Core |
| DÍA 3 | Aductores · Abductores · Glúteos · Pecho · Espalda · Brazos |

### Hipertrofia 5 (5 días L/M/X/J/V)
Split por grupos musculares con series y repeticiones variables.

| Día | Grupos musculares |
|---|---|
| L | Pecho + Tríceps |
| M | Espalda + Bíceps |
| X | Hombros |
| J | Piernas (Cuádriceps) |
| V | Posterior (Isquiotibiales + Glúteos) |

## API

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | SPA (index.html) |
| `GET` | `/api/plans` | Lista de planes con días |
| `GET` | `/api/plan/{slug}/day/{n}` | Datos del día n del plan |
| `GET` | `/api/plan/{slug}/offline` | HTML auto-contenido para uso offline |
| `GET` | `/api/gif/{exercise_id}/{index}` | GIF del ejercicio (7 días de caché) |

## MongoDB

Base de datos: `gym_tracker`

| Colección | Descripción |
|---|---|
| `exercises` | Ejercicios con datos binarios de GIF (`gif_data`) |
| `workout_plans` | Planes (`iniciacion`, `hipertrofia-5`) |
| `workout_days` | Días de cada plan con referencias a ejercicios, sets y reps |

El campo `exercises` en `workout_days` usa el formato:
```json
[{"id": "press-pecho", "sets": 4, "reps": "8"}]
```

## Variables de entorno

| Variable | Por defecto | Descripción |
|---|---|---|
| `MONGODB_URL` | `mongodb://admin:admin@host.docker.internal:27017/gym_tracker?authSource=admin` | Cadena de conexión MongoDB |

## Arranque local

```bash
# Con Docker Compose
docker compose up --build

# La app estará en http://localhost:8095
```

El seed se ejecuta automáticamente en el primer arranque. Descarga los GIFs desde el CDN `JahelCuadrado/ExerciseGymGifsDB@v1.1.0` y los almacena en MongoDB. Puede tardar 2-3 minutos la primera vez.

## Funcionalidad offline

El botón `↓` disponible en el selector de planes y en la barra de navegación genera un fichero `.html` auto-contenido (~20 MB por plan) que incluye:

- GIFs embebidos como `data:image/gif;base64,...`
- CSS inlineado (fuentes sustituidas por sistema)
- JS sin dependencias externas
- Progreso persistido en `localStorage` (compatible con la versión online)

Abrir desde la app Archivos en Safari (iPhone) sin conexión a red.

## Deploy

El despliegue se hace mediante GitHub Actions (`workflow_dispatch`) sobre un runner self-hosted en el servidor omvdls (CasaOS):

```
.github/workflows/deploy.yml
```

El workflow hace `rsync` del código al servidor, reconstruye la imagen Docker con `--no-cache` y verifica que la app responde en `:8095`.
