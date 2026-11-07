export default function Stub({ title, milestone }: { title: string; milestone: string }) {
  return (
    <div className="stub">
      <h1>{title}</h1>
      <p>This screen is planned for {milestone} and is not built yet.</p>
    </div>
  )
}
