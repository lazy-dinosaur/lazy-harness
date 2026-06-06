#!/usr/bin/env python3
"""Measure lazy-harness prompt surfaces without changing runtime behavior.

Phase 1 scope: read-only budget report for prompt/runtime compression work.
The script renders message.received in an isolated runtime directory so the host's
normal runtime journals are not polluted by measurement fixtures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

SCHEMA_VERSION = "1.0"
SYNTHETIC_MESSAGE = "__lazy_prompt_budget_fixture_message__"

DEFAULT_BUDGETS = {
    "messageReceived": {"targetMinTokens": 200, "targetMaxTokens": 600, "hardMaxTokens": 1000, "transitionHardMaxTokens": 1400},
    "lazyAgents": {"targetMaxLines": 140, "hardMaxLines": 200, "transitionHardMaxLines": 220},
    "jcodeHarness05": {"targetMaxLines": 80, "hardMaxLines": 80, "transitionHardMaxLines": 220},
    "skillPrompt": {"targetMaxLines": 120, "hardMaxLines": 160, "transitionHardMaxLines": 200},
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure lazy-harness prompt surfaces")
    parser.add_argument("--root", default=os.environ.get("LAZY_HOST_ROOT") or os.getcwd(), help="Host root (default: LAZY_HOST_ROOT or cwd)")
    parser.add_argument("--format", choices=["json", "md"], default="md", help="Output format")
    parser.add_argument("--transition-message-tokens", type=int, default=DEFAULT_BUDGETS["messageReceived"]["transitionHardMaxTokens"], help="Temporary Phase 1 transition hard ceiling for rendered message.received tokens")
    return parser.parse_args(argv)


def resolve_root(value: str) -> pathlib.Path:
    root = pathlib.Path(value).expanduser().resolve()
    if not (root / ".lazy-harness").is_dir():
        raise SystemExit(f"prompt-budget: {root} does not contain .lazy-harness")
    return root


def estimate_tokens(text: str) -> int:
    non_space = re.sub(r"\s+", "", text)
    whitespace_tokens = len(re.findall(r"\S+", text))
    char_estimate = math.ceil(len(non_space) / 6) if non_space else 0
    return max(whitespace_tokens, char_estimate)


def count_lines(text: str) -> int:
    if text == "":
        return 0
    return len(text.splitlines())


def status_from_line_count(lines: int, hard: int | None, transition: int | None) -> str:
    if transition is not None and lines > transition:
        return "fail"
    if hard is not None and lines > hard:
        return "warn"
    return "pass"


def status_from_tokens(tokens: int, hard: int | None, transition: int | None) -> str:
    if transition is not None and tokens > transition:
        return "fail"
    if hard is not None and tokens > hard:
        return "warn"
    return "pass"


def merge_status(*statuses: str) -> str:
    if "fail" in statuses:
        return "fail"
    if "warn" in statuses:
        return "warn"
    return "pass"


def file_surface(root: pathlib.Path, path: pathlib.Path, *, kind: str, budget_key: str | None = None) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = str(path.relative_to(root))
    line_count = count_lines(text)
    token_estimate = estimate_tokens(text)
    budget = DEFAULT_BUDGETS.get(budget_key or "", {})
    hard = budget.get("hardMaxLines")
    transition = budget.get("transitionHardMaxLines")
    raw_status = status_from_line_count(line_count, hard if isinstance(hard, int) else None, transition if isinstance(transition, int) else None)
    enforcement = "advisory" if kind == "skill-prompt" else "enforced"
    status = "warn" if enforcement == "advisory" and raw_status == "fail" else raw_status
    return {
        "id": rel,
        "path": rel,
        "kind": kind,
        "present": True,
        "lineCount": line_count,
        "tokenEstimate": token_estimate,
        "status": status,
        "rawStatus": raw_status,
        "enforcement": enforcement,
        "budgetKey": budget_key,
        "sha256": hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16],
    }


def collect_file_surfaces(root: pathlib.Path) -> list[dict[str, Any]]:
    surfaces: list[dict[str, Any]] = []
    candidates: list[tuple[pathlib.Path, str, str | None]] = [
        (root / ".lazy-harness" / "AGENTS.md", "lazy-agents", "lazyAgents"),
        (root / "AGENTS.md", "root-agents", None),
    ]
    jcode_harness = root / ".jcode" / "harness"
    if jcode_harness.is_dir():
        for path in sorted(jcode_harness.glob("*.md")):
            key = "jcodeHarness05" if path.name == "05-lazy-harness.md" else None
            candidates.append((path, "jcode-harness", key))
    for base in [root / ".jcode" / "skills", root / ".lazy-harness" / "skills"]:
        if base.is_dir():
            for path in sorted(base.rglob("SKILL.md")):
                candidates.append((path, "skill-prompt", "skillPrompt"))
    for path, kind, budget_key in candidates:
        if path.exists() and path.is_file():
            surfaces.append(file_surface(root, path, kind=kind, budget_key=budget_key))
    return surfaces


def render_message_received(root: pathlib.Path, transition_message_tokens: int) -> dict[str, Any]:
    hook = root / ".lazy-harness" / "hooks" / "lifecycle" / "on-message-received.sh"
    if not hook.exists():
        return {"present": False, "status": "warn", "error": "missing hook", "path": str(hook)}
    runtime_dir = pathlib.Path(tempfile.mkdtemp(prefix="lazy-prompt-budget-runtime-"))
    payload = {
        "event": "message.received",
        "session_id": "prompt-budget-session",
        "message_id": "prompt-budget-message",
        "working_dir": str(root),
        "last_user_message": SYNTHETIC_MESSAGE,
        "recent_tool_calls": [],
        "turn_count": 1,
    }
    env = dict(os.environ)
    for key in ["GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_PREFIX", "GIT_QUARANTINE_PATH"]:
        env.pop(key, None)
    env["LAZY_HOST_ROOT"] = str(root)
    env["LAZY_RUNTIME_ROOT"] = str(runtime_dir)
    try:
        completed = subprocess.run(
            [str(hook)],
            cwd=root,
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
            env=env,
            timeout=5,
        )
        stdout = completed.stdout.strip()
        body = ""
        action = None
        if stdout:
            try:
                data = json.loads(stdout)
                action = data.get("action")
                body = str(data.get("inject", {}).get("body", ""))
            except Exception as exc:  # noqa: BLE001
                return {"present": True, "status": "fail", "error": f"invalid hook JSON: {exc}", "returnCode": completed.returncode}
        token_estimate = estimate_tokens(body)
        line_count = count_lines(body)
        status = status_from_tokens(token_estimate, DEFAULT_BUDGETS["messageReceived"]["hardMaxTokens"], transition_message_tokens)
        journal = runtime_dir / "state" / "search-read-debt.jsonl"
        journal_lines = 0
        if journal.exists():
            journal_lines = len([line for line in journal.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()])
        return {
            "present": True,
            "path": str(hook.relative_to(root)),
            "action": action,
            "returnCode": completed.returncode,
            "lineCount": line_count,
            "tokenEstimate": token_estimate,
            "characterCount": len(body),
            "status": status,
            "hardMaxTokens": DEFAULT_BUDGETS["messageReceived"]["hardMaxTokens"],
            "transitionHardMaxTokens": transition_message_tokens,
            "journalRows": journal_lines,
            "bodyHash": hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()[:16],
            "fixtureMessageLeaked": SYNTHETIC_MESSAGE in body or SYNTHETIC_MESSAGE in stdout,
        }
    except subprocess.TimeoutExpired:
        return {"present": True, "status": "fail", "error": "hook timeout"}
    finally:
        shutil.rmtree(runtime_dir, ignore_errors=True)


def normalized_blocks(text: str, *, min_lines: int = 4) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            if len(current) >= min_lines:
                blocks.append("\n".join(current))
            current = []
            continue
        stripped = re.sub(r"\s+", " ", stripped)
        current.append(stripped)
    if len(current) >= min_lines:
        blocks.append("\n".join(current))
    return blocks


def find_duplicate_blocks(root: pathlib.Path) -> list[dict[str, Any]]:
    primary = root / ".lazy-harness" / "AGENTS.md"
    local = root / ".jcode" / "harness" / "05-lazy-harness.md"
    if not primary.exists() or not local.exists():
        return []
    primary_text = primary.read_text(encoding="utf-8", errors="replace")
    local_text = local.read_text(encoding="utf-8", errors="replace")
    local_blocks = set(normalized_blocks(local_text))
    duplicates: list[dict[str, Any]] = []
    for block in normalized_blocks(primary_text):
        if block in local_blocks:
            digest = hashlib.sha256(block.encode("utf-8", errors="replace")).hexdigest()[:16]
            duplicates.append({
                "hash": digest,
                "lineCount": len(block.splitlines()),
                "preview": block.splitlines()[0][:120],
                "paths": [".lazy-harness/AGENTS.md", ".jcode/harness/05-lazy-harness.md"],
            })
    duplicates.sort(key=lambda row: (-int(row["lineCount"]), row["hash"]))
    return duplicates[:20]


def build_report(root: pathlib.Path, transition_message_tokens: int) -> dict[str, Any]:
    surfaces = collect_file_surfaces(root)
    rendered = render_message_received(root, transition_message_tokens)
    duplicates = find_duplicate_blocks(root)
    statuses = [str(surface.get("status")) for surface in surfaces] + [str(rendered.get("status", "pass"))]
    if rendered.get("fixtureMessageLeaked"):
        statuses.append("fail")
    status = merge_status(*statuses)
    notes = [
        "Phase 1 is measurement-only; message.received behavior is not changed.",
        "Generated measurements are non-canonical and should be used as regression evidence only.",
        "Skill prompts are measured as on-demand assets; oversized skill prompts are advisory warnings, not hard failures.",
    ]
    if duplicates:
        notes.append("Duplicate grammar blocks detected between .lazy-harness/AGENTS.md and .jcode/harness/05-lazy-harness.md.")
    return {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": str(root),
        "status": status,
        "budgets": DEFAULT_BUDGETS | {"messageReceived": {**DEFAULT_BUDGETS["messageReceived"], "transitionHardMaxTokens": transition_message_tokens}},
        "surfaces": surfaces,
        "duplicates": duplicates,
        "renderedMessageReceived": rendered,
        "notes": notes,
    }


def render_md(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Prompt budget")
    lines.append("")
    lines.append(f"- Status: `{report['status']}`")
    lines.append(f"- Root: `{report['root']}`")
    lines.append(f"- Generated: `{report['generatedAt']}`")
    lines.append("")
    rendered = report.get("renderedMessageReceived", {})
    lines.append("## Rendered message.received")
    lines.append("")
    if rendered.get("present"):
        lines.append(f"- Status: `{rendered.get('status')}`")
        lines.append(f"- Lines: `{rendered.get('lineCount')}`")
        lines.append(f"- Estimated tokens: `{rendered.get('tokenEstimate')}`")
        lines.append(f"- Hard max tokens: `{rendered.get('hardMaxTokens')}`")
        lines.append(f"- Transition hard max tokens: `{rendered.get('transitionHardMaxTokens')}`")
        lines.append(f"- Journal rows written in isolated runtime: `{rendered.get('journalRows')}`")
        lines.append(f"- Body hash: `{rendered.get('bodyHash')}`")
    else:
        lines.append(f"- Status: `{rendered.get('status')}`")
        lines.append(f"- Error: {rendered.get('error')}")
    lines.append("")
    lines.append("## Prompt surfaces")
    lines.append("")
    lines.append("| Surface | Kind | Lines | Est. tokens | Enforcement | Status |")
    lines.append("|---|---|---:|---:|---|---|")
    for surface in report.get("surfaces", []):
        lines.append(f"| `{surface.get('path')}` | {surface.get('kind')} | {surface.get('lineCount')} | {surface.get('tokenEstimate')} | {surface.get('enforcement', 'enforced')} | `{surface.get('status')}` |")
    lines.append("")
    lines.append("## Duplicate grammar hints")
    lines.append("")
    duplicates = report.get("duplicates", [])
    if not duplicates:
        lines.append("- No duplicate blocks detected, or comparison surface missing.")
    else:
        for duplicate in duplicates:
            paths = ", ".join(f"`{path}`" for path in duplicate.get("paths", []))
            lines.append(f"- `{duplicate.get('hash')}` ({duplicate.get('lineCount')} lines) in {paths}: {duplicate.get('preview')}")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    for note in report.get("notes", []):
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = resolve_root(args.root)
    report = build_report(root, args.transition_message_tokens)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_md(report))
    return 1 if report.get("status") == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
