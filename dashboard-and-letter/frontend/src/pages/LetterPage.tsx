import { useRef, useState } from 'react'
import { api, pdfUrl } from '../api'
import { LetterFrame } from '../components/LetterFrame'
import { useApp } from '../state'

export default function LetterPage() {
  const { customerId, role, announce } = useApp()
  const ref = useRef<HTMLIFrameElement>(null)
  const [approved, setApproved] = useState(false)
  const [busy, setBusy] = useState(false)
  const approve = async () => {
    setBusy(true)
    try { await api.approveLetter(customerId); setApproved(true); announce('The letter is approved and ready to print.') }
    catch { announce('We could not approve the letter.') }
    finally { setBusy(false) }
  }
  return (
    <div>
      <h1 className="page-title">Your letter</h1>
      <p className="lead">This is the same letter that arrives in the post. It says the same things as your dashboard.</p>
      <div className="actions">
        <button className="btn" onClick={() => ref.current?.contentWindow?.print()}>Print this letter</button>
        {role === 'helper' && !approved && <button className="btn btn-quiet" disabled={busy} onClick={approve}>{busy ? 'Approving…' : 'Approve letter for printing'}</button>}
        {role === 'helper' && approved && <span className="badge st-good">Approved</span>}
        <a className="btn btn-quiet" href={pdfUrl(customerId, !approved)} target="_blank" rel="noreferrer">{approved ? 'Open the PDF' : 'Preview the PDF'}</a>
      </div>
      <LetterFrame customerId={customerId} frameRef={ref} />
    </div>
  )
}
