import json
from datetime import date

import pytest

from counterpart import db
from counterpart.generator import generate
from counterpart.guardrails import check_text, allowed_numbers
from counterpart.llm import prompts
from counterpart.llm.client import LLMClient, LLMUnavailable
from counterpart.llm.writers import draft_reply, triage, write_sections
from counterpart.models import SinceLastVisit
from counterpart.personas import MARGARET
from counterpart.pipeline import build_facts

H = SinceLastVisit(helper="Priya", note="Set up heating pot, £20 a month", date=date(2026, 12, 1))
SCEN = {
    "clean": build_facts(MARGARET, generate(MARGARET), date(2026, 12, 1)),
    "scam": build_facts(MARGARET, generate(MARGARET, events=["scam_transfer"]), date(2026, 12, 1)),
    "sub": build_facts(MARGARET, generate(MARGARET, events=["forgotten_subscription"]), date(2026, 12, 1)),
    "rise": build_facts(MARGARET, generate(MARGARET, events=["price_rise"]), date(2026, 12, 1)),
    "note": build_facts(MARGARET, generate(MARGARET, months=19, end=(2026, 12)), date(2027, 1, 1), H),
}
STUB = LLMClient(mode="stub")


@pytest.mark.parametrize("name", SCEN)
def test_template_writer_passes_every_guardrail(name):
    f = SCEN[name]
    g = write_sections(f, STUB)
    assert g.source == "stub" and g.guardrail["caught"] is False
    assert list(g.texts) == [k for k in prompts.SECTION_IDS if k != "idea" or f.suggestion]  # fixed order
    allowed = allowed_numbers(f)
    assert all(check_text(t, allowed=allowed) == [] for t in g.texts.values())


def test_template_text_tells_the_fixture_story():
    t = write_sections(SCEN["clean"], STUB).texts
    assert "£1,280 came in" in t["last_month"] and "£230 left over" in t["last_month"]
    assert "£990 spare" in t["forecast"] and "TV licence of £175" in t["forecast"] and "£348 spare" in t["forecast"]
    assert t["scam_watch"].startswith("Nothing unusual")
    assert t["since_visit"] == "Nothing new since we last spoke."


def test_scam_text_and_idea_omitted():
    g = write_sections(SCEN["scam"], STUB)
    assert "idea" not in g.texts
    assert "£1,770 more went out than came in" in g.texts["last_month"]
    assert "£2,000 on 18 November" in g.texts["scam_watch"] and "back of your bank card" in g.texts["scam_watch"]


def test_note_appears_in_text():
    assert "Priya agreed: Set up heating pot, £20 a month." in write_sections(SCEN["note"], STUB).texts["since_visit"]


def test_demo_bad_number_flag_gives_the_badge_and_a_clean_result():
    c = db.connect(":memory:")
    db.init_db(c)
    g = write_sections(SCEN["clean"], STUB, conn=c, demo_bad_number=True)
    assert g.guardrail["caught"] and g.guardrail["events"][0]["detail"].startswith("£2,400 was not in the facts")
    assert "2,400" not in " ".join(g.texts.values())
    assert c.execute("SELECT COUNT(*) FROM guardrail_events").fetchone()[0] == 1


# ---- client / cache / live path with a fake model ----

def fake_client(tmp_path, mode, outputs, monkeypatch):
    """A client whose 'API' returns the queued outputs."""
    c = LLMClient(mode=mode, model="test-model", cache_dir=tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    calls = []

    def fake(system, user, *, attempt=0, fresh=False):
        key = c._key(system, user, attempt)
        if not fresh and (hit := c._read(key)) is not None:
            return hit
        if mode != "live":
            raise LLMUnavailable("not in cache")
        calls.append(attempt)
        out = outputs[min(len(calls) - 1, len(outputs) - 1)]
        c._write(key, system, user, out)
        return out

    monkeypatch.setattr(c, "complete_json", fake)
    return c, calls


def test_live_bad_number_is_regenerated(tmp_path, monkeypatch):
    f = SCEN["clean"]
    good = write_sections(f, STUB).texts
    bad = dict(good, forecast=good["forecast"] + " A boiler costs £2,400.")
    c, calls = fake_client(tmp_path, "live", [bad, good], monkeypatch)
    g = write_sections(f, c)
    assert g.source == "llm" and g.texts == good and calls == [0, 1]
    assert g.guardrail["events"][0]["action"] == "regenerated"


def test_live_always_bad_falls_back_to_templates(tmp_path, monkeypatch):
    f = SCEN["clean"]
    bad = dict(write_sections(f, STUB).texts, headline="Pay £999 now")
    c, calls = fake_client(tmp_path, "live", [bad], monkeypatch)
    g = write_sections(f, c)
    assert g.source == "fallback" and len(calls) == 3 and g.guardrail["caught"]
    assert g.texts == write_sections(f, STUB).texts


def test_unavailable_api_falls_back(tmp_path, monkeypatch):
    c = LLMClient(mode="cached", model="m", cache_dir=tmp_path)
    assert write_sections(SCEN["clean"], c).source == "fallback"


def test_model_inventing_an_idea_is_dropped(tmp_path, monkeypatch):
    f = SCEN["scam"]  # code produced no suggestion
    out = dict(write_sections(f, STUB).texts, idea="Put £20 aside.")
    c, _ = fake_client(tmp_path, "live", [out], monkeypatch)
    assert "idea" not in write_sections(f, c).texts


def test_cache_roundtrip_and_key_depends_on_model(tmp_path):
    a = LLMClient(mode="cached", model="m1", cache_dir=tmp_path)
    a._write(a._key("s", "u", 0), "s", "u", {"x": 1})
    assert a.complete_json("s", "u") == {"x": 1}
    with pytest.raises(LLMUnavailable):
        LLMClient(mode="cached", model="m2", cache_dir=tmp_path).complete_json("s", "u")
    with pytest.raises(LLMUnavailable):
        LLMClient(mode="stub", cache_dir=tmp_path).complete_json("s", "u")


def test_live_without_key_is_unavailable_not_a_crash(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(LLMUnavailable):
        LLMClient(mode="live", model="m", cache_dir=tmp_path).complete_json("s", "u")


# ---- triage and reply ----

@pytest.mark.parametrize("text,ticks,cat,urg", [
    ("Can I afford a new boiler?", [], "afford_purchase", "normal"),
    ("Someone phoned me asking for money", [], "scam_worry", "high"),
    ("Why was my gas bill higher?", [], "bill_query", "normal"),
    ("Can I afford a new boiler?", ["worried"], "afford_purchase", "high"),
    ("Hello", ["scam_call"], "scam_worry", "high"),
    ("I got a text about my parcel", [], "scam_worry", "high"),
])
def test_triage_rules(text, ticks, cat, urg):
    r = triage(text, ticks, STUB)
    assert (r["category"], r["urgency"]) == (cat, urg)


def test_model_cannot_lower_urgency(tmp_path, monkeypatch):
    c, _ = fake_client(tmp_path, "live", [{"category": "general", "urgency": "normal", "summary": "x"}], monkeypatch)
    assert triage("Someone phoned me", [], c)["urgency"] == "high"


def test_reply_may_use_case_numbers_only_plus_facts():
    f = SCEN["clean"]
    g = draft_reply(f, "Can I afford a boiler?", "Priya", "Suggest a heating pot, £20 a month, over a year that is £240", [240], STUB)
    assert g.source == "stub" and "£240" in g.texts["text"] and g.texts["text"].startswith("Dear Margaret")
    from counterpart.guardrails import GuardrailFailure
    with pytest.raises(GuardrailFailure):  # a helper note with an unverified figure is blocked
        draft_reply(f, "q", "Priya", "A boiler costs £2,400", [], STUB)
