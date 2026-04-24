from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


ReviewStatus = Literal["approve", "revise", "reject"]


class FileSummary(BaseModel):
    path: str
    language: str = "unknown"
    purpose: str = ""
    important_symbols: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class RepoMap(BaseModel):
    repo_path: str
    files: list[FileSummary] = Field(default_factory=list)
    package_roots: list[str] = Field(default_factory=list)
    test_files: list[str] = Field(default_factory=list)
    likely_entrypoints: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PlannedChange(BaseModel):
    file_path: str
    reason: str
    intended_change: str
    behavior_preservation_notes: str = ""


class CleanupPlan(BaseModel):
    title: str
    rationale: str
    target_files: list[str]
    intended_outcome: str
    planned_changes: list[PlannedChange]
    completion_criteria: list[str]
    good_enough_reason: str
    validation_strategy: list[str]
    risks: list[str] = Field(default_factory=list)
    deferred_work: list[str] = Field(default_factory=list)


class ReviewVerdict(BaseModel):
    status: ReviewStatus
    rationale: str
    guideline_alignment: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    required_revisions: list[str] = Field(default_factory=list)


class FileEdit(BaseModel):
    path: str
    content: str
    reason: str


class ApplyResult(BaseModel):
    summary: str
    changed_files: list[FileEdit]
    added_files: list[FileEdit] = Field(default_factory=list)
    deleted_files: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class TestPlan(BaseModel):
    rationale: str
    behavior_to_preserve: list[str] = Field(default_factory=list)
    unit_tests_to_add: list[str] = Field(default_factory=list)
    smoke_tests_to_add: list[str] = Field(default_factory=list)
    existing_tests_to_run: list[str] = Field(default_factory=list)
    validation_commands: list[str] = Field(default_factory=list)


class CommandResult(BaseModel):
    command: str
    cwd: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""


class ValidationResult(BaseModel):
    passed: bool
    syntax_passed: bool = True
    import_passed: bool = True
    unit_tests_passed: bool = True
    smoke_tests_passed: bool = True
    commands_run: list[CommandResult] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)


class RepairResult(BaseModel):
    summary: str
    changed_files: list[FileEdit] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class RunManifest(BaseModel):
    run_id: str
    created_at: datetime
    task: str
    repo_path: str
    guideline_path: str
    plan: Optional[CleanupPlan] = None
    review: Optional[ReviewVerdict] = None
    test_plan: Optional[TestPlan] = None
    apply_result: Optional[ApplyResult] = None
    validation_result: Optional[ValidationResult] = None
    final_status: str
    changed_files: list[str] = Field(default_factory=list)
    added_tests: list[str] = Field(default_factory=list)
    good_enough_reason: str = ""
    next_recommended_steps: list[str] = Field(default_factory=list)
