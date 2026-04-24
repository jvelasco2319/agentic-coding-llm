from __future__ import annotations

from pathlib import Path

from ..models import RunManifest


def write_manifest(reports_dir: Path, manifest: RunManifest) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"{manifest.run_id}.json"
    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    latest = reports_dir / "latest.json"
    latest.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return path
