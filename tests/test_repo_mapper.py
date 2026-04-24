from pathlib import Path

from agentic_repo_cleaner.context.repo_mapper import RepoMapper


def test_repo_mapper_detects_python_symbols(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    file_path = tmp_path / "src" / "example.py"
    file_path.write_text(
        "class Example:\n    pass\n\ndef run():\n    return 1\n",
        encoding="utf-8",
    )

    repo_map = RepoMapper().map_repo(tmp_path)

    paths = [f.path for f in repo_map.files]
    assert "src/example.py" in paths

    summary = next(f for f in repo_map.files if f.path == "src/example.py")
    assert "Example" in summary.important_symbols
    assert "run" in summary.important_symbols
