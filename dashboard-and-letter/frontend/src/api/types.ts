// Hand-typed from plan.md section C. Money is whole pounds (integers); never do sums on it.
export type HeadlineStatus = 'good' | 'heads_up' | 'attention'
export type ForecastStatus = 'ok' | 'warn' | 'short'
export type FlagSeverity = 'info' | 'medium' | 'high'
export type Role = 'customer' | 'helper'
export type HelperRole = 'banker' | 'post_office' | 'phone'
export type CaseStatus = 'new' | 'prepared' | 'with_helper' | 'draft_ready' | 'approved' | 'closed'
export type CaseSource =
  | 'slip_post_office' | 'slip_post' | 'counter_verbal' | 'hub_visit' | 'phone' | 'system_flag'
export type Urgency = 'high' | 'normal'
export type CaseCategory = 'scam_worry' | 'afford_purchase' | 'bill_query' | 'payment_query' | 'general'
export type DemoEvent = 'scam_transfer' | 'forgotten_subscription' | 'price_rise'
export type Tick = 'worried' | 'scam_call' | 'bill' | 'afford' | 'other'

export interface Flag {
  id: string
  kind: 'unusual_payment' | 'new_regular_payment' | 'price_rise'
  severity: FlagSeverity
  date: string
  amount: number
  plain_name: string
  reasons: string[]
}

export interface Facts {
  as_of: string
  customer: { name: string; reference: string; bank: string; hub_day: string }
  headline_status: HeadlineStatus
  last_month: {
    month: string
    year: number
    in: number
    out: { name: string; amount: number }[]
    cash: number
    left: number
  }
  forecast: { month: string; year: number; status: ForecastStatus; reason: string; extra: number; spare: number }[]
  suggestion: { text_hint: string; amount: number } | null
  flags: Flag[]
  since_last_visit: { helper: string; note: string; date: string } | null
  cash_blind_spot: boolean
}

export interface GuardrailEvent {
  at: string
  check: 'numbers' | 'banned'
  detail: string
  action: 'regenerated' | 'blocked'
}
export interface Guardrail {
  caught: boolean
  events: GuardrailEvent[]
}

export type SectionId = 'headline' | 'last_month' | 'forecast' | 'idea' | 'scam_watch' | 'since_visit' | 'ask'
export interface Section {
  id: SectionId
  title: string
  text: string
  status?: HeadlineStatus | 'nothing_unusual' | 'flagged'
  optional?: boolean
}

export interface Dashboard {
  as_of: string
  facts_version: number
  facts: Facts
  guardrail: Guardrail
  sections: Section[]
}

export type Archetype = 'elderly' | 'first_account' | 'recent_migrant' | 'low_literacy' | 'learning_difficulty' | 'never_budgeted'

export interface PersonaSummary {
  id: string
  name: string
  age: number
  archetype: Archetype
  tagline: string
}

export interface Customer extends PersonaSummary {
  bank: string
  hub_day: string
  preferences: { large_print: boolean; read_aloud_default: boolean; language: string }
}

export interface DemoState {
  as_of: string
  events_applied: DemoEvent[]
  facts_version: number
}

export interface CaseSummary {
  id: string
  source: CaseSource
  status: CaseStatus
  urgency: Urgency
  category: CaseCategory
  summary: string
  created_at: string
  due: string
  route: { team: HelperRole; reason: string }
}

export interface Case extends CaseSummary {
  question_text: string
  ticks: Tick[]
  briefing: {
    asking: string
    numbers: { label: string; value: number }[]
    open_flags: string[]
    things_to_check: string[]
  }
  helper_note: string | null
  draft: { source: string; text: string; guardrail: Guardrail } | null
  approved_at: string | null
}
