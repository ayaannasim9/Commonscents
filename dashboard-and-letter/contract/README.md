# Contract

The seam between `backend/` and `frontend/`. Source of truth is `plan.md` section C.

- `openapi.json`: exported from FastAPI once backend B0 exists (not yet present).
- `fixtures/`: canned JSON responses. File names are fixed in `plan.md` section C7.

Rules: only the backend session edits this folder. The frontend reads it (mock mode: `VITE_API_MODE=mock`).
Backend contract tests compare live responses to these fixtures' keys and types.
