from __future__ import annotations

from pathlib import Path


TEXT_EXTENSIONS = {
    # Python / docs / data
    ".py", ".md", ".txt", ".toml", ".yaml", ".yml", ".json", ".ini", ".cfg",
    ".csv", ".sql",

    # Shell / scripts
    ".sh", ".bat", ".ps1", ".env", ".gitignore",

    # C / C++
    ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hh", ".hxx", ".cmake",

    # MATLAB
    ".m",

    # JavaScript / TypeScript
    ".js", ".jsx", ".ts", ".tsx",

    # Java / Kotlin / C#
    ".java", ".kt", ".cs",

    # Rust / Go
    ".rs", ".go",

    # Build files
    ".gradle", ".make",
}


def is_probably_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    try:
        with path.open("rb") as f:
            chunk = f.read(2048)
        if b"\x00" in chunk:
            return False
        chunk.decode("utf-8")
        return True
    except Exception:
        return False


def read_text_safely(path: Path, max_chars: int) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"<unable to read file: {exc}>"

    if len(text) > max_chars:
        return text[:max_chars] + "\n\n<TRUNCATED>"
    return text
