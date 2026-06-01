#!/usr/bin/env python3
"""Action-boundary rule binding guard.

This helper is intentionally host-root aware. It emits plain STOP text when a
supported action-boundary rule is violated and exits 0 so wrapper hooks can
convert the message into their native allow/deny protocol.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd()).resolve()
LAZY = ROOT / ".lazy-harness"

RUNTIME_COMMAND_RE = re.compile(
    r"""
    (?:^|[;&|]\s*)
    (?:
      bun\s+(?:run\s+)?dev(?:[:\w.-]*)?\b
      | bun\s+[^;&|]*\bscripts/dev-cli\.ts\b
      | bun\s+[^;&|]*\bdev-cli\.ts\b
      | npm\s+run\s+dev(?:[:\w.-]*)?\b
      | pnpm\s+(?:run\s+)?dev(?:[:\w.-]*)?\b
      | yarn\s+(?:run\s+)?dev(?:[:\w.-]*)?\b
      | next\s+dev\b
      | vite\b
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

RUNTIME_RECORD_RE = re.compile(
    r"(?:runtime|dogfood|dev[-_]?server|dev[-_]?instance|test[-_]?instance|instance)",
    re.IGNORECASE,
)


def parse_payload(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw or "{}")
    except Exception:
        return {"raw": raw}
    return data if isinstance(data, dict) else {"raw": raw}


def walk_strings(value: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(value, str):
        strings.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            strings.extend(walk_strings(item))
    elif isinstance(value, list):
        for item in value:
            strings.extend(walk_strings(item))
    return strings


def extract_bash_command(payload: dict[str, Any]) -> str:
    # Prefer known command fields. Jcode payload shapes can vary across versions.
    candidates: list[Any] = []
    for path in [
        ("tool", "args", "command"),
        ("tool", "input", "command"),
        ("args", "command"),
        ("input", "command"),
        ("command",),
    ]:
        cur: Any = payload
        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                cur = None
                break
            cur = cur[key]
        if isinstance(cur, str):
            candidates.append(cur)

    # Fall back to all strings but only return a string that resembles a supported
    # action-boundary command. This avoids treating arbitrary prose as shell.
    candidates.extend(walk_strings(payload))
    for candidate in candidates:
        if not isinstance(candidate, str):
            continue
        if re.search(r"\bgh\s+pr\s+(create|edit)\b", candidate) or RUNTIME_COMMAND_RE.search(candidate):
            return candidate
    return ""


def recent_tool_calls(payload: dict[str, Any]) -> list[dict[str, Any]]:
    calls = payload.get("recent_tool_calls") or payload.get("recentToolCalls") or []
    return [call for call in calls if isinstance(call, dict)] if isinstance(calls, list) else []


def args_blob(call: dict[str, Any]) -> str:
    value = call.get("args_preview") or call.get("argsPreview") or call.get("args") or call.get("input") or ""
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def runtime_policy_dirs() -> tuple[str, ...]:
    # TDD regression records can mention runtime failures, but they are not host
    # runtime policy sources. Avoid letting framework tests make every host dev
    # command block by default.
    return ("domain", "spec", "behavior", "decisions", "ssot")


def runtime_policy_records() -> list[Path]:
    records: list[Path] = []
    for layer in runtime_policy_dirs():
        directory = LAZY / layer
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".md", ".xml", ".json", ".jsonl"}:
                rel = path.relative_to(LAZY).as_posix()
                if RUNTIME_RECORD_RE.search(rel):
                    records.append(path)
    return sorted(records)


def has_runtime_record_lookup(payload: dict[str, Any], records: list[Path]) -> bool:
    rel_records = [f".lazy-harness/{path.relative_to(LAZY).as_posix()}" for path in records]
    runtime_tokens = ("runtime", "dogfood", "dev-cli", "dev server", "dev-server", "instance", "test database", "test db")
    for call in recent_tool_calls(payload):
        name = str(call.get("name") or "").lower()
        blob = args_blob(call)
        blob_lower = blob.lower()
        if any(rel in blob for rel in rel_records):
            return True
        if name in {"read", "grep", "agentgrep", "glob", "bash"} or name.endswith(".agentgrep"):
            if ".lazy-harness" in blob_lower and any(token in blob_lower for token in runtime_tokens):
                return True
    return False


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def default_pr_body_binding() -> dict[str, Any] | None:
    source = LAZY / "ssot" / "pr-description-format.md"
    if not source.exists():
        return None
    return {
        "id": "default-pr-body-format",
        "status": "enforced",
        "sourceRecord": ".lazy-harness/ssot/pr-description-format.md",
        "appliesWhen": ["creating_pull_request", "editing_pull_request"],
        "actions": [{"tool": "bash", "commandRegex": r"\bgh\s+pr\s+(create|edit)\b"}],
        "severity": "block",
        "checks": ["read_source_record", "validate_required_sections"],
        "requiredSections": ["## Why", "## What", "## Task"],
    }


def normalize_bindings(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        items = data.get("bindings")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []


def load_bindings() -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for rel in ["ssot/rule-bindings.json", "generated/rule-bindings.json"]:
        path = LAZY / rel
        if path.exists():
            bindings.extend(normalize_bindings(load_json(path)))
    default = default_pr_body_binding()
    if default and not any(binding.get("id") in {"default-pr-body-format", "pr-body-format"} for binding in bindings):
        bindings.append(default)
    return bindings


def shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except Exception:
        return []


def resolve_body_file(path_text: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = ROOT / path
    return path


def extract_body(command: str) -> tuple[str | None, str]:
    tokens = shell_tokens(command)
    for index, token in enumerate(tokens):
        if token in {"--body", "-b"} and index + 1 < len(tokens):
            return tokens[index + 1], token
        if token.startswith("--body="):
            return token.split("=", 1)[1], "--body"
        if token == "--body-file" and index + 1 < len(tokens):
            path = resolve_body_file(tokens[index + 1])
            try:
                return path.read_text(encoding="utf-8"), f"--body-file {tokens[index + 1]}"
            except Exception as exc:
                return None, f"unreadable --body-file {tokens[index + 1]}: {exc}"
        if token.startswith("--body-file="):
            file_text = token.split("=", 1)[1]
            path = resolve_body_file(file_text)
            try:
                return path.read_text(encoding="utf-8"), f"--body-file={file_text}"
            except Exception as exc:
                return None, f"unreadable --body-file={file_text}: {exc}"
    return None, "missing --body/--body-file"


def command_matches(binding: dict[str, Any], command: str) -> bool:
    for action in binding.get("actions") or []:
        if not isinstance(action, dict):
            continue
        if action.get("tool") not in {None, "bash"}:
            continue
        pattern = action.get("commandRegex")
        if isinstance(pattern, str) and re.search(pattern, command):
            return True
    return False


def missing_sections(body: str, required_sections: list[str]) -> list[str]:
    lowered = body.lower()
    return [section for section in required_sections if section.lower() not in lowered]


def check_pr_body_binding(binding: dict[str, Any], command: str) -> str:
    required = [str(item) for item in binding.get("requiredSections") or ["## Why", "## What", "## Task"]]
    body, source = extract_body(command)
    source_record = str(binding.get("sourceRecord") or ".lazy-harness/ssot/pr-description-format.md")
    if body is None:
        return (
            "STOP. Rule binding violation: PR body format rule must be applied before PR mutation.\n\n"
            f"Source record: `{source_record}`\n"
            f"Problem: {source}.\n"
            "Required body sections:\n"
            + "\n".join(f"  - {section}" for section in required)
            + "\n\nUse `--body-file` or `--body` with the required structure before running `gh pr create/edit`."
        )
    missing = missing_sections(body, required)
    if missing:
        return (
            "STOP. Rule binding violation: PR body does not match the stored PR description format.\n\n"
            f"Source record: `{source_record}`\n"
            f"Body source: {source}\n"
            "Missing sections:\n"
            + "\n".join(f"  - {section}" for section in missing)
            + "\n\nRead the source record and rewrite the PR body before running `gh pr create/edit`."
        )
    return ""


def check_runtime_record_binding(command: str, payload: dict[str, Any]) -> str:
    if not RUNTIME_COMMAND_RE.search(command):
        return ""

    records = runtime_policy_records()
    if not records:
        return ""
    if has_runtime_record_lookup(payload, records):
        return ""

    listed = "\n".join(f"  - `.lazy-harness/{path.relative_to(LAZY).as_posix()}`" for path in records[:8])
    more = "" if len(records) <= 8 else f"\n  - ... and {len(records) - 8} more"
    return (
        "STOP. Runtime action-boundary requires record-first lookup before starting or inspecting a dev/test instance.\n\n"
        f"Command: `{command}`\n\n"
        "Relevant runtime/dogfood records exist in this host:\n"
        f"{listed}{more}\n\n"
        "Before running this command, read or search the relevant canonical record, for example:\n\n"
        "  grep -rli 'runtime\\|dogfood\\|instance\\|dev-cli\\|test database' "
        ".lazy-harness/{domain,spec,behavior,decisions,ssot}/\n\n"
        "Then rerun the command with that record lookup present in recent tool-call history."
    )


def check_bindings(command: str, payload: dict[str, Any], bindings: list[dict[str, Any]]) -> str:
    for binding in bindings:
        if binding.get("status") in {"retired", "advisory-only"}:
            continue
        if not command_matches(binding, command):
            continue
        checks = set(str(item) for item in binding.get("checks") or [])
        if "validate_required_sections" in checks or binding.get("requiredSections"):
            output = check_pr_body_binding(binding, command)
            if output:
                return output
    runtime_output = check_runtime_record_binding(command, payload)
    if runtime_output:
        return runtime_output
    return ""


def main() -> int:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    if not LAZY.exists():
        return 0
    payload = parse_payload(raw)
    command = extract_bash_command(payload)
    if not command:
        return 0
    output = check_bindings(command, payload, load_bindings())
    if output:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
