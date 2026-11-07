"""B3 guardrails (P2, P6): every customer-facing text is checked by code, never trusted.

- check_numbers: every £ amount in the text must exist in the facts (whole-pound rounding allowed).
- check_banned: no links, phone numbers, QR codes, or requests for details.
- run_guarded: retry the writer up to MAX_RETRIES times, log what was caught, then fall back
  (templated text) or raise GuardrailFailure. Nothing unverified is ever returned.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Callable, Iterable, Literal
from zoneinfo import ZoneInfo

MAX_RETRIES = 2
LONDON = ZoneInfo("Europe/London")

# ---------- numbers ----------

# £1,280  £9.99  £ 20   and   "20 pounds"
_POUND_SIGN = re.compile(r"£\s?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{1,2}))?")
_POUND_WORD = re.compile(r"\b(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{1,2}))?\s*(?:pounds?|quid)\b", re.I)


def _to_decimal(whole: str, pence: str | None) -> Decimal:
    return Decimal(whole.replace(",", "") + ("." + pence if pence else ""))


def _round_pound(d: Decimal) -> int:
    return int(d.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def extract_amounts(text: str) -> list[tuple[str, Decimal]]:
    """(as written, value) for every £ amount in the text."""
    found = []
    for rx in (_POUND_SIGN, _POUND_WORD):
        for m in rx.finditer(text):
            found.append((m.group(0).strip(), _to_decimal(m.group(1), m.group(2))))
    return found


def _walk(obj: Any, out: set[int]) -> None:
    if isinstance(obj, bool):
        return
    if isinstance(obj, str):
        for _, v in extract_amounts(obj):
            out.add(_round_pound(v))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, int) and not isinstance(v, bool) and k in _MONEY_KEYS:
                out.add(abs(v))
            else:
                _walk(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _walk(v, out)


# Only these integer fields are money. Years, counts and ids are not allowed to
# vouch for a £ figure (so "2026" can never make £2,026 acceptable).
_MONEY_KEYS = {"in", "in_", "amount", "cash", "left", "extra", "spare"}


def allowed_numbers(facts: Any, extra: Iterable[int] = ()) -> set[int]:
    """Whole-pound figures a text may use: the facts' money fields (absolute values, since
    'left' can be negative), £ amounts inside facts strings, plus case-specific extras
    (C5: briefing.numbers values for a reply draft)."""
    data = facts.to_contract() if hasattr(facts, "to_contract") else facts
    out: set[int] = set()
    _walk(data, out)
    out.update(abs(int(x)) for x in extra)
    return out


# ---------- checks ----------

@dataclass(frozen=True)
class Issue:
    check: Literal["numbers", "banned"]
    detail: str


def check_numbers(text: str, facts: Any = None, *, allowed: set[int] | None = None) -> list[Issue]:
    allowed = allowed_numbers(facts) if allowed is None else allowed
    issues = []
    for written, value in extract_amounts(text):
        # exact whole pounds, or pence that round to an allowed pound (£9.99 -> £10)
        if _round_pound(value) not in allowed:
            issues.append(Issue("numbers", f"{written if written.startswith('£') else '£' + str(value)} was not in the facts"))
    return issues


_BANNED: list[tuple[re.Pattern, str]] = [
    (re.compile(r"https?://|\bwww\.|\b[\w-]+\.(?:com|co\.uk|org|net|uk|gov)\b", re.I), "contains a link"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "contains an email address"),
    # UK phone shapes: 0800 123 4567, 01234 567890, +44 ..., and any 10+ digit run with spaces/dashes
    (re.compile(r"(?<![\d£.,])(?:\+44[\s\d()-]{9,}\d|0[\s\d()-]{9,}\d)"), "contains a phone number"),
    (re.compile(r"\b\d(?:[\s-]?\d){9,}\b"), "contains a long number"),
    (re.compile(r"\bQR\b", re.I), "mentions a QR code"),
    (re.compile(r"\bclick", re.I), "tells the reader to click"),
    (re.compile(r"\btap (?:here|the link)\b", re.I), "tells the reader to tap a link"),
    (re.compile(r"\b(?:verify|confirm|update)\s+(?:your|the)\s+(?:details|account|identity|information)\b", re.I), "asks to verify details"),
    (re.compile(r"\burgent action\b", re.I), "uses pressure wording"),
    (re.compile(r"\b(?:act|reply|respond|pay)\s+(?:now|immediately)\b|\bwithin 24 hours\b", re.I), "uses pressure wording"),
    (re.compile(r"\b(?:send|give|tell|share|enter|read out)\b[^.!?]{0,40}\b(?:pin|password|passcode|security code|card number|sort code|account number)\b", re.I), "asks for secret details"),
]


def check_banned(text: str) -> list[Issue]:
    return [Issue("banned", f"{why}: \"{m.group(0).strip()}\"") for rx, why in _BANNED if (m := rx.search(text))]


def check_text(text: str, facts: Any = None, *, allowed: set[int] | None = None) -> list[Issue]:
    return check_numbers(text, facts, allowed=allowed) + check_banned(text)


# ---------- retry / fallback / logging ----------

class GuardrailFailure(Exception):
    def __init__(self, events: list[dict]):
        self.events = events
        super().__init__("; ".join(e["detail"] for e in events) or "guardrail failure")


@dataclass
class Guarded:
    texts: dict[str, str]
    source: Literal["llm", "fallback"]
    guardrail: dict = field(default_factory=lambda: {"caught": False, "events": []})


def _now() -> str:
    return datetime.now(LONDON).replace(microsecond=0, tzinfo=None).isoformat()


def _event(issue: Issue, action: str, where: str) -> dict:
    detail = issue.detail + (f" (in {where})" if where else "")
    return {"at": _now(), "check": issue.check, "detail": detail, "action": action}


def check_texts(texts: dict[str, str], allowed: set[int]) -> list[tuple[str, Issue]]:
    return [(k, i) for k, t in texts.items() for i in check_text(t, allowed=allowed)]


def log_events(conn: sqlite3.Connection | None, events: list[dict], context: str = "") -> None:
    if conn is None or not events:
        return
    conn.executemany(
        'INSERT INTO guardrail_events(at, "check", detail, action, context) VALUES (?,?,?,?,?)',
        [(e["at"], e["check"], e["detail"], e["action"], context) for e in events],
    )
    conn.commit()


def run_guarded(
    produce: Callable[[int], dict[str, str]],
    allowed: set[int],
    *,
    fallback: Callable[[], dict[str, str]] | None = None,
    conn: sqlite3.Connection | None = None,
    context: str = "",
    max_retries: int = MAX_RETRIES,
) -> Guarded:
    """produce(attempt) -> {section_id: text}. Tries 1 + max_retries times.

    Every failed attempt is logged (action "regenerated"; the last one "blocked").
    Then: use `fallback` (templated text, checked too, marked source="fallback"), or raise
    GuardrailFailure. Unchecked text is never returned."""
    events: list[dict] = []
    for attempt in range(max_retries + 1):
        texts = produce(attempt)
        bad = check_texts(texts, allowed)
        if not bad:
            log_events(conn, events, context)
            return Guarded(texts, "llm", {"caught": bool(events), "events": events})
        action = "regenerated" if attempt < max_retries else "blocked"
        events += [_event(i, action, where) for where, i in bad]

    if fallback is not None:
        texts = fallback()
        bad = check_texts(texts, allowed)
        if not bad:
            log_events(conn, events, context)
            return Guarded(texts, "fallback", {"caught": True, "events": events})
        events += [_event(i, "blocked", f"fallback {where}") for where, i in bad]
    log_events(conn, events, context)
    raise GuardrailFailure(events)


# ---------- demo hook (plan D: "?demo=bad-number") ----------

def corrupt_with_bad_number(texts: dict[str, str], allowed: set[int], amount: int = 2400) -> dict[str, str]:
    """For the guardrail-badge demo: the stub writer calls this on its first attempt when the
    hidden `?demo=bad-number` flag is set. Appends a figure that is not in the facts."""
    while amount in allowed:
        amount += 7
    out = dict(texts)
    key = "forecast" if "forecast" in out else next(iter(out))
    out[key] = out[key] + f" You may also need about £{amount:,} for repairs."
    return out
