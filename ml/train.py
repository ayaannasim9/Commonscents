"""Train and evaluate the ML models.  Run:  python3 train.py [n_customers]

Writes models/hardship_model.joblib, models/categoriser.joblib and models/metrics.json.
"""
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score, accuracy_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import mlmodels as M
import model as core
import population as pop


def one(seed):
    """Generate one synthetic customer and compute its features exactly as the live pipeline does."""
    tx, cust, label, meta = pop.generate(seed)
    acct = cust["account"]
    bal_hist = core._balance_history(tx, acct["current_balance"], pop.TODAY)
    f = core.build_features(tx, cust, bal_hist, pop.TODAY)
    b, _, _, _ = core.simulate(tx, acct["current_balance"], pop.TODAY, horizon=90, n=200, seed=seed)
    lim = acct["overdraft_limit"]
    mc = {"prob_past": float((b < -lim).any(axis=1).mean()), "prob_below": float((b < 0).any(axis=1).mean()),
          "p10_90": float(np.percentile(b[:, -1], 10))}
    x = M.feature_vector(f, acct, mc, M.behaviour_numbers(tx, pop.TODAY))
    rule = float(core._sigmoid(-2.5 + sum(t[1] for t in core._hardship_terms(f, mc["prob_below"], mc["prob_past"]))))
    eligible = acct["current_balance"] >= -lim  # only customers not already past their limit: predict NEW trouble
    spend = max(f["avg_monthly_spending"], 1.0)
    xf = np.concatenate([x, M.mc_quantile_features(b, acct["current_balance"], spend)])
    fut = np.array(meta["future"])
    y_fc = {h: (fut[h - 1] - acct["current_balance"]) / spend for h in M.HORIZONS_ML}
    return x, label, meta["type"], rule, mc["prob_past"], eligible, xf, y_fc, spend


def generate_all(n):
    t = time.time()
    with ProcessPoolExecutor() as ex:
        res = list(ex.map(one, range(1000, 1000 + n), chunksize=20))
    print(f"generated {n} customers in {time.time() - t:.0f}s")
    return res


def train_risk(all_res):
    res = [r for r in all_res if r[5]]
    t = time.time()
    print(f"{len(res)} of {len(all_res)} customers are currently within their overdraft limit and are used")
    n = len(res)
    X = np.array([r[0] for r in res]); y = np.array([r[1] for r in res])
    types = np.array([r[2] for r in res]); rule = np.array([r[3] for r in res]); sim = np.array([r[4] for r in res])
    print(f"generated {n} customers in {time.time() - t:.0f}s, hardship rate {y.mean():.1%}")

    idx = np.arange(n)
    tr, te = train_test_split(idx, test_size=0.25, stratify=y, random_state=42)
    hgb = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=20,
                                         l2_regularization=1.0, random_state=0)
    model = CalibratedClassifierCV(hgb, method="isotonic", cv=5)
    model.fit(X[tr], y[tr])
    logreg = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=0.5)).fit(X[tr], y[tr])

    p = model.predict_proba(X[te])[:, 1]
    p_lr = logreg.predict_proba(X[te])[:, 1]
    cv_auc = cross_val_score(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                                                             min_samples_leaf=20, l2_regularization=1.0, random_state=0),
                             X, y, cv=StratifiedKFold(5, shuffle=True, random_state=1), scoring="roc_auc")
    frac, mean_pred = calibration_curve(y[te], p, n_bins=8, strategy="quantile")
    imp = permutation_importance(model, X[te], y[te], scoring="roc_auc", n_repeats=5, random_state=0)
    by_type = {t: round(float(roc_auc_score(y[te][types[te] == t], p[types[te] == t])), 3)
               for t in np.unique(types[te]) if len(set(y[te][types[te] == t])) == 2}

    metrics = {
        "n_customers": int(n), "n_train": int(len(tr)), "n_test": int(len(te)), "hardship_rate": round(float(y.mean()), 3),
        "label": "goes past overdraft limit within the next 90 days (hidden future)",
        "test": {
            "gradient_boosting_calibrated": {"roc_auc": round(roc_auc_score(y[te], p), 3), "pr_auc": round(average_precision_score(y[te], p), 3),
                                             "brier": round(brier_score_loss(y[te], p), 4), "log_loss": round(log_loss(y[te], p), 4),
                                             "accuracy_at_0.5": round(accuracy_score(y[te], p >= 0.5), 3)},
            "logistic_regression": {"roc_auc": round(roc_auc_score(y[te], p_lr), 3), "brier": round(brier_score_loss(y[te], p_lr), 4)},
            "monte_carlo_only": {"roc_auc": round(roc_auc_score(y[te], sim[te]), 3), "brier": round(brier_score_loss(y[te], sim[te]), 4)},
            "hand_weighted_rules": {"roc_auc": round(roc_auc_score(y[te], rule[te]), 3), "brier": round(brier_score_loss(y[te], rule[te]), 4)},
            "base_rate_guess": {"brier": round(brier_score_loss(y[te], np.full(len(te), y[tr].mean())), 4)},
        },
        "cv_roc_auc_5fold": {"mean": round(float(cv_auc.mean()), 3), "std": round(float(cv_auc.std()), 3)},
        "roc_auc_by_customer_type": by_type,
        "calibration": [{"predicted": round(float(a), 3), "actual": round(float(b), 3)} for a, b in zip(mean_pred, frac)],
        "feature_importance": sorted([{"feature": M.FEATURES[j], "auc_drop": round(float(imp.importances_mean[j]), 4)}
                                      for j in range(len(M.FEATURES))], key=lambda d: -d["auc_drop"]),
    }
    model.fit(X, y)  # final model on all data
    M.MODELS.mkdir(exist_ok=True)
    joblib.dump({"model": model, "medians": np.median(X, axis=0), "metrics": metrics, "features": M.FEATURES},
                M.MODELS / "hardship_model.joblib", compress=3)
    return metrics


def _variants(name, rng):
    """Bank-statement style variants of a merchant name."""
    s = name.upper()
    opts = [name, s, f"CARD PAYMENT TO {s}", f"{s} {rng.integers(100, 9999)}", f"{s}*{rng.integers(10, 99)} GB",
            f"DD {s}", f"{s} LTD", f"{name.lower()} london", f"POS {s} MANCHESTER"]
    return list(rng.choice(opts, 4, replace=False))


def train_categoriser():
    rng = np.random.default_rng(0)
    names = [(n, c) for c, ns in M.TRAINING_MERCHANTS.items() for n in ns]
    texts, labels, groups = [], [], []
    for g, (n, c) in enumerate(names):
        for v in _variants(n, rng):
            texts.append(v); labels.append(c); groups.append(g)
    texts, labels, groups = np.array(texts), np.array(labels), np.array(groups)

    def pipe():
        return make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), lowercase=True, sublinear_tf=True),
                             LogisticRegression(max_iter=3000, C=8))
    # evaluate on merchants never seen in training (group split by merchant)
    from sklearn.model_selection import GroupKFold
    accs = []
    for tr, te in GroupKFold(5).split(texts, labels, groups):
        accs.append(accuracy_score(labels[te], pipe().fit(texts[tr], labels[tr]).predict(texts[te])))
    seen = []
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=0).split(texts, labels):
        seen.append(accuracy_score(labels[te], pipe().fit(texts[tr], labels[tr]).predict(texts[te])))
    final = pipe().fit(texts, labels)
    metrics = {"n_merchants": len(names), "n_examples": int(len(texts)), "n_categories": len(M.TRAINING_MERCHANTS),
               "accuracy_new_statement_formats": round(float(np.mean(seen)), 3),
               "accuracy_unseen_merchants": round(float(np.mean(accs)), 3)}
    joblib.dump({"pipe": final, "metrics": metrics}, M.MODELS / "categoriser.joblib", compress=3)
    return metrics


def pinball(y, q, tau):
    d = y - q
    return float(np.mean(np.maximum(tau * d, (tau - 1) * d)))


def train_forecaster(res):
    """Quantile gradient boosting on top of the simulation, blended with it, with split-conformal intervals."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    XF = np.array([r[6] for r in res]); spend = np.array([r[8] for r in res])
    idx = np.arange(len(res))
    tr, rest = train_test_split(idx, test_size=0.4, random_state=7)
    cal, te = train_test_split(rest, test_size=0.5, random_state=7)  # calibration set for conformal, test set untouched
    models, conformal, metrics = {}, {}, {}
    mc_cols = {(h, q): len(M.FEATURES) + hi * 3 + qi for hi, h in enumerate(M.HORIZONS_ML) for qi, q in enumerate(M.QUANTS)}
    # choose blend weight on the calibration set
    preds = {}
    for h in M.HORIZONS_ML:
        y = np.array([r[7][h] for r in res])
        for q in M.QUANTS:
            m = HistGradientBoostingRegressor(loss="quantile", quantile=q, max_iter=300, learning_rate=0.05,
                                              max_leaf_nodes=15, min_samples_leaf=20, random_state=0).fit(XF[tr], y[tr])
            models[(h, q)] = m
            preds[(h, q)] = m.predict(XF)
    best_w, best_loss = 0.5, 1e9
    for w in np.linspace(0, 1, 11):
        loss = 0
        for h in M.HORIZONS_ML:
            y = np.array([r[7][h] for r in res])
            for q in M.QUANTS:
                loss += pinball(y[cal], w * preds[(h, q)][cal] + (1 - w) * XF[cal, mc_cols[(h, q)]], q)
        if loss < best_loss:
            best_w, best_loss = float(w), loss
    for h in M.HORIZONS_ML:
        y = np.array([r[7][h] for r in res])
        blend = {q: best_w * preds[(h, q)] + (1 - best_w) * XF[:, mc_cols[(h, q)]] for q in M.QUANTS}
        lo, hi_ = np.minimum(blend[0.1], blend[0.9]), np.maximum(blend[0.1], blend[0.9])
        # split-conformal (CQR): widen the 10-90 band so it covers 80% on the calibration set
        E = np.maximum(lo[cal] - y[cal], y[cal] - hi_[cal])
        k = int(np.ceil(0.8 * (len(cal) + 1))) - 1
        Q = float(np.sort(E)[min(k, len(E) - 1)])
        conformal[h] = Q
        mc_lo, mc_mid, mc_hi = (XF[te, mc_cols[(h, q)]] for q in M.QUANTS)

        def score(l, m, u):
            return {"pinball_avg_gbp": round(float(np.mean([pinball(y[te] * spend[te], v * spend[te], q)
                                                            for v, q in ((l, 0.1), (m, 0.5), (u, 0.9))])), 1),
                    "median_abs_error_gbp": round(float(np.median(np.abs((y[te] - m) * spend[te]))), 1),
                    "coverage_80": round(float(((y[te] >= l) & (y[te] <= u)).mean()), 3)}
        metrics[f"{h}d"] = {"monte_carlo_only": score(mc_lo, mc_mid, mc_hi),
                            "learned_quantile_gbm": score(*(preds[(h, q)][te] for q in M.QUANTS)),
                            "hybrid_conformal": score(lo[te] - Q, blend[0.5][te], hi_[te] + Q)}
    out = {"blend_weight_ml": best_w, "n_train": len(tr), "n_calibration": len(cal), "n_test": len(te), "horizons": metrics}
    joblib.dump({"models": models, "conformal": conformal, "blend": best_w, "metrics": out}, M.MODELS / "forecaster.joblib", compress=3)
    return out


def train_segments(res):
    """k-means customer segments on rank-transformed features (robust to outliers), named from member medians."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import QuantileTransformer
    X = np.array([r[0] for r in res])
    idx = [M.FEATURES.index(f) for f in M.SEGMENT_FEATURES]
    raw = np.clip(X[:, idx], -20, 20)
    scaler = QuantileTransformer(n_quantiles=200, output_distribution="normal", random_state=0).fit(raw)
    Z = scaler.transform(raw)
    scores = {k: silhouette_score(Z, KMeans(k, n_init=10, random_state=0).fit_predict(Z), sample_size=1500, random_state=0)
              for k in range(4, 7)}
    k = max(scores, key=scores.get)
    km = KMeans(k, n_init=20, random_state=0).fit(Z)
    labels = km.labels_
    med = pd.DataFrame([np.median(raw[labels == i], axis=0) for i in range(k)], columns=M.SEGMENT_FEATURES)
    rules = [("Comfortable savers", "Strong savings and plenty of headroom.",
              lambda c: c.emergency_fund_months >= 1.5 and c.overdraft_days_pct_90d < 0.2),
             ("Uneven income", "Income arrives in lumps (loans, shifts), so some months are much tighter.",
              lambda c: c.income_volatility > 0.5),
             ("Living in the overdraft", "Little or no buffer; the overdraft is used most days.",
              lambda c: c.overdraft_days_pct_90d > 0.4),
             ("Stretched", "Spending more than comes in each month.", lambda c: c.savings_rate < -0.05),
             ("Building a buffer", "Saving a little each month, with a small cushion so far.",
              lambda c: c.savings_rate > 0 and c.emergency_fund_months < 1.5),
             ("Paying off debt", "A noticeable share of income goes on debt repayments.", lambda c: c.debt_to_income > 0.08),
             ("Lifestyle spenders", "Doing fine, with a larger share on non-essentials.", lambda c: c.non_essential_spend_pct > 0.3),
             ("Getting by", "Balanced, with little room for surprises.", lambda c: True)]
    names, desc, used = [None] * k, [None] * k, set()
    # most distinctive clusters choose first: order clusters by how many rules they match (fewest first)
    order = sorted(range(k), key=lambda i: sum(f(med.iloc[i]) for _, _, f in rules))
    for i in order:
        c = med.iloc[i]
        choice = next(((nm, d) for nm, d, f in rules if f(c) and nm not in used), None)
        if choice is None:  # name by the trait that most sets this group apart from everyone else
            popmed, spread = np.median(raw, axis=0), np.std(raw, axis=0) + 1e-9
            zz = (med.iloc[i].to_numpy() - popmed) / spread
            phrases = {("savings_rate", 1): ("Steady savers", "Saving regularly each month."),
                       ("savings_rate", -1): ("Spending it all", "Little left over at the end of the month."),
                       ("emergency_fund_months", 1): ("Well cushioned", "A good savings cushion for surprises."),
                       ("emergency_fund_months", -1): ("No cushion yet", "Very little set aside for surprises."),
                       ("headroom_months", -1): ("Little headroom", "Close to the overdraft limit."),
                       ("headroom_months", 1): ("Plenty of headroom", "Well away from the overdraft limit."),
                       ("income_volatility", 1): ("Uneven income", "Income changes a lot month to month."),
                       ("income_volatility", -1): ("Steady earners", "Reliable income, modest buffer."),
                       ("non_essential_spend_pct", 1): ("Lifestyle spenders", "A larger share on non-essentials."),
                       ("non_essential_spend_pct", -1): ("Essentials first", "Most spending goes on essentials."),
                       ("overdraft_days_pct_90d", 1): ("Often overdrawn", "In the overdraft on many days."),
                       ("overdraft_days_pct_90d", -1): ("Rarely overdrawn", "Hardly ever uses the overdraft."),
                       ("debt_to_income", 1): ("Paying off debt", "A noticeable share of income goes on debt."),
                       ("debt_to_income", -1): ("Debt-free", "Little or no debt to repay.")}
            for j in np.argsort(-np.abs(zz)):
                nm, d = phrases[(M.SEGMENT_FEATURES[j], 1 if zz[j] > 0 else -1)]
                if nm not in used:
                    choice = (nm, d); break
            choice = choice or ("Getting by", "Balanced, with little room for surprises.")
        names[i], desc[i] = choice
        used.add(choice[0])
    sizes = {names[i]: round(float((labels == i).mean()) * 100) for i in range(k)}
    metrics = {"k": k, "scaling": "quantile (rank) transform", "silhouette": {str(a): round(float(b), 3) for a, b in scores.items()},
               "segments_pct": sizes,
               "typical_member": {names[i]: {c: round(float(med.iloc[i][c]), 2) for c in M.SEGMENT_FEATURES} for i in range(k)}}
    joblib.dump({"scaler": scaler, "kmeans": km, "names": names, "desc": desc, "population": X, "labels": labels,
                 "metrics": metrics}, M.MODELS / "segments.joblib", compress=3)
    return metrics


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    M.MODELS.mkdir(exist_ok=True)
    res = generate_all(n)
    risk = train_risk(res)
    fc = train_forecaster(res)
    seg = train_segments(res)
    cat = train_categoriser()
    out = {"hardship_model": risk, "forecaster": fc, "segments": seg, "categoriser": cat}
    (M.MODELS / "metrics.json").write_text(json.dumps(out, indent=2))
    t = risk["test"]
    print(json.dumps({k: v for k, v in t.items()}, indent=1))
    print("CV AUC", risk["cv_roc_auc_5fold"], "| by type", risk["roc_auc_by_customer_type"])
    print("calibration", risk["calibration"])
    print("top features", [d["feature"] for d in risk["feature_importance"][:6]])
    print("categoriser", cat)
    print("forecaster", json.dumps(fc, indent=1))
    print("segments", json.dumps(seg, indent=1))
