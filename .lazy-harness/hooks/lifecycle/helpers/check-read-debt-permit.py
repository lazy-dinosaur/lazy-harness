#!/usr/bin/env python3
"""Pre-action search/read-debt permit check for direct-search/read-debt rows.

This helper is intentionally protocol-agnostic: it reads sanitized
search/read debt journal evidence and current tool-call evidence, then emits a
plain deny reason only when an action tool is about to run before required
search/read evidence exists.

It does not semantically resolve user intent. LLM/searcher workers do that via
root-bound searches. This helper measures whether the search/read evidence
exists before action.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

try:
    from runtime_paths import runtime_state_path
except Exception:  # pragma: no cover - lifecycle helper must fail open
    runtime_state_path = None  # type: ignore[assignment]

PAYLOAD_RAW = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
try:
    PAYLOAD = json.loads(PAYLOAD_RAW or "{}")
except Exception:
    PAYLOAD = {}
if not isinstance(PAYLOAD, dict):
    raise SystemExit(0)

ROOT = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd()).resolve()
if runtime_state_path is not None:
    PACKET_JOURNAL = runtime_state_path(ROOT, "search-read-debt.jsonl", PAYLOAD)
else:
    PACKET_JOURNAL = Path(os.environ.get("LAZY_RUNTIME_ROOT") or (ROOT / ".lazy-harness" / ".runtime")) / "state" / "search-read-debt.jsonl"
TTL_SECONDS = int(os.environ.get("LAZY_READ_DEBT_TTL_SECONDS", "7200") or "7200")
MIN_CONFIDENCE = float(os.environ.get("LAZY_READ_DEBT_MIN_CONFIDENCE", "0.6") or "0.6")

SEARCH_DEBT_LEVELS = {"harness-first-static", "self-resolve-before-answer", "self-resolve-before-change", "delegate-search"}
DIRECT_SEARCH_EVIDENCE_TOOLS = set()
INVENTORY_EVIDENCE_TOOLS = {
    "read", "Read", "ls", "LS",
    "mcp__filesystem__read_text_file", "mcp__filesystem__read_file", "mcp__filesystem__read_multiple_files",
    "mcp__filesystem__list_directory", "mcp__filesystem__list_directory_with_sizes",
    "mcp__filesystem__directory_tree", "mcp__filesystem__get_file_info",
}

ROOT_BOUND_EVIDENCE_TOOLS = {
    "read", "Read",
    "ls", "LS",
    "mcp__filesystem__read_text_file", "mcp__filesystem__read_file",
    "mcp__filesystem__read_multiple_files", "mcp__filesystem__list_directory",
    "mcp__filesystem__list_directory_with_sizes", "mcp__filesystem__directory_tree",
    "mcp__filesystem__get_file_info",
}

WRITE_TOOLS = {
    "write", "Write", "edit", "Edit", "multiedit", "MultiEdit",
    "patch", "apply_patch", "mcp__filesystem__write_file", "mcp__filesystem__edit_file",
    "mcp__filesystem__create_directory", "mcp__filesystem__move_file",
}

ACTION_TOOLS = {
    *WRITE_TOOLS,
    "bash", "Bash",
    "gmail", "schedule", "open",
}

ACTION_NAME_RE = re.compile(
    r"(?:^|[_:.\-])(write|edit|patch|apply_patch|create|update|delete|remove|send|merge|push|upload|click|type|fill|press|select|drag|drop|navigate|run|close|open|schedule)(?:$|[_:.\-])",
    re.IGNORECASE,
)

LAZY_MAP_COMMAND_RE = re.compile(
    r"(?:^|\s)(?:\.lazy-harness/bin/lazy|(?:^|\s)lazy)\s+map(?:\s|$)"
    r"|(?:^|\s)(?:\.lazy-harness/)?scripts/record-map\.ts(?:\s|$)"
    r"|(?:^|\s)record-map\.ts(?:\s|$)",
    re.IGNORECASE,
)
LAZY_FIND_COMMAND_RE = re.compile(
    r"(?:^|\s)(?:\.lazy-harness/bin/lazy|(?:^|\s)lazy)\s+find(?:\s|$)",
    re.IGNORECASE,
)


READ_ONLY_SHELL_RE = re.compile(
    r"^\s*(?:cd\s+[^;&|]+\s*(?:&&|;)\s*)?"
        r"(?:(?:\.lazy-harness/bin/lazy|lazy)\s+map|pwd|ls|cat|grep|rg|wc|git\s+(?:status|rev-parse))\b",
    re.IGNORECASE | re.DOTALL,
)

ROOT_BOUND_EVIDENCE_RE = re.compile(
    r"(?:\.lazy-harness|\bsrc/|\btests?/|\bdocs/|\bAGENTS\.md\b|\bpackage\.json\b)",
    re.IGNORECASE,
)

GENERIC_READ_SEARCH_NAME_RE = re.compile(
    r"(?:read|tree|list|glob|ls|directory|file|symbol|outline)",
    re.IGNORECASE,
)

DETERMINISTIC_PACKET_RE = re.compile(
    r"\.lazy-harness/scripts/record-index\.ts",
    re.IGNORECASE,
)



def stable_hash(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def call_blob(call: dict[str, Any]) -> str:
    parts: list[str] = []

    def add(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, (dict, list)):
            try:
                parts.append(json.dumps(value, ensure_ascii=False))
            except Exception:
                pass
            if isinstance(value, dict):
                for child in value.values():
                    add(child)
            else:
                for child in value:
                    add(child)
        else:
            parts.append(str(value))

    for key in ("name", "args_preview", "args", "input", "arguments", "command", "body", "path", "file_path"):
        add(call.get(key))
    return "\n".join(parts)


def current_tool() -> tuple[str, dict[str, Any]]:
    raw_tool = PAYLOAD.get("tool")
    tool: dict[str, Any] = raw_tool if isinstance(raw_tool, dict) else {}
    name = str(tool.get("name") or PAYLOAD.get("tool_name") or PAYLOAD.get("toolName") or PAYLOAD.get("name") or "")
    raw_args = tool.get("args")
    args: dict[str, Any] = raw_args if isinstance(raw_args, dict) else {}
    payload_args = PAYLOAD.get("args")
    if not args and isinstance(payload_args, dict):
        args = payload_args
    return name, args


def nested_tool_calls(args: dict[str, Any]) -> list[dict[str, Any]]:
    calls = args.get("tool_calls") or args.get("toolCalls") or args.get("tool_uses") or []
    return [c for c in calls if isinstance(c, dict)] if isinstance(calls, list) else []


def bash_is_read_only(args: dict[str, Any]) -> bool:
    command = str(args.get("command") or args.get("cmd") or "").strip()
    if not command:
        return False
    body = command
    if re.match(r"^cd\s+", command, re.IGNORECASE):
        match = re.match(r"^cd\s+(.+?)\s*&&\s*(.+)$", command, re.IGNORECASE | re.DOTALL)
        if not match or re.search(r"[<>&|;$()`\n]", match.group(1) or ""):
            return False
        body = match.group(2) or ""
    normalized_flags = re.sub(r"\\(.)", r"\1", body).replace("'", "").replace('"', "")
    if re.search(r"[;&<>]|\|\||\$|`|\n", body) or re.search(r"(?:^|\s)--pre(?:=|\s)", normalized_flags, re.IGNORECASE):
        return False
    forbidden = re.search(r"\b(rm|mv|cp|mkdir|touch|tee|python3?\s+-|node\s+-|bun\s+(?:run|x|test)|npm|pnpm|yarn|gh\s+(?:pr\s+(?:create|edit|merge)|issue\s+create))\b", body, re.IGNORECASE)
    if forbidden:
        return False
    first, *filters = (part.strip() for part in body.split("|"))
    if not first or not READ_ONLY_SHELL_RE.search(first):
        return False
    return all(re.match(r"^(?:head|tail|wc)(?:\s|$)", part, re.IGNORECASE) for part in filters)


def is_owned_reader_status_inspection(name: str, args: dict[str, Any]) -> bool:
    if name.lower() != "subagent" or str(args.get("action") or "") != "status":
        return False
    if any(key not in {"action", "id", "includeProgress", "view", "lines"} for key in args):
        return False
    if "includeProgress" in args and not isinstance(args["includeProgress"], bool):
        return False
    if "view" in args and args["view"] != "transcript":
        return False
    if "lines" in args and (not isinstance(args["lines"], int) or isinstance(args["lines"], bool) or args["lines"] <= 0 or args["lines"] > 500):
        return False
    context = PAYLOAD.get("reader_status_inspection")
    if not isinstance(context, dict):
        return False
    evidence_epoch = context.get("evidenceEpoch")
    current_epoch = context.get("currentEpoch")
    if (
        not isinstance(evidence_epoch, int)
        or isinstance(evidence_epoch, bool)
        or not isinstance(current_epoch, int)
        or isinstance(current_epoch, bool)
    ):
        return False
    return (
        context.get("pending") is True
        and evidence_epoch >= 0 and current_epoch >= 0
        and str(context.get("root") or "") == str(ROOT)
        and isinstance(context.get("runId"), str) and bool(context.get("runId"))
        and str(args.get("id") or "") == str(context.get("runId"))
        and evidence_epoch == current_epoch
    )


def is_action_tool(name: str, args: dict[str, Any]) -> bool:
    if not name:
        return False
    lower = name.lower()
    leaf = re.split(r"[.:]", lower)[-1]
    if name in ROOT_BOUND_EVIDENCE_TOOLS:
        return False
    if name in {"batch", "multi_tool_use.parallel"}:
        nested = nested_tool_calls(args)
        if not nested:
            return False
        def nested_args(call: dict[str, Any]) -> dict[str, Any]:
            for key in ("parameters", "input", "args"):
                value = call.get(key)
                if isinstance(value, dict):
                    return value
            return {}
        return any(is_action_tool(str(c.get("recipient_name") or c.get("tool") or c.get("name") or c.get("toolName") or ""), nested_args(c)) for c in nested)
    if leaf in {"bash", "cmd", "command", "shell", "terminal"}:
        return not bash_is_read_only(args)
    if name.lower() == "subagent" and str(args.get("action") or "") == "status":
        return not is_owned_reader_status_inspection(name, args)
    if name in {"subagent", "swarm"} and "action" in args:
        return args.get("action") != "list"
    if name in {"subagent", "swarm"} and (
        str(args.get("action") or "") == "list"
        or is_search_handoff_args(args)
        or is_owned_reader_status_inspection(name, args)
    ):
        return False
    if name in ACTION_TOOLS:
        return True
    if name in {"subagent", "swarm"}:
        return True
    if ACTION_NAME_RE.search(name):
        return True
    if name.startswith("mcp__"):
        return True
    return False


def is_search_handoff_args(args: dict[str, Any]) -> bool:
    blob = json.dumps(args, ensure_ascii=False).lower()
    return any(marker in blob for marker in (
        "searcher", "librarian", "explore", "atlas",
        "lazy-harness.record-reader", "record-reader/reader-join-v1",
        "root-bound search", "requiredread",
        "do not mutate", "read-only", "search-debt",
    ))


def payload_recent_calls() -> list[dict[str, Any]]:
    calls = PAYLOAD.get("recent_tool_calls") or PAYLOAD.get("recentToolCalls") or []
    return [c for c in calls if isinstance(c, dict)] if isinstance(calls, list) else []


def recent_calls(packet_row: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    calls = payload_recent_calls()
    for index in range(len(calls) - 1, -1, -1):
        call = calls[index]
        name = str(call.get("name") or call.get("tool") or "")
        if name != "lazy_reader_join":
            continue
        raw_args = call.get("args")
        args: dict[str, Any] = raw_args if isinstance(raw_args, dict) else {}
        if bool(call.get("is_error")) or str(args.get("status") or "") != "complete":
            return calls[index + 1:]
        break
    return calls


def load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict):
                rows.append(row)
    except Exception:
        return []
    return rows[-200:]


def matching_packet() -> dict[str, Any] | None:
    msg_hash = stable_hash(PAYLOAD.get("message_id") or PAYLOAD.get("messageId"))
    session_hash = stable_hash(PAYLOAD.get("session_id") or PAYLOAD.get("sessionId"))
    if not msg_hash and not session_hash:
        return None
    now = time.time()
    for row in reversed(load_rows(PACKET_JOURNAL)):
        try:
            ts = float(row.get("epochSeconds") or 0)
        except Exception:
            ts = 0
        if ts > 0 and now - ts > TTL_SECONDS:
            continue
        row_msg = row.get("messageIdHash")
        row_session = row.get("sessionIdHash")
        if msg_hash:
            if row_msg != msg_hash:
                continue
            if session_hash and row_session != session_hash:
                continue
            return row
        if session_hash and row_session == session_hash:
            return row
    return None


def required_items(row: dict[str, Any]) -> list[dict[str, Any]]:
    items = row.get("requiredRead") or []
    if not isinstance(items, list):
        return []
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        if path.startswith("./"):
            path = path[2:]
        if path:
            copied = dict(item)
            copied["path"] = path
            out.append(copied)
    return out


def evidence_blob(packet_row: dict[str, Any] | None = None) -> str:
    return "\n".join(call_blob(call) for call in recent_calls(packet_row)).replace("\\", "/")


def shell_has_search_evidence(command: str) -> bool:
    if DETERMINISTIC_PACKET_RE.search(command) or LAZY_FIND_COMMAND_RE.search(command):
        return False
    if LAZY_MAP_COMMAND_RE.search(command):
        return True
    return bool(READ_ONLY_SHELL_RE.search(command) and re.search(r"\.lazy-harness(?:/|\b)", command))


def call_has_search_evidence(call: dict[str, Any]) -> bool:
    name = str(call.get("name") or call.get("tool") or "")
    leaf = re.split(r"[.:]", name.lower())[-1]
    blob = call_blob(call)
    if DETERMINISTIC_PACKET_RE.search(blob) or LAZY_FIND_COMMAND_RE.search(blob):
        return False
    if leaf == "lazy_reader_join":
        return (
            not bool(call.get("is_error"))
            and '"status":"complete"' in blob.replace(" ", "")
            and "LAZY_HARNESS_READER_RESULT: complete" in blob
        )
    if name in DIRECT_SEARCH_EVIDENCE_TOOLS:
        return True
    if name in INVENTORY_EVIDENCE_TOOLS and ROOT_BOUND_EVIDENCE_RE.search(blob):
        return True
    if leaf == "bash" and shell_has_search_evidence(blob):
        return True
    if name in {"subagent", "swarm"} and is_search_handoff_args(call):
        return False
    # Generic fallback: this is an evidence detector, not a project/tool policy.
    # Count root-bound inventory/read-style signals only; keyword search tools do
    # not satisfy map-first evidence debt.
    if ROOT_BOUND_EVIDENCE_RE.search(blob) and GENERIC_READ_SEARCH_NAME_RE.search(name):
        return True
    if ROOT_BOUND_EVIDENCE_RE.search(blob) and re.search(r"(?:^|\s)(?:tree|ls|cat)\s+\.lazy-harness\b|(?:^|\s)read\s+", blob, re.IGNORECASE):
        return True
    return False


def has_search_evidence(packet_row: dict[str, Any] | None = None) -> bool:
    return any(call_has_search_evidence(call) for call in recent_calls(packet_row))


def missing_required_paths(items: list[dict[str, Any]], packet_row: dict[str, Any] | None = None) -> list[str]:
    blob = evidence_blob(packet_row)
    missing: list[str] = []
    for item in items:
        path = str(item.get("path") or "").strip()
        if path.startswith("./"):
            path = path[2:]
        if not path:
            continue
        if path not in blob and f"./{path}" not in blob:
            missing.append(path)
    return missing


def is_search_debt(row: dict[str, Any], items: list[dict[str, Any]]) -> bool:
    if items:
        return False
    level = str(row.get("instructionLevel") or "")
    try:
        fallback_count = int(row.get("fallbackSearchCount") or 0)
    except Exception:
        fallback_count = 0
    if level not in SEARCH_DEBT_LEVELS:
        return False
    return fallback_count > 0 or level == "delegate-search"


def main() -> int:
    name, args = current_tool()
    if not is_action_tool(name, args):
        return 0
    row = matching_packet()
    if not row:
        return 0
    items = required_items(row)
    if is_search_debt(row, items):
        if has_search_evidence(row):
            return 0
        print("[lazy-harness search-debt gate] map-first traversal/read evidence must happen before action.")
        print("")
        print("This turn requires either a content-bearing dedicated Reader join or direct LLM/searcher map-first evidence before action; keyword grep/rg/find search is not enough.")
        print("The guard checks for evidence that the harness was followed; it is not a project/tool allowlist.")
        print("")
        print("Do this first:")
        print("  - preferred: launch `lazy-harness.record-reader`, consume its result packet, then close `lazy_reader_join`")
        print("  - fallback, new scope: run `.lazy-harness/bin/lazy map --overview --complete --format=md`")
        print("  - fallback, re-grounding a work unit already grounded this session (cheaper): drill the exact governing record path or feature id, e.g. `.lazy-harness/bin/lazy map .lazy-harness/<layer>/<record>.md --format=md`")
        print("  - drill one concrete node from that map and read canonical records/files before rerunning the action")
        print("")
        print("Allowed now: lazy map traversal, root-bound inventory/list/read, and concrete record/source/test reads. Action/mutation tools stay blocked until evidence exists.")
        return 0
    try:
        confidence = float(row.get("confidence") or 0)
    except Exception:
        confidence = 0
    if confidence < MIN_CONFIDENCE:
        return 0
    if not items:
        return 0
    missing = missing_required_paths(items, row)
    if not missing:
        return 0

    print("[lazy-harness read-debt gate] requiredRead must be inspected before action.")
    print("")
    print("A search/read-debt row produced concrete requiredRead entries for this turn, but current tool evidence does not show they were read/searched yet.")
    print("")
    print("Do this first:")
    for path in missing[:6]:
        print(f"  - read/search `{path}`")
    print("")
    print("Allowed now: read, grep/agentgrep, ls/glob, and read-only shell searches. After evidence exists, rerun the action tool.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
