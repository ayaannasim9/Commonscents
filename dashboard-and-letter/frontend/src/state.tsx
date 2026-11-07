import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, DEFAULT_CUSTOMER } from './api'
import type { Customer, Role } from './api/types'


interface Ctx {
  role: Role
  setRole: (r: Role) => void
  /** Id every customer-scoped API call uses. Switching it re-renders every screen from that person's data. */
  customerId: string
  setCustomerId: (id: string) => void
  customer: Customer | null
  large: boolean
  setLarge: (b: boolean) => void
  announce: (msg: string) => void
  live: string
}
const C = createContext<Ctx | null>(null)
// eslint-disable-next-line react-refresh/only-export-components
export const useApp = () => {
  const v = useContext(C)
  if (!v) throw new Error('useApp outside provider')
  return v
}

// eslint-disable-next-line react-refresh/only-export-components
export const HELPER = { name: 'Daria', roleLabel: 'Community banker' }

export function AppProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<Role>('customer')
  const [customerId, setCustomerState] = useState<string>(DEFAULT_CUSTOMER)
  const [customer, setCustomer] = useState<Customer | null>(null)
  // null = never chosen, so the customer's own preference applies (Margaret asks for large print).
  const [largeChoice, setLargeChoice] = useState<boolean | null>(null)
  const [live, setLive] = useState('')

  useEffect(() => {
    let live = true
    api.customer(customerId).then((c) => { if (live) setCustomer(c) }).catch(() => { if (live) setCustomer(null) })
    return () => { live = false }
  }, [customerId])

  const large = largeChoice ?? customer?.preferences.large_print ?? false


  const setRole = useCallback((r: Role) => { setRoleState(r) }, [])
  const setCustomerId = useCallback((id: string) => { setCustomerState(id) }, [])
  const setLarge = useCallback((b: boolean) => { setLargeChoice(b) }, [])
  const announce = useCallback((msg: string) => { setLive(''); setTimeout(() => setLive(msg), 50) }, [])

  const value = useMemo(
    () => ({ role, setRole, customerId, setCustomerId, customer, large, setLarge, announce, live }),
    [role, setRole, customerId, setCustomerId, customer, large, setLarge, announce, live],
  )
  return <C.Provider value={value}>{children}</C.Provider>
}
