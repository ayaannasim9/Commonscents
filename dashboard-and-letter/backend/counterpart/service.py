"""One World per app: builds facts and the section text ONCE per facts_version, so the
dashboard and the letter read the same strings (P9)."""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from . import state
from .generator import generate
from .guardrails import Guarded
from .letter import render_letter
from .llm.client import LLMClient
from .llm.writers import write_sections
from .models import Facts, Persona, Transaction
from .persona import MARGARET
from .pipeline import build_facts

TITLES = {"headline": "How things look", "last_month": "Last month", "forecast": "The next three months",
          "idea": "One idea", "scam_watch": "Scam watch", "since_visit": "Since your last visit",
          "ask": "Ask a question"}


class World:
    def __init__(self, conn: sqlite3.Connection, client: LLMClient | None = None, persona: Persona = MARGARET):
        self.conn, self.client, self.persona = conn, client or LLMClient(), persona
        self.lock = threading.RLock()
        self._sections: dict[int, Guarded] = {}

    # -- data --
    def transactions(self) -> list[Transaction]:
        y, m = state.last_full_month(self.conn)
        return generate(self.persona, months=18, events=state.events(self.conn), end=(y, m))

    def facts(self) -> Facts:
        return build_facts(self.persona, self.transactions(), state.as_of(self.conn),
                           state.since_last_visit(self.conn))

    # -- text (cached per facts_version) --
    def guarded(self, *, force: bool = False, demo_bad_number: bool = False) -> tuple[Facts, Guarded]:
        with self.lock:
            v = state.facts_version(self.conn)
            facts = self.facts()
            if force or demo_bad_number or v not in self._sections:
                self._sections = {v: write_sections(facts, self.client, self.conn, demo_bad_number)}
            return facts, self._sections[v]

    @staticmethod
    def section_list(facts: Facts, texts: dict[str, str]) -> list[dict]:
        out = []
        for sid in TITLES:
            if sid not in texts:
                continue
            s = {"id": sid, "title": TITLES[sid], "text": texts[sid]}
            if sid == "headline":
                s["status"] = facts.headline_status
            elif sid == "scam_watch":
                s["status"] = "flagged" if facts.flags else "nothing_unusual"
            elif sid == "idea":
                s["optional"] = True
            out.append(s)
        return out

    def dashboard(self, **kw) -> dict:
        facts, g = self.guarded(**kw)
        return {"as_of": facts.as_of.isoformat(), "facts_version": state.facts_version(self.conn),
                "facts": facts.to_contract(), "guardrail": g.guardrail,
                "sections": self.section_list(facts, g.texts)}

    # -- letters --
    def _row(self, r) -> dict:
        return {"letter_id": f"letter_{r['id']:04d}", "status": r["status"], "html": r["html"],
                "sections": json.loads(r["sections_json"]), "guardrail": json.loads(r["guardrail_json"])}

    def new_letter(self, **kw) -> dict:
        with self.lock:
            facts, g = self.guarded(**kw)
            sections = self.section_list(facts, g.texts)
            cur = self.conn.execute(
                "INSERT INTO letters(facts_version, status, html, sections_json, guardrail_json, created_at) VALUES (?,?,?,?,?,?)",
                (state.facts_version(self.conn), "draft", render_letter(facts, sections), json.dumps(sections),
                 json.dumps(g.guardrail), datetime.now(ZoneInfo("Europe/London")).isoformat(timespec="seconds")))
            self.conn.commit()
            return self._row(self.conn.execute("SELECT * FROM letters WHERE id=?", (cur.lastrowid,)).fetchone())

    def current_letter(self) -> dict:
        """Latest letter for the current facts; a fresh draft if the facts have moved on."""
        with self.lock:
            r = self.conn.execute("SELECT * FROM letters WHERE facts_version=? ORDER BY id DESC LIMIT 1",
                                  (state.facts_version(self.conn),)).fetchone()
            return self._row(r) if r else self.new_letter()

    def approve_letter(self) -> dict:
        with self.lock:
            cur = self.current_letter()
            self.conn.execute("UPDATE letters SET status='approved' WHERE id=?", (int(cur["letter_id"].split("_")[1]),))
            self.conn.commit()
            return {"letter_id": cur["letter_id"], "status": "approved"}
