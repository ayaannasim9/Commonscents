import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import type { Case } from '../api/types'
import { DashboardSkeleton } from '../components/DashboardSkeleton'
import { DashboardView } from '../components/DashboardView'
import { HelperPanel } from '../components/HelperPanel'
import { HELPER, useApp } from '../state'
import { useDashboard } from '../useDashboard'

/** The shared dashboard, exactly as the customer sees it, with the helper panel docked beside it. */
export default function CasePage() {
  const { id = '' } = useParams()
  const { customerId, setCustomerId } = useApp()
  const [c, setC] = useState<Case | null>(null)
  const [err, setErr] = useState(false)
  useEffect(() => {
    let on = true
    setC(null); setErr(false)
    api.case(id, `helper:${HELPER.name.toLowerCase()}`).then((x) => { if (on) setC(x) }).catch(() => { if (on) setErr(true) })
    return () => { on = false }
  }, [id])
  // Show the right person's money: the case's customer becomes the active one.
  useEffect(() => { if (c && c.customer !== customerId) setCustomerId(c.customer) }, [c, customerId, setCustomerId])
  const { data } = useDashboard()

  if (err) return <p className="errbox" role="alert">We could not open this question. <Link to="/queue">Back to the questions</Link></p>
  if (!c) return <div className="skel" style={{ height: 500 }} aria-busy="true" />
  return (
    <div className="casepage">
      <p className="back"><Link to="/queue">← All questions</Link></p>
      <div className="case-grid">
        <div className="case-dash">
          {data && c.customer === customerId ? (
            <DashboardView data={data} customerId={customerId} asking="counter_verbal" onAsked={() => {}} showGuardrail />
          ) : <DashboardSkeleton />}
        </div>
        <HelperPanel c={c} onChange={setC} />
      </div>
    </div>
  )
}
