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
CREATE TABLE IF NOT EXISTS guardrail_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,
  "check" TEXT NOT NULL,
  detail TEXT NOT NULL,
  action TEXT NOT NULL,
  context TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS letters (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  facts_version INTEGER NOT NULL,
  status TEXT NOT NULL,
  html TEXT NOT NULL,
  sections_json TEXT NOT NULL,
  guardrail_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cases (
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,
  status TEXT NOT NULL,
  urgency TEXT NOT NULL,
  category TEXT NOT NULL,
  summary TEXT NOT NULL,
  question_text TEXT,
  ticks_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  due TEXT NOT NULL,
  route_team TEXT NOT NULL,
  route_reason TEXT NOT NULL,
  briefing_json TEXT NOT NULL,
  helper_note TEXT,
  helper TEXT,
  draft_json TEXT,
  approved_at TEXT,
  flag_key TEXT
);
CREATE TABLE IF NOT EXISTS access_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,
  who TEXT NOT NULL,
  role TEXT NOT NULL,
  what TEXT NOT NULL
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
