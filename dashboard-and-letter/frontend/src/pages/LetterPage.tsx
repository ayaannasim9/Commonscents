import { useEffect, useRef, useState } from 'react'
import { api, pdfUrl } from '../api'
import { LetterFrame } from '../components/LetterFrame'
import { useApp } from '../state'
import { useVersion } from '../useVersion'

export default function LetterPage() {
  const { customerId, role, announce } = useApp()
  const ref = useRef<HTMLIFrameElement>(null)
  const [approved, setApproved] = useState(false)
  const version=useVersion()
  useEffect(()=>{let active=true;setApproved(false);api.letterStatus(customerId).then(s=>{if(active)setApproved(s.status==='approved')}).catch(()=>{});return()=>{active=false}},[customerId,version])
  const [busy, setBusy] = useState(false)
  const approve = async () => {
    setBusy(true)
    try { await api.approveLetter(customerId); setApproved(true); announce('The letter is approved and ready to print.') }
    catch { announce('We could not approve the letter. Please try again. If it still fails, check that the dashboard service is running.') }
    finally { setBusy(false) }
  }
  return (
    <div>
      <h1 className="page-title">Your letter</h1>
      <p className="lead">This monthly preview uses the same figures as your dashboard. A helper reviews it before approval. This demo does not send post.</p>
      <div className="actions">
        <button className="btn" onClick={() => ref.current?.contentWindow?.print()}>Print preview</button>
        {role === 'helper' && !approved && <button className="btn btn-quiet" disabled={busy} onClick={approve}>{busy ? 'Approving…' : 'Approve letter for printing'}</button>}
        {role === 'helper' && approved && <span className="badge st-good">Approved</span>}
        <a className="btn btn-quiet" href={pdfUrl(customerId, !approved)} target="_blank" rel="noreferrer" aria-label={`${approved ? 'Open the PDF' : 'Preview the PDF'} (opens in a new tab)`}>{approved ? 'Open the PDF' : 'Preview the PDF'}</a>
      </div>
      <LetterFrame customerId={customerId} frameRef={ref} />
    </div>
  )
}
