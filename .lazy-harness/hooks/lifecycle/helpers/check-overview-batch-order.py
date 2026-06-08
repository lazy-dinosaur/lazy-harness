#!/usr/bin/env python3
"""Deny batching `lazy map --overview` with dependent calls.

This helper is intentionally not a semantic classifier. It only inspects the
current tool-call shape. `lazy map --overview` is the required first inventory
step; putting it inside `batch`/`multi_tool_use.parallel` with query/read calls
means the later calls were chosen before the overview evidence was available.
"""
from __future__ import annotations

import json
import re
import sys
from typing import Any

PAYLOAD_RAW = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
try:
    PAYLOAD = json.loads(PAYLOAD_RAW or "{}")
except Exception:
    raise SystemExit(0)
if not isinstance(PAYLOAD, dict):
    raise SystemExit(0)

OVERVIEW_RE = re.compile(r"(?:^|[\s;|&])(?:\.lazy-harness/bin/lazy|lazy)\s+map\s+--overview\b", re.IGNORECASE)
BATCH_TOOL_NAMES = {"batch", "functions.batch", "multi_tool_use.parallel", "parallel"}


def flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "\n".join(flatten(item) for item in value)
    if isinstance(value, dict):
        parts: list[str] = []
        for key, child in value.items():
            parts.append(str(key))
            parts.append(flatten(child))
        return "\n".join(parts)
    return str(value)


def child_calls(args: dict[str, Any]) -> list[Any]:
    calls = args.get("tool_calls")
    if isinstance(calls, list):
        return calls
    calls = args.get("tool_uses")
    if isinstance(calls, list):
        return calls
    return []


tool = PAYLOAD.get("tool")
if not isinstance(tool, dict):
    raise SystemExit(0)
name = str(tool.get("name") or "")
args = tool.get("args")
if not isinstance(args, dict):
    raise SystemExit(0)

if name not in BATCH_TOOL_NAMES and not name.endswith(".batch") and not name.endswith(".parallel"):
    raise SystemExit(0)

calls = child_calls(args)
if not calls:
    raise SystemExit(0)

if any(OVERVIEW_RE.search(flatten(call)) for call in calls):
    print(
        "STOP. Overview-first batch guard: `lazy map --overview` must be a standalone, sequential tool call before dependent query/read calls.\n\n"
        "Do not put overview inside `batch` or `multi_tool_use.parallel`. Run it first, inspect the output, then use separate follow-up `lazy map <token>`/read calls. Independent reads chosen after the overview may still be batched."
    )
    raise SystemExit(1)

raise SystemExit(0)
