#!/usr/bin/env python3
"""Safe lifecycle payload fixture intake.

Captures response.completed payload *shape* for Phase 3 readiness without storing
raw user/assistant content. Candidates are used to widen lifecycle parity
coverage by tool/category metadata.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd()).resolve()
CANDIDATES = ROOT / ".lazy-harness" / "fixtures" / "lifecycle" / "real-payload-candidates.jsonl"

READ_ONLY_TOOLS = {
    "read", "Read", "grep", "Grep", "agentgrep", "glob", "Glob", "ls", "LS",
    "webfetch", "websearch",
    "mcp__filesystem__read_text_file", "mcp__filesystem__read_file", "mcp__filesystem__read_multiple_files",
    "mcp__filesystem__list_directory", "mcp__filesystem__list_directory_with_sizes", "mcp__filesystem__directory_tree",
    "mcp__filesystem__search_files", "mcp__filesystem__get_file_info",
}

SIGNALS = {
    "rulePlacement": re.compile(r"Rule placement|##\s*Rule placement", re.I),
    "optionGate": re.compile(r"needs-option-gate|선택해주세요|\bA\.\s", re.I),
    "sessionSearch": re.compile(r"session_search", re.I),
    "lazyCli": re.compile(r"lazy\s+(test|doctor|capability|gate-state|record-audit|lifecycle)", re.I),
    "implementationMap": re.compile(r"Implementation map", re.I),
}

PATH_PATTERN = re.compile(r"(?:^|\s)(\.lazy-harness/[A-Za-z0-9_./:-]+|[A-Za-z0-9_./:-]+\.(?:ts|tsx|js|jsx|py|md|json|jsonl|xml|sh))(?:\s|$)")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_payload(raw: str) -> tuple[dict[str, Any], bool, str | None]:
    try:
        payload = json.loads(raw or "{}")
    except Exception as exc:
        return {}, False, str(exc)
    if not isinstance(payload, dict):
        return {}, False, "payload-not-object"
    return payload, True, None


def sanitize_preview(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    hits = []
    for match in PATH_PATTERN.finditer(value):
        token = match.group(1)
        if token.startswith("/"):
            continue
        hits.append(token)
    if hits:
        return "paths:" + ",".join(sorted(set(hits))[:5])
    lowered = value.lower()
    if "git " in lowered:
        return "command:git"
    if "gh " in lowered:
        return "command:gh"
    if "lazy " in lowered or ".lazy-harness/bin/lazy" in lowered:
        return "command:lazy"
    return f"redacted:{len(value)}:{sha(value)}"


def sanitize_tool_call(call: Any) -> dict[str, Any]:
    if not isinstance(call, dict):
        return {"name": "__non_object__", "args_preview": ""}
    name = str(call.get("name") or call.get("tool") or "")
    preview = call.get("args_preview")
    if preview is None:
        preview = call.get("args") or call.get("input") or ""
    if not isinstance(preview, str):
        try:
            preview = json.dumps(preview, sort_keys=True, ensure_ascii=False)
        except Exception:
            preview = str(type(preview).__name__)
    return {"name": name, "args_preview": sanitize_preview(preview)}


def text_signals(text: Any) -> dict[str, Any]:
    if not isinstance(text, str):
        return {"present": False}
    return {
        "present": True,
        "length": len(text),
        "sha256_16": sha(text),
        "signals": {name: bool(pattern.search(text)) for name, pattern in SIGNALS.items()},
    }


def classify(payload: dict[str, Any], parsed_ok: bool) -> str:
    if not parsed_ok:
        return "invalid-json"
    calls = payload.get("recent_tool_calls")
    if not isinstance(calls, list):
        return "missing-tool-calls"
    names = [str(call.get("name") or "") for call in calls if isinstance(call, dict)]
    if names and all(name in READ_ONLY_TOOLS for name in names):
        return "read-only"
    if any(name in {"write", "Write", "edit", "Edit", "multiedit", "MultiEdit", "bash"} for name in names):
        return "mutating-or-shell"
    return "mixed-or-unknown"


def intake(raw: str, name: str | None = None, source: str | None = None) -> dict[str, Any]:
    payload, parsed_ok, parse_error = parse_payload(raw)
    calls = payload.get("recent_tool_calls") if isinstance(payload.get("recent_tool_calls"), list) else []
    sanitized_calls = [sanitize_tool_call(call) for call in calls]
    assistant = text_signals(payload.get("assistant_response"))
    user = text_signals(payload.get("last_user_message"))
    category = classify(payload, parsed_ok)
    digest = sha(json.dumps({"category": category, "calls": sanitized_calls, "assistant": assistant.get("signals"), "user": user.get("present")}, sort_keys=True, ensure_ascii=False))
    fixture_name = name or f"real-{category}-{digest}"
    sanitized_payload: dict[str, Any] = {
        "message_id": f"intake-{digest}",
        "recent_tool_calls": sanitized_calls,
    }
    # Never store raw assistant/user text. For parity, only include synthetic signal text
    # when the category can be represented without user content.
    signals = assistant.get("signals") if isinstance(assistant.get("signals"), dict) else {}
    if signals.get("lazyCli"):
        sanitized_payload["assistant_response"] = "Run lazy test via .lazy-harness/bin/lazy test"
    elif signals.get("rulePlacement"):
        sanitized_payload["assistant_response"] = "## Rule placement\n- Rule: fixture\n- Scope: transient-plan\n- Confirmation: validation evidence"
    return {
        "schemaVersion": "1.0",
        "id": f"lifecycle-intake-{digest}",
        "name": fixture_name,
        "capturedAt": now_iso(),
        "source": source or "manual-intake",
        "category": category,
        "parsedOk": parsed_ok,
        "parseError": parse_error,
        "contentPolicy": "raw user/assistant text omitted; hashes and boolean signals only",
        "assistantResponse": assistant,
        "lastUserMessage": user,
        "toolNames": [call.get("name") for call in sanitized_calls],
        "sanitizedPayload": sanitized_payload,
        "expectOutput": None,
    }


def append_candidate(path: Path, row: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict[str, Any]] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                existing.append(obj)
    existing = [obj for obj in existing if obj.get("id") != row.get("id")]
    existing.append(row)
    path.write_text("\n".join(json.dumps(obj, ensure_ascii=False, sort_keys=True) for obj in existing) + "\n", encoding="utf-8")
    return str(path)


def read_candidates(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def print_md(rows: list[dict[str, Any]]) -> None:
    print("# Lifecycle fixture candidates")
    print(f"- count: {len(rows)}")
    for row in rows:
        print(f"\n## {row.get('name')}")
        print(f"- id: {row.get('id')}")
        print(f"- category: {row.get('category')}")
        print(f"- source: {row.get('source')}")
        print(f"- toolNames: {', '.join(str(x) for x in row.get('toolNames', []))}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe lifecycle real payload fixture intake")
    parser.add_argument("command", choices=["inspect", "append", "list"])
    parser.add_argument("--payload", help="payload JSON string; defaults to stdin for inspect/append")
    parser.add_argument("--name", help="fixture candidate name")
    parser.add_argument("--source", default="manual-intake", help="evidence source label")
    parser.add_argument("--file", default=str(CANDIDATES), help="candidate JSONL file")
    parser.add_argument("--format", choices=["json", "md", "markdown"], default="json")
    args = parser.parse_args()
    path = Path(args.file).resolve()
    fmt = "md" if args.format == "markdown" else args.format
    if args.command == "list":
        rows = read_candidates(path)
        if fmt == "json":
            print(json.dumps({"ok": True, "path": str(path), "count": len(rows), "candidates": rows}, ensure_ascii=False, indent=2))
        else:
            print_md(rows)
        return 0
    raw = args.payload if args.payload is not None else sys.stdin.read()
    row = intake(raw, args.name, args.source)
    if args.command == "append":
        written = append_candidate(path, row)
        row = {**row, "writtenTo": written}
    if fmt == "json":
        print(json.dumps({"ok": True, "candidate": row}, ensure_ascii=False, indent=2))
    else:
        print_md([row])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
