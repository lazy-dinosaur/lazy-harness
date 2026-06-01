# TDD — Runtime Record-First Action Boundary

Status: accepted
Date: 2026-05-31
Layer: TDD
Related SSOT: `.lazy-harness/ssot/rule-lifecycle.md`
Related SDD: `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
Related SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`

## Regression scenario

An agent is asked to run or inspect a host app connected to a test database/runtime instance.

Failure observed:

1. Agent inspects generic commands, env files, or dev-cli source.
2. Agent reasons about worktree/instance behavior.
3. Agent skips the canonical `.lazy-harness` runtime/dogfood SSOT.
4. Agent proceeds toward a dev/test instance command with host-specific assumptions.

Expected behavior:

- If policy-bearing canonical runtime/dogfood/instance records exist in `.lazy-harness/{domain,spec,behavior,decisions,ssot}/`, lazy-harness must require a recent read/search of those records before allowing dev/runtime start or inspect commands.
- TDD regression records are intentionally excluded from default policy-source detection, so this test record does not itself make every host dev command block.
- Hosts without such records should not be blocked by this default guard.

## Protection

`check_rule_action_boundary_runtime_record_guard` in `.lazy-harness/scripts/self-test.py` covers three cases:

1. `bun scripts/dev-cli.ts --test --instance feature-x` is allowed when no matching runtime/dogfood record exists.
2. The same command is blocked when `.lazy-harness/ssot/medivance-dogfood-runtime-policy.md` exists and recent tool history lacks a lookup.
3. The command is allowed after recent tool-call history includes a read of that record.

## Layer completeness gate

- DDD: no domain entity/business-rule change.
- SDD: action-boundary contract updated in `.lazy-harness/spec/platform/rule-binding-action-boundary.md`.
- BDD: visible agent workflow expectation is that dev/runtime execution is stopped until canonical runtime records are consulted.
- TDD: this record and `check_rule_action_boundary_runtime_record_guard`.
- ADR: existing ADR 0039 covers action-boundary bindings; no new trade-off beyond user-confirmed enforcement restoration.
- SSOT: `.lazy-harness/ssot/rule-lifecycle.md` and `.lazy-harness/ssot/harness-enforcement-policy.md` updated.

## Implementation map

- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-rule-action-boundary.py` — implements runtime command detection and record-first lookup requirement.
  - `.lazy-harness/scripts/self-test.py` — fixture for allow/block/allow-after-lookup behavior.
  - `.lazy-harness/spec/platform/rule-binding-action-boundary.md` — SDD contract for runtime/dev-instance action boundary.
  - `.lazy-harness/ssot/rule-lifecycle.md` — canonical lifecycle binding contract.
- Key symbols:
  - `RUNTIME_COMMAND_RE` — identifies dev/runtime command surfaces.
  - `RUNTIME_RECORD_RE` — identifies relevant canonical runtime/dogfood records by path.
  - `runtime_policy_records` — locates relevant records in canonical layers.
  - `has_runtime_record_lookup` — checks recent tool-call history for read/search evidence.
  - `check_runtime_record_binding` — emits STOP text when runtime command lacks record-first evidence.
  - `check_rule_action_boundary_runtime_record_guard` — regression fixture.
- Flow:
  1. Jcode fires `tool.execute.before` for `bash`.
  2. `.jcode/hooks/check-bash.sh` invokes `check-rule-action-boundary.py`.
  3. The helper matches dev/runtime command patterns.
  4. If relevant runtime/dogfood records exist and recent tool-call history lacks a lookup, the helper emits STOP text.
  5. The bash hook converts STOP text into a deny JSON for Jcode.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`

## Rule placement

- Rule: runtime/dev-server/test-instance commands must be bound to record-first lookup when relevant canonical runtime/dogfood records exist.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/rule-binding-runtime-record-first.md`
- Why not AGENTS.md: this is a regression/protection case and implementation map, not the whole grammar.
- Why not `.jcode`: enforcement is shared lazy-harness framework behavior, not local/private Jcode-only preference.
- Confirmation: user-confirmed
