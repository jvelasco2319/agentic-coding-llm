from __future__ import annotations

import time
from dataclasses import dataclass

import requests

from .json_utils import extract_json_object


@dataclass(slots=True)
class OllamaClient:
    base_url: str
    model: str
    timeout_seconds: int = 600
    max_retries: int = 3
    retry_sleep_seconds: float = 5.0

    def chat_text(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url.rstrip('/')}/api/chat"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }

        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout_seconds,
                )

                if response.status_code in {429, 502, 503, 504}:
                    last_error = requests.HTTPError(
                        f"{response.status_code} transient Ollama/cloud error for model {self.model}",
                        response=response,
                    )

                    if attempt < self.max_retries:
                        sleep_time = self.retry_sleep_seconds * attempt
                        print(
                            f"[WARN] Ollama/cloud transient error {response.status_code} "
                            f"for {self.model}. Retrying in {sleep_time:.1f}s "
                            f"({attempt}/{self.max_retries})..."
                        )
                        time.sleep(sleep_time)
                        continue

                response.raise_for_status()
                data = response.json()
                return data["message"]["content"]

            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
                last_error = exc

                if attempt < self.max_retries:
                    sleep_time = self.retry_sleep_seconds * attempt
                    print(
                        f"[WARN] Ollama request failed for {self.model}: {exc}. "
                        f"Retrying in {sleep_time:.1f}s ({attempt}/{self.max_retries})..."
                    )
                    time.sleep(sleep_time)
                    continue

                raise

        raise RuntimeError(f"Ollama chat failed after retries: {last_error}")

    def chat_json(self, system_prompt: str, user_prompt: str) -> dict:
        text = self.chat_text(system_prompt, user_prompt)
        return extract_json_object(text)