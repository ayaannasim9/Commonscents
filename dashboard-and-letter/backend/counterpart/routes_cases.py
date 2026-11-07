from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from .cases import CaseService

router = APIRouter()

Source = Literal["slip_post_office", "slip_post", "counter_verbal", "hub_visit", "phone", "trusted_person", "system_flag"]
Tick = Literal["worried", "scam_call", "bill", "afford", "other"]  # C5: same list as the slip


def svc(request: Request) -> CaseService:
    return request.app.state.cases


class CaseIn(BaseModel):
    source: Source
    text: str = Field(min_length=1, max_length=2000)
    ticks: list[Tick] = []


class NoteIn(BaseModel):
    note: str = Field(min_length=1, max_length=2000)
    helper: str = "Priya"


class DraftIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class ApproveIn(BaseModel):
    helper: str = "Priya"


@router.get("/cases")
def list_cases(request: Request, status: str | None = None, urgency: str | None = None) -> list[dict]:
    """Urgent first, then due date. Closed cases are hidden unless status=closed or status=all."""
    return svc(request).list(status, urgency)


@router.post("/cases")
def create_case(body: CaseIn, request: Request) -> dict:
    return svc(request).create(body.source, body.text, list(body.ticks))


@router.get("/cases/{cid}")
def get_case(cid: str, request: Request, viewer: str | None = None) -> dict:
    return svc(request).view(cid, viewer)


@router.post("/cases/{cid}/note")
def note(cid: str, body: NoteIn, request: Request) -> dict:
    return svc(request).note(cid, body.note, body.helper)


@router.post("/cases/{cid}/draft-reply")
def draft_reply(cid: str, request: Request) -> dict:
    return svc(request).draft_reply(cid)


@router.post("/cases/{cid}/draft")
def edit_draft(cid: str, body: DraftIn, request: Request) -> dict:
    return svc(request).edit_draft(cid, body.text)


@router.post("/cases/{cid}/approve")
def approve(cid: str, request: Request, body: ApproveIn | None = None) -> dict:
    return svc(request).approve(cid, (body or ApproveIn()).helper)
