# Personas

Common Cents serves people who are not well served by a banking app. We show six of them. **The product, the UI components, the letter template and the guardrails are identical for all six. The only thing that differs is the data: each persona's transaction history, and therefore the facts object, the forecast, the flags and the words that come from them.** If a feature needs a per-persona code path, it is out of scope.

Margaret is the hero of the 3-minute demo (`plan.md` section D). The others are shown from the demo page persona picker (`plan.md` F6.6) to prove the idea generalises: same dashboard, different story.

All people here are fictional and every transaction is generated (seeded RNG). No real customer data, ever. Pronouns are deliberately avoided in descriptions.

Cross-references: `plan.md` B1 (generator), B8 (seeds), C3 (`GET /personas`), F6.6 (picker), C7 (fixtures).

---

## How a persona is defined (the contract for the generator)

Backend `PersonaSpec` (extends the Margaret persona in CLAUDE.md; `trusted_person` is removed, see plan section 0.15):

```json
{
  "id": "MRG-4471",
  "name": "Margaret",
  "age": 81,
  "archetype": "elderly",
  "bank": "NatWest",
  "hub_day": "Tuesday",
  "tagline": "Gets a letter, not an app.",
  "preferences": { "large_print": true, "read_aloud_default": false, "language": "en" },
  "income": [ ... ],
  "fixed_bills": [ ... ],
  "variable_spend": [ ... ],
  "annual_items": [ ... ],
  "seeded_events": [],
  "seeded_case": { "source": "slip_post_office", "text": "Can I afford a new boiler?", "ticks": ["afford"] }
}
```

Rules that keep personas honest:

1. **Same pipeline, same thresholds.** Categorise, summarise, forecast and anomalies run unchanged. A persona may add merchants to the lookup table, never a persona-specific rule.
2. **Same output language.** The writer prompt targets reading age about 9 for everyone (CLAUDE.md). No per-persona prompt variants. `preferences` only drive display toggles the UI already has (large print, read-aloud button emphasis).
3. **Seeded RNG per (persona, month)** so history is stable when "Next month" appends (plan B1).
4. **Each persona has a seeded case** so the helper queue is not empty on first view, and each has a planted-event story that works with the same injection buttons (`scam_transfer`, `forgotten_subscription`, `price_rise`).
5. **Print and review before use:** for every persona the backend session runs `print_month.py --persona <id>` and shows the statement and facts JSON for human review, as with Margaret.
6. **No commercial logic.** No credit, overdraft, loan or product suggestions for any persona (CLAUDE.md principle 8). A "short" month is information plus signposting (MoneyHelper, Citizens Advice), never a product.

Demo date and horizon are shared: letter dated 1 Dec 2026, last month November 2026, forecast December to February.

---

## The six personas

| # | Id | Name | Age | Archetype | The story in one line |
|---|---|---|---|---|---|
| 1 | MRG-4471 | Margaret | 81 | `elderly` | Steady pensions, a January squeeze, one scam |
| 2 | JDN-2208 | Jayden | 18 | `first_account` | First job, first account, money gone by the 20th |
| 3 | AMR-3135 | Amira | 29 | `recent_migrant` | Sends money home, hit by UK bills nobody explained |
| 4 | DAN-5502 | Daniel | 46 | `low_literacy` | Cash and direct debits, cannot decode the statement |
| 5 | SAM-7316 | Sam | 27 | `learning_difficulty` | Fixed weekly allowance, runs out before the week does |
| 6 | RAV-6049 | Ravi | 34 | `never_budgeted` | Took over every bill, surprised by the annual ones |

### 1. Margaret, 81 (`elderly`), the hero

- **Who:** retired, rents from a housing association, does not use banking apps. Reads a paper letter; sits with a helper at the hub or Post Office on Tuesdays.
- **Needs from the product:** large print, nothing that moves, a human beside her, scam awareness.
- **Income:** State Pension every 4 weeks (£760, so December has two payments), small work pension monthly (£520).
- **Fixed bills:** rent £480, council tax £118 (10 months a year, none in February or March), phone and TV £30 (April price rise), electricity £32, water £28, gas £86 in winter (about double the summer figure).
- **Variable:** £40 cash every Friday at the Post Office, local shop about £92 a month, pharmacy about £24.
- **Annual:** TV licence £175 in January.
- **Resulting story (already built, see fixtures):** November left over £230; December comfortable, January tight (£15 spare, TV licence), February fine. Cash blind spot is on.
- **Planted event used live:** `scam_transfer` (£2,000 faster payment, 21:14, new payee).
- **Seeded case:** "Can I afford a new boiler?" (`slip_post_office`).
- **Preferences:** `large_print: true`, `read_aloud_default: false`, `language: en`.
- **Changes from CLAUDE.md:** bank is NatWest, no trusted person.

### 2. Jayden, 18 (`first_account`)

- **Who:** left school, first part-time job, first current account. Has never seen a bank statement. Mostly phone-first, but the paper letter is a calm summary a parent or youth worker can go through with them.
- **Needs from the product:** to see where money goes, and why the end of the month is empty. Plain explanations of descriptions.
- **Income:** weekly wage that varies with hours (about £120 to £210 a week, paid Fridays, description like `RETAILCO LTD WAGES`). Small birthday and family gifts occasionally.
- **Fixed bills:** phone contract £22 (direct debit), a gym or streaming subscription £14.99.
- **Variable:** many small card payments (food delivery, bus pass top-ups, vending machine, online games), clustered at weekends and just after payday. Cash withdrawals of £20 to £30, irregular.
- **Annual:** none.
- **Target story:** pay-day highs, then spare falls to near zero around the 20th; one month in the forecast looks `short` because fewer hours are forecast around the holidays (the forecast uses last year's same-month hours, so give last December low hours). There is no debt, no overdraft, no product.
- **Planted event used live:** `forgotten_subscription` (a £9.99 monthly game or music pass they forgot to cancel).
- **Seeded case:** "Why is my money gone before pay day?" (`counter_verbal`, tick `other`).
- **Preferences:** `large_print: false`, `read_aloud_default: false`, `language: en`.
- **Hub day:** Thursday (a youth hub). **Helper role:** banker.

### 3. Amira, 29 (`recent_migrant`)

- **Who:** moved to the UK about 14 months ago, working in care shifts; shares a flat. Speaks good everyday English but is unsure of UK systems and terms.
- **Needs from the product:** UK bill terms in plain words (council tax, TV licence, direct debit), reassurance that a regular transfer abroad is normal and is not a flag, and scam awareness ("someone claiming to be a tax office").
- **Income:** monthly care wages from one employer (`CARELINK SERVICES PAY`), plus a smaller weekly top-up wage from agency shifts, partly irregular.
- **Fixed bills:** room rent £420 (standing order to a named landlord), phone £15, energy share £45, council tax £92 starting this autumn (first bill, 10 months a year) and a TV licence that arrived unexpectedly in November (£174.50 annual, direct debit, new this year).
- **Variable:** monthly money transfer abroad of about £180 to £220 (`WORLDREMIT TRANSFER` style, channel `international_transfer`, payee seen every month, so it is **not** flagged); weekly groceries at a discount supermarket and specialist food shop; transport card.
- **Target story:** the new council tax and TV licence make one forecast month `warn`. A regular remittance must not trigger the anomaly rule (it is a repeat payee within her usual range). The letter explains council tax and TV licence in one plain sentence each.
- **Planted event used live:** `price_rise` (energy up 15%+), and `scam_transfer` also works: a £900 faster payment to a new payee, late evening, is far above her median so it flags.
- **Seeded case:** "What is this payment called TV LICENCE MBP? I did not ask for it." (`slip_post`, tick `bill`).
- **Preferences:** `large_print: false`, `read_aloud_default: true` (helps with reading confidence), `language: en`.
- **Hub day:** Monday. **Helper role:** banker.
- **Out of scope:** translation into other languages. The words stay simple English (reading age about 9). Note as a future extension only.

### 4. Daniel, 46 (`low_literacy`)

- **Who:** warehouse operative, reads slowly and avoids long text; handles money mostly in cash and with direct debits that "just happen". Asks a colleague or the Post Office counter for help.
- **Needs from the product:** short sentences, big numbers, icons, read-aloud on every section, and the cryptic statement decoded into plain names (this persona shows the "decoding" value most clearly).
- **Income:** monthly wage (`HARBOUR LOGISTICS PAYROLL`) plus occasional overtime (extra credit about every third month).
- **Fixed bills:** rent £560, council tax £132, energy £78 (seasonal), water £31, phone £20, car insurance £48 monthly (cryptic: `DD AXLEGRP INS 99021`), a store card or catalogue payment is **not** included (no credit).
- **Variable:** large share paid in cash (withdrawn at the Post Office weekly, £60 to £90); fuel; lunch at the same cafe; pay-point top-ups for gas and electric.
- **Target story:** cash blind spot is high (cash over 25% of outgoings); two descriptions repeatedly mystify (`GOVT-GW LICNCE 77` and the insurance DD). A bank charge for a missed direct debit appears once (`UNPAID ITEM FEE`), the pipeline treats it as "a charge you can avoid next time" via a plain-name lookup.
- **Planted event used live:** `price_rise` (the energy direct debit jumps) to show a rise explained in plain words.
- **Seeded case:** "What is the INS payment? Is it a scam?" (`slip_post_office`, ticks `bill`, `worried`). Urgency is **normal** unless the text mentions calls, texts or money requests (triage rule is code, unchanged).
- **Preferences:** `large_print: true`, `read_aloud_default: true`, `language: en`.
- **Hub day:** Wednesday (Post Office counter). **Helper role:** post_office.

### 5. Sam, 27 (`learning_difficulty`)

- **Who:** lives in supported accommodation, has a support worker who helps weekly. Benefits are paid in; a fixed weekly allowance is moved to spending. Likes routine; unexpected change is stressful.
- **Needs from the product:** the calmest, most predictable view; very few numbers; the helper and support worker sit beside them. Nothing should surprise.
- **Income:** benefit payments, fixed amounts on fixed dates (`DWP UNIVERSAL CREDIT`, `DWP PIP` every 4 weeks), nothing irregular.
- **Fixed bills:** supported-housing charge (direct debit, fixed), phone £12, a monthly leisure club £18.
- **Variable:** a weekly allowance spent on small daily card purchases at the same two places (corner cafe, newsagent), and repeated small in-app purchases on a phone game (£1.99 to £4.99).
- **Target story:** the allowance runs out by Thursday most weeks, which shows as small repeated payments and a low weekly pattern; the monthly total is stable, so the forecast is `ok` every month. The headline status is `good`. This persona shows the product being **quiet** when nothing is wrong, and in-app purchases are explained simply.
- **Planted event used live:** `forgotten_subscription` (a £4.99 monthly game pass), which becomes the only thing on the Scam watch (as an `info` flag, not a scare).
- **Seeded case:** "Where did my game money go?" (`counter_verbal`, tick `other`).
- **Preferences:** `large_print: true`, `read_aloud_default: true`, `language: en`.
- **Hub day:** Friday. **Helper role:** banker. Copy for this persona is the same as everyone's: short, calm sentences.

### 6. Ravi, 34 (`never_budgeted`)

- **Who:** recently separated and now responsible for every household bill for the first time; salaried and comfortable day to day; has never made a budget and does not know what a normal month costs.
- **Needs from the product:** a plain view of "what is left after the things that always come", and an early warning about annual bills.
- **Income:** monthly salary on the last working day (`NORTHGATE CONSULTING SAL`), occasional child maintenance received.
- **Fixed bills:** mortgage or rent £890, council tax £165, energy £95 (seasonal), water £33, broadband and phone £38, childcare £220, three streaming and app subscriptions that previously sat on a partner's card (£8.99, £11.99, £5.99).
- **Annual:** car insurance £620 in March, TV licence £174.50 in January, MOT and car tax in March, so March is crowded.
- **Target story:** every ordinary month leaves a healthy amount, so December and February are `ok` and January is `warn` (TV licence). After "Next month" the horizon becomes January to March, and **March shows `short`** (car insurance, MOT and car tax together). That is the early warning the persona needs. The "one idea" suggestion saves a little each month for March.
- **Planted event used live:** `forgotten_subscription` (a fourth subscription), and `price_rise` (broadband up).
- **Seeded case:** "I have never done a budget. Is my income enough?" (`hub_visit`, tick `afford`).
- **Preferences:** `large_print: false`, `read_aloud_default: false`, `language: en`.
- **Hub day:** Tuesday. **Helper role:** phone.

---

## Merchants to add to the lookup (cryptic description -> plain name)

Backend session adds these to `merchants.py`. Descriptions are deliberately cryptic. Cadence uses the plan B1 values.

| Description (example) | Plain name | Category | Cadence | Persona |
|---|---|---|---|---|
| `RETAILCO LTD WAGES` | Wages | income | weekly | Jayden |
| `CRD 2208 MEALBOX*ORDER` | Food delivery | eating_out | average | Jayden |
| `CRD GAMEPASS*RECUR` | Game pass subscription | subscription | monthly | Jayden, Sam |
| `CARELINK SERVICES PAY` | Wages | income | monthly | Amira |
| `WORLDREMIT TRANSFER` | Money sent abroad | transfer_regular | monthly | Amira |
| `GOVT-GW LICNCE 77` / `DD TV LICENCE MBP` | TV licence | tv_licence | annual | Amira, Daniel, Ravi |
| `HARBOUR LOGISTICS PAYROLL` | Wages | income | monthly | Daniel |
| `DD AXLEGRP INS 99021` | Car insurance | insurance | monthly | Daniel |
| `UNPAID ITEM FEE` | Bank charge for a missed payment | fee | oneoff | Daniel |
| `DWP UNIVERSAL CREDIT` / `DWP PIP` | Benefit payment | income | 4weekly | Sam |
| `DD SUPPORTED HSG CHG` | Housing charge | housing | monthly | Sam |
| `NORTHGATE CONSULTING SAL` | Wages | income | monthly | Ravi |
| `CRD STREAMCO*SUB` etc. | Streaming subscription | subscription | monthly | Ravi |
| `AXA/ANNUAL CAR INS` | Car insurance (yearly) | insurance | annual | Ravi |

`transfer_regular` is new: a repeat payee within her usual range is **excluded from anomaly flagging** by the existing "new payee" test (it only flags first-time payees), so no new rule is needed. A backend test must assert Amira's monthly transfer is **not** flagged.

---

## Acceptance checks per persona (backend session, B9)

1. `GET /personas` lists all six with id, name, age, archetype, tagline.
2. For each persona: statement for November nets to the stated `left` figure within the story above, forecast statuses match the story, and the facts JSON passes the number guardrail with its own letter text.
3. `scam_transfer` is judged against each persona's own median payment, with the same rule for all: a £200 payment flags for Sam (tiny typical payments), a £900 payment flags for Amira, and Amira's regular monthly transfer abroad never flags.
4. Each persona's seeded case appears in `/cases?customer=<id>`; cases and access logs are scoped per customer.
5. Switching persona never changes any code path, template or threshold (assert via a test that all personas use the same functions with only data differing).

## Display copy (shared)

Persona names, archetype labels and taglines appear only on the demo page picker (F6.6) and in What we know. Margaret-facing screens never show an archetype label (a person is not "a low-literacy user" on their own screen).
