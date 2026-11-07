from __future__ import annotations

from ..models import LastMonth, OutItem, Transaction
from .common import MONTH_NAMES, merchant_of, pounds, ym

TOP_N = 5


def summarise(txs: list[Transaction], year: int, month: int) -> tuple[LastMonth, dict]:
    """Last full month. Rounding is arranged so the page adds up:
    left = in - out - cash in whole pounds, and 'Everything else' absorbs the remainder.
    Returns the model plus raw pence totals (for cash_blind_spot)."""
    mt = [t for t in txs if ym(t.date) == (year, month)]
    money_in = sum(t.amount_pence for t in mt if t.amount_pence > 0)
    cash = -sum(t.amount_pence for t in mt if t.channel == "cash_withdrawal")
    by_name: dict[str, int] = {}
    regular_out = 0  # outgoings (incl. cash) excluding one-offs, for the cash blind-spot test
    for t in mt:
        if t.amount_pence >= 0:
            continue
        m = merchant_of(t)
        if t.channel != "cash_withdrawal":
            by_name[m.plain_name] = by_name.get(m.plain_name, 0) - t.amount_pence
        if m.cadence != "oneoff":
            regular_out += -t.amount_pence
    out_total = sum(by_name.values())

    ranked = sorted(by_name.items(), key=lambda kv: (-kv[1], kv[0]))
    top, rest = ranked[:TOP_N], ranked[TOP_N:]
    items = [OutItem(name=n, amount=pounds(p)) for n, p in top]
    if rest:
        items.append(OutItem(name="Everything else", amount=pounds(out_total) - sum(i.amount for i in items)))
    lm = LastMonth(
        month=MONTH_NAMES[month - 1], year=year,
        in_=pounds(money_in), out=items, cash=pounds(cash),
        left=pounds(money_in) - pounds(out_total) - pounds(cash),
    )
    return lm, {"cash": cash, "regular_out": regular_out}
