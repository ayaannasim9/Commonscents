# Common Cents – ML engine

Predicts a customer's future balance, hardship risk, upcoming big expenses and money-saving opportunities from their transactions.

## Run it

```bash
cd ml
python3 generate_data.py              # makes fake bank data for 3 demo customers (already done)
uvicorn api:app --reload --port 8000  # start the API
```

Open http://localhost:8000/docs to try it in the browser.

## Endpoints

| Call | What it returns |
|---|---|
| `GET /customers` | The 3 demo customers: `priya` (student), `jordan` (hours cut, struggling), `margaret` (retired, stable) |
| `GET /customers/{id}/insights` | Everything below for one customer |
| `POST /analyse` | Same output for any customer + transaction list you send |

**Frontend: you don't need the server running to start.** Example responses are in `sample_outputs/priya.json`, `jordan.json` and `margaret.json`.

## What's in the response

| Field | Use it for |
|---|---|
| `cashflow_forecast.horizons` | 7 / 30 / 90 / 180-day cards: `predicted_balance`, `range_low`–`range_high`, `confidence` (0–1) |
| `cashflow_forecast.series` | Forecast chart: `dates` with `p10` (bad case), `p50` (expected), `p90` (good case) for 180 days. Draw p10–p90 as a shaded band, p50 as a line |
| `history.balance_last_90d` | The real past balance, to draw before the forecast starts |
| `cashflow_forecast.depletion` | "Likely to go below £0 on …" and the % chances |
| `hardship_risk` | `score` (0–1), `level` (low/medium/high), `confidence`, top 3 `drivers` with a plain-English `detail`, and `what_if` (effect of £200 extra savings) |
| `upcoming_expenses` | Model 3 cards: `type`, `expected_cost_low/high`, `timeframe`, `confidence`, `why` |
| `opportunities` | Model 4 cards: `opportunity`, `estimated_benefit_annual`, `action`, `confidence`, `why` |
| `features` | Raw numbers (income, spending, savings rate, spending by category…) for charts or the Claude insight layer |
| `history.monthly` | Income vs spending per month, for a bar chart |

Anything with confidence below 60% is already removed (Safety & Ethics rule).

## How the models work (for the pitch)

1. **Cashflow forecast:** finds regular income and bills from payment patterns (weekly, monthly, yearly). It then simulates 1,000 possible futures, drawing day-to-day spending from the customer's own history with seasonal effects (Christmas, summer) and inflation. The percentiles of those futures give the range and confidence.
2. **Hardship risk:** an explainable logistic score built from the forecast (chance of going past the overdraft or below £0), overdraft use, falling savings, falling income, rising bills and emergency fund size. Every factor maps to a sentence the customer can read.
3. **Future expenses:** yearly bills seen last year (insurance, licences, railcards), raised by inflation, plus seasonal spikes and winter energy.
4. **Opportunities:** rules for savings rates, emergency funds, subscriptions, benefits checks and free debt advice.

Never uses protected characteristics, only transactions and balances. Guidance only: it never moves money or blocks spending.

The economic figures in `ASSUMPTIONS` (in `model.py`) are placeholders and should be swapped for real ONS / Bank of England figures if there's time.

## New: onboarding answers, printable report, NatWest / Open Banking data

### The 4 onboarding questions change the forecast
Send the user's answers (exact button labels are fine):
```json
{"goal": "Buy a home", "worry": "Job security", "life_changes": ["New job", "Moving home"],
 "life_change_dates": {"Moving home": "2027-03-01"}, "shock_500": "Credit card"}
```
- `POST /customers/{id}/insights` with that body, or `GET /customers/{id}/insights?goal=...&worry=...&life_changes=New job,Moving home&shock_500=...`
- **Goal** → `goal_plan` (target, monthly amount, months to reach it, what-if) and goal-matching `opportunities` first
- **Worry** → `headline` (a direct answer to their worry) and `priority_sections` (which dashboard sections to show first)
- **Life changes** → applied inside the forecast (e.g. graduation stops student loan payments; new child adds monthly costs). Chart both `series.p50` and `series.p50_without_life_changes`
- **£500 question** → feeds the hardship score, `stress_tests.surprise_bill_500`, and `data_checks` (flags answers that don't match the account)

### Printable report
`GET /customers/{id}/report` (same query params) returns a 4-page A4 report (forecast · alerts & stress tests · coming up & opportunities · your plan). Open it and press **Print / Save as PDF**.
Examples: `sample_outputs/*_report.html` and `*_report.pdf`.

### NatWest data
NatWest's Bank of APIs uses the UK Open Banking v3.1 format. `POST /analyse/openbanking` takes the raw
`/transactions` and `/balances` responses, categorises transactions itself and runs every model.
Demo customers in that format: `data/openbanking/`. Categoriser accuracy on them: 86–99% by category, 100% by type.

### Claude alerts (Section 5 insight layer)
Every `/insights` and `/report` response now has `insights`: a `summary` plus 3–5 `alerts`
(`kind`, `title`, `message`, `why`, `confidence`, `action`) written by Claude (`claude-opus-5-5`) from the model output.
- Needs `export ANTHROPIC_API_KEY=...` in the terminal that runs uvicorn (`pip install anthropic`). Never commit the key.
- No key or an API error → rule-based alerts from the same data (`insights.source` is `"rules"` instead of `"claude"`), so the demo can't break.
- Results are cached per customer + answers, so repeated demo clicks don't spend credits.

### API key
Put `ANTHROPIC_API_KEY=...` in `ml/.env` (git-ignored); `api.py` loads it automatically.

## Advanced layer (`advanced.py`) → `advanced` in every response

| Field | What it is |
|---|---|
| `action_plan` | **Optimiser.** Greedy search over the 1,000 simulated futures: tries cutting each optional category (10–50%), moving each bill to just after payday, pausing subscriptions, stopping gambling spend, and picks the smallest set of changes with the biggest risk reduction per unit of effort. `before` / `after` metrics + ordered `steps` |
| `safe_to_spend` | Daily amount until next payday with an 80% chance of staying above £0 (or within the overdraft if that isn't realistic) |
| `backtest` | Model re-run from 60/90/120 days ago and scored against what really happened vs simple guesses. Proof the forecast works (on synthetic demo data) |
| `behaviour_signals` | Payday splurge, spending spikes (robust median + MAD outliers), buy-now-pay-later, gambling, subscription count. Neutral wording |
| `life_stage` | student / young adult / family / working age / pre-retirement / retired, with stage-specific tips |
| `support` | Self-declared support needs → how we adapt + free resources. **Never used in any score** |
| `bill_calendar` | Next 30 days of bills and income with expected balance after each |

### Optional 5th onboarding question: "Would any of these help you?" (multi-select, skippable)
`"support_needs": ["Money makes me anxious", "I prefer simple explanations", "I struggle with impulse spending", "I want help with gambling", "I find it hard to keep track of bills"]`

These change only **presentation**: Claude's tone (calm / simple), the report wording ("needs attention" instead of "high"), and which help is shown.
We never infer mental health from spending. It's a protected characteristic, and our ethics section rules it out (in line with the FCA's guidance on treating vulnerable customers fairly).
