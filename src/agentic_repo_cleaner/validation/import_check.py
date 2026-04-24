from __future__ import annotations

from pathlib import Path

from .test_runner import run_command
from ..models import CommandResult


def run_basic_import_check(repo_path: Path) -> CommandResult:
    return run_command("python -c \"import sys; print('python ok', sys.version.split()[0])\"", repo_path)
