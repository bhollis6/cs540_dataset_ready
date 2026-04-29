"""Repo profile loading scaffolding for historical environment execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import json


DEFAULT_PROFILE_DIR = Path("repo_profiles")


@dataclass
class RuntimeProfile:
    os: str = "ubuntu-22.04"
    arch: str = "x86_64"
    python: str = "3.10"
    package_manager: str = "uv"


@dataclass
class EnvironmentProfile:
    env_commit_strategy: str = "base_or_override"
    system_packages: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
    pre_install: list[str] = field(default_factory=list)
    install_commands: list[str] = field(default_factory=list)
    install_fallbacks: list[str] = field(default_factory=list)
    post_install: list[str] = field(default_factory=list)
    dependency_pins: dict[str, str] = field(default_factory=dict)


@dataclass
class PluginPolicyProfile:
    mode: str = "default"
    explicit_plugins: list[str] = field(default_factory=list)


@dataclass
class TestProfile:
    command: str = "pytest -q"
    selection_mode: str = "explicit_nodeids"
    plugin_policy: PluginPolicyProfile = field(default_factory=PluginPolicyProfile)
    env_vars: dict[str, str] = field(default_factory=dict)


@dataclass
class HistoricalQuirksProfile:
    known_break_windows: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class DegradationProfile:
    supported_conditions: list[str] = field(default_factory=lambda: [
        "type_hints",
        "naming",
        "comments_docstrings",
        "remove_tests",
    ])
    test_support_globs: list[str] = field(default_factory=list)


@dataclass
class AdmissionProfile:
    pilot_probe_target: int = 3
    pilot_min_verified_tasks: int = 2


@dataclass
class RepoProfile:
    repo: str
    profile_version: int = 1
    runtime: RuntimeProfile = field(default_factory=RuntimeProfile)
    environment: EnvironmentProfile = field(default_factory=EnvironmentProfile)
    test: TestProfile = field(default_factory=TestProfile)
    historical_quirks: HistoricalQuirksProfile = field(default_factory=HistoricalQuirksProfile)
    degradation: DegradationProfile = field(default_factory=DegradationProfile)
    admission: AdmissionProfile = field(default_factory=AdmissionProfile)
    source_path: Path | None = None


def profile_filename_for_repo(repo: str) -> str:
    return repo.replace("/", "__") + ".json"


def load_repo_profile(repo: str, profiles_dir: Path = DEFAULT_PROFILE_DIR) -> RepoProfile | None:
    """Load a repo profile if one exists, otherwise return None."""
    profile_path = profiles_dir / profile_filename_for_repo(repo)
    if not profile_path.exists():
        return None
    with open(profile_path) as f:
        raw = json.load(f)
    profile = repo_profile_from_dict(raw)
    profile.source_path = profile_path
    return profile


def repo_profile_from_dict(data: dict[str, Any]) -> RepoProfile:
    plugin_policy = PluginPolicyProfile(**data.get("test", {}).get("plugin_policy", {}))
    test_data = dict(data.get("test", {}))
    test_data["plugin_policy"] = plugin_policy

    return RepoProfile(
        repo=data["repo"],
        profile_version=int(data.get("profile_version", 1)),
        runtime=RuntimeProfile(**data.get("runtime", {})),
        environment=EnvironmentProfile(**data.get("environment", {})),
        test=TestProfile(**test_data),
        historical_quirks=HistoricalQuirksProfile(**data.get("historical_quirks", {})),
        degradation=DegradationProfile(**data.get("degradation", {})),
        admission=AdmissionProfile(**data.get("admission", {})),
    )


def repo_profile_to_dict(profile: RepoProfile) -> dict[str, Any]:
    return {
        "repo": profile.repo,
        "profile_version": profile.profile_version,
        "runtime": {
            "os": profile.runtime.os,
            "arch": profile.runtime.arch,
            "python": profile.runtime.python,
            "package_manager": profile.runtime.package_manager,
        },
        "environment": {
            "env_commit_strategy": profile.environment.env_commit_strategy,
            "system_packages": profile.environment.system_packages,
            "env_vars": profile.environment.env_vars,
            "pre_install": profile.environment.pre_install,
            "install_commands": profile.environment.install_commands,
            "install_fallbacks": profile.environment.install_fallbacks,
            "post_install": profile.environment.post_install,
            "dependency_pins": profile.environment.dependency_pins,
        },
        "test": {
            "command": profile.test.command,
            "selection_mode": profile.test.selection_mode,
            "plugin_policy": {
                "mode": profile.test.plugin_policy.mode,
                "explicit_plugins": profile.test.plugin_policy.explicit_plugins,
            },
            "env_vars": profile.test.env_vars,
        },
        "historical_quirks": {
            "known_break_windows": profile.historical_quirks.known_break_windows,
            "notes": profile.historical_quirks.notes,
        },
        "degradation": {
            "supported_conditions": profile.degradation.supported_conditions,
            "test_support_globs": profile.degradation.test_support_globs,
        },
        "admission": {
            "pilot_probe_target": profile.admission.pilot_probe_target,
            "pilot_min_verified_tasks": profile.admission.pilot_min_verified_tasks,
        },
    }
