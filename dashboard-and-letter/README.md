# Common Cents

Keeps offline customers connected to their money, through paper and people, with AI working behind the scenes.
A plain-English monthly letter and one shared dashboard show the same facts. Questions become cases, AI drafts, a human approves.

> Prototype for the NatWest financial inclusion challenge. Not an official NatWest product. All people, names and figures are made up.

## Quick start

For the integrated application, use the repository root: `npm install`, `npm run setup:dashboard`, then `npm run dev`, and open http://127.0.0.1:3000. Dashboard and Report share the overview navigation and accessibility controls. The commands below are for the standalone reference application.

You need Python 3.11+, [uv](https://docs.astral.sh/uv/), and Node 20+.

```bash
cp .env.example .env     # then add your API key, see below (optional)
make setup               # one-off: Python venv + frontend packages
make run                 # backend :8000 + frontend :5173 together, Ctrl+C stops both
```

Open **http://localhost:5173**.

With no API key it still works: the letter text comes from a built-in template writer (`LLM_MODE=stub`).

## Commands

| Command | What it does |
|---|---|
| `make setup` | One-off install: Python venv (with PDF support) and frontend packages |
| `make run` | Backend and frontend together |
| `make dev` | Backend only, http://localhost:8000 (API docs at `/docs`) |
| `make frontend` | Frontend only against the live backend, http://localhost:5173 |
| `make test` | Backend tests |
| `make reset` | Put the running demo back to its clean start (same as the Reset button on the Demo page) |
| `make print-month ARGS="--persona AMR-3135"` | Print a month of transactions and the facts JSON for review (`--event scam_transfer` also works) |
| `make openapi` | Re-export `contract/openapi.json` |

## API key setup (optional)

The key lets Claude write the letter, dashboard text, case briefings and reply drafts. All numbers are still worked out by code, and every number Claude writes is checked against the facts before it is shown.

1. Create a key at https://console.anthropic.com/ (Settings, API keys).
2. Copy the example file and edit it:
   ```bash
   cp .env.example .env
   ```
3. In `.env` set:
   ```
   ANTHROPIC_API_KEY=your-key-here
   ANTHROPIC_MODEL=claude-sonnet-5-5
   LLM_MODE=live
   ```
4. Restart `make run`.

`.env` is git-ignored. Never commit a real key.

### LLM modes (`LLM_MODE`)

| Mode | Behaviour |
|---|---|
| `stub` (default) | Never calls the API. Built-in template writer. Free, fast, works offline. |
| `live` | Asks Claude, saves each answer in `backend/cache/`. Repeat runs of the same facts are free. If the API fails it falls back to templates. |
| `cached` | Replays saved answers only, never calls out. Use it for the stage demo when wifi is unreliable: run once in `live` first. |

Tip: rehearse the demo once with `live` so the cache is warm, then switch to `cached` for the real thing.

## What to click

1. Click **Helper** in the top-right switch. This unlocks the helper pages.
2. **People**: six different customers, same product. Click a card to open that person's dashboard.
3. **Demo**: the bank statement next to the letter and dashboard. Buttons: inject a scam transfer, a forgotten subscription or a price rise, **Next month**, **Regenerate**, **Plant a wrong number** (watch the guardrail catch it), **Reset demo**.
4. **Questions**: the helper queue. Open a case to see the dashboard with the helper panel beside it: notes, draft reply, approve.
5. **Letter**: the letter as it arrives on paper. Approve it, then open the PDF.
6. **What we know**: everything held about the customer and who has looked.

### Suggested 3-minute run

1. Demo page: statement next to the letter, then the dashboard (same story, words and visuals).
2. **Inject scam transfer**: the Scam watch changes in both and an urgent case appears.
3. Questions: open the boiler question, add a note, draft a reply, approve.
4. **Next month**: "Since your last visit" shows the note in the letter and the dashboard.
5. What we know, then close.

Use **Reset demo** between runs.

## Troubleshooting

- **Page says it could not load / empty people list:** check that the backend is running on port 8000. Use `npm run dev` from the repository root for the integrated app.
- **`make setup` fails on `uv`:** install it with `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- **PDF returns an error:** install the portable ReportLab dependency with `npm run setup:dashboard` from the repository root. Final PDFs require approval; preview PDFs are available before approval.
- **Port already in use:** `lsof -ti:8000 | xargs kill` (or `:5173`).
- **Old names or data after pulling changes:** run `make reset`, or delete `backend/counterpart.db` and restart.
- **Live mode shows template wording:** `ANTHROPIC_API_KEY` or `ANTHROPIC_MODEL` is missing or wrong in `.env`, so it fell back to templates.

## Project layout

```
backend/    FastAPI, deterministic maths, guardrails, LLM wrapper (Python package: counterpart)
frontend/   React + Vite + TypeScript, plain CSS
contract/   openapi.json and fixtures: the seam between backend and frontend
CLAUDE.md   product rules and non-negotiable principles
PRODUCT.md  users, purpose, constraints
personas.md the six people and their data
plan.md     build plan and contract
```
