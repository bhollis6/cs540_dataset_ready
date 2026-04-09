"""Claude Code CLI provider — uses the local claude CLI (Max plan, no API key needed)."""

from __future__ import annotations

import json
import re
import subprocess
from typing import Any


class ClaudeCodeProvider:
    """Invokes the claude CLI in print mode for structured evaluation.

    Uses the user's Claude Max subscription — no API key required.
    """

    def __init__(self, model: str = "claude-sonnet-4-6") -> None:
        self._model = model

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "claude-code"

    def evaluate(self, system_prompt: str, user_content: str) -> dict[str, Any]:
        """Run evaluation via claude CLI in non-interactive print mode."""
        # Detect Stage 2 (6 criteria) vs Stage 1 (5 criteria)
        has_navigation_depth = (
            "navigation_depth" in system_prompt.lower()
            or "Navigation Depth" in system_prompt
        )

        criteria_lines = [
            '  "scope": {"score": <1-5>, "reasoning": "<text>"},',
            '  "test_coverage": {"score": <1-5>, "reasoning": "<text>"},',
            '  "mutation_relevance": {"score": <1-5>, "reasoning": "<text>"},',
            '  "clarity": {"score": <1-5>, "reasoning": "<text>"},',
            '  "complexity": {"score": <1-5>, "reasoning": "<text>"},',
        ]
        if has_navigation_depth:
            criteria_lines.append('  "navigation_depth": {"score": <1-5>, "reasoning": "<text>"},')

        schema = (
            "{\n"
            + "\n".join(criteria_lines)
            + '\n  "summary": "<brief overall assessment>"\n}'
        )

        full_prompt = (
            f"{user_content}\n\n"
            "Respond with ONLY a JSON object (no markdown fences, no commentary) "
            f"matching this exact schema:\n{schema}"
        )

        result = subprocess.run(
            [
                "claude",
                "-p", full_prompt,
                "--system-prompt", system_prompt,
                "--model", self._model,
                "--output-format", "text",
                "--no-session-persistence",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"claude CLI failed (exit {result.returncode}): {result.stderr[:500]}"
            )

        return _parse_json_response(result.stdout)


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Parse JSON from claude CLI output, stripping markdown fences if present."""
    text = raw.strip()

    # Strip ```json ... ``` fences
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    # Try to find JSON object in the response if there's surrounding text
    if not text.startswith("{"):
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            text = match.group(0)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from claude response: {e}\nRaw: {raw[:500]}")
