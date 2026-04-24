from __future__ import annotations

from pathlib import Path


def load_guideline(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Guideline not found: {path}")
    return path.read_text(encoding="utf-8")
