from __future__ import annotations

from pathlib import Path


def load_guideline(path: Path) -> str:
    """
    Load a project guideline from a text-like file.

    Supported:
    - .md
    - .txt
    - .pdf

    PDF support is intended for text-based/searchable PDFs.
    Scanned image-only PDFs may return little or no text unless OCR is added.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Guideline file not found: {path}")

    suffix = path.suffix.lower()

    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")

    if suffix == ".pdf":
        return _load_pdf_guideline(path)

    raise ValueError(
        f"Unsupported guideline file type: {suffix}. "
        "Use .md, .txt, or .pdf."
    )


def _load_pdf_guideline(path: Path) -> str:
    try:
        import pypdf
    except ImportError as exc:
        raise RuntimeError(
            "PDF guidelines require pypdf. Install it with: pip install pypdf"
        ) from exc

    reader = pypdf.PdfReader(str(path))

    pages: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"\n\n--- Page {index} ---\n{text.strip()}")

    guideline = "\n".join(pages).strip()

    if not guideline:
        raise ValueError(
            "No text could be extracted from the PDF guideline. "
            "The PDF may be scanned/image-only. Convert it to text/Markdown "
            "or add OCR support before using it."
        )

    return guideline