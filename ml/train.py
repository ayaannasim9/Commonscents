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
    return x, label, meta["type"], rule, mc["prob_past"], eligible


def train_risk(n):
    t = time.time()
    with ProcessPoolExecutor() as ex:
        res = [r for r in ex.map(one, range(1000, 1000 + n), chunksize=20) if r[5]]
    print(f"{len(res)} of {n} customers are currently within their overdraft limit and are used")
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


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    M.MODELS.mkdir(exist_ok=True)
    risk = train_risk(n)
    cat = train_categoriser()
    out = {"hardship_model": risk, "categoriser": cat}
    (M.MODELS / "metrics.json").write_text(json.dumps(out, indent=2))
    t = risk["test"]
    print(json.dumps({k: v for k, v in t.items()}, indent=1))
    print("CV AUC", risk["cv_roc_auc_5fold"], "| by type", risk["roc_auc_by_customer_type"])
    print("calibration", risk["calibration"])
    print("top features", [d["feature"] for d in risk["feature_importance"][:6]])
    print("categoriser", cat)
