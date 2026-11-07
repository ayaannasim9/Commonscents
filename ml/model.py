"""Common Cents - ML engine.

analyse(customer, transactions_df) -> dict with:
  Model 1  cashflow_forecast   Monte Carlo balance forecast (7/30/90/180 days, range + confidence)
  Model 2  hardship_risk       risk score, confidence, top drivers, "what if" buffer
  Model 3  upcoming_expenses   annual bills, seasonal spikes
  Model 4  opportunities       savings / efficiency suggestions
Only items with confidence >= CONFIDENCE_THRESHOLD are returned (Safety & Ethics section).
Protected characteristics are never used: only transactions and account balances go in.
"""
from datetime import date, timedelta

import numpy as np
import pandas as pd

import personalise as P
import advanced as A

HORIZONS = [7, 30, 90, 180, 365]
SIM_DAYS = 365
N_SIMS = 1000
CONFIDENCE_THRESHOLD = 0.60

# External data (Section 2). PLACEHOLDER values for the demo: replace with ONS CPI,
# Bank of England base rate and Ofgem price cap figures before claiming accuracy.
ASSUMPTIONS = {
    "cpi_annual": 0.035,
    "food_inflation_annual": 0.04,
    "energy_inflation_annual": 0.05,
    "insurance_inflation_annual": 0.08,
    "best_easy_access_savings_rate": 0.045,
    # Seasonal multipliers for day-to-day spending (Christmas, summer travel, January squeeze)
    "seasonal_prior": {1: 0.9, 2: 0.95, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0, 7: 1.08, 8: 1.08,
                       9: 1.02, 10: 1.0, 11: 1.03, 12: 1.3},
}

INCOME_KINDS = {"income"}
DAY_TO_DAY_KINDS = {"variable", "optional"}
ANNUAL_INFLATION = {"insurance": "insurance_inflation_annual", "utilities": "energy_inflation_annual"}
EXPENSE_LABELS = {"insurance": "Insurance renewal", "vehicle": "Vehicle maintenance", "education": "Education costs",
                  "subscriptions": "Annual subscription", "transport": "Travel pass", "student_finance": "Student loan payment"}


# ------------------------------------------------------------------ helpers
def _prep(tx):
    tx = tx.copy()
    tx["date"] = pd.to_datetime(tx["date"])
    return tx.sort_values("date")


def _balance_history(tx, current_balance, today):
    """Reconstruct end-of-day balances from the current balance backwards."""
    daily = tx.groupby(tx["date"].dt.normalize())["amount"].sum()
    idx = pd.date_range(tx["date"].min().normalize(), pd.Timestamp(today))
    daily = daily.reindex(idx, fill_value=0.0)
    after = daily[::-1].cumsum()[::-1].shift(-1, fill_value=0.0)  # flows after each day
    return current_balance - after


def _sigmoid(z):
    return 1 / (1 + np.exp(-z))


# ------------------------------------------------------------------ recurring detection
def detect_recurring(tx, today):
    """Find regular income and bills from cadence. Returns list of streams."""
    streams = []
    for merchant, g in tx[~tx["kind"].isin(DAY_TO_DAY_KINDS)].groupby("merchant"):
        g = g.sort_values("date")
        dates, amts = g["date"].tolist(), g["amount"].to_numpy()
        cat, kind = g["category"].iloc[0], g["kind"].iloc[0]
        gaps = np.diff([d.toordinal() for d in dates]) if len(dates) > 1 else np.array([])
        med = float(np.median(gaps)) if len(gaps) else 999
        dom_std = float(np.std([d.day for d in dates]))

        if len(dates) >= 3 and 6 <= med <= 8:
            cadence = "weekly"
        elif len(dates) >= 3 and 12 <= med <= 17:
            cadence = "every_n_days"  # fortnightly / buy-now-pay-later instalments
        elif len(dates) >= 3 and 26 <= med <= 32:
            cadence = "monthly" if dom_std <= 1.5 else "every_n_days"
        else:
            cadence = "annual"  # irregular / yearly: repeat on the same dates next year

        if cadence != "annual":
            gap = {"weekly": 7, "monthly": 30.4}.get(cadence, med)
            if (pd.Timestamp(today) - dates[-1]).days > 2.5 * gap:
                continue  # stream has stopped
            recent = amts[-6:]
            trend = 0.0
            if cat == "utilities" and len(recent) >= 4:
                trend = float(np.polyfit(np.arange(len(recent)), recent, 1)[0])  # £ change per payment
            streams.append({"merchant": merchant, "category": cat, "kind": kind, "cadence": cadence,
                            "gap_days": med, "day_of_month": int(np.median([d.day for d in dates])),
                            "last_date": dates[-1], "amount": float(np.median(amts[-3:])),
                            "amount_sd": float(np.std(recent)) if len(recent) > 1 else 0.0,
                            "recent_amounts": recent, "trend_per_payment": trend})
        else:
            streams.append({"merchant": merchant, "category": cat, "kind": kind, "cadence": "annual",
                            "occurrences": list(zip(dates, amts))})
    return streams


def _project_stream(s, today, horizon):
    """Yield (day_index, base_amount, sd, sample_pool) for each future occurrence."""
    t0 = pd.Timestamp(today)
    end = t0 + pd.Timedelta(days=horizon)
    if s["cadence"] == "annual":
        infl = ASSUMPTIONS.get(ANNUAL_INFLATION.get(s["category"], "cpi_annual"))
        used = []
        for d, a in sorted(s["occurrences"], key=lambda x: x[0], reverse=True):  # newest first
            nd = d + pd.DateOffset(years=1)
            while nd <= t0:
                nd += pd.DateOffset(years=1)
            if any(abs((nd - u).days) < 45 for u in used):
                continue  # same yearly payment already projected from a more recent year
            used.append(nd)
            if t0 < nd <= end:
                yield (nd - t0).days - 1, a * (1 + infl if a < 0 else 1), abs(a) * 0.08, None, nd
        return
    if s["cadence"] == "monthly":
        nd = s["last_date"] + pd.DateOffset(months=1)
        dates = []
        while nd <= end:
            if nd > t0:
                dates.append(nd)
            nd += pd.DateOffset(months=1)
    else:
        step = 7 if s["cadence"] == "weekly" else int(round(s["gap_days"]))
        nd, dates = s["last_date"] + pd.Timedelta(days=step), []
        while nd <= end:
            if nd > t0:
                dates.append(nd)
            nd += pd.Timedelta(days=step)
    pool = s["recent_amounts"] if (s["kind"] == "income" and s["amount_sd"] > 0.1 * abs(s["amount"])) else None
    for k, d in enumerate(dates, start=1):
        base = s["amount"] + s["trend_per_payment"] * k
        if s["category"] == "utilities":  # winter uplift learned from own history is in the trend; add seasonal shape
            base = base * (1.0 if d.month not in (11, 12, 1, 2, 3) else 1.0)
        yield (d - t0).days - 1, base, max(s["amount_sd"], abs(base) * 0.03), pool, d


# ------------------------------------------------------------------ Model 1: cashflow forecast
def _seasonal_factors(tx):
    """Month multipliers for day-to-day spend: own history blended 50/50 with the external prior."""
    dd = tx[tx["kind"].isin(DAY_TO_DAY_KINDS)]
    daily = dd.groupby(dd["date"].dt.normalize())["amount"].sum().abs()
    idx = pd.date_range(tx["date"].min().normalize(), tx["date"].max().normalize())
    daily = daily.reindex(idx, fill_value=0.0)
    by_month = daily.groupby(daily.index.month).mean()
    overall = daily.mean() or 1.0
    f = {}
    for m in range(1, 13):
        prior = ASSUMPTIONS["seasonal_prior"][m]
        f[m] = 0.5 * (by_month[m] / overall) + 0.5 * prior if m in by_month.index else prior
    return f, daily


def simulate(tx, current_balance, today, horizon=SIM_DAYS, n=N_SIMS, seed=0):
    rng = np.random.default_rng(seed)
    flows = np.zeros((n, horizon))
    t0 = pd.Timestamp(today)

    # scheduled income and bills
    streams = detect_recurring(tx, today)
    scheduled = []
    for s in streams:
        for i, base, sd, pool, d in _project_stream(s, today, horizon):
            if pool is not None:
                vals = rng.choice(pool, n)
            else:
                vals = base + rng.normal(0, sd, n)
            flows[:, i] += vals
            scheduled.append({"date": d.date().isoformat(), "merchant": s["merchant"], "category": s["category"],
                              "amount": round(float(base), 2), "cadence": s["cadence"], "day_index": i, "_vals": vals})

    # day-to-day spending: bootstrap historical days of the same weekday, de-seasonalised then re-seasonalised
    factors, daily = _seasonal_factors(tx)
    recent = daily[daily.index > t0 - pd.Timedelta(days=182)]
    pools = {w: (recent[recent.index.weekday == w] / np.array([factors[m] for m in recent[recent.index.weekday == w].index.month])).to_numpy()
             for w in range(7)}
    food = ASSUMPTIONS["food_inflation_annual"]
    for i in range(horizon):
        d = t0 + pd.Timedelta(days=i + 1)
        flows[:, i] -= rng.choice(pools[d.weekday()], n) * factors[d.month] * (1 + food) ** ((i + 1) / 365)

    balances = current_balance + np.cumsum(flows, axis=1)
    return balances, flows, scheduled, factors


def cashflow_forecast(balances, today, monthly_outgoings, history_months):
    t0 = pd.Timestamp(today)
    p10, p50, p90 = np.percentile(balances, [10, 50, 90], axis=0)
    hist_factor = min(1.0, history_months / 12)
    horizons = []
    for h in HORIZONS:
        i = h - 1
        spread = p90[i] - p10[i]
        conf = float(np.clip(0.97 * np.exp(-spread / (4 * monthly_outgoings)) * (0.7 + 0.3 * hist_factor), 0.05, 0.97))
        horizons.append({"days": h, "date": (t0 + pd.Timedelta(days=h)).date().isoformat(),
                         "predicted_balance": round(float(p50[i]), 2),
                         "range_low": round(float(p10[i]), 2), "range_high": round(float(p90[i]), 2),
                         "confidence": round(conf, 2)})
    below = balances < 0
    first_neg = np.where(below.any(axis=1), below.argmax(axis=1) + 1, np.inf)
    med = float(np.median(first_neg))
    return {
        "horizons": horizons,
        "series": {"dates": [(t0 + pd.Timedelta(days=i + 1)).date().isoformat() for i in range(balances.shape[1])],
                   "p10": np.round(p10, 2).tolist(), "p50": np.round(p50, 2).tolist(), "p90": np.round(p90, 2).tolist()},
        "depletion": {
            "median_days_until_below_zero": None if np.isinf(med) else int(med),
            "date": None if np.isinf(med) else (t0 + pd.Timedelta(days=int(med))).date().isoformat(),
            "prob_below_zero_30d": round(float(below[:, :30].any(axis=1).mean()), 2),
            "prob_below_zero_90d": round(float(below[:, :90].any(axis=1).mean()), 2),
        },
    }


# ------------------------------------------------------------------ features (Section 3)
def build_features(tx, customer, bal_hist, today):
    t0 = pd.Timestamp(today)
    acct = customer["account"]
    month = tx["date"].dt.to_period("M")
    full = tx[month < t0.to_period("M")]  # complete months only
    fm = full["date"].dt.to_period("M")
    income_m = full[full["kind"] == "income"].groupby(fm)["amount"].sum()
    spend_m = -full[full["amount"] < 0].loc[lambda d: d["kind"] != "transfer"].groupby(fm)["amount"].sum()
    months = sorted(set(fm))
    income_m = income_m.reindex(months, fill_value=0)
    spend_m = spend_m.reindex(months, fill_value=0)
    last6, prev6 = months[-6:], months[-12:-6]

    def avg(series, ms):
        return float(series.reindex(ms, fill_value=0).mean()) if ms else 0.0

    inc6, spd6 = avg(income_m, last6), avg(spend_m, last6)
    util = -full[full["category"] == "utilities"].groupby(fm)["amount"].sum()
    util_growth = None
    if len(util) >= 12:
        util_growth = (util.iloc[-3:].mean() / max(util.iloc[-15:-12].mean() if len(util) >= 15 else util.iloc[-12:-9].mean(), 1)) - 1
    fixed = -full[full["kind"] == "fixed"].groupby(fm)["amount"].sum().reindex(months, fill_value=0)
    nonessential = -full[full["kind"] == "optional"]["amount"].sum() / max(spend_m.sum(), 1)

    sav = pd.Series({p["month"]: p["balance"] for p in customer["savings_history"]})
    sav_6m_ago = sav.iloc[-7] if len(sav) >= 7 else sav.iloc[0]
    od_recent = float((bal_hist[bal_hist.index > t0 - pd.Timedelta(days=90)] < 0).mean())
    od_prior = float((bal_hist[(bal_hist.index <= t0 - pd.Timedelta(days=90)) & (bal_hist.index > t0 - pd.Timedelta(days=180))] < 0).mean())
    debt = -full[full["category"] == "debt_repayment"].groupby(fm)["amount"].sum()

    return {
        "history_months": len(months),
        "avg_monthly_income": round(inc6, 2),
        "avg_monthly_spending": round(spd6, 2),
        "avg_monthly_surplus": round(inc6 - spd6, 2),
        "savings_rate": round((inc6 - spd6) / inc6, 3) if inc6 else 0.0,
        "income_change_pct": round(inc6 / avg(income_m, prev6) - 1, 3) if avg(income_m, prev6) else 0.0,
        "income_volatility": round(float(income_m.iloc[-12:].std() / max(income_m.iloc[-12:].mean(), 1)), 3),
        "fixed_cost_change_pct": round(avg(fixed, last6) / avg(fixed, prev6) - 1, 3) if avg(fixed, prev6) else 0.0,
        "utility_cost_change_pct": None if util_growth is None else round(float(util_growth), 3),
        "non_essential_spend_pct": round(float(nonessential), 3),
        "savings_balance": acct["savings_balance"],
        "savings_change_6m": round(float(sav.iloc[-1] - sav_6m_ago), 2),
        "savings_change_6m_pct": round(float((sav.iloc[-1] - sav_6m_ago) / max(sav_6m_ago, 1)), 3),
        "emergency_fund_months": round((acct["savings_balance"] + max(acct["current_balance"], 0)) / max(spd6, 1), 2),
        "overdraft_days_pct_90d": round(od_recent, 3),
        "overdraft_days_pct_prev_90d": round(od_prior, 3),
        "debt_to_income": round(float(debt.iloc[-6:].mean()) / inc6, 3) if len(debt) and inc6 else 0.0,
        "spending_by_category_monthly": {k: round(v, 2) for k, v in
                                         (-full[(full["amount"] < 0) & (full["kind"] != "transfer")]
                                          .groupby("category")["amount"].sum() / len(months)).sort_values(ascending=False).items()},
    }


# ------------------------------------------------------------------ Model 2: hardship risk
# Transparent weighted logistic model. Weights are hand-set (no labelled hardship data at a hackathon);
# each term is a driver we can explain to the customer.
def _hardship_terms(f, p_neg90, p_over90):
    util = f["utility_cost_change_pct"] or 0.0
    return [
        ("forecast_beyond_overdraft", 3.0 * p_over90, f"{round(p_over90 * 100)}% chance you go past your overdraft limit in the next 90 days"),
        ("forecast_below_zero", 1.2 * p_neg90, f"{round(p_neg90 * 100)}% chance your balance goes below £0 in the next 90 days"),
        ("overdraft_rising", 2.5 * max(0, f["overdraft_days_pct_90d"] - f["overdraft_days_pct_prev_90d"]) + 1.0 * f["overdraft_days_pct_90d"],
         f"In overdraft on {round(f['overdraft_days_pct_90d'] * 100)}% of days in the last 3 months (was {round(f['overdraft_days_pct_prev_90d'] * 100)}%)"),
        ("savings_declining", 1.5 * min(1, max(0, -f["savings_change_6m_pct"])),
         f"Savings fell by £{abs(f['savings_change_6m']):,.0f} in 6 months"),
        ("income_falling", 3.0 * max(0, -f["income_change_pct"]),
         f"Income is {abs(round(f['income_change_pct'] * 100))}% lower than the previous 6 months"),
        ("costs_rising", 2.0 * max(0, util) + 2.0 * max(0, f["fixed_cost_change_pct"]),
         f"Utility costs up {round(util * 100)}% on last year" if util > 0.05 else f"Bills up {round(f['fixed_cost_change_pct'] * 100)}% on 6 months ago"),
        ("spending_exceeds_income", 2.0 * max(0, -f["savings_rate"]),
         f"Spending is £{abs(f['avg_monthly_surplus']):,.0f} a month more than income"),
        ("thin_buffer", 1.0 * max(0, 1 - f["emergency_fund_months"]),
         f"Savings would cover {f['emergency_fund_months']} months of spending"),
    ]


def hardship_risk(f, balances, overdraft_limit, extra_terms=()):
    def probs(b):
        return float((b[:, :90] < 0).any(axis=1).mean()), float((b[:, :90] < -overdraft_limit).any(axis=1).mean())

    p_neg90, p_over90 = probs(balances)
    terms = _hardship_terms(f, p_neg90, p_over90) + list(extra_terms)
    score = float(_sigmoid(-2.5 + sum(t[1] for t in terms)))
    drivers = [{"factor": k, "detail": txt, "weight": round(v, 2)} for k, v, txt in sorted(terms, key=lambda t: -t[1]) if v >= 0.15][:3]

    # Resilience what-if: £200 more in the emergency buffer
    f_buf = dict(f, emergency_fund_months=f["emergency_fund_months"] + 200 / max(f["avg_monthly_spending"], 1))
    score_buf = float(_sigmoid(-2.5 + sum(t[1] for t in _hardship_terms(f_buf, *probs(balances + 200)) + list(extra_terms))))

    conf = round(min(0.9, 0.5 + f["history_months"] / 40), 2)
    level = "high" if score >= 0.6 else "medium" if score >= 0.3 else "low"
    return {"score": round(score, 2), "level": level, "confidence": conf, "drivers": drivers,
            "what_if": {"extra_buffer": 200, "new_score": round(score_buf, 2),
                        "risk_reduction_pct": round((score - score_buf) / score * 100) if score > 0 else 0}}


# ------------------------------------------------------------------ Model 3: future expenses
def upcoming_expenses(tx, scheduled, factors, today, f):
    t0 = pd.Timestamp(today)
    out = []
    # annual / irregular bills seen in history, repeated next year
    for s in scheduled:
        if s["cadence"] != "annual" or s["amount"] >= 0:
            continue
        hist = tx[tx["merchant"] == s["merchant"]]["amount"].abs()
        lo, hi = abs(s["amount"]) * 0.92, abs(s["amount"]) * 1.12
        seen = len(hist)
        out.append({"type": EXPENSE_LABELS.get(s["category"], s["category"].replace("_", " ").title()),
                    "merchant": s["merchant"], "expected_cost_low": round(lo), "expected_cost_high": round(hi),
                    "expected_date": s["date"],
                    "timeframe": f"{(pd.Timestamp(s['date']) - pd.Timedelta(days=14)).strftime('%d %b')} – {(pd.Timestamp(s['date']) + pd.Timedelta(days=14)).strftime('%d %b %Y')}",
                    "confidence": 0.9 if seen >= 2 else 0.75,
                    "why": f"You paid {s['merchant']} £{hist.iloc[-1]:,.0f} around this time last year"
                           + (f"; costs in this category are rising about {round(ASSUMPTIONS.get(ANNUAL_INFLATION.get(s['category'], 'cpi_annual')) * 100)}% a year" if s["category"] in ANNUAL_INFLATION else "")})
    # seasonal spikes in day-to-day spending inside the horizon
    dd = tx[tx["kind"].isin(DAY_TO_DAY_KINDS)]
    monthly = -dd.groupby(dd["date"].dt.to_period("M"))["amount"].sum()
    typical = monthly.median()
    for m in sorted({(t0 + pd.Timedelta(days=i)).month for i in range(1, 181)}, key=lambda m: (m < t0.month, m)):
        past = monthly[[p.month == m for p in monthly.index]]
        if len(past) and past.mean() - typical > 0.15 * typical:
            extra = past.mean() - typical
            yr = t0.year if m >= t0.month else t0.year + 1
            out.append({"type": "Seasonal spending increase", "merchant": None,
                        "expected_cost_low": round(extra * 0.8), "expected_cost_high": round(extra * 1.2),
                        "expected_date": date(yr, m, 1).isoformat(), "timeframe": date(yr, m, 1).strftime("%B %Y"),
                        "confidence": 0.8 if len(past) >= 1 else 0.6,
                        "why": f"Your {date(yr, m, 1).strftime('%B')} spending was about £{extra:,.0f} higher than a typical month last year"})
    # winter energy
    util = -tx[tx["category"] == "utilities"].groupby(tx["date"].dt.month)["amount"].mean()
    if len(util) >= 10:
        winter, summer = util[[m for m in (12, 1, 2) if m in util]].mean(), util[[m for m in (6, 7, 8) if m in util]].mean()
        if winter > summer * 1.15:
            out.append({"type": "Winter energy increase", "merchant": None,
                        "expected_cost_low": round((winter - summer) * 3 * 0.9), "expected_cost_high": round((winter - summer) * 3 * 1.2),
                        "expected_date": t0.date().isoformat(), "timeframe": "December – February",
                        "confidence": 0.85, "why": f"Your energy bills were about £{winter - summer:,.0f}/month higher last winter than in summer"})
    return sorted(out, key=lambda e: e["expected_date"])


# ------------------------------------------------------------------ Model 4: opportunities
def opportunities(customer, f):
    acct, out = customer["account"], []
    best = ASSUMPTIONS["best_easy_access_savings_rate"]
    if acct["savings_balance"] > 1000 and acct.get("savings_rate", 0) < best - 0.01:
        gain = acct["savings_balance"] * (best - acct["savings_rate"])
        out.append({"opportunity": "Savings earning a low interest rate", "estimated_benefit_annual": round(gain),
                    "confidence": 0.88, "action": f"Compare easy-access accounts paying around {best * 100:.1f}%",
                    "why": f"£{acct['savings_balance']:,.0f} is earning {acct['savings_rate'] * 100:.1f}%"})
    if f["avg_monthly_surplus"] > 100 and f["emergency_fund_months"] < 3:
        amt = round(f["avg_monthly_surplus"] * 0.5, -1)
        out.append({"opportunity": "Build an emergency fund", "estimated_benefit_annual": round(amt * 12),
                    "confidence": 0.8, "action": f"Set aside £{amt:,.0f} a month on payday",
                    "why": f"You have about £{f['avg_monthly_surplus']:,.0f} left over each month but savings cover only {f['emergency_fund_months']} months"})
    subs = f["spending_by_category_monthly"].get("subscriptions", 0)
    if subs > 30:
        out.append({"opportunity": "Review subscriptions", "estimated_benefit_annual": round(subs * 12 * 0.3),
                    "confidence": 0.65, "action": "Check which subscriptions you still use",
                    "why": f"Subscriptions cost you about £{subs:,.0f} a month"})
    if f["income_change_pct"] < -0.08 or f["avg_monthly_surplus"] < 0:
        out.append({"opportunity": "Check benefit and support eligibility", "estimated_benefit_annual": None,
                    "confidence": 0.7, "action": "Use a free benefits calculator such as Turn2us or entitledto",
                    "why": "Your income has dropped or your spending is higher than your income"})
    if f["debt_to_income"] > 0.08 and f["avg_monthly_surplus"] < 0:
        out.append({"opportunity": "Free debt advice", "estimated_benefit_annual": None, "confidence": 0.62,
                    "action": "Talk to a free service such as StepChange or MoneyHelper",
                    "why": f"Debt repayments take {round(f['debt_to_income'] * 100)}% of your income"})
    if customer["profile"].get("student") and f["income_volatility"] > 0.5:
        out.append({"opportunity": "Spread your loan instalment", "estimated_benefit_annual": None, "confidence": 0.72,
                    "action": "Move each loan payment to savings and pay yourself a weekly allowance",
                    "why": "Your income arrives in large lumps a few times a year"})
    return out


# ------------------------------------------------------------------ main entry
def analyse(customer, transactions, today=None, answers=None):
    """answers: the 4 onboarding answers (see personalise.py). Optional."""
    today = today or date.today()
    tx = _prep(pd.DataFrame(transactions) if not isinstance(transactions, pd.DataFrame) else transactions)
    tx = tx[tx["date"] <= pd.Timestamp(today)]
    acct = customer["account"]
    limit = acct["overdraft_limit"]
    bal_hist = _balance_history(tx, acct["current_balance"], today)
    f = build_features(tx, customer, bal_hist, today)
    a = P.normalise(answers)

    _, base_flows, scheduled, factors = simulate(tx, acct["current_balance"], today)
    flows, life_changes = P.apply_life_changes(base_flows, scheduled, a, today, np.random.default_rng(1))
    balances = acct["current_balance"] + np.cumsum(flows, axis=1)
    base_bal = acct["current_balance"] + np.cumsum(base_flows, axis=1)

    cf = cashflow_forecast(balances, today, max(f["avg_monthly_spending"], 1), f["history_months"])
    cf["series"]["p50_without_life_changes"] = np.round(np.percentile(base_bal, 50, axis=0), 2).tolist()
    cf["depletion"]["prob_beyond_overdraft_90d"] = round(float((balances[:, :90] < -limit).any(axis=1).mean()), 2)
    cf["overdraft_share_90d"] = round(float((np.percentile(balances[:, :90], 50, axis=0) < 0).mean()), 2)
    cf["overdraft_limit"] = limit
    cf["scheduled_payments"] = [{k: v for k, v in s.items() if k != "_vals"} for s in scheduled
                                if s["day_index"] < 60]
    cf["life_changes"] = life_changes

    extra = []
    if a["shock_500"] in P.SHOCK_WEIGHT and P.SHOCK_WEIGHT[a["shock_500"]] > 0:
        extra.append(("self_reported_resilience", P.SHOCK_WEIGHT[a["shock_500"]],
                      f"You'd cover a £500 surprise bill with {P.SHOCK_LABEL[a['shock_500']]}"))
    hr = hardship_risk(f, balances, limit, extra)
    st = P.stress_tests(flows, scheduled, acct["current_balance"], limit, today)
    ue = upcoming_expenses(tx, scheduled, factors, today, f)
    op = opportunities(customer, f)
    keys = P.GOAL_OPPS.get(a["goal"], [])
    for o in op:
        o["matches_goal"] = any(k in o["opportunity"].lower() for k in keys)
    op.sort(key=lambda o: (not o["matches_goal"], -o["confidence"]))
    hidden = sum(1 for x in ue + op if x["confidence"] < CONFIDENCE_THRESHOLD)

    # advanced layer
    signals = A.behaviour_signals(tx, today)
    support_needs = A.normalise_support((answers or {}).get("support_needs"))
    advanced = {
        "action_plan": A.action_planner(flows, scheduled, acct["current_balance"], limit, f),
        "safe_to_spend": A.safe_to_spend(balances, scheduled, tx, today, limit),
        "backtest": A.backtest(tx, bal_hist, simulate),
        "behaviour_signals": signals,
        "life_stage": A.life_stage(customer.get("profile", {})),
        "support": A.support_plan(support_needs, signals),
        "bill_calendar": A.bill_calendar(scheduled, balances),
    }

    monthly = tx.assign(m=tx["date"].dt.to_period("M").astype(str))
    hist = (monthly[monthly["kind"] != "transfer"]
            .assign(inc=lambda d: d["amount"].clip(lower=0), out=lambda d: (-d["amount"]).clip(lower=0))
            .groupby("m")[["inc", "out"]].sum().round(2))
    return {
        "customer": {k: customer[k] for k in ("id", "name", "persona")},
        "as_of": today.isoformat(),
        "account": acct,
        "answers": dict(a, support_needs=support_needs),
        "headline": P.HEADLINE_FN[a["worry"]](st, f, cf) if a["worry"] in P.HEADLINE_FN else None,
        "priority_sections": P.PRIORITY.get(a["worry"], ["cashflow_forecast", "hardship_risk", "upcoming_expenses", "opportunities"]),
        "cashflow_forecast": cf,
        "hardship_risk": hr,
        "stress_tests": st,
        "goal_plan": P.goal_plan(a["goal"], f, customer, flows, acct["current_balance"], limit),
        "data_checks": P.data_checks(a, customer, f),
        "advanced": advanced,
        "upcoming_expenses": [x for x in ue if x["confidence"] >= CONFIDENCE_THRESHOLD],
        "opportunities": [x for x in op if x["confidence"] >= CONFIDENCE_THRESHOLD],
        "hidden_below_confidence_threshold": hidden,
        "features": f,
        "history": {"monthly": [{"month": m, "income": r.inc, "spending": r.out} for m, r in hist.iterrows()],
                    "balance_last_90d": {"dates": [d.date().isoformat() for d in bal_hist.index[-90:]],
                                         "balance": np.round(bal_hist.to_numpy()[-90:], 2).tolist()}},
        "assumptions": dict({k: v for k, v in ASSUMPTIONS.items() if k != "seasonal_prior"},
                            life_events={k: v["assumption"] for k, v in P.LIFE_EVENTS.items()}),
    }
