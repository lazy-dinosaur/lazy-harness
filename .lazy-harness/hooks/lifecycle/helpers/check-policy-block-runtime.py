#!/usr/bin/env python3
"""Policy Machinery block-runtime dry-run helper.

This helper is deliberately conservative:
- it never classifies raw user/assistant text,
- it only reads explicit `policy_context` / `policyContext` payload fields,
- it only runs when policy_context.blockRuntimeDryRun is true,
- it emits DRY-RUN STOP/ALLOW/BYPASS review output only,
- it never installs hooks, mutates lifecycle state, or exits nonzero to block work.
"""
from __future__ import annotations

import json
import os
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
POLICIES_PATH = ROOT / ".lazy-harness" / "ssot" / "policies.json"


def policy_context() -> dict[str, Any]:
    value = PAYLOAD.get("policy_context") or PAYLOAD.get("policyContext") or {}
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def acknowledged_ids(ctx: dict[str, Any]) -> set[str]:
    ids = as_list(ctx.get("acknowledgedPolicyBlocks") or ctx.get("acknowledged_policy_blocks"))
    return set(ids)


def validation_evidence(ctx: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("validationEvidence", "validation_evidence", "evidenceCapsules", "evidence_capsules", "validationOutputs", "validation_outputs"):
        values.extend(as_list(ctx.get(key)))
    summary = ctx.get("validationEvidenceSummary") or ctx.get("validation_evidence_summary")
    if isinstance(summary, str) and summary.strip():
        values.append(summary.strip())
    return values


def bypass_reason(ctx: dict[str, Any]) -> str:
    value = ctx.get("policyBlockBypassReason") or ctx.get("policy_block_bypass_reason") or ctx.get("blockBypassReason") or ctx.get("block_bypass_reason")
    return str(value).strip() if isinstance(value, str) else ""


def load_policies() -> list[dict[str, Any]]:
    try:
        data = json.loads(POLICIES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    policies = data.get("policies") if isinstance(data, dict) else []
    return [policy for policy in policies if isinstance(policy, dict)] if isinstance(policies, list) else []


def matching_block_policies(stage: str, applies_to: list[str]) -> list[dict[str, Any]]:
    applies = set(applies_to)
    out: list[dict[str, Any]] = []
    for policy in load_policies():
        if policy.get("level") != "block":
            continue
        runtime = policy.get("runtime") if isinstance(policy.get("runtime"), dict) else {}
        if runtime.get("blocks") is not True or runtime.get("requiresExplicitContext") is not True:
            continue
        if stage and str(policy.get("stage") or "") != stage:
            continue
        policy_applies = {str(item) for item in policy.get("appliesTo", []) if str(item)} if isinstance(policy.get("appliesTo"), list) else set()
        if applies and not policy_applies.intersection(applies):
            continue
        out.append(policy)
    return out


def main() -> None:
    ctx = policy_context()
    if not ctx:
        return
    if not as_bool(ctx.get("blockRuntimeDryRun") or ctx.get("block_runtime_dry_run")):
        return
    stage = str(ctx.get("stage") or "").strip()
    applies_to = as_list(ctx.get("appliesTo") or ctx.get("applies_to"))
    if not stage and not applies_to:
        return
    matches = matching_block_policies(stage, applies_to)
    if not matches:
        return

    acknowledged = acknowledged_ids(ctx)
    evidence = validation_evidence(ctx)
    reason = bypass_reason(ctx)
    lines: list[str] = []
    for policy in matches[:5]:
        pid = str(policy.get("id") or "<unknown>")
        summary = str((policy.get("explain") or {}).get("summary") if isinstance(policy.get("explain"), dict) else policy.get("title") or "")
        source = str(policy.get("sourceRecord") or "")
        if pid in acknowledged and reason:
            lines.extend([
                "DRY-RUN BYPASS. Policy Machinery block runtime: explicit structured policy context acknowledged a block-level behavior policy.",
                "No lifecycle hard-stop is installed; this is review-only.",
                f"- {pid}: {summary}",
                f"  bypass: {reason}",
            ])
            if source:
                lines.append(f"  source: {source}")
        elif evidence:
            lines.extend([
                "DRY-RUN ALLOW. Policy Machinery block runtime: validation evidence is attached for a block-level boundary.",
                "No lifecycle hard-stop is installed; this is review-only.",
                f"- {pid}: {summary}",
                f"  evidence: {evidence[0]}",
            ])
            if source:
                lines.append(f"  source: {source}")
        else:
            lines.extend([
                "DRY-RUN STOP. Policy Machinery block runtime: structured policy context matched a block-level behavior policy without validation evidence.",
                "No lifecycle hard-stop is installed; this is review-only.",
                "Matched policies:",
                f"- {pid}: {summary}",
            ])
            if source:
                lines.append(f"  source: {source}")
            lines.extend([
                "",
                "To proceed in a future blocking runtime, attach validation evidence or add policy_context.acknowledgedPolicyBlocks with a policyBlockBypassReason.",
            ])
    if lines:
        print("\n".join(lines))


if __name__ == "__main__":
    main()
