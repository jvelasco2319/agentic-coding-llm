from __future__ import annotations

from pathlib import Path

from .test_runner import run_command
from ..models import CommandResult


def run_smoke_commands(repo_path: Path, commands: list[str]) -> list[CommandResult]:
    return [run_command(cmd, repo_path) for cmd in commands]
