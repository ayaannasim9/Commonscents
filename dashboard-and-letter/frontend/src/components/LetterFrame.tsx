import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { useVersion } from '../useVersion'

/** The letter exactly as the backend renders it (same HTML as the PDF), shown as a sheet of paper. */
export function LetterFrame({ customerId, frameRef }: { customerId: string; frameRef?: React.RefObject<HTMLIFrameElement | null> }) {
  const [html, setHtml] = useState<string | null>(null)
  const [err, setErr] = useState(false)
  const [h, setH] = useState(900)
  const inner = useRef<HTMLIFrameElement>(null)
  const ref = frameRef ?? inner
  const version = useVersion()
  useEffect(() => {
    let on = true
    api.letterHtml(customerId).then((t) => { if (on) { setHtml(t); setErr(false) } }).catch(() => { if (on) setErr(true) })
    return () => { on = false }
  }, [customerId, version])
  if (err && !html) return <p className="errbox" role="alert">We could not load the letter. Please try again in a moment.</p>
  if (!html) return <div className="skel" style={{ height: 900 }} aria-busy="true" />
  return (
    <div className="paper">
      <iframe
        ref={ref}
        title="Your monthly letter"
        srcDoc={html}
        sandbox="allow-same-origin allow-modals"
        style={{ height: h }}
        onLoad={(e) => { const d = e.currentTarget.contentDocument; if (d) setH(d.documentElement.scrollHeight + 8) }}
      />
    </div>
  )
}
