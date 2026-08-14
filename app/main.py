import base64
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .seed import get_db, seed_if_empty

STATIC = Path(__file__).parent / "static"
_OFFLINE_JS = (Path(__file__).parent / "offline_app.js").read_text(encoding="utf-8")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed_if_empty()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/plans")
async def get_plans():
    db = get_db()
    plans = []
    async for plan in db.workout_plans.find().sort("sort_order", 1):
        days = []
        async for day in db.workout_days.find({"plan": plan["_id"]}).sort("day_num", 1):
            days.append({
                "day_num": day["day_num"],
                "day_label": day.get("day_label", f"DÍA {day['day_num']}"),
                "title": day["title"],
            })
        plans.append({
            "_id": plan["_id"],
            "name": plan["name"],
            "sort_order": plan.get("sort_order", 0),
            "days": days,
        })
    return plans


@app.get("/api/plan/{slug}/day/{day_num}")
async def get_plan_day(slug: str, day_num: int):
    db = get_db()
    day = await db.workout_days.find_one({"day_num": day_num, "plan": slug})
    if not day:
        raise HTTPException(404, "Day not found")

    ex_refs = day["exercises"]
    if ex_refs and isinstance(ex_refs[0], str):
        refs = [{"id": i, "sets": 4, "reps": "12"} for i in ex_refs]
    else:
        refs = ex_refs

    ids = [r["id"] for r in refs]
    by_id: dict = {}
    async for ex in db.exercises.find({"_id": {"$in": ids}}):
        ex.pop("gif_data", None)
        by_id[ex["_id"]] = ex

    exercises = []
    for ref in refs:
        ex = by_id.get(ref["id"])
        if not ex:
            continue
        exercises.append({**ex, "sets": ref.get("sets", 4), "reps": ref.get("reps", "12")})

    return {
        "day_num": day["day_num"],
        "day_label": day.get("day_label", f"DÍA {day['day_num']}"),
        "title": day["title"],
        "subtitle": day["subtitle"],
        "muscle_tags": day["muscle_tags"],
        "has_cardio": day.get("has_cardio", False),
        "total": day.get("total", len(ids)),
        "exercises": exercises,
    }


@app.get("/api/plan/{slug}/offline")
async def get_plan_offline(slug: str):
    db = get_db()

    plan_doc = await db.workout_plans.find_one({"_id": slug})
    if not plan_doc:
        raise HTTPException(404, "Plan not found")

    days = []
    async for day in db.workout_days.find({"plan": slug}).sort("day_num", 1):
        days.append(day)

    # Unique exercise IDs preserving order
    seen: list[str] = []
    for day in days:
        for ref in day["exercises"]:
            ex_id = ref if isinstance(ref, str) else ref["id"]
            if ex_id not in seen:
                seen.append(ex_id)

    exercises_map: dict = {}
    async for ex in db.exercises.find({"_id": {"$in": seen}}):
        exercises_map[ex["_id"]] = ex

    days_data = []
    for day in days:
        refs = day["exercises"]
        if refs and isinstance(refs[0], str):
            refs = [{"id": r, "sets": 4, "reps": "12"} for r in refs]

        ex_list = []
        for ref in refs:
            ex = exercises_map.get(ref["id"])
            if not ex:
                continue
            ex_list.append({
                "_id": ex["_id"],
                "name": ex["name"],
                "type": ex.get("type", "regular"),
                "muscle_badge": ex.get("muscle_badge", ""),
                "technique": ex.get("technique", ""),
                "tags": ex.get("tags", []),
                "meta": ex.get("meta"),
                "duration": ex.get("duration"),
                "gifs": ex.get("gifs", []),
                "sets": ref.get("sets", 4),
                "reps": ref.get("reps", "12"),
            })

        days_data.append({
            "day_num": day["day_num"],
            "day_label": day.get("day_label", f"DÍA {day['day_num']}"),
            "title": day["title"],
            "subtitle": day["subtitle"],
            "muscle_tags": day.get("muscle_tags", []),
            "has_cardio": day.get("has_cardio", False),
            "total": day.get("total", len(ex_list)),
            "exercises": ex_list,
        })

    # GIFs → base64 data URIs (deduplicated by exercise)
    gifs_b64: dict[str, str] = {}
    for ex_id, ex in exercises_map.items():
        for i, data in enumerate(ex.get("gif_data", [])):
            gifs_b64[f"{ex_id}/{i}"] = (
                f"data:image/gif;base64,{base64.b64encode(bytes(data)).decode()}"
                if data else ""
            )

    # CSS: strip Google Fonts import, fall back to system fonts
    css = (STATIC / "day.css").read_text(encoding="utf-8")
    css = css.replace(
        "@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap');",
        ""
    )
    css = css.replace("'Bebas Neue', sans-serif", "Impact, 'Arial Narrow', sans-serif")
    css = css.replace("'DM Sans', sans-serif", "-apple-system, 'Helvetica Neue', Arial, sans-serif")

    plan_name = plan_doc["name"]
    days_json  = json.dumps(days_data,  ensure_ascii=False, separators=(",", ":"))
    gifs_json  = json.dumps(gifs_b64,   ensure_ascii=False, separators=(",", ":"))

    parts = [
        '<!DOCTYPE html><html lang="es"><head>',
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">',
        f'<title>GYM CAR — {plan_name}</title>',
        '<style>', css, '</style>',
        '</head><body>',
        '<div class="tabs" id="tabs-bar"></div>',
        '<div id="root"><div class="loading">',
        '<div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div>',
        '</div></div>',
        '<script>',
        f'const PLAN_NAME={json.dumps(plan_name, ensure_ascii=False)};',
        f'const PLAN_SLUG={json.dumps(slug, ensure_ascii=False)};',
        f'const DAYS={days_json};',
        f'const GIFS={gifs_json};',
        _OFFLINE_JS,
        '</script></body></html>',
    ]

    return Response(
        content="".join(parts).encode("utf-8"),
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="gym-{slug}.html"'},
    )


@app.get("/api/gif/{exercise_id}/{index}")
async def get_gif(exercise_id: str, index: int):
    db = get_db()
    ex = await db.exercises.find_one({"_id": exercise_id}, {"gif_data": 1})
    if not ex or not ex.get("gif_data") or index >= len(ex["gif_data"]):
        raise HTTPException(404)
    data = ex["gif_data"][index]
    if not data:
        raise HTTPException(404)
    return Response(
        content=bytes(data),
        media_type="image/gif",
        headers={"Cache-Control": "public, max-age=604800, immutable"},
    )
