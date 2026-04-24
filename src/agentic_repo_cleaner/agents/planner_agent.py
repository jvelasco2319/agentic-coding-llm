from __future__ import annotations

from ..llm.ollama_client import OllamaClient
from ..models import CleanupPlan, RepoMap, ReviewVerdict
from ..prompts import SYSTEM_PLANNER, build_planner_user_prompt


class PlannerAgent:
    def __init__(self, llm: OllamaClient) -> None:
        self.llm = llm

    def create_plan(
        self,
        task: str,
        guideline: str,
        repo_map: RepoMap,
        file_context: dict[str, str],
    ) -> CleanupPlan:
        payload = self.llm.chat_json(
            SYSTEM_PLANNER,
            build_planner_user_prompt(task, guideline, repo_map.model_dump(), file_context),
        )
        return CleanupPlan.model_validate(payload)

    def revise_plan(
        self,
        task: str,
        guideline: str,
        repo_map: RepoMap,
        file_context: dict[str, str],
        previous_plan: CleanupPlan,
        review: ReviewVerdict,
    ) -> CleanupPlan:
        revised_task = (
            task
            + "\n\nPrevious plan:\n"
            + previous_plan.model_dump_json(indent=2)
            + "\n\nReviewer requested revision:\n"
            + review.model_dump_json(indent=2)
        )
        return self.create_plan(revised_task, guideline, repo_map, file_context)
