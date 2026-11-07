"""Read UK Open Banking (v3.1 Account & Transaction API) data, the format NatWest's
Bank of APIs returns, and turn it into the engine's input. Also the "Transaction
Categorisation" step from the architecture diagram.

from_open_banking(transactions_json, balances_json, savings_balances_json=None, profile=None)
    -> (transactions DataFrame, customer dict)
"""
import re

import pandas as pd

# (regex on merchant / description, category, kind)
RULES = [
    (r"student finance|slc ", "student_finance", "income"),
    (r"bet365|betfair|paddy ?power|william hill|ladbrokes|sky ?bet|betway|casino|lottery|pokerstars", "gambling", "optional"),
    (r"pension|dwp", "pension", "income"),
    (r"payroll|salary|wages|\bltd\b|\blimited\b", "salary", "income"),
    (r"lettings|unite students|rent|estate", "rent", "fixed"),
    (r"council", "council_tax", "fixed"),
    (r"energy|british gas|edf|eon|octopus|ovo|water", "utilities", "fixed"),
    (r"insurance|admiral|aviva|direct line|rac |aa |breakdown", "insurance", "fixed"),
    (r"finance|loan|klarna|credit card", "debt_repayment", "fixed"),
    (r"\bee\b|three|vodafone|o2|bt |broadband", "phone", "fixed"),
    (r"netflix|spotify|disney|gym|licensing|prime|sky", "subscriptions", "fixed"),
    (r"railcard|stagecoach|tfl|trainline|uber", "transport", "variable"),
    (r"books|university|tuition", "education", "fixed"),
    (r"tesco|sainsbury|asda|aldi|lidl|morrisons|co-op", "groceries", "variable"),
    (r"shell|esso|bp |texaco", "fuel", "variable"),
    (r"kwik fit|halfords|garage", "vehicle", "variable"),
    (r"boots|pharmacy|superdrug", "health", "variable"),
    (r"deliveroo|just eat|uber eats|cafe|mcdonald|nando", "eating_out", "optional"),
    (r"bar|pub|crown|club|revolution", "going_out", "optional"),
    (r"amazon|asos|argos|john lewis|next|zara|garden", "shopping", "optional"),
    (r"heart foundation|charity|oxfam", "charity", "fixed"),
    (r"transfer (to|from) savings|savings", "savings_transfer", "transfer"),
]
MCC = {"5411": ("groceries", "variable"), "5541": ("fuel", "variable"), "5812": ("eating_out", "optional"),
       "5813": ("going_out", "optional"), "4900": ("utilities", "fixed"), "6300": ("insurance", "fixed")}


def categorise(name, credit, code=None, mcc=None):
    text = f" {name.lower()} "
    for pat, cat, kind in RULES:
        if re.search(pat, text):
            if kind == "income" and not credit:
                continue
            if credit and kind not in ("income", "transfer"):
                continue
            return cat, kind
    if mcc in MCC and not credit:
        return MCC[mcc]
    if credit:
        return ("other_income", "income")
    if code in ("DD", "SO"):  # direct debits / standing orders are bills
        return ("bills_other", "fixed")
    return ("other", "variable")


def _amount(obj):
    a = float(obj["Amount"]["Amount"])
    return a if obj.get("CreditDebitIndicator", "Credit") == "Credit" else -a


def from_open_banking(transactions_json, balances_json, savings_balances_json=None, profile=None,
                      customer_id="ob-customer", name="Customer"):
    rows = []
    for t in transactions_json["Data"]["Transaction"]:
        if t.get("Status", "Booked") != "Booked":
            continue
        merchant = (t.get("MerchantDetails") or {}).get("MerchantName") or t.get("TransactionInformation", "")
        credit = t["CreditDebitIndicator"] == "Credit"
        cat, kind = categorise(merchant, credit, (t.get("ProprietaryBankTransactionCode") or {}).get("Code"),
                               (t.get("MerchantDetails") or {}).get("MerchantCategoryCode"))
        rows.append({"id": t["TransactionId"], "date": t["BookingDateTime"][:10], "amount": _amount(t),
                     "merchant": merchant, "category": cat, "kind": kind})
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

    bal = next(b for b in balances_json["Data"]["Balance"] if b["Type"] in ("InterimAvailable", "ClosingBooked", "InterimBooked"))
    current = _amount(bal)
    if bal["Type"] == "InterimAvailable":  # available includes the overdraft; take it back out
        current -= sum(float(c["Amount"]["Amount"]) for c in bal.get("CreditLine", []) if c.get("Included"))
    limit = sum(float(c["Amount"]["Amount"]) for c in bal.get("CreditLine", []) if c.get("Type") == "Pre-Agreed")

    sav_hist, sav_now = [], 0.0
    if savings_balances_json:
        sav_now = _amount(savings_balances_json["Data"]["Balance"][0])
        sav_hist = savings_balances_json.get("History", [])
    customer = {"id": customer_id, "name": name, "persona": "Open Banking customer", "profile": profile or {},
                "account": {"current_balance": round(current, 2), "overdraft_limit": limit,
                            "savings_balance": sav_now, "savings_product": None, "savings_rate": 0.0},
                "savings_history": sav_hist or [{"month": "now", "balance": sav_now}]}
    return df, customer


# ---------------------------------------------------------------- export demo data in Open Banking format
def to_open_banking(df, customer):
    code = {"income": "BGC", "fixed": "DD", "transfer": "TFR"}
    tx = [{"AccountId": f"{customer['id']}-current", "TransactionId": r["id"],
           "CreditDebitIndicator": "Credit" if r["amount"] > 0 else "Debit", "Status": "Booked",
           "BookingDateTime": f"{r['date']}T00:00:00+00:00",
           "Amount": {"Amount": f"{abs(r['amount']):.2f}", "Currency": "GBP"},
           "TransactionInformation": r["merchant"].upper(),
           "ProprietaryBankTransactionCode": {"Code": code.get(r["kind"], "POS"), "Issuer": "NatWest"},
           "MerchantDetails": {"MerchantName": r["merchant"]}} for r in df.to_dict("records")]
    a = customer["account"]
    bal = {"Data": {"Balance": [{"AccountId": f"{customer['id']}-current", "Type": "ClosingBooked",
                                 "CreditDebitIndicator": "Credit" if a["current_balance"] >= 0 else "Debit",
                                 "Amount": {"Amount": f"{abs(a['current_balance']):.2f}", "Currency": "GBP"},
                                 "CreditLine": [{"Included": False, "Type": "Pre-Agreed",
                                                 "Amount": {"Amount": f"{a['overdraft_limit']:.2f}", "Currency": "GBP"}}]}]}}
    sav = {"Data": {"Balance": [{"AccountId": f"{customer['id']}-savings", "Type": "ClosingBooked",
                                 "CreditDebitIndicator": "Credit",
                                 "Amount": {"Amount": f"{a['savings_balance']:.2f}", "Currency": "GBP"}}]},
           "History": customer["savings_history"]}
    return {"Data": {"Transaction": tx}}, bal, sav


if __name__ == "__main__":
    import json
    from pathlib import Path
    data = Path(__file__).parent / "data"
    out = data / "openbanking"
    out.mkdir(exist_ok=True)
    for c in json.loads((data / "customers.json").read_text()):
        df = pd.read_csv(data / f"{c['id']}_transactions.csv")
        tx, bal, sav = to_open_banking(df, c)
        for nm, obj in (("transactions", tx), ("balances", bal), ("savings", sav)):
            (out / f"{c['id']}_{nm}.json").write_text(json.dumps(obj, indent=1))
        # round trip: does our categoriser recover the right categories without the labels?
        back, cust = from_open_banking(tx, bal, sav, c["profile"], c["id"], c["name"])
        merged = back.merge(df[["id", "category", "kind"]], on="id", suffixes=("", "_true"))
        acc = (merged["category"] == merged["category_true"]).mean()
        kacc = (merged["kind"] == merged["kind_true"]).mean()
        print(f"{c['id']:9s} category accuracy {acc:.0%}  kind accuracy {kacc:.0%}  balance {cust['account']['current_balance']}  od {cust['account']['overdraft_limit']}")
        wrong = merged[merged["category"] != merged["category_true"]].drop_duplicates("merchant")
        if len(wrong):
            print("   mismatches:", list(zip(wrong.merchant, wrong.category, wrong.category_true))[:8])
