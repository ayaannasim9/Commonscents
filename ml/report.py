"""Printable A4 report (HTML + inline SVG charts) from analyse() output.

render(result) -> HTML string. Open in a browser and print / Save as PDF.
"""
from datetime import date
from html import escape

import pandas as pd

INK, MUTED, LINE, BAND, ACCENT = "#18222E", "#5D6A79", "#DCE2E9", "#C7D5F0", "#1F5FAF"
RISK = {"low": "#2E7D4F", "medium": "#B7791F", "high": "#B42318"}
GOOD, BAD = "#2E7D4F", "#B42318"


def money(x, dp=0):
    if x is None:
        return "–"
    s = f"£{abs(x):,.{dp}f}"
    return f"−{s}" if x < 0 else s


def pct(x):
    return f"{round(x * 100)}%"


def _nice_step(span, target=5):
    for s in (10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000, 20000):
        if span / s <= target:
            return s
    return 50000


# ------------------------------------------------------------------ charts
def fan_chart(r, W=720, H=255):
    cf, hist = r["cashflow_forecast"], r["history"]["balance_last_90d"]
    s = cf["series"]
    hd = [pd.Timestamp(d) for d in hist["dates"]]
    fd = [pd.Timestamp(d) for d in s["dates"]]
    start, end = hd[0], fd[-1]
    limit = cf.get("overdraft_limit", 0)
    vals = hist["balance"] + s["p10"] + s["p90"] + s.get("p50_without_life_changes", []) + [0]
    if limit:
        vals.append(-limit)
    lo, hi = min(vals), max(vals)
    step = _nice_step(hi - lo)
    lo, hi = (lo // step) * step, (hi // step + 1) * step
    L, R, T, B = 62, 14, 14, 30
    X = lambda d: L + (d - start).days / (end - start).days * (W - L - R)
    Y = lambda v: T + (hi - v) / (hi - lo) * (H - T - B)
    o = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="Balance history and forecast">']
    v = lo
    while v <= hi + 1e-6:
        o.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{LINE}"/>'
                 f'<text x="{L - 6}" y="{Y(v) + 4:.1f}" text-anchor="end" class="ax">{money(v)}</text>')
        v += step
    m = pd.Timestamp(start.year, start.month, 1) + pd.offsets.MonthBegin(1)
    while m <= end:
        lab = m.strftime("%b") + (f" {m.year}" if m.month == 1 else "")
        o.append(f'<line x1="{X(m):.1f}" x2="{X(m):.1f}" y1="{H - B}" y2="{H - B + 4}" stroke="{MUTED}"/>'
                 f'<text x="{X(m):.1f}" y="{H - B + 16}" text-anchor="middle" class="ax">{lab}</text>')
        m += pd.offsets.MonthBegin(1)
    # zero + overdraft limit
    o.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="{INK}" stroke-width="1.2"/>')
    if limit:
        o.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(-limit):.1f}" y2="{Y(-limit):.1f}" stroke="{BAD}" stroke-dasharray="5 4"/>'
                 f'<text x="{W - R - 4}" y="{Y(-limit) - 5:.1f}" text-anchor="end" class="ax" fill="{BAD}">Overdraft limit {money(-limit)}</text>')
    # today divider
    today = pd.Timestamp(r["as_of"])
    o.append(f'<line x1="{X(today):.1f}" x2="{X(today):.1f}" y1="{T}" y2="{H - B}" stroke="{MUTED}" stroke-dasharray="2 3"/>'
             f'<text x="{X(today) + 4:.1f}" y="{T + 10}" class="ax">Today</text>')
    # band + lines
    band = [f"{X(d):.1f},{Y(v):.1f}" for d, v in zip(fd, s["p90"])] + [f"{X(d):.1f},{Y(v):.1f}" for d, v in zip(fd[::-1], s["p10"][::-1])]
    o.append(f'<polygon points="{" ".join(band)}" fill="{BAND}" fill-opacity=".8"/>')
    if s.get("p50_without_life_changes") and any(abs(a - b) > 1 for a, b in zip(s["p50"], s["p50_without_life_changes"])):
        o.append(f'<polyline points="{" ".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in zip(fd, s["p50_without_life_changes"]))}" fill="none" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="6 4"/>')
    o.append(f'<polyline points="{" ".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in zip(hd, hist["balance"]))}" fill="none" stroke="{INK}" stroke-width="1.8"/>')
    o.append(f'<polyline points="{" ".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in zip(fd, s["p50"]))}" fill="none" stroke="{ACCENT}" stroke-width="2.2"/>')
    # event markers: life changes and yearly bills
    events = [(pd.Timestamp(c["date"]), c["change"], ACCENT) for c in cf.get("life_changes", [])]
    events += [(pd.Timestamp(e["expected_date"]), e["type"], MUTED) for e in r["upcoming_expenses"] if e.get("merchant")]
    for k, (d, lab, col) in enumerate(sorted(events)):
        if start <= d <= end:
            y = H - B - 8 - (k % 3) * 13
            right = X(d) > W - R - 110  # flip label to the left near the right edge
            o.append(f'<circle cx="{X(d):.1f}" cy="{y:.1f}" r="3.5" fill="{col}"/>'
                     f'<text x="{X(d) + (-6 if right else 6):.1f}" y="{y + 4:.1f}" class="ev" fill="{col}" text-anchor="{"end" if right else "start"}">{escape(lab)}</text>')
    o.append("</svg>")
    return "".join(o)


def hbars(items, W=340, label_w=120, fmt=money, color=ACCENT, zero_line=None):
    """items: list of (label, value, color|None). Handles negatives."""
    if not items:
        return ""
    vals = [v for _, v, _ in items] + [0] + ([zero_line] if zero_line is not None else [])
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    rowh, H = 24, 24 * len(items) + 6
    neg_pad = 52 if lo < 0 else 0
    X = lambda v: label_w + neg_pad + (v - lo) / span * (W - label_w - neg_pad - 52)
    o = [f'<svg viewBox="0 0 {W} {H}" class="chart">']
    o.append(f'<line x1="{X(0):.1f}" x2="{X(0):.1f}" y1="0" y2="{H}" stroke="{INK}"/>')
    if zero_line is not None:
        o.append(f'<line x1="{X(zero_line):.1f}" x2="{X(zero_line):.1f}" y1="0" y2="{H}" stroke="{BAD}" stroke-dasharray="4 3"/>')
    for i, (lab, v, col) in enumerate(items):
        y = 4 + i * rowh
        x0, x1 = sorted((X(0), X(v)))
        o.append(f'<text x="{label_w - 8}" y="{y + 14}" text-anchor="end" class="ax">{escape(lab)}</text>'
                 f'<rect x="{x0:.1f}" y="{y + 3}" width="{max(x1 - x0, 1):.1f}" height="14" rx="2" fill="{col or color}"/>'
                 f'<text x="{x1 + 5 if v >= 0 else x0 - 5:.1f}" y="{y + 14}" text-anchor="{"start" if v >= 0 else "end"}" class="val">{fmt(v)}</text>')
    o.append("</svg>")
    return "".join(o)


def month_bars(monthly, W=340, H=125):
    ms = monthly[-12:]
    hi = max(max(m["income"], m["spending"]) for m in ms) or 1
    step = _nice_step(hi, 4)
    hi = (hi // step + 1) * step
    L, B, T = 44, 20, 8
    bw = (W - L - 6) / len(ms)
    Y = lambda v: T + (1 - v / hi) * (H - T - B)
    o = [f'<svg viewBox="0 0 {W} {H}" class="chart">']
    v = 0
    while v <= hi:
        o.append(f'<line x1="{L}" x2="{W}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{LINE}"/><text x="{L - 4}" y="{Y(v) + 3:.1f}" text-anchor="end" class="ax">{money(v)}</text>')
        v += step
    for i, m in enumerate(ms):
        x = L + i * bw
        o.append(f'<rect x="{x + 2:.1f}" y="{Y(m["income"]):.1f}" width="{bw / 2 - 2:.1f}" height="{Y(0) - Y(m["income"]):.1f}" fill="{GOOD}"/>'
                 f'<rect x="{x + bw / 2:.1f}" y="{Y(m["spending"]):.1f}" width="{bw / 2 - 2:.1f}" height="{Y(0) - Y(m["spending"]):.1f}" fill="{BAD}" fill-opacity=".75"/>'
                 f'<text x="{x + bw / 2:.1f}" y="{H - 6}" text-anchor="middle" class="ax">{pd.Timestamp(m["month"]).strftime("%b")[0]}</text>')
    o.append("</svg>")
    return "".join(o)


# ------------------------------------------------------------------ page
CSS = f"""
@page {{ size: A4; margin: 12mm 13mm; }}
* {{ box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ margin: 0; background: #EEF1F5; color: {INK}; font: 10.5pt/1.45 -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }}
.page {{ width: 210mm; min-height: 297mm; margin: 12px auto; background: #fff; padding: 12mm 13mm; display: flex; flex-direction: column; gap: 14px; }}
@media print {{ body {{ background: #fff; }} .page {{ margin: 0; width: auto; min-height: 0; padding: 0; zoom: .9; }} .page + .page {{ break-before: page; }} .noprint {{ display: none; }} }}
h1 {{ font-size: 20pt; margin: 0; letter-spacing: -.01em; }}
h2 {{ font-size: 12pt; margin: 0 0 6px; }}
.eyebrow {{ font-size: 7.5pt; letter-spacing: .12em; text-transform: uppercase; color: {MUTED}; font-weight: 600; }}
.muted {{ color: {MUTED}; }} .small {{ font-size: 8.5pt; }}
header {{ display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid {INK}; padding-bottom: 8px; gap: 16px; }}
header .right {{ text-align: right; font-size: 9pt; color: {MUTED}; }}
.headline {{ background: #F3F6FB; border-left: 4px solid {ACCENT}; padding: 10px 14px; font-size: 12pt; font-weight: 600; }}
.headline .small {{ font-weight: 400; display: block; margin-top: 3px; }}
.tiles {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }}
.tile {{ border: 1px solid {LINE}; border-radius: 6px; padding: 8px 10px; }}
.tile .v {{ font-size: 15pt; font-weight: 700; font-variant-numeric: tabular-nums; }}
.tile .s {{ font-size: 8.5pt; color: {MUTED}; }}
.pill {{ display: inline-block; padding: 1px 8px; border-radius: 99px; color: #fff; font-size: 8pt; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; }}
.chart {{ width: 100%; height: auto; display: block; }}
.chart .ax {{ font-size: 9px; fill: {MUTED}; }} .chart .val {{ font-size: 9px; fill: {INK}; font-weight: 600; }} .chart .ev {{ font-size: 9px; font-weight: 600; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 14px; font-size: 8.5pt; color: {MUTED}; }}
.legend i {{ display: inline-block; width: 16px; height: 8px; margin-right: 5px; vertical-align: middle; border-radius: 2px; }}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 9pt; }}
th {{ text-align: left; font-size: 7.5pt; letter-spacing: .08em; text-transform: uppercase; color: {MUTED}; border-bottom: 1px solid {INK}; padding: 4px 6px; }}
td {{ border-bottom: 1px solid {LINE}; padding: 5px 6px; vertical-align: top; }}
td.n {{ font-variant-numeric: tabular-nums; white-space: nowrap; }}
.drv {{ display: grid; grid-template-columns: 1fr 70px; gap: 4px 10px; align-items: center; font-size: 9.5pt; }}
.meter {{ height: 7px; background: {LINE}; border-radius: 4px; overflow: hidden; }} .meter b {{ display: block; height: 100%; background: {BAD}; }}
.box {{ border: 1px solid {LINE}; border-radius: 6px; padding: 10px 12px; }}
.note {{ font-size: 9pt; border-left: 3px solid #B7791F; padding: 4px 10px; background: #FBF6EC; }}
footer {{ margin-top: auto; font-size: 7.8pt; color: {MUTED}; border-top: 1px solid {LINE}; padding-top: 6px; }}
.alerts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
.alert {{ border: 1px solid {LINE}; border-radius: 6px; padding: 7px 10px; display: flex; flex-direction: column; gap: 3px; font-size: 9pt; }}
.btn {{ position: fixed; top: 12px; right: 12px; background: {INK}; color: #fff; border: 0; border-radius: 6px; padding: 8px 14px; font-weight: 600; cursor: pointer; }}
"""

ANSWER_LABEL = {"build_savings": "Build savings", "buy_home": "Buy a home", "pay_off_debt": "Pay off debt",
                "manage_expenses": "Manage monthly expenses", "retirement": "Retirement",
                "unexpected_bills": "Unexpected bills", "running_out": "Running out of money before payday", "debt": "Debt",
                "not_saving": "Not saving enough", "job_security": "Job security", "savings": "Savings",
                "credit_card": "Credit card", "overdraft": "Overdraft", "family_friends": "Borrowing from family/friends",
                "cannot_cover": "I couldn't cover it"}


def conf_label(c):
    return "High" if c >= 0.8 else "Medium" if c >= 0.6 else "Low"


def plan_page(r, footer):
    A = r.get("advanced")
    if not A:
        return ""
    c, as_of = r["customer"], pd.Timestamp(r["as_of"]).strftime("%d %B %Y")
    ap, sts, bt = A["action_plan"], A.get("safe_to_spend"), A.get("backtest")
    needs = r.get("answers", {}).get("support_needs", [])

    def mrow(lbl, k, f=lambda v: v):
        b, a = ap["before"][k], ap["after"][k]
        better = (a > b) if k == "lowest_expected_balance" else (a < b)
        return (f'<tr><td>{lbl}</td><td class="n">{f(b)}</td><td class="n" style="color:{GOOD if better else INK};font-weight:{700 if better else 400}">{f(a)}</td></tr>')
    if ap["steps"]:
        steps = "".join(f'<li><b>{escape(s["action"])}</b> <span class="small muted">({s["effort"]} · lowest balance then {money(s["after"]["lowest_expected_balance"])})</span></li>' for s in ap["steps"])
        plan = (f'<ol style="margin:0;padding-left:18px;display:flex;flex-direction:column;gap:5px">{steps}</ol>'
                f'<table style="margin-top:8px"><tr><th>Next {ap["window_days"]} days</th><th>Now</th><th>With the plan</th></tr>'
                + mrow("Lowest expected balance", "lowest_expected_balance", money)
                + mrow("Days overdrawn (expected)", "expected_days_overdrawn", lambda v: f"{v:.0f}")
                + mrow("Chance of going past overdraft", "prob_past_overdraft", pct) + "</table>")
    else:
        plan = '<p class="muted" style="margin:0">Your forecast looks healthy. No changes needed to stay on track.</p>'

    cal = A.get("bill_calendar", [])
    cal_rows = "".join(f'<tr><td class="n">{pd.Timestamp(x["date"]).strftime("%a %d %b")}</td><td>{escape(x["who"])}</td>'
                       f'<td class="n" style="color:{GOOD if x["amount"] > 0 else INK}">{"+" if x["amount"] > 0 else ""}{money(x["amount"])}</td>'
                       f'<td class="n">{money(x["balance_after"])}</td></tr>' for x in cal[:10 if "tracking" in needs else 7])
    sig = "".join(f'<li>{escape(x["text"])}</li>' for x in A.get("behaviour_signals", [])) or "<li class=muted>Nothing unusual.</li>"
    sup = A.get("support", {})
    sup_html = "".join(f'<div style="margin-bottom:6px"><b>{escape(i["label"])}</b> <span class="small muted">({escape(i["offered_because"])})</span>'
                       f'<div class="small">{escape(i["how_we_help"])}</div>'
                       + ("<ul class=small style='margin:2px 0 0;padding-left:16px'>" + "".join(f"<li>{escape(x)}</li>" for x in i["resources"]) + "</ul>" if i["resources"] else "")
                       + "</div>" for i in sup.get("items", []))
    ls = A.get("life_stage", {})
    tips = "".join(f"<li>{escape(t)}</li>" for t in ls.get("tips", []))
    return f"""
<section class="page">
  <header><div><div class="eyebrow">Common Cents · Financial forecast</div><h1>Your plan</h1></div>
    <div class="right">{escape(c["name"])} · {as_of}</div></header>
  <div class="cols">
    <div><h2>Smallest changes with the biggest effect</h2>{plan}
      <p class="small muted" style="margin:6px 0 0">{escape(ap["method"])}</p></div>
    <div style="display:flex;flex-direction:column;gap:10px">
      {f'<div class="box"><div class="eyebrow">Safe to spend</div><div style="font-size:15pt;font-weight:700">{money(sts["safe_daily_spend"] if sts["safe_daily_spend"] >= 1 else (sts.get("safe_daily_spend_within_overdraft") or 0))} a day</div><p class="small" style="margin:2px 0 0">{escape(sts["explanation"])}</p></div>' if sts else ''}
      <div><h2>Next {"30" if "tracking" in needs else "few"} days of bills and income</h2>
        <table><tr><th>Date</th><th>Who</th><th>Amount</th><th>Balance after</th></tr>{cal_rows}</table></div>
    </div>
  </div>
  <div class="cols">
    <div><h2>Spending patterns we noticed</h2><ul class="small" style="margin:0;padding-left:16px">{sig}</ul>
      <h2 style="margin-top:10px">For your stage of life ({escape(ls.get("stage", "").replace("_", " "))})</h2><ul class="small" style="margin:0;padding-left:16px">{tips}</ul></div>
    <div><h2>Support you asked for</h2>{sup_html or '<p class="small muted" style="margin:0">You can choose support options at any time.</p>'}
      <p class="small muted" style="margin:4px 0 0">{escape(sup.get("privacy", ""))}</p></div>
  </div>
  {f'<div class="box"><div class="eyebrow">How accurate is this forecast?</div><p style="margin:4px 0 0">{escape(bt["summary"])}</p><p class="small muted" style="margin:2px 0 0">We re-ran the model as if it were {", ".join(str((pd.Timestamp(r["as_of"]) - pd.Timestamp(x["from"])).days) for x in bt["runs"])} days ago and compared it with what really happened. {escape(bt["note"])}</p></div>' if bt else ''}
  {footer}
</section>"""


def render(r):
    c, cf, hr, st, f = r["customer"], r["cashflow_forecast"], r["hardship_risk"], r["stress_tests"], r["features"]
    a, acct = r.get("answers", {}), r["account"]
    hz = {h["days"]: h for h in cf["horizons"]}
    as_of = pd.Timestamp(r["as_of"]).strftime("%d %B %Y")
    dep = cf["depletion"]
    headline = r.get("headline") or (
        f"Your balance is expected to go below £0 around {pd.Timestamp(dep['date']).strftime('%d %B')}." if dep.get("date")
        else "Your balance is expected to stay above £0 for the next 12 months.")

    def tile(label, h):
        return (f'<div class="tile"><div class="eyebrow">{label}</div><div class="v">{money(h["predicted_balance"])}</div>'
                f'<div class="s">likely {money(h["range_low"])} to {money(h["range_high"])} · {conf_label(h["confidence"])} confidence ({pct(h["confidence"])})</div></div>')

    drivers = "".join(f'<div>{escape(d["detail"])}</div><div class="meter"><b style="width:{min(100, d["weight"] / 3 * 100):.0f}%"></b></div>'
                      for d in hr["drivers"]) or '<div class="muted">No significant risk factors found.</div><div></div>'
    life = cf.get("life_changes", [])
    life_html = "".join(f'<li><b>{escape(x["change"])}</b> from {pd.Timestamp(x["date"]).strftime("%d %b %Y")}: {escape(x["effect"])}. '
                        f'<span class="muted">Assumption: {escape(x["assumption"])}.</span></li>' for x in life)

    # page 2 pieces
    limit = acct["overdraft_limit"]
    stress_items = [("Forecast as is", st["baseline"]["lowest_expected_balance"], ACCENT),
                    ("£500 bill tomorrow", st["surprise_bill_500"]["lowest_expected_balance"], "#7A5AA6"),
                    ("No pay for 2 months", st["income_loss_2_months"]["lowest_expected_balance"], BAD)]
    stress_tbl = "".join(f'<tr><td>{n}</td><td class="n">{pct(s["prob_below_zero"])}</td><td class="n">{pct(s["prob_beyond_overdraft"])}</td></tr>'
                         for n, s in (("Forecast as is", st["baseline"]), ("£500 bill tomorrow", st["surprise_bill_500"]),
                                      ("No pay for 2 months", st["income_loss_2_months"])))
    gp = r.get("goal_plan")
    goal_html = (f'<div class="box"><div class="eyebrow">Your goal: {escape(gp["goal"])}</div><p style="margin:4px 0 0">{escape(gp["summary"])}</p>'
                 + (f'<p class="small muted" style="margin:4px 0 0">Target: {escape(gp["target_label"])}</p>' if gp.get("target_label") else "")
                 + "</div>") if gp else ""
    exp_rows = "".join(f'<tr><td class="n">{escape(e["timeframe"])}</td><td><b>{escape(e["type"])}</b>{"<br><span class=small>" + escape(e["merchant"]) + "</span>" if e.get("merchant") else ""}</td>'
                       f'<td class="n">{money(e["expected_cost_low"])}–{money(e["expected_cost_high"])}</td><td>{conf_label(e["confidence"])}</td>'
                       f'<td class="small muted">{escape(e["why"])}</td></tr>' for e in r["upcoming_expenses"][:6])
    opp_rows = "".join(f'<tr><td><b>{escape(o["opportunity"])}</b>{" <span class=small style=color:" + ACCENT + ">★ your goal</span>" if o.get("matches_goal") else ""}<br>'
                       f'<span class="small muted">{escape(o["why"])}</span></td><td class="n">{money(o["estimated_benefit_annual"]) + "/yr" if o.get("estimated_benefit_annual") else "–"}</td>'
                       f'<td class="small">{escape(o["action"])}</td><td>{conf_label(o["confidence"])}</td></tr>' for o in r["opportunities"])
    cats = sorted(f["spending_by_category_monthly"].items(), key=lambda kv: -kv[1])[:6]
    checks = "".join(f'<div class="note">{escape(x)}</div>' for x in r.get("data_checks", []))
    answers_tbl = "".join(f'<tr><td class="muted">{q}</td><td>{escape(v)}</td></tr>' for q, v in (
        ("Main goal", ANSWER_LABEL.get(a.get("goal"), "–")), ("Biggest worry", ANSWER_LABEL.get(a.get("worry"), "–")),
        ("Life changes in next 12 months", ", ".join(x.replace("_", " ").capitalize() for x in a.get("life_changes", [])) or "None"),
        ("How you'd cover a £500 bill", ANSWER_LABEL.get(a.get("shock_500"), "–"))))
    ins = r.get("insights") or {}
    KIND = {"risk": BAD, "forecast": ACCENT, "resilience": GOOD, "opportunity": "#7A5AA6"}
    cards = "".join(f'<div class="alert" style="border-top:3px solid {KIND.get(x["kind"], ACCENT)}"><div class="eyebrow" style="color:{KIND.get(x["kind"], ACCENT)}">{escape(x["kind"])} · {escape(x["confidence"])} confidence</div>'
                    f'<b>{escape(x["title"])}</b><div>{escape(x["message"])}</div><div class="small"><b>Why am I seeing this?</b> {escape(x["why"])}</div>'
                    f'<div class="small"><b>Try:</b> {escape(x["action"])}</div></div>' for x in ins.get("alerts", [])[:4])
    alerts_html = (f'<div><h2>Your alerts</h2>'
                   f'<div class="alerts">{cards}</div><div class="small muted" style="margin-top:4px">'
                   f'{"Written by Claude from the forecast data above." if ins.get("source") == "claude" else "Generated from the forecast data."}</div></div>') if cards else ""
    answers_line = escape(" · ".join(x for x in (ANSWER_LABEL.get(a.get("goal")), ANSWER_LABEL.get(a.get("worry")),
                                                 ", ".join(y.replace("_", " ").capitalize() for y in a.get("life_changes", [])) or "No life changes",
                                                 ("£500 bill: " + ANSWER_LABEL[a["shock_500"]]) if a.get("shock_500") in ANSWER_LABEL else None) if x))
    footer = (f'<footer>Common Cents · Forecast for {escape(c["name"])} · generated {as_of}. Guidance only: this report never moves money, blocks payments or changes '
              f'limits. It uses only your transactions and balances, never protected characteristics. Items below {pct(0.6)} confidence are not shown '
              f'({r.get("hidden_below_confidence_threshold", 0)} hidden).</footer>')

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Financial forecast – {escape(c["name"])}</title><style>{CSS}</style></head><body>
<button class="btn noprint" onclick="window.print()">Print / Save as PDF</button>

<section class="page">
  <header><div><div class="eyebrow">Common Cents · Financial forecast</div><h1>{escape(c["name"])}'s next 12 months</h1>
    <div class="muted small">{escape(c["persona"])}</div></div>
    <div class="right">Prepared {as_of}<br>Based on {f["history_months"]} months of transactions<br>1,000 simulated futures</div></header>

  <div class="headline">{escape(headline)}<span class="small muted">Answer to your biggest worry: {escape(ANSWER_LABEL.get(a.get("worry"), "–"))}</span></div>

  <div class="tiles">
    <div class="tile"><div class="eyebrow">Balance today</div><div class="v">{money(acct["current_balance"])}</div>
      <div class="s">Overdraft limit {money(limit)} · savings {money(acct["savings_balance"])}</div></div>
    {tile("In 30 days", hz[30])}{tile("In 90 days", hz[90])}
    <div class="tile"><div class="eyebrow">Hardship risk</div><div class="v">{pct(hr["score"])} <span class="pill" style="background:{RISK[hr["level"]]}">{"needs attention" if ("anxious" in a.get("support_needs", []) and hr["level"] != "low") else hr["level"]}</span></div>
      <div class="s">{conf_label(hr["confidence"])} confidence · {("£200 more savings → " + pct(hr["what_if"]["new_score"])) if hr["what_if"]["risk_reduction_pct"] > 0 else "needs more than a £200 buffer to improve"}</div></div>
  </div>

  <div><h2>Your balance: last 3 months and next 12 months</h2>{fan_chart(r)}
    <div class="legend"><span><i style="background:{INK}"></i>Actual balance</span><span><i style="background:{ACCENT}"></i>Most likely forecast</span>
      <span><i style="background:{BAND}"></i>Likely range (8 in 10 futures fall here)</span>
      {'<span><i style="background:none;border-top:2px dashed ' + MUTED + ';height:0"></i>Forecast without your life changes</span>' if life else ''}
      {'<span><i style="background:none;border-top:2px dashed ' + BAD + ';height:0"></i>Overdraft limit</span>' if limit else ''}</div>
    <p class="small muted" style="margin:6px 0 0">How to read this: the dark line is what actually happened. The blue line is the most likely path from today; the shaded band shows where your balance lands in 8 out of 10 simulated futures. The wider the band, the less certain the forecast.
    {(' Below £0 is expected around <b>' + pd.Timestamp(dep["date"]).strftime("%d %B %Y") + '</b>.') if dep.get("date") else ''}</p></div>

  <div class="cols">
    <div><h2>What's driving your risk</h2><div class="drv">{drivers}</div></div>
    <div><h2>Planned life changes</h2>{('<ul class="small" style="margin:0;padding-left:16px">' + life_html + '</ul>') if life else '<p class="muted small" style="margin:0">None planned in the next 12 months.</p>'}
      {checks}</div>
  </div>
  <div class="cols">
    <div><h2>Income vs spending, last 12 months</h2>{month_bars(r["history"]["monthly"])}
      <div class="legend"><span><i style="background:{GOOD}"></i>Money in</span><span><i style="background:{BAD};opacity:.75"></i>Money out</span></div></div>
    <div><h2>Where your money goes (per month)</h2>{hbars([(k.replace("_", " ").capitalize(), v, None) for k, v in cats], label_w=110)}</div>
  </div>

  {footer}
</section>

<section class="page">
  <header><div><div class="eyebrow">Common Cents · Financial forecast</div><h1>What could happen, and what you can do</h1></div>
    <div class="right">{escape(c["name"])} · {as_of}</div></header>

  {alerts_html}

  <div class="cols">
    <div><h2>Stress tests: lowest expected balance</h2>{hbars(stress_items, zero_line=-limit if limit else None)}
      <table style="margin-top:6px"><tr><th>Scenario (next 90 days)</th><th>Below £0</th><th>Past overdraft</th></tr>{stress_tbl}</table></div>
    <div style="display:flex;flex-direction:column;gap:10px">{goal_html}
      <div class="small"><b>Your answers:</b> {answers_line}</div></div>
  </div>

  {footer}
</section>

<section class="page">
  <header><div><div class="eyebrow">Common Cents · Financial forecast</div><h1>Coming up, and ways to get ahead</h1></div>
    <div class="right">{escape(c["name"])} · {as_of}</div></header>

  <div><h2>Coming up: bills and spending spikes we expect</h2>
    <table><tr><th>When</th><th>What</th><th>Expected cost</th><th>Confidence</th><th>Why we think so</th></tr>{exp_rows or '<tr><td colspan=5 class=muted>No large one-off costs expected.</td></tr>'}</table></div>

  <div><h2>Opportunities</h2>
    <table><tr><th>Opportunity</th><th>Benefit</th><th>Suggested action</th><th>Confidence</th></tr>{opp_rows or '<tr><td colspan=4 class=muted>No opportunities above the confidence threshold.</td></tr>'}</table></div>

  <div class="small muted"><b>How this forecast was made.</b> We found your regular income and bills from payment patterns, then simulated 1,000 possible futures,
    drawing day-to-day spending from your own history with seasonal effects (for example Christmas) and inflation. Risk scores combine the forecast with trends in
    your overdraft use, savings, income and bills; every factor is listed above. Economic figures and life-event costs are estimates and are listed in the data.</div>
  {footer}
</section>
{plan_page(r, footer)}
</body></html>"""
