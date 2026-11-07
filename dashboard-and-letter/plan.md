# Counterpart: dashboard-and-letter build plan

Status: **plan only, no code written yet.** Read `CLAUDE.md` (product rules, principles P1–P10) and `PRODUCT.md` (users, constraints) first. This file turns them into two parallel workstreams.

Cross-references use section IDs: `C#` = shared contract, `B#` = backend, `F#` = frontend, `D#` = demo, `P#` = CLAUDE.md principle (numbered as in CLAUDE.md "Non-negotiable principles").

---

## 0. Decisions locked in (from planning session)

| # | Decision |
|---|---|
| 0.1 | Hero message: **inclusion without forcing digital**. Paper and screen show the same picture. |
| 0.2 | Scope: **all 8 build steps**. Priority is steps 1–6 (they already show the full loop). |
| 0.3 | This service is self-contained and owns everything in CLAUDE.md. Other services in the repo do not affect it. |
| 0.4 | Layout: `backend/` (FastAPI) and `frontend/` (React + Vite + TS), one start script (`make dev`). |
| 0.5 | LLM: live Claude + on-disk cache + templated fallback if the API fails. Guardrails run on every output regardless of source. |
| 0.6 | PDF: WeasyPrint, HTML template shared with the on-screen letter preview. Check pango installs on WSL early (B7). |
| 0.7 | Auth: role switcher only (Margaret / Helper / Family). No login. |
| 0.8 | Margaret banks with **NatWest** (CLAUDE.md says Lloyds; change `persona.bank` and all mock strings). |
| 0.9 | UI styled NatWest purple + white, **calm paper-like** character. Letter itself has no logo/links (P6). |
| 0.10 | Realistic income: State Pension every 4 weeks (some months have two payments) plus small monthly work pension. |
| 0.11 | Demo date: letter dated **1 Dec 2026**; last full month is **November 2026**; forecast covers **Dec, Jan, Feb**. |
| 0.12 | Equal weight to Margaret-facing screens (calm, accessible) and a judge-facing demo page (`/demo`). |
| 0.13 | Dashboard: tablet landscape, **one scrolling page**, sections in letter order (C2.3). Helper panel docks right. |
| 0.14 | Run the `web-quality-skills-accessibility` skill (WCAG 2.2) on the finished frontend. |

Open items needing a human answer are collected in section 7.

---

## 1. Two sessions, one checkout

No worktrees. Two Claude sessions run in the same checkout on branch `daria-dashboard-and-letter`, each confined to its own directory. The backend and the Vite dev server run side by side, so integration is live.

| Session | Owns (edit) | Never touches |
|---|---|---|
| Backend session | `backend/**`, `contract/**`, `plan.md`, `Makefile` | `frontend/**` |
| Frontend session | `frontend/**` | `backend/**`, `contract/**`, `plan.md` (read-only) |

**Git rules for both sessions (non-negotiable, they share one index):**
1. Commit with explicit paths only: `git add backend/` or `git add frontend/`. Never `git add -A`, `git add .` or `git commit -a`.
2. Never run `git checkout`, `git switch`, `git stash`, `git reset` or `git rebase`. Stay on the current branch.
3. Do not commit the other side's files, even if they show as modified.
4. If you need a contract change (section C), the frontend session asks the human, who relays it to the backend session. Only the backend session edits `contract/` and `plan.md`.
5. A half-written file from the other session may break the running dev server briefly; wait and retry rather than "fixing" their directory.

**The contract is the seam.** Before either side codes, the first commit on `daria-dashboard-and-letter` adds:

```
contract/
  openapi.json            # exported from FastAPI once B0 exists; hand-written stub until then
  fixtures/               # canned JSON responses, one file per scenario (see C5)
  README.md               # points to section C of this file
```

- Frontend develops against `contract/fixtures/*.json` served by a tiny mock (MSW or a Vite dev middleware) so it never blocks on the backend. Switch with `VITE_API_MODE=mock|live`.
- Backend must make `GET`s return exactly the fixture shapes (a pytest contract test compares each live response's keys/types to the fixture, see B9).
- If either side needs a contract change: the backend session edits section C of this file and `contract/` in a **separate small commit**, then the human tells the frontend session to re-read it. Never change a shape locally.

Integration milestones are in section 6.

---

## C. Shared contract (single source of truth)

All money in API responses is **whole pounds as integers** (P1, conventions): the backend stores pence internally and rounds only when building facts. The frontend never does arithmetic on money, it only formats (`£1,240`). Dates are ISO `YYYY-MM-DD` (Europe/London). Month names are English words.

### C1. Enums

```
headline_status : "good" | "heads_up" | "attention"
forecast_status : "ok" | "warn" | "short"
flag_severity   : "info" | "medium" | "high"
role            : "margaret" | "helper" | "family"
helper_role     : "banker" | "post_office" | "phone"
case_status     : "new" | "prepared" | "with_helper" | "draft_ready" | "approved" | "closed"
case_source     : "slip_post_office" | "slip_post" | "counter_verbal" | "hub_visit" | "phone" | "trusted_person" | "system_flag"
urgency         : "high" | "normal"
case_category   : "scam_worry" | "afford_purchase" | "bill_query" | "payment_query" | "general"
event           : "scam_transfer" | "forgotten_subscription" | "price_rise"
```

### C2. Facts and dashboard

`GET /customers/{id}/facts` returns the facts object exactly as in CLAUDE.md "Pipeline step 5", with these additions: `as_of` (letter date), `customer.bank` is `"NatWest"`, `flags[]` entries below, `forecast[]` entries gain `year`, `since_last_visit` may be `null`.

Flag object:

```json
{
  "id": "flag_0001",
  "kind": "unusual_payment | new_regular_payment | price_rise",
  "severity": "high",
  "date": "2026-11-18",
  "amount": 2000,
  "plain_name": "Payment to a new person",
  "reasons": ["First time you have paid this person", "About 15 times your usual payment", "Made late in the evening"]
}
```

`GET /customers/{id}/dashboard` returns **facts plus ready-to-render plain-language text** (written by the letter writer in B4, number-checked; see P2). Frontend renders `text` strings verbatim and never builds sentences from numbers (P9).

```json
{
  "as_of": "2026-12-01",
  "facts": { "...": "facts object" },
  "guardrail": { "caught": false, "events": [] },
  "sections": [
    { "id": "headline",   "title": "How things look",        "text": "…", "status": "good" },
    { "id": "last_month", "title": "Last month",             "text": "…" },
    { "id": "forecast",   "title": "The next three months",  "text": "…" },
    { "id": "idea",       "title": "One idea",               "text": "…" , "optional": true },
    { "id": "scam_watch", "title": "Scam watch",             "text": "…", "status": "nothing_unusual | flagged" },
    { "id": "since_visit","title": "Since your last visit",  "text": "…" },
    { "id": "ask",        "title": "Ask a question",         "text": "…" }
  ]
}
```

C2.3 **Section order is fixed and identical to the letter**: headline, last_month, forecast, idea (omitted if no suggestion), scam_watch, since_visit, ask. The frontend must render them in the array order and never reorder or hide sections except `idea` when absent.

`guardrail.events[]` (for the badge, F6.4): `{ "at": ISO datetime, "check": "numbers|banned", "detail": "£2,400 not in facts", "action": "regenerated|blocked" }`.

### C3. Customers, transactions, events, demo

```
GET  /customers/{id}                 -> { id, name, age, bank, hub_day, trusted_person{name,relation,level}, preferences{large_print,language} }
GET  /customers/{id}/transactions    -> { month, transactions:[{id,date,time|null,description,amount,channel}] }   # amount signed pounds, 2dp, as in CLAUDE.md
POST /customers/{id}/events          { "event": "<event enum>" } -> { facts_version, new_flags:[flag], new_case_id|null }
POST /demo/next-month                -> { as_of }       # advances as_of by one month, keeps history stable
POST /demo/reset                     -> { as_of }
GET  /demo/state                     -> { as_of, events_applied:[...], facts_version }
```

`facts_version` is an integer bumped on any change (event, approved case, next-month); frontend uses it to refetch.

### C4. Letter

```
POST /customers/{id}/letter          -> { letter_id, status:"draft", html, sections:[...], guardrail }
GET  /customers/{id}/letter.html     -> latest letter as printable HTML (same template as the PDF)
GET  /customers/{id}/letter.pdf      -> application/pdf, latest approved letter
POST /customers/{id}/letter/approve  -> { letter_id, status:"approved" }
```

Letter and dashboard text come from the **same generated section strings** (C2). The letter HTML is the dashboard's `sections` laid out as paper plus the tear-off slip. No separate prose generation per view (P9).

### C5. Cases

Case object:

```json
{
  "id": "case_0007",
  "source": "slip_post_office",
  "status": "prepared",
  "urgency": "normal",
  "category": "afford_purchase",
  "summary": "Asking if she can afford a new boiler",
  "question_text": "Can I afford a new boiler?",
  "ticks": ["worried"],
  "created_at": "2026-12-01T10:02:00",
  "due": "2026-12-08",
  "route": { "team": "banker", "reason": "Next hub day (Tuesday)" },
  "briefing": {
    "asking": "…",
    "numbers": [{ "label": "Typical spare each month", "value": 215 }],
    "open_flags": ["flag_0001"],
    "things_to_check": ["…"]
  },
  "helper_note": null,
  "draft": null,
  "approved_at": null
}
```

```
GET  /cases?status=&urgency=         -> [case summary]  (urgent first, then due date)
POST /cases                          { source, text, ticks:["worried"|"scam"|…] } -> case
GET  /cases/{id}?viewer=helper:priya -> case (logs access, P7)
POST /cases/{id}/note                { note, helper:"Priya" } -> case
POST /cases/{id}/draft-reply         -> case with draft:{ text, guardrail } (status draft_ready)
POST /cases/{id}/draft               { text } -> case      # helper edits the draft; re-runs guardrails
POST /cases/{id}/approve             { helper:"Priya" } -> case (status approved, then closed on next-month)
```

`ticks` values for the slip: `"worried"`, `"scam_call"`, `"bill"`, `"afford"`, `"other"` (F5.5 and B8.2 must use this same list).

Approval rules (P3): `approve` returns **409** unless `status=="draft_ready"` and the latest draft passed guardrails.

### C6. Family and transparency

```
GET /customers/{id}/family-alerts -> { alerts:[{ id, at, message, reason_category }] }
```
`message` example: "Margaret may need a check-in today: unusual payment." `reason_category` ∈ `unusual_payment | missed_visit | open_urgent_case`. **No amounts, balances, names of payees or question text** (P5). The backend must make that structurally impossible (separate pydantic model with only these fields).

```
GET /customers/{id}/what-we-know -> {
  profile:{…}, data_held:[{ label, description, count }],
  access_log:[{ at, who, role, what }], trusted_person:{ name, relation, can_see:["alerts"] }
}
```

### C7. Fixtures (contract/fixtures/)

Minimum set, names fixed so both sides agree:

`customer.json`, `transactions.nov.json`, `facts.clean.json`, `dashboard.clean.json`, `dashboard.scam.json` (high flag, `attention`), `dashboard.guardrail-caught.json`, `dashboard.after-note.json` (since_visit filled), `cases.list.json` (one urgent), `case.boiler.prepared.json`, `case.boiler.draft-ready.json`, `case.boiler.approved.json`, `family-alerts.json`, `family-alerts.empty.json`, `what-we-know.json`, `letter.draft.html`.

---

## B. Backend plan (backend session)

Follows CLAUDE.md build order. All paths under `backend/counterpart/`.

- **B0 Scaffold.** `pyproject.toml` (fastapi, uvicorn, pydantic 2, anthropic, weasyprint, pytest), app factory, CORS for Vite (5173), SQLite via plain `sqlite3`, `GET /health`. Export OpenAPI to `contract/openapi.json` (script).
- **B1 Persona + generator + merchants** (CLAUDE.md steps 1). Seeded per-month RNG (`Random(f"{seed}-{year}-{month}")`) so history is stable when "next month" appends. Transaction stores `amount_pence:int`, exposes signed pounds. Optional `time`. Demo end month is November 2026. Merchant lookup returns `plain_name, category, cadence` (`4weekly|monthly|annual|weekly|seasonal|average|oneoff`); unknown descriptions go to the LLM categoriser (B4) and are cached. Persona bank = NatWest. Income model per 0.10. TV licence in January (annual). Events per `event` enum, applied with month; `forgotten_subscription` recurs monthly after first hit; `price_rise` bumps water 18%.
- **B2 Pipeline** (step 2, no LLM): `summarise`, `forecast` (cadence-driven, see rules below), `anomalies`, `facts`. Unit tests on every number. Print a month of transactions and the facts JSON for human review before B3.
  - Forecast rules: 4weekly projects from last payment +28 days; monthly present if present same month last year (or new this year); annual only if present same month last year; weekly counts weekdays in the month; seasonal uses same month last year; average uses last 3 months; `oneoff` ignored. Status: `short` if spare < 0, `warn` if spare < £100 or extra ≥ £50, else `ok`. Reason = largest positive driver vs her 12-month per-item average (or an income dip). Thresholds are tunable and tested.
  - Anomalies: `unusual_payment` = new payee + amount > 3× her median outgoing (+ unusual hour 21:00–07:00 adds a reason). `new_regular_payment` = subscription-category payee first seen within 2 months. `price_rise` = recurring bill up ≥ 15%.
  - `cash_blind_spot` when cash ≥ 10% of outgoings.
- **B3 Guardrails.** `check_numbers(text, facts)` (every £ amount in text must be in facts numbers or in £ amounts inside facts strings; tolerate rounding to the pound) and `check_banned(text)` (URLs, phone numbers, "click", "verify your details", "urgent action", "QR"). Run on every customer-facing draft; failures logged to a `guardrail_events` table and returned in `guardrail` (C2). Retry LLM up to 2 times, then raise `GuardrailFailure`; the API returns the templated fallback marked `source:"fallback"`. Unit tests cover the "£2,400 hallucination" demo case.
- **B4 LLM layer.** One client wrapper (`llm/client.py`) with: live call, disk cache keyed by (prompt hash, model), `LLM_MODE=live|cached|stub`. One `prompts.py`. Writers: letter sections (structured output per C2.sections), triage, case prep, reply drafter, categoriser fallback. Deterministic template writer used as the stub/fallback so the whole app works offline. Model and key from `ANTHROPIC_MODEL`, `ANTHROPIC_API_KEY`.
- **B5 API: customers, facts, dashboard, events, demo, letter HTML** (C2–C4). `dashboard` and `letter` both read one `generate_sections(facts)` result so they cannot disagree (P9). Cache sections per `facts_version`.
- **B6 Cases** (C5): model, service, routing (urgent -> phone team due today; else banker on next hub day; missed visit + open case -> family nudge), triage, case prep (scenario maths in code, e.g. boiler: spare vs typical quote ranges are **hard-coded illustrative ranges labelled as such**, never from the LLM), notes, draft-reply, approve gate (409 rule), access logging (P7). On close, the helper note feeds `since_last_visit` at the next `next-month`.
- **B7 PDF, family alerts, what-we-know** (C4, C6). WeasyPrint spike on day one; if pango fails on WSL, fall back to browser print CSS and drop `/letter.pdf` to a stretch goal (tell frontend).
- **B8 Demo controls.** `next-month`: advance `as_of`, close approved cases, push their notes into `since_last_visit`, regenerate sections. `reset`: wipe state, re-seed. Seed one pre-baked normal case ("Can I afford a new boiler?", `slip_post_office`) so the demo script step 3 works without typing.
- **B8.2** Slip tick list = C5 `ticks`.
- **B9 Contract tests.** For every fixture in C7, a test that the live endpoint (in stub mode with the same scenario) returns the same key set and types. Plus: P5 test (family response has no amounts), P6 test (letter HTML has no `http`, no `<a href>`, no digits resembling phone numbers), P9 test (every figure in dashboard text appears in letter HTML).
- **B10 Polish.** `make dev`, `make test`, `make reset`, README.

Definition of done for backend: steps 1–6 pass with `LLM_MODE=stub`; live LLM path works with the key; fixtures validated.

---

## F. Frontend plan (frontend session)

Design spec produced with the Impeccable skill. Visual world is pinned by the brief (NatWest purple and white, calm paper-like), so no concept roll was run. Mode: **Operate** for helper screens and the dashboard; **Read** for the letter and What we know. Build code-led (no image-comp round).

### F0. Setup

Vite + React 18 + TypeScript, React Router, no UI kit, no chart library. Plain CSS with custom properties in `src/styles/tokens.css`. Fetch layer in `src/api/` typed from `contract/openapi.json` (or hand-typed from section C). `VITE_API_MODE=mock` serves `contract/fixtures/*`. Poll `GET /demo/state` every 2 s (or SSE if backend adds it) and refetch when `facts_version` changes.

Routes:

| Route | Screen | Roles |
|---|---|---|
| `/` | redirects to `/dashboard` | all |
| `/dashboard` | F3 Shared dashboard | margaret, helper |
| `/queue` | F5 Helper queue | helper |
| `/cases/:id` | F3 dashboard + F4 helper panel | helper |
| `/demo` | F6 Statement vs letter | helper (judge page, always reachable) |
| `/family` | F7 Family alert | family |
| `/what-we-know` | F8 What we know | all |
| `/letter` | F9 Printable letter preview | all |

### F1. Design system

**Scene.** A tablet propped between two people at a counter, daylight or strip lighting, one of them 81 with failing close vision. Light theme only (print-like), no dark mode; do not add one.

**Colour strategy: Restrained.** Tinted neutrals plus one brand purple; status colours are small, always paired with icon and word.

Tokens (placeholders: the exact NatWest values are unverified, sources disagree between `#3C1053`, `#401664` and others; **verify by sampling an official NatWest asset before the demo**, and check every pair for contrast):

```
--ink            #2B0D3E   /* body text on paper, aim >= 12:1 */
--purple         #3C1053   /* headings, primary buttons, brand bar */
--purple-soft    #EFE8F5   /* panels, section dividers (pale lilac) */
--paper          #FFFFFF   /* page */
--paper-2        #F8F5FB   /* alternating sections */
--line           #D4C5E0
--status-good    #0B6B3A  (+ check icon, word "Looking good")
--status-warn    #8A5A00  (+ triangle icon, word "Worth a look")
--status-short   #A4161A  (+ cross icon, word "Short")
--focus          #0057FF   /* 3px outline, 2px offset, always visible */
```
Accent pink/teal from NatWest's wider palette may appear **only** on the demo page chrome (F6), never on Margaret-facing screens.

**Type.** NatWest's real typeface is proprietary. Use **Overpass** (open source, close to the wordmark lettering) via Google Fonts, self-hosted woff2 in `public/fonts/` so the demo works offline. Fallback `system-ui, sans-serif`. Scale (default / large-print mode toggled in the top bar): body 20px / 24px, section title 32px / 38px, headline 44px / 52px, never below 18px anywhere on Margaret-facing screens. Line height 1.55, measure max 62ch. Sentence case, no all-caps, no italics for emphasis.

**Layout rules.** Max content width 960px centred; helper panel adds a fixed 360px right column (page does not reflow, content column stays the same width; below 1100px the panel becomes a bottom drawer). Spacing scale 8/16/24/40/64. Sections separated by 64px and a 1px `--line` rule; each section is a `<section aria-labelledby>`. Nothing animates except focus and a 150ms colour change; honour `prefers-reduced-motion`. Zero layout shift: reserve heights, skeletons match final sizes.

**Components** (build once, reuse): `AppBar` (brand mark text "Counterpart", role switcher, large-print toggle, helper role badge), `Section` (title, read-aloud button, content), `StatusBadge` (icon + word + colour), `MoneyBar` (CSS-only horizontal bar, label left, £ right), `MonthCard`, `FlagCard`, `ReadAloudButton`, `GuardrailBadge`, `CaseRow`, `HelperPanel`, `PhoneFrame`, `QuestionForm`, `Disclaimer` footer ("Prototype, not an official NatWest product").

**Read aloud.** `speechSynthesis`, `en-GB`, 0.9 rate. Button label "Read this out loud" with a speaker icon, toggles to "Stop". Reads the section's `text` string, not the DOM, so it is exactly the letter words. If unsupported, hide the button and keep nothing broken.

### F2. App shell and roles

Top bar: product name left; role switcher (segmented control: **Margaret | Helper | Family**) and "Bigger text" toggle right. Role is stored in `localStorage` (try/catch) and is just a UI switch (0.7). Margaret role hides `/queue`, helper panel, demo link. Helper role shows a "You are signed in as Priya, Community banker" strip beneath the bar (role from `helper_role`). Footer: disclaimer plus link to What we know. Skip-to-content link first. Document `lang="en-GB"`, one `<h1>` per route.

### F3. Shared dashboard (hero, `/dashboard` and inside `/cases/:id`)

This is the letter's twin: C2.3 order, same strings. Single column, 960px.

1. **Headline.** Biggest element on the page: `StatusBadge` + one sentence (`sections[headline].text`). Status colour only on the badge and a 6px left bar; the page stays white.
2. **Last month.** Sentence from `text`, then `MoneyBar`s from `facts.last_month`: "Money in £X" (full-width reference bar), each outgoing by plain name (bar length relative to money in), "Cash from the Post Office", and a bold "Left over £Y". Bars are decorative; every value is also text. If left over is negative show it plainly as "£N more went out than came in" **taken from the `text`**, not computed.
3. **Next three months.** Three equal `MonthCard`s in a row (stack on narrow): month name, `StatusBadge` (✓ Looking good / ⚠ Worth a look / ✗ Tight), the reason in words, and "Expected spare: £N". Layout identical every month.
4. **One idea.** One card, `--purple-soft` ground, text + "£N a month" from `facts.suggestion`. Omitted entirely when absent (no empty box). Footer line signposting: MoneyHelper and Citizens Advice by **name only, no link** (P6).
5. **Scam watch.** Calm state: shield-check icon, "Nothing unusual this month". Flagged state: `FlagCard` with the severity word, plain explanation from `text`, the `reasons[]` as a short bulleted list, and a fixed line "You do not have to do anything. Your helper can talk it through with you." Scam flags inform, never block or demand (P4).
6. **Since your last visit.** Helper name, note text, date. Empty state: "Nothing new since we last spoke."
7. **Ask a question.** The same options as the tear-off slip, as large radio/checkbox tiles (`ticks` list from C5) plus a textarea. Submit creates a case (`POST /cases`, source `hub_visit` in helper context else `counter_verbal`; Margaret solo = `hub_visit`... confirm in section 7). Success shows "Thank you. Priya or a colleague will reply by letter." (copy from backend `ask.text`).

Every section has a header row: title left, `ReadAloudButton` right. `GuardrailBadge` (F6.4) never appears on Margaret role.

States: loading (skeletons same height), error ("We could not load this. Your letter has the same information." with retry), `attention` headline (still calm, no flashing, no red page).

### F4. Helper panel (docks right on `/cases/:id`, helper role only)

Fixed 360px column, `--paper-2` ground, 1px left rule, sticky. Contents top to bottom:
1. Case header: source icon + label, urgency badge, due date, `route` ("Banker, next hub day Tuesday").
2. "She is asking": `briefing.asking`.
3. "Relevant numbers": `briefing.numbers` as label/value rows, "from the dashboard" tag; scenario maths come from backend.
4. "Open flags": `FlagCard` summaries linking (scroll-to) the Scam watch section.
5. "Things to check or mention": checklist (`things_to_check`), check state is local only.
6. Your notes: textarea, "Save note" -> `POST /cases/:id/note`.
7. "Draft reply" button -> `POST /cases/:id/draft-reply`; shows an editable textarea with the draft, a `GuardrailBadge` if `draft.guardrail.caught`, "Save edit" (`POST /cases/:id/draft`).
8. "Approve and send to post queue" primary button, **disabled until `status==draft_ready`**; a confirm dialog states "This will be sent as a letter. Check the numbers." After success: status chip "Approved", panel locks the draft.

The dashboard left of the panel is **pixel-identical** to Margaret's (P10): the panel adds nothing inside the 960px column.

### F5. Helper queue (`/queue`)

A list (not a dense table): each `CaseRow` is a 72px-high row with source icon + text label, urgency badge (High first, left-edge purple bar), summary, status chip, due date. Sorted as the API returns (urgent first). Filters: All / Urgent / Mine are chips above the list (client-side). Opening a row goes to `/cases/:id`. Empty state: "No open questions." New cases arriving via polling fade in without shifting rows already on screen (insert at top, reserved space, no animation under reduced motion). Helpers see body text 18px minimum; this screen is Operate, not Margaret-facing, so it may be denser than F3 but not a table grid.

### F6. Demo control page, "Statement vs letter" (`/demo`)

Judge-facing, this is where the pink/teal accent from the NatWest palette is allowed, as a slim demo toolbar only.

1. Two-pane layout. Left: raw statement list (`GET /transactions`): date, cryptic description (monospace-ish, `font-variant-numeric: tabular-nums`), signed amount, channel. Right: tabs **Letter | Dashboard** showing the letter preview (`/letter.html` in an iframe-less rendered component, F9) or the dashboard (F3 read-only embed). Tab choice persists.
2. Toolbar buttons: **Inject scam transfer**, **Inject forgotten subscription**, **Inject price rise**, **Next month**, **Regenerate**, **Reset demo**. Each shows an in-flight state and, on success, briefly highlights (outline, 1s, reduced-motion safe) the changed statement rows and the Scam watch section.
3. A thin status strip: `as_of` date, `LLM mode` (live/cached/stub), `facts_version`.
4. **Guardrail badge.** When `guardrail.caught` is true, a small badge "Guardrail caught this" (shield icon) appears above the affected letter/dashboard text; clicking opens a popover listing `guardrail.events[]` ("£2,400 was not in the facts, so it was regenerated"). Visible on `/demo` and for helpers on drafts; never to Margaret.
5. Side-by-side "same numbers" affordance: a toggle "Highlight figures" outlines every £ amount in both panes, proving P9 visually (pure CSS on the rendered strings).

### F7. Family alert (`/family`)

Centre-stage phone frame (CSS-drawn, 360x720) with a lock-screen style SMS bubble: sender "Counterpart", text from `alerts[0].message`, time. Nothing else on the phone. Beside it (outside the frame) a small caption for judges: "This is everything Sarah sees. No balances, no transactions, no question content." Empty state: phone shows "No alerts today." The page polls and updates when a new alert appears.

### F8. What we know (`/what-we-know`)

Read-mode page, printable (`@media print`: hide app bar/role switcher, black on white, 12pt, page breaks between sections). Sections: "About you" (profile), "What we hold" (`data_held` list with plain descriptions and counts), "Who has looked" (`access_log` as a simple list: date, who, why), "Who gets alerts" (trusted person, what they can and cannot see). "Print this page" button. Visible to margaret and helper.

### F9. Letter preview (`/letter`, also embedded in F6)

Renders `letter.html` from the backend inside a paper-styled container (A4 ratio, shadow-free), so what is on screen matches the PDF. Includes the tear-off slip at the bottom as a dashed-bordered block with the same ticks as F3.7. Buttons: "Print / Save as PDF" (browser print) and "Download PDF" (`/letter.pdf`, hidden if the endpoint 404s). The letter has no links, no QR, no phone number.

### F10. Accessibility (acceptance criteria; run the accessibility skill at the end)

- WCAG 2.2 AA minimum; body text contrast >= 7:1 where possible. All status uses icon + word + colour.
- Fully keyboard operable, logical tab order, visible 3px focus ring, skip link, no keyboard traps in dialogs (focus trap + Esc + return focus).
- Landmarks (`header`, `main`, `nav`, `aside` for helper panel, `footer`), one `h1`, ordered headings.
- Targets >= 48x48px, 8px apart. Forms have visible labels, errors in text and `aria-live="polite"`.
- Respect `prefers-reduced-motion`, `prefers-contrast`; support 200% zoom and 400% reflow without horizontal scroll (except the F6 statement pane).
- Read-aloud on every F3 section (F1). Screen-reader pass with NVDA/VoiceOver on F3 and F4.
- Dynamic updates (new case, alert) announced politely via a live region, never stealing focus.

### F11. Frontend definition of done

All routes work against mock fixtures with every C7 fixture exercised; then pass against live backend; no console errors; Lighthouse accessibility >= 95 on F3, F5, F8; `prefers-reduced-motion` verified; run `impeccable detect` once and fix mechanical findings; finish with the Impeccable review and document the built system into `DESIGN.md` (documenter step) after the build, not before.

---

## 5. Cross-reference matrix (who needs what from whom)

| Frontend feature | Backend dependency | Contract |
|---|---|---|
| F3 dashboard | B5 `dashboard`, B4 writers, B3 guardrails | C2, C7 |
| F3.5 scam watch | B2 anomalies, B1 events | C1 flag, C2 |
| F3.7 ask | B6 cases, B8.2 ticks | C5 |
| F4 helper panel | B6 briefing, draft-reply, approve (409 rule) | C5 |
| F5 queue | B6 routing, ordering | C5 |
| F6 demo | B5 events, B8 next-month/reset, B3 guardrail events | C3, C2.guardrail |
| F7 family | B7 family model (P5 test in B9) | C6 |
| F8 what we know | B6 access logging (P7), B7 | C6 |
| F9 letter | B5 letter HTML, B7 PDF | C4 |

---

## 6. Milestones and integration

1. **M0 (first commit, both start):** this plan + `contract/` skeleton + empty fixtures stubs. Start the two sessions (section 8).
2. **M1 Backend B0–B2 and Frontend F0–F2 + F1 tokens** in parallel. Backend prints a month and facts for human review.
3. **M2 B3–B5, F3 + F6 (statement vs letter) on fixtures.** First real integration: `VITE_API_MODE=live` against `LLM_MODE=stub`. Demo steps 1–2 work.
4. **M3 B6, F4 + F5.** Demo step 3 works. **Cut line:** if time runs out, stop after this plus B8 next-month (steps 1–6 are the full loop).
5. **M4 B8 next-month/reset, approval -> since_visit.** Demo step 4.
6. **M5 B7 + F7 + F8 + F9.** Demo step 5.
7. **M6 polish:** live LLM on, rehearsal x3 from `reset`, accessibility pass, disclaimer, fonts self-hosted, offline test (wifi off, `LLM_MODE=cached`).

Commit each milestone to `daria-dashboard-and-letter` with explicit paths (section 1 rules); open one PR to `main` at the end.

---

## D. Demo script mapping (3 minutes)

| Step | What happens | Backend | Frontend |
|---|---|---|---|
| 1 | Raw statement next to the letter, flip to dashboard: same story | B5 | F6, F3 |
| 2 | Click **Inject scam transfer**: Scam watch changes in letter and dashboard, urgent case appears, family alert appears | B1, B2, B6, B7 | F6.2, F3.5, F5, F7 |
| 3 | Open the boiler case: dashboard + helper panel, note, draft, approve | B6 | F4 |
| 4 | **Next month**: letter and dashboard both show "Since your last visit" with the note | B8 | F3.6, F6 |
| 5 | Ten seconds on What we know | B6, B7 | F8 |
| 6 | Close line: "We didn't make Margaret go digital. We gave her and the people around her the same clear picture, on paper and on screen." | | |

Also show: the guardrail badge once (force a bad number in stub mode with a hidden `?demo=bad-number` flag on the backend, B3).

---

## 7. Open items (need a human)

1. **NatWest brand specifics.** Confirm exact purple hex and whether to display the NatWest name/mark in the app bar. Recommendation: text "Counterpart" only, no logo, plus the disclaimer.
2. **Disclaimer wording** in the footer: confirm.
3. **Margaret solo case source** when she asks a question herself on a home tablet: use `hub_visit`? or add a new `self_service` source? (Adding means updating C1.)
4. **Boiler scenario numbers** (B6): illustrative cost ranges, who signs them off.
5. **Are cached LLM outputs committed** to the repo for the offline fallback? Recommended yes (`backend/cache/`), after a clean rehearsal run.
6. **Impeccable update available** (v4.8.0 vs 4.3.1): not applied; run `npx impeccable update` yourself in a new session if wanted.

---

## 8. How to start each session

Both prompts include the git rules from section 1.

Backend session prompt:
> Read `CLAUDE.md`, `PRODUCT.md`, `plan.md` sections 0, 1, C, B, 5, 6, D. You own `backend/`, `contract/` and `plan.md`; do not touch `frontend/`. Git: commit with explicit paths only (`git add backend/ contract/`), never `-A`/`.`/`commit -a`, never checkout/stash/reset/rebase. Build B0 then B1–B2 only; stop and show me a printed month of transactions and the facts JSON before B3.

Frontend session prompt:
> Read `CLAUDE.md`, `PRODUCT.md`, `plan.md` sections 0, 1, C, F, 5, 6, D. You own `frontend/` only; `backend/`, `contract/` and `plan.md` are read-only. Git: commit with explicit paths only (`git add frontend/`), never `-A`/`.`/`commit -a`, never checkout/stash/reset/rebase. Build F0–F3 against `contract/fixtures/` (`VITE_API_MODE=mock`). If you need a contract change, stop and ask me. Use the Impeccable and web-quality accessibility skills; verify contrast of the tokens in F1.
