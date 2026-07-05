# Rule Binding Action Boundary

Status: superseded-by-organic-response-lifecycle
Layer: SDD
Related SSOT: `.lazy-harness/ssot/rule-lifecycle.md`
Related ADR: `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md`
Superseded by: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Replacement SDD: `.lazy-harness/spec/platform/response-rule-audit.md`
Related TDD: `.lazy-harness/tests/rule-binding-pr-body-guard.md`

## Rule digest

- Status: deprecated
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 액션 바운더리
  - 행동 경계 가드
  - action boundary
- Applies when:
  - evaluating old tool-attached rule binding/action-boundary helpers
  - seeing `check-rule-action-boundary.py` in old generated or user-owned Jcode bash hooks
  - migrating project policy away from `bash`, `gh`, `dev-cli`, or MCP-specific adapters
- Must:
  - treat tool-attached project-policy enforcement as legacy compatibility only
  - keep `.jcode/hooks/check-bash.sh` focused on destructive shell safety
  - move PR/runtime/release/DB guidance into pre-response relevant-record digest plus `response.completed` audit
  - keep `check-rule-action-boundary.py` as a no-op compatibility shim so older hooks do not break
- Must not:
  - add new project/team policy branches keyed to concrete tools such as bash, gh, dev-cli, or GitHub MCP
  - block malformed PR descriptions in `tool.execute.before`; response-rule audit owns that backstop now
- Record completion:
  - changes to legacy action-boundary compatibility update this SDD, ADR 0039, rule lifecycle SSOT, and Phase 5 tests
- Related records:
  - `.lazy-harness/spec/platform/response-rule-audit.md`
  - `.lazy-harness/ssot/harness-enforcement-policy.md`
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`

## Purpose

This record used to define before-action rule binding enforcement for stored project rules. Phase 5 of the organic memory loop supersedes that direction.

The original dogfood failure was real: a stored PR body rule was missed during PR creation. The first implementation solved that with a `gh pr create/edit` tool-attached hard block in `check-rule-action-boundary.py` and generated `.jcode/hooks/check-bash.sh`.

The user later rejected that architectural direction because it was too tool-attached and slow to scale. ADR 0041 replaced it with:

```text
message.received relevant-record digest
+ response.completed response-rule-audit
+ narrow hard stops only after evidence
```

## Current contract

### `check-rule-action-boundary.py`

Current status: **legacy compatibility shim**.

- It parses payloads for compatibility.
- It emits no output by default.
- It does not enforce PR body format, runtime policy, release policy, DB policy, or other project/team guidance.
- Existing host/user-owned bash hooks may still call it safely after sync.

### Generated `.jcode/hooks/check-bash.sh`

Current status: **destructive shell safety only**.

The generated bash hook should block only generic destructive shell patterns, for example:

- `rm -rf /`
- `sudo rm -rf /`
- raw disk overwrite such as `dd ... of=/dev/sd*`
- filesystem creation on block devices such as `mkfs /dev/...`

It must not call project-policy helpers or know PR body formats.

### PR body guidance replacement

PR body structure is now handled by response lifecycle:

1. Host PR records include compact `## Rule digest` metadata.
2. `message.received` surfaces relevant PR description records before the assistant responds.
3. `response.completed` audit detects strong evidence that a surfaced PR rule was ignored.
4. Clean/compliant turns remain silent.

## Non-goals

- Do not remove destructive shell safety.
- Do not remove mandatory record-completion gates.
- Do not remove response audit/backstop.
- Do not promote Phase 6 hard stops in this Phase 5 migration.

## Implementation map

- Status: `phase5-superseded`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-rule-action-boundary.py` — legacy no-op compatibility shim.
  - `.lazy-harness/scripts/jcode-wiring.ts` — generated bash hook no longer calls the action-boundary helper.
  - `.lazy-harness/ssot/rule-lifecycle.md` — lifecycle SSOT now points to organic response lifecycle for action guidance.
  - `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md` — historical ADR amended/superseded by ADR 0041.
  - `.lazy-harness/spec/platform/response-rule-audit.md` — replacement audit surface.
  - `.lazy-harness/tests/rule-binding-pr-body-guard.md` — TDD record updated to protect no-op legacy behavior and replacement audit coverage.
  - `.lazy-harness/scripts/self-test.py` — Phase 5 regression fixtures.
- Key symbols:
  - `main` (`check-rule-action-boundary.py`) — parses payload and returns 0 with no output.
  - `checkBashHook` (`jcode-wiring.ts`) — generated destructive shell safety hook.
  - `check_rule_action_boundary_legacy_no_project_policy` (`self-test.py`) — verifies malformed PR bodies are no longer blocked by the legacy helper.
  - `check_jcode_wiring_bash_safety_only_hook` (`self-test.py`) — verifies generated bash hook contains destructive safety only and no project-policy adapter.
  - `check_response_rule_audit_from_surfaced_digest` (`self-test.py`) — verifies the replacement PR miss audit path.
- Flow:
  1. A host/user-owned old bash hook may call `check-rule-action-boundary.py`.
  2. The helper emits nothing, so the old hook continues to the destructive safety checks.
  3. New generated bash hooks do not call the helper at all.
  4. PR/runtime/project guidance arrives through relevant-record digest before response.
  5. Misses are caught after response by `check-response-rule-audit.py` when strong evidence exists.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_rule_action_boundary_legacy_no_project_policy`
  - `.lazy-harness/scripts/self-test.py#check_jcode_wiring_bash_safety_only_hook`
  - `.lazy-harness/scripts/self-test.py#check_response_rule_audit_from_surfaced_digest`
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - SDD: `.lazy-harness/spec/platform/response-rule-audit.md`
  - SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`
- Machine index:
  - graph ids: `kg_phase5_rule_action_boundary_superseded`, `kg_phase5_bash_safety_only_wiring`, `kg_phase5_legacy_boundary_noop`

## Rule placement

- Rule: action-boundary project-policy branches are superseded; keep only compatibility shims and generic destructive shell safety.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
- Why not AGENTS.md: this is a platform migration contract, not core agent grammar.
- Why not `.jcode`: the behavior is shared lazy-harness framework behavior and must sync to all hosts.
- Confirmation: user approved Phase 5 migration on 2026-06-01.

## Discovery capture

- DDD: no domain vocabulary change.
- SDD: this record updated from active enforcement to superseded compatibility.
- BDD: agent-visible action guidance moves to pre-response context and post-response audit.
- TDD: Phase 5 tests updated to protect no-op legacy helper and safety-only bash hook.
- ADR: ADR 0039 amended/superseded by ADR 0041.
- SSOT: rule lifecycle SSOT updated.
