from decimal import Decimal

import pytest

from counterpart import db
from counterpart.generator import generate
from counterpart.guardrails import (
    GuardrailFailure, allowed_numbers, check_banned, check_numbers, corrupt_with_bad_number,
    extract_amounts, run_guarded,
)
from counterpart.persona import MARGARET
from counterpart.pipeline import build_facts
from datetime import date, datetime

CLEAN = build_facts(MARGARET, generate(MARGARET), date(2026, 12, 1))
SCAM = build_facts(MARGARET, generate(MARGARET, events=["scam_transfer"]), date(2026, 12, 1))
OK = {"last_month": "In November, £1,280 came in. Rent was £480 and you had £230 left over.",
      "forecast": "January looks tight, with about £15 spare, because your TV licence of £175 is due."}


def details(issues):
    return [i.detail for i in issues]


def test_allowed_numbers_come_from_money_fields_not_years():
    a = allowed_numbers(CLEAN)
    assert {1280, 480, 118, 92, 86, 160, 230, 990, 15, 175, 348, 20} <= a
    assert 2026 not in a and 2027 not in a


def test_negative_left_is_allowed_as_absolute():
    assert 1770 in allowed_numbers(SCAM) and 2000 in allowed_numbers(SCAM)


def test_amounts_inside_facts_strings_are_allowed():
    assert allowed_numbers({"r": "was £28 now £33"}) == {28, 33}
    assert 20 in allowed_numbers({"since_last_visit": {"note": "Set up heating pot, £20 a month"}})


def test_good_text_passes():
    assert all(check_numbers(t, CLEAN) == [] for t in OK.values())


def test_hallucinated_2400_is_caught():
    assert details(check_numbers("You will need £2,400 for a boiler.", CLEAN)) == ["£2,400 was not in the facts"]


def test_pence_round_to_the_pound():
    assert check_numbers("A payment of £9.99 started.", {"amount": 10}) == []
    assert check_numbers("Rent of £480.40", CLEAN) == []  # rounds to 480
    assert check_numbers("Rent of £481", CLEAN) != []


def test_pounds_written_in_words_are_checked_too():
    assert check_numbers("about 2400 pounds", CLEAN) != []
    assert check_numbers("about 20 pounds", CLEAN) == []


def test_amount_is_not_vouched_for_by_a_year():
    assert check_numbers("You will pay £2,026.", CLEAN) != []


def test_extract_handles_commas_and_spacing():
    assert [v for _, v in extract_amounts("£1,280 and £ 20 and £9.99")] == [Decimal("1280"), Decimal("20"), Decimal("9.99")]


@pytest.mark.parametrize("text", [
    "Visit https://natwest.com/help", "Go to www.example.org", "Email help@bank.co.uk",
    "Call 0800 123 4567 today", "Ring 01632 960 001", "Call +44 20 7946 0958",
    "Scan the QR code", "Click here", "Please verify your details", "Confirm your account now",
    "Urgent action needed", "Reply immediately", "Tell us your PIN", "Please give us your card number",
])
def test_banned_content_is_caught(text):
    assert check_banned(text) != []


@pytest.mark.parametrize("text", [
    "Use the number on the back of your bank card.",
    "We will never ask for your details in a letter.",
    "If someone calls and asks you for money, put the phone down.",
    "In November, £1,280 came in on 3 November 2026.",
    "Free help is available from MoneyHelper and Citizens Advice.",
    "Reference MRG-4471.",
])
def test_safe_text_is_not_blocked(text):
    assert check_banned(text) == []


def conn():
    c = db.connect(":memory:")
    db.init_db(c)
    return c


def test_run_guarded_clean_first_time():
    g = run_guarded(lambda n: OK, allowed_numbers(CLEAN))
    assert g.source == "llm" and g.guardrail == {"caught": False, "events": []}


def test_bad_number_then_regenerated_clean_is_the_demo_badge():
    allowed = allowed_numbers(CLEAN)
    c = conn()
    g = run_guarded(lambda n: corrupt_with_bad_number(OK, allowed) if n == 0 else OK, allowed, conn=c, context="letter")
    assert g.texts == OK and g.source == "llm"
    assert g.guardrail["caught"] is True
    [e] = g.guardrail["events"]
    assert (e["check"], e["action"]) == ("numbers", "regenerated")
    assert e["detail"].startswith("£2,400 was not in the facts")
    datetime.fromisoformat(e["at"])
    assert c.execute("SELECT COUNT(*) FROM guardrail_events").fetchone()[0] == 1  # logged


def test_persistent_failure_retries_twice_then_raises():
    calls = []
    bad = {"a": "Pay £999 now"}

    def produce(n):
        calls.append(n)
        return bad

    with pytest.raises(GuardrailFailure) as ex:
        run_guarded(produce, allowed_numbers(CLEAN))
    assert calls == [0, 1, 2]  # one try + two retries
    assert [e["action"] for e in ex.value.events if e["check"] == "numbers"] == ["regenerated", "regenerated", "blocked"]


def test_fallback_is_used_and_marked():
    g = run_guarded(lambda n: {"a": "Pay £999"}, allowed_numbers(CLEAN), fallback=lambda: OK)
    assert g.source == "fallback" and g.texts == OK and g.guardrail["caught"] is True


def test_fallback_is_checked_too():
    with pytest.raises(GuardrailFailure):
        run_guarded(lambda n: {"a": "Pay £999"}, allowed_numbers(CLEAN), fallback=lambda: {"a": "Pay £888"})


def test_banned_text_triggers_regeneration():
    g = run_guarded(lambda n: {"a": "Visit www.x.com"} if n == 0 else OK, allowed_numbers(CLEAN))
    assert g.guardrail["events"][0]["check"] == "banned"


def test_extra_case_numbers_are_allowed():
    text = {"reply": "Saving £20 a month for a year is £240."}
    assert check_numbers(text["reply"], CLEAN) != []
    assert run_guarded(lambda n: text, allowed_numbers(CLEAN, extra=[240])).source == "llm"


def test_corrupt_helper_never_picks_an_allowed_figure():
    allowed = {2400, 2407}
    assert "£2,414" in corrupt_with_bad_number(OK, allowed)["forecast"]
