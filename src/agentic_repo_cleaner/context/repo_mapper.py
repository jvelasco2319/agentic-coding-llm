from __future__ import annotations

import ast
from pathlib import Path

from ..models import FileSummary, RepoMap
from .file_reader import is_probably_text


IGNORED_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "venv", ".venv", "env", ".env", "dist", "build", "node_modules",
    "workspaces",
}


class RepoMapper:
    def map_repo(self, repo_path: Path) -> RepoMap:
        files: list[FileSummary] = []
        test_files: list[str] = []
        likely_entrypoints: list[str] = []
        package_roots: set[str] = set()

        for path in sorted(repo_path.rglob("*")):
            if not path.is_file():
                continue
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            rel = path.relative_to(repo_path).as_posix()

            if not is_probably_text(path):
                continue

            summary = self._summarize_file(path, rel)
            files.append(summary)

            if "test" in path.name.lower() or "/tests/" in f"/{rel}":
                test_files.append(rel)

            if path.name in {"cli.py", "main.py", "__main__.py", "app.py"}:
                likely_entrypoints.append(rel)

            if path.name == "__init__.py":
                package_roots.add(str(Path(rel).parent).replace("\\", "/"))

        return RepoMap(
            repo_path=str(repo_path),
            files=files,
            package_roots=sorted(package_roots),
            test_files=sorted(test_files),
            likely_entrypoints=sorted(likely_entrypoints),
            notes=[],
        )

    def _summarize_file(self, path: Path, rel: str) -> FileSummary:
        language = self._language_for(path)
        symbols: list[str] = []
        risks: list[str] = []

        if path.suffix == ".py":
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        symbols.append(node.name)
            except SyntaxError as exc:
                risks.append(f"syntax_error: {exc}")
            except Exception as exc:
                risks.append(f"parse_error: {exc}")

        purpose = self._guess_purpose(rel, symbols)
        return FileSummary(path=rel, language=language, purpose=purpose, important_symbols=symbols[:50], risks=risks)

    @staticmethod
    def _language_for(path: Path) -> str:
        return {
            ".py": "python",
            ".md": "markdown",
            ".toml": "toml",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
        }.get(path.suffix.lower(), "text")

    @staticmethod
    def _guess_purpose(rel: str, symbols: list[str]) -> str:
        lowered = rel.lower()
        if "test" in lowered:
            return "test file"
        if rel.endswith("cli.py"):
            return "command-line entry point"
        if rel.endswith("config.py"):
            return "configuration"
        if rel.endswith("models.py"):
            return "data models / schemas"
        if rel.endswith("validator.py"):
            return "validation orchestration"
        if symbols:
            return "contains: " + ", ".join(symbols[:8])
        return "text/config/source file"
