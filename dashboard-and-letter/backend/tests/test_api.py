"""B5 API + B9-style contract tests: live responses must match the fixtures' keys and types."""
import json
import re
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from counterpart import state
from counterpart.app import create_app
from counterpart.guardrails import allowed_numbers, extract_amounts
from counterpart.llm.client import LLMClient
from counterpart.models import SinceLastVisit

FIX = Path(__file__).resolve().parents[2] / "contract" / "fixtures"
C = "/customers/MRG-4471"


def fx(name):
    return json.loads((FIX / name).read_text())


@pytest.fixture
def client():
    return TestClient(create_app(":memory:", LLMClient(mode="stub")))


def kind(v):
    return "null" if v is None else "bool" if isinstance(v, bool) else "number" if isinstance(v, (int, float)) else type(v).__name__


def check_shape(live, fixture, path="$"):
    """Same keys, same types. None on either side is accepted (nullable fields); lists compare the
    union of their elements' keys, so optional keys such as section.status are fine."""
    if live is None or fixture is None:
        return
    assert kind(live) == kind(fixture), f"{path}: {kind(live)} != {kind(fixture)}"
    if isinstance(fixture, dict):
        assert set(live) == set(fixture), f"{path}: keys {sorted(set(live) ^ set(fixture))}"
        for k in fixture:
            check_shape(live[k], fixture[k], f"{path}.{k}")
    elif isinstance(fixture, list) and fixture and live:
        if isinstance(fixture[0], dict):
            lk, fk = {k for x in live for k in x}, {k for x in fixture for k in x}
            assert lk == fk, f"{path}[]: keys {sorted(lk ^ fk)}"
            merged = {}
            for x in fixture:
                for k, v in x.items():
                    if v is not None:
                        merged.setdefault(k, v)
            for i, x in enumerate(live):
                for k, v in x.items():
                    check_shape(v, merged.get(k), f"{path}[{i}].{k}")
        else:
            assert {kind(x) for x in live} == {kind(x) for x in fixture}, path


def test_customer_matches_fixture(client):
    assert client.get(C).json() == fx("customer.json")


def test_unknown_customer_404(client):
    assert client.get("/customers/NOPE/facts").status_code == 404


def test_transactions_contract_and_net(client):
    r = client.get(f"{C}/transactions").json()
    check_shape(r, fx("transactions.nov.json"))
    assert r["month"] == "2026-11" and round(sum(t["amount"] for t in r["transactions"]), 2) == 230.0
    assert client.get(f"{C}/transactions?month=2026-10").json()["month"] == "2026-10"


def test_facts_contract(client):
    r = client.get(f"{C}/facts").json()
    check_shape(r, fx("facts.clean.json"))
    assert r == fx("facts.clean.json")  # the fixture IS the backend's clean output now


def test_dashboard_contract_clean(client):
    r = client.get(f"{C}/dashboard").json()
    check_shape(r, fx("dashboard.clean.json"))
    assert [s["id"] for s in r["sections"]] == [s["id"] for s in fx("dashboard.clean.json")["sections"]]
    assert r["facts"] == fx("dashboard.clean.json")["facts"]
    assert r["guardrail"] == {"caught": False, "events": []}


def test_scam_event_flow_and_contract(client):
    r = client.post(f"{C}/events", json={"event": "scam_transfer"}).json()
    check_shape(r, {"facts_version": 2, "new_flags": [fx("dashboard.scam.json")["facts"]["flags"][0]], "new_case_id": None})
    assert r["facts_version"] == 2 and len(r["new_flags"]) == 1
    d = client.get(f"{C}/dashboard").json()
    check_shape(d, fx("dashboard.scam.json"))
    assert d["facts"] == fx("dashboard.scam.json")["facts"]
    assert [s["id"] for s in d["sections"]] == ["headline", "last_month", "forecast", "scam_watch", "since_visit", "ask"]
    assert {s["id"]: s.get("status") for s in d["sections"]}["scam_watch"] == "flagged"
    assert d["facts_version"] == 2


def test_event_is_idempotent_and_validated(client):
    client.post(f"{C}/events", json={"event": "price_rise"})
    again = client.post(f"{C}/events", json={"event": "price_rise"}).json()
    assert again["facts_version"] == 2 and again["new_flags"] == []
    assert client.post(f"{C}/events", json={"event": "nope"}).status_code == 422


def test_demo_bad_number_shows_badge_then_clears_on_regenerate(client):
    d = client.get(f"{C}/dashboard?demo=bad-number").json()
    check_shape(d, fx("dashboard.guardrail-caught.json"))
    assert d["guardrail"]["caught"] and d["guardrail"]["events"][0]["detail"].startswith("£2,400")
    assert "2,400" not in json.dumps(d["sections"])
    assert client.get(f"{C}/dashboard").json()["guardrail"]["caught"]  # badge persists until regenerate
    assert not client.post(f"{C}/letter").json()["guardrail"]["caught"]
    assert not client.get(f"{C}/dashboard").json()["guardrail"]["caught"]


def test_next_month_matches_after_note_fixture(client):
    assert client.post("/demo/next-month").json() == {"as_of": "2027-01-01"}
    state.set_since_last_visit(client.app.state.db, SinceLastVisit(helper="Priya", note="Set up heating pot, £20 a month", date=date(2026, 12, 1)))
    d = client.get(f"{C}/dashboard").json()
    check_shape(d, fx("dashboard.after-note.json"))
    f, ref = d["facts"], fx("dashboard.after-note.json")["facts"]
    assert (f["last_month"], f["forecast"], f["since_last_visit"]["note"]) == (ref["last_month"], ref["forecast"], ref["since_last_visit"]["note"])
    assert "Priya agreed: Set up heating pot" in next(s for s in d["sections"] if s["id"] == "since_visit")["text"]


def test_demo_state_and_reset(client):
    client.post(f"{C}/events", json={"event": "scam_transfer"})
    client.post("/demo/next-month")
    s = client.get("/demo/state").json()
    assert s == {"as_of": "2027-01-01", "events_applied": ["scam_transfer"], "facts_version": 3}
    assert client.post("/demo/reset").json() == {"as_of": "2026-12-01"}
    s = client.get("/demo/state").json()
    assert s["events_applied"] == [] and s["as_of"] == "2026-12-01" and s["facts_version"] == 4  # only goes up
    assert client.get(f"{C}/facts").json() == fx("facts.clean.json")


# ---- letter ----

def test_letter_contract_and_approve(client):
    r = client.post(f"{C}/letter").json()
    assert r["status"] == "draft" and r["letter_id"].startswith("letter_")
    assert set(r) == {"letter_id", "status", "html", "sections", "guardrail"}
    assert client.post(f"{C}/letter/approve").json() == {"letter_id": r["letter_id"], "status": "approved"}


def test_letter_html_follows_the_facts(client):
    before = client.get(f"{C}/letter.html").text
    client.post(f"{C}/events", json={"event": "scam_transfer"})
    after = client.get(f"{C}/letter.html").text
    assert "Nothing unusual this month" in before and "Nothing unusual this month" not in after
    assert "£2,000 on 18 November" in after


def test_p6_letter_has_no_links_or_phone_numbers(client):
    for ev in (None, "scam_transfer"):
        if ev:
            client.post(f"{C}/events", json={"event": ev})
        html = client.get(f"{C}/letter.html").text
        assert "http" not in html and "<a " not in html.lower() and "href" not in html and "<img" not in html
        assert not re.search(r"\d[\d\s-]{9,}\d", re.sub(r"<style>.*?</style>", "", html, flags=re.S))


def test_p9_dashboard_and_letter_say_the_same(client):
    for ev in (None, "scam_transfer"):
        if ev:
            client.post(f"{C}/events", json={"event": ev})
        d = client.get(f"{C}/dashboard").json()
        html = client.get(f"{C}/letter.html").text
        for s in d["sections"]:
            assert s["text"].replace("&", "&amp;") in html or s["text"] in html
        figs = {w for t in (s["text"] for s in d["sections"]) for w, _ in extract_amounts(t)}
        assert figs and all(f in html for f in figs)


def test_p9_letter_regenerate_changes_both(client):
    a = client.get(f"{C}/dashboard").json()["sections"]
    client.post(f"{C}/letter")
    assert client.get(f"{C}/dashboard").json()["sections"] == a  # stub is deterministic, still same strings


def test_every_figure_in_dashboard_is_in_the_facts(client):
    client.post(f"{C}/events", json={"event": "forgotten_subscription"})
    d = client.get(f"{C}/dashboard").json()
    allowed = allowed_numbers(d["facts"])
    for s in d["sections"]:
        for _, v in extract_amounts(s["text"]):
            assert round(v) in allowed
