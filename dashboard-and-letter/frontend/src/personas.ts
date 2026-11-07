import type { Archetype } from './api/types'
// Archetype labels appear only on the demo picker and the persona gallery, never on a customer's own dashboard.
export const ARCHETYPE_LABEL: Record<Archetype, string> = {
  elderly: 'Older customer',
  first_account: 'First account',
  recent_migrant: 'Recent migrant',
  low_literacy: 'Low literacy',
  learning_difficulty: 'Learning difficulty',
  never_budgeted: 'Never budgeted',
}
