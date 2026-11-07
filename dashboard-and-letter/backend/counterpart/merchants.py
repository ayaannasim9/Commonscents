"""Merchant lookup: cryptic bank description -> plain name, category, cadence.

Unknown descriptions return a neutral "Something else" unless a `fallback`
(the LLM categoriser, wired up in B4, result cached by the caller) is supplied.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

Cadence = str  # 4weekly | monthly | annual | weekly | seasonal | average | oneoff


@dataclass(frozen=True)
class Merchant:
    key: str
    plain_name: str
    category: str
    cadence: Cadence
    reason: str | None = None  # wording used when this item drives a forecast month

    @property
    def reason_label(self) -> str:
        return self.reason or self.plain_name.lower()


_RULES: list[tuple[re.Pattern, Merchant]] = [
    (re.compile(r"HARROWGATE HOUSING"), Merchant("rent", "Rent", "housing", "monthly")),
    (re.compile(r"CNCL TAX"), Merchant("council_tax", "Council tax", "tax", "monthly")),
    (re.compile(r"DWP STATE PENSION"), Merchant("state_pension", "State Pension", "income", "4weekly", "State Pension")),
    (re.compile(r"NEST PENSN"), Merchant("work_pension", "Work pension", "income", "monthly", "work pension")),
    (re.compile(r"VF BBAND/TV"), Merchant("phone_tv", "Phone and TV", "phone_tv", "monthly")),
    (re.compile(r"EDF ENERGY"), Merchant("electricity", "Electricity", "energy", "monthly")),
    (re.compile(r"BGAS .*ENERGY"), Merchant("gas", "Gas", "energy", "seasonal")),
    (re.compile(r"SEVERN TRENT"), Merchant("water", "Water", "water", "monthly", "water bill")),
    (re.compile(r"TV LICENCE"), Merchant("tv_licence", "TV licence", "licence", "annual", "TV licence")),
    (re.compile(r"POST OFFICE CNTR WDL"), Merchant("cash", "Cash from the Post Office", "cash", "weekly")),
    (re.compile(r"PATELS NEWS"), Merchant("local_shop", "Local shop", "shopping", "average")),
    (re.compile(r"BOOTS PHARM"), Merchant("chemist", "Chemist", "health", "average")),
    (re.compile(r"STREAMFLIX"), Merchant("streaming", "Monthly streaming payment", "subscription", "monthly", "new monthly payment")),
    (re.compile(r"FASTER PMT TO"), Merchant("new_payee", "Payment to a new person", "transfer", "oneoff")),
]

UNKNOWN = Merchant("unknown", "Something else", "other", "oneoff")


def categorise(description: str, fallback: Callable[[str], Merchant] | None = None) -> Merchant:
    for pattern, merchant in _RULES:
        if pattern.search(description):
            return merchant
    return fallback(description) if fallback else UNKNOWN


def payee_of(description: str) -> str | None:
    """Payee name from a faster-payment description, else None."""
    m = re.search(r"FASTER PMT TO (.+?) \d\d-\d\d-\d\d", description)
    return m.group(1) if m else None
