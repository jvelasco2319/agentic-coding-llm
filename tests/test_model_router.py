from agentic_repo_cleaner.config import AppConfig
from agentic_repo_cleaner.llm.model_router import ModelRouter


def test_model_router_defaults_to_user_three_model_setup() -> None:
    router = ModelRouter(AppConfig())
    summary = router.model_summary()

    assert summary["mapper"] == "glm-5.1:cloud"
    assert summary["planner"] == "minimax-m2.5:cloud"
    assert summary["reviewer"] == "kimi-k2.5:cloud"
    assert summary["applier"] == "minimax-m2.5:cloud"
    assert summary["test_designer"] == "minimax-m2.5:cloud"
    assert summary["repair"] == "minimax-m2.5:cloud"
