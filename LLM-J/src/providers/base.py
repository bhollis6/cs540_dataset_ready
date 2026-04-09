"""LLM provider protocol and factory."""

from __future__ import annotations

from typing import Any, Protocol


class LLMProvider(Protocol):
    """Interface for LLM providers that can evaluate PR candidates."""

    def evaluate(self, system_prompt: str, user_content: str) -> dict[str, Any]:
        """Send a prompt to the LLM and return the structured JSON response.

        The provider is responsible for:
        - Making the API call
        - Extracting the JSON response (via tool-use, JSON mode, or text parsing)
        - Returning a parsed dict matching the JudgeResponse schema

        Raises ValueError on malformed responses after retries.
        """
        ...

    @property
    def model_name(self) -> str:
        """Return the model identifier being used."""
        ...

    @property
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'anthropic', 'openrouter')."""
        ...


def get_provider(provider: str, model: str, api_key: str = "") -> LLMProvider:
    """Factory to create the appropriate LLM provider."""
    if provider == "claude-code":
        from src.providers.claude_code import ClaudeCodeProvider
        return ClaudeCodeProvider(model=model)
    elif provider == "anthropic":
        from src.providers.anthropic import AnthropicProvider
        return AnthropicProvider(model=model, api_key=api_key)
    elif provider == "openrouter":
        from src.providers.openrouter import OpenRouterProvider
        return OpenRouterProvider(model=model, api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")
