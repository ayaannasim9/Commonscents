# Accessibility and restoration review — 7 November 2026

## NatWise UI update

Reference: the remote `OverviewOfApp/Overview/styles.css`, retrieved from GitHub on 7 November 2026. The purple header, gold logo, rounded cards and section navigation are retained. The application is renamed NatWise, including its page title and standalone dashboard branding. `app/accessibility.css` applies shared fixes after the existing module styles.

Implemented in this pass:

- Fixed the header gradient so dark-mode accent colours cannot reduce white-text contrast. Darkened Wrapped gradients and strengthened form borders. High contrast now includes the header, controls and Wrapped cards; added Windows forced-colour styles.
- Shared system font, relative font sizing, four visible text-size settings up to double size, and screen-reader announcements of changes. The dark-mode button reflects the system theme on first load.
- Dashboard sections use the reference branch's rounded cards and readable body-sized summaries. Spending labels remain outside chart bars.
- Visible keyboard focus, a skip link, native labelled controls, larger helper controls and wrapped layouts. Onboarding moves focus to its first question. Reduced motion includes pseudo-elements and scrolling; removed the perpetual lesson pulse.
- Letter PDF links announce that they open a new tab. Approval errors include a recovery step. Decorative icons stay hidden from screen readers, and chart values/statuses have text equivalents.

Executed browser checks:

- Start, Dashboard, Future, Wrapped, Learn, Support and Report: **320 CSS pixels wide with double-size text; document scrollWidth = 320 on all seven tabs**. This tests reflow and text scaling; it is not an actual browser-zoom test.
- Dashboard dark-theme visible text: computed foreground/background sample found no failures against 4.5:1 normal / 3:1 large text. This does not cover every state, gradient, PDF or graphic.
- Keyboard End moved focus from Dashboard to Report, a solid focus outline was present, and Enter activated Report.
- Submitting an empty question displayed an alert: “Please tick a box or write your question, then send it.” No case was submitted.
- High-contrast light mode produced black header text on white, with matching controls. System dark-mode state was correctly exposed as pressed.

Not yet verified: actual 200%/400% browser zoom, OS forced-colours/reduced-motion settings, comprehensive automated contrast scanning, and end-to-end VoiceOver, NVDA and TalkBack. These require a manual assistive-technology acceptance pass before claiming WCAG conformance. There is no autoplaying media; captions/transcripts are not applicable to the current screens.

Scope: combined overview shell and Learn panel. This is a WCAG-inspired engineering review, not a declaration of WCAG 2.2 AA conformance. Checks below distinguish implemented features from executed tests.

## Restored content inventory

Compared against [original Overview/app.js](https://github.com/ayaannasim9/Commonscents/blob/OverviewOfApp/Overview/app.js), blob `fa1d4ef5602d21a3d1f9bfb69a398ed92062b284` (GitHub and local Git object matched).

| Original unit | Restored lessons |
| --- | --- |
| Banking in the UK | What is a current account?; Sort code and account number; Is my money safe? |
| Your NatWest app | Download and log in; Your home screen; Pay someone |
| The NatWest website | Log in online; Statements and settings |
| Stay safe and get help | Spot a scam; Getting help |

All 10 lessons, 30 teaching cards, 30 exercises, four guidebooks and the optional four-question knowledge check are retained. Existing 17 life-situation lessons remain. The bank account demo details are never requested from learners. Matching, ordering, missing-word and multiple-choice tasks retain their learning objectives. Ordering uses buttons rather than dragging. Knowledge-check recommendations do not falsely award learning completion; the original mock streak, arbitrary starting points and reward chest points were not imported.

Security/product wording was reviewed: pending debit payments, balances versus spendable money, account identifiers, payment-status uncertainty, deposit eligibility, and HTTPS/padlocks. Original source content is preserved separately from the reviewed version. Sources are attached to lessons. The revised HTTPS explanation is consistent with [Canadian Centre for Cyber Security guidance](https://www.cyber.gc.ca/en/guidance/shopping-online-safely-itsap00071), and pending-payment wording with [NatWest guidance](https://www.natwest.com/current-accounts/bank-account-guides/pending-transactions.html).

## Checklist and evidence

| Area | Implemented / checked | Still to verify |
| --- | --- | --- |
| Contrast | Shared theme colours, dark/high-contrast support; sampled visible banking-path text in dark theme had no computed failures against 4.5:1 normal / 3:1 large-text thresholds. | Full contrast audit of every state and overview graphic, including gradients, disabled controls and focus indicators. |
| Non-colour information | Correct/incorrect feedback is text; selected answers have native selected state; completion uses ticks and text. | Comprehensive review of remaining overview charts. |
| Images/media | Decorative Penny SVG is hidden from accessibility tree. No video/audio added; no autoplay added. Existing overview chart has an accessible description. | Any future meaningful images need text alternatives; future videos need captions/transcripts. |
| Reflow/text | 320px viewport with extra-large text: tested reading, missing-word and ordering screens had scrollWidth equal to viewport width. Mobile main navigation wraps and is not sticky. | Actual 200% and 400% browser zoom across all overview tabs, browsers and orientations. Narrow viewport is a reflow check, not a claim to have tested browser zoom. |
| Keyboard | Native radios/selects, labelled matching dropdowns, Move up/down ordering, no drag requirement; ordering completed using Enter and graded correctly. Main tabs have aria-controls, roving tabindex and Arrow/Home/End handling; Home key tested. | Full keyboard journey through every overview form and lesson result state. |
| Focus | Visible focus styles; lesson headings receive focus on screen change; answer feedback receives focus; boundary move buttons use aria-disabled so focus can remain on the moved item. Verified feedback focus in matching/ordering. | Manual screen-reader focus review, backwards navigation, OS high-contrast modes. |
| Targets | Buttons minimum 44px, dropdowns minimum 48px, answer labels are large targets. | Complete automated target-size audit including inline links and overview controls. |
| Motion | Shared reduced-motion CSS disables animations/transitions; learning scroll checks reduced-motion preference. No timed questions or flashing learning content. | OS reduced-motion toggle smoke test across all overview tabs. |
| Language/errors | Plain language; fieldsets and legends; corrections explain the answer; failed network requests preserve retryable attempts. | Plain-language review with older users and live failure-mode tests. |
| Semantics/ARIA | Native controls and details, labelled tab panels, progressbar values, status announcements, one shared main landmark. Accessibility snapshots show restored controls and labels. | NVDA, VoiceOver and TalkBack end-to-end testing; automated accessibility scanner. |

## Executed functional checks

- Fresh local SQL replay including migration 004; all prior grading, locks, invalid-input, RLS, streak and idempotency tests pass.
- Original lesson-ID inventory compared to restored curriculum. All 10 lessons tested for incorrect answers, correct completion and no duplicate XP.
- All four exercise styles represented. Matching/order encodings checked against stored questions.
- Browser: matching dropdowns selected and graded; ordering completed by keyboard and graded; missing-word native radios exposed correctly.
- Existing hosted progress was retained. Browser test questions did not complete a lesson or award XP.

## Assistive-technology acceptance pass still needed

Run VoiceOver + Safari, NVDA + Firefox/Chrome and TalkBack + Chrome. For each: navigate to Learn, open a course and guide, read explanations, complete every exercise type, hear feedback, exit, change tabs and confirm saved completion. Check pronunciation, reading order, announcement duplication, focus visibility and no traps. Repeat at 200%/400% zoom and with text spacing overrides. Record actual results before changing this document to “passed”.
