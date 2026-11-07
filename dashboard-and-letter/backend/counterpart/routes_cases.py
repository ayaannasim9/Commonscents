from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from .cases import CaseService, _viewer
from .personas import DEFAULT_ID, SPECS
from fastapi import HTTPException

router = APIRouter()

Source = Literal["slip_post_office", "slip_post", "counter_verbal", "hub_visit", "phone", "system_flag"]
Tick = Literal["worried", "scam_call", "bill", "afford", "other"]  # C5: same list as the slip


def svc(request: Request) -> CaseService:
    return request.app.state.cases


def viewer_log(w, cid: str, viewer: str, what: str) -> None:
    who, role = _viewer(viewer)
    w.log_access(cid, who, role, what)


class CaseIn(BaseModel):
    customer: str = DEFAULT_ID
    source: Source
    text: str = Field(min_length=1, max_length=2000)
    ticks: list[Tick] = []


class NoteIn(BaseModel):
    note: str = Field(min_length=1, max_length=2000)
    helper: str = "Daria"


class DraftIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class ApproveIn(BaseModel):
    helper: str = "Daria"


@router.get("/cases")
def list_cases(request: Request, status: str | None = None, urgency: str | None = None,
               customer: str = DEFAULT_ID) -> list[dict]:
    """One customer's queue (default Margaret; customer=all for everyone). Urgent first, then due date.
    Closed cases are hidden unless status=closed or status=all."""
    if customer != "all" and customer not in SPECS:
        raise HTTPException(404, "Unknown customer")
    return svc(request).list(status, urgency, None if customer == "all" else customer)


@router.post("/cases")
def create_case(body: CaseIn, request: Request) -> dict:
    if body.customer not in SPECS:
        raise HTTPException(404, "Unknown customer")
    return svc(request).create(body.customer, body.source, body.text, list(body.ticks))


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
