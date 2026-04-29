"""Tests for Stage 2 container bundle preparation."""

from __future__ import annotations

import json
from pathlib import Path

from src.workflow import stage2_container_bundle


def test_prepare_stage2_container_bundles_writes_bundle_artifacts(tmp_path: Path, monkeypatch) -> None:
    clones_dir = tmp_path / "clones"
    output_dir = tmp_path / "bundles"
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "encode__httpx.json").write_text(json.dumps({"repo": "encode/httpx"}), encoding="utf-8")

    bare_repo = clones_dir / "httpx.git"
    bare_repo.mkdir(parents=True)

    monkeypatch.setattr(stage2_container_bundle, "load_repo_profile", lambda repo, _: None)
    monkeypatch.setattr(stage2_container_bundle, "_resolve_probe_commits", lambda **kwargs: ["abc123def456"])
    monkeypatch.setattr(stage2_container_bundle, "_detect_requirement_files", lambda **kwargs: ["requirements.txt"])
    monkeypatch.setattr(
        stage2_container_bundle,
        "_export_commit_archive",
        lambda **kwargs: kwargs["output_path"].write_bytes(b"tar"),
    )
    monkeypatch.setattr(
        stage2_container_bundle,
        "_write_bundle_files",
        lambda **kwargs: (
            (kwargs["bundle_dir"] / "Dockerfile").write_text("FROM python:3.10-slim\n", encoding="utf-8"),
            (kwargs["bundle_dir"] / "install.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8"),
            (kwargs["bundle_dir"] / "probe.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8"),
            (kwargs["bundle_dir"] / "build_image.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8"),
            (kwargs["bundle_dir"] / "run_probe.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8"),
            (kwargs["bundle_dir"] / "metadata.json").write_text("{}", encoding="utf-8"),
            (kwargs["bundle_dir"] / "profile.json").write_text("null", encoding="utf-8"),
        ),
    )

    def fake_ensure_clone(repo: str, clones: Path) -> Path:
        return bare_repo

    monkeypatch.setattr("src.deep_eval.repo_manager.ensure_clone", fake_ensure_clone)

    report_path = stage2_container_bundle.prepare_stage2_container_bundles(
        repo="encode/httpx",
        clones_dir=clones_dir,
        output_dir=output_dir,
        profiles_dir=profiles_dir,
        sample_size=1,
    )

    report = json.loads(report_path.read_text())
    assert report["repo"] == "encode/httpx"
    assert report["summary"]["bundle_count"] == 1
    assert Path(report["bundles"][0]["bundle_dir"]).exists()
    assert report["bundles"][0]["default_results_dir"].endswith("probe_results")


def test_render_install_script_includes_requirement_followups() -> None:
    profile = None

    script = stage2_container_bundle._render_install_script(
        profile,
        requirement_files=["requirements.txt", "requirements-test.txt"],
    )

    assert "python -m pip install -e ." in script
    assert "python -m pip install -r requirements.txt" in script
    assert "python -m pip install -r requirements-test.txt" in script


def test_render_dockerfile_installs_uv_for_uv_profiles() -> None:
    class Runtime:
        python = "3.11"
        package_manager = "uv"

    class Environment:
        system_packages: list[str] = []

    class Profile:
        runtime = Runtime()
        environment = Environment()

    dockerfile = stage2_container_bundle._render_dockerfile(Profile())
    assert "RUN python -m pip install uv" in dockerfile


def test_render_install_script_adds_system_flag_for_uv_profiles() -> None:
    class Runtime:
        package_manager = "uv"

    class Environment:
        env_vars: dict[str, str] = {}
        pre_install: list[str] = []
        install_commands = ["uv pip install -e ."]
        install_fallbacks = ["pip install -e ."]
        post_install: list[str] = []

    class Profile:
        runtime = Runtime()
        environment = Environment()

    script = stage2_container_bundle._render_install_script(Profile(), requirement_files=[])
    assert "uv pip install --system -e ." in script


def test_render_install_script_exports_environment_env_vars_and_post_install() -> None:
    class Runtime:
        package_manager = "uv"

    class Environment:
        env_vars = {"SETUPTOOLS_SCM_PRETEND_VERSION_FOR_CATTRS": "0.0"}
        pre_install: list[str] = []
        install_commands = ["uv pip install -e ."]
        install_fallbacks: list[str] = []
        post_install = ["python -m pip install pytest hypothesis msgspec PyYAML pymongo orjson cbor2 msgpack tomlkit ujson"]

    class Profile:
        runtime = Runtime()
        environment = Environment()

    script = stage2_container_bundle._render_install_script(Profile(), requirement_files=[])
    assert 'export SETUPTOOLS_SCM_PRETEND_VERSION_FOR_CATTRS="0.0"' in script
    assert "python -m pip install pytest hypothesis msgspec PyYAML pymongo orjson cbor2 msgpack tomlkit ujson" in script


def test_normalize_probe_command_injects_collect_only_and_plugin_policy() -> None:
    class PluginPolicy:
        mode = "explicit_only"
        explicit_plugins = ["anyio.pytest_plugin"]

    command = stage2_container_bundle._normalize_probe_command("pytest -q", PluginPolicy())
    assert command.startswith("PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ")
    assert "--collect-only" in command
    assert "anyio.pytest_plugin" in command


def test_render_probe_script_writes_structured_probe_result() -> None:
    script = stage2_container_bundle._render_probe_script(None)
    assert 'RESULTS_DIR="${LLMJ_RESULTS_DIR:-/tmp/llmj-stage2-results}"' in script
    assert 'install.stdout.log' in script
    assert 'probe.stdout.log' in script
    assert 'probe_result.json' in script
    assert 'if bash -lc' in script
    assert '\n  if bash -lc ' in script
    assert '\nfi\nexport INSTALL_STATUS PROBE_STATUS PROBE_EXIT_CODE' in script
    assert script.count("\nfi\n") >= 3
    assert "PROBE_CMD_STATUS" not in script


def test_render_run_script_mounts_host_results_directory() -> None:
    script = stage2_container_bundle._render_run_script(
        {
            "repo_short": "httpx",
            "commit_sha": "abc123def4567890",
        }
    )
    assert 'RESULTS_DIR="${1:-$(pwd)/probe_results}"' in script
    assert "if docker run --rm" in script
    assert '-v "$RESULTS_DIR:/results"' in script
    assert 'container.stdout.log' in script
    assert 'docker_exit_code.txt' in script
