"""Seeded 18-month transaction generator. One generic engine; a persona is just data (personas.py).

Each month has its own RNG (`Random(f"{seed}-{persona}-{year}-{month}")`) so history is stable when
"next month" appends. Planted events land in a named month and (for subscriptions and price rises)
carry forward.
"""
from __future__ import annotations

import calendar
import random
from datetime import date, timedelta

from . import config
from .models import PlantedEvent, Transaction
from .personas import Item, PersonaSpec

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


def _active(it: Item, y: int, m: int) -> bool:
    if it.kind == "once":
        return it.start == (y, m)
    return (not it.start or (y, m) >= it.start) and m not in it.skip and (it.months is None or m in it.months)


def _amount(it: Item, y: int, m: int, rng: random.Random, price_on: bool) -> int:
    base = it.seasonal.get(m, it.amount)
    for cy, cm, cp in it.changes:
        if (y, m) >= (cy, cm):
            base = cp
    rng_range = it.low.get((y, m), it.rng)
    if rng_range:
        lo, hi = sorted(abs(v) // 100 for v in rng_range)
        base = (1 if (it.rng or rng_range)[0] > 0 else -1) * rng.randint(lo, hi) * 100
    if it.price_event and price_on:
        base = round(base * 1.18)  # +18%
    return base


def _day(it_day: int, y: int, m: int, credit: bool) -> date:
    last = calendar.monthrange(y, m)[1]
    d = date(y, m, last if it_day == -1 else min(it_day, last))
    return _prev_weekday(d) if (credit or it_day == -1) else d


def _bias_days(rng: random.Random, y: int, m: int, bias: str | None) -> int:
    last = calendar.monthrange(y, m)[1]
    if bias:
        want = (lambda wd: wd >= 5) if bias == "weekend" else (lambda wd: wd <= 3)
        pool = [d for d in range(1, last + 1) if want(date(y, m, d).weekday())]
        if pool and (bias == "early_week" or rng.random() < 0.7):
            return rng.choice(pool)
    return rng.randint(1, last)


def _month_raw(spec: PersonaSpec, y: int, m: int, events: list[PlantedEvent], seed: int) -> list[_RAW]:
    rng = random.Random(f"{seed}-{spec.id}-{y}-{m}")
    last = calendar.monthrange(y, m)[1]
    out: list[_RAW] = []

    def active(name: str) -> bool:
        return any(e.name == name and (e.year, e.month) <= (y, m) for e in events)

    price_on = active("price_rise")
    for it in spec.items:
        if not _active(it, y, m):
            continue
        credit = it.channel == "credit"
        if it.kind in ("monthly", "once"):
            out.append((_day(it.day, y, m, credit), None, it.desc, _amount(it, y, m, rng, price_on), it.channel))
        elif it.kind == "annual":
            if it.month == m:
                out.append((_day(it.day, y, m, credit), None, it.desc, _amount(it, y, m, rng, price_on), it.channel))
        elif it.kind == "4weekly":
            d = it.anchor + timedelta(days=28 * ((date(y, m, 1) - it.anchor).days // 28 - 1))
            while (d.year, d.month) <= (y, m):
                if (d.year, d.month) == (y, m):
                    out.append((d, None, it.desc, it.amount, it.channel))
                d += timedelta(days=28)
        elif it.kind == "weekly":
            for day in range(1, last + 1):
                if date(y, m, day).weekday() == it.weekday:
                    t = None if credit else _hhmm(rng, *it.hours)
                    out.append((date(y, m, day), t, it.desc, _amount(it, y, m, rng, price_on), it.channel))
        elif it.kind == "sporadic":
            for _ in range(rng.randint(*it.count)):
                out.append((date(y, m, rng.randint(1, last)), _hhmm(rng, *it.hours), it.desc,
                            _amount(it, y, m, rng, price_on), it.channel))
        elif it.kind == "spread":
            for amt in _split(rng, it.total, it.trips):
                out.append((date(y, m, _bias_days(rng, y, m, it.bias)), _hhmm(rng, *it.hours), it.desc, amt, it.channel))

    # --- planted events (same three for everyone; only the figures are the persona's data) ---
    if active("forgotten_subscription"):
        desc, pence, day = spec.subscription
        out.append((date(y, m, min(day, last)), "00:30", desc, -pence, "card"))
    for e in events:
        if e.name == "scam_transfer" and (e.year, e.month) == (y, m):
            payee, pence, time = spec.scam
            out.append((date(y, m, 18), time, f"FASTER PMT TO {payee}", -pence, "faster_payment"))
    return out


def generate(
    persona: PersonaSpec,
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
        raw.extend(_month_raw(persona, y, m, evs, seed))
    raw.sort(key=lambda r: (r[0], r[1] or ""))  # stable: ties keep insertion order
    return [
        Transaction(id=f"tx_{i:04d}", date=d, time=t, description=desc, amount_pence=p, channel=ch)
        for i, (d, t, desc, p, ch) in enumerate(raw, 1)
    ]
