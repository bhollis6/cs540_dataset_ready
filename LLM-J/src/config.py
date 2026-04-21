"""Configuration loading and validation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration loaded from env vars and CLI args."""

    # GitHub
    github_token: str = ""

    # LLM provider
    provider: str = "claude-code"
    model: str = "claude-sonnet-4-6"

    # API keys (resolved based on provider)
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""

    # Scraper settings
    repos: list[str] = field(default_factory=list)
    max_prs: int = 300
    target_candidates: int | None = None  # stop early if enough pass pre-filter
    skip_bot_prs: bool = True

    # Pre-filter thresholds
    min_lines_changed: int = 5
    max_lines_changed: int = 500
    max_files_changed: int = 20
    min_description_length: int = 20

    # Evaluation settings
    accept_threshold: int = 18
    review_threshold: int = 13
    reliability_check: bool = False
    max_retries: int = 1
    min_navigation_depth: int = 3

    # Paths
    input_dir: Path = Path("candidates")
    input_file: Path | None = None
    output_dir: Path = Path("results")

    @property
    def api_key(self) -> str:
        """Return the API key for the configured provider."""
        if self.provider == "anthropic":
            return self.anthropic_api_key
        elif self.provider == "openrouter":
            return self.openrouter_api_key
        return ""

    def validate(self) -> list[str]:
        """Return a list of validation errors, empty if valid."""
        errors: list[str] = []

        if self.provider == "anthropic" and not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required when using the anthropic provider")
        elif self.provider == "openrouter" and not self.openrouter_api_key:
            errors.append("OPENROUTER_API_KEY is required when using the openrouter provider")

        return errors

    def validate_scraper(self) -> list[str]:
        """Validate config for scraper mode."""
        errors = self.validate()
        if not self.github_token:
            errors.append("GITHUB_TOKEN is required for scraping PRs")
        if not self.repos:
            errors.append("At least one --repo is required")
        return errors

    def validate_evaluator(self) -> list[str]:
        """Validate config for evaluator mode."""
        errors = self.validate()
        if self.input_file and not self.input_file.exists():
            errors.append(f"Input file does not exist: {self.input_file}")
        elif not self.input_file and not self.input_dir.exists():
            errors.append(f"Input directory does not exist: {self.input_dir}")
        return errors


def load_config() -> Config:
    """Load config from environment variables. CLI args are applied separately."""
    load_dotenv(override=True)

    return Config(
        github_token=os.getenv("GITHUB_TOKEN", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
    )
