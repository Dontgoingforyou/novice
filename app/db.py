"""SQLite. Данные вымышленные, файл локальный, в git не кладётся."""

from __future__ import annotations

import os
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from app.domain import ROLES, Checkin, Checkpoint

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("NOVICE_DB", ROOT / "data" / "novice.sqlite"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    place TEXT NOT NULL,
    start_date TEXT NOT NULL,
    manager TEXT NOT NULL,
    buddy TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY,
    person_id INTEGER NOT NULL REFERENCES people(id),
    code TEXT NOT NULL,
    day_offset INTEGER NOT NULL,
    title TEXT NOT NULL,
    detail TEXT NOT NULL,
    owner TEXT NOT NULL,
    kind TEXT NOT NULL,
    done_at TEXT,
    result TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY,
    person_id INTEGER NOT NULL REFERENCES people(id),
    day_offset INTEGER NOT NULL,
    understands TEXT NOT NULL,
    knows_who TEXT NOT NULL,
    wants_stay TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    resolved_note TEXT NOT NULL DEFAULT '',
    UNIQUE (person_id, day_offset)
);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    count = conn.execute("SELECT COUNT(*) AS n FROM people").fetchone()["n"]
    if count == 0:
        seed(conn, date.today())
    conn.commit()


def seed(conn: sqlite3.Connection, today: date) -> None:
    """Семь историй относительно сегодня, чтобы доска не протухала."""
    people = [
        {
            "name": "Кира Лебедева",
            "role": "seller",
            "place": "Магазин «Север»",
            "start": today - timedelta(days=5),
            "manager": "Ольга Семёнова",
            "buddy": "Нина Волкова",
            "done": ["buddy", "uniform", "first_shift", "training_receipt"],
            "checkins": [],
        },
        {
            "name": "Павел Орлов",
            "role": "warehouse",
            "place": "Склад «Химки»",
            "start": today - timedelta(days=16),
            "manager": "Игорь Пашин",
            "buddy": "Степан Юдин",
            "done": ["buddy", "safety", "first_pick", "inbound", "solo_pick"],
            "checkins": [],
        },
        {
            "name": "Денис Шаров",
            "role": "wholesale",
            "place": "Отдел продаж",
            "start": today - timedelta(days=22),
            "manager": "Марина Ким",
            "buddy": "Олег Рыбин",
            "done": ["buddy", "catalog", "listen", "first_call", "checkin_14"],
            "checkins": [
                {
                    "day": 14,
                    "understands": "yes",
                    "knows_who": "no",
                    "wants_stay": "unsure",
                    "note": "Прайс понял. Кто ведёт сети — не сказал никто. Клиентов наставника пока не передают.",
                }
            ],
        },
        {
            "name": "Алина Мороз",
            "role": "office",
            "place": "Головной офис",
            "start": today - timedelta(days=3),
            "manager": "Алексей Берестов",
            "buddy": "",
            "done": [],
            "checkins": [],
        },
        {
            "name": "Тимур Сафин",
            "role": "seller",
            "place": "Магазин «Речной»",
            "start": today - timedelta(days=48),
            "manager": "Ольга Семёнова",
            "buddy": "Катя Мишина",
            "done": ["buddy", "uniform", "first_shift", "training_receipt", "solo_permit", "checkin_14", "solo_review"],
            "checkins": [
                {
                    "day": 14,
                    "understands": "yes",
                    "knows_who": "yes",
                    "wants_stay": "yes",
                    "note": "Зал уже сам, по размерам иногда зовёт Катю.",
                }
            ],
        },
        {
            "name": "Ева Громова",
            "role": "warehouse",
            "place": "Склад «Химки»",
            "start": today - timedelta(days=70),
            "manager": "Игорь Пашин",
            "buddy": "Степан Юдин",
            "done": [
                "buddy",
                "safety",
                "first_pick",
                "inbound",
                "solo_pick",
                "checkin_14",
                "pick_rate",
                "checkin_45",
                "inventory",
            ],
            "checkins": [
                {
                    "day": 14,
                    "understands": "yes",
                    "knows_who": "yes",
                    "wants_stay": "yes",
                    "note": "Смену поняла, к Степану ходит сама.",
                },
                {
                    "day": 45,
                    "understands": "yes",
                    "knows_who": "yes",
                    "wants_stay": "yes",
                    "note": "Норму ещё не всегда берёт, уходить не собирается.",
                },
            ],
        },
        {
            "name": "Софья Ильина",
            "role": "seller",
            "place": "Магазин «Север»",
            "start": today - timedelta(days=90),
            "manager": "Ольга Семёнова",
            "buddy": "Катя Мишина",
            "done": [
                "buddy",
                "uniform",
                "first_shift",
                "training_receipt",
                "solo_permit",
                "checkin_14",
                "solo_review",
                "checkin_45",
                "quality_60",
            ],
            "checkins": [
                {
                    "day": 14,
                    "understands": "yes",
                    "knows_who": "yes",
                    "wants_stay": "yes",
                    "note": "Первую неделю тянула Катю, потом отпустила.",
                },
                {
                    "day": 45,
                    "understands": "yes",
                    "knows_who": "yes",
                    "wants_stay": "yes",
                    "note": "Хочет остаться на «Севере», не переводиться.",
                },
            ],
        },
        {
            "name": "Глеб Фомин",
            "role": "wholesale",
            "place": "Отдел продаж",
            "start": today - timedelta(days=1),
            "manager": "Марина Ким",
            "buddy": "Олег Рыбин",
            "done": ["buddy"],
            "checkins": [],
        },
    ]
    for item in people:
        _insert_person(conn, item, today)


def _insert_person(conn: sqlite3.Connection, item: dict, today: date) -> int:
    cur = conn.execute(
        """
        INSERT INTO people (name, role, place, start_date, manager, buddy)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (item["name"], item["role"], item["place"], item["start"].isoformat(), item["manager"], item["buddy"]),
    )
    person_id = int(cur.lastrowid)
    done = set(item["done"])
    for code, offset, owner, kind, title, detail in ROLES[item["role"]]["points"]:
        done_at = today.isoformat() if code in done else None
        conn.execute(
            """
            INSERT INTO checkpoints
                (person_id, code, day_offset, title, detail, owner, kind, done_at, result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, '')
            """,
            (person_id, code, offset, title, detail, owner, kind, done_at),
        )
    for checkin in item["checkins"]:
        conn.execute(
            """
            INSERT INTO checkins
                (person_id, day_offset, understands, knows_who, wants_stay, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_id,
                checkin["day"],
                checkin["understands"],
                checkin["knows_who"],
                checkin["wants_stay"],
                checkin["note"],
                today.isoformat(),
            ),
        )
    return person_id


def create_person(
    conn: sqlite3.Connection,
    *,
    name: str,
    role: str,
    place: str,
    start: date,
    manager: str,
    buddy: str,
    today: date,
) -> int:
    done = ["buddy"] if buddy.strip() else []
    return _insert_person(
        conn,
        {
            "name": name.strip(),
            "role": role,
            "place": place.strip(),
            "start": start,
            "manager": manager.strip(),
            "buddy": buddy.strip(),
            "done": done,
            "checkins": [],
        },
        today,
    )


def list_people(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(conn.execute("SELECT * FROM people ORDER BY start_date, name"))


def get_person(conn: sqlite3.Connection, person_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()


def list_checkpoints(conn: sqlite3.Connection, person_id: int) -> list[Checkpoint]:
    rows = conn.execute(
        "SELECT * FROM checkpoints WHERE person_id = ? ORDER BY day_offset, id",
        (person_id,),
    )
    return [_checkpoint(row) for row in rows]


def list_checkins(conn: sqlite3.Connection, person_id: int) -> list[Checkin]:
    rows = conn.execute(
        "SELECT * FROM checkins WHERE person_id = ? ORDER BY day_offset",
        (person_id,),
    )
    return [_checkin(row) for row in rows]


def mark_done(conn: sqlite3.Connection, person_id: int, checkpoint_id: int, today: date) -> bool:
    point = conn.execute(
        "SELECT * FROM checkpoints WHERE id = ? AND person_id = ?",
        (checkpoint_id, person_id),
    ).fetchone()
    if point is None or point["kind"] != "task" or point["code"] == "buddy":
        return False
    conn.execute(
        "UPDATE checkpoints SET done_at = ? WHERE id = ? AND done_at IS NULL",
        (today.isoformat(), checkpoint_id),
    )
    return True


def set_buddy(conn: sqlite3.Connection, person_id: int, buddy: str, today: date) -> bool:
    name = buddy.strip()
    if not name:
        return False
    conn.execute("UPDATE people SET buddy = ? WHERE id = ?", (name, person_id))
    conn.execute(
        """
        UPDATE checkpoints
        SET done_at = ?
        WHERE person_id = ? AND code = 'buddy' AND done_at IS NULL
        """,
        (today.isoformat(), person_id),
    )
    return True


def save_checkin(
    conn: sqlite3.Connection,
    person_id: int,
    day_offset: int,
    understands: str,
    knows_who: str,
    wants_stay: str,
    note: str,
    today: date,
) -> bool:
    point = conn.execute(
        """
        SELECT id FROM checkpoints
        WHERE person_id = ? AND kind = 'checkin' AND day_offset = ?
        """,
        (person_id, day_offset),
    ).fetchone()
    if point is None:
        return False
    conn.execute(
        """
        INSERT INTO checkins
            (person_id, day_offset, understands, knows_who, wants_stay, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (person_id, day_offset, understands, knows_who, wants_stay, note.strip(), today.isoformat()),
    )
    conn.execute(
        "UPDATE checkpoints SET done_at = ? WHERE id = ? AND done_at IS NULL",
        (today.isoformat(), point["id"]),
    )
    return True


def resolve_checkin(conn: sqlite3.Connection, person_id: int, day_offset: int, note: str, today: date) -> bool:
    text = note.strip()
    if not text:
        return False
    cur = conn.execute(
        """
        UPDATE checkins
        SET resolved_at = ?, resolved_note = ?
        WHERE person_id = ? AND day_offset = ? AND resolved_at IS NULL
        """,
        (today.isoformat(), text, person_id, day_offset),
    )
    return cur.rowcount > 0


def save_decision(conn: sqlite3.Connection, person_id: int, checkpoint_id: int, result: str, today: date) -> bool:
    cur = conn.execute(
        """
        UPDATE checkpoints
        SET done_at = ?, result = ?
        WHERE id = ? AND person_id = ? AND kind = 'decision' AND done_at IS NULL
        """,
        (today.isoformat(), result, checkpoint_id, person_id),
    )
    return cur.rowcount > 0


def _checkpoint(row: sqlite3.Row) -> Checkpoint:
    return Checkpoint(
        id=row["id"],
        code=row["code"],
        day_offset=row["day_offset"],
        title=row["title"],
        detail=row["detail"],
        owner=row["owner"],
        kind=row["kind"],
        done=row["done_at"] is not None,
        result=row["result"],
    )


def _checkin(row: sqlite3.Row) -> Checkin:
    return Checkin(
        day_offset=row["day_offset"],
        understands=row["understands"],
        knows_who=row["knows_who"],
        wants_stay=row["wants_stay"],
        note=row["note"],
        resolved=row["resolved_at"] is not None,
        resolved_note=row["resolved_note"],
    )
