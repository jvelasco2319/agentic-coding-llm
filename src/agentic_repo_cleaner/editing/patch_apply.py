from __future__ import annotations

from pathlib import Path

from ..models import FileEdit


def _ensure_inside_repo(repo_path: Path, rel_path: str) -> Path:
    target = (repo_path / rel_path).resolve()
    repo_resolved = repo_path.resolve()
    if repo_resolved not in target.parents and target != repo_resolved:
        raise ValueError(f"Path escapes repo: {rel_path}")
    return target


def apply_file_edits(
    repo_path: Path,
    changed_files: list[FileEdit],
    added_files: list[FileEdit],
    deleted_files: list[str],
) -> None:
    for edit in [*changed_files, *added_files]:
        target = _ensure_inside_repo(repo_path, edit.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(edit.content, encoding="utf-8")

    for rel in deleted_files:
        target = _ensure_inside_repo(repo_path, rel)
        if target.exists() and target.is_file():
            target.unlink()
