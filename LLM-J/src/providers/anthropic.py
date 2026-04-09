"""Anthropic provider using tool-use for structured output."""

from __future__ import annotations

from typing import Any

import anthropic


def _build_evaluation_tool(has_navigation_depth: bool) -> dict[str, Any]:
    """Build the tool schema for Stage 1 or Stage 2 evaluation."""
    import copy

    tool = copy.deepcopy(EVALUATION_TOOL)
    if has_navigation_depth:
        tool["input_schema"]["properties"]["navigation_depth"] = {
            "type": "object",
            "properties": {
                "score": {
                    "type": "integer",
                    "description": "Score from 1-5 for navigation depth",
                },
                "reasoning": {
                    "type": "string",
                    "description": "Explanation for the navigation depth score",
                },
            },
            "required": ["score", "reasoning"],
        }
        tool["input_schema"]["required"].append("navigation_depth")

    return tool


# Tool schema that forces the LLM to return structured evaluation JSON
EVALUATION_TOOL = {
    "name": "submit_evaluation",
    "description": "Submit the structured evaluation of a PR candidate.",
    "input_schema": {
        "type": "object",
        "properties": {
            "scope": {
                "type": "object",
                "properties": {
                    "score": {
                        "type": "integer",
                        "description": "Score from 1-5 for how focused the PR scope is",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation for the scope score",
                    },
                },
                "required": ["score", "reasoning"],
            },
            "test_coverage": {
                "type": "object",
                "properties": {
                    "score": {
                        "type": "integer",
                        "description": "Score from 1-5 for test coverage quality",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation for the test coverage score",
                    },
                },
                "required": ["score", "reasoning"],
            },
            "mutation_relevance": {
                "type": "object",
                "properties": {
                    "score": {
                        "type": "integer",
                        "description": "Score from 1-5 for mutation relevance",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation for the mutation relevance score",
                    },
                },
                "required": ["score", "reasoning"],
            },
            "clarity": {
                "type": "object",
                "properties": {
                    "score": {
                        "type": "integer",
                        "description": "Score from 1-5 for issue description clarity",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation for the clarity score",
                    },
                },
                "required": ["score", "reasoning"],
            },
            "complexity": {
                "type": "object",
                "properties": {
                    "score": {
                        "type": "integer",
                        "description": "Score from 1-5 for complexity (3-4 is ideal)",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation for the complexity score",
                    },
                },
                "required": ["score", "reasoning"],
            },
            "summary": {
                "type": "string",
                "description": "Brief overall assessment of this PR as an experiment candidate",
            },
        },
        "required": [
            "scope", "test_coverage", "mutation_relevance",
            "clarity", "complexity", "summary",
        ],
    },
}


class AnthropicProvider:
    """Anthropic API provider using tool-use for guaranteed structured output."""

    def __init__(self, model: str, api_key: str) -> None:
        self._model = model
        self._client = anthropic.Anthropic(api_key=api_key)

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def evaluate(self, system_prompt: str, user_content: str) -> dict[str, Any]:
        """Send evaluation request using tool-use for structured output."""
        # Detect Stage 2 and add navigation_depth to the tool schema
        has_navigation_depth = (
            "navigation_depth" in system_prompt.lower()
            or "Navigation Depth" in system_prompt
        )
        tool = _build_evaluation_tool(has_navigation_depth)

        response = self._client.messages.create(
            model=self._model,
            max_tokens=2000,
            system=system_prompt,
            tools=[tool],
            tool_choice={"type": "tool", "name": "submit_evaluation"},
            messages=[
                {"role": "user", "content": user_content},
            ],
        )

        # Extract the tool use result
        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_evaluation":
                return block.input

        raise ValueError("No tool_use block found in Anthropic response")
