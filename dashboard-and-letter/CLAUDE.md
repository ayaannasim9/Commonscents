# Common Cents

Hackathon project for the NatWest financial inclusion challenge.

**One-liner:** Common Cents keeps offline customers connected to their money, through paper and people, with AI working behind the scenes.

Older customers who don't use banking apps get a plain-English monthly letter (overview, 3-month forecast, scam watch, tear-off question slip). The same information is shown visually on **one shared dashboard** that Margaret and her in-person helper look at together, at the hub or Post Office counter, and that Margaret can also open herself if she wants to. Any question she asks, through any channel, becomes one case in a helper queue. AI prepares each case and drafts every reply; a human approves before anything reaches her. The next letter and the dashboard both confirm what was agreed, closing the loop.

**The letter and the dashboard are two views of the same thing.** The letter describes it in words; the dashboard shows it visually. Margaret never _has_ to use a screen (the letter always arrives), but she's never shut out of one either. Helper-only tools (case queue, notes, approval) sit alongside the shared dashboard, not inside it.

---

## Non-negotiable principles

These are the product's ethics and the judges will probe them. Code must enforce them, not just mention them.

1. **Code does the maths, the LLM only writes.** Every figure (totals, forecasts, flags) is computed deterministically in Python. The LLM receives a facts object and turns it into words. It never calculates.
2. **Number guardrail.** After the LLM writes a letter or reply, code extracts every £ amount from the text and checks each appears in the facts object. Any mismatch → regenerate (max 2 retries), then fail loudly. Never ship a letter with an unverified number.
3. **Human approval gate.** Nothing customer-facing is "sent" without a helper clicking approve. Drafts and sent items are separate states.
4. **The AI never decides.** Scam flags inform, they don't block. No recommendations framed as financial advice; scenarios and information only, with signposting (MoneyHelper, Citizens Advice).
5. ~~Trusted person gets alerts, never access.~~ **Dropped: family alerts and the trusted person are out of scope** (see `plan.md` 0.15).
6. **Letters never ask for anything risky.** No links, no QR codes, no phone numbers other than "the number on the back of your bank card", never requests details. Scammers will copy the format.
7. **Transparency.** Every case view access is logged. A "What we know about you" page lists all data held on the customer and who viewed it.
8. **No commercial use.** No upsell, credit or marketing logic anywhere in the codebase.
9. **Letter and dashboard can never disagree.** Both are rendered from the same facts object. No figure or status may be computed separately for either view.
10. **What Margaret sees, the helper sees.** The shared dashboard is identical for both. The helper gets extra tools next to it, never a different version of her money.

---

## Stack

- **Backend:** Python 3.11+, FastAPI, Pydantic models, SQLite (via SQLModel or plain sqlite3; keep it simple)
- **Frontend:** React + Vite + TypeScript, plain CSS or Tailwind
- **LLM:** Claude API via the official `anthropic` Python SDK. Model and key from env (`ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`)
- **PDF letters:** WeasyPrint or ReportLab (HTML template → PDF preferred so the letter and the on-screen preview share one template)

---

## Mock data

### Persona: Margaret

```json
{
  "id": "MRG-4471",
  "name": "Margaret",
  "age": 81,
  "bank": "NatWest",
  "hub_day": "Tuesday",
  "preferences": { "large_print": true, "language": "en" }
}
```

### Generator

Generate 18 months of transactions ending at the demo "current month". Seeded RNG so output is reproducible.

Transaction shape:

```json
{
  "id": "tx_0001",
  "date": "2026-01-03",
  "description": "DD BGAS 4421 ENERGY",
  "amount": -145.0,
  "channel": "direct_debit"
}
```

Margaret's normal life:

- State Pension every 4 weeks, small work pension monthly
- Rent, council tax, TV/phone by direct debit, fixed amounts (council tax 10 months/year)
- Gas: seasonal, roughly double November–March
- £40 cash every Friday at the Post Office (`POST OFFICE CNTR WDL`)
- Small card spends at a local shop and pharmacy
- Annual items: TV licence, an April price rise on phone
- Descriptions deliberately cryptic so decoding is visible

**Planted events** (toggled by flags, used live in the demo):

- `scam_transfer`: £2,000 faster payment to a new payee at 21:14, after no similar payment in history
- `forgotten_subscription`: new recurring £9.99 card payment she likely doesn't know about
- `price_rise`: a bill jumps by 15%+

Generator exposes `generate(persona, months=18, events=[...]) -> list[Transaction]`.

---

## Pipeline

All deterministic except where marked LLM.

1. **Categorise** — a merchant lookup table maps description patterns to `{ plain_name, category }`. Unknown descriptions → LLM fallback, result cached.
2. **Summarise** — last full month: total in, top outgoings by plain name, cash withdrawn, left over. Round to whole pounds.
3. **Forecast** — next 3 months: known recurring items + seasonal average per category from the same months last year. Output per month: `status` (`ok` / `warn` / `short`), main reason, extra cost, expected spare.
4. **Anomalies** — compare against her own history: new payee + amount > 3× her typical outgoing + unusual hour → flag with human-readable reasons.
5. **Facts object** — single Pydantic model that is the _only_ input to the writer:

```json
{
  "customer": {
    "name": "Margaret",
    "reference": "MRG-4471",
    "bank": "NatWest",
    "hub_day": "Tuesday"
  },
  "headline_status": "good",
  "last_month": {
    "in": 1240,
    "out": [{ "name": "Rent", "amount": 620 }],
    "cash": 160,
    "left": 215
  },
  "forecast": [
    {
      "month": "January",
      "status": "warn",
      "reason": "gas",
      "extra": 60,
      "spare": 150
    }
  ],
  "suggestion": { "text_hint": "save for January heating", "amount": 20 },
  "flags": [],
  "since_last_visit": {
    "helper": "Daria",
    "note": "Set up heating pot, £20/month"
  },
  "cash_blind_spot": true
}
```

---

## LLM usage

Keep every prompt in one prompts module. Every call returns structured output where possible.

- **Letter writer** — facts object → letter sections. Rules in the prompt: one page, plain English, reading age ~9, warm not patronising, names not codes, whole pounds, no percentages, at most one suggestion, mention the cash blind spot if set, never include links/phone numbers/requests. Same section order every month: headline, last month, next three months, one idea (optional), scam watch, since your last visit, question slip.
- **Triage** — incoming question (typed, or OCR'd slip text) → `{ category, urgency, summary }`. Urgency `high` if it mentions calls, texts, someone asking for money, or the "worried" box is ticked.
- **Case prep** — facts + question → helper briefing: what she's asking, relevant numbers (pulled from facts, scenario maths done in code), open flags, suggested things to check or mention.
- **Reply drafter** — case + helper's notes → short reply letter for the customer. Same guardrails as the monthly letter.

Guardrails:

- `check_numbers(text, facts)` — every £ figure in the text must exist in the facts (allow rounding to the pound).
- `check_banned(text)` — no URLs, no phone numbers, no "click", "verify your details", "urgent action".
- Both run on every customer-facing draft. Failures are logged and shown in the dashboard as a small "guardrail caught this" badge (good demo moment).

---

## Cases

Case states: `new → prepared → with_helper → draft_ready → approved → closed`

Case sources (all produce the same case shape): `slip_post_office`, `slip_post`, `counter_verbal`, `hub_visit`, `phone`, `system_flag`.

Routing (simple rules, not ML):

- `urgency == high` → phone team, due today
- otherwise → her bank's community banker on her next hub day

On case close, the helper's note is stored and appears in the next letter's "since your last visit".

---

## API (FastAPI)

```
GET  /customers/{id}                      profile
GET  /customers/{id}/transactions         raw statement
POST /customers/{id}/events               { "event": "scam_transfer" } inject a planted event
GET  /customers/{id}/facts                computed facts object
GET  /customers/{id}/dashboard            facts + plain-language section text for the shared dashboard
POST /customers/{id}/letter               generate letter draft (runs guardrails)
GET  /customers/{id}/letter.pdf           rendered PDF of latest approved letter
GET  /customers/{id}/what-we-know         transparency page data

GET  /cases?status=...                    helper queue
POST /cases                               create a case { source, text, ticks[] }
GET  /cases/{id}                          case view (logs access)
POST /cases/{id}/note                     helper note
POST /cases/{id}/draft-reply              AI reply draft
POST /cases/{id}/approve                  human approval gate

GET  /personas                            the six demo personas (see personas.md)
POST /demo/reset                          reset to clean demo state
```

---

## Frontend

Large, clean, accessible UI. Real accessibility: semantic HTML, keyboard navigable, high contrast, large text by default (minimum 18px body), read-aloud button on every section, no jargon, no dense tables on Margaret-facing screens.

### 1. Shared dashboard (the hero screen)

The visual version of the letter. Same sections, same order, same numbers:

- **Headline** — one sentence and a single status colour/icon
- **Last month** — money in, main outgoings by plain name, cash, left over. Simple bars, not a chart library showcase
- **Next three months** — three large month cards with ✓ / ⚠ / ✗, the reason in words, expected spare money
- **One idea** — at most one suggestion
- **Scam watch** — "nothing unusual" or the flag explained in plain words
- **Since your last visit** — the helper's agreed actions
- **Ask a question** — shows the same options as the tear-off slip; creates a case

Used two ways:

- **Together at the counter:** the helper turns the screen (or a tablet) towards Margaret and they go through it side by side
- **Margaret on her own** (optional): a simple login on a home tablet or a family member's device. Never required

Must look calm and familiar month to month: fixed layout, nothing moves around.

### 2. Helper panel (helper-only, next to the dashboard)

When the helper is signed in, the shared dashboard stays exactly as Margaret sees it, with a side panel:

- her open question and the AI-prepared briefing (relevant numbers, flags, things to check)
- notes box, "Draft reply", editable draft, "Approve"
- role indicator (banker / Post Office / phone)

### 3. Helper queue

List of cases with source icon, urgency, summary, due date. Urgent cases on top. Opening a case opens the shared dashboard with the helper panel.

### 4. Statement vs letter (demo only)

Left: raw transactions with cryptic descriptions. Right: the letter and the dashboard (toggle). Buttons: "Inject scam transfer", "Inject forgotten subscription", "Next month", "Regenerate". Guardrail badge when it fires.

### 5. Persona gallery (replaces family alert)

Six personas, same product, different transaction data. See `personas.md` and `plan.md` F7.

### 6. What we know

Everything held about Margaret and an access log. Printable. Visible to Margaret and the helper.

---

## Demo script (target 3 minutes)

1. Raw statement next to Margaret's letter, then flip to the shared dashboard: same story, words vs visuals.
2. Click "Inject scam transfer" → letter and dashboard scam watch both change, an urgent case appears in the queue.
3. Open a slip case ("Can I afford a new boiler?") → the shared dashboard opens with the helper panel. "This is what Margaret and Daria look at together at the counter." Type a note, draft reply, approve.
4. Click "Next month" → letter and dashboard both show "Since your last visit" with the note.
5. Ten seconds on What We Know.
6. Close: "We didn't make Margaret go digital. We gave her and the people around her the same clear picture, on paper and on screen."

`POST /demo/reset` must return everything to the clean starting state so the demo can be rerun.

---

## Build order

1. Persona + generator + merchant lookup. Print a month of transactions to check the story reads right.
2. Summarise, forecast, anomalies, facts object. Unit-test the numbers. No LLM yet.
3. LLM letter writer + guardrails. Letter preview as HTML.
4. Shared dashboard rendered from the same facts object, plus the Statement vs Letter page with event buttons.
5. Cases: model, service, triage, case prep, queue + helper panel beside the dashboard.
6. Approval gate, notes feeding the next letter and dashboard, "next month" button.
7. Persona gallery, What We Know page, PDF export, read-aloud.
8. Demo reset, polish, rehearse.

If time runs short, stop after step 6: that already demonstrates the full loop.

---

## Conventions

- Money stored as integer pence internally; formatted to whole pounds only at the facts/output stage.
- All dates in Europe/London.
- No real customer data, ever. Everything is generated.
- Prompts live in one prompts module, not inline.
- Keep LLM calls behind a single client wrapper so we can stub them for tests and for an offline demo fallback (cached outputs).
- British English in all customer-facing text.

## Out of scope

- Real bank integration or Open Banking connections
- Authentication beyond a role switcher for the demo (customer / helper), plus a demo persona picker
- A native mobile app; the shared dashboard is a web page that works on a tablet
- Actually sending SMS or post
