import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import type { Dashboard, PersonaSummary } from '../api/types'
import { StatusBadge } from '../components/ui'
import { ARCHETYPE_LABEL } from '../personas'
import { useApp } from '../state'

type Card = { p: PersonaSummary; d: Dashboard | null }

/** F7: six people, one product. Each card shows that person's own headline, verbatim from their dashboard. */
export default function PersonasPage() {
  const { setCustomerId, announce } = useApp()
  const nav = useNavigate()
  const [cards, setCards] = useState<Card[] | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let live = true
    api.personas()
      .then((ps) => Promise.all(ps.map(async (p) => ({ p, d: await api.dashboard(p.id).catch(() => null) }))))
      .then((c) => { if (live) setCards(c) })
      .catch(() => { if (live) setFailed(true) })
    return () => { live = false }
  }, [])

  const open = (p: PersonaSummary) => { setCustomerId(p.id); announce(`Now showing ${p.name}.`); nav('/dashboard') }

  return (
    <div className="personas-page">
      <h1>Six people, one product</h1>
      <p className="sec-text">The same dashboard, letter and rules for everyone. Only the data differs. Pick a person to open their dashboard.</p>
      <p className="sec-text"><Link to="/demo">Back to the demo</Link></p>
      {failed ? (
        <p role="alert">We could not load the people. Please try again.</p>
      ) : (
        <ul className="persona-grid" aria-busy={!cards}>
          {(cards ?? Array.from({ length: 6 }, () => null)).map((c, i) => (
            <li key={c?.p.id ?? i}>
              {c ? (
                <button type="button" className="persona-card" onClick={() => open(c.p)}>
                  <span className="persona-top">
                    <span className="persona-name">{c.p.name}, {c.p.age}</span>
                    <span className="persona-arch">{ARCHETYPE_LABEL[c.p.archetype]}</span>
                  </span>
                  <span className="persona-tag">{c.p.tagline}</span>
                  {c.d && (
                    <>
                      <StatusBadge status={c.d.facts.headline_status} />
                      <span className="persona-head">{c.d.sections.find((s) => s.id === 'headline')?.text}</span>
                    </>
                  )}
                </button>
              ) : (
                <div className="skel persona-card" aria-hidden="true" />
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
