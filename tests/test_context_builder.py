from pathlib import Path

from agentic_repo_cleaner.config import AppConfig
from agentic_repo_cleaner.context.context_builder import ContextBuilder
from agentic_repo_cleaner.context.repo_mapper import RepoMapper


def test_context_builder_reads_selected_files(tmp_path: Path) -> None:
    (tmp_path / "cli.py").write_text("print('hello')", encoding="utf-8")

    repo_map = RepoMapper().map_repo(tmp_path)
    context = ContextBuilder(AppConfig()).build_initial_context(tmp_path, repo_map)

    assert "cli.py" in context
    assert "hello" in context["cli.py"]
