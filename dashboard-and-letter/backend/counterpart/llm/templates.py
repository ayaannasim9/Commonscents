"""Deterministic templated writer: the stub, the offline demo, and the guardrail fallback.
Same sections, same order as the LLM letter. Uses only figures from the facts."""
from __future__ import annotations

from datetime import date

from ..models import Facts

SIGNPOST = "Free, independent help is available from MoneyHelper and Citizens Advice."
NEVER = ("We will never ask for your details in a letter. If someone calls and asks you for money, "
         "put the phone down and use the number on the back of your bank card.")


def gbp(n: int) -> str:
    return f"£{abs(n):,}"


def _day(d: date) -> str:
    return f"{d.day} {d.strftime('%B')}"


def _lower(s: str) -> str:
    return s[0].lower() + s[1:]


def headline(f: Facts) -> str:
    high = [x for x in f.flags if x.severity == "high"]
    short = next((m for m in f.forecast if m.status == "short"), None)
    warn = next((m for m in f.forecast if m.status == "warn"), None)
    if high:
        return ("Something needs a look together. One payment last month does not look like your usual "
                "ones, so please go through it with your helper.")
    if short:
        return f"{short.month} may be short of money, so it is worth talking it through with your helper."
    if warn:
        why = ("because your TV licence is due" if warn.reason == "TV licence"
               else f"mainly because of {warn.reason}" if warn.extra > 0 else "because there is not much spare")
        return f"You are doing fine. {warn.month} will be a little tight {why}, so it is worth planning for."
    if f.flags:
        return "You are doing fine. There is one small thing to look at with your helper."
    return "You are doing fine. Nothing needs your attention this month."


def last_month(f: Facts) -> str:
    lm = f.last_month
    big = [i for i in lm.out if i.name != "Everything else"][:3]
    bills = ", ".join(f"{_lower(i.name)} ({gbp(i.amount)})" for i in big)
    out = f"In {lm.month}, {gbp(lm.in_)} came in. Your biggest payments were {bills}."
    if lm.cash:
        out += f" You took out {gbp(lm.cash)} in cash at the Post Office."
    out += (f" {gbp(lm.left)} more went out than came in." if lm.left < 0
            else f" You had {gbp(lm.left)} left over." if lm.left else " Nothing was left over.")
    if f.cash_blind_spot:
        out += " We cannot see what the cash was spent on."
    return out


def forecast(f: Facts) -> str:
    parts = []
    for m in f.forecast:
        if m.status == "short":
            s = f"{m.month} looks short, with about {gbp(m.spare)} less than you need"
        else:
            s = f"{m.month} looks {'tight' if m.status == 'warn' else 'comfortable' if m.spare >= 500 else 'fine'}, with about {gbp(m.spare)} spare"
        if m.reason == "two pension payments":
            s += " because you get two pension payments"
        elif m.reason == "TV licence":
            s += f", mainly because your TV licence of {gbp(m.extra)} is due"
        elif m.extra > 0:
            s += f", mainly because of {m.reason}, which is about {gbp(m.extra)} more than usual"
        parts.append(s + ".")
    return " ".join(parts)


def idea(f: Facts) -> str | None:
    if not f.suggestion:
        return None
    s = f.suggestion
    return (f"One idea is to {s.text_hint}, perhaps {gbp(s.amount)} a month. "
            f"This is only an idea, and it is your choice. {SIGNPOST}")


def scam_watch(f: Facts) -> str:
    if not f.flags:
        return f"Nothing unusual this month. Your payments all look like your normal ones. {NEVER}"
    parts = []
    for x in f.flags:
        if x.kind == "unusual_payment":
            parts.append(f"One payment does not look like your usual ones: {gbp(x.amount)} on {_day(x.date)}, "
                         f"{_lower(x.plain_name)}. " + ". ".join(x.reasons) + ". It may be fine, but please check "
                         "it with your helper. If you did not make it, use the number on the back of your bank card.")
        elif x.kind == "new_regular_payment":
            parts.append(f"A new payment of {gbp(x.amount)} started on {_day(x.date)}. It is likely to come out "
                         "every month. If you do not know what it is, ask your helper.")
        else:
            parts.append(f"{x.plain_name}. " + ". ".join(x.reasons) + ". You may want to ask your helper about it.")
    return " ".join(parts) + f" {NEVER}"


def since_visit(f: Facts) -> str:
    s = f.since_last_visit
    return "Nothing new since we last spoke." if not s else f"When we last spoke, {s.helper} agreed: {s.note.rstrip('.')}."


def ask(f: Facts) -> str:
    return (f"If you have a question, tick a box on the slip or ask your helper on {f.customer.hub_day}. "
            "Your helper or a colleague will reply by letter.")


def sections(f: Facts) -> dict[str, str]:
    out = {"headline": headline(f), "last_month": last_month(f), "forecast": forecast(f)}
    if (i := idea(f)):
        out["idea"] = i
    out |= {"scam_watch": scam_watch(f), "since_visit": since_visit(f), "ask": ask(f)}
    return out


def reply(name: str, helper: str, note: str, numbers: list[int]) -> str:
    return (f"Dear {name},\n\nThank you for your question. {note.rstrip('.')}.\n\n{SIGNPOST}\n\n"
            f"With best wishes,\n{helper}")
