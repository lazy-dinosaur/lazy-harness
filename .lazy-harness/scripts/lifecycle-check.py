#!/usr/bin/env python3
"""Shadow lifecycle orchestrator for response.completed helpers.

Phase 2 performance work: parse payload once, compute shared state once, and
run the existing helper order in shadow mode. This script does not replace the
hook and does not mutate hook behavior.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd()).resolve()
HELPER_DIR = Path(__file__).resolve().parents[1] / "hooks" / "lifecycle" / "helpers"
sys.path.insert(0, str(HELPER_DIR))
try:
    from runtime_paths import runtime_state_path
except Exception:  # pragma: no cover - transitional hosts can still run shadow mode
    runtime_state_path = None  # type: ignore[assignment]

HELPERS = [
    ".lazy-harness/hooks/lifecycle/helpers/check-layer-impact.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-ddd-trigger.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-ssot-trigger.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-user-correction-capture.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-operating-rule-storage.py",
    ".lazy-harness/hooks/lifecycle/helpers/check-impl-map-status-drift.py",
    ".lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py",
    ".lazy-harness/hooks/lifecycle/helpers/check-record-decision-shadow.py",
    ".lazy-harness/hooks/lifecycle/helpers/check-option-gate-discipline.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-record-before-session-history.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-lazy-cli-entrypoint.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-tdd-cross-verify.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-affected-tests.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-aftershock-reanalysis.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-fix-regression.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-adr-sync.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-handoff-stale.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-policy-warn-runtime.py",
    ".lazy-harness/hooks/lifecycle/helpers/check-policy-block-runtime.py",
]

READ_ONLY_TOOLS = {
    "read", "Read",
    "grep", "Grep", "agentgrep", "glob", "Glob", "ls", "LS",
    "webfetch", "websearch",
    "mcp__filesystem__read_text_file", "mcp__filesystem__read_file", "mcp__filesystem__read_multiple_files",
    "mcp__filesystem__list_directory", "mcp__filesystem__list_directory_with_sizes", "mcp__filesystem__directory_tree",
    "mcp__filesystem__search_files", "mcp__filesystem__get_file_info",
}

WRITE_ONLY_HELPERS = {
    ".lazy-harness/hooks/lifecycle/helpers/check-layer-impact.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-ddd-trigger.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-ssot-trigger.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-tdd-cross-verify.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-affected-tests.sh",
}


def parse_payload(raw: str) -> tuple[dict[str, Any], bool, str | None]:
    try:
        payload = json.loads(raw or "{}")
    except Exception as exc:
        return {}, False, str(exc)
    if not isinstance(payload, dict):
        return {}, False, "payload-not-object"
    return payload, True, None


def fastpath_skips(payload: dict[str, Any], parsed_ok: bool) -> tuple[set[str], str]:
    if not parsed_ok:
        return set(), "fallback:payload-parse-failed"
    if "recent_tool_calls" not in payload:
        return set(), "fallback:missing-recent-tool-calls"
    calls = payload.get("recent_tool_calls")
    if not isinstance(calls, list):
        return set(), "fallback:recent-tool-calls-not-list"
    for call in calls:
        if not isinstance(call, dict):
            return set(), "fallback:tool-call-not-object"
        name = str(call.get("name") or "")
        if name not in READ_ONLY_TOOLS:
            return set(), f"fallback:non-read-only-tool:{name}"
    return set(WRITE_ONLY_HELPERS), "read-only-fast-path"


def inject_json(body: str) -> str:
    return json.dumps({"inject": {"body": body, "format": "system_reminder"}}, ensure_ascii=False)


def run_one_helper(helper_path: Path, helper: str, raw_payload: str, root: Path, helper_env: dict[str, str] | None = None) -> dict[str, Any]:
    start = time.perf_counter()
    env = {**os.environ, **(helper_env or {}), "LAZY_HOST_ROOT": str(root)}
    completed = subprocess.run(
        [str(helper_path), raw_payload],
        cwd=root,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
    return {
        "helper": helper,
        "status": "ran",
        "skipped": False,
        "exitCode": completed.returncode,
        "durationMs": elapsed_ms,
        "outputEmitted": bool(completed.stdout.strip()),
        "stdout": completed.stdout,
    }


def inspect(raw_payload: str, root: Path, helper_env: dict[str, str] | None = None, sandbox_context: dict[str, Any] | None = None) -> dict[str, Any]:
    payload, parsed_ok, parse_error = parse_payload(raw_payload)
    skip, fastpath_reason = fastpath_skips(payload, parsed_ok)
    helper_results: list[dict[str, Any]] = []
    selected: list[str] = []
    skipped: list[str] = []
    first_output = ""
    first_helper: str | None = None
    start = time.perf_counter()

    for helper in HELPERS:
        helper_path = root / helper
        if not helper_path.exists() or not os.access(helper_path, os.X_OK):
            skipped.append(helper)
            helper_results.append({"helper": helper, "status": "missing-or-not-executable", "skipped": True})
            continue
        if helper in skip:
            skipped.append(helper)
            helper_results.append({"helper": helper, "status": "fast-path-skipped", "skipped": True})
            continue
        selected.append(helper)
        result = run_one_helper(helper_path, helper, raw_payload, root, helper_env)
        helper_results.append(result)
        if result.get("outputEmitted"):
            first_output = str(result.get("stdout") or "")
            first_helper = helper
            break

    duration_ms = round((time.perf_counter() - start) * 1000, 3)
    return {
        "ok": True,
        "mode": "lifecycle-check.shadow",
        "schemaVersion": "1.0",
        "root": str(root),
        "parsedOk": parsed_ok,
        "parseError": parse_error,
        "fastPathReason": fastpath_reason,
        "selectedHelpers": selected,
        "skippedHelpers": skipped,
        "firstOutputHelper": first_helper,
        "firstOutput": first_output,
        "injectJson": inject_json(first_output) if first_output else "",
        "outputEmitted": bool(first_output),
        "durationMs": duration_ms,
        "helperResults": helper_results,
        "notes": [
            "Shadow orchestrator only; response.completed hook still owns production behavior.",
            "Parity tests must pass before any Phase 3 replacement.",
        ],
        "sandboxContext": sandbox_context or {},
    }


def git_output(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def bounded_copy_text(src: Path, dst: Path, max_lines: int = 400) -> int:
    if not src.exists() or not src.is_file():
        return 0
    try:
        lines = [line for line in src.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
    except Exception:
        return 0
    if max_lines > 0:
        lines = lines[-max_lines:]
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)


def source_runtime_state_candidates(root: Path, payload: dict[str, Any], name: str) -> list[Path]:
    candidates: list[Path] = []
    explicit_runtime = os.environ.get("LAZY_RUNTIME_ROOT")
    if explicit_runtime:
        candidates.append(Path(explicit_runtime) / "state" / name)
    if runtime_state_path is not None:
        try:
            candidates.append(runtime_state_path(root, name, payload))
        except Exception:
            pass
    candidates.append(root / ".lazy-harness" / "state" / name)
    seen: set[str] = set()
    out: list[Path] = []
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        out.append(candidate)
    return out


def mirror_first_existing_state(root: Path, payload: dict[str, Any], sandbox_runtime: Path, name: str, max_lines: int = 400) -> tuple[bool, int]:
    target = sandbox_runtime / "state" / name
    for source in source_runtime_state_candidates(root, payload, name):
        copied = bounded_copy_text(source, target, max_lines=max_lines)
        if copied:
            return True, copied
    return False, 0


def mirror_tool_events(root: Path, payload: dict[str, Any], target: Path, max_lines: int = 400) -> int:
    """Mirror only current message/session tool events into sandbox.

    `.jcode/hooks/tool-events.jsonl` can contain raw tool payloads. Compare-mode
    sandbox needs it only for stateful helpers that correlate by message/session
    id, so copy a bounded filtered subset instead of a wholesale log tail.
    """
    source = root / ".jcode" / "hooks" / "tool-events.jsonl"
    if not source.exists() or not source.is_file():
        return 0
    message_id = str(payload.get("message_id") or payload.get("messageId") or "")
    session_id = str(payload.get("session_id") or payload.get("sessionId") or "")
    if not message_id and not session_id:
        return 0
    matched: list[str] = []
    try:
        lines = source.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return 0
    for line in lines[-max_lines:]:
        _, sep, rest = line.partition(" ")
        if not sep:
            continue
        try:
            event = json.loads(rest)
        except Exception:
            continue
        if not isinstance(event, dict):
            continue
        event_message_id = str(event.get("message_id") or event.get("messageId") or "")
        event_session_id = str(event.get("session_id") or event.get("sessionId") or "")
        if message_id and event_message_id != message_id:
            continue
        if session_id and event_session_id != session_id:
            continue
        matched.append(line)
    if not matched:
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(matched[-max_lines:]) + "\n", encoding="utf-8")
    return len(matched[-max_lines:])


def sandbox_root(root: Path, raw_payload: str) -> tuple[Path, dict[str, str], dict[str, Any]]:
    """Create a temporary host copy for side-effect-safe compare/debug runs."""
    tmp = Path(tempfile.mkdtemp(prefix="lazy_lifecycle_check_sandbox_"))
    shutil.copytree(
        root / ".lazy-harness",
        tmp / ".lazy-harness",
        ignore=shutil.ignore_patterns(".cache", "state", "logs", "node_modules", "__pycache__"),
    )
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=False)
    payload, _, _ = parse_payload(raw_payload)
    sandbox_runtime = tmp / ".lazy-harness" / ".sandbox-runtime"
    sandbox_shared = tmp / ".lazy-harness" / ".sandbox-shared"
    helper_env: dict[str, str] = {
        "LAZY_RUNTIME_ROOT": str(sandbox_runtime),
        "LAZY_SHARED_ROOT": str(sandbox_shared),
        "LAZY_LIFECYCLE_SANDBOX_CONTEXT": "1",
    }
    last_subject = git_output(root, "log", "-1", "--pretty=%s")
    head = git_output(root, "rev-parse", "HEAD")
    if last_subject:
        helper_env["LAZY_LIFECYCLE_GIT_LAST_SUBJECT"] = last_subject
    if head:
        helper_env["LAZY_LIFECYCLE_GIT_HEAD"] = head

    mirrored: dict[str, Any] = {}
    for name in ("open-gates.json", "surfaced-rule-digests.jsonl", "search-read-debt.jsonl"):
        ok, rows = mirror_first_existing_state(root, payload, sandbox_runtime, name, max_lines=400)
        mirrored[name] = {"copied": ok, "rows": rows}

    tool_events_rows = mirror_tool_events(root, payload, tmp / ".jcode" / "hooks" / "tool-events.jsonl", max_lines=400)
    mirrored[".jcode/hooks/tool-events.jsonl"] = {"copied": tool_events_rows > 0, "rows": tool_events_rows}

    context = {
        "runtimeRoot": str(sandbox_runtime),
        "sharedRoot": str(sandbox_shared),
        "gitSubjectProvided": bool(last_subject),
        "gitHeadProvided": bool(head),
        "mirroredState": mirrored,
        "notes": [
            "Sandbox helpers run with isolated LAZY_RUNTIME_ROOT/LAZY_SHARED_ROOT.",
            "Only bounded state/journal tails are mirrored into the temporary sandbox.",
        ],
    }
    return tmp, helper_env, context


def render_md(result: dict[str, Any]) -> str:
    lines = ["# Lifecycle check shadow", ""]
    lines.append(f"- Root: `{result['root']}`")
    lines.append(f"- Parsed: {result['parsedOk']}")
    lines.append(f"- Fast-path: {result['fastPathReason']}")
    lines.append(f"- Output emitted: {result['outputEmitted']}")
    lines.append(f"- First output helper: {result['firstOutputHelper']}")
    lines.append(f"- Duration ms: {result['durationMs']}")
    lines.append("")
    lines.append("## Helpers")
    for item in result["helperResults"]:
        if item.get("skipped"):
            lines.append(f"- SKIP `{item['helper']}` ({item['status']})")
        else:
            lines.append(f"- RUN `{item['helper']}` exit={item.get('exitCode')} emitted={item.get('outputEmitted')} durationMs={item.get('durationMs')}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Shadow lifecycle response.completed orchestrator")
    parser.add_argument("--root", default=str(ROOT), help="host root")
    parser.add_argument("--payload", help="payload JSON string; defaults to stdin")
    parser.add_argument("--format", choices=["json", "md", "markdown"], default="json")
    parser.add_argument("--sandbox", action="store_true", help="run against a temporary .lazy-harness copy for side-effect-safe compare/debug mode")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    raw_payload = args.payload if args.payload is not None else sys.stdin.read()
    cleanup_root: Path | None = None
    helper_env: dict[str, str] | None = None
    sandbox_context: dict[str, Any] | None = None
    try:
        if args.sandbox:
            cleanup_root, helper_env, sandbox_context = sandbox_root(root, raw_payload)
            root = cleanup_root
        result = inspect(raw_payload, root, helper_env=helper_env, sandbox_context=sandbox_context)
        result["sandbox"] = bool(args.sandbox)
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(render_md(result))
    finally:
        if cleanup_root is not None:
            shutil.rmtree(cleanup_root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
