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


@app.get("/api/day/{day_num}")
async def get_day(day_num: int):
    db = get_db()
    day = await db.workout_days.find_one({"day_num": day_num, "plan": "iniciacion"})
    if not day:
        raise HTTPException(404, "Day not found")

    ids = day["exercises"]
    by_id: dict = {}
    async for ex in db.exercises.find({"_id": {"$in": ids}}):
        ex.pop("gif_data", None)
        by_id[ex["_id"]] = ex

    return {
        "day_num": day["day_num"],
        "title": day["title"],
        "subtitle": day["subtitle"],
        "muscle_tags": day["muscle_tags"],
        "has_cardio": day.get("has_cardio", False),
        "total": day.get("total", len(ids)),
        "exercises": [by_id[i] for i in ids if i in by_id],
    }


@app.get("/api/gif/{exercise_id}/{index}")
async def get_gif(exercise_id: str, index: int):
    db = get_db()
    ex = await db.exercises.find_one({"_id": exercise_id}, {"gif_data": 1})
    if not ex or not ex.get("gif_data") or index >= len(ex["gif_data"]):
        raise HTTPException(404)
    return Response(
        content=bytes(ex["gif_data"][index]),
        media_type="image/gif",
        headers={"Cache-Control": "public, max-age=604800, immutable"},
    )
