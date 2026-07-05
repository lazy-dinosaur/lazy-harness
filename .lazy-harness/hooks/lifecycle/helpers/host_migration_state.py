"""host_migration_state.py — deterministic pending-migration surfacing for the turn-start reminder.

Runs `lazy record-lint --format=json` and `lazy graph-hygiene --migration-plan --format=json`
with bounded timeouts and, when the host has pending record/graph migration work, returns a
compact reminder line pointing at the guided resume paths (lazy-record-quality /
lazy-memory-backfill / lazy-graph-migrate).

Contract (pi-agent-package SDD; user-approved resume-surfacing decision 2026-07-05):
- deterministic registry/validator enumeration only; user-text-agnostic; advisory-only
- bounded timeout shorter than the extension hook timeout; fail open (empty list) on
  any error/timeout so slow lint never prevents read-debt arming
- never rewrites records; surfaces state so agent + user can resume the guided,
  user-approved batch flow (never-bulk-rewrite principle preserved)
"""

import json
import os
import subprocess

LINT_COMMAND_TIMEOUT_SECONDS = float(os.environ.get("LAZY_HARNESS_LINT_TIMEOUT_SECONDS", "5"))


def _run_json(cmd: list, cwd: str) -> dict:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=LINT_COMMAND_TIMEOUT_SECONDS,
            cwd=cwd,
        )
        data = json.loads(result.stdout or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def migration_lines(lazy_bin: str, cwd: str) -> list:
    """Return [] when clean/unknown; one compact pending-migration reminder line otherwise."""
    lint = _run_json([lazy_bin, "record-lint", "--format=json"], cwd)
    issues = int(lint.get("issueCount") or 0)
    advisories = int(lint.get("advisoryCount") or 0)
    plan = _run_json([lazy_bin, "graph-hygiene", "--migration-plan", "--format=json"], cwd).get("migrationPlan") or {}
    legacy = int(plan.get("legacySchemaRows") or 0)
    removed = int(plan.get("removedFrameworkRefs") or 0)
    if issues <= 0 and advisories <= 0 and legacy <= 0 and removed <= 0:
        return []
    parts = []
    if issues > 0 or advisories > 0:
        parts.append(
            f"record-lint issues={issues} (→ `lazy-record-quality` skill) / advisories={advisories} (→ `lazy-memory-backfill` skill, ADR 0053)"
        )
    if legacy > 0 or removed > 0:
        parts.append(
            f"graph legacy-schema rows={legacy} / removed-framework refs={removed} (→ `lazy-graph-migrate` skill, ADR 0050)"
        )
    return [
        (
            "- Host record migration PENDING (deterministic probes): "
            + "; ".join(parts)
            + ". Do not leave this silent: surface it to the user this session and offer to resume the guided migration. "
            + "All paths are batch-scoped and user-approved; progress persists in this host's plan records. "
            + "Host records/graph rows are NEVER rewritten automatically."
        ),
    ]
