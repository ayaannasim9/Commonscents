"""Demo state in SQLite, keyed by customer id: as_of, facts_version, planted events, last helper note."""
from __future__ import annotations

import sqlite3
from datetime import date

from . import db
from .models import PlantedEvent, SinceLastVisit
from .pipeline.common import add_months


def get(conn: sqlite3.Connection, cid: str, key: str) -> str:
    return conn.execute("SELECT value FROM demo_state WHERE customer=? AND key=?", (cid, key)).fetchone()[0]


def _set(conn: sqlite3.Connection, cid: str, key: str, value: str) -> None:
    conn.execute("INSERT INTO demo_state(customer, key, value) VALUES (?,?,?) "
                 "ON CONFLICT(customer, key) DO UPDATE SET value=excluded.value", (cid, key, value))


def as_of(conn, cid: str) -> date:
    return date.fromisoformat(get(conn, cid, "as_of"))


def facts_version(conn, cid: str) -> int:
    return int(get(conn, cid, "facts_version"))


def bump(conn, cid: str) -> int:
    v = facts_version(conn, cid) + 1
    _set(conn, cid, "facts_version", str(v))
    conn.commit()
    return v


def last_full_month(conn, cid: str) -> tuple[int, int]:
    d = as_of(conn, cid)
    return add_months(d.year, d.month, -1)


def events(conn, cid: str) -> list[PlantedEvent]:
    return [PlantedEvent(name=r["name"], year=r["year"], month=r["month"])
            for r in conn.execute("SELECT name, year, month FROM planted_events WHERE customer=? ORDER BY id", (cid,))]


def add_event(conn, cid: str, name: str) -> bool:
    """Plant an event in the last full month. False if it is already there."""
    y, m = last_full_month(conn, cid)
    if conn.execute("SELECT 1 FROM planted_events WHERE customer=? AND name=? AND year=? AND month=?",
                    (cid, name, y, m)).fetchone():
        return False
    conn.execute("INSERT INTO planted_events(customer, name, year, month) VALUES (?,?,?,?)", (cid, name, y, m))
    conn.commit()
    return True


def next_month(conn, cid: str) -> date:
    d = as_of(conn, cid)
    y, m = add_months(d.year, d.month, 1)
    _set(conn, cid, "as_of", date(y, m, 1).isoformat())
    conn.commit()
    bump(conn, cid)
    return as_of(conn, cid)


def since_last_visit(conn, cid: str) -> SinceLastVisit | None:
    raw = get(conn, cid, "since_last_visit")
    return SinceLastVisit.model_validate_json(raw) if raw else None


def set_since_last_visit(conn, cid: str, value: SinceLastVisit | None) -> None:
    _set(conn, cid, "since_last_visit", value.model_dump_json() if value else "")
    conn.commit()
    bump(conn, cid)


def reset_all(conn, customers: list[str]) -> None:
    """Back to the clean starting state for everyone. facts_version only goes up, so clients refetch."""
    old = {c: facts_version(conn, c) for c in customers}
    for t in db.TABLES:
        conn.execute(f"DELETE FROM {t}")
    for c in customers:
        for k, v in db.DEFAULTS.items():
            _set(conn, c, k, v)
        _set(conn, c, "facts_version", str(old[c] + 1))
    conn.commit()
