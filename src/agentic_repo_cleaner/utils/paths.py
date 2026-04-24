from __future__ import annotations

from pathlib import Path


def as_posix_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()
