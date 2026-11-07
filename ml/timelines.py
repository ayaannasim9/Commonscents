"""Build the Overview app's three 5-year timelines (A stay the same, B worst case, C best realistic)
from the ML engine's output. Shape matches Overview/app.js TimeTravelEngine.getTimelines()."""
import numpy as np
import pandas as pd


def _gbp(v):
    return ("−" if v < 0 else "") + f"£{abs(v):,.0f}"


def build(r):
    c, acct, f = r["customer"], r["account"], r["features"]
    cf, hr, st, adv = r["cashflow_forecast"], r["hardship_risk"], r["stress_tests"], r.get("advanced", {})
    s = cf["series"]
    cur0, sav0 = acct["current_balance"], acct["savings_balance"]
    start = round(cur0 + sav0)
    inc, out = round(f["avg_monthly_income"]), round(f["avg_monthly_spending"])
    sav_monthly = max(0, round(f["savings_change_6m"] / 6))

    # Year 1 comes from the simulation (incl. life changes). Years 2-5 continue the customer's usual
    # monthly surplus/deficit plus any ongoing life-change costs (one-off effects are not repeated).
    import personalise as P
    ongoing = sum(P.LIFE_EVENTS[k]["monthly"] * 12 for k in r.get("answers", {}).get("life_changes", []) if k in P.LIFE_EVENTS)
    later = 12 * f["avg_monthly_surplus"] + ongoing
    spread = s["p50"][-1] - s["p10"][-1]

    def path(y1, per_year):
        return [start] + [round(start + y1 + per_year * (k - 1)) for k in range(1, 6)]

    # A: most likely
    y1_a = s["p50"][-1] - cur0
    pts_a = path(y1_a, later)
    drift_a = later
    # B: bad case (1 in 10 futures) plus a £500 surprise bill every year
    pts_b = path(s["p10"][-1] - cur0 - 500, later - spread - 500)
    # C: most likely path + the action plan's monthly savings + savings interest opportunities
    plan = adv.get("action_plan", {})
    plan_monthly = sum(x["detail"].get("monthly_saving", 0) for x in plan.get("steps", []))
    interest = sum(o.get("estimated_benefit_annual") or 0 for o in r["opportunities"] if "interest" in o["opportunity"].lower())
    pts_c = path(y1_a + 12 * plan_monthly + interest, later + 12 * plan_monthly + interest)

    def end(pts5, sav, debt=0, extra_out=0, sv=0):
        return {"cur": round(pts5 - sav + debt), "sav": round(max(sav, 0)), "inv": 0, "debt": round(debt),
                "in": inc, "out": out + extra_out, "sv": sv, "iv": 0}

    sav_a = max(0, sav0 + f["savings_change_6m"] * 2 * 5) if f["savings_change_6m"] < 0 else sav0 + sav_monthly * 60
    debt_b = max(0, -pts_b[5] - acct["overdraft_limit"])
    sav_c = sav0 + 12 * 5 * plan_monthly

    pay = st.get("before_next_payday", {})
    up = r["upcoming_expenses"]
    drivers = hr.get("drivers", [])
    life = cf.get("life_changes", [])
    sts = adv.get("safe_to_spend") or {}

    ms_a = []
    if pay:
        ms_a.append(["1 month", "💷", f"Next money in: {_gbp(pay['next_income_amount'])} on {pd.Timestamp(pay['next_income_date']).strftime('%d %b')}",
                     f"The day before it arrives, your balance is expected to be about {_gbp(pay['expected_balance_day_before'])}. {sts.get('explanation', '')}".strip()])
    if drivers:
        ms_a.append(["3 months", "📉", drivers[0]["detail"], "This is the biggest factor in your risk score right now."])
    if up:
        e = next((x for x in up if x.get("merchant")), up[0])
        ms_a.append(["1 year", "📅", f"{e['type']}: {_gbp(e['expected_cost_low'])}–{_gbp(e['expected_cost_high'])}", f"{e['timeframe']}. {e['why']}."])
    for l in life:
        ms_a.append([pd.Timestamp(l["date"]).strftime("%b %Y"), "🧭", l["change"], f"{l['effect']}. {l['assumption']}."])
    ms_a.append(["5 years", "🔮", f"About {_gbp(pts_a[5])} in total", f"If nothing changes, your accounts would go from {_gbp(start)} to about {_gbp(pts_a[5])}."])

    il = st["income_loss_2_months"]
    ms_b = [["1 year", "⛈️", "If your pay stopped for 2 months",
             f"Your lowest expected balance would be {_gbp(il['lowest_expected_balance'])}, with a {round(il['prob_beyond_overdraft'] * 100)}% chance of going past your overdraft."],
            ["Any time", "🧾", "A £500 surprise bill",
             f"Your lowest expected balance would fall to {_gbp(st['surprise_bill_500']['lowest_expected_balance'])}."],
            ["5 years", "🛡️", "A risk check, not a prediction",
             "Free help from StepChange, MoneyHelper or Citizens Advice is available before things get that far."]]

    ms_c = [[f"Step {i + 1}", "✅", x["action"], f"Effort: {x['effort']}. After this step your lowest expected balance would be {_gbp(x['after']['lowest_expected_balance'])}."]
            for i, x in enumerate(plan.get("steps", [])[:3])]
    for o in r["opportunities"][:1]:
        ms_c.append([f"Step {len(ms_c) + 1}", "💡", o["opportunity"], f"{o['action']}. {o['why']}."])
    ms_c.append(["5 years", "🎉", f"About {_gbp(pts_c[5] - pts_a[5])} better off", f"Compared with changing nothing, following the plan leaves you with about {_gbp(pts_c[5])}."])

    acts, prev_low = [], plan.get("before", {}).get("lowest_expected_balance", 0)
    for x in plan.get("steps", [])[:3]:
        d = x["detail"]
        gain = x["after"]["lowest_expected_balance"] - prev_low
        prev_low = x["after"]["lowest_expected_balance"]
        worth = (f"Saves £{d['monthly_saving'] * 12:,.0f} a year" if d.get("monthly_saving")
                 else f"Your lowest balance ends up £{gain:,.0f} better" if gain >= 1
                 else f"About {round(plan['before']['expected_days_overdrawn'] - x['after']['expected_days_overdrawn'])} fewer days overdrawn")
        acts.append(["✂️" if d["type"] == "cut" else "📅" if d["type"] == "move_bill" else "⏸️", x["action"], worth,
                     f"Tested in 1,000 simulated futures. Effort: {x['effort']}.", "Add to my plan"])
    for o in r["opportunities"][:1]:
        acts.append(["🧭", o["opportunity"], f"£{o['estimated_benefit_annual']:,} a year" if o.get("estimated_benefit_annual") else "Could help a lot",
                     o["why"] + ".", "See help you can get", "support"])

    return {
        "person": {"name": c["name"], "persona": c["persona"],
                   "now": {"cur": round(cur0), "sav": round(sav0), "inv": 0, "debt": 0, "in": inc, "out": out, "sv": sav_monthly, "iv": 0}},
        "timelines": {
            "A": {"name": "Stay the same", "icon": "➡️", "c": "#007a78", "sub": "What happens if nothing changes?", "pts": pts_a,
                  "why": "Year 1 is the most likely path from 1,000 simulated futures of your account. Later years continue your usual monthly pattern.",
                  "end": end(pts_a[5], sav_a, sv=sav_monthly), "ms": ms_a},
            "B": {"name": "Worst case", "icon": "⛈️", "c": "#b0123a", "sub": "A risk check, not a prediction. Knowing helps you prepare.", "pts": pts_b,
                  "why": "Uses the bad-case end of the simulation (1 in 10 futures) plus a £500 surprise bill each year.",
                  "end": end(pts_b[5], 0, debt=debt_b, extra_out=round(500 / 12)), "ms": ms_b},
            "C": {"name": "Best realistic", "icon": "🌱", "c": "#0b6b3a", "sub": "If you follow your action plan.", "pts": pts_c,
                  "why": "Adds the savings from your optimised action plan and better savings rates to the most likely path.",
                  "end": end(pts_c[5], sav_c, sv=sav_monthly + round(plan_monthly)), "ms": ms_c},
        },
        "actions": acts,
        "report_url": f"/customers/{c['id']}/report",
    }
