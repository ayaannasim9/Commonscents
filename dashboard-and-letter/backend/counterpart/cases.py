"""B6 cases + B8 demo loop. One case shape for every source. AI prepares and drafts, a human approves."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import state
from .guardrails import GuardrailFailure, _event, allowed_numbers, check_texts, extract_amounts
from .llm import prompts
from .llm.client import LLMUnavailable
from .llm.writers import draft_reply, plain_summary, triage
from .models import Facts, SinceLastVisit
from .pipeline.anomalies import usual_payment_pence
from .pipeline.common import pounds
from .pipeline.facts import GENTLE_SAVING
from .service import World

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SUMMARY_KEYS = ("id", "source", "status", "urgency", "category", "summary", "created_at", "due", "route")


class CaseError(Exception):
    def __init__(self, status: int, detail):
        self.status, self.detail = status, detail


def case_numbers(briefing: dict) -> list[int]:
    """Figures a reply may use besides the facts: briefing values and £ amounts named in its labels."""
    out = [b["value"] for b in briefing["numbers"]]
    for b in briefing["numbers"]:
        out += [round(v) for _, v in extract_amounts(b["label"])]
    return out


def _id(n: int) -> str:
    return f"case_{n:04d}"


def _num(cid: str) -> int:
    try:
        return int(cid.split("_")[1])
    except (IndexError, ValueError):
        raise CaseError(404, "Unknown case")


class CaseService:
    def __init__(self, world: World):
        self.w = world

    @property
    def conn(self):
        return self.w.conn

    def now(self) -> datetime:
        """Demo date with the real London clock time, so dates agree with as_of."""
        t = datetime.now(ZoneInfo("Europe/London"))
        return datetime.combine(state.as_of(self.conn), t.time()).replace(microsecond=0)

    # ---- routing (simple rules, not ML) ----
    def route(self, urgency: str) -> tuple[dict, str]:
        today = state.as_of(self.conn)
        if urgency == "high":
            return {"team": "phone", "reason": "Urgent: phone team, due today"}, today.isoformat()
        hub = self.w.persona.hub_day
        d = today + timedelta(days=1)
        while WEEKDAYS[d.weekday()] != hub:
            d += timedelta(days=1)
        return {"team": "banker", "reason": f"Next hub day ({hub})"}, d.isoformat()

    # ---- briefing: every number comes from code ----
    def briefing(self, facts: Facts, category: str, question: str | None, system: bool = False) -> dict:
        name = facts.customer.name
        numbers: list[dict] = []
        lm = facts.last_month
        flags = [f for f in facts.flags if f.severity == "high"]
        usual = None
        if category == "scam_worry" and flags:
            f = flags[0]
            y, m = state.last_full_month(self.conn)
            usual = pounds(usual_payment_pence(self.w.transactions(), y, m))
            numbers = [{"label": "Payment", "value": f.amount}, {"label": "Her usual payment is about", "value": usual}]
        else:
            numbers.append({"label": "Left over last month", "value": lm.left})
            if category == "afford_purchase":
                # scenario maths in code; always present, even when the letter withholds its idea
                a = facts.suggestion.amount if facts.suggestion else GENTLE_SAVING
                numbers.append({"label": f"Putting aside £{a} a month for a year", "value": a * 12})
            if category == "payment_query" and flags:
                numbers.append({"label": "Unusual payment last month", "value": flags[0].amount})

        obj = plain_summary("afford_purchase", question or "").removeprefix("Asking if she can afford ")
        item = re.sub(r"^(?:a |an |the )?(?:new )?", "", obj).strip() or "one"
        asking = {
            True: "No question yet. The system noticed a payment that is not like her usual ones.",
        }.get(system) or (
            f"{name} wants to know whether she can afford {obj}." if category == "afford_purchase"
            else f"{name} is worried about a possible scam: \"{question}\"" if category == "scam_worry"
            else f"{name} asks: \"{question}\"")
        checks = {
            "scam_worry": ["Ask whether she made the payment herself.", "Ask if anyone phoned or texted her asking for money.",
                           "If it was not her, explain she can use the number on the back of her bank card."],
            "afford_purchase": [f"Is her current {item} failing, or is she planning ahead?",
                                "Ask if she has a quote, as costs vary a lot.",
                                "Mention that free help is available from MoneyHelper and Citizens Advice.",
                                "Remind her not to share her details with anyone who phones her about it."],
            "bill_query": ["Which bill is she looking at, and what changed?", "Check the bill against her statement together.",
                           "Mention that free help is available from MoneyHelper and Citizens Advice."],
            "payment_query": ["Which payment is she asking about?", "Ask whether she recognises the name on her statement.",
                              "If it is not hers, explain she can use the number on the back of her bank card."],
            "general": ["Make sure you understand what she is asking.", "Mention that free help is available from MoneyHelper and Citizens Advice."],
        }[category]
        asking, checks = self._llm_prep(asking, checks, question, numbers)
        return {"asking": asking, "numbers": numbers, "open_flags": [f.id for f in flags], "things_to_check": checks}

    def _llm_prep(self, asking, checks, question, numbers):
        """Live/cached: let the model reword the briefing text. No figures allowed; templates on any problem."""
        if self.w.client.mode == "stub" or not question:
            return asking, checks
        try:
            r = self.w.client.complete_json(prompts.PREP_SYSTEM, f"QUESTION: {question}\nTEMPLATE: {asking} {checks}")
            a, c = str(r["asking"]).strip(), [str(x).strip() for x in r["things_to_check"]][:5]
            if a and c and not check_texts({"a": a, **{f"c{i}": x for i, x in enumerate(c)}}, set()):
                return a, c
        except (LLMUnavailable, KeyError, TypeError):
            pass
        return asking, checks

    # ---- create ----
    def create(self, source: str, text: str | None, ticks: list[str], *, system_flag: dict | None = None,
               created_at: str | None = None, flag_key: str | None = None) -> dict:
        with self.w.lock:
            facts = self.w.facts()
            if system_flag:
                t = {"category": "scam_worry", "urgency": "high",
                     "summary": f"Unusual £{system_flag['amount']:,} payment to a new person"}
            else:
                t = triage(text or "", ticks, self.w.client)
            route, due = self.route(t["urgency"])
            brief = self.briefing(facts, t["category"], text, system=bool(system_flag))
            cur = self.conn.execute(
                "INSERT INTO cases(source,status,urgency,category,summary,question_text,ticks_json,created_at,due,"
                "route_team,route_reason,briefing_json,flag_key) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (source, "prepared", t["urgency"], t["category"], t["summary"], text, json.dumps(ticks),
                 created_at or self.now().isoformat(), due, route["team"], route["reason"], json.dumps(brief), flag_key))
            self.conn.commit()
            return self._get(cur.lastrowid)

    def open_flag_cases(self, flags: list[dict]) -> str | None:
        """A high-severity flag opens one urgent system_flag case (once per flag)."""
        new_id = None
        for f in flags:
            if f["severity"] != "high":
                continue
            key = f"{f['kind']}|{f['date']}|{f['amount']}"
            if self.conn.execute("SELECT 1 FROM cases WHERE flag_key=?", (key,)).fetchone():
                continue
            new_id = self.create("system_flag", None, [], system_flag=f, flag_key=key)["id"]
        return new_id

    def seed(self) -> None:
        """Demo step 3 works without typing: the boiler question from a Post Office slip."""
        d = state.as_of(self.conn)
        self.create("slip_post_office", "Can I afford a new boiler?", ["afford"], created_at=f"{d.isoformat()}T10:02:00")

    # ---- read ----
    def _row(self, n: int):
        r = self.conn.execute("SELECT * FROM cases WHERE id=?", (n,)).fetchone()
        if not r:
            raise CaseError(404, "Unknown case")
        return r

    def _summary(self, r) -> dict:
        return {"id": _id(r["id"]), "source": r["source"], "status": r["status"], "urgency": r["urgency"],
                "category": r["category"], "summary": r["summary"], "created_at": r["created_at"], "due": r["due"],
                "route": {"team": r["route_team"], "reason": r["route_reason"]}}

    def _full(self, r) -> dict:
        return {**self._summary(r), "question_text": r["question_text"], "ticks": json.loads(r["ticks_json"]),
                "briefing": json.loads(r["briefing_json"]), "helper_note": r["helper_note"],
                "draft": json.loads(r["draft_json"]) if r["draft_json"] else None, "approved_at": r["approved_at"]}

    def _get(self, n: int) -> dict:
        return self._full(self._row(n))

    def list(self, status: str | None = None, urgency: str | None = None) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM cases").fetchall()
        rows = [r for r in rows if (r["status"] == status if status and status != "all" else status == "all" or r["status"] != "closed")
                and (not urgency or r["urgency"] == urgency)]
        rows.sort(key=lambda r: (r["urgency"] != "high", r["due"], r["created_at"], r["id"]))
        return [self._summary(r) for r in rows]

    def view(self, cid: str, viewer: str | None) -> dict:
        """Every case view is logged (P7)."""
        n = _num(cid)
        case = self._get(n)
        who, role = _viewer(viewer)
        self.log(who, role, f"Looked at your question: {case['summary']}" if case["question_text"]
                 else f"Looked at a payment alert: {case['summary']}")
        return case

    def log(self, who: str, role: str, what: str) -> None:
        self.conn.execute("INSERT INTO access_log(at, who, role, what) VALUES (?,?,?,?)",
                          (self.now().isoformat(), who, role, what))
        self.conn.commit()

    # ---- helper actions ----
    def note(self, cid: str, note: str, helper: str) -> dict:
        n = _num(cid)
        with self.w.lock:
            r = self._row(n)
            if r["status"] in ("approved", "closed"):
                raise CaseError(409, "This case is already approved")
            status = "with_helper" if r["status"] in ("new", "prepared") else r["status"]
            self.conn.execute("UPDATE cases SET helper_note=?, helper=?, status=? WHERE id=?", (note.strip(), helper, status, n))
            self.conn.commit()
            return self._get(n)

    def draft_reply(self, cid: str) -> dict:
        n = _num(cid)
        with self.w.lock:
            r = self._row(n)
            if r["status"] in ("approved", "closed"):
                raise CaseError(409, "This case is already approved")
            if not (r["helper_note"] or "").strip():
                raise CaseError(409, "Add a note first: the reply is drafted from it")
            nums = case_numbers(json.loads(r["briefing_json"]))
            try:
                g = draft_reply(self.w.facts(), r["question_text"] or r["summary"], r["helper"] or "Your helper",
                                r["helper_note"], nums, self.w.client, self.conn)
            except GuardrailFailure as e:
                raise CaseError(422, {"message": "The draft was blocked: it contains something the checks do not allow. "
                                                 "Edit the note and try again.", "guardrail": {"caught": True, "events": e.events}})
            return self._save_draft(n, g.texts["text"], g.source, g.guardrail)

    def edit_draft(self, cid: str, text: str) -> dict:
        n = _num(cid)
        with self.w.lock:
            r = self._row(n)
            if r["status"] in ("approved", "closed"):
                raise CaseError(409, "This case is already approved")
            nums = case_numbers(json.loads(r["briefing_json"]))
            bad = check_texts({"draft": text}, allowed_numbers(self.w.facts(), extra=nums))
            events = [_event(i, "blocked", "") for _, i in bad]
            return self._save_draft(n, text, "helper", {"caught": bool(bad), "events": events}, ok=not bad)

    def _save_draft(self, n: int, text: str, source: str, guardrail: dict, ok: bool = True) -> dict:
        draft = {"source": source, "guardrail": guardrail, "text": text}
        status = "draft_ready" if ok else "with_helper"
        self.conn.execute("UPDATE cases SET draft_json=?, status=? WHERE id=?", (json.dumps(draft), status, n))
        self.conn.commit()
        return self._get(n)

    def approve(self, cid: str, helper: str) -> dict:
        """The human approval gate (P3): 409 unless a draft is ready and passed the guardrails."""
        n = _num(cid)
        with self.w.lock:
            r = self._row(n)
            draft = json.loads(r["draft_json"]) if r["draft_json"] else None
            if r["status"] != "draft_ready" or not draft:
                raise CaseError(409, "There is no draft ready to approve")
            if any(e["action"] == "blocked" for e in draft["guardrail"]["events"]):
                raise CaseError(409, "The latest draft did not pass the checks")
            self.conn.execute("UPDATE cases SET status='approved', approved_at=?, helper=? WHERE id=?",
                              (self.now().isoformat(), helper, n))
            self.conn.commit()
            state.bump(self.conn)
            return self._get(n)

    # ---- B8: next month ----
    def advance(self) -> str:
        """Close approved cases; their note becomes next month's 'since your last visit'."""
        with self.w.lock:
            old = state.as_of(self.conn)
            approved = self.conn.execute("SELECT * FROM cases WHERE status='approved' ORDER BY approved_at DESC, id DESC").fetchall()
            new_as_of = state.next_month(self.conn)
            visit = None
            if approved:
                r = approved[0]
                visit = SinceLastVisit(helper=r["helper"] or "Your helper", note=r["helper_note"] or "", date=old)
                self.conn.execute("UPDATE cases SET status='closed' WHERE status='approved'")
                self.conn.commit()
            if visit != state.since_last_visit(self.conn):
                state.set_since_last_visit(self.conn, visit)
            return new_as_of.isoformat()

    def reset(self) -> None:
        self.seed()


def _viewer(viewer: str | None) -> tuple[str, str]:
    """'helper:priya' or 'helper:priya:phone' -> ('Priya', role)."""
    parts = (viewer or "").split(":")
    who = parts[1].strip().title() if len(parts) > 1 and parts[1].strip() else "A helper"
    role = parts[2] if len(parts) > 2 and parts[2] in ("banker", "post_office", "phone") else "banker"
    return who, role
