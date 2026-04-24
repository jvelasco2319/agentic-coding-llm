from pathlib import Path

from agentic_repo_cleaner.context.guideline_loader import load_guideline


def test_load_guideline(tmp_path: Path) -> None:
    guideline = tmp_path / "guideline.md"
    guideline.write_text("# Guideline\nPreserve behavior.", encoding="utf-8")

    assert "Preserve behavior" in load_guideline(guideline)
