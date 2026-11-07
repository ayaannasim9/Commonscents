import { useEffect, useState } from 'react'
import { api } from '../api'
import type { WhatWeKnow } from '../api/types'
import { longDate } from '../format'
import { useApp } from '../state'
import { useVersion } from '../useVersion'

export default function WhatWeKnowPage() {
  const { customerId } = useApp()
  const [d, setD] = useState<WhatWeKnow | null>(null)
  const [err, setErr] = useState(false)
  const version = useVersion()
  useEffect(() => {
    let on = true
    api.whatWeKnow(customerId).then((x) => { if (on) { setD(x); setErr(false) } }).catch(() => { if (on) setErr(true) })
    return () => { on = false }
  }, [customerId, version])
  if (err && !d) return <p className="errbox" role="alert">We could not load this page. Please try again.</p>
  if (!d) return <div className="skel" style={{ height: 600 }} aria-busy="true" />
  const p = d.profile
  return (
    <article className="wwk">
      <h1 className="page-title">What we know about {p.name}</h1>
      <p className="lead">This is everything we hold about you, and everyone who has looked at it.</p>
      <div className="actions no-print"><button className="btn" onClick={() => window.print()}>Print this page</button></div>

      <section aria-labelledby="w-about"><h2 id="w-about">About you</h2>
        <dl className="facts">
          <div><dt>Name</dt><dd>{p.name}</dd></div>
          <div><dt>Age</dt><dd>{p.age}</dd></div>
          <div><dt>Your bank</dt><dd>{p.bank}</dd></div>
          <div><dt>Your hub day</dt><dd>{p.hub_day}</dd></div>
        </dl>
      </section>

      <section aria-labelledby="w-held"><h2 id="w-held">What we hold</h2>
        <ul className="held">
          {d.data_held.map((x) => (
            <li key={x.label}><div><strong>{x.label}</strong><p>{x.description}</p></div><span className="count" aria-label={`${x.count} held`}>{x.count}</span></li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="w-log"><h2 id="w-log">Who has looked</h2>
        {d.access_log.length === 0 ? <p>Nobody has looked at your information yet.</p> : (
          <ul className="log">
            {d.access_log.map((a, i) => (
              <li key={a.at + i}><span className="when">{longDate(a.at)}, {a.at.slice(11, 16)}</span><span><strong>{a.who}</strong> ({a.role.replace('_', ' ')}): {a.what}</span></li>
            ))}
          </ul>
        )}
      </section>
    </article>
  )
}
