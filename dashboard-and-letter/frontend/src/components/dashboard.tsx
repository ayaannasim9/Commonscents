import { useId, useState, type FormEvent, type ReactNode } from 'react'
import { api } from '../api'
import type { Facts, Flag, Tick } from '../api/types'
import { longDate, pounds, sentence } from '../format'
import { Icon } from './Icon'
import { ReadAloudButton, StatusBadge } from './ui'

export function Section({ id, title, text, level = 2, children }: { id: string; title: string; text: string; level?: 1 | 2; children: ReactNode }) {
  const H = `h${level}` as 'h1' | 'h2'
  return (
    <section className="sec" aria-labelledby={`h-${id}`} id={id}>
      <div className="sec-head">
        <H id={`h-${id}`}>{title}</H>
        <ReadAloudButton id={id} title={title} text={text} />
      </div>
      {children}
    </section>
  )
}

function MoneyBar({ label, amount, of, cls = '' }: { label: string; amount: number; of: number; cls?: string }) {
  // Bar length is decoration only; every value is also written as text beside it.
  const w = Math.max(2, Math.min(100, (amount / of) * 100))
  return (
    <li className={`bar ${cls}`}>
      <div className="bar-head"><span>{label}</span><span className="bar-val">{pounds(amount)}</span></div>
      <div className="bar-track" aria-hidden="true"><div className="bar-fill" style={{ width: `${w}%` }} /></div>
    </li>
  )
}

export function LastMonthBars({ lm }: { lm: Facts['last_month'] }) {
  const neg = lm.left < 0
  return (
    <ul className="bars" aria-label={`${lm.month} in numbers`}>
      <MoneyBar label="Money in" amount={lm.in} of={lm.in} cls="bar-in" />
      {lm.out.map((o) => <MoneyBar key={o.name} label={o.name} amount={o.amount} of={lm.in} />)}
      <MoneyBar label="Cash from the Post Office" amount={lm.cash} of={lm.in} cls="bar-cash" />
      <li className={`bar bar-left ${neg ? 'neg' : ''}`}>
        <div className="bar-head">
          <span>{neg ? 'More went out than came in' : 'Left over'}</span>
          <span className="bar-val">{pounds(Math.abs(lm.left))}</span>
        </div>
      </li>
    </ul>
  )
}

export function MonthCards({ forecast }: { forecast: Facts['forecast'] }) {
  return (
    <ul className="months" aria-label="Forecast for each month">
      {forecast.map((f) => (
        <li key={f.month + f.year} className="month">
          <h3>{f.month}</h3>
          <StatusBadge status={f.status} kind="forecast" />
          <p className="month-reason">{sentence(f.reason)}{f.extra > 0 && <> ({pounds(f.extra)} extra)</>}</p>
          <p className="month-spare"><span>Expected spare</span><strong>{pounds(f.spare)}</strong></p>
        </li>
      ))}
    </ul>
  )
}

const SEV: Record<Flag['severity'], { word: string; cls: string; icon: string }> = {
  high: { word: 'Please look at this', cls: 'st-short', icon: 'info' },
  medium: { word: 'Worth checking', cls: 'st-warn', icon: 'triangle' },
  info: { word: 'For your information', cls: 'st-info', icon: 'info' },
}
export function FlagCard({ flag }: { flag: Flag }) {
  const sev = SEV[flag.severity]
  return (
    <article className={`flag sev-${flag.severity}`} id={flag.id} aria-labelledby={`t-${flag.id}`}>
      <span className={`badge ${sev.cls}`} style={{ justifySelf: 'start' }}><Icon name={sev.icon} size={22} />{sev.word}</span>
      <h3 id={`t-${flag.id}`}>{flag.plain_name}, {longDate(flag.date)}</h3>
      <ul>{flag.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
      <p className="flag-calm">You do not have to do anything. Your helper can talk it through with you.</p>
    </article>
  )
}

const TICKS: { v: Tick; label: string }[] = [
  { v: 'worried', label: 'I am worried about something' },
  { v: 'scam_call', label: 'Someone has asked me for money' },
  { v: 'bill', label: 'A bill looks wrong' },
  { v: 'afford', label: 'Can I afford something?' },
  { v: 'other', label: 'Something else' },
]

export function QuestionForm({ customerId, source, onAsked }: { customerId: string; source: string; onAsked: () => void }) {
  const [ticks, setTicks] = useState<Tick[]>([])
  const [text, setText] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const errId = useId()

  if (done)
    return (
      <p className="ask-done" role="status"><Icon name="check-circle" size={32} />Thank you. Priya or a colleague will reply by letter.</p>
    )

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!ticks.length && !text.trim()) return setErr('Please tick a box or write your question, then send it.')
    setErr(''); setBusy(true)
    try {
      await api.createCase(customerId, source, text.trim(), ticks)
      setDone(true); onAsked()
    } catch {
      setErr('We could not send that just now. Nothing was lost. Please try again, or ask your helper.')
    } finally { setBusy(false) }
  }
  return (
    <form className="ask-form" onSubmit={submit} noValidate aria-describedby={err ? errId : undefined}>
      <fieldset>
        <legend>What is this about? (tick any that fit)</legend>
        <div className="tiles">
          {TICKS.map((t) => (
            <label key={t.v} className="tile">
              <input type="checkbox" checked={ticks.includes(t.v)} onChange={(e) => setTicks(e.target.checked ? [...ticks, t.v] : ticks.filter((x) => x !== t.v))} />
              {t.label}
            </label>
          ))}
        </div>
      </fieldset>
      <div>
        <label htmlFor="ask-text" className="lbl" style={{ display: 'block' }}>Your question (you can leave this blank)</label>
        <textarea id="ask-text" value={text} onChange={(e) => setText(e.target.value)} />
      </div>
      <p id={errId} className="err" role="alert" style={{ minHeight: err ? undefined : 0 }}>{err && <><Icon name="info" size={24} />{err}</>}</p>
      <div><button className="btn" type="submit" disabled={busy}>{busy ? 'Sending…' : 'Send my question'}</button></div>
    </form>
  )
}
