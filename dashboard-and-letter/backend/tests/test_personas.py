"""personas.md acceptance checks: six people, one product. Only the data differs."""
import re
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from counterpart.app import create_app
from counterpart.generator import generate
from counterpart.guardrails import allowed_numbers, check_text
from counterpart.llm.client import LLMClient
from counterpart.llm.writers import write_sections
from counterpart.personas import SPECS
from counterpart.pipeline import build_facts
from counterpart.pipeline.anomalies import anomalies

IDS = list(SPECS)
STUB = LLMClient(mode="stub")
EVENTS = ["scam_transfer", "forgotten_subscription", "price_rise"]


@pytest.fixture
def client():
    return TestClient(create_app(":memory:", STUB))


def facts_for(cid, events=(), end=(2026, 11), as_of=date(2026, 12, 1)):
    spec = SPECS[cid]
    return build_facts(spec.profile(), generate(spec, events=list(events), end=end), as_of)


def test_personas_endpoint_lists_all_six(client):
    r = client.get("/personas").json()
    assert [p["id"] for p in r] == ["MRG-4471", "JDN-2208", "AMR-3135", "DAN-5502", "SAM-7316", "RAV-6049"]
    assert all(set(p) == {"id", "name", "age", "archetype", "tagline"} for p in r)
    assert [p["archetype"] for p in r] == ["elderly", "first_account", "recent_migrant", "low_literacy", "learning_difficulty", "never_budgeted"]


@pytest.mark.parametrize("cid", IDS)
def test_customer_profile_has_no_trusted_person(client, cid):
    c = client.get(f"/customers/{cid}").json()
    assert set(c) == {"id", "name", "age", "archetype", "tagline", "bank", "hub_day", "preferences"}
    assert c["bank"] == "NatWest" and "read_aloud_default" in c["preferences"]


@pytest.mark.parametrize("cid", IDS)
@pytest.mark.parametrize("events", [[], EVENTS])
def test_every_persona_writes_a_guardrail_clean_letter(cid, events):
    f = facts_for(cid, events)
    g = write_sections(f, STUB)
    allowed = allowed_numbers(f)
    assert g.guardrail["caught"] is False
    assert all(check_text(t, allowed=allowed) == [] for t in g.texts.values())
    assert g.texts["headline"] and g.texts["last_month"] and g.texts["forecast"]


@pytest.mark.parametrize("cid", IDS)
def test_the_page_adds_up_and_matches_the_statement(cid):
    spec = SPECS[cid]
    txs = generate(spec)
    f = build_facts(spec.profile(), txs, date(2026, 12, 1))
    lm = f.last_month
    assert lm.in_ - sum(i.amount for i in lm.out) - lm.cash == lm.left
    net = sum(t.amount_pence for t in txs if (t.date.year, t.date.month) == (2026, 11))
    assert abs(lm.left - net / 100) <= 1.5  # whole-pound rounding only


@pytest.mark.parametrize("cid", IDS)
def test_unknown_descriptions_do_not_appear(cid):
    from counterpart.merchants import categorise
    assert all(categorise(t.description).key != "unknown" for t in generate(SPECS[cid]))


@pytest.mark.parametrize("cid", IDS)
def test_clean_months_never_flag_anything(cid):
    """Amira's regular transfer abroad, Ravi's subscriptions, Daniel's fee: none of it looks like a scam."""
    spec = SPECS[cid]
    txs = generate(spec)
    for y, m in [(2026, 11), (2026, 10), (2026, 9), (2026, 8), (2026, 5), (2026, 1)]:
        assert [f for f in anomalies(txs, y, m) if f.kind == "unusual_payment"] == [], (cid, y, m)
    assert facts_for(cid).flags == []


def test_amiras_monthly_transfer_is_never_flagged_in_any_month():
    txs = generate(SPECS["AMR-3135"])
    sends = [t for t in txs if t.channel == "international_transfer"]
    assert len(sends) == 18
    for y, m in sorted({(t.date.year, t.date.month) for t in txs})[3:]:
        assert anomalies(txs, y, m) == [] or all(f.kind != "price_rise" or f.plain_name != "Money sent abroad bill went up"
                                                for f in anomalies(txs, y, m))
    f = facts_for("AMR-3135")
    assert f.flags == [] and any(o.name == "Money sent abroad" for o in f.last_month.out)


@pytest.mark.parametrize("cid,amount", [("SAM-7316", 200), ("AMR-3135", 900), ("MRG-4471", 2000), ("JDN-2208", 400),
                                        ("DAN-5502", 1500), ("RAV-6049", 1800)])
def test_scam_transfer_is_judged_against_each_persons_own_usual_payment(cid, amount):
    f = facts_for(cid, ["scam_transfer"])
    [flag] = f.flags
    assert (flag.kind, flag.severity, flag.amount) == ("unusual_payment", "high", amount)
    assert f.headline_status == "attention"


def test_planted_events_work_for_everyone():
    for cid in IDS:
        assert [x.kind for x in facts_for(cid, ["forgotten_subscription"]).flags] == ["new_regular_payment"], cid
    for cid in IDS:
        kinds = [x.kind for x in facts_for(cid, ["price_rise"]).flags]
        assert kinds == ["price_rise"], (cid, kinds)


def test_the_six_stories():
    jay = facts_for("JDN-2208")
    assert {m.month: m.status for m in jay.forecast}["December"] == "short" and jay.forecast[0].reason == "lower income"
    assert jay.suggestion is None  # no "put aside for lower income" nonsense
    ami = facts_for("AMR-3135")
    assert any(m.status == "warn" for m in ami.forecast) and any(o.name == "TV licence" for o in ami.last_month.out)
    dan = facts_for("DAN-5502")
    assert dan.cash_blind_spot and any(m.reason == "TV licence" for m in dan.forecast)
    sam = facts_for("SAM-7316")
    assert sam.headline_status == "good" and all(m.status == "ok" for m in sam.forecast) and sam.flags == []
    rav = facts_for("RAV-6049", end=(2026, 12), as_of=date(2027, 1, 1))  # after "Next month"
    assert [m.status for m in rav.forecast] == ["warn", "ok", "short"] and rav.forecast[2].reason == "car insurance"
    assert rav.suggestion and "car insurance" in rav.suggestion.text_hint


def test_each_persona_has_its_own_seeded_case(client):
    for cid, spec in SPECS.items():
        [c] = client.get(f"/cases?customer={cid}").json()
        assert c["customer"] == cid and c["source"] == spec.case.source and c["status"] == "prepared"
    assert len(client.get("/cases?customer=all").json()) == 6
    assert client.get("/cases?customer=NOPE").status_code == 404


def test_seeded_urgency_and_routing_follow_the_same_rules(client):
    def case(cid):
        return client.get(f"/cases?customer={cid}").json()[0]
    assert case("AMR-3135")["urgency"] == "normal"      # "payment called ..." is not a phone call
    assert case("DAN-5502")["urgency"] == "high"        # the worried box is ticked (CLAUDE.md triage rule)
    assert case("DAN-5502")["route"]["team"] == "phone"
    assert (case("JDN-2208")["route"]["team"], case("JDN-2208")["due"]) == ("banker", "2026-12-03")   # Thursday
    assert case("RAV-6049")["route"] == {"team": "phone", "reason": "Next hub day (Tuesday)"}
    assert case("RAV-6049")["category"] == "afford_purchase"


def test_state_is_keyed_by_customer(client):
    r = client.post("/customers/JDN-2208/events", json={"event": "scam_transfer"}).json()
    assert r["new_case_id"] and len(r["new_flags"]) == 1
    assert client.get("/demo/state?customer=JDN-2208").json()["events_applied"] == ["scam_transfer"]
    assert client.get("/demo/state").json() == {"as_of": "2026-12-01", "events_applied": [], "facts_version": 1}  # Margaret untouched
    assert client.get("/customers/MRG-4471/facts").json()["flags"] == []
    assert [c["urgency"] for c in client.get("/cases?customer=MRG-4471").json()] == ["normal"]
    assert [c["urgency"] for c in client.get("/cases?customer=JDN-2208").json()] == ["high", "normal"]
    client.post("/demo/next-month?customer=SAM-7316")
    assert client.get("/demo/state?customer=SAM-7316").json()["as_of"] == "2027-01-01"
    assert client.get("/demo/state?customer=AMR-3135").json()["as_of"] == "2026-12-01"


def test_access_log_and_what_we_know_are_scoped(client):
    [jc] = client.get("/cases?customer=JDN-2208").json()
    client.get(f"/cases/{jc['id']}?viewer=helper:daria")
    client.get("/customers/JDN-2208/dashboard?viewer=helper:daria")
    jay = client.get("/customers/JDN-2208/what-we-know").json()
    assert [e["who"] for e in jay["access_log"]] == ["Daria", "Daria"] and "Looked at your dashboard" in [e["what"] for e in jay["access_log"]]
    assert client.get("/customers/MRG-4471/what-we-know").json()["access_log"] == []
    assert set(jay) == {"profile", "data_held", "access_log"} and "trusted_person" not in str(jay)
    assert [d["label"] for d in jay["data_held"]] == ["Your details", "Your bank payments", "Your letters", "Your questions", "Helper notes"]
    assert jay["data_held"][3]["count"] == 1


def test_reset_resets_all_six(client):
    client.post("/customers/JDN-2208/events", json={"event": "scam_transfer"})
    client.post("/demo/next-month?customer=RAV-6049")
    client.post("/demo/reset")
    for cid in IDS:
        s = client.get(f"/demo/state?customer={cid}").json()
        assert s["events_applied"] == [] and s["as_of"] == "2026-12-01"
        assert len(client.get(f"/cases?customer={cid}").json()) == 1
    assert client.get("/customers/JDN-2208/facts").json()["flags"] == []


def test_no_persona_specific_code_outside_personas_py():
    """Same functions, same thresholds, same templates: only data differs (personas.md rule 5)."""
    names = [s.name for s in SPECS.values()]
    pat = re.compile("|".join([r"\b%s\b" % n for n in names] + [re.escape(i) for i in IDS]))
    src = Path(__file__).resolve().parents[1] / "counterpart"
    offenders = []
    for f in src.rglob("*.py"):
        if f.name == "personas.py":
            continue
        for n, line in enumerate(f.read_text().splitlines(), 1):
            code = line.split("#")[0]
            if pat.search(code) and not line.strip().startswith(('"""', "'''")) and "default Margaret" not in line and "Margaret's as_of" not in line:
                offenders.append(f"{f.name}:{n}: {line.strip()[:80]}")
    assert offenders == [], offenders


def test_trusted_person_and_family_are_gone(client):
    assert client.get("/customers/MRG-4471/family-alerts").status_code == 404
    assert client.post("/cases", json={"source": "trusted_person", "text": "hi"}).status_code == 422
    from counterpart import models
    assert not hasattr(models, "TrustedPerson")
