"""The six personas (personas.md) as DATA. The pipeline, letter template, thresholds and guardrails are
identical for all of them; only the items below differ. No persona-specific code lives anywhere else."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .models import Persona, Preferences

DEFAULT_ID = "MRG-4471"
DEMO_END = (2026, 11)  # last full month shared by every persona


def p(pounds: float) -> int:
    return round(pounds * 100)


@dataclass(frozen=True)
class Item:
    """One line of someone's financial life. Amounts are signed pence (negative = money out)."""
    desc: str
    channel: str
    kind: str = "monthly"          # monthly | weekly | 4weekly | spread | sporadic | annual | once
    amount: int = 0
    rng: tuple[int, int] | None = None   # random amount per payment, whole pounds, in pence (sign as amount)
    day: int = 1                   # day of month; -1 = last working day
    weekday: int = 4               # weekly: 0 = Monday ... 4 = Friday
    month: int | None = None       # annual: which month
    skip: frozenset = frozenset()  # months with no payment
    months: frozenset | None = None  # only these months
    seasonal: dict = field(default_factory=dict)   # month -> pence
    changes: tuple = ()            # ((year, month, pence), ...) new amount from then on
    low: dict = field(default_factory=dict)        # {(year, month): (lo, hi)} different range that month
    total: int = 0                 # spread: month total (signed pence), split over `trips`
    trips: int = 1
    count: tuple[int, int] = (1, 1)  # sporadic: how many times a month
    hours: tuple[int, int] = (9, 16)
    bias: str | None = None        # spread: "weekend" | "early_week"
    anchor: date | None = None     # 4weekly
    start: tuple[int, int] | None = None   # first month it exists; for kind "once" the only month
    price_event: bool = False      # the bill that the price_rise event bumps


@dataclass(frozen=True)
class SeededCase:
    source: str
    text: str
    ticks: tuple[str, ...]


@dataclass(frozen=True)
class PersonaSpec:
    id: str
    name: str
    age: int
    archetype: str
    tagline: str
    hub_day: str
    helper_role: str               # banker | post_office | phone
    preferences: Preferences
    items: tuple[Item, ...]
    scam: tuple[str, int, str]     # (payee text after "FASTER PMT TO ", pence, time)
    subscription: tuple[str, int, int]   # (description, pence, day) for forgotten_subscription
    case: SeededCase
    bank: str = "NatWest"          # plan 0.8

    def profile(self) -> Persona:
        return Persona(id=self.id, name=self.name, age=self.age, archetype=self.archetype, tagline=self.tagline,
                       bank=self.bank, hub_day=self.hub_day, preferences=self.preferences)


def out(desc, pounds, channel="direct_debit", **kw) -> Item:
    return Item(desc, channel, amount=-p(pounds), **kw)


def inc(desc, pounds, kind="monthly", **kw) -> Item:
    return Item(desc, "credit", kind=kind, amount=p(pounds), **kw)


def spread(desc, pounds, trips, **kw) -> Item:
    return Item(desc, "card", kind="spread", total=-p(pounds), trips=trips, **kw)


def prefs(large, read_aloud) -> Preferences:
    return Preferences(large_print=large, read_aloud_default=read_aloud, language="en")


WINTER = (11, 12, 1, 2, 3)
NO_CTAX = frozenset({2, 3})  # council tax is paid 10 months a year

MARGARET = PersonaSpec(
    id="MRG-4471", name="Margaret", age=81, archetype="elderly", tagline="Gets a letter, not an app.",
    hub_day="Tuesday", helper_role="banker", preferences=prefs(True, False),
    items=(
        inc("DWP STATE PENSION 4WK", 760, "4weekly", anchor=date(2026, 11, 3)),
        inc("NEST PENSN 7783", 520, day=25),
        out("DD HARROWGATE HOUSING 0071", 480, day=1),
        out("DD LBROUGH CNCL TAX 5532", 118, day=3, skip=NO_CTAX),
        out("DD VF BBAND/TV 8830", 28, day=8, changes=((2026, 4, -p(30)),)),  # April price rise
        out("DD EDF ENERGY 7710", 32, day=12),
        out("DD BGAS 4421 ENERGY", 43, day=15, seasonal={m: -p(86) for m in WINTER}),
        out("DD SEVERN TRENT 0912", 28, day=20, price_event=True),
        out("DD TV LICENCE MBP", 175, kind="annual", month=1, day=5),
        Item("POST OFFICE CNTR WDL", "cash_withdrawal", kind="weekly", amount=-p(40), hours=(10, 11)),
        spread("CRD 4471 PATELS NEWS&FOOD", 92, 8),
        spread("CRD 4471 BOOTS PHARM 0231", 24, 2, hours=(10, 15)),
    ),
    scam=("M HOLLOWAY 04-00-75 ****3391", 200000, "21:14"),
    subscription=("CRD 4471 STREAMFLIX*MEMBER", p(9.99), 9),
    case=SeededCase("slip_post_office", "Can I afford a new boiler?", ("afford",)),
)

JAYDEN = PersonaSpec(
    id="JDN-2208", name="Jayden", age=18, archetype="first_account", tagline="First job, first account.",
    hub_day="Thursday", helper_role="banker", preferences=prefs(False, False),
    items=(
        # weekly wage that follows the hours; last December was quiet (the forecast reads last year's hours)
        Item("RETAILCO LTD WAGES", "credit", kind="weekly", amount=p(165), rng=(p(130), p(210)),
             low={(2025, 12): (p(55), p(75))}),
        Item("BIRTHDAY GIFT FROM FAMILY", "credit", kind="once", amount=p(50), start=(2026, 3), day=14),
        out("DD O2 MOBILE 4417", 22, day=6, price_event=True),
        out("DD FITLIFE GYM 3318", 14.99, day=10),
        Item("ATM WDL 0142 HIGH ST", "cash_withdrawal", kind="sporadic", rng=(-p(30), -p(20)), count=(2, 3), hours=(14, 23)),
        spread("CRD 2208 MEALBOX*ORDER", 230, 14, bias="weekend", hours=(12, 23)),
        spread("CRD 2208 TFL TRAVEL CH", 56, 4),
        spread("CRD 2208 VENDCO 0098", 60, 16, hours=(8, 15)),
        spread("CRD 2208 GAMEZONE*STORE", 80, 6, bias="weekend", hours=(16, 23)),
        spread("CRD 2208 ASOSLIKE*FASH", 90, 3, hours=(19, 23)),
    ),
    scam=("D HARRISON 60-83-71 ****5527", 40000, "22:36"),
    subscription=("CRD GAMEPASS*RECUR", p(9.99), 12),
    case=SeededCase("counter_verbal", "Why is my money gone before pay day?", ("other",)),
)

AMIRA = PersonaSpec(
    id="AMR-3135", name="Amira", age=29, archetype="recent_migrant", tagline="New to UK bills.",
    hub_day="Monday", helper_role="banker", preferences=prefs(False, True),
    items=(
        inc("CARELINK SERVICES PAY", 1060, day=28),
        Item("AGENCY SHIFTS 3135 PAY", "credit", kind="weekly", amount=p(80), rng=(p(35), p(110)),
             low={(2025, 12): (p(20), p(40))}),
        Item("FASTER PMT TO K ADEYEMI 20-11-65 ****0457", "faster_payment", amount=-p(420), day=1),  # rent, standing order
        out("DD LYCA MOBILE 1190", 15, day=7),
        out("DD OCTOPUS ENERGY 3302", 45, day=14, price_event=True),
        out("DD CITY CNCL TAX 7081", 92, day=3, skip=NO_CTAX, start=(2026, 9)),  # first bill this autumn
        out("DD TV LICENCE MBP", 174.5, kind="annual", month=11, day=9, start=(2026, 11)),  # arrived unexpectedly
        Item("WORLDREMIT TRANSFER", "international_transfer", amount=-p(200), rng=(-p(220), -p(180)), day=5),
        spread("CRD 3135 LIDLISH SUPERMKT", 190, 7),
        spread("CRD 3135 AFRO-ASIAN FOODS", 65, 3),
        spread("CRD 3135 TFL TRAVEL CH", 62, 4),
    ),
    scam=("T OKONKWO 77-22-14 ****8810", 90000, "22:48"),
    subscription=("CRD GAMEPASS*RECUR", p(9.99), 11),
    case=SeededCase("slip_post", "What is this payment called TV LICENCE MBP? I did not ask for it.", ("bill",)),
)

DANIEL = PersonaSpec(
    id="DAN-5502", name="Daniel", age=46, archetype="low_literacy", tagline="Cash and direct debits.",
    hub_day="Wednesday", helper_role="post_office", preferences=prefs(True, True),
    items=(
        inc("HARBOUR LOGISTICS PAYROLL", 1880, day=28),
        Item("HARBOUR LOGISTICS OT 5502", "credit", kind="monthly", amount=p(190), rng=(p(140), p(260)),
             months=frozenset({2, 5, 8, 11}), day=28),
        out("DD CAMDEN LETTINGS 6633", 560, day=1),
        out("DD LBROUGH CNCL TAX 5532", 132, day=3, skip=NO_CTAX),
        out("DD EON NEXT ENERGY 5520", 78, day=14, price_event=True),
        out("DD SEVERN TRENT 0912", 31, day=20),
        out("DD O2 MOBILE 4417", 20, day=6),
        out("DD AXLEGRP INS 99021", 48, day=11),
        out("GOVT-GW LICNCE 77", 174.5, kind="annual", month=1, day=7),
        Item("UNPAID ITEM FEE", "direct_debit", kind="once", amount=-p(8), start=(2026, 8), day=19),
        Item("POST OFFICE CNTR WDL", "cash_withdrawal", kind="weekly", amount=-p(85), rng=(-p(100), -p(70)), hours=(12, 13)),
        spread("CRD 5502 SHELLISH FUEL", 120, 4),
        spread("CRD 5502 HARBOUR CAFE", 60, 8, hours=(11, 14)),
        spread("PAYPOINT TOPUP 6620", 20, 1, hours=(17, 19)),
    ),
    scam=("L PETERS 30-91-22 ****2204", 150000, "21:52"),
    subscription=("CRD GAMEPASS*RECUR", p(9.99), 10),
    case=SeededCase("slip_post_office", "What is the INS payment? Is it a scam?", ("bill", "worried")),
)

SAM = PersonaSpec(
    id="SAM-7316", name="Sam", age=27, archetype="learning_difficulty", tagline="Calm, steady, predictable.",
    hub_day="Friday", helper_role="banker", preferences=prefs(True, True),
    items=(
        inc("DWP UNIVERSAL CREDIT", 420, "4weekly", anchor=date(2026, 11, 6)),
        inc("DWP PIP", 290, "4weekly", anchor=date(2026, 11, 13)),
        out("DD SUPPORTED HSG CHG", 210, day=2),
        out("DD LYCA MOBILE 1190", 12, day=7, price_event=True),
        out("DD ACTIVEPLUS CLUB 5530", 18, day=15),
        Item("POST OFFICE CNTR WDL", "cash_withdrawal", kind="weekly", amount=-p(25), weekday=0, hours=(10, 11)),
        spread("CRD 7316 CORNER CAFE", 70, 12, bias="early_week", hours=(9, 13)),
        spread("CRD 7316 KAUR NEWSAGENT", 45, 9, bias="early_week", hours=(8, 12)),
        spread("CRD 7316 PLAYSTORE*INAPP", 22, 6, hours=(15, 20)),
    ),
    scam=("R ELLIS 09-01-28 ****6641", 20000, "21:30"),
    subscription=("CRD GAMEPASS*RECUR", p(4.99), 8),
    case=SeededCase("counter_verbal", "Where did my game money go?", ("other",)),
)

RAVI = PersonaSpec(
    id="RAV-6049", name="Ravi", age=34, archetype="never_budgeted", tagline="Every bill, for the first time.",
    hub_day="Tuesday", helper_role="phone", preferences=prefs(False, False),
    items=(
        inc("NORTHGATE CONSULTING SAL", 2450, day=-1),
        Item("CHILD MAINT PYMT 6049", "credit", kind="monthly", amount=p(250), months=frozenset({2, 6, 9, 11}), day=12),
        out("DD HALIFAXISH MTGE 2264", 890, day=1),
        out("DD LBROUGH CNCL TAX 5532", 165, day=3, skip=NO_CTAX),
        out("DD BGAS 6049 ENERGY", 65, day=15, seasonal={m: -p(125) for m in WINTER}),
        out("DD SEVERN TRENT 0912", 33, day=20),
        out("DD VF BBAND/TV 8830", 38, day=8, price_event=True),
        out("DD LITTLE ACORNS NURS 4410", 220, day=2),
        out("CRD STREAMCO*SUB", 8.99, "card", day=5),
        out("CRD MUSICBOX*SUB", 11.99, "card", day=6),
        out("CRD FITAPP*SUB", 5.99, "card", day=7),
        out("DD TV LICENCE MBP", 174.5, kind="annual", month=1, day=7),
        out("AXA/ANNUAL CAR INS", 620, "direct_debit", kind="annual", month=3, day=10),
        out("MOT TESTING SVC 0231", 55, "card", kind="annual", month=3, day=16),
        out("DD DVLA VEHICLE TAX", 195, kind="annual", month=3, day=18),
        spread("CRD 6049 TESCOISH EXPRESS", 420, 10),
        spread("CRD 6049 SHELLISH FUEL", 90, 3),
        spread("CRD 6049 PIZZABAR", 70, 3, bias="weekend", hours=(18, 22)),
    ),
    scam=("A WRIGHT 40-12-09 ****1175", 180000, "21:20"),
    subscription=("CRD NEWSHUB*DIGITAL", p(7.99), 9),
    case=SeededCase("hub_visit", "I have never done a budget. Is my income enough?", ("afford",)),
)

SPECS: dict[str, PersonaSpec] = {s.id: s for s in (MARGARET, JAYDEN, AMIRA, DANIEL, SAM, RAVI)}
