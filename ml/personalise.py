"""Turn the 4 onboarding answers into changes to the forecast, stress tests and a goal plan.

answers = {
  "goal":   "Build savings" | "Buy a home" | "Pay off debt" | "Manage monthly expenses" | "Retirement",
  "worry":  "Unexpected bills" | "Running out of money before payday" | "Debt" | "Not saving enough" | "Job security",
  "life_changes": ["Moving home", "New job", "Graduation", "Retirement", "New child"] or ["None"],
  "life_change_dates": {"Moving home": "2027-03-01"},          # optional, otherwise sensible defaults
  "shock_500": "Savings" | "Credit card" | "Overdraft" | "Borrowing from family/friends" | "I couldn't cover it",
}
"""
from datetime import date

import numpy as np
import pandas as pd


def money(x):
    return f"-£{abs(x):,.0f}" if x < 0 else f"£{x:,.0f}"

EARNED = {"salary", "wages"}

# Placeholder costs for life events. Labelled as assumptions in the output and report.
LIFE_EVENTS = {
    "moving_home": {"default_days": 90, "one_off": -1200, "monthly": 0,
                    "assumption": "Moving costs and an overlapping deposit of about £1,200"},
    "new_job": {"default_days": 60, "one_off": 0, "monthly": 0,
                "assumption": "Pay changes by about +8% (could be -15% to +30%), with a 30% chance of a missed payday while switching"},
    "graduation": {"default_days": None, "one_off": 0, "monthly": 0,
                   "assumption": "Student loan payments stop after graduation in July"},
    "retirement": {"default_days": 180, "one_off": 0, "monthly": 0,
                   "assumption": "Earned income replaced by a pension of about 55% of current pay"},
    "new_child": {"default_days": 180, "one_off": -800, "monthly": -450,
                  "assumption": "About £450 a month in extra costs plus £800 for essentials at the start"},
}

_GOALS = {"build savings": "build_savings", "buy a home": "buy_home", "pay off debt": "pay_off_debt",
          "manage monthly expenses": "manage_expenses", "retirement": "retirement"}
_WORRIES = {"unexpected bills": "unexpected_bills", "running out of money before payday": "running_out",
            "debt": "debt", "not saving enough": "not_saving", "job security": "job_security"}
_CHANGES = {"moving home": "moving_home", "new job": "new_job", "graduation": "graduation",
            "retirement": "retirement", "new child": "new_child"}
_SHOCK = {"savings": "savings", "credit card": "credit_card", "overdraft": "overdraft",
          "borrowing from family/friends": "family_friends", "i couldn't cover it": "cannot_cover"}
SHOCK_LABEL = {"savings": "savings", "credit_card": "a credit card", "overdraft": "your overdraft",
               "family_friends": "borrowing from family or friends", "cannot_cover": "nothing (you said you couldn't cover it)"}
SHOCK_WEIGHT = {"savings": 0.0, "overdraft": 0.5, "credit_card": 0.6, "family_friends": 0.8, "cannot_cover": 1.2}


def _norm(v, table):
    if v is None:
        return None
    k = str(v).strip().lower().replace("’", "'")
    return table.get(k, k.replace(" ", "_"))


def normalise(answers):
    a = answers or {}
    changes = [_norm(c, _CHANGES) for c in a.get("life_changes", []) if str(c).strip().lower() != "none"]
    dates = {_norm(k, _CHANGES): v for k, v in (a.get("life_change_dates") or {}).items()}
    return {"goal": _norm(a.get("goal"), _GOALS), "worry": _norm(a.get("worry"), _WORRIES),
            "life_changes": [c for c in changes if c in LIFE_EVENTS], "life_change_dates": dates,
            "shock_500": _norm(a.get("shock_500"), _SHOCK)}


def _event_day(change, dates, today, horizon):
    if change in dates:
        d = (pd.Timestamp(dates[change]) - pd.Timestamp(today)).days
    elif change == "graduation":
        d = (pd.Timestamp(date(today.year if today.month < 7 else today.year + 1, 7, 1)) - pd.Timestamp(today)).days
    else:
        d = LIFE_EVENTS[change]["default_days"]
    return int(np.clip(d, 1, horizon)) - 1


def apply_life_changes(flows, scheduled, a, today, rng):
    """Return adjusted copy of flows and a list of what was applied."""
    flows = flows.copy()
    n, horizon = flows.shape
    applied = []
    for ch in a["life_changes"]:
        ev = LIFE_EVENTS[ch]
        i0 = _event_day(ch, a["life_change_dates"], today, horizon)
        when = (pd.Timestamp(today) + pd.Timedelta(days=i0 + 1)).date()
        effect = []
        if ev["one_off"]:
            flows[:, i0] += ev["one_off"]
            effect.append(f"£{abs(ev['one_off']):,} one-off")
        if ev["monthly"]:
            flows[:, i0:] += ev["monthly"] / 30.4
            effect.append(f"£{abs(ev['monthly']):,}/month")
        if ch == "new_job":
            mult = rng.lognormal(np.log(1.08), 0.12, n)
            first = True
            for s in scheduled:
                if s["category"] in EARNED and s["amount"] > 0 and s["day_index"] >= i0:
                    i = s["day_index"]
                    flows[:, i] += s["_vals"] * (mult - 1)
                    if first:  # possible missed payday when switching
                        flows[:, i] -= s["_vals"] * mult * (rng.random(n) < 0.3)
                        first = False
            effect.append("pay changes, possible gap between jobs")
        if ch == "retirement":
            for s in scheduled:
                if s["category"] in EARNED and s["amount"] > 0 and s["day_index"] >= i0:
                    flows[:, s["day_index"]] -= s["_vals"] * 0.45
            effect.append("earned income falls to about 55%")
        if ch == "graduation":
            lost = 0
            for s in scheduled:
                if s["category"] == "student_finance" and s["day_index"] >= i0:
                    flows[:, s["day_index"]] -= s["_vals"]
                    lost += s["amount"]
            effect.append(f"£{lost:,.0f} of student loan payments stop" if lost else "no student loan after this date")
        applied.append({"change": ch.replace("_", " ").capitalize(), "date": when.isoformat(),
                        "day_index": i0, "effect": ", ".join(effect), "assumption": ev["assumption"]})
    return flows, applied


def _risk(b, limit, days=90):
    return {"prob_below_zero": round(float((b[:, :days] < 0).any(axis=1).mean()), 2),
            "prob_beyond_overdraft": round(float((b[:, :days] < -limit).any(axis=1).mean()), 2),
            "lowest_expected_balance": round(float(np.percentile(b[:, :days], 50, axis=0).min()), 2)}


def stress_tests(flows, scheduled, current, limit, today):
    base = current + np.cumsum(flows, axis=1)
    out = {"baseline": _risk(base, limit)}
    # £500 surprise bill tomorrow
    out["surprise_bill_500"] = _risk(base - 500, limit)
    # pay stops for 2 months starting in 30 days
    f2 = flows.copy()
    lost = 0.0
    for s in scheduled:
        if s["category"] in EARNED and s["amount"] > 0 and 30 <= s["day_index"] < 90:
            f2[:, s["day_index"]] -= s["_vals"]
            lost += s["amount"]
    out["income_loss_2_months"] = dict(_risk(current + np.cumsum(f2, axis=1), limit, 120), income_lost=round(lost, 2))
    # before next payday
    t0 = pd.Timestamp(today)
    incomes = sorted([s for s in scheduled if s["amount"] > 0], key=lambda s: s["day_index"])
    biggest = max((s["amount"] for s in incomes), default=0)
    # "payday" = next main income (ignore small top-ups like weekly bar shifts)
    nxt = next((s for s in incomes if s["amount"] >= 0.4 * biggest), None)
    if nxt:
        i = nxt["day_index"]
        out["before_next_payday"] = {
            "next_income_date": nxt["date"], "next_income_from": nxt["merchant"], "next_income_amount": nxt["amount"],
            "prob_below_zero_before": round(float((base[:, :max(i, 1)] < 0).any(axis=1).mean()), 2),
            "expected_balance_day_before": round(float(np.percentile(base[:, max(i - 1, 0)], 50)), 2)}
    return out


def goal_plan(goal, f, customer, flows, current, limit):
    acct, profile = customer["account"], customer.get("profile", {})
    surplus = f["avg_monthly_surplus"]
    spend = max(f["avg_monthly_spending"], 1)
    cats = f["spending_by_category_monthly"]
    optional = {k: v for k, v in cats.items() if k in ("going_out", "eating_out", "shopping", "gifts", "subscriptions")}

    def months_to(target, have, per_month):
        if have >= target:
            return 0
        return None if per_month <= 0 else int(np.ceil((target - have) / per_month))

    def effect_of_saving(per_month):
        b = current + np.cumsum(flows + per_month / 30.4, axis=1)
        return round(float((b[:, :90] < 0).any(axis=1).mean()), 2), float(np.percentile(b[:, :90], 50, axis=0).min())

    if goal == "build_savings":
        target = round(3 * spend, -1)
        save = max(round(surplus * 0.5, -1), 25)
        m = months_to(target, acct["savings_balance"], save)
        return {"goal": "Build savings", "target": target, "target_label": "3 months of spending as an emergency fund",
                "current": acct["savings_balance"], "suggested_monthly": save, "months_to_target": m,
                "summary": f"Saving £{save:,.0f} a month gets you to £{target:,.0f} in {m} months." if m else
                           f"You already have 3 months of spending saved (£{target:,.0f})."}
    if goal == "buy_home":
        price = 230000  # placeholder first-time-buyer price; swap for regional ONS figure
        target = price * 0.10
        save = max(round(surplus * 0.6, -1), 50)
        lisa = profile.get("age_range") in ("18-24", "25-34")
        per = save * (1.25 if lisa else 1)
        m = months_to(target, acct["savings_balance"], per)
        return {"goal": "Buy a home", "target": target, "target_label": f"10% deposit on a £{price:,} home (placeholder price)",
                "current": acct["savings_balance"], "suggested_monthly": save, "months_to_target": m,
                "summary": (f"At £{save:,.0f} a month{' into a Lifetime ISA (25% government bonus)' if lisa else ''}, "
                            f"a £{target:,.0f} deposit takes about {m // 12} years {m % 12} months." if m else
                            "Your current surplus isn't enough to save for a deposit yet. Start with day-to-day costs.")}
    if goal == "pay_off_debt":
        repay = cats.get("debt_repayment", 0)
        return {"goal": "Pay off debt", "target": None, "target_label": "Lower debt repayments as a share of income",
                "current": repay, "suggested_monthly": None, "months_to_target": None,
                "summary": (f"Debt repayments are £{repay:,.0f} a month ({round(f['debt_to_income'] * 100)}% of income). "
                            + ("Pay the highest-interest debt first and talk to a free adviser before taking new credit."
                               if repay else "No regular debt repayments found in your account."))}
    if goal == "manage_expenses":
        top = sorted(optional.items(), key=lambda kv: -kv[1])[:2]
        cut = round(sum(v for _, v in top) * 0.2)
        (before, low_b), (after, low_a) = effect_of_saving(0), effect_of_saving(cut)
        names = " and ".join(k.replace("_", " ") for k, _ in top) or "non-essential spending"
        change = (f"changes your chance of going below £0 in 90 days from {round(before * 100)}% to {round(after * 100)}%"
                  if before - after >= 0.05 else f"lifts your lowest expected balance from {money(low_b)} to {money(low_a)}")
        return {"goal": "Manage monthly expenses", "target": cut, "target_label": f"Cut {names} by 20%",
                "current": round(sum(v for _, v in top)), "suggested_monthly": cut, "months_to_target": None,
                "what_if": {"prob_below_zero_90d_before": before, "prob_below_zero_90d_after": after,
                            "lowest_balance_before": round(low_b, 2), "lowest_balance_after": round(low_a, 2)},
                "summary": f"Cutting {names} by 20% frees £{cut:,} a month and {change}."}
    if goal == "retirement":
        if profile.get("retired"):
            runway = None if surplus >= 0 else round(acct["savings_balance"] / -surplus)
            return {"goal": "Retirement", "target": None, "target_label": "Make income last",
                    "current": acct["savings_balance"], "suggested_monthly": None, "months_to_target": runway,
                    "summary": "Your pension covers your spending each month." if surplus >= 0 else
                               f"You spend £{-surplus:,.0f} a month more than your pension; savings would last about {runway} months."}
        return {"goal": "Retirement", "target": None, "target_label": "Grow pension savings",
                "current": None, "suggested_monthly": round(max(surplus * 0.3, 0), -1), "months_to_target": None,
                "summary": "Check your workplace pension contribution. Raising it by 1% of pay usually gets matched by your employer."}
    return None


HEADLINE_FN = {
    "running_out": lambda st, f, cf: (
        f"There's a {round(st['before_next_payday']['prob_below_zero_before'] * 100)}% chance you go below £0 before your next payment "
        f"({st['before_next_payday']['next_income_from']}, {pd.Timestamp(st['before_next_payday']['next_income_date']).strftime('%d %b')})."
        if "before_next_payday" in st else "We couldn't find a regular payday in your account."),
    "unexpected_bills": lambda st, f, cf: (
        f"You could absorb a £500 surprise bill: your lowest expected balance would still be {money(st['surprise_bill_500']['lowest_expected_balance'])}."
        if st['surprise_bill_500']['prob_below_zero'] < 0.05 else
        f"A £500 surprise bill tomorrow would give you a {round(st['surprise_bill_500']['prob_beyond_overdraft'] * 100)}% chance of going past your overdraft limit "
        f"in the next 90 days (now {round(st['baseline']['prob_beyond_overdraft'] * 100)}%)."),
    "job_security": lambda st, f, cf: (
        f"If your pay stopped for 2 months from next month, your lowest expected balance would be {money(st['income_loss_2_months']['lowest_expected_balance'])}, "
        f"with a {round(st['income_loss_2_months']['prob_beyond_overdraft'] * 100)}% chance of going past your overdraft."),
    "debt": lambda st, f, cf: (
        f"Debt repayments take {round(f['debt_to_income'] * 100)}% of your income, and you're forecast to be in overdraft on "
        f"{round(cf['overdraft_share_90d'] * 100)}% of the next 90 days."),
    "not_saving": lambda st, f, cf: (
        f"At your current pace you'd {'add' if f['avg_monthly_surplus'] >= 0 else 'lose'} about £{abs(f['avg_monthly_surplus']) * 12:,.0f} "
        f"over the next 12 months."),
}


def data_checks(a, customer, f):
    out = []
    cash = customer["account"]["savings_balance"] + max(customer["account"]["current_balance"], 0)
    if a.get("shock_500") == "savings" and cash < 500:
        out.append(f"You said you'd use savings for a £500 bill, but you have £{cash:,.0f} available. "
                   "The forecast assumes it would come from your overdraft.")
    if a.get("shock_500") == "cannot_cover" and customer["account"]["savings_balance"] >= 500:
        out.append(f"You have £{customer['account']['savings_balance']:,.0f} in savings, which could cover a £500 bill.")
    if a.get("worry") == "debt" and f["debt_to_income"] == 0 and f["overdraft_days_pct_90d"] == 0:
        out.append("We didn't find debt repayments or overdraft use in this account. You may have debt elsewhere.")
    return out


PRIORITY = {
    "running_out": ["before_next_payday", "cashflow_forecast", "hardship_risk", "upcoming_expenses", "opportunities"],
    "unexpected_bills": ["surprise_bill_500", "upcoming_expenses", "cashflow_forecast", "hardship_risk", "opportunities"],
    "job_security": ["income_loss_2_months", "cashflow_forecast", "hardship_risk", "opportunities", "upcoming_expenses"],
    "debt": ["hardship_risk", "cashflow_forecast", "opportunities", "upcoming_expenses"],
    "not_saving": ["goal_plan", "opportunities", "cashflow_forecast", "upcoming_expenses"],
}
GOAL_OPPS = {"build_savings": ["emergency", "interest"], "buy_home": ["emergency", "interest"],
             "pay_off_debt": ["debt", "benefit"], "manage_expenses": ["subscriptions", "spread", "benefit"],
             "retirement": ["interest", "emergency"]}
