import pytest
from fastapi.testclient import TestClient

from counterpart.app import create_app
from counterpart.llm.client import LLMClient
from test_api import C, check_shape, fx


@pytest.fixture
def client():
    return TestClient(create_app(":memory:", LLMClient(mode="stub")))


def boiler(client):
    [b] = [c for c in client.get("/cases").json() if c["source"] == "slip_post_office"]
    return b["id"]


def test_seeded_boiler_case_matches_fixture(client):
    cid = boiler(client)
    c = client.get(f"/cases/{cid}?viewer=helper:priya").json()
    ref = fx("case.boiler.prepared.json")
    check_shape(c, ref)
    for k in ("source", "status", "urgency", "category", "summary", "question_text", "ticks", "route", "due"):
        assert c[k] == ref[k], k
    assert c["briefing"] == ref["briefing"]  # numbers, flags and checks match, all computed in code


def test_list_contract_and_order(client):
    check_shape(client.get("/cases").json(), fx("cases.list.json"))
    r = client.post(f"{C}/events", json={"event": "scam_transfer"}).json()
    assert r["new_case_id"]
    lst = client.get("/cases").json()
    assert [c["urgency"] for c in lst] == ["high", "normal"]  # urgent on top
    check_shape(lst, fx("cases.list.json"))
    urgent = lst[0]
    assert (urgent["source"], urgent["summary"], urgent["due"]) == ("system_flag", "Unusual £2,000 payment to a new person", "2026-12-01")
    assert urgent["route"] == {"team": "phone", "reason": "Urgent: phone team, due today"}


def test_scam_case_matches_fixture_and_is_not_duplicated(client):
    client.post(f"{C}/events", json={"event": "scam_transfer"})
    again = client.post(f"{C}/events", json={"event": "scam_transfer"}).json()
    assert again["new_case_id"] is None and len(client.get("/cases").json()) == 2
    cid = client.get("/cases?urgency=high").json()[0]["id"]
    c = client.get(f"/cases/{cid}").json()
    ref = fx("case.scam.prepared.json")
    check_shape(c, ref)
    assert c["briefing"]["numbers"][0] == ref["briefing"]["numbers"][0]
    assert c["briefing"]["open_flags"] == ["flag_0001"] and c["question_text"] is None


def test_new_urgent_question_routes_to_phone(client):
    c = client.post("/cases", json={"source": "phone", "text": "Someone rang asking for money", "ticks": []}).json()
    assert (c["urgency"], c["category"], c["route"]["team"], c["status"]) == ("high", "scam_worry", "phone", "prepared")
    n = client.post("/cases", json={"source": "slip_post", "text": "Why is my gas bill higher?", "ticks": ["bill"]}).json()
    assert (n["urgency"], n["route"]["reason"], n["due"]) == ("normal", "Next hub day (Tuesday)", "2026-12-08")
    assert client.post("/cases", json={"source": "x", "text": "hi"}).status_code == 422
    assert client.post("/cases", json={"source": "phone", "text": "hi", "ticks": ["nope"]}).status_code == 422


def test_viewing_a_case_is_logged(client):
    cid = boiler(client)
    client.get(f"/cases/{cid}?viewer=helper:priya:banker")
    rows = client.app.state.db.execute("SELECT who, role, what FROM access_log").fetchall()
    assert [(r["who"], r["role"]) for r in rows] == [("Priya", "banker")] and "boiler" in rows[0]["what"]
    assert client.get("/cases/case_9999").status_code == 404


def test_approval_gate_409s(client):
    cid = boiler(client)
    assert client.post(f"/cases/{cid}/approve").status_code == 409          # nothing drafted
    assert client.post(f"/cases/{cid}/draft-reply").status_code == 409      # needs a note first
    client.post(f"/cases/{cid}/note", json={"note": "Talked it through.", "helper": "Priya"})
    assert client.get(f"/cases/{cid}").json()["status"] == "with_helper"
    assert client.post(f"/cases/{cid}/approve").status_code == 409          # note but no draft


def test_draft_with_unverified_number_cannot_be_approved(client):
    cid = boiler(client)
    client.post(f"/cases/{cid}/note", json={"note": "Suggest a heating pot, £20 a month.", "helper": "Priya"})
    d = client.post(f"/cases/{cid}/draft-reply").json()
    assert d["status"] == "draft_ready" and d["draft"]["guardrail"]["caught"] is False
    bad = client.post(f"/cases/{cid}/draft", json={"text": "Dear Margaret, a boiler costs £2,400. Priya"}).json()
    assert bad["status"] == "with_helper" and bad["draft"]["guardrail"]["events"][0]["action"] == "blocked"
    assert client.post(f"/cases/{cid}/approve").status_code == 409
    ok = client.post(f"/cases/{cid}/draft", json={"text": "Dear Margaret, saving £20 a month is £240 in a year. Priya"}).json()
    assert ok["status"] == "draft_ready" and ok["draft"]["source"] == "helper"
    assert client.post(f"/cases/{cid}/approve", json={"helper": "Priya"}).json()["status"] == "approved"
    assert client.post(f"/cases/{cid}/note", json={"note": "x"}).status_code == 409  # locked once approved


def test_note_with_unverified_figure_blocks_the_draft(client):
    cid = boiler(client)
    client.post(f"/cases/{cid}/note", json={"note": "Boilers cost about £2,400.", "helper": "Priya"})
    r = client.post(f"/cases/{cid}/draft-reply")
    assert r.status_code == 422 and "blocked" in r.json()["detail"]["message"]


def test_the_full_demo_loop(client):
    v0 = client.get(f"{C}/dashboard").json()
    assert "Nothing new since we last spoke" in next(s for s in v0["sections"] if s["id"] == "since_visit")["text"]
    assert client.post(f"{C}/events", json={"event": "scam_transfer"}).json()["new_case_id"]       # step 2
    cid = boiler(client)                                                                            # step 3
    client.get(f"/cases/{cid}?viewer=helper:priya")
    client.post(f"/cases/{cid}/note", json={"note": "Set up a heating pot, £20 a month", "helper": "Priya"})
    d = client.post(f"/cases/{cid}/draft-reply").json()
    check_shape(d, fx("case.boiler.draft-ready.json"))
    a = client.post(f"/cases/{cid}/approve", json={"helper": "Priya"}).json()
    check_shape(a, fx("case.boiler.approved.json"))
    assert a["status"] == "approved" and a["approved_at"]
    assert client.post("/demo/next-month").json() == {"as_of": "2027-01-01"}                       # step 4
    dash = client.get(f"{C}/dashboard").json()
    visit = next(s for s in dash["sections"] if s["id"] == "since_visit")["text"]
    assert visit == "When we last spoke, Priya agreed: Set up a heating pot, £20 a month."
    assert dash["facts"]["since_last_visit"] == {"helper": "Priya", "note": "Set up a heating pot, £20 a month", "date": "2026-12-01"}
    assert visit in client.get(f"{C}/letter.html").text                                              # letter agrees
    assert client.get(f"/cases/{cid}").json()["status"] == "closed"
    assert cid not in [c["id"] for c in client.get("/cases").json()]                                # off the queue
    assert cid in [c["id"] for c in client.get("/cases?status=closed").json()]
    client.post("/demo/next-month")                                                                  # and it rolls off again
    assert client.get(f"{C}/facts").json()["since_last_visit"] is None


def test_reset_restores_the_demo(client):
    cid = boiler(client)
    client.post(f"/cases/{cid}/note", json={"note": "x", "helper": "Priya"})
    client.post(f"{C}/events", json={"event": "scam_transfer"})
    client.post("/demo/reset")
    lst = client.get("/cases").json()
    assert [c["source"] for c in lst] == ["slip_post_office"] and lst[0]["id"] == "case_0001" and lst[0]["status"] == "prepared"
    assert client.app.state.db.execute("SELECT COUNT(*) FROM access_log").fetchone()[0] == 0


def test_afford_case_after_scam_has_no_saving_number_but_open_flag(client):
    client.post(f"{C}/events", json={"event": "scam_transfer"})
    client.post("/demo/reset")  # reset clears; plant again then add a fresh question
    client.post(f"{C}/events", json={"event": "scam_transfer"})
    c = client.post("/cases", json={"source": "counter_verbal", "text": "Can I afford a new fridge?", "ticks": []}).json()
    assert c["briefing"]["open_flags"] == ["flag_0001"]
    assert [n["value"] for n in c["briefing"]["numbers"]] == [-1770, 240]  # scenario kept even though the letter's idea is withheld
