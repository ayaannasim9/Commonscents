"""Pydantic models. Money is integer pence internally; whole pounds only in Facts."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, computed_field

Channel = Literal["direct_debit", "credit", "cash_withdrawal", "card", "faster_payment"]


class TrustedPerson(BaseModel):
    name: str
    relation: str
    level: str


class Preferences(BaseModel):
    large_print: bool
    language: str


class Persona(BaseModel):
    id: str
    name: str
    age: int
    bank: str
    hub_day: str
    trusted_person: TrustedPerson
    preferences: Preferences


class Transaction(BaseModel):
    id: str
    date: date
    time: str | None = None
    description: str
    amount_pence: int  # signed: negative = money out
    channel: Channel

    @computed_field  # signed pounds, 2dp, as the contract's transactions endpoint shows
    @property
    def amount(self) -> float:
        return round(self.amount_pence / 100, 2)


class PlantedEvent(BaseModel):
    name: Literal["scam_transfer", "forgotten_subscription", "price_rise"]
    year: int
    month: int


# ---- Facts (C2): whole pounds, the only input to the writer ----

class FactsCustomer(BaseModel):
    name: str
    reference: str
    bank: str
    hub_day: str


class OutItem(BaseModel):
    name: str
    amount: int


class LastMonth(BaseModel):
    month: str
    year: int
    in_: int
    out: list[OutItem]
    cash: int
    left: int

    model_config = {"populate_by_name": True}


class ForecastMonth(BaseModel):
    month: str
    year: int
    status: Literal["ok", "warn", "short"]
    reason: str
    extra: int
    spare: int


class Suggestion(BaseModel):
    text_hint: str
    amount: int


class Flag(BaseModel):
    id: str
    kind: Literal["unusual_payment", "new_regular_payment", "price_rise"]
    severity: Literal["info", "medium", "high"]
    date: date
    amount: int
    plain_name: str
    reasons: list[str]


class SinceLastVisit(BaseModel):
    helper: str
    note: str
    date: date


class Facts(BaseModel):
    as_of: date
    customer: FactsCustomer
    headline_status: Literal["good", "heads_up", "attention"]
    last_month: LastMonth
    forecast: list[ForecastMonth]
    suggestion: Suggestion | None
    flags: list[Flag]
    since_last_visit: SinceLastVisit | None
    cash_blind_spot: bool

    def to_contract(self) -> dict:
        """JSON in the contract's shape (`in`, not `in_`)."""
        d = self.model_dump(mode="json")
        d["last_month"]["in"] = d["last_month"].pop("in_")
        return d
