"""End-to-end tests for the ML engine. Run:  cd ml && python3 -m pytest -q"""
import json
import os
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ML = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML))

import api  # noqa: E402  (loads ml/.env)
os.environ.pop("ANTHROPIC_API_KEY", None)  # tests never call Claude; alerts use the rule-based fallback
from fastapi.testclient import TestClient  # noqa: E402

import mlmodels as M  # noqa: E402
import population as pop  # noqa: E402
from model import analyse  # noqa: E402
from openbanking import categorise, from_open_banking, to_open_banking  # noqa: E402

TODAY = date(2026, 11, 7)
CUSTOMERS = {c["id"]: c for c in json.loads((ML / "data/customers.json").read_text())}
client = TestClient(api.app)


def _tx(cid):
    return pd.read_csv(ML / f"data/{cid}_transactions.csv")


def check_result(r):
    json.dumps(r, allow_nan=False)  # valid JSON for front ends: no NaN/inf anywhere
    s = r["cashflow_forecast"]["series"]
    assert len(s["dates"]) == len(s["p50"]) == 365
    assert all(a <= b + 1e-6 <= c + 2e-6 for a, b, c in zip(s["p10"], s["p50"], s["p90"]))
    for h in r["cashflow_forecast"]["horizons"]:
        assert h["range_low"] <= h["predicted_balance"] <= h["range_high"]
        assert 0 <= h["confidence"] <= 1
    hr = r["hardship_risk"]
    assert 0 <= hr["score"] <= 1 and hr["level"] in ("low", "medium", "high")
    assert all(x["confidence"] >= 0.6 for x in r["upcoming_expenses"] + r["opportunities"])
    for k in ("action_plan", "safe_to_spend", "backtest", "behaviour_signals", "life_stage", "support", "bill_calendar"):
        assert k in r["advanced"]


@pytest.mark.parametrize("cid", list(CUSTOMERS))
def test_demo_customers(cid):
    r = analyse(CUSTOMERS[cid], _tx(cid), TODAY, api.DEMO_ANSWERS[cid])
    check_result(r)
    assert r["hardship_risk"]["model"].startswith("gradient boosting")


def test_risk_ordering_makes_sense():
    s = {cid: analyse(CUSTOMERS[cid], _tx(cid), TODAY)["hardship_risk"]["score"] for cid in CUSTOMERS}
    assert s["jordan"] > s["priya"] >= s["margaret"]


@pytest.mark.parametrize("seed", range(5000, 5012))
def test_random_synthetic_customers(seed):
    tx, cust, _, _ = pop.generate(seed)
    check_result(analyse(cust, tx, pop.TODAY))


@pytest.mark.parametrize("answers", [
    {"goal": g, "worry": w, "life_changes": [lc], "shock_500": sh, "support_needs": sn}
    for g, w, lc, sh, sn in zip(
        ["Build savings", "Buy a home", "Pay off debt", "Manage monthly expenses", "Retirement", "Build savings"],
        ["Unexpected bills", "Running out of money before payday", "Debt", "Not saving enough", "Job security", "Debt"],
        ["Moving home", "New job", "Graduation", "Retirement", "New child", "None"],
        ["Savings", "Credit card", "Overdraft", "Borrowing from family/friends", "I couldn't cover it", "Savings"],
        [["Money makes me anxious"], ["I prefer simple explanations"], ["I struggle with impulse spending"],
         ["I want help with gambling"], ["I find it hard to keep track of bills"], []])])
def test_every_answer_option(answers):
    for cid in CUSTOMERS:
        check_result(analyse(CUSTOMERS[cid], _tx(cid), TODAY, answers))


def test_trained_model_beats_baselines():
    m = json.loads((ML / "models/metrics.json").read_text())["hardship_model"]["test"]
    gb = m["gradient_boosting_calibrated"]
    assert gb["roc_auc"] >= 0.9
    assert gb["roc_auc"] > m["hand_weighted_rules"]["roc_auc"]
    assert gb["roc_auc"] > m["monte_carlo_only"]["roc_auc"]
    assert gb["brier"] < m["base_rate_guess"]["brier"]


def test_categoriser():
    assert categorise("CARD PAYMENT TO GREGGS", False)[0] == "eating_out"
    assert categorise("WAITROSE 1234", False)[0] == "groceries"
    assert categorise("E.ON NEXT", False)[0] == "utilities"
    assert categorise("Bet365", False)[0] == "gambling"


def test_open_banking_round_trip():
    c = CUSTOMERS["jordan"]
    tx, bal, sav = to_open_banking(_tx("jordan"), c)
    back, cust = from_open_banking(tx, bal, sav, c["profile"], "jordan", "Jordan")
    assert cust["account"]["current_balance"] == c["account"]["current_balance"]
    assert cust["account"]["overdraft_limit"] == c["account"]["overdraft_limit"]
    assert len(back) == len(_tx("jordan"))


def test_api_endpoints():
    assert client.get("/health").json() == {"ok": True}
    assert len(client.get("/customers").json()) == 3
    assert client.get("/customers/nobody/insights").status_code == 404
    r = client.get("/customers/priya/insights", params={"goal": "Buy a home", "worry": "Debt", "life_changes": "New job"})
    assert r.status_code == 200 and r.json()["insights"]["alerts"]
    t = client.get("/customers/jordan/timelines").json()
    assert set(t["timelines"]) == {"A", "B", "C"} and all(len(x["pts"]) == 6 for x in t["timelines"].values())
    html = client.get("/customers/margaret/report").text
    assert "Your plan" in html and "Risk model" in html
    assert client.get("/app/").status_code == 200
    ob = {k: json.loads((ML / f"data/openbanking/margaret_{k}.json").read_text()) for k in ("transactions", "balances", "savings")}
    r = client.post("/analyse/openbanking", json={"transactions": ob["transactions"], "balances": ob["balances"],
                                                  "savings_balances": ob["savings"], "today": "2026-11-07"})
    assert r.status_code == 200
    check_result(r.json())
