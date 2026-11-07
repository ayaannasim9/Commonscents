"""Settings from the environment (never hard-code keys)."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]  # dashboard-and-letter/
load_dotenv(ROOT / ".env")

DB_PATH = Path(os.environ.get("COUNTERPART_DB", ROOT / "backend" / "counterpart.db"))
LLM_MODE = os.environ.get("LLM_MODE", "stub")  # live | cached | stub (used from B4)
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "")
SEED = int(os.environ.get("COUNTERPART_SEED", "4471"))
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
