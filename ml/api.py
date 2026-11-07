"""Common Cents ML API.

Run:   uvicorn api:app --reload --port 8000
Docs:  http://localhost:8000/docs

GET  /customers                    list demo customers
GET  /customers/{id}/insights      full ML output for a demo customer
POST /analyse                      run the models on your own data:
     {"customer": {...same shape as data/customers.json...}, "transactions": [{date, amount, merchant, category, kind}, ...]}
"""
import json
from datetime import date
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import timelines as TL
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from model import analyse
from openbanking import from_open_banking
from report import render
import insights as ai

# Load ANTHROPIC_API_KEY from ml/.env if present (file is git-ignored; never commit keys)
_env = Path(__file__).parent / ".env"
if _env.exists():
    import os
    for line in _env.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

DATA = Path(__file__).parent / "data"
DEMO_TODAY = date(2026, 11, 7)  # demo data ends on this date

app = FastAPI(title="Common Cents ML")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _customers():
    return {c["id"]: c for c in json.loads((DATA / "customers.json").read_text())}


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/customers")
def customers():
    return [{k: c[k] for k in ("id", "name", "persona", "account")} for c in _customers().values()]


# Example answers for each demo customer (used when none are sent)
DEMO_ANSWERS = {
    "priya": {"goal": "Build savings", "worry": "Running out of money before payday", "life_changes": ["Graduation"], "shock_500": "Overdraft",
              "support_needs": ["I struggle with impulse spending"]},
    "jordan": {"goal": "Manage monthly expenses", "worry": "Job security", "life_changes": ["New child"], "shock_500": "I couldn't cover it",
               "support_needs": ["Money makes me anxious", "I find it hard to keep track of bills"]},
    "margaret": {"goal": "Retirement", "worry": "Unexpected bills", "life_changes": ["None"], "shock_500": "Savings",
                 "support_needs": ["I prefer simple explanations"]},
}


class Answers(BaseModel):
    goal: str | None = None
    worry: str | None = None
    life_changes: list[str] = []
    life_change_dates: dict[str, str] = {}
    shock_500: str | None = None
    support_needs: list[str] = []   # optional, self-declared; presentation only


def _run(cid, answers):
    cs = _customers()
    if cid not in cs:
        raise HTTPException(404, f"No customer '{cid}'. Try one of: {', '.join(cs)}")
    tx = pd.read_csv(DATA / f"{cid}_transactions.csv")
    ans = answers if answers is not None else DEMO_ANSWERS.get(cid)
    r = analyse(cs[cid], tx, today=DEMO_TODAY, answers=ans)
    r["insights"] = ai.generate(r, cache_key=json.dumps([cid, ans], sort_keys=True))  # Section 5: Claude-written alerts
    return r


def _query_answers(goal, worry, life_changes, shock_500):
    if not any([goal, worry, life_changes, shock_500]):
        return None
    return {"goal": goal, "worry": worry, "shock_500": shock_500,
            "life_changes": [x.strip() for x in (life_changes or "").split(",") if x.strip()]}


@app.get("/customers/{cid}/insights")
def insights(cid: str, goal: str | None = None, worry: str | None = None,
             life_changes: str | None = Query(None, description="comma separated"), shock_500: str | None = None):
    return _run(cid, _query_answers(goal, worry, life_changes, shock_500))


@app.post("/customers/{cid}/insights")
def insights_with_answers(cid: str, answers: Answers):
    return _run(cid, answers.model_dump())


@app.get("/customers/{cid}/report", response_class=HTMLResponse)
def report(cid: str, goal: str | None = None, worry: str | None = None,
           life_changes: str | None = None, shock_500: str | None = None, support_needs: str | None = None):
    """Printable A4 report. Open in a browser, then Print / Save as PDF."""
    ans = _query_answers(goal, worry, life_changes, shock_500)
    if support_needs:
        ans = (ans or {}) | {"support_needs": [x.strip() for x in support_needs.split(",") if x.strip()]}
    return render(_run(cid, ans))


@app.post("/customers/{cid}/report", response_class=HTMLResponse)
def report_with_answers(cid: str, answers: Answers):
    return render(_run(cid, answers.model_dump()))


class AnalyseRequest(BaseModel):
    customer: dict
    transactions: list[dict]
    answers: Answers | None = None
    today: date | None = None


@app.post("/analyse")
def analyse_custom(req: AnalyseRequest):
    return analyse(req.customer, req.transactions, today=req.today or date.today(),
                   answers=req.answers.model_dump() if req.answers else None)


class OpenBankingRequest(BaseModel):
    transactions: dict   # Open Banking v3.1 GET /accounts/{id}/transactions response
    balances: dict       # GET /accounts/{id}/balances response
    savings_balances: dict | None = None
    profile: dict = {}
    name: str = "Customer"
    answers: Answers | None = None
    today: date | None = None


@app.post("/analyse/openbanking")
def analyse_openbanking(req: OpenBankingRequest):
    """Run the models straight on NatWest / UK Open Banking API responses."""
    tx, customer = from_open_banking(req.transactions, req.balances, req.savings_balances, req.profile, name=req.name)
    return analyse(customer, tx, today=req.today or date.today(), answers=req.answers.model_dump() if req.answers else None)


# ---------------------------------------------------------------- Overview app (Martins) integration
@app.get("/customers/{cid}/timelines")
def timelines(cid: str, goal: str | None = None, worry: str | None = None,
              life_changes: str | None = None, shock_500: str | None = None, support_needs: str | None = None):
    """Three 5-year timelines + recommendations in the shape Overview/app.js expects."""
    ans = _query_answers(goal, worry, life_changes, shock_500)
    if support_needs:
        ans = (ans or {}) | {"support_needs": [x.strip() for x in support_needs.split(",") if x.strip()]}
    return TL.build(_run(cid, ans))


_OVERVIEW = Path(__file__).resolve().parent.parent / "Overview"
if _OVERVIEW.exists():
    app.mount("/app", StaticFiles(directory=_OVERVIEW, html=True), name="overview")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/app/" if _OVERVIEW.exists() else "/docs")
