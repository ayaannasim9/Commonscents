from datetime import date

import pytest

from counterpart.generator import generate
from counterpart.merchants import categorise, payee_of
from counterpart.persona import MARGARET
from counterpart.pipeline import build_facts
from counterpart.pipeline.common import pounds

AS_OF = date(2026, 12, 1)


@pytest.fixture(scope="module")
def txs():
    return generate(MARGARET)


def facts(txs):
    return build_facts(MARGARET, txs, AS_OF)


def test_generator_is_reproducible_and_18_months(txs):
    assert txs == generate(MARGARET)
    assert (txs[0].date, txs[-1].date) == (date(2025, 6, 1), date(2026, 11, 30))


def test_history_stable_when_a_month_is_appended(txs):
    longer = generate(MARGARET, months=19, end=(2026, 12))
    keep = {(t.date, t.description, t.amount_pence, t.time) for t in txs}
    assert keep <= {(t.date, t.description, t.amount_pence, t.time) for t in longer}


def test_money_is_integer_pence(txs):
    assert all(isinstance(t.amount_pence, int) for t in txs)


def test_every_description_is_categorised(txs):
    assert all(categorise(t.description).key != "unknown" for t in txs)


def test_friday_cash_is_forty_pounds(txs):
    cash = [t for t in txs if t.channel == "cash_withdrawal"]
    assert cash and all(t.amount_pence == -4000 and t.date.weekday() == 4 for t in cash)


def test_council_tax_ten_months(txs):
    months = {t.date.month for t in txs if "CNCL TAX" in t.description}
    assert months == set(range(1, 13)) - {2, 3}


def test_clean_november_numbers(txs):
    lm = facts(txs).last_month
    assert (lm.month, lm.year, lm.in_, lm.cash, lm.left) == ("November", 2026, 1280, 160, 230)
    assert lm.in_ - sum(i.amount for i in lm.out) - lm.cash == lm.left  # the page adds up
    assert [(i.name, i.amount) for i in lm.out][:4] == [("Rent", 480), ("Council tax", 118), ("Local shop", 92), ("Gas", 86)]


def test_clean_forecast_matches_fixture_story(txs):
    f = facts(txs).forecast
    assert [(m.month, m.year, m.status, m.reason, m.extra, m.spare) for m in f] == [
        ("December", 2026, "ok", "two pension payments", 0, 990),
        ("January", 2027, "warn", "TV licence", 175, 15),
        ("February", 2027, "ok", "nothing unusual", 0, 348),
    ]


def test_clean_headline_suggestion_flags(txs):
    f = facts(txs)
    assert f.headline_status == "heads_up"
    assert f.flags == [] and f.cash_blind_spot is True and f.since_last_visit is None
    assert f.suggestion and f.suggestion.amount == 20 and "TV licence" in f.suggestion.text_hint


def test_scam_transfer_flagged():
    f = facts(generate(MARGARET, events=["scam_transfer"]))
    assert f.last_month.left == -1770
    assert f.headline_status == "attention"
    [flag] = f.flags
    assert (flag.kind, flag.severity, flag.amount, flag.date) == ("unusual_payment", "high", 2000, date(2026, 11, 18))
    assert flag.id == "flag_0001"
    assert "Made late in the evening" in flag.reasons and flag.reasons[0].startswith("First time")
    assert f.cash_blind_spot is True  # one-offs do not dilute the cash test
    assert f.suggestion is None  # no savings nudge in the same breath as a fraud alert


def test_big_daytime_payment_to_known_style_still_needs_new_payee():
    assert payee_of("FASTER PMT TO M HOLLOWAY 04-00-75 ****3391") == "M HOLLOWAY"
    assert payee_of("DD EDF ENERGY 7710") is None


def test_forgotten_subscription_flag_and_forecast():
    f = facts(generate(MARGARET, events=["forgotten_subscription"]))
    [flag] = f.flags
    assert (flag.kind, flag.amount) == ("new_regular_payment", 10)
    assert f.forecast[0].spare == 980  # 990 less £9.99, it recurs


def test_price_rise_flag():
    f = facts(generate(MARGARET, events=["price_rise"]))
    [flag] = f.flags
    assert flag.kind == "price_rise" and flag.amount == 33
    assert flag.reasons[0] == "It was £28 and is now £33"


def test_ordinary_bills_do_not_trip_price_rise(txs):
    # gas doubles every November and the phone rose 7% in April: neither is a flag
    assert facts(txs).flags == []


def test_after_a_month_the_story_rolls(txs):
    longer = generate(MARGARET, months=19, end=(2026, 12))
    f = build_facts(MARGARET, longer, date(2027, 1, 1))
    assert (f.last_month.month, f.last_month.in_, f.last_month.left) == ("December", 2040, 990)
    assert [(m.month, m.spare) for m in f.forecast] == [("January", 15), ("February", 348), ("March", 348)]


def test_pounds_rounds_half_up_and_keeps_sign():
    assert [pounds(x) for x in (999, 50, 49, -1770_00, -150, 0)] == [10, 1, 0, -1770, -2, 0]


def test_contract_shape_uses_in_not_in_underscore(txs):
    d = facts(txs).to_contract()
    assert "in" in d["last_month"] and "in_" not in d["last_month"]
