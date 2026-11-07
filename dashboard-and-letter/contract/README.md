# Contract

The seam between `backend/` and `frontend/`. Source of truth is `plan.md` section C.

- `openapi.json`: exported from FastAPI (`make openapi`). Covers personas, customers, facts, dashboard, events, letter, what-we-know, cases and demo routes for all six customers; the PDF follows (B7).
- `fixtures/`: canned JSON responses. File names are fixed in `plan.md` section C7.

Rules: only the backend session edits this folder. The frontend reads it (mock mode: `VITE_API_MODE=mock`).
Backend contract tests compare live responses to these fixtures' keys and types.

Fixtures are written and number-checked (see plan.md section C7 for the story they tell). Regenerate only by hand-editing; keep totals consistent: statement net = `last_month.left`.
