from __future__ import annotations

from ..llm.ollama_client import OllamaClient
from ..models import CleanupPlan, RepoMap, TestPlan
from ..prompts import SYSTEM_TEST_DESIGNER, build_test_designer_user_prompt


class TestDesignerAgent:
    def __init__(self, llm: OllamaClient) -> None:
        self.llm = llm

    def create_test_plan(
        self,
        task: str,
        guideline: str,
        repo_map: RepoMap,
        plan: CleanupPlan,
        file_context: dict[str, str],
    ) -> TestPlan:
        payload = self.llm.chat_json(
            SYSTEM_TEST_DESIGNER,
            build_test_designer_user_prompt(task, guideline, repo_map.model_dump(), plan.model_dump(), file_context),
        )
        return TestPlan.model_validate(payload)
