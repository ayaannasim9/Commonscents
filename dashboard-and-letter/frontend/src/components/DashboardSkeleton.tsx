// Heights match the loaded sections so nothing jumps when data arrives.
const H = [220, 520, 360, 200, 260, 120, 640]
export function DashboardSkeleton() {
  return (
    <div className="dash" aria-busy="true" aria-label="Loading your dashboard">
      {H.map((h, i) => <div key={i} className="skel" style={{ height: h, marginTop: i ? 64 : 0 }} />)}
    </div>
  )
}
