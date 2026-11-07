from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from . import state
from .service import World

router = APIRouter()


def world(request: Request) -> World:
    return request.app.state.world


def _customer(request: Request, cid: str) -> World:
    w = world(request)
    if cid != w.persona.id:
        raise HTTPException(404, "Unknown customer")
    return w


@router.get("/customers/{cid}")
def customer(cid: str, request: Request) -> dict:
    p = _customer(request, cid).persona
    return p.model_dump(mode="json")


@router.get("/customers/{cid}/transactions")
def transactions(cid: str, request: Request, month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$")) -> dict:
    w = _customer(request, cid)
    y, m = state.last_full_month(w.conn)
    if month:
        y, m = int(month[:4]), int(month[5:])
    rows = [{"id": t.id, "date": t.date.isoformat(), "time": t.time, "description": t.description,
             "amount": t.amount, "channel": t.channel}
            for t in w.transactions() if (t.date.year, t.date.month) == (y, m)]
    return {"month": f"{y}-{m:02d}", "transactions": rows}


@router.get("/customers/{cid}/facts")
def facts(cid: str, request: Request) -> dict:
    return _customer(request, cid).facts().to_contract()


@router.get("/customers/{cid}/dashboard")
def dashboard(cid: str, request: Request, demo: str | None = None) -> dict:
    return _customer(request, cid).dashboard(demo_bad_number=demo == "bad-number")


class EventIn(BaseModel):
    event: Literal["scam_transfer", "forgotten_subscription", "price_rise"]


@router.post("/customers/{cid}/events")
def inject_event(cid: str, body: EventIn, request: Request) -> dict:
    w = _customer(request, cid)
    with w.lock:
        before = {(f.kind, f.date, f.amount) for f in w.facts().flags}
        if state.add_event(w.conn, body.event):
            state.bump(w.conn)
        new = [f.model_dump(mode="json") for f in w.facts().flags if (f.kind, f.date, f.amount) not in before]
        # new_case_id: B6 opens a system_flag case for high flags
        return {"facts_version": state.facts_version(w.conn), "new_flags": new, "new_case_id": None}


@router.post("/customers/{cid}/letter")
def make_letter(cid: str, request: Request, demo: str | None = None) -> dict:
    return _customer(request, cid).new_letter(force=True, demo_bad_number=demo == "bad-number")


@router.get("/customers/{cid}/letter.html", response_class=HTMLResponse)
def letter_html(cid: str, request: Request) -> str:
    return _customer(request, cid).current_letter()["html"]


@router.post("/customers/{cid}/letter/approve")
def approve_letter(cid: str, request: Request) -> dict:
    return _customer(request, cid).approve_letter()


# ---- demo controls (C3) ----

@router.get("/demo/state")
def demo_state(request: Request) -> dict:
    w = world(request)
    return {"as_of": state.as_of(w.conn).isoformat(), "events_applied": [e.name for e in state.events(w.conn)],
            "facts_version": state.facts_version(w.conn)}


@router.post("/demo/next-month")
def next_month(request: Request) -> dict:
    w = world(request)
    with w.lock:  # B8 will also close approved cases and push their notes into since_last_visit
        return {"as_of": state.next_month(w.conn).isoformat()}


@router.post("/demo/reset")
def reset(request: Request) -> dict:
    w = world(request)
    with w.lock:
        w._sections.clear()
        return {"as_of": state.reset(w.conn).isoformat()}
