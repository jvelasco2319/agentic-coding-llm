from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .config import AppConfig
from .llm.model_router import ModelRouter
from .pipeline import Pipeline
from .context.repo_mapper import RepoMapper
from .validation.validator import Validator

app = typer.Typer(help="Guideline-driven autonomous repo cleaner.")
console = Console()


def _make_config(
    mapper_model: Optional[str],
    planner_model: Optional[str],
    reviewer_model: Optional[str],
    applier_model: Optional[str],
    test_designer_model: Optional[str],
    repair_model: Optional[str],
) -> AppConfig:
    config = AppConfig()

    if mapper_model:
        config.mapper_model = mapper_model
    if planner_model:
        config.planner_model = planner_model
    if reviewer_model:
        config.reviewer_model = reviewer_model

    # Supporting roles default to planner model unless explicitly overridden.
    if applier_model:
        config.applier_model = applier_model
    else:
        config.applier_model = config.planner_model

    if test_designer_model:
        config.test_designer_model = test_designer_model
    else:
        config.test_designer_model = config.planner_model

    if repair_model:
        config.repair_model = repair_model
    else:
        config.repair_model = config.planner_model

    return config


@app.command()
def models(
    mapper_model: Optional[str] = typer.Option(None, help="Mapper model override."),
    planner_model: Optional[str] = typer.Option(None, help="Planner model override."),
    reviewer_model: Optional[str] = typer.Option(None, help="Reviewer model override."),
) -> None:
    """
    Show the role-to-model routing.
    """
    config = _make_config(mapper_model, planner_model, reviewer_model, None, None, None)
    console.print_json(data=ModelRouter(config).model_summary())


@app.command()
def map(repo: Path = typer.Option(..., exists=True, file_okay=False, help="Target repository path.")) -> None:
    repo_map = RepoMapper().map_repo(repo)
    console.print_json(repo_map.model_dump_json(indent=2))


@app.command()
def validate(repo: Path = typer.Option(..., exists=True, file_okay=False, help="Target repository path.")) -> None:
    config = AppConfig()
    result = Validator(config).validate(repo, extra_commands=[])
    console.print_json(result.model_dump_json(indent=2))
    raise typer.Exit(0 if result.passed else 1)


@app.command()
def plan(
    repo: Path = typer.Option(..., exists=True, file_okay=False, help="Target repository path."),
    guideline: Path = typer.Option(Path("guidelines/project_guideline.md"), help="Path to guideline markdown."),
    task: str = typer.Option("Organize, clean, document, and test this repo while preserving working behavior."),
    mapper_model: Optional[str] = typer.Option(None, help="Mapper model. Default: glm-5.1:cloud"),
    planner_model: Optional[str] = typer.Option(None, help="Planner model. Default: minimax-m2.5:cloud"),
    reviewer_model: Optional[str] = typer.Option(None, help="Reviewer model. Default: kimi-k2.5:cloud"),
    applier_model: Optional[str] = typer.Option(None, help="Applier model. Default: planner model."),
    test_designer_model: Optional[str] = typer.Option(None, help="Test designer model. Default: planner model."),
    repair_model: Optional[str] = typer.Option(None, help="Repair model. Default: planner model."),
) -> None:
    config = _make_config(
        mapper_model=mapper_model,
        planner_model=planner_model,
        reviewer_model=reviewer_model,
        applier_model=applier_model,
        test_designer_model=test_designer_model,
        repair_model=repair_model,
    )
    result = Pipeline(config).plan_only(repo, guideline, task)
    console.print_json(result.model_dump_json(indent=2))


@app.command()
def apply(
    repo: Path = typer.Option(..., exists=True, file_okay=False, help="Target repository path."),
    guideline: Path = typer.Option(Path("guidelines/project_guideline.md"), help="Path to guideline markdown."),
    task: str = typer.Option("Organize, clean, document, and test this repo while preserving working behavior."),
    mapper_model: Optional[str] = typer.Option(None, help="Mapper model. Default: glm-5.1:cloud"),
    planner_model: Optional[str] = typer.Option(None, help="Planner model. Default: minimax-m2.5:cloud"),
    reviewer_model: Optional[str] = typer.Option(None, help="Reviewer model. Default: kimi-k2.5:cloud"),
    applier_model: Optional[str] = typer.Option(None, help="Applier model. Default: planner model."),
    test_designer_model: Optional[str] = typer.Option(None, help="Test designer model. Default: planner model."),
    repair_model: Optional[str] = typer.Option(None, help="Repair model. Default: planner model."),
) -> None:
    config = _make_config(
        mapper_model=mapper_model,
        planner_model=planner_model,
        reviewer_model=reviewer_model,
        applier_model=applier_model,
        test_designer_model=test_designer_model,
        repair_model=repair_model,
    )
    manifest = Pipeline(config).apply(repo, guideline, task)
    console.print_json(manifest.model_dump_json(indent=2))
    raise typer.Exit(0 if manifest.final_status == "applied" else 1)


if __name__ == "__main__":
    app()
