"""OpenRouter provider using OpenAI-compatible API with JSON mode."""

from __future__ import annotations

import json
import re
from typing import Any

import openai


class OpenRouterProvider:
    """OpenRouter API provider using OpenAI-compatible interface."""

    def __init__(self, model: str, api_key: str) -> None:
        self._model = model
        self._client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "openrouter"

    def evaluate(self, system_prompt: str, user_content: str) -> dict[str, Any]:
        """Send evaluation request using JSON mode."""
        response = self._client.chat.completions.create(
            model=self._model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=2000,
        )

        raw = response.choices[0].message.content or ""
        return _parse_json_response(raw)


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Parse JSON from LLM response, stripping markdown fences if present."""
    text = raw.strip()

    # Strip ```json ... ``` fences
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM response: {e}\nRaw: {raw[:500]}")
