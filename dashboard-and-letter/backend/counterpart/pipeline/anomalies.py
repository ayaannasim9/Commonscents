from __future__ import annotations

from datetime import date
from statistics import median

from ..merchants import payee_of
from ..models import Flag, Transaction
from .common import add_months, merchant_of, pounds, ym

UNUSUAL_MULTIPLE = 3         # amount > 3x her usual payment
PRICE_RISE = 1.15            # recurring bill up >= 15%
UNUSUAL_HOURS = (21, 7)      # 21:00 to 07:00
NEW_PAYMENT_WINDOW = 2       # months


def _late(time: str | None) -> bool:
    if not time:
        return False
    h = int(time[:2])
    return h >= UNUSUAL_HOURS[0] or h < UNUSUAL_HOURS[1]


def _times(n: float) -> str:
    return "Many times your usual payment" if n >= 100 else f"About {round(n)} times your usual payment"


def usual_payment_pence(txs: list[Transaction], year: int, month: int) -> int:
    """Median of her bills and transfers before the given month (what 'usual' means in flags)."""
    return round(median(-t.amount_pence for t in txs if ym(t.date) < (year, month)
                        and t.amount_pence < 0 and t.channel in ("direct_debit", "faster_payment")))


def anomalies(txs: list[Transaction], year: int, month: int) -> list[Flag]:
    """Flags about the last full month (subscriptions: first seen within two months)."""
    flags: list[Flag] = []
    target = (year, month)
    before = [t for t in txs if ym(t.date) < target]

    # usual payment = median of her earlier bills and transfers (small card spends and cash excluded,
    # otherwise the median is a few pounds and everything looks enormous)
    usual = median(-t.amount_pence for t in before
                   if t.amount_pence < 0 and t.channel in ("direct_debit", "faster_payment"))
    seen_payees = {payee_of(t.description) for t in before} - {None}

    for t in (t for t in txs if ym(t.date) == target and t.amount_pence < 0):
        payee = payee_of(t.description)
        if payee and payee not in seen_payees and -t.amount_pence > UNUSUAL_MULTIPLE * usual:
            reasons = ["First time you have paid this person", _times(-t.amount_pence / usual)]
            late = _late(t.time)
            if late:
                reasons.append("Made late in the evening")
            high = late or -t.amount_pence > 10 * usual
            flags.append(Flag(
                id="", kind="unusual_payment", severity="high" if high else "medium", date=t.date,
                amount=pounds(-t.amount_pence), plain_name=merchant_of(t).plain_name, reasons=reasons,
            ))

    # new regular payment: subscription-category payee first seen within the window
    by_key: dict[str, list[Transaction]] = {}
    for t in txs:
        if merchant_of(t).category == "subscription":
            by_key.setdefault(merchant_of(t).key, []).append(t)
    for ts in by_key.values():
        first = min(ts, key=lambda t: t.date)
        if add_months(*ym(first.date), NEW_PAYMENT_WINDOW) >= target:
            flags.append(Flag(
                id="", kind="new_regular_payment", severity="medium", date=first.date,
                amount=pounds(-first.amount_pence), plain_name="New monthly payment",
                reasons=["A new card payment started that you may not know about",
                         "It is likely to come out every month"],
            ))

    # price rise: a monthly bill up >= 15% on its previous payment
    by_bill: dict[str, list[Transaction]] = {}
    for t in txs:
        m = merchant_of(t)
        if m.cadence == "monthly" and t.amount_pence < 0 and ym(t.date) <= target and m.category not in ("subscription", "transfer_regular"):
            by_bill.setdefault(m.key, []).append(t)
    for ts in by_bill.values():
        ts.sort(key=lambda t: t.date)
        # amounts are negative, so a bigger bill is more negative
        if len(ts) >= 2 and ym(ts[-1].date) == target and ts[-1].amount_pence <= PRICE_RISE * ts[-2].amount_pence:
            new, old = pounds(-ts[-1].amount_pence), pounds(-ts[-2].amount_pence)
            flags.append(Flag(
                id="", kind="price_rise", severity="info", date=ts[-1].date, amount=new,
                plain_name=f"{merchant_of(ts[-1]).plain_name} bill went up",
                reasons=[f"It was £{old} and is now £{new}", f"That is £{new - old} more each month"],
            ))

    flags.sort(key=lambda f: (f.date, f.kind))
    return [f.model_copy(update={"id": f"flag_{i:04d}"}) for i, f in enumerate(flags, 1)]
