from __future__ import annotations

from datetime import date

from ..models import Facts, FactsCustomer, Persona, SinceLastVisit, Suggestion, Transaction
from .anomalies import anomalies
from .common import add_months
from .forecast import forecast
from .summarise import summarise

CASH_BLIND_SPOT = 0.10          # cash >= 10% of regular outgoings
GENTLE_SAVING = 20              # illustrative default, £ a month
SMALL_SAVING = 10               # when last month's spare was under £100


def _suggestion(last_left: int, months) -> Suggestion | None:
    """One gentle, non-advisory idea, aimed at the worst coming month that has a cost to plan for."""
    tight = [m for m in months if m.status in ("warn", "short") and m.extra > 0 and m.reason != "lower income"]
    if not tight or last_left <= 0:
        return None
    worst = max(tight, key=lambda m: (m.status == "short", m.extra))
    return Suggestion(text_hint=f"put a little aside for the {worst.reason}",
                      amount=GENTLE_SAVING if last_left >= 100 else SMALL_SAVING)


def build_facts(
    persona: Persona,
    txs: list[Transaction],
    as_of: date,
    since_last_visit: SinceLastVisit | None = None,
) -> Facts:
    ly, lm_ = add_months(as_of.year, as_of.month, -1)
    last_month, raw = summarise(txs, ly, lm_)
    months = forecast(txs, (as_of.year, as_of.month))
    flags = anomalies(txs, ly, lm_)

    if any(f.severity == "high" for f in flags) or any(m.status == "short" for m in months):
        status = "attention"
    elif any(m.status == "warn" for m in months) or any(f.severity == "medium" for f in flags):
        status = "heads_up"
    else:
        status = "good"

    return Facts(
        as_of=as_of,
        customer=FactsCustomer(name=persona.name, reference=persona.id, bank=persona.bank, hub_day=persona.hub_day),
        headline_status=status,
        last_month=last_month,
        forecast=months,
        suggestion=_suggestion(last_month.left, months),
        flags=flags,
        since_last_visit=since_last_visit,
        cash_blind_spot=raw["regular_out"] > 0 and raw["cash"] >= CASH_BLIND_SPOT * raw["regular_out"],
    )
