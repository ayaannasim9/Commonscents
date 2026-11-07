// In-browser mock of the backend, built on contract/fixtures/*. Stateful enough to walk the demo script.
import { STANDIN_CUSTOMERS, standinCase, standinDashboard, standinPersona } from './standins'
import type { Case, CaseSummary, Dashboard } from './types'

const json = import.meta.glob('../../../contract/fixtures/*.json', { eager: true, import: 'default' }) as Record<string, unknown>
const raw = import.meta.glob('../../../contract/fixtures/*.html', { eager: true, query: '?raw', import: 'default' }) as Record<string, string>

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const fx = (name: string): any => {
  const hit = Object.entries(json).find(([p]) => p.endsWith(`/${name}.json`))
  if (!hit) throw new Error(`Missing fixture ${name}.json`)
  return structuredClone(hit[1])
}

const has = (name: string) => Object.keys(json).some((p) => p.endsWith(`/${name}.json`))
const MARGARET = 'MRG-4471'

export class MockHttpError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

type Stage = 'prepared' | 'with_helper' | 'draft_ready' | 'approved'
const fresh = () => ({
  month: 0, // 0 = December 2026 letter, 1 = January 2027 letter
  scam: false,
  guardrail: false,
  version: 1,
  boiler: 'prepared' as Stage,
  note: null as string | null,
  draftText: null as string | null,
  made: [] as { customer: string; c: Case }[],
  seq: 100,
})
let s = fresh()
const bump = () => { s.version += 1 }
const wait = () => new Promise((r) => setTimeout(r, 120))

function dashboard(cid = MARGARET): Dashboard {
  if (cid !== MARGARET) {
    const slug = STANDIN_CUSTOMERS.find((c) => c.id === cid)?.name.toLowerCase()
    const d: Dashboard | null = slug && has(`dashboard.${slug}`) ? fx(`dashboard.${slug}`) : standinDashboard(cid)
    if (!d) throw new MockHttpError(404, 'Customer not found')
    d.facts_version = s.version
    return d
  }
  const d: Dashboard = s.month === 1 ? fx('dashboard.after-note') : s.scam ? fx('dashboard.scam') : s.guardrail ? fx('dashboard.guardrail-caught') : fx('dashboard.clean')
  d.facts_version = s.version
  return d
}

function boiler(): Case {
  const name = { prepared: 'case.boiler.prepared', with_helper: 'case.boiler.prepared', draft_ready: 'case.boiler.draft-ready', approved: 'case.boiler.approved' }[s.boiler]
  const c: Case = fx(name)
  c.status = s.boiler
  if (s.note) c.helper_note = s.note
  if (s.draftText && c.draft) c.draft.text = s.draftText
  return c
}

const summary = (c: Case): CaseSummary => {
  const { id, source, status, urgency, category, summary: sm, created_at, due, route } = c
  return { id, source, status, urgency, category, summary: sm, created_at, due, route }
}

const allCases = (cid = MARGARET): Case[] => {
  const mine = s.made.filter((m) => m.customer === cid).map((m) => m.c)
  if (cid !== MARGARET) { const seeded = standinCase(cid, fx('case.boiler.prepared')); return [...(seeded ? [seeded] : []), ...mine] }
  return [...(s.scam ? [fx('case.scam.prepared') as Case] : []), boiler(), ...mine]
}
const customers = (): Record<string, unknown> => ({ [MARGARET]: fx('customer'), ...Object.fromEntries(STANDIN_CUSTOMERS.map((c) => [c.id, c])) })
const personaList = () => (has('personas') ? fx('personas') : [fx('customer'), ...STANDIN_CUSTOMERS].map((c) => standinPersona(c)))

export async function handle(method: string, path: string, body?: unknown): Promise<unknown> {
  await wait()
  const [p, query = ''] = path.split('?')
  const b = (body ?? {}) as Record<string, unknown>
  const m = (re: RegExp) => p.match(re)

  const cid = p.match(/^\/customers\/([^/]+)/)?.[1] ?? MARGARET
  if (method === 'GET' && p === '/personas') return personaList()
  if (method === 'GET' && m(/^\/customers\/[^/]+$/)) {
    const c = customers()[cid]
    if (!c) throw new MockHttpError(404, 'Customer not found')
    return c
  }
  if (method === 'GET' && m(/\/dashboard$/)) return dashboard(cid)
  if (method === 'GET' && m(/\/transactions$/)) return cid !== MARGARET ? { month: '2026-11', transactions: [] } : s.scam ? fx('transactions.nov.scam') : fx('transactions.nov')
  if (method === 'GET' && m(/\/what-we-know$/)) return fx('what-we-know')
  if (method === 'GET' && m(/\/letter\.html$/)) return raw[Object.keys(raw).find((k) => k.endsWith('letter.draft.html'))!]
  if (method === 'POST' && m(/\/events$/)) {
    if (b.event === 'scam_transfer' && cid === MARGARET) s.scam = true
    bump()
    return { facts_version: s.version, new_flags: [], new_case_id: b.event === 'scam_transfer' && cid === MARGARET ? 'case_0008' : null }
  }
  if (method === 'POST' && m(/\/letter$/)) {
    s.guardrail = cid === MARGARET && !s.guardrail && !s.scam && s.month === 0
    bump()
    return { letter_id: 'letter_1', status: 'draft', html: '', sections: dashboard(cid).sections, guardrail: dashboard(cid).guardrail }
  }
  if (method === 'GET' && p === '/demo/state') return { as_of: dashboard().as_of, events_applied: s.scam ? ['scam_transfer'] : [], facts_version: s.version }
  if (method === 'POST' && p === '/demo/next-month') { s.month = 1; bump(); return { as_of: dashboard().as_of } }
  if (method === 'POST' && p === '/demo/reset') { s = { ...fresh(), version: s.version + 1 }; return { as_of: dashboard().as_of } }

  if (method === 'GET' && p === '/cases') {
    const q = new URLSearchParams(query)
    const customer = q.get('customer') ?? MARGARET
    let list = allCases(customer).map(summary)
    if (q.get('status')) list = list.filter((c) => c.status === q.get('status'))
    if (q.get('urgency')) list = list.filter((c) => c.urgency === q.get('urgency'))
    return list.sort((a, c) => (a.urgency === c.urgency ? a.due.localeCompare(c.due) : a.urgency === 'high' ? -1 : 1))
  }
  if (method === 'POST' && p === '/cases') {
    const ticks = (b.ticks as string[]) ?? []
    const urgent = ticks.includes('worried') || ticks.includes('scam_call')
    const customer = String(b.customer ?? MARGARET)
    const c: Case = {
      ...fx('case.boiler.prepared'),
      id: `case_0${s.seq++}`, source: b.source, status: 'prepared', urgency: urgent ? 'high' : 'normal',
      category: 'general', summary: String(b.text || 'Question from the slip').slice(0, 80),
      question_text: b.text, ticks, helper_note: null, draft: null,
    }
    s.made.push({ customer, c })
    bump()
    return c
  }
  const cs = m(/^\/cases\/([^/]+)(?:\/(note|draft-reply|draft|approve))?$/)
  if (cs) {
    const [, id, action] = cs
    const c = [MARGARET, ...STANDIN_CUSTOMERS.map((x) => x.id)].flatMap((k) => allCases(k)).find((x) => x.id === id)
    if (!c) throw new MockHttpError(404, 'Case not found')
    const isBoiler = id === 'case_0007'
    if (method === 'GET' && !action) return c
    if (!isBoiler) return c
    if (action === 'note') { s.note = String(b.note); if (s.boiler === 'prepared') s.boiler = 'with_helper'; bump(); return boiler() }
    if (action === 'draft-reply') { s.boiler = 'draft_ready'; bump(); return boiler() }
    if (action === 'draft') { s.draftText = String(b.text); bump(); return boiler() }
    if (action === 'approve') {
      if (s.boiler !== 'draft_ready') throw new MockHttpError(409, 'The reply must be drafted and checked before it can be approved.')
      s.boiler = 'approved'; bump(); return boiler()
    }
  }
  throw new MockHttpError(404, `No mock for ${method} ${path}`)
}
