import { useEffect, useState } from 'react'
import { api } from '../api'
import type { PersonaSummary } from '../api/types'
import { ARCHETYPE_LABEL } from '../personas'
import { useApp } from '../state'

/** F6.6: switches the active customer. Does not reset anything; every screen re-renders from that person's data. */
export function PersonaPicker() {
  const { customerId, setCustomerId, announce } = useApp()
  const [list, setList] = useState<PersonaSummary[] | null>(null)
  useEffect(() => { api.personas().then(setList).catch(() => setList([])) }, [])
  if (!list) return <div className="skel" style={{ height: 76 }} aria-busy="true" />
  if (!list.length) return <p>We could not load the list of people. Please try again.</p>
  return (
    <fieldset className="picker">
      <legend>Whose dashboard</legend>
      <div className="picker-opts">
        {list.map((p) => (
          <label key={p.id} className="picker-opt">
            <input type="radio" name="persona" value={p.id} checked={customerId === p.id}
              onChange={() => { setCustomerId(p.id); announce(`Now showing ${p.name}.`) }} />
            <span className="picker-name">{p.name}</span>
            <span className="picker-arch">{ARCHETYPE_LABEL[p.archetype]}</span>
          </label>
        ))}
      </div>
    </fieldset>
  )
}
