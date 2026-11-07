import { useSyncExternalStore } from 'react'
import type { ForecastStatus, Guardrail, HeadlineStatus } from '../api/types'
import { useApp } from '../state'
import { Icon } from './Icon'

type Look = { cls: string; icon: string; word: string }
const HEADLINE: Record<HeadlineStatus, Look> = {
  good: { cls: 'st-good', icon: 'check-circle', word: 'Looking good' },
  heads_up: { cls: 'st-warn', icon: 'triangle', word: 'Worth a look' },
  attention: { cls: 'st-short', icon: 'talk', word: 'Worth talking through' },
}
const FORECAST: Record<ForecastStatus, Look> = {
  ok: HEADLINE.good,
  warn: HEADLINE.heads_up,
  short: { cls: 'st-short', icon: 'cross', word: 'Tight' },
}
export function StatusBadge({ status, kind = 'headline', className = '' }: { status: HeadlineStatus | ForecastStatus; kind?: 'headline' | 'forecast'; className?: string }) {
  const look = (kind === 'forecast' ? FORECAST : HEADLINE)[status as never] as Look
  return (
    <span className={`badge ${look.cls} ${className}`}>
      <Icon name={look.icon} size={22} />
      {look.word}
    </span>
  )
}

/* Read aloud: reads the section's text string (the letter's words), not the DOM. */
const speechOk = typeof window !== 'undefined' && 'speechSynthesis' in window
let current: string | null = null
const subs = new Set<() => void>()
const setCurrent = (id: string | null) => { current = id; subs.forEach((f) => f()) }
const subscribe = (f: () => void) => { subs.add(f); return () => { subs.delete(f) } }

export function ReadAloudButton({ id, title, text }: { id: string; title: string; text: string }) {
  const speaking = useSyncExternalStore(subscribe, () => current === id, () => false)
  const { customer } = useApp()
  if (!speechOk) return null
  const toggle = () => {
    window.speechSynthesis.cancel()
    if (current === id) return setCurrent(null)
    const u = new SpeechSynthesisUtterance(text)
    u.lang = 'en-GB'
    u.rate = 0.9
    u.onend = u.onerror = () => { if (current === id) setCurrent(null) }
    setCurrent(id)
    window.speechSynthesis.speak(u)
  }
  return (
    <button type="button" className={`read ${speaking ? 'on' : ''} ${customer?.preferences.read_aloud_default ? 'emph' : ''}`} aria-label={`${speaking ? 'Stop' : 'Read this out loud'}: ${title}`} onClick={toggle}>
      <Icon name={speaking ? 'stop' : 'speaker'} size={22} />
      {speaking ? 'Stop' : 'Read this out loud'}
    </button>
  )
}

/* Helpers and the demo page only; never rendered for Margaret. */
export function GuardrailBadge({ guardrail }: { guardrail: Guardrail }) {
  if (!guardrail.caught) return null
  return (
    <details className="guardrail-details">
      <summary className="guardrail-badge"><Icon name="shield" size={22} /> Guardrail caught this</summary>
      <ul>
        {guardrail.events.map((e) => (
          <li key={e.at + e.detail}>{e.detail}, so it was {e.action}.</li>
        ))}
      </ul>
    </details>
  )
}
