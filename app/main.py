import base64
import html as _html
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .seed import get_db, seed_if_empty

STATIC = Path(__file__).parent / "static"
_OFFLINE_JS = (Path(__file__).parent / "offline_app.js").read_text(encoding="utf-8")


def _e(s) -> str:
    return _html.escape(str(s) if s is not None else "")


def _dots(n: int) -> str:
    return '<div class="set-dot"></div>' * (n or 4)


def _offline_card(ex: dict, ref: dict, day_num: int, gifs: dict, lazy: bool = False) -> str:
    ex_id = ex["_id"]
    cid = f"{day_num}-{ex_id}"
    gx = ex.get("gifs", [])
    g0 = gx[0] if len(gx) > 0 else {}
    g1 = gx[1] if len(gx) > 1 else {}
    name = _e(ex.get("name", ""))
    s0 = gifs.get(f"{ex_id}/0", "")
    s1 = gifs.get(f"{ex_id}/1", "")
    img_attr = "data-src" if lazy else "src"

    imgs = (
        '<div class="card-imgs">'
        f'<div class="card-img"><img {img_attr}="{s0}" alt="{name}">'
        f'<span class="img-tag">{_e(g0.get("label", ""))}</span></div>'
        f'<div class="card-img"><img {img_attr}="{s1}" alt="{name}">'
        f'<span class="img-tag{" accent" if g1.get("accent") else ""}">'
        f'{_e(g1.get("label", ""))}</span></div>'
        '</div>'
    )

    if ex.get("type") == "cardio":
        technique = ex.get("technique") or ""
        body = (
            '<div class="cardio-info">'
            '<div class="cardio-text"><div class="cardio-name">Cardio</div>'
            f'<div class="cardio-meta">{_e(ex.get("meta") or "")}</div>'
            '<span class="expand-hint">↓ técnica</span></div>'
            f'<div class="cardio-time">{_e(ex.get("duration") or "")}</div>'
            f'<div class="check-btn" id="chk-{cid}">✓</div>'
            '</div>'
            f'<div class="card-detail" id="det-{cid}">'
            '<div class="detail-body">'
            f'<div class="detail-text">{_e(technique)}</div>'
            '</div></div>'
        )
    else:
        sets = ref.get("sets", 4)
        reps = ref.get("reps", "12")
        tags = "".join(f'<span class="detail-tag">{_e(t)}</span>' for t in ex.get("tags", []))
        body = (
            '<div class="card-info">'
            f'<div class="card-text"><div class="card-name">{name}</div>'
            f'<div class="card-sub"><span class="muscle-badge">{_e(ex.get("muscle_badge", ""))}</span>'
            '<span class="expand-hint">↓ técnica</span></div></div>'
            f'<div class="card-right"><div class="sets-row">{_dots(sets)}</div>'
            f'<div class="reps-label">{sets}×{reps}</div>'
            f'<div class="check-btn" id="chk-{cid}">✓</div></div>'
            '</div>'
            f'<div class="card-detail" id="det-{cid}">'
            '<div class="detail-body">'
            f'<div class="detail-text">{_e(ex.get("technique") or "")}</div>'
            f'<div class="detail-tags">{tags}</div>'
            '</div></div>'
        )

    return (
        f'<div class="card" id="card-{cid}" onclick="toggleItem(event,\'{cid}\',{day_num})">'
        f'{imgs}{body}</div>'
    )


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

    # GIFs → base64 data URIs keyed as "{ex_id}/{index}"
    gifs_b64: dict[str, str] = {}
    for ex_id, ex in exercises_map.items():
        for i, data in enumerate(ex.get("gif_data", [])):
            gifs_b64[f"{ex_id}/{i}"] = (
                f"data:image/gif;base64,{base64.b64encode(bytes(data)).decode()}"
                if data else ""
            )

    # CSS: strip Google Fonts import, use system fonts
    css = (STATIC / "day.css").read_text(encoding="utf-8")
    css = css.replace(
        "@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap');",
        ""
    )
    css = css.replace("'Bebas Neue', sans-serif", "Impact, 'Arial Narrow', sans-serif")
    css = css.replace("'DM Sans', sans-serif", "-apple-system, 'Helvetica Neue', Arial, sans-serif")

    # CSS-only day switching via :target (fallback when JS is blocked in Safari file mode)
    if days:
        first_n = days[0]["day_num"]
        other_targets = ",".join(f"#day-{d['day_num']}:target" for d in days[1:])
        css += "\n[id^='day-']:target{display:block}"
        if other_targets:
            css += f"\n#root:has({other_targets}) #day-{first_n}{{display:none}}"

    plan_name = plan_doc["name"]
    day_totals: dict[int, int] = {}

    # Pre-render tabs — use <a href="#day-N"> so :target works without JS
    tabs_html = ""
    for day in days:
        n = day["day_num"]
        label = _e(day.get("day_label", f"DÍA {n}"))
        tabs_html += f'<a class="tab" href="#day-{n}" data-day="{n}" onclick="loadDay({n});return false;">{label}</a>'

    # Pre-render day panels with cards and embedded base64 GIFs
    panels_html = ""
    first_day_num = days[0]["day_num"] if days else None
    for day in days:
        n = day["day_num"]
        is_first = (n == first_day_num)
        refs = day["exercises"]
        if refs and isinstance(refs[0], str):
            refs = [{"id": r, "sets": 4, "reps": "12"} for r in refs]

        title = day["title"]
        title_parts = title.split(" ", 1)
        title_html = (
            f"{_e(title_parts[0])}<br>{_e(title_parts[1])}"
            if len(title_parts) >= 2 else _e(title)
        )

        muscle_tags = "".join(
            f'<span class="tag">{_e(t)}</span>'
            for t in day.get("muscle_tags", [])
        )

        total = day.get("total", len(refs))
        day_totals[n] = total

        cards_html = ""
        section_shown = False
        for ref in refs:
            ex_id = ref["id"] if isinstance(ref, dict) else ref
            ex = exercises_map.get(ex_id)
            if not ex:
                continue
            lazy = not is_first
            ref_dict = ref if isinstance(ref, dict) else {"id": ex_id}
            if ex.get("type") == "cardio":
                cards_html += _offline_card(ex, ref_dict, n, gifs_b64, lazy=lazy)
                cards_html += '<div class="section-title">Ejercicios</div>'
                section_shown = True
            else:
                if not section_shown:
                    cards_html += '<div class="section-title">Ejercicios</div>'
                    section_shown = True
                cards_html += _offline_card(ex, ref_dict, n, gifs_b64, lazy=lazy)

        hidden_attr = "" if is_first else " hidden"
        panels_html += (
            f'<div id="day-{n}"{hidden_attr}>'
            f'<header data-day="{n}">'
            '<div class="label-day">Gym CAR — Nacho</div>'
            f'<h1>{title_html}</h1>'
            f'<div class="subtitle">{_e(day.get("subtitle", ""))}</div>'
            f'<div class="muscle-tags">{muscle_tags}</div>'
            '</header>'
            '<div class="progress-wrap">'
            '<div class="progress-header">'
            '<span class="progress-label">Progreso</span>'
            f'<span class="progress-count" id="cnt-{n}">0 / {total}</span>'
            '</div>'
            '<div class="progress-bar-bg">'
            f'<div class="progress-bar-fill" id="pb-{n}" style="width:0%"></div>'
            '</div></div>'
            '<div class="content"><div style="height:18px"></div>'
            f'{cards_html}'
            f'<div class="complete-banner" id="ban-{n}">'
            '<div class="complete-emoji">🔥</div>'
            '<div class="complete-title">SESIÓN COMPLETADA</div>'
            f'<div class="complete-sub">{_e(title)} terminado · Buen trabajo</div>'
            '</div>'
            '<div class="footer">GYM CAR · Nacho</div>'
            '</div></div>'
        )

    totals_json = json.dumps(day_totals, separators=(",", ":"))

    parts = [
        '<!DOCTYPE html><html lang="es"><head>',
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">',
        f'<title>GYM CAR — {_e(plan_name)}</title>',
        '<style>', css, '</style>',
        '</head><body>',
        f'<div class="tabs" id="tabs-bar">{tabs_html}</div>',
        '<div id="root">',
        panels_html,
        '</div>',
        '<script>',
        f'const PLAN_SLUG={json.dumps(slug, ensure_ascii=False)};',
        f'const DAY_TOTALS={totals_json};',
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
