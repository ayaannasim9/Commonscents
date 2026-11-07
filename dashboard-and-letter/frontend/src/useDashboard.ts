import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api'
import type { Dashboard } from './api/types'
import { useApp } from './state'

/** Loads the dashboard and refetches whenever /demo/state reports a new facts_version (polled every 2 s). */
export function useDashboard() {
  const { announce } = useApp()
  const [data, setData] = useState<Dashboard | null>(null)
  const [error, setError] = useState(false)
  const version = useRef<number | null>(null)

  const load = useCallback(async (quiet = false) => {
    try {
      const d = await api.dashboard()
      version.current = d.facts_version
      setData(d); setError(false)
      if (quiet) announce('The dashboard has been updated.')
    } catch { setError(true) }
  }, [announce])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    const t = setInterval(async () => {
      if (document.hidden || version.current === null) return
      try {
        const s = await api.demoState()
        if (s.facts_version !== version.current) load(true)
      } catch { /* the next tick tries again */ }
    }, 2000)
    return () => clearInterval(t)
  }, [load])

  return { data, error, retry: () => { setError(false); load() } }
}
