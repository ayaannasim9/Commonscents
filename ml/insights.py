"""Section 5 – Insight Generation Layer.

Turns the ML output into short, plain-English alerts with "why", confidence and a suggested action,
using Claude. If no API key is set (or the call fails) it falls back to rule-based alerts built from
the same data, so the demo never breaks.

Needs ANTHROPIC_API_KEY in the environment (never hard-code it).
"""
import json
import os

import anthropic

MODEL = "claude-opus-5-5"
_cache = {}

SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "alerts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": ["risk", "forecast", "resilience", "opportunity"]},
                    "title": {"type": "string"},
                    "message": {"type": "string"},
                    "why": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["High", "Medium"]},
                    "action": {"type": "string"},
                },
                "required": ["kind", "title", "message", "why", "confidence", "action"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "alerts"],
    "additionalProperties": False,
}

SYSTEM = """You write the customer-facing alerts for Common Cents, a UK banking app that forecasts a customer's finances.
You receive the output of our forecasting models as JSON. Write a one-sentence summary and 3 to 5 alerts.

Rules:
- Use only numbers that appear in the data. Never invent figures, rates or dates. Round money to whole pounds.
- Put the customer's stated worry and goal first.
- Each alert: a short title; a message of one or two plain sentences in the second person; "why" that names the
  specific data behind it (the "Why am I seeing this?" line); confidence High (>= 0.8) or Medium (0.6-0.8);
  and one concrete, achievable action. Do not include anything below 0.6 confidence.
- Kinds: risk (danger ahead), forecast (what will happen), resilience (a change that lowers risk, use the what-if
  numbers), opportunity (something that improves outcomes).
- Guidance only. Never say the bank will move money, block spending or change limits. Don't promise outcomes.
- Calm, supportive, non-judgemental tone. UK spelling. No jargon such as "p50" or "Monte Carlo".
- Use "advanced": one alert should give the first 1-2 steps of action_plan with their measured effect, and use
  safe_to_spend when it helps. Mention behaviour signals factually and without blame.
- answers.support_needs are preferences the customer chose. Follow them:
  anxious -> start with something positive, say "needs attention" rather than "high risk", no more than 3 alerts;
  simple -> short sentences, at most one number per sentence, no percentages where a word will do;
  impulse -> include the safe-to-spend amount and one practical tip;
  tracking -> name the next bill dates;
  gambling (or support items offered) -> one gentle, optional mention of free help, never judgemental.
  Never mention mental health conditions or guess at them."""


def _compact(r):
    """The parts of the model output Claude needs (drop the big chart arrays)."""
    cf = r["cashflow_forecast"]
    return {
        "customer": r["customer"], "as_of": r["as_of"], "account": r["account"], "answers": r.get("answers"),
        "headline": r.get("headline"),
        "forecast": {"horizons": cf["horizons"], "depletion": cf["depletion"], "life_changes": cf.get("life_changes", []),
                     "next_scheduled": cf.get("scheduled_payments", [])[:8]},
        "hardship_risk": r["hardship_risk"], "stress_tests": r.get("stress_tests"), "goal_plan": r.get("goal_plan"),
        "upcoming_expenses": r["upcoming_expenses"], "opportunities": r["opportunities"],
        "data_checks": r.get("data_checks", []),
        "features": {k: v for k, v in r["features"].items()},
        "advanced": {k: v for k, v in r.get("advanced", {}).items() if k != "bill_calendar"}
                    | {"bill_calendar_next_30_days": r.get("advanced", {}).get("bill_calendar", [])[:10]},
    }


def _fallback(r):
    """Rule-based alerts from the same data (no API call)."""
    hr, out = r["hardship_risk"], []
    conf = lambda c: "High" if c >= 0.8 else "Medium"
    if hr["drivers"]:
        out.append({"kind": "risk", "title": f"{hr['level'].capitalize()} risk of money trouble",
                    "message": f"Your hardship risk is {round(hr['score'] * 100)}%.", "why": hr["drivers"][0]["detail"],
                    "confidence": conf(hr["confidence"]), "action": "Look at the forecast chart and the ideas below."})
    for e in r["upcoming_expenses"][:2]:
        out.append({"kind": "forecast", "title": e["type"], "message": f"Expect about £{e['expected_cost_low']:,}–£{e['expected_cost_high']:,} ({e['timeframe']}).",
                    "why": e["why"], "confidence": conf(e["confidence"]), "action": "Set this amount aside before it's due."})
    if hr["what_if"]["risk_reduction_pct"] > 0:
        out.append({"kind": "resilience", "title": "A small buffer helps",
                    "message": f"£200 more in savings would lower your risk from {round(hr['score'] * 100)}% to {round(hr['what_if']['new_score'] * 100)}%.",
                    "why": "Based on 1,000 simulated futures of your account.", "confidence": "Medium", "action": "Set up a small automatic transfer on payday."})
    for o in r["opportunities"][:1]:
        out.append({"kind": "opportunity", "title": o["opportunity"], "message": o["action"], "why": o["why"],
                    "confidence": conf(o["confidence"]), "action": o["action"]})
    return {"summary": r.get("headline") or "", "alerts": out, "source": "rules"}


def generate(r, cache_key=None):
    if cache_key and cache_key in _cache:
        return _cache[cache_key]
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        return _fallback(r)
    try:
        client = anthropic.Anthropic()
        resp = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": json.dumps(_compact(r), default=str)}],
        )
        if resp.stop_reason in ("refusal", "max_tokens"):
            return _fallback(r) | {"note": f"Claude stopped: {resp.stop_reason}"}
        text = next(b.text for b in resp.content if b.type == "text")
        out = json.loads(text) | {"source": "claude", "model": resp.model}
    except anthropic.AuthenticationError:
        return _fallback(r) | {"note": "Invalid ANTHROPIC_API_KEY"}
    except anthropic.RateLimitError:
        return _fallback(r) | {"note": "Rate limited, used rule-based alerts"}
    except (anthropic.APIStatusError, anthropic.APIConnectionError, StopIteration, json.JSONDecodeError) as e:
        return _fallback(r) | {"note": f"Claude unavailable ({type(e).__name__}), used rule-based alerts"}
    if cache_key:
        _cache[cache_key] = out
    return out
