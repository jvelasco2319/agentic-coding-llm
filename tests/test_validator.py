from pathlib import Path

from agentic_repo_cleaner.config import AppConfig
from agentic_repo_cleaner.validation.validator import Validator


def test_validator_can_compile_simple_repo(tmp_path: Path) -> None:
    (tmp_path / "example.py").write_text("x = 1\n", encoding="utf-8")
    config = AppConfig(run_pytest=False)
    result = Validator(config).validate(tmp_path, extra_commands=[])

    assert result.syntax_passed
    assert result.import_passed
    assert result.passed
