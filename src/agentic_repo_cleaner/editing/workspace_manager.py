from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import AppConfig


@dataclass(slots=True)
class WorkspaceManager:
    config: AppConfig
    repo_path: Path
    run_id: str

    @property
    def workspace_root(self) -> Path:
        return self.repo_path / self.config.workspace_dir_name

    @property
    def runs_dir(self) -> Path:
        return self.workspace_root / self.config.runs_dir_name / self.run_id

    @property
    def candidates_dir(self) -> Path:
        return self.workspace_root / self.config.candidates_dir_name / self.run_id

    @property
    def backups_dir(self) -> Path:
        return self.workspace_root / self.config.backups_dir_name / self.run_id

    @property
    def reports_dir(self) -> Path:
        return self.workspace_root / self.config.reports_dir_name

    def prepare(self) -> None:
        for path in [self.runs_dir, self.candidates_dir, self.backups_dir, self.reports_dir]:
            path.mkdir(parents=True, exist_ok=True)
