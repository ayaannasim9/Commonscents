#!/usr/bin/env bash
# Start the whole Common Cents project. Ctrl+C stops everything.
#   Main app + ML engine   http://localhost:8001        (Overview app, forecasts, reports)
#   Dashboard & letters    http://localhost:5173        (Daria; backend on :8000)
#   Learning module        http://127.0.0.1:3000        (Ayaan; needs Supabase keys in .env.local)
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
PIDS=()
cleanup() { echo; echo "Stopping..."; for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null || true; done; }
trap cleanup EXIT INT TERM

echo "== 1/3 ML engine + main app (:8001)"
python3 -m pip install -q -r "$ROOT/ml/requirements.txt"
(cd "$ROOT/ml" && python3 -m uvicorn api:app --port 8001) & PIDS+=($!)

echo "== 2/3 Dashboard & letters (:8000 backend, :5173 frontend)"
DL="$ROOT/dashboard-and-letter"
if [ ! -x "$DL/backend/.venv/bin/uvicorn" ]; then
  if command -v uv >/dev/null; then (cd "$DL/backend" && uv venv .venv && uv pip install -p .venv/bin/python -e '.[pdf]')
  else (cd "$DL/backend" && python3 -m venv .venv && .venv/bin/pip install -q -e '.[pdf]'); fi
fi
[ -f "$DL/.env" ] || cp "$DL/.env.example" "$DL/.env"
[ -d "$DL/frontend/node_modules" ] || (cd "$DL/frontend" && npm install --silent)
(cd "$DL/backend" && .venv/bin/uvicorn counterpart.app:app --port 8000) & PIDS+=($!)
(cd "$DL/frontend" && VITE_API_MODE=live npm run dev -- --port 5173) & PIDS+=($!)

echo "== 3/3 Learning module (:3000)"
[ -d "$ROOT/node_modules" ] || (cd "$ROOT" && npm ci --silent)
(cd "$ROOT" && npm run dev) & PIDS+=($!)

sleep 4
cat <<MSG

  Common Cents is running:
    Main app (start here)   http://localhost:8001
    Dashboard & letters     http://localhost:5173
    Learning module         http://127.0.0.1:3000
    ML API docs             http://localhost:8001/docs

  Ctrl+C to stop.
MSG
wait
