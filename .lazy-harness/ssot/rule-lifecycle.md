# Rule Lifecycle and Binding

Status: accepted
Layer: SSOT
Date: 2026-05-26
Related SDD: `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
Related ADR: `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md`
Related TDD: `.lazy-harness/tests/rule-binding-pr-body-guard.md`

## Purpose

A lazy-harness rule is not fully installed just because it is written in a record.

Durable rule capture has two responsibilities:

1. Store the human-readable rule in the correct `.lazy-harness` layer.
2. Bind executable or high-risk rules to the intent/action boundaries where agents and hooks must retrieve or enforce them.

This closes the dogfood gap where a host PR body rule was stored in Medivance records but was missed when a PR was created.

## Lifecycle states

| State | Meaning |
|---|---|
| `captured` | Rule exists in a human-readable record but has no trigger/action binding yet. |
| `bound` | Rule has machine-readable metadata describing when it applies. |
| `enforced` | A hook/helper/CLI/audit path checks the rule at or before the relevant action boundary. |
| `advisory-only` | Rule is intentionally not enforced; this must be explicit, not accidental. |
| `retired` | Rule is obsolete and should not be applied. |

A rule intended to affect future agent behavior should not remain only `captured` unless the record explicitly says it is advisory-only or still under planning.

## Binding metadata contract

Rule bindings are machine-readable JSON records. The canonical committed bindings live under `.lazy-harness/ssot/rule-bindings.json` when a host/framework has installed bindings. Generated caches may live under `.lazy-harness/generated/**`, but generated files are not canonical.

Minimum binding fields:

```json
{
  "id": "pr-body-format",
  "status": "enforced",
  "sourceRecord": ".lazy-harness/ssot/pr-description-format.md",
  "appliesWhen": ["creating_pull_request", "editing_pull_request"],
  "actions": [
    {"tool": "bash", "commandRegex": "\\bgh\\s+pr\\s+(create|edit)\\b"}
  ],
  "severity": "block",
  "checks": ["read_source_record", "validate_required_sections"],
  "requiredSections": ["## Why", "## What", "## Task"]
}
```

## Default PR body binding

If a host contains `.lazy-harness/ssot/pr-description-format.md`, lazy-harness treats PR body formatting as an executable candidate even before a host-specific `rule-bindings.json` exists:

- Action boundary: `gh pr create` / `gh pr edit` through bash tool execution.
- Required sections: `## Why`, `## What`, `## Task`.
- Severity: `block` for non-interactive PR commands with missing or malformed body content.

Hosts may override this by adding an explicit binding with `status: advisory-only`, different `requiredSections`, or different action patterns.

## Audit expectation

Record/audit tooling should eventually report any enduring rule that has enforcement language but lacks binding metadata. Until that audit is implemented, action-boundary helpers protect the first exemplar.

## Implementation map

- Status: `implemented-first-exemplar`
- Primary files:
  - `.lazy-harness/ssot/rule-lifecycle.md` — this SSOT lifecycle contract.
  - `.lazy-harness/spec/platform/rule-binding-action-boundary.md` — SDD for before-action rule checks.
  - `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md` — ADR choosing rule bindings over prompt-only recall.
  - `.lazy-harness/tests/rule-binding-pr-body-guard.md` — regression record for PR body guard.
  - `.lazy-harness/hooks/lifecycle/helpers/check-rule-action-boundary.py` — generic action-boundary helper with PR exemplar support.
  - `.jcode/hooks/check-bash.sh` and generated `.jcode` wiring — call the helper before allowing bash commands.
  - `.lazy-harness/scripts/self-test.py` — fixture coverage.
- Key symbols:
  - `load_bindings` (`check-rule-action-boundary.py`) — reads host bindings and default PR exemplar.
  - `check_pr_body_binding` (`check-rule-action-boundary.py`) — validates `gh pr create/edit` bodies.
  - `check_rule_action_boundary_pr_body_guard` (`self-test.py`) — regression coverage.
- Flow:
  1. User/agent captures a durable rule.
  2. If the rule affects a high-risk action boundary, add binding metadata or mark advisory-only.
  3. Before bash execution, `.jcode/hooks/check-bash.sh` invokes `check-rule-action-boundary.py`.
  4. The helper reads host records/bindings and denies malformed PR body commands before mutation.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
  - TDD: `.lazy-harness/tests/rule-binding-pr-body-guard.md`
  - ADR: `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md`
