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


def _m(pattern: str, key: str, plain: str, category: str, cadence: str, reason: str | None = None):
    return re.compile(pattern), Merchant(key, plain, category, cadence, reason)


_RULES: list[tuple[re.Pattern, Merchant]] = [
    _m(r"FASTER PMT TO K ADEYEMI", "rent_so", "Rent", "housing", "monthly"),  # a known landlord, not "a new person"
    (re.compile(r"HARROWGATE HOUSING"), Merchant("rent", "Rent", "housing", "monthly")),
    (re.compile(r"CNCL TAX"), Merchant("council_tax", "Council tax", "tax", "monthly")),
    (re.compile(r"DWP STATE PENSION"), Merchant("state_pension", "State Pension", "income", "4weekly", "pension")),
    (re.compile(r"NEST PENSN"), Merchant("work_pension", "Work pension", "income", "monthly", "work pension")),
    (re.compile(r"VF BBAND/TV"), Merchant("phone_tv", "Phone and TV", "phone_tv", "monthly")),
    (re.compile(r"EDF ENERGY"), Merchant("electricity", "Electricity", "energy", "monthly")),
    (re.compile(r"BGAS .*ENERGY"), Merchant("gas", "Gas", "energy", "seasonal")),
    (re.compile(r"SEVERN TRENT"), Merchant("water", "Water", "water", "monthly", "water bill")),
    (re.compile(r"TV LICENCE|LICNCE"), Merchant("tv_licence", "TV licence", "licence", "annual", "TV licence")),
    (re.compile(r"POST OFFICE CNTR WDL"), Merchant("cash", "Cash from the Post Office", "cash", "weekly")),
    (re.compile(r"PATELS NEWS"), Merchant("local_shop", "Local shop", "shopping", "average")),
    (re.compile(r"BOOTS PHARM"), Merchant("chemist", "Chemist", "health", "average")),
    (re.compile(r"STREAMFLIX"), Merchant("streaming", "Monthly streaming payment", "subscription", "monthly", "new monthly payment")),
    (re.compile(r"FASTER PMT TO"), Merchant("new_payee", "Payment to a new person", "transfer", "oneoff")),
    # ---- added for the other five personas (personas.md); data only, no persona-specific rules ----
    _m(r"RETAILCO LTD WAGES", "wages_weekly", "Wages", "income", "weekly", "wages"),
    _m(r"CARELINK SERVICES PAY|HARBOUR LOGISTICS PAYROLL|NORTHGATE CONSULTING SAL", "wages", "Wages", "income", "monthly", "wages"),
    _m(r"AGENCY SHIFTS", "agency", "Agency pay", "income", "weekly", "agency pay"),
    _m(r"HARBOUR LOGISTICS OT", "overtime", "Overtime pay", "income", "oneoff"),
    _m(r"BIRTHDAY GIFT", "gift", "Gift from family", "income", "oneoff"),
    _m(r"CHILD MAINT", "maintenance", "Child maintenance", "income", "oneoff"),
    _m(r"DWP UNIVERSAL CREDIT", "uc", "Benefit payment", "income", "4weekly", "benefit"),
    _m(r"DWP PIP", "pip", "Benefit payment", "income", "4weekly", "benefit"),
    _m(r"MEALBOX", "food_delivery", "Food delivery", "eating_out", "average"),
    _m(r"GAMEZONE", "games", "Online games", "games", "average"),
    _m(r"VENDCO", "snacks", "Snacks", "eating_out", "average"),
    _m(r"TFL TRAVEL", "travel", "Bus and travel", "transport", "average"),
    _m(r"ASOSLIKE", "clothes", "Clothes", "shopping", "average"),
    _m(r"ATM WDL", "atm", "Cash from a machine", "cash", "average"),
    _m(r"GAMEPASS\*RECUR", "gamepass", "Game pass subscription", "subscription", "monthly", "new monthly payment"),
    _m(r"STREAMCO\*SUB", "streamco", "Streaming subscription", "subscription", "monthly"),
    _m(r"MUSICBOX\*SUB", "musicbox", "Music subscription", "subscription", "monthly"),
    _m(r"FITAPP\*SUB", "fitapp", "Fitness app subscription", "subscription", "monthly"),
    _m(r"NEWSHUB\*DIGITAL", "newshub", "News subscription", "subscription", "monthly", "new monthly payment"),
    _m(r"FITLIFE GYM", "gym", "Gym membership", "subscription", "monthly"),
    _m(r"\bMOBILE\b", "mobile", "Phone", "phone_tv", "monthly"),
    _m(r"(?:OCTOPUS|EON NEXT) ENERGY", "energy_dd", "Energy", "energy", "monthly"),
    _m(r"WORLDREMIT", "remittance", "Money sent abroad", "transfer_regular", "monthly"),
    _m(r"LIDLISH SUPERMKT|TESCOISH EXPRESS", "supermarket", "Supermarket", "shopping", "average"),
    _m(r"AFRO-ASIAN FOODS", "specialist_food", "Specialist food shop", "shopping", "average"),
    _m(r"CAMDEN LETTINGS", "rent_dd", "Rent", "housing", "monthly"),
    _m(r"HALIFAXISH MTGE", "mortgage", "Mortgage", "housing", "monthly"),
    _m(r"SUPPORTED HSG CHG", "housing_charge", "Housing charge", "housing", "monthly"),
    _m(r"AXLEGRP INS", "car_insurance", "Car insurance", "insurance", "monthly"),
    _m(r"AXA/ANNUAL CAR INS", "car_insurance_year", "Car insurance (yearly)", "insurance", "annual", "car insurance"),
    _m(r"MOT TESTING", "mot", "MOT", "car", "annual", "MOT"),
    _m(r"DVLA VEHICLE TAX", "car_tax", "Car tax", "car", "annual", "car tax"),
    _m(r"UNPAID ITEM FEE", "unpaid_fee", "Bank charge for a missed payment", "fee", "oneoff"),
    _m(r"SHELLISH FUEL", "fuel", "Fuel", "transport", "average"),
    _m(r"HARBOUR CAFE|CORNER CAFE", "cafe", "Cafe", "eating_out", "average"),
    _m(r"PIZZABAR", "takeaway", "Eating out", "eating_out", "average"),
    _m(r"PAYPOINT TOPUP", "topup", "Gas and electric top-up", "energy", "average"),
    _m(r"KAUR NEWSAGENT", "newsagent", "Newsagent", "shopping", "average"),
    _m(r"PLAYSTORE\*INAPP", "inapp", "In-app purchases", "games", "average"),
    _m(r"ACTIVEPLUS CLUB", "leisure_club", "Leisure club", "leisure", "monthly"),
    _m(r"LITTLE ACORNS", "childcare", "Childcare", "childcare", "monthly"),
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
