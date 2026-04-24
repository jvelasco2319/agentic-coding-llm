from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .agents.applier_agent import ApplierAgent
from .agents.planner_agent import PlannerAgent
from .agents.repair_agent import RepairAgent
from .agents.reviewer_agent import ReviewerAgent
from .agents.test_designer_agent import TestDesignerAgent
from .config import AppConfig
from .context.context_builder import ContextBuilder
from .context.guideline_loader import load_guideline
from .context.repo_mapper import RepoMapper
from .editing.backup_manager import BackupManager
from .editing.patch_apply import apply_file_edits
from .editing.workspace_manager import WorkspaceManager
from .llm.model_router import ModelRouter
from .models import CleanupPlan, RunManifest
from .reporting.manifest import write_manifest
from .validation.validator import Validator


class Pipeline:
    """
    Orchestrates guideline-driven autonomous repo cleanup.

    The LLM agents decide what should be done and what should be validated.
    The deterministic validator executes objective checks.

    Model routing defaults to your three Ollama cloud models:
    - Mapper/context: glm-5.1:cloud
    - Planner/applier/test/repair: minimax-m2.5:cloud
    - Reviewer/final review: kimi-k2.5:cloud
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.router = ModelRouter(config)

        self.mapper = RepoMapper()
        self.context_builder = ContextBuilder(config)

        self.planner = PlannerAgent(self.router.client_for("planner"))
        self.reviewer = ReviewerAgent(self.router.client_for("reviewer"))
        self.test_designer = TestDesignerAgent(self.router.client_for("test_designer"))
        self.applier = ApplierAgent(self.router.client_for("applier"))
        self.repair_agent = RepairAgent(self.router.client_for("repair"))

        self.validator = Validator(config)

    def plan_only(self, repo_path: Path, guideline_path: Path, task: str) -> CleanupPlan:
        guideline = load_guideline(guideline_path)
        repo_map = self.mapper.map_repo(repo_path)
        file_context = self.context_builder.build_initial_context(repo_path, repo_map)

        plan = self.planner.create_plan(task, guideline, repo_map, file_context)

        for _ in range(self.config.max_plan_revisions):
            review = self.reviewer.review_plan(task, guideline, repo_map, plan)
            if review.status == "approve":
                return plan
            if review.status == "reject":
                return plan
            plan = self.planner.revise_plan(task, guideline, repo_map, file_context, plan, review)

        return plan

    def apply(self, repo_path: Path, guideline_path: Path, task: str) -> RunManifest:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]
        workspace = WorkspaceManager(self.config, repo_path, run_id)
        workspace.prepare()

        guideline = load_guideline(guideline_path)
        repo_map = self.mapper.map_repo(repo_path)
        file_context = self.context_builder.build_initial_context(repo_path, repo_map)

        plan = self.planner.create_plan(task, guideline, repo_map, file_context)

        review = None
        for _ in range(self.config.max_plan_revisions):
            review = self.reviewer.review_plan(task, guideline, repo_map, plan)
            if review.status == "approve":
                break
            if review.status == "reject":
                break
            plan = self.planner.revise_plan(task, guideline, repo_map, file_context, plan, review)

        if review is None or review.status != "approve":
            manifest = RunManifest(
                run_id=run_id,
                created_at=datetime.now(),
                task=task,
                repo_path=str(repo_path),
                guideline_path=str(guideline_path),
                plan=plan,
                review=review,
                final_status="plan_not_approved",
                good_enough_reason="Reviewer did not approve the plan.",
            )
            write_manifest(workspace.reports_dir, manifest)
            return manifest

        target_context = self.context_builder.build_context_for_files(repo_path, plan.target_files)
        test_plan = self.test_designer.create_test_plan(task, guideline, repo_map, plan, target_context)
        apply_result = self.applier.apply(task, guideline, plan, test_plan, target_context)

        backup = BackupManager(repo_path, workspace.backups_dir)
        backup.backup_paths([*plan.target_files, *[f.path for f in apply_result.added_files]])

        apply_file_edits(repo_path, apply_result.changed_files, apply_result.added_files, apply_result.deleted_files)

        validation = self.validator.validate(repo_path, extra_commands=test_plan.validation_commands)

        repair_attempt = 0
        while not validation.passed and repair_attempt < self.config.max_repair_attempts:
            candidate_files = list({*[f.path for f in apply_result.changed_files], *[f.path for f in apply_result.added_files]})
            repair_context = self.context_builder.build_context_for_files(repo_path, candidate_files)
            repair_result = self.repair_agent.repair(task, guideline, plan, validation, repair_context)
            apply_file_edits(repo_path, repair_result.changed_files, [], [])
            validation = self.validator.validate(repo_path, extra_commands=test_plan.validation_commands)
            repair_attempt += 1

        final_review = self.reviewer.review_completed_work(task, guideline, repo_map, plan, apply_result, validation)

        if validation.passed and final_review.status == "approve":
            final_status = "applied"
            good_enough_reason = plan.good_enough_reason
        else:
            backup.restore_all()
            final_status = "reverted_failed_validation_or_review"
            good_enough_reason = "Validation or final reviewer approval failed; original files were restored."

        manifest = RunManifest(
            run_id=run_id,
            created_at=datetime.now(),
            task=task,
            repo_path=str(repo_path),
            guideline_path=str(guideline_path),
            plan=plan,
            review=final_review,
            test_plan=test_plan,
            apply_result=apply_result,
            validation_result=validation,
            final_status=final_status,
            changed_files=[f.path for f in apply_result.changed_files] + [f.path for f in apply_result.added_files],
            added_tests=[*test_plan.unit_tests_to_add, *test_plan.smoke_tests_to_add],
            good_enough_reason=good_enough_reason,
            next_recommended_steps=plan.deferred_work,
        )
        write_manifest(workspace.reports_dir, manifest)
        return manifest
