import type { CaseSource, CaseStatus } from './api/types'
export const SOURCE_LABEL: Record<CaseSource, string> = {
  slip_post_office: 'Slip handed in at the Post Office', slip_post: 'Slip sent by post', counter_verbal: 'Asked at the counter',
  hub_visit: 'Asked at the hub', phone: 'Phone call', system_flag: 'Noticed by the system',
}
export const STATUS_LABEL: Record<CaseStatus, string> = {
  new: 'New', prepared: 'Ready to look at', with_helper: 'Being looked at', draft_ready: 'Reply drafted', approved: 'Approved', closed: 'Closed',
}
