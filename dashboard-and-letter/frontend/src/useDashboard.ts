import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api'
import type { Dashboard } from './api/types'
import { useApp } from './state'

/** Loads the dashboard and refetches whenever /demo/state reports a new facts_version (polled every 2 s). */
export function useDashboard() {
  const { announce, customerId } = useApp()
  const [data, setData] = useState<Dashboard | null>(null)
  const [error, setError] = useState(false)
  const version = useRef<number | null>(null)
  const current = useRef(customerId)
  current.current = customerId

  const load = useCallback(async (quiet = false) => {
    try {
      const d = await api.dashboard(customerId)
      if (current.current !== customerId) return // switched person while this was loading
      version.current = d.facts_version
      setData(d); setError(false)
      if (quiet) announce('The dashboard has been updated.')
    } catch { setError(true) }
  }, [announce, customerId])

  // A different customer is a different page: drop the old data so nobody sees one person's money under another's name.
  useEffect(() => { version.current = null; setData(null); setError(false); load() }, [load])
  useEffect(() => {
    const t = setInterval(async () => {
      if (document.hidden || version.current === null) return
      try {
        const s = await api.demoState(customerId)
        if (s.facts_version !== version.current) load(true)
      } catch { /* the next tick tries again */ }
    }, 2000)
    return () => clearInterval(t)
  }, [load])

  return { data, error, retry: () => { setError(false); load() } }
}
