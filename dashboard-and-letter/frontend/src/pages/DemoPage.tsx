import { Link } from 'react-router-dom'
import { PersonaPicker } from '../components/PersonaPicker'
import { useApp } from '../state'

// F6 is only partly built: the persona picker (F6.6) lives here; statement, letter tabs and event buttons come later.
export default function DemoPage() {
  const { customer } = useApp()
  return (
    <div className="stub">
      <h1>Statement and letter</h1>
      <PersonaPicker />
      <p style={{ marginTop: 24 }}>Showing {customer?.name ?? 'the selected person'}. The statement, letter and event buttons are planned for F6 and are not built yet.</p>
      <p style={{ marginTop: 16 }}><Link to="/personas">See all six people side by side</Link> or <Link to="/dashboard">open the dashboard</Link>.</p>
    </div>
  )
}
