import { useEffect, useRef } from 'react'
import { BrowserRouter, Navigate, NavLink, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import type { Role } from './api/types'
import DashboardPage from './pages/DashboardPage'
import DemoPage from './pages/DemoPage'
import PersonasPage from './pages/PersonasPage'
import Stub from './pages/Stub'
import { HELPER, useApp } from './state'


function AppBar() {
  const { role, setRole, large, setLarge, customer } = useApp()
  const roles: { v: Role; label: string }[] = [
    { v: 'customer', label: customer?.name ?? 'Customer' },
    { v: 'helper', label: 'Helper' },
  ]
  const links = [
    { to: '/dashboard', label: 'Dashboard' },
    role === 'helper' && { to: '/queue', label: 'Questions' },
    role === 'helper' && { to: '/demo', label: 'Demo' },
    role === 'helper' && { to: '/personas', label: 'People' },
    { to: '/letter', label: 'Letter' },
    { to: '/what-we-know', label: 'What we know' },
  ].filter(Boolean) as { to: string; label: string }[]
  return (
    <header>
     <div className="appbar">
      <div className="appbar-inner">
        <NavLink to="/" className="brand">Counterpart</NavLink>
        <nav className="mainnav" aria-label="Main">
          <ul>{links.map((l) => <li key={l.to}><NavLink to={l.to}>{l.label}</NavLink></li>)}</ul>
        </nav>
        <fieldset className="segmented">
          <legend>Who is looking</legend>
          {roles.map((r) => (
            <label key={r.v}>
              <input type="radio" name="role" value={r.v} checked={role === r.v} aria-label={r.v === 'customer' ? `${r.label} (customer view)` : r.label} onChange={() => setRole(r.v)} />
              {r.label}
            </label>
          ))}
        </fieldset>
        <label className="toggle">
          <input type="checkbox" checked={large} onChange={(e) => setLarge(e.target.checked)} />
          Bigger text
        </label>
      </div>
     </div>
     {role === 'helper' && <div className="helperstrip"><p>You are signed in as {HELPER.name}, {HELPER.roleLabel}.</p></div>}
    </header>
  )
}

const TITLES: Record<string, string> = {
  '/dashboard': 'Your money', '/queue': 'Questions', '/cases': 'Question', '/demo': 'Statement and letter',
  '/personas': 'People', '/what-we-know': 'What we know about you', '/letter': 'Your letter',
}

function Layout() {
  const { live } = useApp()
  const { pathname } = useLocation()
  const main = useRef<HTMLElement>(null)
  const prev = useRef(pathname)
  useEffect(() => {
    const t = TITLES[pathname.replace(/^\/cases\/.+/, '/cases')] ?? 'Counterpart'
    document.title = t === 'Counterpart' ? t : `${t} - Counterpart`
  }, [pathname])
  useEffect(() => {
    if (prev.current === pathname) return
    prev.current = pathname
    main.current?.focus({ preventScroll: true }); window.scrollTo(0, 0)
  }, [pathname])
  return (
    <>
      <a className="skip-link" href="#main">Skip to the main content</a>
      <AppBar />
      <main id="main" ref={main} tabIndex={-1} className="main"><div className="page"><Outlet /></div></main>
      <footer className="footer">
        <div className="footer-inner">
          <p>Prototype, not an official NatWest product. All names and figures are made up.</p>
          <NavLink to="/what-we-know">What we know about you</NavLink>
        </div>
      </footer>
      <div className="visually-hidden" role="status" aria-live="polite">{live}</div>
    </>
  )
}

function Guard({ allow, children }: { allow: Role[]; children: React.ReactElement }) {
  const { role } = useApp()
  return allow.includes(role) ? children : <Navigate to="/dashboard" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Guard allow={['customer', 'helper']}><DashboardPage /></Guard>} />
          <Route path="/queue" element={<Guard allow={['helper']}><Stub title="Questions" milestone="F5" /></Guard>} />
          <Route path="/cases/:id" element={<Guard allow={['helper']}><Stub title="Question" milestone="F4" /></Guard>} />
          <Route path="/demo" element={<Guard allow={['helper']}><DemoPage /></Guard>} />
          <Route path="/personas" element={<Guard allow={['helper']}><PersonasPage /></Guard>} />
          <Route path="/what-we-know" element={<Stub title="What we know about you" milestone="F8" />} />
          <Route path="/letter" element={<Stub title="Your letter" milestone="F9" />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
