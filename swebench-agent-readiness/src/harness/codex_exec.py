"""Minimal non-interactive Codex CLI runner for the first pilot."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CodexExecSpec:
    """Execution contract for one non-interactive Codex run."""

    condition: str
    workspace_dir: Path
    prompt_path: Path
    stdout_log_path: Path
    stderr_log_path: Path
    output_last_message_path: Path
    sandbox_mode: str = "workspace-write"
    env_bin_dir: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition": self.condition,
            "workspace_dir": str(self.workspace_dir),
            "prompt_path": str(self.prompt_path),
            "stdout_log_path": str(self.stdout_log_path),
            "stderr_log_path": str(self.stderr_log_path),
            "output_last_message_path": str(self.output_last_message_path),
            "sandbox_mode": self.sandbox_mode,
            "env_bin_dir": str(self.env_bin_dir) if self.env_bin_dir else None,
        }


def build_codex_exec_command(spec: CodexExecSpec) -> list[str]:
    """Build the exact CLI argv for one Codex run."""

    return [
        "codex",
        "exec",
        "-C",
        str(spec.workspace_dir),
        "--full-auto",
        "--ephemeral",
        "--json",
        "--color",
        "never",
        "--output-last-message",
        str(spec.output_last_message_path),
        "--sandbox",
        spec.sandbox_mode,
        "-",
    ]


def run_codex_exec(spec: CodexExecSpec) -> subprocess.CompletedProcess[str]:
    """Run Codex against a materialized pilot workspace."""

    prompt = spec.prompt_path.read_text(encoding="utf-8")
    spec.stdout_log_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    if spec.env_bin_dir is not None:
        current_path = env.get("PATH", "")
        env["PATH"] = os.pathsep.join([str(spec.env_bin_dir), current_path]) if current_path else str(spec.env_bin_dir)
    with spec.stdout_log_path.open("w", encoding="utf-8") as stdout_handle:
        with spec.stderr_log_path.open("w", encoding="utf-8") as stderr_handle:
            return subprocess.run(
                build_codex_exec_command(spec),
                input=prompt,
                text=True,
                stdout=stdout_handle,
                stderr=stderr_handle,
                env=env,
                check=False,
            )


def write_codex_exec_spec(spec: CodexExecSpec, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(spec.to_dict(), handle, indent=2)
    return path
