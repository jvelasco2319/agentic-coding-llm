from __future__ import annotations

import requests

from .json_utils import extract_json_object


class OllamaClient:
    """
    Minimal Ollama chat client.
    """

    def __init__(self, base_url: str, model: str, timeout: int = 300) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def chat_text(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

    def chat_json(self, system_prompt: str, user_prompt: str) -> dict:
        text = self.chat_text(system_prompt, user_prompt)
        return extract_json_object(text)
