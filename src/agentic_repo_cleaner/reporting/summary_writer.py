from __future__ import annotations

from ..models import RunManifest


def build_markdown_summary(manifest: RunManifest) -> str:
    lines = [
        f"# Run Summary: {manifest.run_id}",
        "",
        f"Status: **{manifest.final_status}**",
        "",
        "## Task",
        manifest.task,
        "",
        "## Changed Files",
    ]
    lines.extend(f"- `{path}`" for path in manifest.changed_files or ["None"])
    lines.extend(["", "## Good Enough Reason", manifest.good_enough_reason or "Not provided."])
    lines.extend(["", "## Next Recommended Steps"])
    lines.extend(f"- {step}" for step in manifest.next_recommended_steps or ["None"])
    return "\n".join(lines)
