"""One World per app: builds facts and the section text ONCE per (customer, facts_version), so the
dashboard and the letter read the same strings (P9). Every method takes a customer id; the code path
is identical for all six personas, only their data differs."""
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
from .models import Facts, Transaction
from .personas import DEFAULT_ID, SPECS, PersonaSpec
from .pipeline import build_facts

TITLES = {"headline": "How things look", "last_month": "Last month", "forecast": "The next three months",
          "idea": "One idea", "scam_watch": "Scam watch", "since_visit": "Since your last visit",
          "ask": "Ask a question"}


class UnknownCustomer(KeyError):
    pass


class World:
    def __init__(self, conn: sqlite3.Connection, client: LLMClient | None = None):
        self.conn, self.client = conn, client or LLMClient()
        self.lock = threading.RLock()
        self._sections: dict[str, tuple[int, Guarded]] = {}

    def spec(self, cid: str) -> PersonaSpec:
        try:
            return SPECS[cid]
        except KeyError:
            raise UnknownCustomer(cid)

    # -- data --
    def transactions(self, cid: str) -> list[Transaction]:
        return generate(self.spec(cid), months=18, events=state.events(self.conn, cid), end=state.last_full_month(self.conn, cid))

    def facts(self, cid: str) -> Facts:
        return build_facts(self.spec(cid).profile(), self.transactions(cid), state.as_of(self.conn, cid),
                           state.since_last_visit(self.conn, cid))

    # -- text (cached per customer and facts_version) --
    def guarded(self, cid: str, *, force: bool = False, demo_bad_number: bool = False) -> tuple[Facts, Guarded]:
        with self.lock:
            v = state.facts_version(self.conn, cid)
            facts = self.facts(cid)
            cached = self._sections.get(cid)
            if force or demo_bad_number or not cached or cached[0] != v:
                g = write_sections(facts, self.client, self.conn, demo_bad_number)
                self._sections[cid] = (v, g)
            return facts, self._sections[cid][1]

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

    def dashboard(self, cid: str, **kw) -> dict:
        facts, g = self.guarded(cid, **kw)
        return {"as_of": facts.as_of.isoformat(), "facts_version": state.facts_version(self.conn, cid),
                "facts": facts.to_contract(), "guardrail": g.guardrail,
                "sections": self.section_list(facts, g.texts)}

    # -- letters --
    def _row(self, r) -> dict:
        return {"letter_id": f"letter_{r['id']:04d}", "status": r["status"], "html": r["html"],
                "sections": json.loads(r["sections_json"]), "guardrail": json.loads(r["guardrail_json"])}

    def new_letter(self, cid: str, **kw) -> dict:
        with self.lock:
            facts, g = self.guarded(cid, **kw)
            sections = self.section_list(facts, g.texts)
            cur = self.conn.execute(
                "INSERT INTO letters(customer, facts_version, status, html, sections_json, guardrail_json, created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (cid, state.facts_version(self.conn, cid), "draft", render_letter(facts, sections), json.dumps(sections),
                 json.dumps(g.guardrail), datetime.now(ZoneInfo("Europe/London")).isoformat(timespec="seconds")))
            self.conn.commit()
            return self._row(self.conn.execute("SELECT * FROM letters WHERE id=?", (cur.lastrowid,)).fetchone())

    def current_letter(self, cid: str) -> dict:
        """Latest letter for the current facts; a fresh draft if the facts have moved on."""
        with self.lock:
            r = self.conn.execute("SELECT * FROM letters WHERE customer=? AND facts_version=? ORDER BY id DESC LIMIT 1",
                                  (cid, state.facts_version(self.conn, cid))).fetchone()
            return self._row(r) if r else self.new_letter(cid)

    def approve_letter(self, cid: str) -> dict:
        with self.lock:
            cur = self.current_letter(cid)
            self.conn.execute("UPDATE letters SET status='approved' WHERE id=?", (int(cur["letter_id"].split("_")[1]),))
            self.conn.commit()
            return {"letter_id": cur["letter_id"], "status": "approved"}

    def letter_pdf(self, cid: str, preview: bool = False) -> bytes:
        """PDF of the customer's latest APPROVED letter (P3). preview=True renders the current draft with a banner."""
        from weasyprint import HTML  # imported here so the API starts even if pango is missing

        with self.lock:
            if preview:
                html = self.current_letter(cid)["html"].replace(
                    "<body>", '<body><p style="border:2px solid #2B0D3E;padding:3mm;font-weight:bold">'
                              "DRAFT: not yet approved by a helper. Not for posting.</p>", 1)
            else:
                r = self.conn.execute("SELECT html FROM letters WHERE customer=? AND status='approved' ORDER BY id DESC LIMIT 1",
                                      (cid,)).fetchone()
                if not r:
                    raise LookupError("No approved letter yet")
                html = r["html"]
        return HTML(string=html).write_pdf()

    def clear_cache(self) -> None:
        self._sections.clear()

    # -- transparency (C6, P7) --
    def what_we_know(self, cid: str) -> dict:
        c = self.conn
        n = lambda q: c.execute(q, (cid,)).fetchone()[0]  # noqa: E731
        held = [
            ("Your details", "Your name, age, bank, and the day you visit the hub.", 1),
            ("Your bank payments", "Money in and out of your account, for the last 18 months.", len(self.transactions(cid))),
            ("Your letters", "Each monthly letter we have prepared for you.", n("SELECT COUNT(*) FROM letters WHERE customer=?")),
            ("Your questions", "Questions you have asked, and the replies sent.", n("SELECT COUNT(*) FROM cases WHERE customer=?")),
            ("Helper notes", "Notes your helper wrote after talking with you.",
             n("SELECT COUNT(*) FROM cases WHERE customer=? AND helper_note IS NOT NULL")),
        ]
        log = c.execute("SELECT at, who, role, what FROM access_log WHERE customer=? ORDER BY at DESC, id DESC", (cid,))
        return {"profile": self.spec(cid).profile().model_dump(mode="json"),
                "data_held": [{"label": a, "description": b, "count": k} for a, b, k in held],
                "access_log": [dict(r) for r in log]}

    def log_access(self, cid: str, who: str, role: str, what: str) -> None:
        at = datetime.combine(state.as_of(self.conn, cid), datetime.now(ZoneInfo("Europe/London")).time()).replace(microsecond=0)
        self.conn.execute("INSERT INTO access_log(customer, at, who, role, what) VALUES (?,?,?,?,?)",
                          (cid, at.isoformat(), who, role, what))
        self.conn.commit()


__all__ = ["World", "UnknownCustomer", "DEFAULT_ID"]
