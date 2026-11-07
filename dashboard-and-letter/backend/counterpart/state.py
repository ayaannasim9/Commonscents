"""Demo state in SQLite: as_of date, facts_version, planted events, the last helper note."""
from __future__ import annotations

import json
import sqlite3
from datetime import date

from . import db
from .models import PlantedEvent, SinceLastVisit
from .pipeline.common import add_months


def get(conn: sqlite3.Connection, key: str) -> str:
    return conn.execute("SELECT value FROM demo_state WHERE key=?", (key,)).fetchone()[0]


def _set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT INTO demo_state(key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


def as_of(conn) -> date:
    return date.fromisoformat(get(conn, "as_of"))


def facts_version(conn) -> int:
    return int(get(conn, "facts_version"))


def bump(conn) -> int:
    v = facts_version(conn) + 1
    _set(conn, "facts_version", str(v))
    conn.commit()
    return v


def last_full_month(conn) -> tuple[int, int]:
    d = as_of(conn)
    return add_months(d.year, d.month, -1)


def events(conn) -> list[PlantedEvent]:
    return [PlantedEvent(name=r["name"], year=r["year"], month=r["month"])
            for r in conn.execute("SELECT name, year, month FROM planted_events ORDER BY id")]


def add_event(conn, name: str) -> bool:
    """Plant an event in the last full month. False if it is already there."""
    y, m = last_full_month(conn)
    if conn.execute("SELECT 1 FROM planted_events WHERE name=? AND year=? AND month=?", (name, y, m)).fetchone():
        return False
    conn.execute("INSERT INTO planted_events(name, year, month) VALUES (?,?,?)", (name, y, m))
    conn.commit()
    return True


def next_month(conn) -> date:
    d = as_of(conn)
    y, m = add_months(d.year, d.month, 1)
    _set(conn, "as_of", date(y, m, 1).isoformat())
    conn.commit()
    bump(conn)
    return as_of(conn)


def since_last_visit(conn) -> SinceLastVisit | None:
    try:
        raw = get(conn, "since_last_visit")
    except TypeError:
        return None
    return SinceLastVisit(**json.loads(raw)) if raw else None


def set_since_last_visit(conn, value: SinceLastVisit | None) -> None:
    _set(conn, "since_last_visit", value.model_dump_json() if value else "")
    conn.commit()
    bump(conn)


def reset(conn) -> date:
    """Back to the clean starting state. facts_version only goes up, so clients refetch."""
    v = facts_version(conn)
    for t in ("planted_events", "letters", "guardrail_events", "cases", "access_log"):
        conn.execute(f"DELETE FROM {t}")
    conn.execute("DELETE FROM demo_state")
    for k, val in db.DEFAULTS.items():
        _set(conn, k, val)
    _set(conn, "facts_version", str(v + 1))
    conn.commit()
    return as_of(conn)
