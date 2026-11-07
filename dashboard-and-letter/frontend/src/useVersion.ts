import { useEffect, useState } from 'react'
import { api } from './api'

/** facts_version from /demo/state, polled every 2 s. Screens refetch their own data when it changes. */
export function useVersion() {
  const [v, setV] = useState<number | null>(null)
  useEffect(() => {
    let on = true
    const tick = async () => {
      if (document.hidden) return
      try { const s = await api.demoState(); if (on) setV(s.facts_version) } catch { /* try again next tick */ }
    }
    tick()
    const t = setInterval(tick, 2000)
    return () => { on = false; clearInterval(t) }
  }, [])
  return v
}
