"""Plain sqlite3. Every table that holds customer data carries a `customer` column (plan B8.1)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 3  # bump when a table changes; a dev database with another version is rebuilt

SCHEMA = """
CREATE TABLE IF NOT EXISTS demo_state (
  customer TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (customer, key)
);
CREATE TABLE IF NOT EXISTS planted_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer TEXT NOT NULL,
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
  customer TEXT NOT NULL,
  facts_version INTEGER NOT NULL,
  status TEXT NOT NULL,
  html TEXT NOT NULL,
  sections_json TEXT NOT NULL,
  guardrail_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cases (
  id INTEGER PRIMARY KEY,
  customer TEXT NOT NULL,
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
  customer TEXT NOT NULL,
  at TEXT NOT NULL,
  who TEXT NOT NULL,
  role TEXT NOT NULL,
  what TEXT NOT NULL
);
"""

TABLES = ["demo_state", "planted_events", "guardrail_events", "letters", "cases", "access_log"]
DEFAULTS = {"as_of": "2026-12-01", "facts_version": "1", "since_last_visit": ""}


def connect(path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection, customers: list[str] | tuple[str, ...] = ()) -> None:
    if conn.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
        for t in TABLES:
            conn.execute(f"DROP TABLE IF EXISTS {t}")
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.executescript(SCHEMA)
    for cid in customers:
        for k, v in DEFAULTS.items():
            conn.execute("INSERT OR IGNORE INTO demo_state(customer, key, value) VALUES (?,?,?)", (cid, k, v))
    conn.commit()
