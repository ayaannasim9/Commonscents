#!/usr/bin/env bash
# One command to run Common Cents: Next app (:3000) + dashboard backend (:8000) + ML engine (:8001).
set -e
cd "$(dirname "$0")"
python3 -m pip install -q -r ml/requirements.txt
[ -x dashboard-and-letter/backend/.venv/bin/python ] || npm run setup:dashboard
[ -d node_modules ] || npm install
echo "Open http://127.0.0.1:3000  (ML engine: http://127.0.0.1:8001/docs)"
npm run dev
