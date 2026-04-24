from __future__ import annotations

from ..llm.ollama_client import OllamaClient
from ..models import RepoMap
from ..prompts import SYSTEM_MAPPER, build_mapper_user_prompt


class MapperAgent:
    """
    Optional LLM mapper.

    The deterministic RepoMapper is used by default. This class is included for
    future expansion if you want the LLM to add semantic repo summaries.
    """

    def __init__(self, llm: OllamaClient) -> None:
        self.llm = llm

    def map_from_text(self, repo_tree: str, file_summaries: str) -> RepoMap:
        payload = self.llm.chat_json(SYSTEM_MAPPER, build_mapper_user_prompt(repo_tree, file_summaries))
        return RepoMap.model_validate(payload)
