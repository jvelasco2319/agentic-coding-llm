from __future__ import annotations

import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .modes import get_mode

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


@contextmanager
def pipeline_stage(name: str):
    start = time.perf_counter()
    print(f"[PIPELINE] START: {name}")
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"[PIPELINE] DONE:  {name} ({elapsed:.2f}s)")


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
        self.mode = get_mode(config.mode)
        self.mode_payload = self.mode.to_prompt_dict()
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

        plan = self.planner.create_plan(
            task,
            guideline,
            repo_map,
            file_context,
            self.mode_payload,
        )

        for _ in range(self.config.max_plan_revisions):
            review = self.reviewer.review_plan(
                task,
                guideline,
                repo_map,
                plan,
                self.mode_payload,
            )
            if review.status == "approve":
                return plan
            if review.status == "reject":
                return plan
            plan = self.planner.revise_plan(
                task,
                guideline,
                repo_map,
                file_context,
                plan,
                review,
                self.mode_payload,
            )
        return plan

    def apply(self, repo_path: Path, guideline_path: Path, task: str) -> RunManifest:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]

        print("\n[PIPELINE] ========================================")
        print(f"[PIPELINE] Starting run: {run_id}")
        print(f"[PIPELINE] Mode: {self.mode.name}")
        print(f"[PIPELINE] Repo: {repo_path}")
        print(f"[PIPELINE] Guideline: {guideline_path}")
        print("[PIPELINE] ========================================\n")

        with pipeline_stage("Prepare workspace"):
            workspace = WorkspaceManager(self.config, repo_path, run_id)
            workspace.prepare()

        with pipeline_stage("Load guideline"):
            guideline = load_guideline(guideline_path)

        with pipeline_stage("Map repository"):
            repo_map = self.mapper.map_repo(repo_path)

        with pipeline_stage("Build initial context"):
            file_context = self.context_builder.build_initial_context(repo_path, repo_map)

        with pipeline_stage("Create plan"):
            plan = self.planner.create_plan(
                task,
                guideline,
                repo_map,
                file_context,
                self.mode_payload,
            )
        review = None
        for attempt in range(self.config.max_plan_revisions):
            with pipeline_stage(f"Review plan attempt {attempt + 1}"):
                review = self.reviewer.review_plan(
                    task,
                    guideline,
                    repo_map,
                    plan,
                    self.mode_payload,
                )

            print(f"[PIPELINE] Plan review status: {review.status}")

            if review.status == "approve":
                break
            if review.status == "reject":
                break

            with pipeline_stage(f"Revise plan attempt {attempt + 1}"):
                plan = self.planner.revise_plan(
                    task,
                    guideline,
                    repo_map,
                    file_context,
                    plan,
                    review,
                    self.mode_payload,
                )

        if review is None or review.status != "approve":
            manifest = RunManifest(
                run_id=run_id,
                created_at=datetime.now(),
                task=task,
                mode=self.mode.name,
                mode_description=self.mode.description,
                validation_profile=self.mode.validation_profile,
                repo_path=str(repo_path),
                guideline_path=str(guideline_path),
                plan=plan,
                review=review,
                final_status="plan_not_approved",
                good_enough_reason="Reviewer did not approve the plan.",
            )
            write_manifest(workspace.reports_dir, manifest)
            return manifest

        with pipeline_stage("Build target file context"):
            target_context = self.context_builder.build_context_for_files(repo_path, plan.target_files)

        with pipeline_stage("Create test plan"):
            test_plan = self.test_designer.create_test_plan(
                task,
                guideline,
                repo_map,
                plan,
                target_context,
                self.mode_payload,
            )

        with pipeline_stage("Apply candidate changes"):
            apply_result = self.applier.apply(
                task,
                guideline,
                plan,
                test_plan,
                target_context,
                self.mode_payload,
            )

        with pipeline_stage("Backup target files"):
            backup = BackupManager(repo_path, workspace.backups_dir)
            backup.backup_paths([*plan.target_files, *[f.path for f in apply_result.added_files]])

        with pipeline_stage("Write candidate changes to repo"):
            apply_file_edits(
                repo_path,
                apply_result.changed_files,
                apply_result.added_files,
                apply_result.deleted_files,
            )

        with pipeline_stage("Run deterministic validation"):
            validation = self.validator.validate(repo_path, extra_commands=test_plan.validation_commands)

        print(f"[PIPELINE] Validation passed: {validation.passed}")

        repair_attempt = 0
        while not validation.passed and repair_attempt < self.config.max_repair_attempts:
            print(f"[PIPELINE] Validation failed. Starting repair attempt {repair_attempt + 1}...")

            with pipeline_stage(f"Build repair context attempt {repair_attempt + 1}"):
                candidate_files = list({
                    *[f.path for f in apply_result.changed_files],
                    *[f.path for f in apply_result.added_files],
                })
                repair_context = self.context_builder.build_context_for_files(repo_path, candidate_files)

            with pipeline_stage(f"Repair candidate attempt {repair_attempt + 1}"):
                repair_result = self.repair_agent.repair(
                    task,
                    guideline,
                    plan,
                    validation,
                    repair_context,
                    self.mode_payload,
                )

            with pipeline_stage(f"Apply repair edits attempt {repair_attempt + 1}"):
                apply_file_edits(repo_path, repair_result.changed_files, [], [])

            with pipeline_stage(f"Re-run validation attempt {repair_attempt + 1}"):
                validation = self.validator.validate(repo_path, extra_commands=test_plan.validation_commands)

            print(f"[PIPELINE] Validation passed after repair: {validation.passed}")

            repair_attempt += 1

        with pipeline_stage("Final review"):
            final_review = self.reviewer.review_completed_work(
                task,
                guideline,
                repo_map,
                plan,
                apply_result,
                validation,
                self.mode_payload,
            )

        print(f"[PIPELINE] Final review status: {final_review.status}")

        if validation.passed and final_review.status == "approve":
            print("[PIPELINE] Run accepted. Changes remain applied.")
            final_status = "applied"
            good_enough_reason = plan.good_enough_reason
        else:
            print("[PIPELINE] Run failed validation or final review. Restoring backup...")
            with pipeline_stage("Restore backup"):
                backup.restore_all()
            final_status = "reverted_failed_validation_or_review"
            good_enough_reason = "Validation or final reviewer approval failed; original files were restored."

        manifest = RunManifest(
            run_id=run_id,
            created_at=datetime.now(),
            task=task,
            mode=self.mode.name,
            mode_description=self.mode.description,
            validation_profile=self.mode.validation_profile,
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
        with pipeline_stage("Write manifest"):
            write_manifest(workspace.reports_dir, manifest)

        print(f"[PIPELINE] Final status: {final_status}")
        print("[PIPELINE] Run complete.\n")

        return manifest
