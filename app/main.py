from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db
from app.domain import (
    ANSWERS,
    DECISIONS,
    OWNERS,
    ROLES,
    bucket,
    collect_signals,
    day_label,
    day_number,
    due_date,
    negative_parts,
    on_board,
    point_state,
    role_label,
)

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="Новичок")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")

MONTHS = "января февраля марта апреля мая июня июля августа сентября октября ноября декабря".split()


def ru_date(value: date) -> str:
    return f"{value.day} {MONTHS[value.month - 1]}"


def parse_date(raw: str) -> date | None:
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def card_for(row, checkpoints, checkins, today: date) -> dict:
    start = date.fromisoformat(row["start_date"])
    signals = collect_signals(today, start, checkpoints, checkins)
    checkins_by_day = {item.day_offset: item for item in checkins}
    points = []
    for point in checkpoints:
        checkin = checkins_by_day.get(point.day_offset) if point.kind == "checkin" else None
        points.append(
            {
                "id": point.id,
                "code": point.code,
                "title": point.title,
                "detail": point.detail,
                "owner": OWNERS.get(point.owner, point.owner),
                "owner_code": point.owner,
                "kind": point.kind,
                "done": point.done,
                "result": DECISIONS.get(point.result, ""),
                "day_offset": point.day_offset,
                "due": ru_date(due_date(start, point.day_offset)),
                "state": point_state(today, start, point, checkin),
                "checkin": _checkin_view(checkin) if checkin else None,
                "open_checkin": point.kind == "checkin" and checkin is None and due_date(start, point.day_offset) <= today,
                "open_decision": point.kind == "decision" and not point.done and due_date(start, point.day_offset) <= today,
            }
        )
    number = day_number(today, start)
    return {
        "id": row["id"],
        "name": row["name"],
        "role": row["role"],
        "role_label": role_label(row["role"]),
        "place": row["place"],
        "manager": row["manager"],
        "buddy": row["buddy"],
        "start": ru_date(start),
        "start_iso": row["start_date"],
        "day_number": number,
        "day_label": day_label(number),
        "signals": signals,
        "headline": signals[0].text if signals else "Идёт по плану",
        "tone": signals[0].tone if signals else "ok",
        "bucket": bucket(signals),
        "points": points,
        "on_board": on_board(today, start),
    }


def _checkin_view(checkin) -> dict:
    return {
        "day_offset": checkin.day_offset,
        "understands": ANSWERS["understands"].get(checkin.understands, checkin.understands),
        "knows_who": ANSWERS["knows_who"].get(checkin.knows_who, checkin.knows_who),
        "wants_stay": ANSWERS["wants_stay"].get(checkin.wants_stay, checkin.wants_stay),
        "note": checkin.note,
        "resolved": checkin.resolved,
        "resolved_note": checkin.resolved_note,
        "negative": bool(negative_parts(checkin)) and not checkin.resolved,
    }


def load_card(conn, person_id: int, today: date) -> dict | None:
    row = db.get_person(conn, person_id)
    if row is None:
        return None
    return card_for(row, db.list_checkpoints(conn, person_id), db.list_checkins(conn, person_id), today)


def board_cards(conn, today: date, manager: str) -> list[dict]:
    cards = []
    for row in db.list_people(conn):
        if manager and row["manager"] != manager:
            continue
        card = card_for(row, db.list_checkpoints(conn, row["id"]), db.list_checkins(conn, row["id"]), today)
        if card["on_board"]:
            cards.append(card)
    order = {"act": 0, "today": 1, "ok": 2}
    cards.sort(key=lambda item: (order[item["bucket"]], -item["day_number"], item["name"]))
    return cards


def managers(conn) -> list[str]:
    rows = conn.execute("SELECT DISTINCT manager FROM people ORDER BY manager")
    return [row["manager"] for row in rows]


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


@app.on_event("startup")
def startup() -> None:
    with db.connect() as conn:
        db.init_db(conn)


@app.get("/")
def board(request: Request, manager: str = "Ольга Семёнова"):
    today = date.today()
    with db.connect() as conn:
        db.init_db(conn)
        names = managers(conn)
        chosen = manager if manager in names or manager == "" else names[0] if names else ""
        if manager == "all":
            chosen = ""
        cards = board_cards(conn, today, chosen)
    groups = {
        "act": [card for card in cards if card["bucket"] == "act"],
        "today": [card for card in cards if card["bucket"] == "today"],
        "ok": [card for card in cards if card["bucket"] == "ok"],
    }
    return templates.TemplateResponse(
        request,
        "board.html",
        {
            "groups": groups,
            "total": len(cards),
            "act": len(groups["act"]),
            "managers": names,
            "manager": chosen,
            "today": ru_date(today),
        },
    )


@app.get("/new")
def new_person(request: Request, error: str = ""):
    return templates.TemplateResponse(
        request,
        "new.html",
        {"roles": ROLES, "error": error, "today": date.today().isoformat()},
    )


@app.post("/new")
def create_person(
    request: Request,
    name: str = Form(""),
    role: str = Form(""),
    place: str = Form(""),
    start_date: str = Form(""),
    manager: str = Form(""),
    buddy: str = Form(""),
):
    today = date.today()
    start = parse_date(start_date)
    error = ""
    if not name.strip() or not place.strip() or not manager.strip():
        error = "Нужны имя, площадка и руководитель."
    elif role not in ROLES:
        error = "Выберите роль: от неё зависит план."
    elif start is None:
        error = "Дата выхода должна быть календарной."
    elif start > today:
        error = "Человек ещё не вышел. План откроется в день выхода."
    if error:
        return templates.TemplateResponse(
            request,
            "new.html",
            {"roles": ROLES, "error": error, "today": today.isoformat()},
            status_code=400,
        )
    with db.connect() as conn:
        db.init_db(conn)
        person_id = db.create_person(
            conn,
            name=name,
            role=role,
            place=place,
            start=start,
            manager=manager,
            buddy=buddy,
            today=today,
        )
        conn.commit()
    return redirect(f"/p/{person_id}")


@app.get("/p/{person_id}")
def person(request: Request, person_id: int, error: str = ""):
    today = date.today()
    with db.connect() as conn:
        db.init_db(conn)
        card = load_card(conn, person_id, today)
    if card is None:
        return templates.TemplateResponse(request, "missing.html", status_code=404)
    return templates.TemplateResponse(
        request,
        "person.html",
        {"card": card, "error": error, "decisions": DECISIONS, "answers": ANSWERS},
    )


@app.get("/p/{person_id}/my")
def mine(request: Request, person_id: int):
    today = date.today()
    with db.connect() as conn:
        db.init_db(conn)
        card = load_card(conn, person_id, today)
    if card is None:
        return templates.TemplateResponse(request, "missing.html", status_code=404)
    return templates.TemplateResponse(
        request,
        "mine.html",
        {"card": card, "answers": ANSWERS},
    )


@app.post("/p/{person_id}/checkpoints/{checkpoint_id}/done")
def done(person_id: int, checkpoint_id: int):
    today = date.today()
    with db.connect() as conn:
        db.init_db(conn)
        if db.get_person(conn, person_id) is None:
            return redirect("/")
        ok = db.mark_done(conn, person_id, checkpoint_id, today)
        conn.commit()
    if not ok:
        return redirect(f"/p/{person_id}?error=Эту+точку+так+не+закрывают")
    return redirect(f"/p/{person_id}")


@app.post("/p/{person_id}/buddy")
def buddy(person_id: int, buddy_name: str = Form("")):
    today = date.today()
    if not buddy_name.strip():
        return redirect(f"/p/{person_id}?error=Напишите+имя+наставника")
    with db.connect() as conn:
        db.init_db(conn)
        if db.get_person(conn, person_id) is None:
            return RedirectResponse("/", status_code=303)
        db.set_buddy(conn, person_id, buddy_name, today)
        conn.commit()
    return redirect(f"/p/{person_id}")


@app.post("/p/{person_id}/checkins/{day_offset}")
def checkin(
    person_id: int,
    day_offset: int,
    understands: str = Form(""),
    knows_who: str = Form(""),
    wants_stay: str = Form(""),
    note: str = Form(""),
    next_url: str = Form(""),
):
    today = date.today()
    valid = (
        understands in ANSWERS["understands"]
        and knows_who in ANSWERS["knows_who"]
        and wants_stay in ANSWERS["wants_stay"]
    )
    back = f"/p/{person_id}/my" if next_url == "my" else f"/p/{person_id}"
    if not valid:
        return redirect(back + "?error=Ответьте+на+все+три+вопроса")
    with db.connect() as conn:
        db.init_db(conn)
        row = db.get_person(conn, person_id)
        if row is None:
            return RedirectResponse("/", status_code=303)
        start = date.fromisoformat(row["start_date"])
        if due_date(start, day_offset) > today:
            return redirect(back + "?error=Этот+разговор+ещё+не+наступил")
        try:
            db.save_checkin(conn, person_id, day_offset, understands, knows_who, wants_stay, note, today)
        except sqlite3.IntegrityError:
            conn.rollback()
            return redirect(back + "?error=Разговор+уже+записан")
        conn.commit()
    return redirect(back)


@app.post("/p/{person_id}/checkins/{day_offset}/resolve")
def resolve(person_id: int, day_offset: int, resolved_note: str = Form("")):
    today = date.today()
    if not resolved_note.strip():
        return redirect(f"/p/{person_id}?error=Напишите,+что+сделали:+иначе+сигнал+никуда+не+денется")
    with db.connect() as conn:
        db.init_db(conn)
        ok = db.resolve_checkin(conn, person_id, day_offset, resolved_note, today)
        conn.commit()
    if not ok:
        return redirect(f"/p/{person_id}?error=Сигнал+уже+закрыт+или+разговора+не+было")
    return redirect(f"/p/{person_id}")


@app.post("/p/{person_id}/checkpoints/{checkpoint_id}/decision")
def decision(person_id: int, checkpoint_id: int, result: str = Form("")):
    if result not in DECISIONS:
        return redirect(f"/p/{person_id}?error=Выберите+одно+из+трёх+решений")
    today = date.today()
    with db.connect() as conn:
        db.init_db(conn)
        row = db.get_person(conn, person_id)
        if row is None:
            return RedirectResponse("/", status_code=303)
        point = conn.execute(
            "SELECT day_offset, kind FROM checkpoints WHERE id = ? AND person_id = ?",
            (checkpoint_id, person_id),
        ).fetchone()
        if point is None or point["kind"] != "decision":
            return redirect(f"/p/{person_id}?error=Это+не+точка+решения")
        if due_date(date.fromisoformat(row["start_date"]), point["day_offset"]) > today:
            return redirect(f"/p/{person_id}?error=90-й+день+ещё+не+наступил")
        db.save_decision(conn, person_id, checkpoint_id, result, today)
        conn.commit()
    return redirect(f"/p/{person_id}")


@app.get("/health")
def health():
    return {"ok": True, "time": datetime.now().isoformat(timespec="seconds")}
