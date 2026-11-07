"""Plain sqlite3. B0 only needs demo state and planted events; later steps add tables."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS demo_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS planted_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  year INTEGER NOT NULL,
  month INTEGER NOT NULL
);
"""

DEFAULTS = {"as_of": "2026-12-01", "facts_version": "1"}


def connect(path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    for k, v in DEFAULTS.items():
        conn.execute("INSERT OR IGNORE INTO demo_state(key, value) VALUES (?, ?)", (k, v))
    conn.commit()
