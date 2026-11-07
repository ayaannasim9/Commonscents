PY := backend/.venv/bin/python

.PHONY: setup dev test print-month openapi
setup:
	cd backend && uv venv .venv && uv pip install -p .venv/bin/python -e '.[dev]'
dev:
	cd backend && .venv/bin/uvicorn counterpart.app:app --reload --port 8000
test:
	cd backend && .venv/bin/pytest -q
print-month:
	cd backend && .venv/bin/python scripts/print_month.py $(ARGS)
openapi:
	cd backend && .venv/bin/python scripts/export_openapi.py
