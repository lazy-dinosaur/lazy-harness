"""host_migration_state.py — deterministic pending-migration surfacing for the turn-start reminder.

Runs `lazy record-lint --format=json` with a bounded timeout and, when the host has
pending record-migration work (issues or advisories > 0), returns compact reminder
lines pointing at the guided resume path (lazy-record-quality / lazy-memory-backfill).

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


def migration_lines(lazy_bin: str, cwd: str) -> list:
    """Return [] when clean/unknown; compact pending-migration reminder lines otherwise."""
    try:
        result = subprocess.run(
            [lazy_bin, "record-lint", "--format=json"],
            capture_output=True,
            text=True,
            timeout=LINT_COMMAND_TIMEOUT_SECONDS,
            cwd=cwd,
        )
        data = json.loads(result.stdout or "{}")
        if not isinstance(data, dict):
            return []
        issues = int(data.get("issueCount") or 0)
        advisories = int(data.get("advisoryCount") or 0)
    except Exception:
        return []
    if issues <= 0 and advisories <= 0:
        return []
    return [
        (
            f"- Host record migration PENDING (deterministic record-lint probe): issues={issues}, advisories={advisories}. "
            "Do not leave this silent: surface it to the user this session and offer to resume the guided migration \u2014 "
            "issues (digest/broken refs) \u2192 `lazy-record-quality` skill; advisories (surface terms/reachability, ADR 0053) \u2192 "
            "`lazy-memory-backfill` skill. Both are batch-scoped and user-approved; batch progress persists in this host's plan records. "
            "Host records are NEVER rewritten automatically."
        ),
    ]
