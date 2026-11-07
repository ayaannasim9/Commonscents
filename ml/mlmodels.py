"""Trained ML models.

1. Hardship risk model: gradient-boosted trees (HistGradientBoostingClassifier), isotonic-calibrated,
   trained on a synthetic population to predict "goes past overdraft limit in the next 90 days"
   from history-only features plus the Monte Carlo forecast. Per-customer explanations by
   feature ablation (replace one feature with the population median, measure the change).
2. Merchant categoriser: TF-IDF character n-grams + logistic regression, for merchants the
   keyword rules don't recognise.

Train with:  python3 train.py      (writes models/*.joblib and models/metrics.json)
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODELS = Path(__file__).parent / "models"
GAMBLING = r"bet365|betfair|paddy ?power|william hill|ladbrokes|sky ?bet|betway|casino|lottery|pokerstars"
BNPL = r"klarna|clearpay|laybuy|paypal pay in 3|zilch"

FEATURES = [
    "mc_prob_past_overdraft_90d", "mc_prob_below_zero_90d", "mc_p10_90d_vs_spend",
    "headroom_months", "balance_vs_income", "savings_rate", "income_change_pct", "income_volatility",
    "fixed_cost_change_pct", "utility_cost_change_pct", "non_essential_spend_pct", "emergency_fund_months",
    "savings_change_6m_pct", "overdraft_days_pct_90d", "overdraft_days_change", "debt_to_income",
    "gambling_share", "bnpl_share", "payday_splurge_ratio", "spend_spike_days",
]


def behaviour_numbers(tx, today):
    t0 = pd.Timestamp(today)
    last = tx[tx["date"] > t0 - pd.Timedelta(days=180)]
    income = float(last.loc[last["kind"] == "income", "amount"].sum()) or 1.0
    merch = last["merchant"].str.lower()
    gamb = float(-last.loc[merch.str.contains(GAMBLING, regex=True) | (last["category"] == "gambling"), "amount"].sum())
    bnpl = float(-last.loc[merch.str.contains(BNPL, regex=True), "amount"].sum())
    opt = last[last["kind"] == "optional"]
    daily = (-opt.groupby(opt["date"].dt.normalize())["amount"].sum()).reindex(
        pd.date_range(t0 - pd.Timedelta(days=179), t0), fill_value=0.0)
    med = float(daily.median()); mad = float((daily - med).abs().median()) or 5.0
    spikes = int(((daily > med + 5 * mad) & (daily > 60)).sum())
    inc = tx[tx["kind"] == "income"]
    ratio = 1.0
    if len(inc):
        big = inc[inc["amount"] >= 0.3 * inc["amount"].max()]["date"].dt.normalize().unique()
        post = [daily[d: d + pd.Timedelta(days=2)].sum() for d in big if d in daily.index]
        if post and daily.mean() > 0:
            ratio = float(np.mean(post) / (daily.mean() * 3))
    return {"gambling_share": gamb / income, "bnpl_share": bnpl / income,
            "payday_splurge_ratio": min(ratio, 10.0), "spend_spike_days": spikes}


def feature_vector(f, account, mc, beh):
    """f: build_features() output; mc: dict(prob_past, prob_below, p10_90); beh: behaviour_numbers()."""
    spend = max(f["avg_monthly_spending"], 1.0)
    inc = max(f["avg_monthly_income"], 1.0)
    v = {
        "mc_prob_past_overdraft_90d": mc["prob_past"], "mc_prob_below_zero_90d": mc["prob_below"],
        "mc_p10_90d_vs_spend": mc["p10_90"] / spend,
        "headroom_months": (account["current_balance"] + account["overdraft_limit"]) / spend,
        "balance_vs_income": account["current_balance"] / inc,
        "savings_rate": f["savings_rate"], "income_change_pct": f["income_change_pct"],
        "income_volatility": f["income_volatility"], "fixed_cost_change_pct": f["fixed_cost_change_pct"],
        "utility_cost_change_pct": f["utility_cost_change_pct"] or 0.0,
        "non_essential_spend_pct": f["non_essential_spend_pct"], "emergency_fund_months": f["emergency_fund_months"],
        "savings_change_6m_pct": f["savings_change_6m_pct"], "overdraft_days_pct_90d": f["overdraft_days_pct_90d"],
        "overdraft_days_change": f["overdraft_days_pct_90d"] - f["overdraft_days_pct_prev_90d"],
        "debt_to_income": f["debt_to_income"], **beh,
    }
    return np.array([float(np.clip(np.nan_to_num(v[k]), -50, 50)) for k in FEATURES])


# ------------------------------------------------------------------ explanations
def _pct(x):
    return f"{round(x * 100)}%"


TEXT = {
    "mc_prob_past_overdraft_90d": lambda v: f"{_pct(v)} chance of going past your overdraft limit in the next 90 days",
    "mc_prob_below_zero_90d": lambda v: f"{_pct(v)} chance of your balance going below £0 in the next 90 days",
    "mc_p10_90d_vs_spend": lambda v: "In a bad month, your balance could fall well below zero" if v < 0 else "Even in a bad month you stay in credit",
    "headroom_months": lambda v: f"Your balance plus overdraft covers {max(v, 0):.1f} months of spending",
    "balance_vs_income": lambda v: f"Your balance today is {_pct(v)} of a month's income",
    "savings_rate": lambda v: f"You spend {_pct(-v)} more than you earn" if v < 0 else f"You keep {_pct(v)} of your income",
    "income_change_pct": lambda v: f"Income is {_pct(abs(v))} {'lower' if v < 0 else 'higher'} than the previous 6 months",
    "income_volatility": lambda v: "Your income changes a lot from month to month" if v > 0.3 else "Your income is steady",
    "fixed_cost_change_pct": lambda v: f"Bills are {_pct(abs(v))} {'higher' if v > 0 else 'lower'} than 6 months ago",
    "utility_cost_change_pct": lambda v: f"Energy bills are {_pct(abs(v))} {'higher' if v > 0 else 'lower'} than last year",
    "non_essential_spend_pct": lambda v: f"{_pct(v)} of spending is non-essential",
    "emergency_fund_months": lambda v: f"Savings would cover {v:.1f} months of spending",
    "savings_change_6m_pct": lambda v: "Savings haven't grown in 6 months" if abs(v) < 0.01 else f"Savings {'fell' if v < 0 else 'grew'} by {_pct(abs(v))} in 6 months",
    "overdraft_days_pct_90d": lambda v: f"In overdraft on {_pct(v)} of days in the last 3 months",
    "overdraft_days_change": lambda v: "Overdraft use is about the same as the 3 months before" if abs(v) < 0.02 else f"Overdraft use {'went up' if v > 0 else 'went down'} compared with the 3 months before",
    "debt_to_income": lambda v: f"Debt repayments take {_pct(v)} of your income",
    "gambling_share": lambda v: f"{_pct(v)} of income goes to gambling",
    "bnpl_share": lambda v: f"{_pct(v)} of income goes to buy-now-pay-later",
    "payday_splurge_ratio": lambda v: f"Non-essential spending is {v:.1f}× higher just after payday",
    "spend_spike_days": lambda v: f"{int(v)} days of unusually high spending in 6 months",
}


class RiskModel:
    def __init__(self, bundle):
        self.model, self.medians, self.metrics = bundle["model"], bundle["medians"], bundle.get("metrics", {})

    @classmethod
    def load(cls):
        p = MODELS / "hardship_model.joblib"
        return cls(joblib.load(p)) if p.exists() else None

    def predict(self, x):
        return float(self.model.predict_proba(x.reshape(1, -1))[0, 1])

    def explain(self, x, top=4):
        """Feature ablation: how much does each feature push this customer's risk up vs a typical value?"""
        p = self.predict(x)
        X = np.repeat(x.reshape(1, -1), len(FEATURES), axis=0)
        X[np.arange(len(FEATURES)), np.arange(len(FEATURES))] = self.medians
        deltas = p - self.model.predict_proba(X)[:, 1]
        flat = {"income_change_pct", "fixed_cost_change_pct", "utility_cost_change_pct", "overdraft_days_change",
                "gambling_share", "bnpl_share", "spend_spike_days"}
        ok = [j for j in range(len(FEATURES)) if not (FEATURES[j] in flat and abs(x[j]) < 0.02)]
        item = lambda j: {"factor": FEATURES[j], "detail": TEXT[FEATURES[j]](x[j]), "impact": round(float(deltas[j]), 3)}
        out = [item(j) for j in sorted(ok, key=lambda j: -deltas[j]) if deltas[j] > 0.03][:top]
        good = {"headroom_months": lambda v: v > 1, "emergency_fund_months": lambda v: v > 1, "savings_rate": lambda v: v > 0,
                "mc_prob_past_overdraft_90d": lambda v: v < 0.2, "mc_prob_below_zero_90d": lambda v: v < 0.2,
                "income_volatility": lambda v: v <= 0.3, "savings_change_6m_pct": lambda v: v > 0.01}
        protective = [item(j) for j in sorted(ok, key=lambda j: deltas[j])
                      if deltas[j] < -0.05 and FEATURES[j] in good and good[FEATURES[j]](x[j])][:2]
        return p, out, protective


# ------------------------------------------------------------------ merchant categoriser
TRAINING_MERCHANTS = {
    "groceries": ["Tesco", "Tesco Express", "Sainsbury's", "Sainsburys Local", "Asda", "Asda Superstore", "Aldi", "Lidl", "Morrisons",
                  "Co-op Food", "Waitrose", "Iceland", "M&S Food", "Ocado", "Spar", "Farmfoods", "Budgens", "Costco"],
    "eating_out": ["Deliveroo", "Just Eat", "Uber Eats", "McDonald's", "Nando's", "Greggs", "Pret A Manger", "KFC", "Burger King",
                   "Pizza Hut", "Domino's Pizza", "Costa Coffee", "Starbucks", "Caffe Nero", "Wagamama", "Subway", "Five Guys", "Leon"],
    "going_out": ["The Crown", "Wetherspoon", "Revolution Bar", "Odeon Cinema", "Vue Cinema", "Cineworld", "Ticketmaster",
                  "The Red Lion", "O2 Academy", "Brewdog", "All Bar One", "Slug and Lettuce", "Hollywood Bowl"],
    "shopping": ["Amazon", "Amazon Marketplace", "ASOS", "Argos", "John Lewis", "Next", "Primark", "Zara", "H&M", "Boohoo",
                 "Currys", "IKEA", "TK Maxx", "JD Sports", "Very.co.uk", "eBay", "Etsy", "B&Q", "Dunelm", "Shein"],
    "transport": ["Stagecoach", "TfL Travel", "Trainline", "Uber", "Bolt", "National Express", "Avanti West Coast", "First Bus",
                  "LNER", "Northern Rail", "Arriva", "Bee Network", "Megabus", "NCP Parking"],
    "fuel": ["Shell", "Esso", "BP", "Texaco", "Gulf", "Jet Petrol", "Tesco Petrol", "Asda Petrol", "Sainsburys Petrol"],
    "utilities": ["Octopus Energy", "British Gas", "EDF Energy", "E.ON Next", "OVO Energy", "Scottish Power", "United Utilities",
                  "Thames Water", "Severn Trent", "Yorkshire Water", "So Energy"],
    "phone": ["EE", "Vodafone", "O2", "Three Mobile", "giffgaff", "BT Broadband", "Virgin Media", "TalkTalk", "Plusnet",
              "Sky Mobile", "Lebara", "iD Mobile", "Hyperoptic"],
    "subscriptions": ["Netflix", "Spotify", "Disney Plus", "Amazon Prime", "Apple.com Bill", "Google Storage", "YouTube Premium",
                      "PureGym", "The Gym Group", "TV Licensing", "Now TV", "Audible", "Xbox Game Pass", "PlayStation Plus", "Sky TV"],
    "insurance": ["Admiral", "Aviva Insurance", "Direct Line", "Churchill Insurance", "LV Insurance", "Hastings Direct",
                  "AA Insurance", "RAC Breakdown", "Legal and General", "Vitality", "Esure", "Saga Insurance"],
    "health": ["Boots", "Superdrug", "Lloyds Pharmacy", "Specsavers", "Vision Express", "Bupa Dental", "Holland & Barrett"],
    "debt_repayment": ["Klarna", "Clearpay", "Black Horse Finance", "Barclaycard", "Capital One", "Vanquis", "Zopa Loan",
                       "PayPal Pay in 3", "Laybuy", "Santander Loan", "Novuna Finance", "Aqua Card"],
    "gambling": ["Bet365", "William Hill", "Paddy Power", "Ladbrokes", "Coral", "Sky Bet", "Betfair", "Betway",
                 "National Lottery", "PokerStars", "888 Casino", "Grosvenor Casino"],
    "council_tax": ["Manchester City Council", "Leeds City Council", "Birmingham City Council", "Stockport Council",
                    "Salford City Council", "Council Tax Bristol", "London Borough of Camden", "Trafford Council"],
    "rent": ["Northside Lettings", "Unite Students", "Foxtons Rent", "OpenRent", "Home Lettings", "Grainger Rent",
             "Your Move Lettings", "Housing Association Rent", "iQ Student Accommodation"],
    "education": ["Blackwell's Books", "Waterstones", "University of Manchester", "Coursera", "Udemy", "Open University"],
}
CAT_KIND = {"groceries": "variable", "eating_out": "optional", "going_out": "optional", "shopping": "optional",
            "transport": "variable", "fuel": "variable", "utilities": "fixed", "phone": "fixed", "subscriptions": "fixed",
            "insurance": "fixed", "health": "variable", "debt_repayment": "fixed", "gambling": "optional",
            "council_tax": "fixed", "rent": "fixed", "education": "fixed"}


class Categoriser:
    def __init__(self, bundle):
        self.pipe, self.metrics = bundle["pipe"], bundle.get("metrics", {})

    @classmethod
    def load(cls):
        p = MODELS / "categoriser.joblib"
        return cls(joblib.load(p)) if p.exists() else None

    def predict(self, name, min_conf=0.45):
        proba = self.pipe.predict_proba([name])[0]
        j = int(np.argmax(proba))
        cat = self.pipe.classes_[j]
        return (str(cat), CAT_KIND[str(cat)], float(proba[j])) if proba[j] >= min_conf else None


_risk, _cat = "unloaded", "unloaded"


def risk_model():
    global _risk
    if _risk == "unloaded":
        _risk = RiskModel.load()
    return _risk


def categoriser():
    global _cat
    if _cat == "unloaded":
        _cat = Categoriser.load()
    return _cat


# ------------------------------------------------------------------ learned forecaster (quantile GBM + conformal)
HORIZONS_ML = (30, 90)
QUANTS = (0.1, 0.5, 0.9)
MC_FEATURES = [f"mc_q{int(q * 100)}_{h}d" for h in HORIZONS_ML for q in QUANTS]
FORECAST_FEATURES = FEATURES + MC_FEATURES


def mc_quantile_features(balances, current, spend):
    """Monte Carlo quantiles of the balance change at 30/90 days, scaled by monthly spending."""
    out = []
    for h in HORIZONS_ML:
        out += list((np.percentile(balances[:, h - 1], [q * 100 for q in QUANTS]) - current) / max(spend, 1.0))
    return np.array(out)


class Forecaster:
    """Hybrid of the Monte Carlo simulation and quantile gradient boosting, with split-conformal intervals."""

    def __init__(self, bundle):
        self.models, self.conformal, self.blend, self.metrics = bundle["models"], bundle["conformal"], bundle["blend"], bundle.get("metrics", {})

    @classmethod
    def load(cls):
        p = MODELS / "forecaster.joblib"
        return cls(joblib.load(p)) if p.exists() else None

    def predict(self, xf, current, spend):
        out = {}
        mc = xf[len(FEATURES):]
        for hi, h in enumerate(HORIZONS_ML):
            ml = [float(self.models[(h, q)].predict(xf.reshape(1, -1))[0]) for q in QUANTS]
            mcq = list(mc[hi * 3: hi * 3 + 3])
            w = self.blend
            lo, mid, hiq = sorted(w * a + (1 - w) * b for a, b in zip(ml, mcq))
            pad = self.conformal[h]
            s = max(spend, 1.0)
            out[h] = {"low": round(current + (lo - pad) * s, 2), "expected": round(current + mid * s, 2),
                      "high": round(current + (hiq + pad) * s, 2)}
        return out


_fc = "unloaded"


def forecaster():
    global _fc
    if _fc == "unloaded":
        _fc = Forecaster.load()
    return _fc


# ------------------------------------------------------------------ customer segmentation (k-means)
SEGMENT_FEATURES = ["savings_rate", "emergency_fund_months", "headroom_months", "income_volatility",
                    "non_essential_spend_pct", "overdraft_days_pct_90d", "debt_to_income"]


class Segmenter:
    def __init__(self, bundle):
        self.scaler, self.km, self.names, self.desc = bundle["scaler"], bundle["kmeans"], bundle["names"], bundle["desc"]
        self.pop, self.labels, self.metrics = bundle["population"], bundle["labels"], bundle.get("metrics", {})

    @classmethod
    def load(cls):
        p = MODELS / "segments.joblib"
        return cls(joblib.load(p)) if p.exists() else None

    def assign(self, x):
        idx = [FEATURES.index(f) for f in SEGMENT_FEATURES]
        z = self.scaler.transform(np.clip(x[idx], -20, 20).reshape(1, -1))
        k = int(self.km.predict(z)[0])
        peers = self.pop[self.labels == k]

        def pct(feat, higher_is_better=True, group=peers):
            j = FEATURES.index(feat)
            v = (group[:, j] < x[j]).mean() if higher_is_better else (group[:, j] > x[j]).mean()
            return round(float(v) * 100)
        return {"segment": self.names[k], "description": self.desc[k], "share_of_customers": round(float((self.labels == k).mean()) * 100),
                "peer_percentiles": {"savings_rate": pct("savings_rate"), "emergency_fund": pct("emergency_fund_months"),
                                     "overdraft_use_lower_than": pct("overdraft_days_pct_90d", higher_is_better=False),
                                     "savings_rate_vs_everyone": pct("savings_rate", group=self.pop)}}


_seg = "unloaded"


def segmenter():
    global _seg
    if _seg == "unloaded":
        _seg = Segmenter.load()
    return _seg


# ------------------------------------------------------------------ unusual transactions (Isolation Forest)
def unusual_transactions(tx, today, recent_days=45, max_items=5):
    """Fit an Isolation Forest on the customer's own spending and flag recent transactions that don't fit."""
    from sklearn.ensemble import IsolationForest
    t0 = pd.Timestamp(today)
    d = tx[(tx["amount"] < 0) & (tx["kind"] != "transfer") & (tx["date"] > t0 - pd.Timedelta(days=365))].copy()
    if len(d) < 40:
        return []
    d["amt"] = -d["amount"]
    first_seen = tx.groupby("merchant")["date"].transform("min").reindex(d.index)
    counts = d["merchant"].map(d["merchant"].value_counts())
    med = d.groupby("merchant")["amt"].transform("median")
    mad = d.groupby("merchant")["amt"].transform(lambda s: (s - s.median()).abs().median()).replace(0, np.nan)
    cat_share = d["category"].map(d["category"].value_counts(normalize=True))
    F = pd.DataFrame({
        "log_amount": np.log1p(d["amt"]),
        "merchant_rarity": -np.log(counts),
        "new_merchant": ((d["date"] - first_seen).dt.days < 30).astype(float),
        "vs_usual": ((d["amt"] - med) / mad.fillna(d["amt"].std() or 1)).clip(-10, 10).fillna(0),
        "category_rarity": -np.log(cat_share),
        "weekend": (d["date"].dt.weekday >= 5).astype(float),
    })
    iso = IsolationForest(n_estimators=200, contamination=0.02, random_state=0).fit(F)
    score = -iso.score_samples(F)
    flag = iso.predict(F) == -1
    d = d.assign(score=score, flag=flag, **{c: F[c] for c in F})
    recent = d[(d["date"] > t0 - pd.Timedelta(days=recent_days)) & d["flag"] & (d["amt"] >= 25)].sort_values("score", ascending=False)
    out = []
    for _, r in recent.iterrows():
        prev = tx[(tx["merchant"] == r["merchant"]) & (tx["date"] < r["date"])]["date"]
        if len(prev) and 330 <= (r["date"] - prev.max()).days <= 400:
            continue  # yearly bill (insurance, licence, books): expected, not unusual
        rare_big = r["merchant_rarity"] > -np.log(3) and r["log_amount"] > np.log1p(d["amt"].quantile(0.95))
        if not (r["new_merchant"] or r["vs_usual"] > 3 or rare_big):
            continue  # Isolation Forest always flags its top 2%; only keep flags with a concrete reason
        if len(out) >= max_items:
            break
        why = ("First payment to this merchant" if r["new_merchant"] else
               f"About {r['amt'] / max(med[_], 1):.1f}× your usual payment to {r['merchant']}" if r["vs_usual"] > 3 else
               "A large payment to a merchant you rarely use")
        out.append({"date": r["date"].date().isoformat(), "merchant": r["merchant"], "amount": round(float(r["amt"]), 2),
                    "category": r["category"], "why": why, "anomaly_score": round(float(r["score"]), 3)})
    return out
