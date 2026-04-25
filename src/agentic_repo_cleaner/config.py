from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    """
    Runtime configuration for the autonomous repo cleaner.

    The default model routing matches your current three-model Ollama setup:

    - mapper_model: glm-5.1:cloud
    - planner_model: minimax-m2.5:cloud
    - reviewer_model: kimi-k2.5:cloud

    The other work-producing roles default to the planner model because they are
    closer to planning/implementation than independent review.
    """

    mode: str = "cleanup"

    ollama_host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))

    mapper_model: str = field(default_factory=lambda: os.getenv("AGENTIC_MAPPER_MODEL", "glm-5.1:cloud"))
    planner_model: str = field(default_factory=lambda: os.getenv("AGENTIC_PLANNER_MODEL", "minimax-m2.5:cloud"))
    reviewer_model: str = field(default_factory=lambda: os.getenv("AGENTIC_REVIEWER_MODEL", "kimi-k2.6:cloud"))

    # Supporting roles. These default to the planner model unless overridden.
    applier_model: str = field(default_factory=lambda: os.getenv("AGENTIC_APPLIER_MODEL", "minimax-m2.5:cloud"))
    test_designer_model: str = field(default_factory=lambda: os.getenv("AGENTIC_TEST_DESIGNER_MODEL", "minimax-m2.5:cloud"))
    repair_model: str = field(default_factory=lambda: os.getenv("AGENTIC_REPAIR_MODEL", "minimax-m2.5:cloud"))

    max_context_files: int = 30
    max_file_chars: int = 28_000
    max_total_context_chars: int = 180_000

    max_plan_revisions: int = 3
    max_repair_attempts: int = 3

    workspace_dir_name: str = "workspaces"
    runs_dir_name: str = "runs"
    candidates_dir_name: str = "candidates"
    backups_dir_name: str = "backups"
    reports_dir_name: str = "reports"

    run_pytest: bool = True
    run_compileall: bool = True
    run_import_check: bool = True

    def workspace_root(self, project_root: Path) -> Path:
        return project_root / self.workspace_dir_name
