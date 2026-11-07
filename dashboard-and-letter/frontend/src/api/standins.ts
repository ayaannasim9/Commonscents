// MOCK-ONLY stand-ins for the five personas whose fixtures the backend has not written yet.
// The mock prefers contract/fixtures/personas.json and dashboard.<id>.json when they exist and only
// falls back to this file. Nothing here ships to the live mode. Numbers are invented for layout testing
// and follow personas.md; the sentences are templated here only because the backend writer is not wired in.
import type { Case, Customer, Dashboard, Facts, ForecastStatus, HeadlineStatus, PersonaSummary } from './types'

type Spec = {
  c: Customer
  status: HeadlineStatus
  lm: Facts['last_month']
  fc: [ForecastStatus, string, number, number][] // status, reason, extra, spare (Dec, Jan, Feb)
  idea?: { hint: string; amount: number; text: string }
  cash_blind_spot: boolean
  question: { text: string; source: Case['source']; ticks: Case['ticks']; category: Case['category']; urgency: Case['urgency']; summary: string; team: 'banker' | 'post_office' | 'phone' }
}

const cust = (id: string, name: string, age: number, archetype: Customer['archetype'], tagline: string, hub_day: string, large: boolean, readAloud: boolean): Customer => ({
  id, name, age, archetype, tagline, bank: 'NatWest', hub_day,
  preferences: { large_print: large, read_aloud_default: readAloud, language: 'en' },
})
const lm = (in_: number, out: [string, number][], cash: number, left: number): Facts['last_month'] => ({
  month: 'November', year: 2026, in: in_, out: out.map(([name, amount]) => ({ name, amount })), cash, left,
})

const SPECS: Spec[] = [
  {
    c: cust('JDN-2208', 'Jayden', 18, 'first_account', 'First job, first account.', 'Thursday', false, false),
    status: 'heads_up',
    lm: lm(610, [['Food delivery', 164], ['Travel', 52], ['Games and apps', 41], ['Phone', 22], ['Streaming', 15], ['Everything else', 238]], 60, 18),
    fc: [['short', 'fewer working hours', 0, 0], ['ok', 'nothing unusual', 0, 95], ['ok', 'nothing unusual', 0, 70]],
    cash_blind_spot: true,
    question: { text: 'Why is my money gone before pay day?', source: 'counter_verbal', ticks: ['other'], category: 'general', urgency: 'normal', summary: 'Asking why money runs out before pay day', team: 'banker' },
  },
  {
    c: cust('AMR-3135', 'Amira', 29, 'recent_migrant', 'New to UK bills.', 'Monday', false, true),
    status: 'heads_up',
    lm: lm(1480, [['Rent', 420], ['Groceries', 210], ['Money sent abroad', 200], ['Council tax', 92], ['Energy', 45], ['Everything else', 96]], 40, 377),
    fc: [['warn', 'council tax and TV licence', 267, 58], ['ok', 'nothing unusual', 0, 290], ['ok', 'nothing unusual', 0, 300]],
    cash_blind_spot: true,
    question: { text: 'What is this payment called TV LICENCE MBP? I did not ask for it.', source: 'slip_post', ticks: ['bill'], category: 'bill_query', urgency: 'normal', summary: 'Asking about a TV licence payment', team: 'banker' },
  },
  {
    c: cust('DAN-5502', 'Daniel', 46, 'low_literacy', 'Cash and direct debits.', 'Wednesday', true, true),
    status: 'good',
    lm: lm(1980, [['Rent', 560], ['Energy', 78], ['Council tax', 132], ['Car insurance', 48], ['Water', 31], ['Everything else', 118]], 380, 633),
    fc: [['ok', 'nothing unusual', 0, 590], ['ok', 'nothing unusual', 0, 560], ['ok', 'nothing unusual', 0, 600]],
    cash_blind_spot: true,
    question: { text: 'What is the INS payment? Is it a scam?', source: 'slip_post_office', ticks: ['bill', 'worried'], category: 'payment_query', urgency: 'high', summary: 'Asking what a payment is and whether it is a scam', team: 'phone' },
  },
  {
    c: cust('SAM-7316', 'Sam', 27, 'learning_difficulty', 'A weekly allowance.', 'Friday', true, true),
    status: 'good',
    lm: lm(1180, [['Housing charge', 540], ['Cafe and newsagent', 220], ['Game purchases', 64], ['Leisure club', 18], ['Phone', 12], ['Everything else', 36]], 0, 290),
    fc: [['ok', 'nothing unusual', 0, 285], ['ok', 'nothing unusual', 0, 290], ['ok', 'nothing unusual', 0, 280]],
    cash_blind_spot: false,
    question: { text: 'Where did my game money go?', source: 'counter_verbal', ticks: ['other'], category: 'general', urgency: 'normal', summary: 'Asking where game money went', team: 'banker' },
  },
  {
    c: cust('RAV-6049', 'Ravi', 34, 'never_budgeted', 'Every bill, first time.', 'Tuesday', false, false),
    status: 'heads_up',
    lm: lm(3350, [['Rent', 890], ['Childcare', 220], ['Council tax', 165], ['Energy', 95], ['Streaming', 27], ['Everything else', 640]], 60, 1253),
    fc: [['ok', 'nothing unusual', 0, 1200], ['warn', 'TV licence', 175, 1020], ['ok', 'nothing unusual', 0, 1260]],
    idea: { hint: 'put a little aside for the March car costs', amount: 150, text: 'If you put £150 aside each month, March will feel easier. This is only an idea, and it is your choice. Free, independent help is available from MoneyHelper and Citizens Advice.' },
    cash_blind_spot: false,
    question: { text: 'I have never done a budget. Is my income enough?', source: 'hub_visit', ticks: ['afford'], category: 'afford_purchase', urgency: 'normal', summary: 'Asking if income is enough, first budget', team: 'phone' },
  },
]

const MONTHS = [['December', 2026], ['January', 2027], ['February', 2027]] as const
const p = (n: number) => `£${n.toLocaleString('en-GB')}`

function dashboard(s: Spec): Dashboard {
  const facts: Facts = {
    as_of: '2026-12-01',
    customer: { name: s.c.name, reference: s.c.id, bank: 'NatWest', hub_day: s.c.hub_day },
    headline_status: s.status,
    last_month: s.lm,
    forecast: s.fc.map(([status, reason, extra, spare], i) => ({ month: MONTHS[i][0], year: MONTHS[i][1], status, reason, extra, spare })),
    suggestion: s.idea ? { text_hint: s.idea.hint, amount: s.idea.amount } : null,
    flags: [],
    since_last_visit: null,
    cash_blind_spot: s.cash_blind_spot,
  }
  const tight = facts.forecast.find((f) => f.status !== 'ok')
  const top3 = s.lm.out.slice(0, 3).map((o) => `${o.name.toLowerCase()} (${p(o.amount)})`)
  const fcText = facts.forecast.map((f) => f.status === 'ok' ? `${f.month} looks fine, with about ${p(f.spare)} spare.` : f.status === 'warn' ? `${f.month} looks tight, with about ${p(f.spare)} spare, mainly because of ${f.reason}.` : `${f.month} looks very tight, with nothing spare, mainly because of ${f.reason}.`).join(' ')
  const sections: Dashboard['sections'] = [
    { id: 'headline', title: 'How things look', status: s.status, text: tight ? `You are doing fine. ${tight.month} will be a little tight because of ${tight.reason}, so it is worth planning for.` : 'You are doing fine. Nothing needs your attention this month.' },
    { id: 'last_month', title: 'Last month', text: `In November, ${p(s.lm.in)} came in. Your biggest bills were ${top3.join(', ')}. You took out ${p(s.lm.cash)} in cash, and you had ${p(s.lm.left)} left over.` },
    { id: 'forecast', title: 'The next three months', text: fcText },
    ...(s.idea ? [{ id: 'idea' as const, title: 'One idea', text: s.idea.text, optional: true }] : []),
    { id: 'scam_watch', title: 'Scam watch', status: 'nothing_unusual', text: 'Nothing unusual this month. Your payments all look like your normal ones. We will never ask for your details in a letter. If someone calls and asks you for money, put the phone down and use the number on the back of your bank card.' },
    { id: 'since_visit', title: 'Since your last visit', text: 'Nothing new since we last spoke.' },
    { id: 'ask', title: 'Ask a question', text: `If you have a question, tick a box on the slip or ask your helper on ${s.c.hub_day}. A colleague will reply by letter.` },
  ]
  return { as_of: '2026-12-01', facts_version: 1, facts, guardrail: { caught: false, events: [] }, sections }
}

export const STANDIN_CUSTOMERS: Customer[] = SPECS.map((s) => s.c)
export const standinPersona = (c: Customer): PersonaSummary => ({ id: c.id, name: c.name, age: c.age, archetype: c.archetype, tagline: c.tagline })
export const standinDashboard = (id: string): Dashboard | null => {
  const s = SPECS.find((x) => x.c.id === id)
  return s ? dashboard(s) : null
}
/** One short seeded question per persona, built on top of a real case fixture. */
export const standinCase = (id: string, base: Case): Case | null => {
  const s = SPECS.find((x) => x.c.id === id)
  if (!s) return null
  const q = s.question
  const n = 200 + SPECS.indexOf(s)
  return {
    ...base,
    id: `case_0${n}`, source: q.source, status: 'prepared', urgency: q.urgency, category: q.category, summary: q.summary,
    question_text: q.text, ticks: q.ticks, helper_note: null, draft: null, approved_at: null,
    due: q.urgency === 'high' ? '2026-12-01' : '2026-12-08',
    route: { team: q.team, reason: q.urgency === 'high' ? 'Urgent: phone team, due today' : `Next hub day (${s.c.hub_day})` },
    briefing: { asking: q.summary + '.', numbers: [{ label: 'Left over last month', value: s.lm.left }], open_flags: [], things_to_check: ['Check what the question is really about, then talk it through together.'] },
  }
}
