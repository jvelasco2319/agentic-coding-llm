from __future__ import annotations

from pathlib import Path

from ..config import AppConfig
from ..models import CommandResult, ValidationResult
from .import_check import run_basic_import_check
from .syntax_check import run_compileall
from .test_runner import run_command


class Validator:
    """
    Deterministic validation layer.

    The LLM can decide which tests/commands matter, but this class executes
    commands and records objective pass/fail evidence.
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def validate(self, repo_path: Path, extra_commands: list[str]) -> ValidationResult:
        commands: list[CommandResult] = []
        failures: list[str] = []

        syntax_passed = True
        import_passed = True
        unit_tests_passed = True
        smoke_tests_passed = True

        if self.config.run_compileall:
            result = run_compileall(repo_path)
            commands.append(result)
            syntax_passed = result.exit_code == 0
            if not syntax_passed:
                failures.append("compileall failed")

        if self.config.run_import_check:
            result = run_basic_import_check(repo_path)
            commands.append(result)
            import_passed = result.exit_code == 0
            if not import_passed:
                failures.append("basic import check failed")

        if self.config.run_pytest:
            result = run_command("python -m pytest -q", repo_path)
            commands.append(result)

            pytest_missing = "No module named pytest" in result.stderr

            if pytest_missing:
                # Do not fail validation just because pytest is not installed.
                # The LLM/test-designer may still provide unittest or smoke commands.
                unit_tests_passed = True
            else:
                unit_tests_passed = result.exit_code == 0
                if not unit_tests_passed:
                    failures.append("pytest failed")

        for cmd in extra_commands:
            if not cmd.strip():
                continue
            result = run_command(cmd, repo_path)
            commands.append(result)
            if result.exit_code != 0:
                smoke_tests_passed = False
                failures.append(f"extra validation command failed: {cmd}")

        passed = syntax_passed and import_passed and unit_tests_passed and smoke_tests_passed
        return ValidationResult(
            passed=passed,
            syntax_passed=syntax_passed,
            import_passed=import_passed,
            unit_tests_passed=unit_tests_passed,
            smoke_tests_passed=smoke_tests_passed,
            commands_run=commands,
            failures=failures,
        )
