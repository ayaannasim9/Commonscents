import { useEffect, useState } from 'react'
import { api, ApiError } from '../api'
import type { Case } from '../api/types'
import { pounds, longDate } from '../format'
import { HELPER } from '../state'
import { SOURCE_LABEL, STATUS_LABEL } from '../labels'
import { Icon } from './Icon'
import { GuardrailBadge } from './ui'

/** Helper-only tools. Sits NEXT TO the shared dashboard; nothing here changes what the customer sees (P10). */
export function HelperPanel({ c, onChange }: { c: Case; onChange: (c: Case) => void }) {
  const [note, setNote] = useState(c.helper_note ?? '')
  const [draft, setDraft] = useState(c.draft?.text ?? '')
  const [busy, setBusy] = useState('')
  const [err, setErr] = useState('')
  const [confirm, setConfirm] = useState(false)
  useEffect(() => { setDraft(c.draft?.text ?? '') }, [c.draft?.text])
  const locked = c.status === 'approved' || c.status === 'closed'

  const run = async (name: string, f: () => Promise<Case>) => {
    setBusy(name); setErr('')
    try { onChange(await f()) }
    catch (e) { setErr(e instanceof ApiError && e.status === 409 ? 'This cannot be approved yet. Make sure there is a reply draft that passed the checks.' : 'That did not work. Nothing was changed. Please try again.') }
    finally { setBusy(''); setConfirm(false) }
  }

  return (
    <aside className="hpanel" aria-label="Helper tools">
      <h2>For the helper</h2>
      <p className="hp-meta">{SOURCE_LABEL[c.source]} · due {longDate(c.due)}</p>
      <p className="hp-route"><span className={`badge ${c.urgency === 'high' ? 'st-short' : 'st-info'}`}>{c.urgency === 'high' ? 'Urgent' : 'Normal'}</span> {c.route.reason}</p>
      <p className="hp-status">Status: <strong>{STATUS_LABEL[c.status]}</strong></p>

      <section aria-labelledby="hp-ask"><h3 id="hp-ask">She is asking</h3>
        <p>{c.briefing.asking}</p>
        {c.question_text && <blockquote>{c.question_text}</blockquote>}
      </section>

      {c.briefing.numbers.length > 0 && (
        <section aria-labelledby="hp-num"><h3 id="hp-num">Relevant numbers</h3>
          <dl className="hp-nums">{c.briefing.numbers.map((n) => <div key={n.label}><dt>{n.label}</dt><dd>{pounds(n.value)}</dd></div>)}</dl>
          <p className="hp-small">From the dashboard, worked out by code.</p>
        </section>
      )}

      {c.briefing.open_flags.length > 0 && (
        <section aria-labelledby="hp-flags"><h3 id="hp-flags">Open flags</h3>
          <ul>{c.briefing.open_flags.map((f) => <li key={f}><a href="#scam_watch">See {f} in Scam watch</a></li>)}</ul>
        </section>
      )}

      <section aria-labelledby="hp-check"><h3 id="hp-check">Things to check or mention</h3>
        <ul className="hp-checks">{c.briefing.things_to_check.map((t, i) => (
          <li key={i}><label><input type="checkbox" /> {t}</label></li>
        ))}</ul>
      </section>

      <section aria-labelledby="hp-note"><h3 id="hp-note">Your notes</h3>
        <label className="visually-hidden" htmlFor="note">Your notes</label>
        <textarea id="note" value={note} onChange={(e) => setNote(e.target.value)} disabled={locked} placeholder="What did you agree together?" />
        <button className="btn btn-quiet" disabled={locked || !note.trim() || !!busy} onClick={() => run('note', () => api.addNote(c.id, note.trim(), HELPER.name))}>{busy === 'note' ? 'Saving…' : 'Save note'}</button>
      </section>

      <section aria-labelledby="hp-draft"><h3 id="hp-draft">Reply to her</h3>
        {!c.draft && <button className="btn" disabled={locked || !!busy} onClick={() => run('draft', () => api.draftReply(c.id))}>{busy === 'draft' ? 'Drafting…' : 'Draft reply'}</button>}
        {c.draft && (
          <>
            <GuardrailBadge guardrail={c.draft.guardrail} />
            <label className="visually-hidden" htmlFor="draft">Reply draft</label>
            <textarea id="draft" className="tall" value={draft} onChange={(e) => setDraft(e.target.value)} disabled={locked} />
            <div className="hp-row">
              <button className="btn btn-quiet" disabled={locked || draft === c.draft.text || !!busy} onClick={() => run('save', () => api.saveDraft(c.id, draft))}>{busy === 'save' ? 'Saving…' : 'Save edit'}</button>
              <button className="btn btn-quiet" disabled={locked || !!busy} onClick={() => run('draft', () => api.draftReply(c.id))}>Draft again</button>
            </div>
          </>
        )}
      </section>

      <section aria-labelledby="hp-ok"><h3 id="hp-ok">Approve</h3>
        {locked ? (
          <p className="hp-done" role="status"><Icon name="check-circle" size={28} /> Approved{c.approved_at ? ` on ${longDate(c.approved_at)}` : ''}. It goes in the next letter.</p>
        ) : confirm ? (
          <div className="hp-confirm" role="group" aria-label="Confirm approval">
            <p>This will be sent as a letter. Please check the numbers first.</p>
            <div className="hp-row">
              <button className="btn" disabled={!!busy} onClick={() => run('approve', () => api.approve(c.id, HELPER.name))}>{busy === 'approve' ? 'Approving…' : 'Yes, approve'}</button>
              <button className="btn btn-quiet" onClick={() => setConfirm(false)}>Cancel</button>
            </div>
          </div>
        ) : (
          <button className="btn" disabled={c.status !== 'draft_ready' || !!busy} onClick={() => setConfirm(true)}>Approve and send</button>
        )}
        {c.status !== 'draft_ready' && !locked && <p className="hp-small">You can approve once a reply has been drafted.</p>}
      </section>
      <p className="err" role="alert" style={{ minHeight: err ? undefined : 0 }}>{err && <><Icon name="info" size={24} /> {err}</>}</p>
    </aside>
  )
}
