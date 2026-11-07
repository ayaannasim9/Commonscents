"""Seeded 18-month transaction generator for the persona.

Each month has its own RNG (`Random(f"{seed}-{year}-{month}")`) so history is
stable when "next month" appends. Events are placed in a named month.
"""
from __future__ import annotations

import calendar
import random
from datetime import date, timedelta

from . import config
from .models import Persona, PlantedEvent, Transaction

PENSION_ANCHOR = date(2026, 11, 3)  # a State Pension payday; others are +/- 28 days
STATE_PENSION = 76000
WORK_PENSION = 52000
RENT = 48000
COUNCIL_TAX = 11800
PHONE_BEFORE_APRIL_2026, PHONE_AFTER = 2800, 3000
ELECTRICITY = 3200
GAS_WINTER, GAS_SUMMER = 8600, 4300
WATER = 2800
TV_LICENCE = 17500
CASH_WEEKLY = 4000
SHOP_MONTH_TOTAL = 9200  # eight trips, split randomly; total steady
SHOP_TRIPS = 8
CHEMIST_MONTH_TOTAL = 2400
SUBSCRIPTION = 999
SCAM_AMOUNT = 200000

_RAW = tuple[date, str | None, str, int, str]  # date, time, description, pence, channel


def _month_add(y: int, m: int, n: int) -> tuple[int, int]:
    i = y * 12 + (m - 1) + n
    return i // 12, i % 12 + 1


def months_ending(end: tuple[int, int], months: int) -> list[tuple[int, int]]:
    return [_month_add(*end, -(months - 1) + i) for i in range(months)]


def _prev_weekday(d: date) -> date:
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def _split(rng: random.Random, total: int, n: int) -> list[int]:
    weights = [rng.uniform(0.6, 1.4) for _ in range(n)]
    parts = [int(total * w / sum(weights)) for w in weights]
    parts[-1] += total - sum(parts)
    return parts


def _hhmm(rng: random.Random, lo_h: int, hi_h: int) -> str:
    return f"{rng.randint(lo_h, hi_h):02d}:{rng.randint(0, 59):02d}"


def _month_raw(y: int, m: int, events: list[PlantedEvent], seed: int) -> list[_RAW]:
    rng = random.Random(f"{seed}-{y}-{m}")
    last = calendar.monthrange(y, m)[1]
    out: list[_RAW] = []
    add = lambda d, t, desc, p, ch: out.append((d, t, desc, p, ch))  # noqa: E731

    # Event effects carry forward from the month they were planted.
    def active(name: str) -> PlantedEvent | None:
        for e in events:
            if e.name == name and (e.year, e.month) <= (y, m):
                return e
        return None

    # --- income ---
    n = (date(y, m, 1) - PENSION_ANCHOR).days // 28 - 1
    d = PENSION_ANCHOR + timedelta(days=28 * n)
    while d.year * 12 + d.month <= y * 12 + m:
        if (d.year, d.month) == (y, m):
            add(d, None, "DWP STATE PENSION 4WK", STATE_PENSION, "credit")
        d += timedelta(days=28)
    add(_prev_weekday(date(y, m, 25)), None, "NEST PENSN 7783", WORK_PENSION, "credit")

    # --- direct debits ---
    add(date(y, m, 1), None, "DD HARROWGATE HOUSING 0071", -RENT, "direct_debit")
    if m not in (2, 3):  # council tax: 10 months a year
        add(date(y, m, 3), None, "DD LBROUGH CNCL TAX 5532", -COUNCIL_TAX, "direct_debit")
    phone = PHONE_AFTER if (y, m) >= (2026, 4) else PHONE_BEFORE_APRIL_2026  # April price rise
    add(date(y, m, 8), None, "DD VF BBAND/TV 8830", -phone, "direct_debit")
    add(date(y, m, 12), None, "DD EDF ENERGY 7710", -ELECTRICITY, "direct_debit")
    winter = m in (11, 12, 1, 2, 3)
    add(date(y, m, 15), None, "DD BGAS 4421 ENERGY", -(GAS_WINTER if winter else GAS_SUMMER), "direct_debit")
    water = WATER
    if active("price_rise"):
        water = round(WATER * 1.18)  # +18%
    add(date(y, m, 20), None, "DD SEVERN TRENT 0912", -water, "direct_debit")
    if m == 1:
        add(date(y, m, 5), None, "DD TV LICENCE MBP", -TV_LICENCE, "direct_debit")

    # --- cash every Friday ---
    for day in range(1, last + 1):
        if date(y, m, day).weekday() == 4:
            add(date(y, m, day), _hhmm(rng, 10, 11), "POST OFFICE CNTR WDL", -CASH_WEEKLY, "cash_withdrawal")

    # --- small card spends ---
    for amt in _split(rng, SHOP_MONTH_TOTAL, SHOP_TRIPS):
        add(date(y, m, rng.randint(1, last)), _hhmm(rng, 9, 16), "CRD 4471 PATELS NEWS&FOOD", -amt, "card")
    for amt in _split(rng, CHEMIST_MONTH_TOTAL, 2):
        add(date(y, m, rng.randint(1, last)), _hhmm(rng, 10, 15), "CRD 4471 BOOTS PHARM 0231", -amt, "card")

    # --- planted events ---
    if active("forgotten_subscription"):
        add(date(y, m, 9), "00:30", "CRD 4471 STREAMFLIX*MEMBER", -SUBSCRIPTION, "card")
    for e in events:
        if e.name == "scam_transfer" and (e.year, e.month) == (y, m):
            add(date(y, m, 18), "21:14", "FASTER PMT TO M HOLLOWAY 04-00-75 ****3391", -SCAM_AMOUNT, "faster_payment")
    return out


def generate(
    persona: Persona,
    months: int = 18,
    events: list[PlantedEvent | str] | None = None,
    end: tuple[int, int] = (2026, 11),
    seed: int | None = None,
) -> list[Transaction]:
    """18 months of transactions ending at `end`. String events land in the end month."""
    seed = config.SEED if seed is None else seed
    evs = [e if isinstance(e, PlantedEvent) else PlantedEvent(name=e, year=end[0], month=end[1]) for e in events or []]
    raw: list[_RAW] = []
    for y, m in months_ending(end, months):
        raw.extend(_month_raw(y, m, evs, seed))
    raw.sort(key=lambda r: (r[0], r[1] or ""))  # stable: ties keep insertion order
    return [
        Transaction(id=f"tx_{i:04d}", date=d, time=t, description=desc, amount_pence=p, channel=ch)
        for i, (d, t, desc, p, ch) in enumerate(raw, 1)
    ]
