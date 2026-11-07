import { handle } from './mock'
import type { Case, CaseSummary, Customer, Dashboard, DemoEvent, DemoState, Tick } from './types'

export const MOCK = import.meta.env.VITE_API_MODE !== 'live'
export const CUSTOMER_ID = 'MRG-4471'

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

const c = `/customers/${CUSTOMER_ID}`
export const api = {
  customer: () => request<Customer>('GET', c),
  dashboard: () => request<Dashboard>('GET', `${c}/dashboard`),
  demoState: () => request<DemoState>('GET', '/demo/state'),
  injectEvent: (event: DemoEvent) => request('POST', `${c}/events`, { event }),
  nextMonth: () => request('POST', '/demo/next-month'),
  reset: () => request('POST', '/demo/reset'),
  cases: (q = '') => request<CaseSummary[]>('GET', `/cases${q}`),
  case: (id: string, viewer?: string) => request<Case>('GET', `/cases/${id}${viewer ? `?viewer=${viewer}` : ''}`),
  createCase: (source: string, text: string, ticks: Tick[]) => request<Case>('POST', '/cases', { source, text, ticks }),
}
