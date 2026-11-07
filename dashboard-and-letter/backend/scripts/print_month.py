"""Print a month of transactions (with plain names) and the facts JSON, for human review.

  python scripts/print_month.py [--event scam_transfer ...] [--month 2026-11]
"""
import argparse
import json
from datetime import date

from counterpart.generator import generate
from counterpart.merchants import categorise
from counterpart.persona import DEMO_END, MARGARET
from counterpart.pipeline import build_facts

ap = argparse.ArgumentParser()
ap.add_argument("--event", action="append", default=[])
ap.add_argument("--month", default=f"{DEMO_END[0]}-{DEMO_END[1]:02d}")
a = ap.parse_args()
y, m = map(int, a.month.split("-"))
txs = generate(MARGARET, events=a.event)
print(f"=== Statement {a.month} (events: {a.event or 'none'}) ===")
print(f"{'date':<11}{'time':<6}{'amount':>10}  {'description':<46} -> plain name")
net = 0
for t in (t for t in txs if (t.date.year, t.date.month) == (y, m)):
    net += t.amount_pence
    print(f"{t.date!s:<11}{t.time or '':<6}{t.amount:>10.2f}  {t.description:<46} -> {categorise(t.description).plain_name}")
print(f"{'net':<17}{net/100:>10.2f}\n")
as_of = date(y + (m == 12), m % 12 + 1, 1)
print("=== Facts ===")
print(json.dumps(build_facts(MARGARET, txs, as_of).to_contract(), indent=2))
