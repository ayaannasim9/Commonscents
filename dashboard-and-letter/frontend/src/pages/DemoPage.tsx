import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import type { DemoEvent, Statement } from '../api/types'
import { DashboardView } from '../components/DashboardView'
import { LetterFrame } from '../components/LetterFrame'
import { PersonaPicker } from '../components/PersonaPicker'
import { GuardrailBadge } from '../components/ui'
import { longDate } from '../format'
import { useApp } from '../state'
import { useDashboard } from '../useDashboard'
import { useVersion } from '../useVersion'

const BUTTONS: { key: string; label: string; ev?: DemoEvent }[] = [
  { key: 'scam', label: 'Inject scam transfer', ev: 'scam_transfer' },
  { key: 'sub', label: 'Inject forgotten subscription', ev: 'forgotten_subscription' },
  { key: 'price', label: 'Inject price rise', ev: 'price_rise' },
]

/** F6: judge-facing demo control page. Statement on the left; letter or dashboard on the right. */
export default function DemoPage() {
  const { customerId, customer, announce } = useApp()
  const { data } = useDashboard()
  const version = useVersion()
  const [st, setSt] = useState<Statement | null>(null)
  const [tab, setTab] = useState<'letter' | 'dashboard'>('letter')
  const [busy, setBusy] = useState('')
  const [asOf, setAsOf] = useState('')
  const [msg, setMsg] = useState('')

  const loadState = useCallback(() => { api.demoState().then((s) => setAsOf(s.as_of)).catch(() => {}) }, [])
  useEffect(() => { api.transactions(customerId).then(setSt).catch(() => setSt(null)); loadState() }, [customerId, version, loadState])

  const act = async (key: string, f: () => Promise<unknown>, done: string) => {
    setBusy(key); setMsg('')
    try { await f(); setMsg(done); announce(done) } catch { setMsg('That did not work. Please try again.') }
    finally { setBusy(''); loadState() }
  }

  return (
    <div className="demo">
      <h1 className="page-title">Statement and letter</h1>
      <p className="lead">Left: what the bank statement looks like. Right: the same month as a letter and a dashboard.</p>
      <PersonaPicker />

      <div className="toolbar" role="group" aria-label="Demo controls">
        {BUTTONS.map((b) => (
          <button key={b.key} className="btn btn-demo" disabled={!!busy} onClick={() => act(b.key, () => api.injectEvent(customerId, b.ev!), `${b.label}: done.`)}>{busy === b.key ? 'Working…' : b.label}</button>
        ))}
        <button className="btn btn-demo" disabled={!!busy} onClick={() => act('next', () => api.nextMonth(), 'Moved on to next month.')}>{busy === 'next' ? 'Working…' : 'Next month'}</button>
        <button className="btn btn-demo btn-quiet" disabled={!!busy} onClick={() => act('regen', () => api.regenerate(customerId), 'Letter written again.')}>Regenerate</button>
        <button className="btn btn-demo btn-quiet" disabled={!!busy} onClick={() => act('bad', () => api.regenerate(customerId, true), 'Wrong number planted. Watch the guardrail catch it.')}>Plant a wrong number</button>
        <button className="btn btn-demo btn-quiet" disabled={!!busy} onClick={() => act('reset', () => api.reset(), 'Everything is back to the start.')}>Reset demo</button>
      </div>
      <p className="strip" role="status">{asOf ? `Letter date: ${longDate(asOf)}` : ''} {customer ? `· Showing ${customer.name}` : ''} {msg && `· ${msg}`}</p>

      <div className="demo-grid">
        <section aria-labelledby="stm" className="stmt">
          <h2 id="stm">The bank statement</h2>
          {!st ? <div className="skel" style={{ height: 400 }} aria-busy="true" /> : (
            <table>
              <caption className="visually-hidden">Bank statement for {st.month}</caption>
              <thead><tr><th scope="col">Date</th><th scope="col">What the bank calls it</th><th scope="col" className="num">Amount</th></tr></thead>
              <tbody>
                {st.transactions.map((t) => (
                  <tr key={t.id} className={t.amount < 0 && t.amount <= -1000 ? 'big' : ''}>
                    <td>{t.date.slice(8)}/{t.date.slice(5, 7)}{t.time ? ` ${t.time}` : ''}</td>
                    <td className="desc">{t.description}</td>
                    <td className={`num ${t.amount < 0 ? 'out' : 'in'}`}>{t.amount < 0 ? '−' : '+'}£{Math.abs(t.amount).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section aria-labelledby="rt" className="right">
          <h2 id="rt" className="visually-hidden">Letter and dashboard</h2>
          <div className="tabs" role="group" aria-label="Show">
            {(['letter', 'dashboard'] as const).map((t) => (
              <button key={t} type="button" className="chip" aria-pressed={tab === t} onClick={() => setTab(t)}>{t === 'letter' ? 'The letter' : 'The dashboard'}</button>
            ))}
          </div>
          {data && <GuardrailBadge guardrail={data.guardrail} />}
          {tab === 'letter' ? <LetterFrame customerId={customerId} /> : data ? (
            <div className="dash-embed"><DashboardView data={data} customerId={customerId} asking="counter_verbal" onAsked={() => {}} showGuardrail /></div>
          ) : <div className="skel" style={{ height: 600 }} aria-busy="true" />}
        </section>
      </div>
    </div>
  )
}
