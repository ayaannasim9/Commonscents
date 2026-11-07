"""The only place that talks to Claude. Everything else goes through LLMClient.

Modes (LLM_MODE): stub = never call out (writers use templates); cached = replay the on-disk
cache, never call out; live = cache first, then call Claude and store the answer.
Any failure raises LLMUnavailable, and the caller falls back to templates.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from .. import config

CACHE_DIR = config.ROOT / "backend" / "cache"


class LLMUnavailable(Exception):
    pass


class LLMClient:
    def __init__(self, mode: str | None = None, model: str | None = None, cache_dir: Path | None = None):
        self.mode = mode or config.LLM_MODE
        self.model = model if model is not None else config.ANTHROPIC_MODEL
        self.cache_dir = Path(cache_dir or CACHE_DIR)

    # -- cache --
    def _key(self, system: str, user: str, attempt: int) -> str:
        return hashlib.sha256(json.dumps([self.model, system, user, attempt]).encode()).hexdigest()[:40]

    def _read(self, key: str) -> dict | None:
        f = self.cache_dir / f"{key}.json"
        return json.loads(f.read_text())["output"] if f.exists() else None

    def _write(self, key: str, system: str, user: str, out: dict) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / f"{key}.json").write_text(
            json.dumps({"model": self.model, "system": system, "user": user, "output": out}, indent=2))

    # -- call --
    def complete_json(self, system: str, user: str, *, attempt: int = 0, fresh: bool = False) -> dict:
        if self.mode == "stub":
            raise LLMUnavailable("stub mode")
        key = self._key(system, user, attempt)
        if not fresh and (hit := self._read(key)) is not None:
            return hit
        if self.mode != "live":
            raise LLMUnavailable("not in cache")
        if not (os.environ.get("ANTHROPIC_API_KEY") and self.model):
            raise LLMUnavailable("ANTHROPIC_API_KEY or ANTHROPIC_MODEL not set")
        try:
            import anthropic

            msg = anthropic.Anthropic().messages.create(
                model=self.model, max_tokens=1500, system=system,
                messages=[{"role": "user", "content": user}],
            )
            out = _parse_json("".join(b.text for b in msg.content if b.type == "text"))
        except Exception as e:  # network, auth, rate limit, bad JSON: all mean "use the fallback"
            raise LLMUnavailable(f"{type(e).__name__}: {e}") from e
        self._write(key, system, user, out)
        return out


def _parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    out = json.loads(text)
    if not isinstance(out, dict):
        raise ValueError("expected a JSON object")
    return out
