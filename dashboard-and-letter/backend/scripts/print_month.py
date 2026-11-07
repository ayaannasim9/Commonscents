"""Print a month of transactions (with plain names) and the facts, for human review.

  python scripts/print_month.py [--persona JDN-2208] [--event scam_transfer ...] [--month 2026-11] [--json]
"""
import argparse
import json
from datetime import date

from counterpart.generator import generate
from counterpart.merchants import categorise
from counterpart.personas import DEFAULT_ID, DEMO_END, SPECS
from counterpart.pipeline import build_facts

ap = argparse.ArgumentParser()
ap.add_argument("--persona", default=DEFAULT_ID, help="id, or a first name such as jayden")
ap.add_argument("--event", action="append", default=[])
ap.add_argument("--month", default=f"{DEMO_END[0]}-{DEMO_END[1]:02d}")
ap.add_argument("--json", action="store_true", help="print the full facts JSON (default: a compact summary)")
a = ap.parse_args()
spec = next(s for s in SPECS.values() if a.persona.lower() in (s.id.lower(), s.name.lower()))
y, m = map(int, a.month.split("-"))
txs = generate(spec, events=a.event, end=(y, m))
print(f"=== {spec.name} ({spec.id}, {spec.archetype}) statement {a.month} (events: {a.event or 'none'}) ===")
print(f"{'date':<11}{'time':<6}{'amount':>10}  {'description':<46} -> plain name")
net = 0
for t in (t for t in txs if (t.date.year, t.date.month) == (y, m)):
    net += t.amount_pence
    print(f"{t.date!s:<11}{t.time or '':<6}{t.amount:>10.2f}  {t.description:<46} -> {categorise(t.description).plain_name}")
print(f"{'net':<17}{net/100:>10.2f}\n")
as_of = date(y + (m == 12), m % 12 + 1, 1)
f = build_facts(spec.profile(), txs, as_of).to_contract()
if a.json:
    print("=== Facts ===")
    print(json.dumps(f, indent=2))
else:
    lm = f["last_month"]
    print(f"=== Facts summary (as of {f['as_of']}) ===")
    print(f"headline {f['headline_status']} | in £{lm['in']:,} | cash £{lm['cash']:,} | left £{lm['left']:,} | cash blind spot {f['cash_blind_spot']}")
    print("out: " + ", ".join(f"{o['name']} £{o['amount']:,}" for o in lm["out"]))
    for fm in f["forecast"]:
        print(f"  {fm['month']:<9} {fm['status']:<5} spare £{fm['spare']:>5,}  extra £{fm['extra']:>4,}  reason: {fm['reason']}")
    print("suggestion:", f["suggestion"])
    for fl in f["flags"]:
        print("  FLAG", fl["kind"], fl["severity"], f"£{fl['amount']:,}", fl["plain_name"], fl["reasons"])
