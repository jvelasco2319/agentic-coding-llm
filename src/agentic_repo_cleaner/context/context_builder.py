from __future__ import annotations

from pathlib import Path

from ..config import AppConfig
from ..models import RepoMap
from .file_reader import read_text_safely


class ContextBuilder:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def build_initial_context(self, repo_path: Path, repo_map: RepoMap) -> dict[str, str]:
        selected = self._select_initial_files(repo_map)
        return self.build_context_for_files(repo_path, selected)

    def build_context_for_files(self, repo_path: Path, paths: list[str]) -> dict[str, str]:
        result: dict[str, str] = {}
        total = 0

        for rel in paths:
            full = repo_path / rel
            if not full.exists() or not full.is_file():
                continue
            text = read_text_safely(full, self.config.max_file_chars)
            if total + len(text) > self.config.max_total_context_chars:
                break
            result[rel] = text
            total += len(text)

        return result

    def _select_initial_files(self, repo_map: RepoMap) -> list[str]:
        candidates: list[str] = []

        candidates.extend(repo_map.likely_entrypoints)
        candidates.extend(["pyproject.toml", "setup.py", "README.md"])

        for f in repo_map.files:
            if f.path.endswith(("models.py", "config.py", "pipeline.py", "validator.py")):
                candidates.append(f.path)

        for f in repo_map.files:
            if f.language == "python":
                candidates.append(f.path)

        deduped = []
        for p in candidates:
            if p not in deduped:
                deduped.append(p)
        return deduped[: self.config.max_context_files]
