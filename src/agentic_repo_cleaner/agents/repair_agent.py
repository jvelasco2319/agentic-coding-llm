from __future__ import annotations

from ..llm.ollama_client import OllamaClient
from ..models import CleanupPlan, RepairResult, ValidationResult
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
    ) -> RepairResult:
        payload = self.llm.chat_json(
            SYSTEM_REPAIR,
            build_repair_user_prompt(task, guideline, plan.model_dump(), validation_result.model_dump(), file_context),
        )
        return RepairResult.model_validate(payload)
