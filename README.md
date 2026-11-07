# NatWise

The overview is the application homepage. Its **Learn** tab contains the Supabase-backed learning journeys in the same page. The overview header, navigation, text size, contrast and dark-mode controls are shared across all sections. `/learn` redirects to `/#learn` for older bookmarks.

## Run locally

```sh
npm install
npm run setup:dashboard
npm run dev
```

Open http://127.0.0.1:3000/. Keep Supabase credentials in `.env.local` using `.env.example` as a template. Never commit credentials. Learning progress uses the existing demo learner; authentication is not implemented.

- `/`: existing overview with integrated Dashboard and Report panels.
- `/#learn`: four UK life-situation journeys plus the restored 10-lesson Banking basics course, glossary, scam protection and quizzes within the overview.
- `/api/learn`: server-side Supabase learning API.

The overview still uses mock data. Its banking connection, forecasts and support matching are demonstrations, not live integrations. The original Future and Wrapped examples remain separate from the selected dashboard customer. Its former in-memory learning implementation has been replaced by the learning module.

## Dashboard and monthly letter

Integrated from `daria-dashboard-and-letter` into `overview-learning-integration`. The Dashboard tab includes spending, forecasts, scam watch and questions. Report displays the selected customer's monthly letter with print and PDF previews. Helper view exposes the question queue, case notes, draft replies, approval, six fictional people and demo controls. Nothing is actually posted or sent; the role switch is a demo control, not authentication.

`npm run dev` starts Next on port 3000 and the Python FastAPI service on port 8000 (or reuses an already-running backend). Python 3.11+ is required. Run `npm run dev:web` or `npm run dev:dashboard` to start either separately. The browser calls the same-origin `/api/counterpart/*` proxy. The default template writer requires no AI key.

Learning remains in Supabase. Imported dashboard cases, notes and approvals currently persist in the ignored local SQLite database `dashboard-and-letter/backend/counterpart.db`; they have not been migrated to Supabase. Customer selection and the demo role are held in memory. PDF generation uses ReportLab without native system libraries, preserves the letter's wording and figures, and retains the approval requirement for final PDFs.

The imported components live in `dashboard-and-letter/frontend/src`; `app/components/dashboard-module.tsx` mounts them inside the overview shell. Shared colours, contrast and text sizing apply through `app/dashboard-theme.css`. After editing imported styles or that theme, run `npm run styles:dashboard` to regenerate the scoped stylesheet.

## Source files

Edit `Overview/index.html`, `Overview/styles.css` and `Overview/app.js` for the overview. The homepage renders the HTML shell and mounts the React learning module into its Learn panel; scripts and styles remain editable here. The original `Overview/common-cents.html` and zip are standalone reference snapshots, not the running application.

The learning UI lives in `app/components/`, its integration in `app/components/overview-app.tsx`, and its content in `content/`. `app/learning-integrated.css` scopes learning styles to the module and uses the overview’s theme variables. Learning remains mounted when changing tabs, preserving an in-progress explanation or question.

## Database and verification

SQL migrations remain versioned in `supabase/migrations/`. Migration `202611070004_restore_original_banking.sql` adds the original banking course and exercise metadata without changing existing completions. The existing hosted database was set up by applying those SQL files; reconcile its migration history before using `db:deploy` to avoid replaying them.

```sh
npm run typecheck
npm test
npm run test:dashboard
npm run build
# With the local app running:
npm run test:integration
```

Display controls apply to all sections. The optional starting-point selector recommends a journey without bypassing lesson completion. Banking basics also retains the original four-question knowledge check and four unit guidebooks. Gold Penny, unit milestones, all ten original lessons and the screen/branch guide are adapted from the overview’s original learning experience; progress and grading remain backed by Supabase. Overview onboarding and display preferences remain in memory for the current page session.


## Restored original content

The original GitHub `Overview/app.js` blob is `fa1d4ef5602d21a3d1f9bfb69a398ed92062b284`. Its lesson data is retained unchanged in `content/original/overview-banking.json`. `scripts/restore-banking.py` builds the reviewed course and additive migration, preserving original lesson IDs with a `bank-` prefix, all 30 reading cards and all 30 exercises. Do not edit an already-applied migration; use a new migration for future changes.

Matching and ordering are rendered as labelled selects and move buttons. Their complete answer combinations map to server-graded option indices, so the existing transactional grading and idempotent XP mechanism remain authoritative. Banking basics is flexible; the knowledge check suggests where to start without granting completions or XP.

See `docs/accessibility-review.md` for verified checks and remaining assistive-technology tests. This is not a WCAG conformance certification.
