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
    ) -> ApplyResult:
        payload = self.llm.chat_json(
            SYSTEM_APPLIER,
            build_applier_user_prompt(task, guideline, plan.model_dump(), test_plan.model_dump(), file_context),
        )
        return ApplyResult.model_validate(payload)
