# Commonscents learning module

Local financial education prototype using Next.js, React, TypeScript, Tailwind CSS and Supabase PostgreSQL. Includes four UK life-situation journeys with 17 lessons and 51 scenario questions, practical checklists, source links, server-graded quizzes and persistent progress. The six original foundation lessons remain in the database to preserve earlier progress. No authentication or browser persistence.

## Start

1. Run `npm ci` to install the locked dependencies, including the pinned Supabase CLI.
2. Copy `.env.example` to `.env.local` and fill in your development project's URL and **server secret** key (or legacy service-role key). A publishable key alone cannot access these protected tables.
3. Apply the repository migrations using the terminal workflow below. No SQL Editor copy/paste is required.
4. Run `npm run dev` and open http://127.0.0.1:3000.

Without configuration, the app displays a labelled layout preview with lessons disabled. There is no local-storage fallback.

## Reproducible database migrations

SQL files in `supabase/migrations/` are the source of truth. Track them together with `supabase/config.toml`, `package.json` and `package-lock.json` in Git. The initial migration includes starter lessons and the temporary demo learner because the prototype needs them in both local and hosted development databases. Separate optional test fixtures can be added later.

### Existing hosted development project

Run from the repository root:

```sh
npm run db:login
npm run db:link -- --project-ref YOUR_PROJECT_REF
npm run db:history
npm run db:plan
npm run db:deploy
```

`YOUR_PROJECT_REF` is the identifier in your project's `https://<ref>.supabase.co` URL. Login uses a Supabase account access token/browser flow, separate from the application's API secret key. Follow the CLI prompts privately; do not put credentials in source files or command arguments. The CLI may need database credentials depending on your account access.

`db:plan` previews pending migrations without applying them. `db:deploy` applies pending files and records their versions in Supabase migration history; subsequent runs skip applied files. Both explicitly target the linked remote project. Vault synchronization is disabled for these commands because this module does not manage project secrets.

If a project already has tables or migration history from the parent application, reconcile that baseline before deploying this module. If the initial SQL was previously run manually, verify it matches the migration before marking its version applied; do not rerun it blindly or reset the hosted database.

### Optional fully local database

Requires a running Docker-compatible container runtime:

```sh
npm run db:start
npm run db:migrate:local
npm run db:status
```

Use the local API URL and server key shown by the status command in `.env.local`, then restart Next.js. These commands target the local stack by default in the pinned CLI version. `npm run db:stop` stops it. Local configuration currently selects PostgreSQL 17; align this with your hosted project's major version before relying on full-stack parity. The Docker stack has not yet been started or verified on this machine.

### Future schema changes

```sh
npm run db:migration:new -- add_learning_feature
# Edit the generated SQL file.
npm test
npm run db:migrate:local
npm run db:plan
npm run db:deploy
```

Add a new migration for each change; do not rewrite migrations already applied to shared environments. `npm test` replays every migration in filename order against an isolated PGlite database. For full Supabase verification, replay against the optional local stack as well. CLI state in `supabase/.temp/` and credentials are ignored by Git.

## Accessible starting guides and scam protection

The default journey for new learners is `independent` (Managing money for the first time). Migration `202611070003_accessible_money_basics.sql` also switches the demo learner to it once, preserving completions and XP. Later explicit journey choices still persist.

`content/money-guide.json` contains a tailored introduction for every journey plus 18 plain-English money terms with examples and source links. The definitions are educational information, not product recommendations. All paths expose the same `own-scams` lesson, stored once under the independent journey; completing it from any path awards XP only once and counts towards the independent path. The independent journey has five lessons; other paths have four. Its final unit contains one lesson, so denominators are dynamic.

The interface uses larger default reading text, native expandable explanations, labelled search, visible focus, reduced-motion support and a session-only larger-text toggle. Lesson reading can be revisited with Previous explanation. Test with older learners and assistive technology before public release; automated checks are not a usability certification.

## UK learning content

`content/journeys.json` is the editable content reference for the UK journeys. The immutable database snapshot is `supabase/migrations/202611070002_uk_journeys.sql`. Future published content edits must be delivered in a new migration; editing JSON alone does not update Supabase. `lib/journey-preview.ts` contains public metadata only, never quiz answers.

Each lesson includes a realistic scenario, three questions, an optional practical checklist, primary guidance links and a source-check date (7 November 2026). Monetary examples are fictional exercises, not benefit entitlements, tax calculations or recommended budgets. Nation-specific differences are called out rather than treating England's rules as universal. This is a researched prototype, not professional financial/legal review. Recheck sources before a public release and when rules change.

The initial migration was applied in the SQL Editor. The journeys migration was applied from its local file using the CLI's HTTPS-backed SQL command after direct database connections timed out:

```sh
npx --no-install supabase db query --remote --file supabase/migrations/202611070002_uk_journeys.sql
```

All three migrations (including `202611070003_accessible_money_basics.sql`) are already applied to the currently linked project. Do not rerun them there. This SQL API route does not populate the CLI migration ledger. Before the next `db:deploy`, verify the deployed schema and reconcile the applied versions (`202611070001`, `202611070002`, `202611070003`) using Supabase migration history repair once database connectivity works. Fresh environments can replay the migration files in order with the normal CLI workflow.

## Architecture

- `app/components/learning-app.tsx`: interactive path, library, progress and quiz UI.
- `app/api/learn/route.ts`: server-only question delivery, feedback and completion API.
- `lib/learning.ts`: database-to-UI adapter.
- `lib/supabase.ts`: server-only database client and temporary demo learner identity.
- `lib/progress.ts`: progress and streak calculations; prototype timezone is Europe/London.
- `supabase/migrations/`: schema, reviewed starter content and transactional grading function.

University and first-job paths unlock in order within each journey. First-time money management and bills allow any topic to be opened immediately. The selected journey persists on the demo learner. The bills journey hides daily targets and streak displays and provides a direct link to free debt advice.

Quiz pass threshold: 2/3. All attempts persist; a lesson awards 30 XP on its first successful completion. Replaying does not award additional XP or extend a streak. Completion requests have unique IDs and are idempotent. A learner-row lock serializes concurrent completion requests. Streaks count consecutive dates with newly completed lessons, remaining active until the day after the last completion. Lesson explanations are intentionally available during a quiz because this is a learning exercise, not an exam.

RLS is enabled with no browser policies. Credentials remain server-only. Demo endpoints deliberately share one fixed learner and are **not suitable for public hosting**; development and start commands bind to loopback. During integration, replace the demo learner with the parent app's verified server identity, add authorization for every learner-specific request and configure the learner timezone. Keep the existing parent-app authentication system.

## Verification

`npm test` runs the migration and reward/security checks in an isolated PostgreSQL-compatible PGlite instance, plus timezone and streak checks. It never touches your Supabase project. Also run `npm run typecheck` and `npm run build`. Webpack is selected because Turbopack's CSS worker could not bind its internal port in this environment. With a configured database: complete a lesson, reload and check progress; replay it and confirm no duplicate XP; verify locked lessons cannot be loaded; retry a failed submission and confirm the request is idempotent.
