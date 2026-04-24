from __future__ import annotations

import subprocess
from pathlib import Path

from ..models import CommandResult


def run_command(command: str, cwd: Path, timeout: int = 300) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return CommandResult(
        command=command,
        cwd=str(cwd),
        exit_code=completed.returncode,
        stdout=completed.stdout[-12000:],
        stderr=completed.stderr[-12000:],
    )
