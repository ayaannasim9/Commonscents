"""Synthetic customer population for training and testing the ML models.

Each customer gets ~13 months of history plus a hidden 90-day future. Archetypes (salaried, hourly,
student, pensioner) have random incomes, bills, habits and random shocks (pay cut, surprise bill,
price rise) that may land in the history or the hidden future. The label is whether the customer
went past their overdraft limit during the hidden 90 days.

No protected characteristics are generated or used.
"""
from datetime import date, timedelta

import numpy as np
import pandas as pd

TODAY = date(2026, 11, 7)
HIST_DAYS, FUT_DAYS = 400, 90


def _lognorm(rng, mean, sigma):
    return float(rng.lognormal(np.log(mean), sigma))


def generate(seed, today=TODAY):
    rng = np.random.default_rng(seed)
    start = today - timedelta(days=HIST_DAYS - 1)
    days = [start + timedelta(days=i) for i in range(HIST_DAYS + FUT_DAYS)]
    rows = []

    def add(d, amt, merchant, cat, kind):
        rows.append((d, round(float(amt), 2), merchant, cat, kind))

    itype = rng.choice(["salary", "wages", "student", "pension"], p=[0.55, 0.17, 0.12, 0.16])
    if itype == "salary":
        pay = _lognorm(rng, 2100, 0.35); payday = int(rng.integers(1, 29)); monthly_inc = pay
    elif itype == "wages":
        weekly = _lognorm(rng, 420, 0.3); monthly_inc = weekly * 52 / 12
    elif itype == "student":
        loan = rng.uniform(1300, 2400); side = rng.uniform(0, 160); monthly_inc = loan * 3 / 12 + side * 52 / 12
    else:
        state = rng.uniform(700, 950); private = rng.uniform(0, 900); monthly_inc = state * 13 / 12 + private

    budget = monthly_inc * rng.uniform(0.78, 1.14)
    rent = budget * (rng.uniform(0.28, 0.45) if itype != "pension" or rng.random() < 0.3 else 0)
    council = rng.uniform(90, 180)
    energy0, energy_trend = rng.uniform(60, 150), (rng.uniform(0.005, 0.03) if rng.random() < 0.5 else 0.0)
    phone = rng.uniform(12, 50)
    subs = [(m, rng.uniform(5, 16), int(rng.integers(1, 29))) for m in
            rng.choice(["Netflix", "Spotify", "Disney Plus", "PureGym", "Amazon Prime", "Sky TV"], int(rng.integers(0, 5)), replace=False)]
    debt = budget * rng.uniform(0.03, 0.12) if rng.random() < 0.4 else 0
    bnpl = rng.uniform(20, 80) if rng.random() < 0.15 else 0
    insurance = (int(rng.integers(1, 13)), int(rng.integers(1, 29)), rng.uniform(150, 800)) if rng.random() < 0.6 else None
    fixed = rent + council + energy0 + phone + sum(s[1] for s in subs) + debt + bnpl
    var_month = max(budget - fixed, budget * 0.15)
    groc_day, opt_day, trans_day = var_month * 0.45 / 30.4, var_month * 0.35 / 30.4, var_month * 0.2 / 30.4
    opt_sigma, splurge = rng.uniform(0.3, 0.9), (rng.uniform(1.5, 3.5) if rng.random() < 0.3 else 1.0)
    gamble = rng.uniform(5, 60) if rng.random() < 0.08 else 0

    od_limit = 1500.0 if itype == "student" else float(rng.choice([0, 250, 500, 1000, 1500], p=[0.15, 0.3, 0.3, 0.15, 0.1]))
    savings = _lognorm(rng, 800, 1.2) if rng.random() < 0.8 else 0.0
    balance = rng.uniform(-0.3 * od_limit, 1500)
    opening = balance

    cut_day = int(rng.integers(HIST_DAYS - 150, HIST_DAYS + FUT_DAYS)) if rng.random() < 0.25 else None
    cut = rng.uniform(0.6, 0.9)
    rise_day = int(rng.integers(HIST_DAYS - 200, HIST_DAYS + FUT_DAYS)) if rng.random() < 0.3 else None
    surprises = {int(d): rng.uniform(200, 1500) for d in rng.integers(0, HIST_DAYS + FUT_DAYS, rng.poisson(0.7))}

    balances, sav_hist, last_draw, post_income = [], {}, -99, -99
    for i, d in enumerate(days):
        flow = 0.0
        inc_mult = cut if (cut_day is not None and i >= cut_day) else 1.0
        rise = 1.3 if (rise_day is not None and i >= rise_day) else 1.0
        income_today = 0.0
        if itype == "salary" and d.day == payday:
            income_today = pay * inc_mult; add(d, income_today, "Employer Payroll Ltd", "salary", "income")
        elif itype == "wages" and d.weekday() == 4:
            income_today = weekly * inc_mult * rng.uniform(0.8, 1.2); add(d, income_today, "Agency Payroll", "wages", "income")
        elif itype == "student":
            if (d.month, d.day) in ((9, 22), (1, 12), (4, 20)):
                income_today = loan; add(d, loan, "Student Finance England", "student_finance", "income")
            if d.weekday() == 4 and side > 0 and d.month not in (6, 7, 8):
                add(d, side * inc_mult * rng.uniform(0.7, 1.3), "SU Payroll", "wages", "income"); flow += rows[-1][1]
        elif itype == "pension":
            if (d - start).days % 28 == 3:
                income_today = state; add(d, state, "DWP State Pension", "pension", "income")
            if d.day == 1 and private > 0:
                add(d, private, "Aviva Pension", "pension", "income"); flow += private
        flow += income_today
        if income_today > 0.3 * monthly_inc:
            post_income = i

        bills = []
        if d.day == 1 and rent: bills.append((rent * (1.05 if rise > 1 else 1), "Home Lettings", "rent", "fixed"))
        if d.day == 10: bills.append((council, "City Council", "council_tax", "fixed"))
        if d.day == 12:
            winter = 1.3 if d.month in (11, 12, 1, 2, 3) else 1.0
            bills.append((energy0 * (1 + energy_trend) ** (i / 30.4) * winter * rise, "Octopus Energy", "utilities", "fixed"))
        if d.day == 18: bills.append((phone, "EE", "phone", "fixed"))
        if d.day == 3 and debt: bills.append((debt, "Loan Finance", "debt_repayment", "fixed"))
        if bnpl and d.day in (6, 20): bills.append((bnpl / 2, "Klarna", "debt_repayment", "fixed"))
        for m, a, dd in subs:
            if d.day == dd: bills.append((a, m, "subscriptions", "fixed"))
        if insurance and (d.month, d.day) == insurance[:2]: bills.append((insurance[2], "Direct Line Insurance", "insurance", "fixed"))
        if i in surprises: bills.append((surprises[i], "Kwik Fit", "vehicle", "variable"))
        for a, m, c, k in bills:
            add(d, -a, m, c, k); flow -= a

        wk = 1.25 if d.weekday() >= 4 else 0.9
        g = rng.lognormal(np.log(max(groc_day, 1) * wk), 0.4) if rng.random() < 0.6 else 0
        if g: add(d, -g, "Tesco", "groceries", "variable"); flow -= g
        boost = splurge if i - post_income <= 2 else 1.0
        xmas = 1.5 if d.month == 12 and d.day <= 24 else 1.0
        o = rng.lognormal(np.log(max(opt_day, 1) * 2 * boost * xmas * wk), opt_sigma) if rng.random() < 0.5 else 0
        if o: add(d, -o, "Amazon", "shopping", "optional"); flow -= o
        t = rng.lognormal(np.log(max(trans_day, 1)), 0.3) if rng.random() < 0.7 else 0
        if t: add(d, -t, "Stagecoach", "transport", "variable"); flow -= t
        if gamble and d.weekday() == 5 and rng.random() < 0.6:
            gg = rng.lognormal(np.log(gamble), 0.6); add(d, -gg, "Bet365", "gambling", "optional"); flow -= gg

        balance += flow
        # savings behaviour: save after a good payday, draw down when overdrawn
        if income_today > 0 and balance > 0.8 * budget:
            mv = min(balance - 0.6 * budget, 0.15 * income_today)
            if mv > 20:
                add(d, -mv, "Transfer to Savings", "savings_transfer", "transfer"); balance -= mv; savings += mv
        if balance < -0.4 * max(od_limit, 200) and savings > 50 and i - last_draw >= 7:
            mv = min(savings, 250.0)
            add(d, mv, "Transfer from Savings", "savings_transfer", "transfer"); balance += mv; savings -= mv; last_draw = i
        balances.append(balance)
        sav_hist[d.strftime("%Y-%m")] = round(savings, 2)

    tx = pd.DataFrame(rows, columns=["date", "amount", "merchant", "category", "kind"])
    tx["date"] = pd.to_datetime(tx["date"])
    hist = tx[tx["date"] <= pd.Timestamp(today)].reset_index(drop=True)
    future = np.array(balances[HIST_DAYS:])
    label = int(future.min() < -od_limit)
    hist_months = [m for m in sav_hist if m <= today.strftime("%Y-%m")]
    customer = {
        "id": f"syn-{seed}", "name": f"Synthetic {seed}", "persona": itype,
        "profile": {"student": itype == "student", "retired": itype == "pension"},
        "account": {"current_balance": round(balances[HIST_DAYS - 1], 2), "overdraft_limit": od_limit,
                    "savings_balance": sav_hist[today.strftime("%Y-%m")], "savings_product": None, "savings_rate": 0.01},
        "savings_history": [{"month": m, "balance": sav_hist[m]} for m in hist_months],
    }
    return hist, customer, label, {"type": itype, "opening": opening, "future_min": float(future.min()),
                                   "future": future.round(2).tolist()}
