from __future__ import annotations

from ..llm.ollama_client import OllamaClient
from ..models import CleanupPlan, FileEdit, RepairResult, ValidationResult
from ..prompts import SYSTEM_REPAIR, build_repair_user_prompt


class RepairAgent:
    def __init__(self, llm: OllamaClient) -> None:
        self.llm = llm

    def repair(
        self,
        task: str,
        guideline: str,
        plan: CleanupPlan,
        validation_result: ValidationResult,
        file_context: dict[str, str],
        mode: dict,
    ) -> RepairResult:
        payload = self.llm.chat_json(
            SYSTEM_REPAIR,
            build_repair_user_prompt(
                task,
                guideline,
                plan.model_dump(),
                validation_result.model_dump(),
                file_context,
                mode,
            ),
        )

        # Defensive recovery: if a model returns ApplyResult-shaped JSON during
        # repair, convert changed_files into RepairResult.
        if "changed_files" in payload and "summary" in payload:
            return RepairResult.model_validate(
                {
                    "summary": payload.get("summary", "Recovered repair result."),
                    "changed_files": payload.get("changed_files", []),
                    "notes": payload.get("notes", []),
                }
            )

        # Defensive recovery: if a model returns a single file-edit object,
        # wrap it as a repair result.
        if all(key in payload for key in ("path", "content", "reason")):
            return RepairResult(
                summary="Recovered single-file repair result.",
                changed_files=[FileEdit.model_validate(payload)],
                notes=["Repair agent returned a single file edit object instead of RepairResult wrapper."],
            )

        return RepairResult.model_validate(payload)