import type { Case, CaseSummary, Statement, WhatWeKnow, Customer, PersonaSummary, Dashboard, DemoEvent, DemoState, Tick } from './types'

export const pdfUrl = (id: string, preview = false) => `/api/counterpart/customers/${id}/letter.pdf${preview ? '?preview=true' : ''}`
export const MOCK = false
export const DEFAULT_CUSTOMER = 'MRG-4471'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api/counterpart${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return (res.headers.get('content-type')?.includes('json') ? res.json() : res.text()) as Promise<T>
}

const c = (id: string) => `/customers/${id}`
export const api = {
  personas: () => request<PersonaSummary[]>('GET', '/personas'),
  customer: (id: string) => request<Customer>('GET', c(id)),
  dashboard: (id: string) => request<Dashboard>('GET', `${c(id)}/dashboard`),
  transactions: (id: string) => request<Statement>('GET', `${c(id)}/transactions`),
  letterStatus: (id: string) => request<{letter_id:string;status:string}>('GET', `${c(id)}/letter`),
  letterHtml: (id: string) => request<string>('GET', `${c(id)}/letter.html`),
  regenerate: (id: string, badNumber = false) => request('POST', `${c(id)}/letter${badNumber ? '?demo=bad-number' : ''}`),
  approveLetter: (id: string) => request('POST', `${c(id)}/letter/approve`),
  whatWeKnow: (id: string) => request<WhatWeKnow>('GET', `${c(id)}/what-we-know`),
  addNote: (cid: string, note: string, helper: string) => request<Case>('POST', `/cases/${cid}/note`, { note, helper }),
  draftReply: (cid: string) => request<Case>('POST', `/cases/${cid}/draft-reply`),
  saveDraft: (cid: string, text: string) => request<Case>('POST', `/cases/${cid}/draft`, { text }),
  approve: (cid: string, helper: string) => request<Case>('POST', `/cases/${cid}/approve`, { helper }),
  demoState: (id = DEFAULT_CUSTOMER) => request<DemoState>('GET', `/demo/state?customer=${encodeURIComponent(id)}`),
  injectEvent: (id: string, event: DemoEvent) => request('POST', `${c(id)}/events`, { event }),
  nextMonth: (id = DEFAULT_CUSTOMER) => request('POST', `/demo/next-month?customer=${encodeURIComponent(id)}`),
  reset: () => request('POST', '/demo/reset'),
  cases: (id: string, q = '') => request<CaseSummary[]>('GET', `/cases?customer=${id}${q ? `&${q}` : ''}`),
  case: (id: string, viewer?: string) => request<Case>('GET', `/cases/${id}${viewer ? `?viewer=${viewer}` : ''}`),
  createCase: (customer: string, source: string, text: string, ticks: Tick[]) => request<Case>('POST', '/cases', { customer, source, text, ticks }),
}
