from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .seed import get_db, seed_if_empty

STATIC = Path(__file__).parent / "static"


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
