"""Parse lightweight bootstrap metrics from Codex JSONL logs."""

from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


EDIT_COMMAND_HINTS = (
    "apply_patch",
    "sed -i",
    "perl -0pi",
    "python - <<",
    "python3 - <<",
    "cat <<",
    "tee ",
    ">>",
    " > ",
)


@dataclass(frozen=True)
class CodexAgentMetrics:
    """Minimal exploration and usage metrics for one Codex run."""

    files_opened_before_first_edit: int | None
    opened_files_before_first_edit: list[str] = field(default_factory=list)
    relevant_files_opened: int | None = None
    relevant_opened_files: list[str] = field(default_factory=list)
    dead_end_file_opens: int | None = None
    dead_end_opened_files: list[str] = field(default_factory=list)
    exploration_efficiency: float | None = None
    first_edit_detected: bool = False
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "files_opened_before_first_edit": self.files_opened_before_first_edit,
            "opened_files_before_first_edit": list(self.opened_files_before_first_edit),
            "relevant_files_opened": self.relevant_files_opened,
            "relevant_opened_files": list(self.relevant_opened_files),
            "dead_end_file_opens": self.dead_end_file_opens,
            "dead_end_opened_files": list(self.dead_end_opened_files),
            "exploration_efficiency": self.exploration_efficiency,
            "first_edit_detected": self.first_edit_detected,
            "input_tokens": self.input_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


def parse_codex_agent_metrics(
    *,
    stdout_log_path: Path,
    workspace_dir: Path,
    relevant_files: set[str] | None = None,
) -> CodexAgentMetrics:
    """Extract the first useful bootstrap metrics from a Codex JSONL log."""

    events = _load_codex_events(stdout_log_path)
    first_edit_index = _first_codex_edit_index(events)
    pre_edit_events = events if first_edit_index is None else events[:first_edit_index]
    opened_files = _codex_opened_files(pre_edit_events, workspace_path=workspace_dir)
    relevant_file_set = {path.replace("\\", "/") for path in (relevant_files or set())}
    relevant_opened_files = sorted(path for path in opened_files if path in relevant_file_set)
    dead_end_opened_files = sorted(path for path in opened_files if path not in relevant_file_set)
    usage = _extract_usage(events)
    token_values = [usage.get("input_tokens"), usage.get("output_tokens")]
    total_tokens = None
    if any(value is not None for value in token_values):
        total_tokens = sum(int(value or 0) for value in token_values)

    return CodexAgentMetrics(
        files_opened_before_first_edit=len(opened_files),
        opened_files_before_first_edit=opened_files,
        relevant_files_opened=len(relevant_opened_files),
        relevant_opened_files=relevant_opened_files,
        dead_end_file_opens=len(dead_end_opened_files),
        dead_end_opened_files=dead_end_opened_files,
        exploration_efficiency=(
            round(len(relevant_opened_files) / len(opened_files), 4) if opened_files else None
        ),
        first_edit_detected=first_edit_index is not None,
        input_tokens=usage.get("input_tokens"),
        cached_input_tokens=usage.get("cached_input_tokens"),
        output_tokens=usage.get("output_tokens"),
        total_tokens=total_tokens,
    )


def _load_codex_events(stdout_path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stdout_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _first_codex_edit_index(events: list[dict[str, Any]]) -> int | None:
    for index, event in enumerate(events):
        item = event.get("item", {})
        item_type = item.get("type")
        if item_type in {"patch", "file_change"}:
            return index
        if item_type == "command_execution" and _looks_like_edit_command(item.get("command", "")):
            return index
    return None


def _looks_like_edit_command(command: str) -> bool:
    normalized = command.lower()
    return any(hint in normalized for hint in EDIT_COMMAND_HINTS)


def _codex_opened_files(events: list[dict[str, Any]], *, workspace_path: Path) -> list[str]:
    opened: list[str] = []
    seen: set[str] = set()
    for event in events:
        item = event.get("item", {})
        if item.get("type") != "command_execution" or event.get("type") != "item.completed":
            continue
        for relative_path in _extract_paths_from_command(item.get("command", ""), workspace_path=workspace_path):
            if relative_path in seen:
                continue
            seen.add(relative_path)
            opened.append(relative_path)
    return opened


def _extract_paths_from_command(command: str, *, workspace_path: Path) -> list[str]:
    inner = _extract_shell_command(command)
    if not inner:
        return []
    try:
        tokens = shlex.split(inner)
    except ValueError:
        return []
    candidates: list[str] = []
    for token in tokens:
        if token.startswith("-") or token in {"bash", "python", "python3", "rg", "sed", "cat", "head", "tail", "git", "nl"}:
            continue
        normalized = token.strip().strip("\"'").replace("\\", "/")
        if "::" in normalized:
            normalized = normalized.split("::", 1)[0]
        if normalized.startswith("/"):
            path = Path(normalized)
            if path.is_file():
                try:
                    relative = path.relative_to(workspace_path).as_posix()
                except ValueError:
                    continue
                candidates.append(relative)
            continue
        if normalized.startswith(".") or "/" in normalized:
            path = workspace_path / normalized
            if path.exists() and path.is_file():
                candidates.append(path.relative_to(workspace_path).as_posix())
    return candidates


def _extract_shell_command(command: str) -> str:
    match = re.search(r"bash -lc (?P<quote>['\"])(?P<body>.*)(?P=quote)$", command)
    if match:
        return match.group("body")
    return command


def _extract_usage(events: list[dict[str, Any]]) -> dict[str, int | None]:
    for event in reversed(events):
        if event.get("type") != "turn.completed":
            continue
        usage = event.get("usage", {})
        return {
            "input_tokens": _maybe_int(usage.get("input_tokens")),
            "cached_input_tokens": _maybe_int(usage.get("cached_input_tokens")),
            "output_tokens": _maybe_int(usage.get("output_tokens")),
        }
    return {
        "input_tokens": None,
        "cached_input_tokens": None,
        "output_tokens": None,
    }


def _maybe_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
