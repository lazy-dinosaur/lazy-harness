#!/usr/bin/env python3
"""Policy Machinery warn-only response.completed helper.

This helper is deliberately conservative:
- it never classifies raw user/assistant text,
- it only reads explicit `policy_context` / `policyContext` payload fields,
- it emits WARN guidance only, never blocking-gate output,
- acknowledged warnings remain silent.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
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
LAZY = ROOT / ".lazy-harness"
LAZY_BIN = LAZY / "bin" / "lazy"


def policy_context() -> dict[str, Any]:
    value = PAYLOAD.get("policy_context") or PAYLOAD.get("policyContext") or {}
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def acknowledged_ids(ctx: dict[str, Any]) -> set[str]:
    ids = as_list(ctx.get("acknowledgedPolicyWarnings") or ctx.get("acknowledged_policy_warnings"))
    return set(ids)


def resolve(stage: str, applies_to: list[str]) -> dict[str, Any] | None:
    if not LAZY_BIN.exists():
        return None
    cmd = [str(LAZY_BIN), "policy", "resolve", "--runtime", "warn", "--format=json"]
    if stage:
        cmd.extend(["--stage", stage])
    if applies_to:
        cmd.extend(["--applies-to", ",".join(applies_to)])
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "LAZY_HOST_ROOT": str(ROOT)},
    )
    if completed.returncode != 0:
        return None
    try:
        data = json.loads(completed.stdout or "{}")
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def main() -> None:
    ctx = policy_context()
    if not ctx:
        return
    stage = str(ctx.get("stage") or "").strip()
    applies_to = as_list(ctx.get("appliesTo") or ctx.get("applies_to"))
    if not stage and not applies_to:
        return
    acknowledged = acknowledged_ids(ctx)
    data = resolve(stage, applies_to)
    if not data or data.get("enforcement") != "warn-only":
        return
    matches = [m for m in data.get("matches", []) if isinstance(m, dict) and m.get("enforcement") == "warn-only"]
    matches = [m for m in matches if str(m.get("id") or "") not in acknowledged]
    if not matches:
        return
    lines = [
        "WARN. Policy Machinery warn-only runtime: structured policy context matched warn-level behavior policy.",
        "This is guidance only, not a block. You may continue, but include validation evidence or a short bypass reason.",
        "",
        "Matched policies:",
    ]
    for match in matches[:5]:
        pid = str(match.get("id") or "<unknown>")
        summary = str(match.get("summary") or match.get("title") or "")
        source = str(match.get("sourceRecord") or "")
        lines.append(f"- {pid}: {summary}")
        if source:
            lines.append(f"  source: {source}")
    lines.extend([
        "",
        "Bypass/acknowledge: add policy_context.acknowledgedPolicyWarnings with the policy id after deciding to proceed.",
    ])
    print("\n".join(lines))


if __name__ == "__main__":
    main()
