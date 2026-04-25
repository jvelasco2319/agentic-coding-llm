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
        mode: dict,
    ) -> CleanupPlan:
        payload = self.llm.chat_json(
            SYSTEM_PLANNER,
            build_planner_user_prompt(
                task,
                guideline,
                repo_map.model_dump(),
                file_context,
                mode,
            ),
        )

        payload = self._normalize_plan_payload(payload)

        return CleanupPlan.model_validate(payload)

    def revise_plan(
        self,
        task: str,
        guideline: str,
        repo_map: RepoMap,
        file_context: dict[str, str],
        previous_plan: CleanupPlan,
        review: ReviewVerdict,
        mode: dict,
    ) -> CleanupPlan:
        revised_task = (
            task
            + "\n\nPrevious plan:\n"
            + previous_plan.model_dump_json(indent=2)
            + "\n\nReviewer requested revision:\n"
            + review.model_dump_json(indent=2)
        )
        return self.create_plan(
            revised_task,
            guideline,
            repo_map,
            file_context,
            mode,
        )

    def _normalize_plan_payload(self, payload: dict) -> dict:
        """
        Defensive cleanup for common Planner formatting mistakes.

        Handles:
        - missing planned_changes when the model returned a single top-level
          intended_change / behavior_preservation_notes pair
        - missing optional list fields
        """

        if not isinstance(payload, dict):
            raise ValueError(
                "Planner returned invalid payload type. Expected one CleanupPlan JSON object."
            )

        payload.setdefault("title", "Generated cleanup plan")
        payload.setdefault("rationale", "")
        payload.setdefault("target_files", [])
        payload.setdefault("intended_outcome", "")
        payload.setdefault("completion_criteria", [])
        payload.setdefault("good_enough_reason", "")
        payload.setdefault("validation_strategy", [])
        payload.setdefault("risks", [])
        payload.setdefault("deferred_work", [])

        if "planned_changes" not in payload:
            target_files = payload.get("target_files") or []

            file_path = target_files[0] if target_files else ""
            intended_change = payload.get("intended_change", "")
            behavior_notes = payload.get("behavior_preservation_notes", "")

            payload["planned_changes"] = [
                {
                    "file_path": file_path,
                    "reason": payload.get(
                        "rationale",
                        "Planner returned a single top-level change description.",
                    ),
                    "intended_change": intended_change
                    or "Verify requested behavior and make the smallest necessary change.",
                    "behavior_preservation_notes": behavior_notes
                    or "Preserve existing behavior unless the task explicitly requires a fix.",
                }
            ]

        return payload