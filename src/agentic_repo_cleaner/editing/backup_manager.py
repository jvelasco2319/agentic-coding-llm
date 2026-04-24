from __future__ import annotations

import shutil
from pathlib import Path


class BackupManager:
    def __init__(self, repo_path: Path, backup_dir: Path) -> None:
        self.repo_path = repo_path
        self.backup_dir = backup_dir
        self.backed_up: list[tuple[Path, Path]] = []

    def backup_paths(self, rel_paths: list[str]) -> None:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        for rel in sorted(set(rel_paths)):
            src = self.repo_path / rel
            dst = self.backup_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.exists() and src.is_file():
                shutil.copy2(src, dst)
                self.backed_up.append((src, dst))

    def restore_all(self) -> None:
        for src, dst in self.backed_up:
            if dst.exists():
                src.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, src)
