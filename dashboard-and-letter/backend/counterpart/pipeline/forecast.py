from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, timedelta
from statistics import mean

from ..merchants import Merchant
from ..models import ForecastMonth, Transaction
from .common import MONTH_NAMES, add_months, merchant_of, pounds, ym

# Tunable thresholds (plan B2). Tested in tests/test_forecast.py.
WARN_SPARE = 10_000      # warn if spare < £100
WARN_EXTRA = 5_000       # warn if the extra cost >= £50
DRIVER_MIN = 5_000       # an item is only named as the reason if it is >= £50 above usual
INCOME_DIP = 0.85        # income < 85% of the 12-month average counts as a dip
RECENT_MONTHS = 3        # a monthly item must have been seen this recently to be projected


class _Item:
    def __init__(self, merchant: Merchant):
        self.m = merchant
        self.txs: list[Transaction] = []

    @property
    def totals(self) -> dict[tuple[int, int], int]:
        out: dict[tuple[int, int], int] = defaultdict(int)
        for t in self.txs:
            out[ym(t.date)] += t.amount_pence
        return out


def _weekday_count(y: int, m: int, weekday: int) -> int:
    return sum(1 for d in range(1, calendar.monthrange(y, m)[1] + 1) if date(y, m, d).weekday() == weekday)


def _project(item: _Item, y: int, m: int, last_hist: tuple[int, int]) -> int | None:
    """Projected signed pence for `item` in (y, m), or None if it does not occur."""
    cad, tot = item.m.cadence, item.totals
    ordered = sorted(item.txs, key=lambda t: t.date)
    latest = ordered[-1]
    ly = (y - 1, m)
    first_seen = ym(ordered[0].date)
    if cad == "4weekly":
        d, n = latest.date, 0
        while (d.year, d.month) <= (y, m):
            d += timedelta(days=28)
            if (d.year, d.month) == (y, m):
                n += 1
        return n * latest.amount_pence
    if cad == "monthly":
        if add_months(*last_hist, -(RECENT_MONTHS - 1)) > max(tot):
            return None
        if ly in tot or first_seen > ly:  # present same month last year, or new since
            return latest.amount_pence
        return None
    if cad == "annual":
        return tot[ly] if ly in tot else None
    if cad == "weekly":
        return _weekday_count(y, m, 4) * latest.amount_pence
    if cad == "seasonal":
        return tot[ly] if ly in tot else latest.amount_pence
    if cad == "average":
        recent = [tot.get(add_months(*last_hist, -i), 0) for i in range(RECENT_MONTHS)]
        return round(mean(recent))
    return None  # oneoff


def _typical(item: _Item, last_hist: tuple[int, int]) -> int:
    """What this item normally costs in a month it occurs (positive pence), 12-month view."""
    tot = item.totals
    window = [tot[k] for k in (add_months(*last_hist, -i) for i in range(12)) if k in tot]
    if item.m.cadence == "annual" or not window:
        return 0
    return round(-mean(window))


def forecast(txs: list[Transaction], first: tuple[int, int], months: int = 3) -> list[ForecastMonth]:
    """Forecast `months` months starting at `first` (year, month) from history before `first`."""
    last_hist = add_months(*first, -1)
    hist = [t for t in txs if ym(t.date) <= last_hist]
    items: dict[str, _Item] = {}
    for t in hist:
        m = merchant_of(t)
        items.setdefault(m.key, _Item(m)).txs.append(t)

    income_hist = defaultdict(int)
    for t in hist:
        if t.amount_pence > 0:
            income_hist[ym(t.date)] += t.amount_pence
    trailing = [income_hist.get(add_months(*last_hist, -i), 0) for i in range(12)]
    avg_income = mean(trailing)

    result = []
    for k in range(months):
        y, m = add_months(*first, k)
        income = 0
        costs: dict[str, tuple[Merchant, int]] = {}
        four_weekly_payments = 0
        for key, item in items.items():
            p = _project(item, y, m, last_hist)
            if not p:
                continue
            if p > 0:
                income += p
                if item.m.cadence == "4weekly":
                    four_weekly_payments = p // item.txs[-1].amount_pence
            else:
                costs[key] = (item.m, -p)
        spend = sum(c for _, c in costs.values())
        spare = income - spend

        # reason = largest cost above its usual level, else an income story, else nothing
        best: tuple[int, Merchant] | None = None
        for key, (mer, amt) in costs.items():
            extra = amt - _typical(items[key], last_hist)
            if extra >= DRIVER_MIN and (best is None or extra > best[0]):
                best = (extra, mer)
        if best:
            extra, reason = best[0], best[1].reason_label
        elif income < INCOME_DIP * avg_income:
            extra, reason = round(avg_income - income), "lower income"
        elif four_weekly_payments >= 2:
            extra, reason = 0, "two pension payments"
        else:
            extra, reason = 0, "nothing unusual"

        status = "short" if spare < 0 else "warn" if (spare < WARN_SPARE or extra >= WARN_EXTRA) else "ok"
        result.append(ForecastMonth(
            month=MONTH_NAMES[m - 1], year=y, status=status, reason=reason,
            extra=pounds(extra), spare=pounds(spare),
        ))
    return result
