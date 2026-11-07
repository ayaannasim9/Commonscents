"""Generate realistic fake bank data for 3 demo customers (18 months of history).

Run:  python3 generate_data.py
Writes data/customers.json and data/<id>_transactions.csv
"""
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

TODAY = date(2026, 11, 7)
START = date(2025, 5, 1)
OUT = Path(__file__).parent / "data"


def all_days():
    d = START
    while d <= TODAY:
        yield d
        d += timedelta(days=1)


class Ledger:
    def __init__(self, seed):
        self.rng = np.random.default_rng(seed)
        self.rows = []

    def add(self, d, amount, merchant, category, kind):
        self.rows.append({"date": d.isoformat(), "amount": round(float(amount), 2),
                          "merchant": merchant, "category": category, "kind": kind})

    def maybe(self, d, p, mean, merchant, category, kind="variable", sigma=0.35):
        if self.rng.random() < p:
            self.add(d, -self.rng.lognormal(np.log(mean), sigma), merchant, category, kind)


def xmas(d):  # festive multiplier
    if d.month == 12 and d.day <= 24:
        return 1.8
    return 1.0


# ---------------------------------------------------------------- student
def student():
    L = Ledger(1)
    loans = {date(2025, 9, 22): 1650, date(2026, 1, 12): 1650, date(2026, 4, 20): 1650, date(2026, 9, 21): 1700}
    for d in all_days():
        if d in loans:
            L.add(d, loans[d], "Student Finance England", "student_finance", "income")
        if d - timedelta(days=1) in loans:
            L.add(d, -L.rng.uniform(110, 170), "ASOS", "shopping", "optional")
        if d - timedelta(days=2) in loans:
            L.add(d, -L.rng.uniform(55, 80), "Revolution Bar", "going_out", "optional")
        if d.weekday() == 4:  # Friday wages
            summer = d.month in (6, 7, 8)
            L.add(d, L.rng.uniform(200, 260) if summer else L.rng.uniform(85, 140), "SU Bar Payroll", "wages", "income")
        if d.day == 1:
            L.add(d, -520, "Unite Students", "rent", "fixed")
        if d.day == 5:
            L.add(d, -22.99, "PureGym", "subscriptions", "fixed")
        if d.day == 15:
            L.add(d, -6.99, "Spotify", "subscriptions", "fixed")
        if d.day == 20:
            L.add(d, -15.00, "Three Mobile", "phone", "fixed")
        if d.month == 1 and d.day == 14:
            L.add(d, -30, "16-25 Railcard", "transport", "fixed")
        if d.month == 9 and d.day == 25:
            L.add(d, -85, "Blackwell's Books", "education", "fixed")
        x = xmas(d)
        if d.weekday() in (1, 5):
            L.maybe(d, 0.9, 24 * x, "Tesco", "groceries")
        if d.weekday() in (4, 5):
            L.maybe(d, 0.45, 26 * x, "Revolution Bar", "going_out", "optional")
            L.maybe(d, 0.25, 18, "Deliveroo", "eating_out", "optional")
        if d.weekday() < 5:
            L.maybe(d, 0.4, 2.5, "Stagecoach", "transport", sigma=0.1)
        L.maybe(d, 0.05 * x, 38, "ASOS", "shopping", "optional", 0.5)
        if d.month == 12 and 1 <= d.day <= 20:
            L.maybe(d, 0.15, 35, "Amazon", "gifts", "optional", 0.5)
    return L, {"id": "priya", "name": "Priya", "persona": "Second-year student on a maintenance loan",
               "profile": {"age_range": "18-24", "student": True, "retired": False, "dependants": 0,
                           "home_owner": False, "vehicle": False, "region": "North West"},
               "target_balance": 420, "overdraft_limit": 1500,
               "savings": {"start": 150, "monthly_change": 0, "product": "Easy Saver", "rate": 0.015}}


# ---------------------------------------------------------------- worker (struggling)
def worker():
    L = Ledger(2)
    savings_moves = []
    for i, d in enumerate(all_days()):
        months_in = (d.year - START.year) * 12 + d.month - START.month
        if d.day == 25:
            L.add(d, 1950 if d < date(2026, 3, 1) else 1720, "ACME Logistics Ltd", "salary", "income")
        if d.day == 1:
            L.add(d, -850, "Northside Lettings", "rent", "fixed")
        if d.day == 3:
            L.add(d, -189, "Black Horse Finance", "debt_repayment", "fixed")
        if d.day == 8:
            L.add(d, -10.99, "Netflix", "subscriptions", "fixed")
        if d.day == 10:
            L.add(d, -128, "Manchester City Council", "council_tax", "fixed")
        if d.day == 12:
            winter = 1.3 if d.month in (11, 12, 1, 2, 3) else 1.0
            L.add(d, -(92 * (1.015 ** months_in) * winter), "Octopus Energy", "utilities", "fixed")
        if d.day == 15:
            L.add(d, -11.99, "Spotify", "subscriptions", "fixed")
        if d.day == 18:
            L.add(d, -28, "EE", "phone", "fixed")
        if d == date(2026, 3, 14):
            L.add(d, -640, "Admiral Car Insurance", "insurance", "fixed")
        if d >= date(2026, 6, 1) and d.day in (6, 20):
            L.add(d, -24.99, "Klarna", "debt_repayment", "fixed")
        if d >= date(2026, 4, 1) and d.weekday() == 5:
            L.maybe(d, 0.35, 15, "Bet365", "gambling", "optional", 0.6)
        if d == date(2025, 6, 9):
            L.add(d, -455, "Kwik Fit", "vehicle", "variable")
        # savings: paid in until Dec 2025, then drawn down
        if d.day == 26:
            if d < date(2026, 2, 1):
                L.add(d, -100, "Transfer to Savings", "savings_transfer", "transfer")
                savings_moves.append((d, 100))
            else:
                L.add(d, 150, "Transfer from Savings", "savings_transfer", "transfer")
                savings_moves.append((d, -150))
        x = xmas(d)
        if d.weekday() in (2, 6):
            L.maybe(d, 0.95, 34 * x, "Tesco", "groceries")
        if d.weekday() == 0:
            L.maybe(d, 0.9, 42, "Shell", "fuel", sigma=0.15)
        if d.weekday() in (4, 5):
            L.maybe(d, 0.35, 22, "Just Eat", "eating_out", "optional")
            L.maybe(d, 0.3, 26 * x, "The Crown", "going_out", "optional")
        L.maybe(d, 0.05 * x, 35, "Amazon", "shopping", "optional", 0.6)
        if d.month == 12 and 1 <= d.day <= 22:
            L.maybe(d, 0.2, 45, "Argos", "gifts", "optional", 0.5)
    return L, {"id": "jordan", "name": "Jordan", "persona": "Warehouse supervisor, hours recently cut",
               "profile": {"age_range": "25-34", "student": False, "retired": False, "dependants": 1,
                           "home_owner": False, "vehicle": True, "region": "North West"},
               "target_balance": -160, "overdraft_limit": 500,
               "savings": {"start": 750, "moves": savings_moves, "product": "Easy Saver", "rate": 0.015}}


# ---------------------------------------------------------------- retired (stable)
def retired():
    L = Ledger(3)
    sav_moves = []
    pension_day = date(2025, 5, 6)
    for d in all_days():
        if (d - pension_day).days % 28 == 0 and d >= pension_day:
            L.add(d, 884.80, "DWP State Pension", "pension", "income")
        if d.day == 1:
            L.add(d, 240, "Aviva Pension", "pension", "income")
            L.add(d, -165, "Stockport Council", "council_tax", "fixed")
        if d.day == 15:
            winter = 1.45 if d.month in (11, 12, 1, 2, 3) else 1.0
            L.add(d, -(105 * winter), "British Gas", "utilities", "fixed")
        if d.day == 20:
            L.add(d, -46, "BT Broadband", "phone", "fixed")
        if d.day == 22:
            L.add(d, -45, "Sky TV", "subscriptions", "fixed")
            L.add(d, -20, "British Heart Foundation", "charity", "fixed")
        if d.day == 2:
            L.add(d, -150, "Transfer to Savings", "savings_transfer", "transfer")
            sav_moves.append((d, 150))
        if d.weekday() == 2:
            L.maybe(d, 0.6, 38, "Esso", "fuel", sigma=0.15)
        if d.month == 4 and d.day == 1:
            L.add(d, -174.50, "TV Licensing", "subscriptions", "fixed")
        if d.month == 10 and d.day == 2:
            L.add(d, -310 if d.year == 2025 else -338, "Direct Line Home Insurance", "insurance", "fixed")
        if d == date(2026, 2, 10):
            L.add(d, -128, "RAC Breakdown", "insurance", "fixed")
        x = xmas(d)
        if d.weekday() in (0, 3):
            L.maybe(d, 0.95, 38 * x, "Sainsbury's", "groceries")
        if d.weekday() == 5:
            L.maybe(d, 0.4, 22, "M&S Cafe", "eating_out", "optional")
        L.maybe(d, 0.08, 15, "Boots", "health")
        if d.month in (4, 5, 6, 7):
            L.maybe(d, 0.08, 30, "Dobbies Garden Centre", "shopping", "optional")
        if d.month == 12 and 1 <= d.day <= 22:
            L.maybe(d, 0.2, 55, "John Lewis", "gifts", "optional", 0.5)
    return L, {"id": "margaret", "name": "Margaret", "persona": "Retired, living on state and private pension",
               "profile": {"age_range": "65+", "student": False, "retired": True, "dependants": 0,
                           "home_owner": True, "vehicle": True, "region": "North West"},
               "target_balance": 2650, "overdraft_limit": 0,
               "savings": {"start": 11400, "moves": sav_moves, "product": "Instant Access Saver", "rate": 0.005}}


def savings_history(meta):
    """Month-end savings balances."""
    s = meta["savings"]
    months = pd.period_range(START, TODAY, freq="M")
    out, bal = [], s["start"]
    moves = s.get("moves")
    for m in months:
        if moves is not None:
            bal += sum(a for d, a in moves if d.year == m.year and d.month == m.month)
        else:
            bal += s["monthly_change"]
        out.append({"month": str(m), "balance": round(bal, 2)})
    return out


def main():
    OUT.mkdir(exist_ok=True)
    customers = []
    for make in (student, worker, retired):
        L, meta = make()
        df = pd.DataFrame(L.rows).sort_values("date").reset_index(drop=True)
        df.insert(0, "id", [f"{meta['id']}-{i:05d}" for i in range(len(df))])
        df.to_csv(OUT / f"{meta['id']}_transactions.csv", index=False)
        current = float(meta["target_balance"])
        opening = round(current - df.amount.sum(), 2)
        sav = savings_history(meta)
        customers.append({
            "id": meta["id"], "name": meta["name"], "persona": meta["persona"], "profile": meta["profile"],
            "account": {"current_balance": current, "overdraft_limit": meta["overdraft_limit"],
                        "savings_balance": sav[-1]["balance"], "savings_product": meta["savings"]["product"],
                        "savings_rate": meta["savings"]["rate"]},
            "savings_history": sav,
        })
        print(f"{meta['id']:9s} {len(df):5d} transactions  opening £{opening:,.2f}  current balance £{current:,.2f}  savings £{sav[-1]['balance']:,.2f}")
    (OUT / "customers.json").write_text(json.dumps(customers, indent=2))


if __name__ == "__main__":
    main()
