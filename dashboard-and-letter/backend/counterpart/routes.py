from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from . import state
from .personas import DEFAULT_ID, SPECS
from .routes_cases import viewer_log
from .service import UnknownCustomer, World

router = APIRouter()


def world(request: Request) -> World:
    return request.app.state.world


def _customer(request: Request, cid: str) -> World:
    w = world(request)
    try:
        w.spec(cid)
    except UnknownCustomer:
        raise HTTPException(404, "Unknown customer")
    return w


@router.get("/personas")
def personas() -> list[dict]:
    """The six demo personas (personas.md). Same product for all; only their data differs."""
    return [{"id": s.id, "name": s.name, "age": s.age, "archetype": s.archetype, "tagline": s.tagline}
            for s in SPECS.values()]


@router.get("/customers/{cid}")
def customer(cid: str, request: Request) -> dict:
    return _customer(request, cid).spec(cid).profile().model_dump(mode="json")


@router.get("/customers/{cid}/transactions")
def transactions(cid: str, request: Request, month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$")) -> dict:
    w = _customer(request, cid)
    y, m = state.last_full_month(w.conn, cid)
    if month:
        y, m = int(month[:4]), int(month[5:])
    rows = [{"id": t.id, "date": t.date.isoformat(), "time": t.time, "description": t.description,
             "amount": t.amount, "channel": t.channel}
            for t in w.transactions(cid) if (t.date.year, t.date.month) == (y, m)]
    return {"month": f"{y}-{m:02d}", "transactions": rows}


@router.get("/customers/{cid}/facts")
def facts(cid: str, request: Request) -> dict:
    return _customer(request, cid).facts(cid).to_contract()


@router.get("/customers/{cid}/dashboard")
def dashboard(cid: str, request: Request, demo: str | None = None, viewer: str | None = None) -> dict:
    w = _customer(request, cid)
    if viewer:  # the helper's own views are logged too (P7); the customer's are not
        viewer_log(w, cid, viewer, "Looked at your dashboard")
    return w.dashboard(cid, demo_bad_number=demo == "bad-number")


class EventIn(BaseModel):
    event: Literal["scam_transfer", "forgotten_subscription", "price_rise"]


@router.post("/customers/{cid}/events")
def inject_event(cid: str, body: EventIn, request: Request) -> dict:
    w = _customer(request, cid)
    with w.lock:
        before = {(f.kind, f.date, f.amount) for f in w.facts(cid).flags}
        if state.add_event(w.conn, cid, body.event):
            state.bump(w.conn, cid)
        new = [f.model_dump(mode="json") for f in w.facts(cid).flags if (f.kind, f.date, f.amount) not in before]
        case_id = request.app.state.cases.open_flag_cases(cid, new)  # high flag -> urgent system_flag case
        return {"facts_version": state.facts_version(w.conn, cid), "new_flags": new, "new_case_id": case_id}


@router.post("/customers/{cid}/letter")
def make_letter(cid: str, request: Request, demo: str | None = None) -> dict:
    return _customer(request, cid).new_letter(cid, force=True, demo_bad_number=demo == "bad-number")


@router.get("/customers/{cid}/letter.html", response_class=HTMLResponse)
def letter_html(cid: str, request: Request) -> str:
    return _customer(request, cid).current_letter(cid)["html"]


@router.get("/customers/{cid}/letter.pdf")
def letter_pdf(cid: str, request: Request, preview: bool = False) -> Response:
    """The latest approved letter as a PDF (same HTML as the on-screen letter). ?preview=true marks a draft."""
    w = _customer(request, cid)
    try:
        pdf = w.letter_pdf(cid, preview)
    except LookupError:
        raise HTTPException(409, "No approved letter yet: approve the letter first, or use ?preview=true")
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="letter-{cid}.pdf"'})


@router.post("/customers/{cid}/letter/approve")
def approve_letter(cid: str, request: Request) -> dict:
    return _customer(request, cid).approve_letter(cid)


@router.get("/customers/{cid}/what-we-know")
def what_we_know(cid: str, request: Request) -> dict:
    return _customer(request, cid).what_we_know(cid)


# ---- demo controls (C3). Per-customer ones take ?customer=<id> (default Margaret). ----

def _demo_customer(request: Request, customer: str) -> str:
    _customer(request, customer)
    return customer


@router.get("/demo/state")
def demo_state(request: Request, customer: str = DEFAULT_ID) -> dict:
    w = world(request)
    cid = _demo_customer(request, customer)
    return {"as_of": state.as_of(w.conn, cid).isoformat(), "events_applied": [e.name for e in state.events(w.conn, cid)],
            "facts_version": state.facts_version(w.conn, cid)}


@router.post("/demo/next-month")
def next_month(request: Request, customer: str = DEFAULT_ID) -> dict:
    w = world(request)
    cid = _demo_customer(request, customer)
    with w.lock:  # closes approved cases; their note becomes "since your last visit"
        return {"as_of": request.app.state.cases.advance(cid)}


@router.post("/demo/reset")
def reset(request: Request) -> dict:
    """Resets all six customers; returns Margaret's as_of (they all start on the same date)."""
    w = world(request)
    with w.lock:
        w.clear_cache()
        state.reset_all(w.conn, list(SPECS))
        request.app.state.cases.seed_all()
        return {"as_of": state.as_of(w.conn, DEFAULT_ID).isoformat()}
