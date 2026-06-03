#!/usr/bin/env python3
"""response.completed shadow bridge for Record Decision Packet.

This helper is intentionally conservative:
- it always exits 0,
- writes sanitized non-canonical shadow journal rows,
- emits no stdout by default,
- only emits ADVISORY when LAZY_RECORD_DECISION_SHADOW_ADVISORY=1.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PAYLOAD_RAW = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    PAYLOAD = json.loads(PAYLOAD_RAW or "{}")
except Exception:
    PAYLOAD = {}
if not isinstance(PAYLOAD, dict):
    raise SystemExit(0)

ROOT = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd()).resolve()
GENERATOR = ROOT / ".lazy-harness" / "scripts" / "record-decision-broker.ts"
JOURNAL = ROOT / ".lazy-harness" / "state" / "record-decision-packets.jsonl"
ADVISORY_ENABLED = os.environ.get("LAZY_RECORD_DECISION_SHADOW_ADVISORY", "0") == "1"

WRITE_TOOLS = {
    "Write", "Edit", "MultiEdit", "write", "edit", "multiedit",
    "mcp__filesystem__write_file", "mcp__filesystem__edit_file",
    "apply_patch", "patch",
}
READ_TOOLS = {
    "read", "Read", "grep", "Grep", "agentgrep", "glob", "Glob", "ls", "LS",
    "webfetch", "websearch", "mcp__filesystem__read_text_file", "mcp__filesystem__read_file",
    "mcp__filesystem__read_multiple_files", "mcp__filesystem__list_directory",
    "mcp__filesystem__list_directory_with_sizes", "mcp__filesystem__directory_tree",
    "mcp__filesystem__search_files", "mcp__filesystem__get_file_info",
}
RECORD_RE = re.compile(r"\.lazy-harness/(?:domain|spec|behavior|tests|decisions|ssot|planning|plans|knowledge)/[^\s\"'`,)}]+")
SOURCE_PATH_RE = re.compile(r"(?:(?:src|packages|app|components|lib|server|tests|test|__tests__)/[^\s\"'`,)}]+|[^\s\"'`,)}]+\.(?:ts|tsx|js|jsx|py|rs|go|java|kt|swift|md|json|xml|yml|yaml))")
VALIDATION_RE = re.compile(r"\b(?:lazy test|self-test|doctor|pytest|vitest|npm test|bun test|cargo test|validation|검증|테스트)\b", re.IGNORECASE)


def stable_hash(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def compact(value: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def recent_calls() -> list[dict[str, Any]]:
    calls = PAYLOAD.get("recent_tool_calls") or PAYLOAD.get("recentToolCalls") or []
    return [c for c in calls if isinstance(c, dict)] if isinstance(calls, list) else []


def call_blob(call: dict[str, Any]) -> str:
    parts: list[str] = []

    def append(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, dict):
            for child in value.values():
                append(child)
            try:
                parts.append(json.dumps(value, ensure_ascii=False))
            except Exception:
                pass
        elif isinstance(value, list):
            for child in value:
                append(child)
            try:
                parts.append(json.dumps(value, ensure_ascii=False))
            except Exception:
                pass
        else:
            parts.append(str(value))

    for key in ("name", "args_preview", "args", "input", "arguments", "command", "body", "title", "path", "file_path", "patch_text"):
        append(call.get(key))
    return "\n".join(parts)


def normalize_path(candidate: str) -> str:
    text = candidate.strip().strip('"\'`,;')
    if not text:
        return text
    if text.startswith("./"):
        text = text[2:]
    return text.replace("\\", "/")


def extract_paths(blob: str) -> tuple[list[str], list[str], list[str]]:
    records: list[str] = []
    tests: list[str] = []
    files: list[str] = []
    for match in RECORD_RE.findall(blob):
        records.append(normalize_path(match))
    for match in SOURCE_PATH_RE.findall(blob):
        path = normalize_path(match)
        if not path or path.startswith(".lazy-harness/"):
            continue
        if re.search(r"(?:^|/)(?:tests?|__tests__)/|\.(?:test|spec)\.", path):
            tests.append(path)
        else:
            files.append(path)
    return unique(files)[:12], unique(records)[:12], unique(tests)[:12]


def unique(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            out.append(value)
            seen.add(value)
    return out


def build_generator_args() -> list[str]:
    calls = recent_calls()
    names = [str(c.get("name") or "") for c in calls]
    write_calls = [c for c in calls if str(c.get("name") or "") in WRITE_TOOLS]
    read_only = bool(calls) and not write_calls and all(name in READ_TOOLS for name in names)
    args = ["--message", "response.completed shadow"]

    all_changed_files: list[str] = []
    all_changed_records: list[str] = []
    all_changed_tests: list[str] = []
    all_required_reads: list[str] = []
    validation_seen = False
    for call in calls:
        name = str(call.get("name") or "")
        blob = call_blob(call)
        if name in write_calls_names():
            files, records, tests = extract_paths(blob)
            all_changed_files.extend(files)
            all_changed_records.extend(records)
            all_changed_tests.extend(tests)
        elif name in READ_TOOLS:
            files, records, tests = extract_paths(blob)
            all_required_reads.extend(records)
            all_required_reads.extend(files)
            all_required_reads.extend(tests)
        if VALIDATION_RE.search(blob):
            validation_seen = True
        if name:
            args.extend(["--tool-call", name])

    for path in unique(all_changed_files):
        args.extend(["--changed-file", path])
    for path in unique(all_changed_records):
        args.extend(["--changed-record", path])
    for path in unique(all_changed_tests):
        args.extend(["--changed-test", path])
    for path in unique(all_required_reads):
        args.extend(["--required-read", path])

    if validation_seen:
        args.extend(["--validation", "response.completed validation evidence"])
    if read_only:
        args.append("--read-only")
    if not calls:
        args.append("--no-record-needed")
    if not write_calls and (validation_seen or not all_changed_files):
        args.append("--validation-only" if validation_seen else "--read-only")
    return args


def write_calls_names() -> set[str]:
    return WRITE_TOOLS


def run_generator(args: list[str]) -> dict[str, Any] | None:
    if not GENERATOR.exists():
        return None
    try:
        completed = subprocess.run(
            ["bun", str(GENERATOR), *args, "--format=json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=float(os.environ.get("LAZY_RECORD_DECISION_SHADOW_TIMEOUT_SECONDS", "5")),
            check=False,
        )
    except Exception:
        return None
    if completed.returncode != 0:
        return None
    try:
        parsed = json.loads(completed.stdout)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def sanitize_packet(packet: dict[str, Any]) -> dict[str, Any]:
    decision = packet.get("recordDecision") if isinstance(packet.get("recordDecision"), dict) else {}
    evidence = []
    for item in decision.get("evidence") or []:
        if not isinstance(item, dict):
            continue
        evidence.append({
            "kind": item.get("kind"),
            "path": item.get("path"),
            "toolName": item.get("toolName"),
            "confidence": item.get("confidence"),
        })
    recommended = []
    for item in decision.get("recommendedRecords") or []:
        if not isinstance(item, dict):
            continue
        recommended.append({
            "path": item.get("path"),
            "layer": item.get("layer"),
            "action": item.get("action"),
            "confidence": item.get("confidence"),
        })
    return {
        "schemaVersion": "1.0",
        "event": "record-decision.shadow",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "epochSeconds": int(time.time()),
        "messageIdHash": stable_hash(PAYLOAD.get("message_id") or PAYLOAD.get("messageId")),
        "sessionIdHash": stable_hash(PAYLOAD.get("session_id") or PAYLOAD.get("sessionId")),
        "packetHash": stable_hash(json.dumps(packet, ensure_ascii=False, sort_keys=True)),
        "disposition": decision.get("disposition"),
        "trigger": decision.get("trigger"),
        "confidence": decision.get("confidence"),
        "evidence": evidence[:20],
        "recommendedRecords": recommended[:20],
        "notes": ["shadow=true", "advisoryDefault=false", "mutationAllowed=false"],
    }


def append_journal(row: dict[str, Any]) -> None:
    try:
        JOURNAL.parent.mkdir(parents=True, exist_ok=True)
        existing: list[str] = []
        if JOURNAL.exists():
            existing = [line for line in JOURNAL.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()][-199:]
        existing.append(json.dumps(row, ensure_ascii=False, sort_keys=True))
        JOURNAL.write_text("\n".join(existing) + "\n", encoding="utf-8")
    except Exception:
        pass


def advisory_text(row: dict[str, Any]) -> str:
    if not ADVISORY_ENABLED:
        return ""
    disposition = str(row.get("disposition") or "")
    if disposition not in {"candidate-needed", "option-gate-needed"}:
        return ""
    if disposition == "candidate-needed":
        title = "ADVISORY. Record Decision shadow: candidate record capture may be needed."
        problem = "문제: shadow RecordDecisionPacket이 candidate-needed를 산출했습니다. 이는 기록 후보가 있을 수 있다는 관측이며 차단이 아닙니다."
    else:
        title = "ADVISORY. Record Decision shadow: option gate may be needed."
        problem = "문제: shadow RecordDecisionPacket이 option-gate-needed를 산출했습니다. layer/path/meaning이 애매할 수 있다는 관측이며 차단이 아닙니다."
    lines = [title, "", problem, "", "추천 확인:"]
    for rec in row.get("recommendedRecords") or []:
        if not isinstance(rec, dict):
            continue
        action = rec.get("action") or "candidate"
        path = rec.get("path") or "(no path)"
        layer = f" [{rec.get('layer')}]" if rec.get("layer") else ""
        lines.append(f"  - {action}: {path}{layer}")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    packet = run_generator(build_generator_args())
    if not packet:
        return 0
    row = sanitize_packet(packet)
    append_journal(row)
    text = advisory_text(row)
    if text:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
