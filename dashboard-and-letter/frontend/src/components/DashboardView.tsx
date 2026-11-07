import type { Dashboard, Section as Sec } from '../api/types'
import { longDate } from '../format'
import { FlagCard, LastMonthBars, MonthCards, QuestionForm, Section } from './dashboard'
import { Icon } from './Icon'
import { GuardrailBadge, StatusBadge } from './ui'

/** The shared dashboard. Pure render of the dashboard payload: sections in array order, text verbatim (P9, P10). */
export function DashboardView({ data, customerId, asking, onAsked, showGuardrail }: { data: Dashboard; customerId: string; asking: string; onAsked: () => void; showGuardrail: boolean }) {
  const { facts } = data
  const body = (s: Sec) => {
    switch (s.id) {
      case 'headline':
        return (
          <>
            <StatusBadge status={facts.headline_status} className="headline-badge" />
            <p className={`headline-text ${s.text.length > 90 ? 'long' : ''}`}>{s.text}</p>
          </>
        )
      case 'last_month':
        return (<><p className="sec-text">{s.text}</p><LastMonthBars lm={facts.last_month} /></>)
      case 'forecast':
        return (<><p className="sec-text">{s.text}</p><MonthCards forecast={facts.forecast} /></>)
      case 'idea':
        return (
          <div className="idea">
            {facts.suggestion && <p className="idea-amount">£{facts.suggestion.amount.toLocaleString('en-GB')} a month</p>}
            <p>{s.text}</p>
          </div>
        )
      case 'scam_watch':
        return (
          <>
            {s.status === 'flagged' && facts.flags.length ? facts.flags.map((f) => <FlagCard key={f.id} flag={f} />) : (
              <p className="watch" aria-hidden="true"><Icon name="shield" size={36} />Nothing unusual this month</p>
            )}
            <p>{s.text}</p>
          </>
        )
      case 'since_visit':
        return (
          <div className="since">
            <p>{s.text}</p>
            {facts.since_last_visit && <p className="since-by">{facts.since_last_visit.helper}, {longDate(facts.since_last_visit.date)}</p>}
          </div>
        )
      case 'ask':
        return (<><p>{s.text}</p><QuestionForm customerId={customerId} source={asking} onAsked={onAsked} /></>)
    }
  }
  return (
    <div className="dash">
      {showGuardrail && <GuardrailBadge guardrail={data.guardrail} />}
      {data.sections.map((s) => (
        <Section key={s.id} id={s.id} title={s.title} text={s.text} level={s.id === 'headline' ? 1 : 2}>
          {body(s)}
        </Section>
      ))}
    </div>
  )
}
