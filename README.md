# Common Cents: Financial Time Travel

Most banking tools explain where money went. Common Cents predicts where financial hardship may happen next, and helps people act before it does, in whatever way suits them: app, paper letter, a human helper, or lessons.

Built at GreatUniHack 2026 for the **NatWest: AI-Powered Financial Inclusion & Resilience** challenge. All people and figures are made up.

## Run everything

```bash
./start.sh
```

| App | URL | Folder | Owner |
|---|---|---|---|
| **Main app (start here)**: onboarding, 5-year timelines, Wrapped, Learn, Support, Report | http://localhost:8001 | `Overview/` | Martins |
| **ML engine + API + printable report** | http://localhost:8001/docs | `ml/` | Animesh |
| **Dashboard & letters**: plain-English letter, helper queue, scam watch | http://localhost:5173 | `dashboard-and-letter/` | Daria |
| **Learning module**: life-situation lessons and quizzes | http://127.0.0.1:3000 | `app/`, `lib/`, `supabase/` | Ayaan |

Needs Python 3.11+ and Node 20+. `start.sh` installs what's missing on first run.

### API keys (optional, never commit them)
- `ml/.env`: `ANTHROPIC_API_KEY=...` turns on Claude-written alerts in the forecast report (rule-based without it).
- `dashboard-and-letter/.env`: `ANTHROPIC_API_KEY`, `LLM_MODE=live` turns on Claude-written letters (template writer without it).
- `.env.local` (root): Supabase URL and server key for the learning module (see `LEARNING_MODULE.md`). Without it the module shows a preview.

## How the parts connect

```
onboarding answers (Overview) ─┐
                               ▼
bank transactions ──► ML engine (ml/) ──► 5-year timelines A/B/C ──► Overview Future tab
(NatWest Open Banking format)  │                                   ► recommendations ("Do this next")
                               ├──► Claude alerts + 4-page A4 report ─► Overview Report tab
                               └──► JSON API (/customers/{id}/insights) for other front ends
```

The Overview app is served by the ML API, and `Overview/ml-bridge.js` swaps its example data for live forecasts. Pick Jordan, Priya or Margaret with the **Demo customer** menu.

## What the ML engine does (`ml/`)
- **Cashflow forecast**: 1,000 simulated futures per customer (7 days to 12 months) with ranges and confidence
- **Hardship risk** with explainable drivers, **upcoming expenses**, **opportunities**
- **Onboarding answers** (goal, worry, life changes, £500 shock, optional support needs) change the forecast
- **Action planner**: an optimiser that finds the smallest changes with the biggest risk reduction
- **Safe-to-spend**, **backtest** (35–77% more accurate than simple baselines), **behaviour signals**, **life-stage** tips
- **Support preferences** (anxiety, simple language, impulse spending, gambling, bill tracking) change presentation only and are never used in scoring
- Reads **UK Open Banking v3.1** (NatWest's API format)

Details: [`ml/README.md`](ml/README.md).

## Ethics
Guidance only: nothing moves money or blocks payments. No protected characteristics are used, and mental health is never inferred. Recommendations under 60% confidence are hidden. Every number Claude writes comes from the models.
