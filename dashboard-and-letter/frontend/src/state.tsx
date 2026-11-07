import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { Role } from './api/types'

const read = (k: string) => { try { return localStorage.getItem(k) } catch { return null } }
const write = (k: string, v: string) => { try { localStorage.setItem(k, v) } catch { /* private window: carry on without storage */ } }

interface Ctx {
  role: Role
  setRole: (r: Role) => void
  large: boolean
  setLarge: (b: boolean) => void
  announce: (msg: string) => void
  live: string
}
const C = createContext<Ctx | null>(null)
export const useApp = () => {
  const v = useContext(C)
  if (!v) throw new Error('useApp outside provider')
  return v
}

export const HELPER = { name: 'Priya', roleLabel: 'Community banker' }

export function AppProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<Role>(() => (['margaret', 'helper', 'family'].includes(read('cs.role') ?? '') ? (read('cs.role') as Role) : 'margaret'))
  // Margaret's profile asks for large print, so it is the default until she (or a helper) chooses otherwise.
  const [large, setLargeState] = useState<boolean>(() => (read('cs.large') ?? 'true') === 'true')
  const [live, setLive] = useState('')

  useEffect(() => { document.documentElement.dataset.large = String(large) }, [large])
  const setRole = useCallback((r: Role) => { setRoleState(r); write('cs.role', r) }, [])
  const setLarge = useCallback((b: boolean) => { setLargeState(b); write('cs.large', String(b)) }, [])
  const announce = useCallback((msg: string) => { setLive(''); setTimeout(() => setLive(msg), 50) }, [])

  const value = useMemo(() => ({ role, setRole, large, setLarge, announce, live }), [role, setRole, large, setLarge, announce, live])
  return <C.Provider value={value}>{children}</C.Provider>
}
