"""Advanced features on top of the core models.

1. action_planner   – greedy optimiser over the Monte Carlo simulation: finds the smallest set of changes
                      (cut a category, move a bill date, pause a subscription) that most reduces risk.
2. safe_to_spend    – daily allowance until next payday with an 80% chance of staying above £0.
3. backtest         – forecasts from 60/90/120 days ago, scored against what actually happened.
4. behaviour_signals– payday splurges, spending spikes, buy-now-pay-later, gambling (neutral, factual).
5. life_stage       – age/stage-specific suggestions (student, young adult, family, pre-retirement, retired).
6. support          – self-declared support preferences. Used ONLY for presentation and signposting,
                      never in any score (mental health is a protected characteristic).
"""
from datetime import date

import numpy as np
import pandas as pd

EVAL_DAYS = 120
OPTIONAL = {"going_out", "eating_out", "shopping", "gifts", "gambling"}

# ------------------------------------------------------------------ 1. action planner
def _objective(b, limit, spend):
    lo = b.min(axis=1)
    p_od = (lo < -limit).mean()
    p0 = (lo < 0).mean()
    days0 = (b < 0).sum(axis=1).mean() / b.shape[1]
    short = np.maximum(0, -lo - limit).mean() / max(spend, 1)
    return float(p_od + 0.3 * p0 + 0.5 * days0 + 0.5 * min(short, 2))


def _metrics(b, limit):
    return {"prob_past_overdraft": round(float((b.min(axis=1) < -limit).mean()), 2),
            "prob_below_zero": round(float((b.min(axis=1) < 0).mean()), 2),
            "expected_days_overdrawn": round(float((b < 0).sum(axis=1).mean()), 1),
            "lowest_expected_balance": round(float(np.percentile(b, 50, axis=0).min()), 2)}


def action_planner(flows, scheduled, current, limit, f, max_steps=5):
    H = EVAL_DAYS
    base = flows[:, :H]
    spend = max(f["avg_monthly_spending"], 1)
    cats = f["spending_by_category_monthly"]

    candidates = []  # (group, label, effort, delta[H])
    for cat, monthly in cats.items():
        if cat in OPTIONAL and monthly >= (5 if cat == "gambling" else 20):
            for p in (50, 100) if cat == "gambling" else (10, 20, 30, 50):
                d = np.full(H, monthly * p / 100 / 30.4)
                label = (f"Stop gambling spend (about £{monthly:,.0f} a month)" if p == 100 else
                         f"Spend {p}% less on {cat.replace('_', ' ')} (about £{monthly * p / 100:,.0f} a month)")
                candidates.append((f"cut:{cat}", label, min(p, 60) / 100, d, {"type": "cut", "category": cat, "pct": p, "monthly_saving": round(monthly * p / 100)}))
    bills = {}
    for s in scheduled:
        if s["amount"] < 0 and s["cadence"] == "monthly" and s["day_index"] < H:
            bills.setdefault(s["merchant"], []).append(s)
    # main monthly payday (salary / pension); bills are only moved to just after it
    pay = [s for s in scheduled if s["amount"] > 0 and s["cadence"] == "monthly"]
    payday = pd.Timestamp(max(pay, key=lambda s: s["amount"])["date"]).day if pay else None
    for m, occ in bills.items():
        day = pd.Timestamp(occ[0]["date"]).day
        if payday is None:
            break
        gap = (day - payday) % 30  # days from payday to this bill
        if gap <= 7:
            continue  # already soon after payday
        for k in ((payday + 1 - day) % 30 or 30,):
            d = np.zeros(H)
            for s in occ:
                i = s["day_index"]
                if i + k < H:
                    d[i] -= s["amount"]
                    d[i + k] += s["amount"]
            new_day = (pd.Timestamp(occ[0]["date"]) + pd.Timedelta(days=k)).day
            candidates.append((f"move:{m}", f"Ask {m} to move your £{abs(occ[0]['amount']):,.0f} payment from the {_ord(day)} to the {_ord(new_day)}",
                               0.1, d, {"type": "move_bill", "merchant": m, "from_day": day, "to_day": new_day}))
        if occ[0]["category"] == "subscriptions":
            d = np.zeros(H)
            for s in occ:
                d[s["day_index"]] -= s["amount"]
            candidates.append((f"pause:{m}", f"Pause {m} for a few months (£{abs(occ[0]['amount']):,.2f} a month)",
                               0.15, d, {"type": "pause", "merchant": m, "monthly_saving": round(abs(occ[0]["amount"]), 2)}))

    def bal(delta):
        return current + np.cumsum(base + delta, axis=1)

    chosen, delta = {}, np.zeros(H)
    before = _metrics(bal(delta), limit)
    obj = _objective(bal(delta), limit, spend)
    steps = []
    for _ in range(max_steps):
        best = None
        for g, label, effort, d, meta in candidates:
            if g in chosen and chosen[g][2] >= effort:
                continue
            nd = delta - (chosen[g][3] if g in chosen else 0) + d
            gain = obj - _objective(bal(nd), limit, spend)
            if gain > 0.01 and (best is None or gain / effort > best[0]):
                best = (gain / effort, g, (label, meta, effort, d), nd, gain)
        if not best:
            break
        _, g, (label, meta, effort, d), nd, gain = best
        chosen[g] = (label, meta, effort, d)
        delta = nd
        obj -= gain
        steps.append({"action": label, "detail": meta, "effort": "easy" if effort <= 0.15 else "moderate" if effort <= 0.2 else "harder",
                      "after": _metrics(bal(delta), limit)})
    # if an upgraded cut replaced an earlier step for the same category, keep only the latest
    seen, uniq = set(), []
    for s in reversed(steps):
        key = s["detail"].get("category") or s["detail"].get("merchant")
        if key not in seen:
            seen.add(key)
            uniq.append(s)
    after = _metrics(bal(delta), limit)
    return {"window_days": H, "before": before, "after": after, "steps": uniq[::-1],
            "method": "Greedy search over 1,000 simulated futures: each round adds the change with the biggest risk reduction per unit of effort."}


def _ord(n):
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


# ------------------------------------------------------------------ 2. safe to spend
def safe_to_spend(balances, scheduled, tx, today, limit=0):
    incomes = sorted([s for s in scheduled if s["amount"] > 0], key=lambda s: s["day_index"])
    if not incomes:
        return None
    biggest = max(s["amount"] for s in incomes)
    nxt = next(s for s in incomes if s["amount"] >= 0.4 * biggest)
    days = max(nxt["day_index"], 1)
    t0 = pd.Timestamp(today)
    recent = tx[(tx["date"] > t0 - pd.Timedelta(days=90)) & tx["kind"].isin(["variable", "optional"])]
    typical = float(-recent["amount"].sum() / 90)
    q20 = float(np.percentile(balances[:, :days].min(axis=1), 20))
    allowance = max(0.0, typical + q20 / days)
    within_od = max(0.0, typical + (q20 + limit) / days) if limit else None
    when = pd.Timestamp(nxt["date"]).strftime("%d %b")
    if allowance >= 3 * max(typical, 1):
        text = (f"You have plenty of room: your usual £{typical:,.0f} a day is well covered until {when}, "
                f"with an 80% chance of staying above £0.")
    elif allowance >= 1:
        text = (f"Spend up to £{allowance:,.0f} a day on everyday things until {when} and you have an 80% chance of staying above £0. "
                f"You usually spend £{typical:,.0f} a day.")
    elif within_od and within_od >= 1:
        text = (f"Staying above £0 until {when} isn't likely. To stay within your £{limit:,.0f} overdraft, keep everyday spending "
                f"under £{within_od:,.0f} a day (you usually spend £{typical:,.0f}).")
    else:
        text = (f"Your bills before {when} are more than the money available, even with very little everyday spending. "
                f"Talking to your bank or a free debt adviser now is the best next step.")
    return {"until": nxt["date"], "from": nxt["merchant"], "days": days, "typical_daily_spend": round(typical, 2),
            "safe_daily_spend": round(allowance, 2),
            "safe_daily_spend_within_overdraft": None if within_od is None else round(within_od, 2),
            "confidence": 0.8, "explanation": text}


# ------------------------------------------------------------------ 3. backtest
def backtest(tx, bal_hist, simulate_fn, cutoffs=(60, 90, 120), horizon=60):
    """Pretend it's N days ago, forecast, and compare with what actually happened."""
    today = bal_hist.index[-1]
    runs = []
    for back in cutoffs:
        cut = today - pd.Timedelta(days=back)
        if cut - pd.Timedelta(days=180) < bal_hist.index[0]:
            continue
        b, _, _, _ = simulate_fn(tx[tx["date"] <= cut], float(bal_hist[cut]), cut.date(), horizon=horizon, n=500, seed=7)
        actual = bal_hist[cut + pd.Timedelta(days=1): cut + pd.Timedelta(days=horizon)].to_numpy()
        h = len(actual)
        p10, p50, p90 = np.percentile(b[:, :h], [10, 50, 90], axis=0)
        flat = np.full(h, float(bal_hist[cut]))
        prev = bal_hist[cut - pd.Timedelta(days=horizon - 1): cut].to_numpy()
        seasonal = prev[:h] - prev[0] + float(bal_hist[cut])  # repeat last period's shape
        runs.append({"from": cut.date().isoformat(), "days": h,
                     "coverage_80": float(((actual >= p10) & (actual <= p90)).mean()),
                     "mae": float(np.abs(actual - p50).mean()),
                     "mae_flat": float(np.abs(actual - flat).mean()),
                     "mae_repeat": float(np.abs(actual - seasonal).mean())})
    if not runs:
        return None
    mae, flat, rep = (np.mean([r[k] for r in runs]) for k in ("mae", "mae_flat", "mae_repeat"))
    cov = np.mean([r["coverage_80"] for r in runs])
    return {"runs": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()} for r in runs],
            "avg_error": round(float(mae), 2), "avg_error_flat_guess": round(float(flat), 2),
            "avg_error_repeat_last_period": round(float(rep), 2),
            "improvement_vs_best_simple_guess_pct": round(float((1 - mae / min(flat, rep)) * 100)),
            "range_coverage": round(float(cov), 2),
            "summary": (f"Tested on {len(runs)} past periods: average error £{mae:,.0f} vs £{min(flat, rep):,.0f} for the best simple guess "
                        f"({round((1 - mae / min(flat, rep)) * 100)}% better). The 80% range contained the real balance {round(cov * 100)}% of the time."),
            "note": "Measured on the demo data, which is synthetic."}


# ------------------------------------------------------------------ 4. behaviour signals
GAMBLING = r"bet365|betfair|paddy ?power|william hill|ladbrokes|sky ?bet|betway|casino|lottery|pokerstars"
BNPL = r"klarna|clearpay|laybuy|paypal pay in 3|zilch"


def behaviour_signals(tx, today):
    t0 = pd.Timestamp(today)
    out = []
    last180 = tx[tx["date"] > t0 - pd.Timedelta(days=180)]
    disc = last180[last180["kind"] == "optional"]
    daily = (-disc.groupby(disc["date"].dt.normalize())["amount"].sum()).reindex(
        pd.date_range(t0 - pd.Timedelta(days=179), t0), fill_value=0.0)

    # payday splurge: optional spending in the 3 days after main income vs a typical 3 days
    inc = tx[tx["kind"] == "income"]
    if len(inc):
        big = inc[inc["amount"] >= 0.4 * inc["amount"].max()]["date"].dt.normalize().unique()
        post = [daily[d: d + pd.Timedelta(days=2)].sum() for d in big if d in daily.index]
        if post:
            typical3 = daily.mean() * 3 or 1
            ratio = float(np.mean(post) / typical3)
            if ratio >= 1.5:
                out.append({"signal": "payday_splurge", "severity": "watch", "value": round(ratio, 1),
                            "text": f"In the 3 days after money comes in, you spend about {ratio:.1f}× your usual on non-essentials."})
    # spending spikes: robust outliers (median + 5 × MAD)
    med = float(daily.median())
    mad = float((daily - med).abs().median()) or 5.0
    spikes = daily[(daily > med + 5 * mad) & (daily > 60)]
    if len(spikes) >= 2:
        out.append({"signal": "spending_spikes", "severity": "info", "value": int(len(spikes)),
                    "text": f"{len(spikes)} days in the last 6 months had unusually high non-essential spending (£{spikes.sum():,.0f} in total)."})
    # buy now pay later
    bnpl = last180[last180["merchant"].str.lower().str.contains(BNPL, regex=True)]
    if len(bnpl):
        out.append({"signal": "buy_now_pay_later", "severity": "watch", "value": round(float(-bnpl["amount"].sum() / 6)),
                    "text": f"You're paying about £{-bnpl['amount'].sum() / 6:,.0f} a month to buy-now-pay-later providers. These count as debt."})
    # gambling
    g = last180[last180["merchant"].str.lower().str.contains(GAMBLING, regex=True) | (last180["category"] == "gambling")]
    if len(g):
        monthly = float(-g["amount"].sum() / 6)
        out.append({"signal": "gambling", "severity": "watch", "value": round(monthly),
                    "text": f"About £{monthly:,.0f} a month goes to gambling sites. If you'd like, there are free tools that can help you stay in control."})
    # subscriptions count
    subs = tx[(tx["date"] > t0 - pd.Timedelta(days=60)) & (tx["category"] == "subscriptions")]["merchant"].nunique()
    if subs >= 3:
        out.append({"signal": "subscriptions", "severity": "info", "value": int(subs),
                    "text": f"You have {subs} active subscriptions."})
    return out


# ------------------------------------------------------------------ 5. life stage
def life_stage(profile):
    age = profile.get("age_range", "")
    if profile.get("student"):
        stage = "student"
    elif profile.get("retired") or age == "65+":
        stage = "retired"
    elif profile.get("dependants", 0):
        stage = "family"
    elif age in ("50-64",):
        stage = "pre_retirement"
    else:
        stage = "young_adult" if age in ("18-24", "25-34") else "working_age"
    tips = {
        "student": ["Check when your interest-free student overdraft ends after graduation, and plan to clear it before then.",
                    "Treat each loan payment as money for the whole term: divide it by the weeks until the next one."],
        "young_adult": ["If you're under 40, a Lifetime ISA adds a 25% government bonus on savings for a first home or retirement.",
                        "Build one month of spending as a buffer before saving for bigger goals."],
        "family": ["Check you're claiming Child Benefit and, if you work, Tax-Free Childcare.",
                   "Aim for a bigger buffer than average: families face more surprise costs."],
        "working_age": ["Check your workplace pension contribution and whether your employer matches more.",
                        "Keep three months of spending as an emergency fund."],
        "pre_retirement": ["From 50 you can get free, impartial pension guidance from Pension Wise (MoneyHelper).",
                           "Check your State Pension forecast on GOV.UK to see if you have gaps to fill."],
        "retired": ["Check whether you could get Pension Credit: many eligible people don't claim it, and it unlocks other help.",
                    "Keep easy-access savings for bills, and compare rates on larger savings."],
    }[stage]
    return {"stage": stage, "tips": tips}


# ------------------------------------------------------------------ 6. support preferences
SUPPORT_KEYS = {"money makes me anxious": "anxious", "i prefer simple explanations": "simple",
                "i struggle with impulse spending": "impulse", "i want help with gambling": "gambling",
                "i find it hard to keep track of bills": "tracking"}
SUPPORT = {
    "anxious": {"label": "Money makes me anxious",
                "how_we_help": "We lead with what's going well, show one thing at a time, and avoid alarming language.",
                "resources": ["Money and Mental Health Policy Institute: practical guides on managing money and mental health",
                              "Mind: mental health information and support",
                              "You can ask your bank to record that you'd like extra support"]},
    "simple": {"label": "I prefer simple explanations", "how_we_help": "Short sentences, fewer numbers, no jargon.", "resources": []},
    "impulse": {"label": "I struggle with impulse spending",
                "how_we_help": "We show your safe-to-spend amount and flag spending bursts after payday.",
                "resources": ["Try a 48-hour wait before non-essential buys over £30",
                              "Move fun money into a separate pot on payday, so the main account only covers bills",
                              "Remove saved cards from shopping apps"]},
    "gambling": {"label": "I want help with gambling",
                 "how_we_help": "We show your gambling spend clearly and point you to free tools.",
                 "resources": ["GamCare: free, confidential support for anyone affected by gambling",
                               "GAMSTOP: free self-exclusion from UK online gambling sites",
                               "Turn on your bank's gambling block, if your bank offers one"]},
    "tracking": {"label": "I find it hard to keep track of bills",
                 "how_we_help": "We list every bill for the next 30 days with the date and your expected balance after it.",
                 "resources": ["Ask providers to move payment dates to just after payday (see your action plan)"]},
}


def normalise_support(values):
    out = []
    for v in values or []:
        k = SUPPORT_KEYS.get(str(v).strip().lower().replace("’", "'"), str(v).strip().lower())
        if k in SUPPORT and k not in out:
            out.append(k)
    return out


def support_plan(needs, signals):
    sig = {s["signal"] for s in signals}
    keys = list(needs)
    if "gambling" in sig and "gambling" not in keys:
        keys.append("gambling")  # offered gently because spending was detected; never scored
    return {"needs": needs, "items": [dict(key=k, **SUPPORT[k], offered_because="you asked" if k in needs else "we noticed gambling payments")
                                      for k in keys],
            "privacy": "Support preferences only change how information is shown. They are never used in any score or shared."}


def bill_calendar(scheduled, balances, days=30):
    p50 = np.percentile(balances, 50, axis=0)
    rows = [{"date": s["date"], "who": s["merchant"], "amount": s["amount"],
             "balance_after": round(float(p50[s["day_index"]]), 2)}
            for s in sorted(scheduled, key=lambda s: s["day_index"]) if s["day_index"] < days]
    return rows
