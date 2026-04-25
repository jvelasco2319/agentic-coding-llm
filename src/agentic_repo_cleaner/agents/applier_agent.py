from __future__ import annotations

from ..llm.ollama_client import OllamaClient
from ..models import ApplyResult, CleanupPlan, TestPlan
from ..prompts import SYSTEM_APPLIER, build_applier_user_prompt


class ApplierAgent:
    def __init__(self, llm: OllamaClient) -> None:
        self.llm = llm

    def apply(
        self,
        task: str,
        guideline: str,
        plan: CleanupPlan,
        test_plan: TestPlan,
        file_context: dict[str, str],
        mode: dict,
    ) -> ApplyResult:
        payload = self.llm.chat_json(
            SYSTEM_APPLIER,
            build_applier_user_prompt(
                task,
                guideline,
                plan.model_dump(),
                test_plan.model_dump(),
                file_context,
                mode,
            ),
        )

        payload = self._normalize_apply_payload(payload, file_context)
        return ApplyResult.model_validate(payload)

    def _normalize_apply_payload(
        self,
        payload: dict,
        file_context: dict[str, str],
    ) -> dict:
        """
        Defensive cleanup for common LLM formatting mistakes.

        Handles:
        - existing files incorrectly placed in added_files
        - missing reason fields in file edits
        - missing top-level list fields
        """
        payload.setdefault("summary", "Applied requested changes.")
        payload.setdefault("changed_files", [])
        payload.setdefault("added_files", [])
        payload.setdefault("deleted_files", [])
        payload.setdefault("notes", [])

        existing_paths = set(file_context.keys())

        normalized_changed = []
        normalized_added = []

        for edit in payload.get("changed_files", []):
            if not isinstance(edit, dict):
                continue

            edit.setdefault("reason", "Changed by Applier to satisfy the requested task.")
            normalized_changed.append(edit)

        for edit in payload.get("added_files", []):
            if not isinstance(edit, dict):
                continue

            edit.setdefault("reason", "Added by Applier to satisfy the requested task.")

            # If the file already exists in the provided context, this is not
            # actually an added file. Move it to changed_files.
            if edit.get("path") in existing_paths:
                edit["reason"] = (
                    edit.get("reason")
                    or "Existing file was updated by Applier."
                )
                normalized_changed.append(edit)
            else:
                normalized_added.append(edit)

        payload["changed_files"] = normalized_changed
        payload["added_files"] = normalized_added

        return payload