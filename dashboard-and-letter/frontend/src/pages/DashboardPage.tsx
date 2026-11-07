import { DashboardSkeleton } from '../components/DashboardSkeleton'
import { DashboardView } from '../components/DashboardView'
import { Icon } from '../components/Icon'
import { useDashboard } from '../useDashboard'
import { useApp } from '../state'

export default function DashboardPage() {
  const { role, customerId } = useApp()
  const { data, error, retry } = useDashboard()
  if (error && !data)
    return (
      <div className="errbox" role="alert">
        <p><Icon name="info" size={24} /> We could not load this. Your letter has the same information.</p>
        <button className="btn" onClick={retry}>Try again</button>
      </div>
    )
  if (!data) return <DashboardSkeleton />
  return (
    <DashboardView
      data={data}
      customerId={customerId}
      asking={role === 'helper' ? 'counter_verbal' : 'hub_visit'}
      onAsked={() => {}}
      showGuardrail={role === 'helper'}
    />
  )
}
