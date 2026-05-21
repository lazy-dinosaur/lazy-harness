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
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd()).resolve()

HELPERS = [
    ".lazy-harness/hooks/lifecycle/helpers/check-layer-impact.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-ddd-trigger.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-ssot-trigger.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-option-gate-discipline.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-record-before-session-history.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-lazy-cli-entrypoint.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-tdd-cross-verify.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-affected-tests.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-aftershock-reanalysis.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-fix-regression.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-adr-sync.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-handoff-stale.sh",
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


def run_one_helper(helper_path: Path, helper: str, raw_payload: str, root: Path) -> dict[str, Any]:
    start = time.perf_counter()
    completed = subprocess.run(
        [str(helper_path), raw_payload],
        cwd=root,
        text=True,
        capture_output=True,
        env={**os.environ, "LAZY_HOST_ROOT": str(root)},
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


def inspect(raw_payload: str, root: Path) -> dict[str, Any]:
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
        result = run_one_helper(helper_path, helper, raw_payload, root)
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
    }


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
    args = parser.parse_args()
    root = Path(args.root).resolve()
    raw_payload = args.payload if args.payload is not None else sys.stdin.read()
    result = inspect(raw_payload, root)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_md(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
