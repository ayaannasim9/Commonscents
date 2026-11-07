"""Writers: facts in, guardrail-checked words out. LLM first (live/cached), templates otherwise."""
from __future__ import annotations

import re
import sqlite3

from ..guardrails import Guarded, allowed_numbers, corrupt_with_bad_number, run_guarded
from ..models import Facts
from . import prompts, templates
from .client import LLMClient, LLMUnavailable

_KEEP = {"headline", "last_month", "forecast", "idea", "scam_watch", "since_visit", "ask"}


def write_sections(
    facts: Facts,
    client: LLMClient | None = None,
    conn: sqlite3.Connection | None = None,
    demo_bad_number: bool = False,
) -> Guarded:
    """The one function that produces letter/dashboard text (P9: both views share its output)."""
    client = client or LLMClient()
    allowed = allowed_numbers(facts)
    base = templates.sections(facts)

    def produce(attempt: int) -> dict[str, str]:
        if client.mode == "stub":
            out = dict(base)
        else:
            raw = client.complete_json(prompts.LETTER_SYSTEM, prompts.letter_user(facts.to_contract(), attempt), attempt=attempt)
            out = {k: str(v).strip() for k, v in raw.items() if k in _KEEP and str(v).strip()}
            missing = set(base) - set(out)
            if missing:
                raise LLMUnavailable(f"missing sections: {sorted(missing)}")
            if "idea" in out and "idea" not in base:
                del out["idea"]  # never invent a suggestion code did not produce
        if demo_bad_number and attempt == 0:
            out = corrupt_with_bad_number(out, allowed)
        return out

    try:
        g = run_guarded(produce, allowed, fallback=lambda: dict(base), conn=conn, context="letter")
    except LLMUnavailable:
        g = run_guarded(lambda n: dict(base), allowed, conn=conn, context="letter")
        g.source = "fallback"
        return g
    if client.mode == "stub" and g.source == "llm":
        g.source = "stub"
    return g


# ---- triage (urgency rules are code; the model may only add to them) ----

# Urgency is a code rule (CLAUDE.md): calls, texts, or someone asking for money. "called" on its own is
# not a phone call ("what is this payment called?"), so only calls to or from her count.
_CALLS = (r"phone[ds]?\b|rang\b|ringing|(?:called|calls|calling)\s+(?:me|us)|a (?:phone )?call|phone call|"
          r"text(?:ed|s|ing)?\b|sms|e-?mail(?:ed|s)?")
_URGENT = re.compile(rf"\b(?:{_CALLS}|asked? (?:me )?for money|send (?:them|him|her) money|scam|fraud|suspicious|gift cards?)", re.I)
_CATEGORY = [
    ("scam_worry", re.compile(rf"\b(?:scam|fraud|suspicious|{_CALLS}|asked? (?:me )?for money)", re.I)),
    ("afford_purchase", re.compile(r"\b(afford|buy|boiler|new (fridge|cooker|washing)|replace|cost)\b", re.I)),
    ("bill_query", re.compile(r"\b(bill|council tax|gas|electric|water|licence|direct debit|price)\b", re.I)),
    ("payment_query", re.compile(r"\b(payment|paid|took|taken|charge[ds]?|transaction|what is this)\b", re.I)),
]


def afford_object(text: str) -> str | None:
    """'Can I afford a new boiler?' -> 'a new boiler'."""
    m = re.search(r"afford\s+(.+)$", text.strip().rstrip("?.! "), re.I)
    return m.group(1) if m else None


def plain_summary(category: str, text: str) -> str:
    t = text.strip().rstrip("?.! ")
    if category == "afford_purchase":
        obj = afford_object(t)
        return f"Asking about affording {obj}" if obj else t[:140]
    if category == "scam_worry":
        return "Worried about a possible scam"
    if category in ("bill_query", "payment_query"):
        return f"Question about {'a bill' if category == 'bill_query' else 'a payment'}: {t[:100]}"
    return t[:140] or "A question"


def triage(text: str, ticks: list[str] | None = None, client: LLMClient | None = None) -> dict:
    ticks = ticks or []
    urgent = bool(_URGENT.search(text)) or bool({"worried", "scam_call", "scam"} & set(ticks))
    category = next((c for c, rx in _CATEGORY if rx.search(text)), "general")
    if "scam_call" in ticks and category == "general":
        category = "scam_worry"
    for tick, cat in (("afford", "afford_purchase"), ("bill", "bill_query")):
        if tick in ticks and category == "general":
            category = cat
    summary = plain_summary(category, text)
    client = client or LLMClient()
    try:
        r = client.complete_json(prompts.TRIAGE_SYSTEM, f"QUESTION:\n{text}\nTICKS: {ticks}")
        if r.get("category") in {c for c, _ in _CATEGORY} | {"general"}:
            category = r["category"]
        urgent = urgent or r.get("urgency") == "high"  # the model can raise urgency, never lower it
        summary = str(r.get("summary") or summary)[:200]
    except LLMUnavailable:
        pass
    return {"category": category, "urgency": "high" if urgent else "normal", "summary": summary}


def draft_reply(
    facts: Facts, question: str, helper: str, note: str, numbers: list[int],
    client: LLMClient | None = None, conn: sqlite3.Connection | None = None,
) -> Guarded:
    """Reply draft; may use only the facts plus the case's briefing numbers (C5)."""
    client = client or LLMClient()
    allowed = allowed_numbers(facts, extra=numbers)
    fb = lambda: {"text": templates.reply(facts.customer.name, helper, note, numbers)}  # noqa: E731

    def produce(attempt: int) -> dict[str, str]:
        if client.mode == "stub":
            return fb()
        user = (f"FACTS:\n{prompts.j(facts.to_contract())}\nNUMBERS: {numbers}\nQUESTION: {question}\n"
                f"HELPER: {helper}\nHELPER NOTE: {note}" + (prompts.RETRY_NOTE if attempt else ""))
        r = client.complete_json(prompts.REPLY_SYSTEM, user, attempt=attempt)
        if not str(r.get("text", "")).strip():
            raise LLMUnavailable("empty reply")
        return {"text": str(r["text"]).strip()}

    try:
        g = run_guarded(produce, allowed, fallback=fb, conn=conn, context="reply")
    except LLMUnavailable:
        g = run_guarded(lambda n: fb(), allowed, conn=conn, context="reply")
        g.source = "fallback"
        return g
    if client.mode == "stub" and g.source == "llm":
        g.source = "stub"
    return g
