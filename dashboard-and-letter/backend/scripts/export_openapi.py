"""Write contract/openapi.json from the live app."""
import json
from pathlib import Path

from counterpart.app import create_app

out = Path(__file__).resolve().parents[2] / "contract" / "openapi.json"
out.write_text(json.dumps(create_app(":memory:").openapi(), indent=2) + "\n")
print("wrote", out)
