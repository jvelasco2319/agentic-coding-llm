from __future__ import annotations

from dataclasses import dataclass

from ..config import AppConfig
from .ollama_client import OllamaClient


@dataclass(slots=True)
class ModelRouter:
    """
    Role-specific Ollama model router.

    Default mapping:

    - mapper/context understanding: glm-5.1:cloud
    - planner/test/applier/repair: minimax-m2.5:cloud
    - reviewer/final review: kimi-k2.5:cloud
    """

    config: AppConfig

    def client_for(self, role: str) -> OllamaClient:
        model = self.model_for(role)
        return OllamaClient(base_url=self.config.ollama_host, model=model)

    def model_for(self, role: str) -> str:
        normalized = role.strip().lower()

        if normalized in {"mapper", "context", "repo_mapper"}:
            return self.config.mapper_model

        if normalized in {"planner", "plan", "test_designer", "tests", "applier", "apply", "repair"}:
            if normalized in {"test_designer", "tests"}:
                return self.config.test_designer_model
            if normalized in {"applier", "apply"}:
                return self.config.applier_model
            if normalized == "repair":
                return self.config.repair_model
            return self.config.planner_model

        if normalized in {"reviewer", "review", "final_review"}:
            return self.config.reviewer_model

        return self.config.planner_model

    def model_summary(self) -> dict[str, str]:
        return {
            "mapper": self.config.mapper_model,
            "planner": self.config.planner_model,
            "reviewer": self.config.reviewer_model,
            "applier": self.config.applier_model,
            "test_designer": self.config.test_designer_model,
            "repair": self.config.repair_model,
        }
