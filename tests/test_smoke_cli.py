from typer.testing import CliRunner

from agentic_repo_cleaner.cli import app


def test_cli_help_runs() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_cli_models_runs() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["models"])
    assert result.exit_code == 0
    assert "glm-5.1:cloud" in result.stdout
    assert "minimax-m2.5:cloud" in result.stdout
    assert "kimi-k2.5:cloud" in result.stdout
