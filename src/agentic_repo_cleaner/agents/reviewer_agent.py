from __future__ import annotations

from ..llm.ollama_client import OllamaClient
from ..models import ApplyResult, CleanupPlan, RepoMap, ReviewVerdict, ValidationResult
from ..prompts import (
    SYSTEM_REVIEWER,
    build_plan_reviewer_user_prompt,
    build_reviewer_user_prompt,
)


class ReviewerAgent:
    def __init__(self, llm: OllamaClient) -> None:
        self.llm = llm

    def review_plan(
        self,
        task: str,
        guideline: str,
        repo_map: RepoMap,
        plan: CleanupPlan,
        mode: dict,
    ) -> ReviewVerdict:
        payload = self.llm.chat_json(
            SYSTEM_REVIEWER,
            build_plan_reviewer_user_prompt(
                task=task,
                guideline=guideline,
                repo_map=repo_map.model_dump(),
                plan=plan.model_dump(),
                mode=mode,
            ),
        )
        return ReviewVerdict.model_validate(payload)

    def review_completed_work(
        self,
        task: str,
        guideline: str,
        repo_map: RepoMap,
        plan: CleanupPlan,
        apply_result: ApplyResult,
        validation_result: ValidationResult,
        mode: dict,
    ) -> ReviewVerdict:
        payload = self.llm.chat_json(
            SYSTEM_REVIEWER,
            build_reviewer_user_prompt(
                task=task,
                guideline=guideline,
                repo_map=repo_map.model_dump(),
                plan=plan.model_dump(),
                apply_result=apply_result.model_dump(),
                validation_result=validation_result.model_dump(),
                mode=mode,
            ),
        )
        return ReviewVerdict.model_validate(payload)