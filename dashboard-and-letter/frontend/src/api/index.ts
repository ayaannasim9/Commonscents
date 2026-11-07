import { handle } from './mock'
import type { Case, CaseSummary, Statement, WhatWeKnow, Customer, PersonaSummary, Dashboard, DemoEvent, DemoState, Tick } from './types'

export const pdfUrl = (id: string, preview = false) => `/api/customers/${id}/letter.pdf${preview ? '?preview=true' : ''}`
export const MOCK = import.meta.env.VITE_API_MODE !== 'live'
export const DEFAULT_CUSTOMER = 'MRG-4471'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  if (MOCK) {
    try {
      return (await handle(method, path, body)) as T
    } catch (e) {
      const err = e as { status?: number; message: string }
      throw new ApiError(err.status ?? 500, err.message)
    }
  }
  const res = await fetch(`/api${path}`, {
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
  letterHtml: (id: string) => request<string>('GET', `${c(id)}/letter.html`),
  regenerate: (id: string, badNumber = false) => request('POST', `${c(id)}/letter${badNumber ? '?demo=bad-number' : ''}`),
  approveLetter: (id: string) => request('POST', `${c(id)}/letter/approve`),
  whatWeKnow: (id: string) => request<WhatWeKnow>('GET', `${c(id)}/what-we-know`),
  addNote: (cid: string, note: string, helper: string) => request<Case>('POST', `/cases/${cid}/note`, { note, helper }),
  draftReply: (cid: string) => request<Case>('POST', `/cases/${cid}/draft-reply`),
  saveDraft: (cid: string, text: string) => request<Case>('POST', `/cases/${cid}/draft`, { text }),
  approve: (cid: string, helper: string) => request<Case>('POST', `/cases/${cid}/approve`, { helper }),
  demoState: () => request<DemoState>('GET', '/demo/state'),
  injectEvent: (id: string, event: DemoEvent) => request('POST', `${c(id)}/events`, { event }),
  nextMonth: () => request('POST', '/demo/next-month'),
  reset: () => request('POST', '/demo/reset'),
  cases: (id: string, q = '') => request<CaseSummary[]>('GET', `/cases?customer=${id}${q ? `&${q}` : ''}`),
  case: (id: string, viewer?: string) => request<Case>('GET', `/cases/${id}${viewer ? `?viewer=${viewer}` : ''}`),
  createCase: (customer: string, source: string, text: string, ticks: Tick[]) => request<Case>('POST', '/cases', { customer, source, text, ticks }),
}
