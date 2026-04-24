from __future__ import annotations

from pathlib import Path

from .test_runner import run_command
from ..models import CommandResult


def run_compileall(repo_path: Path) -> CommandResult:
    return run_command("python -m compileall -q .", repo_path)
