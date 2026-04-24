from pathlib import Path

from agentic_repo_cleaner.editing.patch_apply import apply_file_edits
from agentic_repo_cleaner.models import FileEdit


def test_apply_file_edits_writes_file(tmp_path: Path) -> None:
    apply_file_edits(
        tmp_path,
        changed_files=[FileEdit(path="a.py", content="x = 1\n", reason="test")],
        added_files=[],
        deleted_files=[],
    )

    assert (tmp_path / "a.py").read_text(encoding="utf-8") == "x = 1\n"
