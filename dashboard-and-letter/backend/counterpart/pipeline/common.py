from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from ..merchants import Merchant, categorise
from ..models import Transaction

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]


def pounds(pence: int) -> int:
    """Whole pounds, half-up, sign preserved (the only place money is rounded)."""
    q = (Decimal(abs(pence)) / 100).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return int(q) * (1 if pence >= 0 else -1)


def add_months(y: int, m: int, n: int) -> tuple[int, int]:
    i = y * 12 + (m - 1) + n
    return i // 12, i % 12 + 1


def ym(d: date) -> tuple[int, int]:
    return d.year, d.month


def merchant_of(tx: Transaction) -> Merchant:
    return categorise(tx.description)


def monthly_totals(txs: list[Transaction]) -> dict[str, dict[tuple[int, int], int]]:
    """item key -> (year, month) -> signed pence."""
    out: dict[str, dict[tuple[int, int], int]] = defaultdict(lambda: defaultdict(int))
    for t in txs:
        out[merchant_of(t).key][ym(t.date)] += t.amount_pence
    return out
