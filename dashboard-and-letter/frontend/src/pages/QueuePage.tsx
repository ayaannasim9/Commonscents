import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import type { CaseSummary, PersonaSummary } from '../api/types'
import { longDate } from '../format'
import { Icon } from '../components/Icon'
import { SOURCE_LABEL, STATUS_LABEL } from '../labels'

export default function QueuePage() {
  const [cases, setCases] = useState<CaseSummary[] | null>(null)
  const [names, setNames] = useState<Record<string, PersonaSummary>>({})
  const [filter, setFilter] = useState<'all' | 'urgent'>('all')
  const [err, setErr] = useState(false)
  useEffect(() => { api.personas().then((l) => setNames(Object.fromEntries(l.map((p) => [p.id, p])))).catch(() => {}) }, [])
  useEffect(() => {
    let on = true
    const load = () => api.cases('all').then((c) => { if (on) { setCases(c); setErr(false) } }).catch(() => { if (on) setErr(true) })
    load(); const t = setInterval(load, 3000)
    return () => { on = false; clearInterval(t) }
  }, [])
  if (err && !cases) return <p className="errbox" role="alert">We could not load the questions. Please try again.</p>
  if (!cases) return <div className="skel" style={{ height: 320 }} aria-busy="true" />
  const shown = (filter === 'urgent' ? cases.filter((c) => c.urgency === 'high') : cases).filter((c) => c.status !== 'closed')
  return (
    <div>
      <h1 className="page-title">Questions</h1>
      <p className="lead">Urgent questions are at the top. Open one to see the dashboard with the briefing beside it.</p>
      <div className="chips" role="group" aria-label="Show">
        {(['all', 'urgent'] as const).map((f) => (
          <button key={f} type="button" className="chip" aria-pressed={filter === f} onClick={() => setFilter(f)}>{f === 'all' ? 'All questions' : 'Urgent only'}</button>
        ))}
      </div>
      {shown.length === 0 ? <p className="empty">No open questions.</p> : (
        <ul className="cases">
          {shown.map((c) => (
            <li key={c.id}>
              <Link to={`/cases/${c.id}`} className={`case-row ${c.urgency === 'high' ? 'urgent' : ''}`}>
                <span className="case-who">{names[c.customer]?.name ?? c.customer}</span>
                <span className="case-main">
                  <strong>{c.summary}</strong>
                  <span className="case-meta">{SOURCE_LABEL[c.source]} · due {longDate(c.due)}</span>
                </span>
                {c.urgency === 'high' && <span className="badge st-short"><Icon name="triangle" size={20} />Urgent</span>}
                <span className="chip-status">{STATUS_LABEL[c.status]}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
