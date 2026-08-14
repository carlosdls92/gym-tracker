import asyncio
import os

import httpx
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://host.docker.internal:27017")
CDN = "https://cdn.jsdelivr.net/gh/JahelCuadrado/ExerciseGymGifsDB@v1.1.0/"

_client = None
_db = None


def get_db():
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(MONGODB_URL)
        _db = _client.gym_tracker
    return _db


# ─── Catálogo de ejercicios ────────────────────────────────────────────────────
EXERCISES = [
    # ── Iniciación ────────────────────────────────────────────────────────────
    {
        "id": "cardio",
        "name": "Cardio",
        "type": "cardio",
        "muscle_badge": "Cardio",
        "meta": "Cinta · bicicleta · elíptica · Intensidad media-baja",
        "duration": "12'",
        "technique": None,
        "tags": [],
        "gifs": [
            {"label": "Cinta de correr", "accent": True,  "path": "cardio/run-equipment.gif"},
            {"label": "Carrera",          "accent": True,  "path": "cardio/run.gif"},
        ],
    },
    {
        "id": "ext-cuadriceps",
        "name": "Extensión de cuádriceps",
        "type": "regular",
        "muscle_badge": "Cuádriceps",
        "technique": "Sentado en la máquina, respaldo recto, rodillo sobre el empeine. Extiende las piernas hasta la posición recta contrayendo el cuádriceps. Baja controlado sin dejar caer el peso.",
        "tags": ["Máquina", "Aislamiento", "Cuádriceps"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "quads/lever-leg-extension.gif"},
            {"label": "Variante",   "accent": True,  "path": "quads/resistance-band-leg-extension.gif"},
        ],
    },
    {
        "id": "prensa",
        "name": "Prensa",
        "type": "regular",
        "muscle_badge": "Cuádriceps",
        "technique": "Pies a la anchura de caderas sobre la plataforma. Baja el peso flexionando rodillas hasta 90° sin despegar la espalda baja del respaldo. Empuja desde los talones hasta casi extender las piernas.",
        "tags": ["Máquina", "Compuesto", "Cuádriceps · Glúteos"],
        "gifs": [
            {"label": "Movimiento",       "accent": False, "path": "quads/lever-alternate-leg-press.gif"},
            {"label": "Sentadilla banco", "accent": True,  "path": "quads/barbell-bench-squat.gif"},
        ],
    },
    {
        "id": "deadlift",
        "name": "Deadlift",
        "type": "regular",
        "muscle_badge": "Espalda baja · Glúteos",
        "technique": "Pies a la anchura de caderas, barra sobre los pies. Agarre doble supino o mixto. Espalda recta, pecho arriba. Levanta empujando el suelo con los pies mientras extiendes cadera y rodillas simultáneamente.",
        "tags": ["Barra", "Compuesto", "Erector espinal"],
        "gifs": [
            {"label": "Movimiento",       "accent": False, "path": "glutes/barbell-deadlift.gif"},
            {"label": "Con mancuernas",   "accent": True,  "path": "glutes/dumbbell-deadlift.gif"},
        ],
    },
    {
        "id": "press-pecho",
        "name": "Press de pecho",
        "type": "regular",
        "muscle_badge": "Pectorales",
        "technique": "Tumbado en banco plano, agarre ligeramente más ancho que los hombros. Baja la barra hasta rozar el pecho en línea con los pezones. Empuja verticalmente hacia arriba sin bloquear los codos.",
        "tags": ["Barra / mancuernas", "Compuesto", "Pecho · Tríceps · Hombro anterior"],
        "gifs": [
            {"label": "Movimiento",     "accent": False, "path": "pectorals/barbell-bench-press.gif"},
            {"label": "Con mancuernas", "accent": True,  "path": "pectorals/dumbbell-bench-press.gif"},
        ],
    },
    {
        "id": "jalon-abierto",
        "name": "Jalón abierto",
        "type": "regular",
        "muscle_badge": "Dorsal ancho",
        "technique": "Agarre amplio en barra de polea. Lleva la barra hacia el pecho superior inclinando ligeramente el torso atrás. Contrae los dorsales apretando los omóplatos. Sube controlado sin soltar de golpe.",
        "tags": ["Polea alta", "Agarre ancho", "Dorsal · Redondo mayor"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "lats/cable-bar-lateral-pulldown.gif"},
            {"label": "En cable",   "accent": True,  "path": "lats/cable-pulldown.gif"},
        ],
    },
    {
        "id": "laterales-hombros",
        "name": "Laterales de hombros",
        "type": "regular",
        "muscle_badge": "Deltoides lateral",
        "technique": "De pie con mancuernas, codos ligeramente doblados. Eleva los brazos a los lados hasta la altura del hombro (en T). El meñique ligeramente más alto que el pulgar. Baja controlado en 2-3 segundos.",
        "tags": ["Mancuernas", "Elevación lateral", "Deltoides medial"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "delts/dumbbell-lateral-raise.gif"},
            {"label": "En cable",   "accent": True,  "path": "delts/cable-lateral-raise.gif"},
        ],
    },
    {
        "id": "martillo",
        "name": "Martillo",
        "type": "regular",
        "muscle_badge": "Bíceps · Braquial",
        "technique": "De pie con mancuernas en agarre neutro (pulgar arriba). Codos pegados al torso. Flexiona llevando la mancuerna hacia el hombro sin rotar la muñeca. Baja lentamente. Alterna brazos o hazlo simultáneo.",
        "tags": ["Mancuernas", "Curl neutro", "Braquial · Braquiorradial"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "biceps/dumbbell-hammer-curl.gif"},
            {"label": "Variante",   "accent": True,  "path": "biceps/dumbbell-hammer-curl-v-2.gif"},
        ],
    },
    {
        "id": "fondos",
        "name": "Fondos",
        "type": "regular",
        "muscle_badge": "Tríceps · Pecho",
        "technique": "En paralelas o banco, cuerpo erguido para enfatizar tríceps. Baja flexionando codos hasta 90°, manteniendo los codos cerca del cuerpo. Empuja hasta extender los brazos sin hiperextender los codos.",
        "tags": ["Peso corporal", "Compuesto", "Tríceps · Pecho inferior"],
        "gifs": [
            {"label": "En banco",     "accent": False, "path": "triceps/bench-dip-knees-bent.gif"},
            {"label": "En paralelas", "accent": True,  "path": "pectorals/chest-dip.gif"},
        ],
    },
    {
        "id": "abdominales",
        "name": "Abdominales",
        "type": "regular",
        "muscle_badge": "Core",
        "technique": "Crunch en suelo, rodillas dobladas, pies apoyados. Exhala al contraer el abdomen llevando el esternón hacia las caderas. No tires del cuello. Baja lento manteniendo tensión.",
        "tags": ["Peso corporal", "Crunch", "Recto abdominal"],
        "gifs": [
            {"label": "Movimiento",    "accent": False, "path": "abs/crunch-floor.gif"},
            {"label": "Brazos arriba", "accent": True,  "path": "abs/crunch-hands-overhead.gif"},
        ],
    },
    {
        "id": "femoral-tumbado",
        "name": "Femoral tumbado",
        "type": "regular",
        "muscle_badge": "Isquiotibiales",
        "technique": "Tumbado boca abajo en la máquina, talones bajo el rodillo. Flexiona las rodillas llevando los talones hacia los glúteos. Baja controlado sin soltar de golpe.",
        "tags": ["Máquina", "Aislamiento", "Femoral"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "hamstrings/lever-lying-leg-curl.gif"},
            {"label": "Músculos",   "accent": True,  "path": "hamstrings/dumbbell-lying-femoral.gif"},
        ],
    },
    {
        "id": "sentadillas",
        "name": "Sentadillas",
        "type": "regular",
        "muscle_badge": "Cuádriceps",
        "technique": "Pies a la anchura de hombros, barra sobre trapecios. Baja hasta que los muslos queden paralelos al suelo, rodillas en línea con los pies. Empuja desde los talones al subir.",
        "tags": ["Barra libre", "Compuesto", "Glúteo + Cuádriceps"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "quads/barbell-wide-squat.gif"},
            {"label": "Músculos",   "accent": True,  "path": "quads/barbell-bench-squat.gif"},
        ],
    },
    {
        "id": "deadlift-rdl",
        "name": "Deadlift Rumanian",
        "type": "regular",
        "muscle_badge": "Espalda baja",
        "technique": "De pie con barra, piernas casi extendidas. Inclina el torso hacia adelante empujando caderas atrás, barra pegada a las piernas. Siente el estiramiento en el femoral. Sube con espalda recta.",
        "tags": ["Barra libre", "Cadena posterior", "Lumbar + Femoral"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "glutes/barbell-romanian-deadlift.gif"},
            {"label": "Músculos",   "accent": True,  "path": "glutes/dumbbell-romanian-deadlift.gif"},
        ],
    },
    {
        "id": "jalon-cerrado",
        "name": "Jalón cerrado",
        "type": "regular",
        "muscle_badge": "Dorsal ancho",
        "technique": "Agarre cerrado neutro en la polea alta. Tira llevando los codos hacia las caderas, juntando los omóplatos. Pecho ligeramente elevado. Vuelve controlado evitando balanceo.",
        "tags": ["Polea alta", "Tracción vertical", "Dorsal + Bíceps"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "lats/cable-underhand-pulldown.gif"},
            {"label": "Músculos",   "accent": True,  "path": "lats/lever-front-pulldown.gif"},
        ],
    },
    {
        "id": "superior-pecho",
        "name": "Superior de pecho",
        "type": "regular",
        "muscle_badge": "Pecho superior",
        "technique": "Press inclinado 30-45° con barra o mancuernas. Baja hasta la parte alta del pecho controlado. Empuja hacia arriba y ligeramente al centro. No bloquees los codos al extender.",
        "tags": ["Banco inclinado", "Press", "Clavicular + Hombro"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "pectorals/barbell-incline-bench-press.gif"},
            {"label": "Músculos",   "accent": True,  "path": "pectorals/dumbbell-incline-bench-press.gif"},
        ],
    },
    {
        "id": "frontales",
        "name": "Frontales",
        "type": "regular",
        "muscle_badge": "Deltoides frontal",
        "technique": "De pie con mancuernas, brazos colgando. Eleva los brazos al frente hasta la altura del hombro (90°) con el codo ligeramente doblado. Baja controlado sin usar impulso.",
        "tags": ["Mancuernas", "Elevación frontal", "Hombro anterior"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "delts/dumbbell-front-raise.gif"},
            {"label": "Músculos",   "accent": True,  "path": "delts/barbell-front-raise.gif"},
        ],
    },
    {
        "id": "barra-biceps",
        "name": "Barra recta bíceps",
        "type": "regular",
        "muscle_badge": "Bíceps",
        "technique": "De pie, agarre supino en barra recta. Codos pegados al torso. Flexiona llevando la barra hacia los hombros contrayendo el bíceps al máximo. Baja lentamente en 2-3 segundos.",
        "tags": ["Barra EZ / recta", "Curl", "Bíceps braquial"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "biceps/barbell-curl.gif"},
            {"label": "Músculos",   "accent": True,  "path": "biceps/barbell-standing-close-grip-curl.gif"},
        ],
    },
    {
        "id": "extension-v",
        "name": "Extensión en V",
        "type": "regular",
        "muscle_badge": "Tríceps",
        "technique": "Polea alta con barra en V. Codos fijos al costado del torso. Empuja hacia abajo extendiendo completamente los brazos. Vuelve controlado sin dejar que los codos se alejen del cuerpo.",
        "tags": ["Polea alta", "Press-down", "Tríceps largo + lateral"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "triceps/cable-triceps-pushdown-v-bar.gif"},
            {"label": "Músculos",   "accent": True,  "path": "triceps/cable-pushdown-with-rope-attachment.gif"},
        ],
    },
    {
        "id": "maquina-aductor",
        "name": "Máquina aductor",
        "type": "regular",
        "muscle_badge": "Aductores",
        "technique": "Sentado en la máquina con las piernas separadas sobre los almohadillados. Aprieta los muslos hacia dentro juntando las piernas hasta el límite cómodo. Mantén 1 segundo y vuelve controlado a la posición inicial.",
        "tags": ["Máquina", "Aislamiento", "Aductor largo · Grácil"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "adductors/lever-seated-hip-adduction.gif"},
            {"label": "En cable",   "accent": True,  "path": "adductors/cable-hip-adduction.gif"},
        ],
    },
    {
        "id": "maquina-abductor",
        "name": "Máquina abductor",
        "type": "regular",
        "muscle_badge": "Abductores",
        "technique": "Sentado en la máquina con las piernas juntas dentro de los almohadillados. Abre las piernas hacia afuera empujando contra la resistencia. Vuelve lentamente a la posición inicial sin dejar caer el peso.",
        "tags": ["Máquina", "Aislamiento", "Glúteo medio · TFL"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "abductors/lever-seated-hip-abduction.gif"},
            {"label": "Con banda",  "accent": True,  "path": "abductors/resistance-band-seated-hip-abduction.gif"},
        ],
    },
    {
        "id": "hip-thrust",
        "name": "Hip thrust",
        "type": "regular",
        "muscle_badge": "Glúteos",
        "technique": "Espalda apoyada en el banco, barra sobre las caderas con almohadilla. Pies planos en el suelo a la anchura de caderas. Empuja la cadera hacia arriba apretando glúteos al máximo. Mantén 1 segundo en el punto alto.",
        "tags": ["Barra · Máquina", "Glúteo mayor", "Isquiotibiales"],
        "gifs": [
            {"label": "Glute bridge", "accent": False, "path": "glutes/barbell-glute-bridge.gif"},
            {"label": "Con banda",    "accent": True,  "path": "glutes/resistance-band-hip-thrusts-on-knees-female.gif"},
        ],
    },
    {
        "id": "apertura",
        "name": "Apertura",
        "type": "regular",
        "muscle_badge": "Pectorales",
        "technique": "Tumbado en banco con mancuernas, codos ligeramente doblados. Abre los brazos describiendo un arco amplio hasta sentir el estiramiento del pecho. Cierra llevando las mancuernas arriba como si abrazaras un árbol.",
        "tags": ["Mancuernas · Cable", "Aislamiento", "Pectoral mayor"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "pectorals/dumbbell-fly.gif"},
            {"label": "En cable",   "accent": True,  "path": "pectorals/cable-middle-fly.gif"},
        ],
    },
    {
        "id": "remo-maquina",
        "name": "Remo en máquina",
        "type": "regular",
        "muscle_badge": "Espalda media",
        "technique": "Sentado en la máquina de remo, pecho apoyado en el pad. Tira de los mangos hacia el torso apretando los omóplatos al final del movimiento. Vuelve controlado extendiendo los brazos sin redondear la espalda.",
        "tags": ["Máquina", "Compuesto", "Dorsal · Romboides · Bíceps"],
        "gifs": [
            {"label": "Movimiento",       "accent": False, "path": "upper-back/lever-seated-row.gif"},
            {"label": "Agarre estrecho",  "accent": True,  "path": "upper-back/lever-narrow-grip-seated-row.gif"},
        ],
    },
    {
        "id": "face-pull",
        "name": "Face pull",
        "type": "regular",
        "muscle_badge": "Deltoides posterior",
        "technique": "Polea alta con cuerda, agarre neutro. Tira hacia la cara separando los extremos de la cuerda a ambos lados de la cabeza. Los codos deben quedar a la altura de los hombros o más altos. Contrae el deltoides posterior.",
        "tags": ["Polea alta", "Cuerda", "Deltoides posterior · Manguito rotador"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "upper-back/cable-high-row-kneeling.gif"},
            {"label": "Variante",   "accent": True,  "path": "upper-back/cable-rope-elevated-seated-row.gif"},
        ],
    },
    {
        "id": "curl-alterno",
        "name": "Curl alterno",
        "type": "regular",
        "muscle_badge": "Bíceps",
        "technique": "De pie con mancuernas en agarre supino. Alterna brazos: mientras uno sube el otro baja. Codo fijo al costado. Rota la muñeca al subir para supinar completamente. Baja controlado en 2 segundos cada repetición.",
        "tags": ["Mancuernas", "Curl alternado", "Bíceps braquial · Braquial"],
        "gifs": [
            {"label": "Movimiento",   "accent": False, "path": "biceps/dumbbell-alternate-biceps-curl.gif"},
            {"label": "Simultáneo",   "accent": True,  "path": "biceps/dumbbell-biceps-curl.gif"},
        ],
    },
    {
        "id": "extension-v-invertida",
        "name": "Extensión V invertida",
        "type": "regular",
        "muscle_badge": "Tríceps",
        "technique": "Polea alta con barra V en agarre invertido (prono). Codos fijos al costado. Extiende los brazos empujando hacia abajo hasta bloquear. El agarre inverso activa más la cabeza lateral del tríceps. Sube lento controlado.",
        "tags": ["Polea alta", "Agarre invertido", "Tríceps lateral · Largo"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "triceps/cable-reverse-grip-pushdown.gif"},
            {"label": "Overhead",   "accent": True,  "path": "triceps/cable-overhead-triceps-extension-rope-attachment.gif"},
        ],
    },
    # ── Hipertrofia 5 ────────────────────────────────────────────────────────
    {
        "id": "cruces-polea",
        "name": "Cruces de polea",
        "type": "regular",
        "muscle_badge": "Pectorales",
        "technique": "Poleas altas a los lados, inclínate ligeramente adelante. Junta las manos frente al pecho describiendo un arco amplio. Mantén los codos levemente doblados durante todo el recorrido. Contrae el pecho al máximo en el punto de cruce.",
        "tags": ["Cable", "Aislamiento", "Pectoral mayor"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "pectorals/cable-crossover.gif"},
            {"label": "Variante",   "accent": True,  "path": "pectorals/cable-fly-mid.gif"},
        ],
    },
    {
        "id": "press-hombros-db",
        "name": "Press hombros mancuernas",
        "type": "regular",
        "muscle_badge": "Deltoides",
        "technique": "Sentado o de pie con mancuernas a la altura de los hombros. Empuja hacia arriba hasta casi extender los brazos. Baja controlado hasta que los codos queden a 90° o ligeramente más abajo.",
        "tags": ["Mancuernas", "Press vertical", "Deltoides frontal + medial"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "delts/dumbbell-shoulder-press.gif"},
            {"label": "Sentado",    "accent": True,  "path": "delts/dumbbell-seated-shoulder-press.gif"},
        ],
    },
    {
        "id": "gemelos",
        "name": "Gemelos",
        "type": "regular",
        "muscle_badge": "Gemelos",
        "technique": "De pie en el borde de un escalón, talones fuera. Sube de puntillas lo máximo posible contrayendo los gemelos. Baja lentamente hasta sentir el estiramiento completo. No rebotas en el punto bajo.",
        "tags": ["Peso corporal · Máquina", "Elevación de talones", "Gastrocnemio · Sóleo"],
        "gifs": [
            {"label": "Movimiento",  "accent": False, "path": "calves/standing-calf-raise.gif"},
            {"label": "En máquina",  "accent": True,  "path": "calves/lever-standing-calf-raise.gif"},
        ],
    },
    {
        "id": "dominadas",
        "name": "Dominadas",
        "type": "regular",
        "muscle_badge": "Dorsal ancho",
        "technique": "Agarre prono más ancho que los hombros. Arranca desde posición colgada con escápulas bajas. Tira llevando el pecho hacia la barra. Baja controlado hasta la extensión completa sin soltar el hombro.",
        "tags": ["Peso corporal", "Tracción vertical", "Dorsal + Redondo + Bíceps"],
        "gifs": [
            {"label": "Movimiento",   "accent": False, "path": "lats/pull-up.gif"},
            {"label": "Agarre ancho", "accent": True,  "path": "lats/wide-grip-pull-up.gif"},
        ],
    },
    {
        "id": "barra-pecho-multipower",
        "name": "Barra pecho Multipower",
        "type": "regular",
        "muscle_badge": "Pectorales",
        "technique": "Press de banca en máquina Smith. Ajusta el banco plano, agarre ligeramente más ancho que los hombros. La guía controlada permite enfocarse en el pecho. Baja hasta rozar el pecho, empuja hasta casi extender.",
        "tags": ["Multipower", "Compuesto", "Pecho + Tríceps"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "pectorals/smith-machine-chest-press.gif"},
            {"label": "Inclinado",  "accent": True,  "path": "pectorals/barbell-incline-bench-press.gif"},
        ],
    },
    {
        "id": "remo-mancuernas",
        "name": "Remo mancuernas",
        "type": "regular",
        "muscle_badge": "Dorsal · Romboides",
        "technique": "Apoya una rodilla y mano en el banco, espalda paralela al suelo. Tira la mancuerna hacia la cadera llevando el codo lo más atrás posible. Aprieta los omóplatos en el punto alto. Baja controlado.",
        "tags": ["Mancuernas", "Unilateral", "Dorsal + Romboides + Bíceps"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "upper-back/dumbbell-bent-over-row.gif"},
            {"label": "Un brazo",   "accent": True,  "path": "upper-back/dumbbell-one-arm-row.gif"},
        ],
    },
    {
        "id": "serrato",
        "name": "Serrato anterior",
        "type": "regular",
        "muscle_badge": "Serrato",
        "technique": "Con mancuerna o cable, extiende el brazo por encima de la cabeza empujando la escápula hacia afuera (protracción escapular). Mantén el codo extendido. Mejora la salud del hombro y la definición lateral del tronco.",
        "tags": ["Cable · Mancuerna", "Aislamiento", "Serrato anterior"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "pectorals/weighted-serratus-anterior-dips.gif"},
            {"label": "Variante",   "accent": True,  "path": "lats/cable-pulldown.gif"},
        ],
    },
    {
        "id": "lumbares",
        "name": "Extensiones lumbares",
        "type": "regular",
        "muscle_badge": "Espalda baja",
        "technique": "Tumbado boca abajo en banco de extensiones con caderas sobre el pivote. Baja el torso hasta la horizontal o ligeramente más. Sube contrayendo los erectores espinales hasta alinear el cuerpo. No hiperextiendas al final.",
        "tags": ["Banco hiperextensión", "Erector espinal", "Glúteos · Femoral"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "lower-back/hyperextension.gif"},
            {"label": "Con peso",   "accent": True,  "path": "lower-back/weighted-back-extension.gif"},
        ],
    },
    {
        "id": "zancadas",
        "name": "Zancadas",
        "type": "regular",
        "muscle_badge": "Cuádriceps · Glúteos",
        "technique": "De pie con mancuernas o barra. Da un paso largo hacia adelante, baja la rodilla trasera casi hasta el suelo. La rodilla delantera no debe sobrepasar los dedos del pie. Empuja desde el talón delantero para volver.",
        "tags": ["Mancuernas · Barra", "Compuesto", "Cuádriceps + Glúteo"],
        "gifs": [
            {"label": "Movimiento",  "accent": False, "path": "quads/barbell-lunge.gif"},
            {"label": "Caminando",   "accent": True,  "path": "quads/dumbbell-walking-lunge.gif"},
        ],
    },
    {
        "id": "press-frances",
        "name": "Press francés",
        "type": "regular",
        "muscle_badge": "Tríceps",
        "technique": "Tumbado en banco plano con barra EZ. Baja la barra hacia la frente doblando los codos. Codos fijos apuntando al techo. Extiende los brazos contrayendo el tríceps largo. No separes los codos durante el movimiento.",
        "tags": ["Barra EZ", "Skull crusher", "Tríceps largo"],
        "gifs": [
            {"label": "Movimiento",      "accent": False, "path": "triceps/barbell-lying-triceps-extension.gif"},
            {"label": "Con mancuernas",  "accent": True,  "path": "triceps/dumbbell-lying-triceps-extension.gif"},
        ],
    },
    {
        "id": "barra-z-predicador",
        "name": "Barra Z predicador",
        "type": "regular",
        "muscle_badge": "Bíceps",
        "technique": "Sentado en el banco predicador, brazos sobre el almohadillado inclinado, agarre supino en barra EZ. Baja controlado hasta casi extender. Sube contrayendo el bíceps al máximo sin soltar los codos del soporte.",
        "tags": ["Banco predicador", "Barra EZ", "Bíceps braquial"],
        "gifs": [
            {"label": "Movimiento",   "accent": False, "path": "biceps/barbell-preacher-curl.gif"},
            {"label": "Con barra EZ", "accent": True,  "path": "biceps/ez-barbell-preacher-curl.gif"},
        ],
    },
    {
        "id": "dominadas-supina",
        "name": "Dominadas supinas",
        "type": "regular",
        "muscle_badge": "Dorsal · Bíceps",
        "technique": "Agarre supino (palmas hacia ti) a la anchura de hombros. Desde posición colgada, tira llevando el pecho hacia la barra. Activa bíceps y dorsal simultáneamente. Baja controlado hasta la extensión completa.",
        "tags": ["Peso corporal", "Agarre supino", "Dorsal + Bíceps"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "lats/chin-up.gif"},
            {"label": "Variante",   "accent": True,  "path": "lats/underhand-pull-up.gif"},
        ],
    },
    {
        "id": "polea-baja-cuerda",
        "name": "Polea baja cuerda",
        "type": "regular",
        "muscle_badge": "Bíceps",
        "technique": "Polea baja con accesorio de cuerda o barra. De pie o sentado, curl hacia los hombros manteniendo los codos fijos al costado. El agarre con cuerda permite una supinación más natural y mayor rango de movimiento.",
        "tags": ["Cable", "Curl", "Bíceps braquial · Braquiorradial"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "biceps/cable-curl.gif"},
            {"label": "Con cuerda", "accent": True,  "path": "biceps/cable-rope-hammer-curl.gif"},
        ],
    },
    {
        "id": "press-hombros-barra",
        "name": "Press hombros barra",
        "type": "regular",
        "muscle_badge": "Deltoides",
        "technique": "De pie o sentado con barra a la altura de los hombros, agarre prono ligeramente más ancho. Empuja la barra verticalmente por encima de la cabeza. Activa el core para estabilizar. Baja controlado hasta la barbilla o un poco más abajo.",
        "tags": ["Barra libre", "Press vertical", "Deltoides + Trapecios"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "delts/barbell-overhead-press.gif"},
            {"label": "Sentado",    "accent": True,  "path": "delts/barbell-seated-overhead-press.gif"},
        ],
    },
    {
        "id": "laterales-banco",
        "name": "Laterales banco inclinado",
        "type": "regular",
        "muscle_badge": "Deltoides lateral",
        "technique": "Apoyado de lado en banco inclinado 30-45°. Eleva la mancuerna hacia el techo describiendo un arco. La posición inclinada aisla mejor el deltoides lateral eliminando el balanceo del torso.",
        "tags": ["Mancuerna", "Banco inclinado", "Deltoides medial"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "delts/dumbbell-incline-lateral-raise.gif"},
            {"label": "Variante",   "accent": True,  "path": "delts/dumbbell-lateral-raise.gif"},
        ],
    },
    {
        "id": "frontales-disco",
        "name": "Frontales con disco",
        "type": "regular",
        "muscle_badge": "Deltoides frontal",
        "technique": "De pie sujetando un disco con ambas manos a la altura de las caderas. Eleva los brazos hasta la horizontal (90°) manteniendo codos ligeramente doblados. El disco obliga a trabajar en pronación, activando el deltoides anterior.",
        "tags": ["Disco", "Elevación frontal", "Hombro anterior"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "delts/plate-front-raise.gif"},
            {"label": "Con barra",  "accent": True,  "path": "delts/barbell-front-raise.gif"},
        ],
    },
    {
        "id": "tirones-sumo",
        "name": "Tirones sumo",
        "type": "regular",
        "muscle_badge": "Trapecios · Hombros",
        "technique": "De pie con barra o mancuernas en agarre cerrado. Tira hacia arriba llevando los codos por encima de los hombros, barra cerca del cuerpo. Los codos guían el movimiento. En el punto alto los codos quedan a la altura de los ojos.",
        "tags": ["Barra · Mancuernas", "Remo vertical", "Trapecios + Deltoides"],
        "gifs": [
            {"label": "Movimiento",      "accent": False, "path": "delts/barbell-upright-row.gif"},
            {"label": "Con mancuernas",  "accent": True,  "path": "delts/dumbbell-upright-row.gif"},
        ],
    },
    {
        "id": "apertura-maquina",
        "name": "Apertura en máquina",
        "type": "regular",
        "muscle_badge": "Pectorales",
        "technique": "Sentado en la máquina pec-deck, codos apoyados en los almohadillados. Junta los brazos frente al pecho apretando los pectorales. Mantén 1 segundo en la contracción. Abre lentamente controlando el estiramiento.",
        "tags": ["Máquina pec-deck", "Aislamiento", "Pectoral mayor"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "pectorals/lever-pec-deck-fly.gif"},
            {"label": "En cable",   "accent": True,  "path": "pectorals/cable-crossover.gif"},
        ],
    },
    {
        "id": "posterior-maquina",
        "name": "Posterior en máquina",
        "type": "regular",
        "muscle_badge": "Deltoides posterior",
        "technique": "Sentado en la máquina pec-deck de cara al respaldo, abre los brazos hacia atrás en arco amplio. Aprieta los deltoides posteriores y romboides al final del movimiento. Vuelve lento controlando la vuelta.",
        "tags": ["Máquina reverse pec-deck", "Aislamiento", "Deltoides posterior + Romboides"],
        "gifs": [
            {"label": "Movimiento", "accent": False, "path": "upper-back/lever-pec-deck-rear-delt-row.gif"},
            {"label": "En cable",   "accent": True,  "path": "delts/cable-rear-delt-row.gif"},
        ],
    },
]

# ─── Planes ────────────────────────────────────────────────────────────────────
PLANS = [
    {"_id": "iniciacion",    "name": "Iniciación",   "sort_order": 1},
    {"_id": "hipertrofia-5", "name": "Hipertrofia 5","sort_order": 2},
]

# ─── Días de entrenamiento ─────────────────────────────────────────────────────
WORKOUT_DAYS = [
    # ── Iniciación ────────────────────────────────────────────────────────────
    {
        "plan": "iniciacion", "day_num": 1, "day_label": "DÍA 1",
        "title": "DÍA UNO",
        "subtitle": "Piernas · Pecho · Espalda · Brazos · Core",
        "muscle_tags": ["Cuádriceps", "Espalda baja", "Pecho", "Dorsal", "Hombros", "Bíceps", "Tríceps", "Core"],
        "has_cardio": True, "total": 10,
        "exercises": [
            {"id": "cardio",            "sets": 1, "reps": "12'"},
            {"id": "ext-cuadriceps",    "sets": 4, "reps": "12"},
            {"id": "prensa",            "sets": 4, "reps": "12"},
            {"id": "deadlift",          "sets": 4, "reps": "12"},
            {"id": "press-pecho",       "sets": 4, "reps": "12"},
            {"id": "jalon-abierto",     "sets": 4, "reps": "12"},
            {"id": "laterales-hombros", "sets": 4, "reps": "12"},
            {"id": "martillo",          "sets": 4, "reps": "12"},
            {"id": "fondos",            "sets": 4, "reps": "12"},
            {"id": "abdominales",       "sets": 4, "reps": "15"},
        ],
    },
    {
        "plan": "iniciacion", "day_num": 2, "day_label": "DÍA 2",
        "title": "DÍA DOS",
        "subtitle": "Piernas · Espalda · Pecho · Brazos · Core",
        "muscle_tags": ["Femoral", "Cuádriceps", "Espalda", "Pecho", "Hombros", "Bíceps", "Tríceps", "Core"],
        "has_cardio": True, "total": 10,
        "exercises": [
            {"id": "cardio",          "sets": 1, "reps": "12'"},
            {"id": "femoral-tumbado", "sets": 4, "reps": "12"},
            {"id": "sentadillas",     "sets": 4, "reps": "12"},
            {"id": "deadlift-rdl",    "sets": 4, "reps": "12"},
            {"id": "jalon-cerrado",   "sets": 4, "reps": "12"},
            {"id": "superior-pecho",  "sets": 4, "reps": "12"},
            {"id": "frontales",       "sets": 4, "reps": "12"},
            {"id": "barra-biceps",    "sets": 4, "reps": "12"},
            {"id": "extension-v",     "sets": 4, "reps": "12"},
            {"id": "abdominales",     "sets": 4, "reps": "15"},
        ],
    },
    {
        "plan": "iniciacion", "day_num": 3, "day_label": "DÍA 3",
        "title": "DÍA TRES",
        "subtitle": "Aductores · Abductores · Glúteos · Pecho · Espalda · Brazos · Core",
        "muscle_tags": ["Aductores", "Abductores", "Glúteos", "Pectorales", "Dorsal", "Hombros", "Bíceps", "Tríceps"],
        "has_cardio": False, "total": 9,
        "exercises": [
            {"id": "maquina-aductor",       "sets": 4, "reps": "15"},
            {"id": "maquina-abductor",      "sets": 4, "reps": "15"},
            {"id": "hip-thrust",            "sets": 4, "reps": "12"},
            {"id": "apertura",              "sets": 4, "reps": "12"},
            {"id": "remo-maquina",          "sets": 4, "reps": "12"},
            {"id": "face-pull",             "sets": 4, "reps": "15"},
            {"id": "curl-alterno",          "sets": 4, "reps": "12"},
            {"id": "extension-v-invertida", "sets": 4, "reps": "12"},
            {"id": "abdominales",           "sets": 4, "reps": "15"},
        ],
    },
    # ── Hipertrofia 5 ─────────────────────────────────────────────────────────
    {
        "plan": "hipertrofia-5", "day_num": 1, "day_label": "L",
        "title": "PECHO Y TRÍCEPS",
        "subtitle": "Pectorales · Tríceps · Hombro anterior",
        "muscle_tags": ["Pectorales", "Tríceps", "Hombro anterior"],
        "has_cardio": False, "total": 8,
        "exercises": [
            {"id": "press-pecho",           "sets": 4, "reps": "8"},
            {"id": "barra-pecho-multipower", "sets": 4, "reps": "10"},
            {"id": "superior-pecho",        "sets": 4, "reps": "10"},
            {"id": "apertura-maquina",      "sets": 4, "reps": "12"},
            {"id": "cruces-polea",          "sets": 4, "reps": "15"},
            {"id": "press-frances",         "sets": 4, "reps": "12"},
            {"id": "extension-v",           "sets": 4, "reps": "15"},
            {"id": "fondos",                "sets": 4, "reps": "10"},
        ],
    },
    {
        "plan": "hipertrofia-5", "day_num": 2, "day_label": "M",
        "title": "ESPALDA Y BÍCEPS",
        "subtitle": "Dorsal · Romboides · Bíceps",
        "muscle_tags": ["Dorsal ancho", "Espalda media", "Bíceps", "Braquial"],
        "has_cardio": False, "total": 8,
        "exercises": [
            {"id": "dominadas",         "sets": 4, "reps": "8"},
            {"id": "remo-mancuernas",   "sets": 4, "reps": "10"},
            {"id": "jalon-cerrado",     "sets": 4, "reps": "12"},
            {"id": "dominadas-supina",  "sets": 3, "reps": "8"},
            {"id": "polea-baja-cuerda", "sets": 3, "reps": "15"},
            {"id": "curl-alterno",      "sets": 4, "reps": "12"},
            {"id": "barra-z-predicador","sets": 4, "reps": "12"},
            {"id": "martillo",          "sets": 3, "reps": "12"},
        ],
    },
    {
        "plan": "hipertrofia-5", "day_num": 3, "day_label": "X",
        "title": "HOMBROS",
        "subtitle": "Deltoides anterior · lateral · posterior",
        "muscle_tags": ["Deltoides", "Trapecios", "Serrato", "Manguito rotador"],
        "has_cardio": False, "total": 9,
        "exercises": [
            {"id": "press-hombros-barra", "sets": 4, "reps": "10"},
            {"id": "press-hombros-db",    "sets": 4, "reps": "12"},
            {"id": "laterales-hombros",   "sets": 4, "reps": "15"},
            {"id": "laterales-banco",     "sets": 4, "reps": "15"},
            {"id": "frontales-disco",     "sets": 4, "reps": "12"},
            {"id": "tirones-sumo",        "sets": 4, "reps": "12"},
            {"id": "posterior-maquina",   "sets": 3, "reps": "15"},
            {"id": "face-pull",           "sets": 3, "reps": "15"},
            {"id": "serrato",             "sets": 3, "reps": "15"},
        ],
    },
    {
        "plan": "hipertrofia-5", "day_num": 4, "day_label": "J",
        "title": "PIERNAS",
        "subtitle": "Cuádriceps · Glúteos · Gemelos · Lumbares",
        "muscle_tags": ["Cuádriceps", "Glúteos", "Gemelos", "Espalda baja"],
        "has_cardio": False, "total": 6,
        "exercises": [
            {"id": "sentadillas",    "sets": 5, "reps": "5"},
            {"id": "prensa",         "sets": 4, "reps": "15"},
            {"id": "ext-cuadriceps", "sets": 4, "reps": "12"},
            {"id": "zancadas",       "sets": 3, "reps": "12"},
            {"id": "lumbares",       "sets": 3, "reps": "15"},
            {"id": "gemelos",        "sets": 4, "reps": "20"},
        ],
    },
    {
        "plan": "hipertrofia-5", "day_num": 5, "day_label": "V",
        "title": "POSTERIOR",
        "subtitle": "Isquiotibiales · Glúteos · Aductores · Abductores",
        "muscle_tags": ["Isquiotibiales", "Glúteos", "Aductores", "Abductores"],
        "has_cardio": False, "total": 6,
        "exercises": [
            {"id": "deadlift",         "sets": 4, "reps": "5"},
            {"id": "deadlift-rdl",     "sets": 4, "reps": "10"},
            {"id": "femoral-tumbado",  "sets": 4, "reps": "12"},
            {"id": "maquina-aductor",  "sets": 4, "reps": "15"},
            {"id": "maquina-abductor", "sets": 4, "reps": "15"},
            {"id": "hip-thrust",       "sets": 4, "reps": "12"},
        ],
    },
]


# ─── Seed ──────────────────────────────────────────────────────────────────────
async def _download(client: httpx.AsyncClient, path: str) -> bytes:
    r = await client.get(CDN + path, timeout=60)
    r.raise_for_status()
    return r.content


async def seed_if_empty() -> None:
    db = get_db()

    existing_ids: set[str] = set()
    async for ex in db.exercises.find({}, {"_id": 1}):
        existing_ids.add(ex["_id"])

    new_exercises = [ex for ex in EXERCISES if ex["id"] not in existing_ids]

    if new_exercises:
        print(f"Descargando {len(new_exercises)} nuevos ejercicios...", flush=True)
        unique_paths = list({g["path"] for ex in new_exercises for g in ex["gifs"]})
        gif_cache: dict[str, bytes] = {}

        async with httpx.AsyncClient() as client:
            batch_size = 8
            for i in range(0, len(unique_paths), batch_size):
                batch = unique_paths[i: i + batch_size]
                results = await asyncio.gather(*[_download(client, p) for p in batch], return_exceptions=True)
                for path, result in zip(batch, results):
                    if isinstance(result, Exception):
                        print(f"  ✗ {path}: {result}", flush=True)
                    else:
                        gif_cache[path] = result
                        print(f"  ✓ {path}", flush=True)

        docs = []
        for ex in new_exercises:
            docs.append({
                "_id": ex["id"],
                "name": ex["name"],
                "type": ex.get("type", "regular"),
                "muscle_badge": ex.get("muscle_badge", ""),
                "technique": ex.get("technique"),
                "tags": ex.get("tags", []),
                "meta": ex.get("meta"),
                "duration": ex.get("duration"),
                "gifs": [{"label": g["label"], "accent": g["accent"]} for g in ex["gifs"]],
                "gif_data": [gif_cache.get(g["path"], b"") for g in ex["gifs"]],
            })

        await db.exercises.insert_many(docs)
        await db.exercises.create_index("type")
        print(f"  → {len(docs)} ejercicios insertados.", flush=True)

    for plan in PLANS:
        await db.workout_plans.replace_one({"_id": plan["_id"]}, plan, upsert=True)

    for day in WORKOUT_DAYS:
        await db.workout_days.replace_one(
            {"plan": day["plan"], "day_num": day["day_num"]},
            day,
            upsert=True,
        )

    await db.workout_days.create_index([("plan", 1), ("day_num", 1)])
    print("Base de datos al día.", flush=True)
