"""Tests for repo profile scaffolding."""

from __future__ import annotations

from pathlib import Path

from src.profiles import (
    RepoProfile,
    load_repo_profile,
    profile_filename_for_repo,
    repo_profile_from_dict,
    repo_profile_to_dict,
)


def test_profile_filename_for_repo() -> None:
    assert profile_filename_for_repo("encode/httpx") == "encode__httpx.json"


def test_repo_profile_roundtrip() -> None:
    raw = {
        "repo": "encode/httpx",
        "runtime": {"python": "3.11"},
        "environment": {
            "env_vars": {
                "SETUPTOOLS_SCM_PRETEND_VERSION": "0.0",
                "SETUPTOOLS_SCM_PRETEND_VERSION_FOR_CATTRS": "0.0",
            },
            "install_commands": ["uv pip install -e ."],
            "post_install": ["python -m pip install pytest"],
        },
        "test": {
            "command": "pytest -q",
            "plugin_policy": {"mode": "default", "explicit_plugins": []},
        },
    }

    profile = repo_profile_from_dict(raw)
    assert isinstance(profile, RepoProfile)
    assert profile.repo == "encode/httpx"
    assert profile.runtime.python == "3.11"

    roundtripped = repo_profile_from_dict(repo_profile_to_dict(profile))
    assert roundtripped.repo == profile.repo
    assert roundtripped.environment.env_vars == {
        "SETUPTOOLS_SCM_PRETEND_VERSION": "0.0",
        "SETUPTOOLS_SCM_PRETEND_VERSION_FOR_CATTRS": "0.0",
    }
    assert roundtripped.environment.install_commands == ["uv pip install -e ."]
    assert roundtripped.environment.post_install == ["python -m pip install pytest"]


def test_load_repo_profile_returns_none_for_missing_profile(tmp_path: Path) -> None:
    assert load_repo_profile("encode/httpx", tmp_path) is None


def test_load_repo_profile_reads_existing_profile(tmp_path: Path) -> None:
    profile_dir = tmp_path
    profile_path = profile_dir / "encode__httpx.json"
    profile_path.write_text(
        '{"repo":"encode/httpx","runtime":{"python":"3.11"}}',
        encoding="utf-8",
    )

    profile = load_repo_profile("encode/httpx", profile_dir)
    assert profile is not None
    assert profile.repo == "encode/httpx"
    assert profile.runtime.python == "3.11"
    assert profile.source_path == profile_path


def test_profile_roundtrip_preserves_post_install_commands() -> None:
    profile = repo_profile_from_dict({
        "repo": "encode/starlette",
        "environment": {
            "post_install": [
                "python -m pip install pytest pytest-cov trio httpx pyyaml jinja2 itsdangerous \"python-multipart<0.0.14\""
            ],
        },
        "test": {"plugin_policy": {"mode": "default", "explicit_plugins": []}},
    })

    roundtripped = repo_profile_from_dict(repo_profile_to_dict(profile))
    assert roundtripped.environment.post_install == [
        "python -m pip install pytest pytest-cov trio httpx pyyaml jinja2 itsdangerous \"python-multipart<0.0.14\""
    ]


def test_starlette_profile_installs_historical_test_dependencies() -> None:
    profile = load_repo_profile("encode/starlette", Path("repo_profiles"))

    assert profile is not None
    command = profile.environment.post_install[0]
    assert "pytest-cov" in command
    assert '"python-multipart<0.0.14"' in command


def test_cattrs_profile_installs_attrs_for_historical_tests() -> None:
    profile = load_repo_profile("python-attrs/cattrs", Path("repo_profiles"))

    assert profile is not None
    command = profile.environment.post_install[0]
    assert "attrs" in command


def test_uvicorn_profile_installs_historical_test_dependencies() -> None:
    profile = load_repo_profile("encode/uvicorn", Path("repo_profiles"))

    assert profile is not None
    command = profile.environment.post_install[0]
    assert "pytest-xdist" in command
    assert '"pytest-asyncio<0.24"' in command
    assert "xdist.plugin" in profile.test.plugin_policy.explicit_plugins


def test_copier_profile_installs_git_runtime_and_pytest_plugins() -> None:
    profile = load_repo_profile("copier-org/copier", Path("repo_profiles"))

    assert profile is not None
    command = profile.environment.post_install[0]
    assert "pytest-gitconfig" in command
    assert "pexpect" in command
    assert "poethepoet" in command
    assert "git" in profile.environment.system_packages
    assert "pytest_gitconfig.plugin" in profile.test.plugin_policy.explicit_plugins
