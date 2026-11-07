PY := backend/.venv/bin/python

.PHONY: setup dev frontend run test reset print-month openapi
setup:                       ## one-off: Python venv + frontend packages
	cd backend && uv venv .venv && uv pip install -p .venv/bin/python -e '.[dev,pdf]'
	cd frontend && npm install
dev:                         ## backend only, http://localhost:8000
	cd backend && .venv/bin/uvicorn counterpart.app:app --reload --port 8000
frontend:                    ## frontend only against the live backend, http://localhost:5173
	cd frontend && VITE_API_MODE=live npm run dev
run:                         ## backend + frontend together (Ctrl+C stops both)
	@trap 'kill 0' INT TERM EXIT; \
	(cd backend && .venv/bin/uvicorn counterpart.app:app --reload --port 8000) & \
	(cd frontend && VITE_API_MODE=live npm run dev) & \
	wait
test:
	cd backend && .venv/bin/pytest -q
reset:                       ## put the running demo back to its clean start
	curl -s -X POST http://localhost:8000/demo/reset && echo
print-month:
	cd backend && .venv/bin/python scripts/print_month.py $(ARGS)
openapi:
	cd backend && .venv/bin/python scripts/export_openapi.py
