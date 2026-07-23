# Gate Fingerprint State

Status: accepted
Layer: SSOT
Date: 2026-05-18
Related SDD: `.lazy-harness/spec/platform/option-gate-discipline.md`
Related SDD: `.lazy-harness/spec/platform/project-rule-router.md`
Related TDD: `.lazy-harness/tests/bdd-trigger-option-gate-loop-bypass.md`
Related TDD: `.lazy-harness/tests/project-rule-placement-gate-loop.md`

## Rule digest

- Status: active
- Layer: SSOT
- Scope: framework-global
- Aliases:
  - 게이트 상태
  - fingerprint
  - 게이트 중복 방지
- Applies when:
  - implementing or debugging lifecycle option-gate / STOP reminders that need same-turn duplicate suppression
  - reasoning about turn-boundary state for loop-prone helpers (BDD trigger, project-rule-placement)
- Must:
  - treat `open-gates.json` as regenerable runtime state, not a canonical record
  - clear `open_fingerprints` whenever `message_id` (the turn boundary) changes
  - emit a gate reminder only if `(helper, fingerprint)` is not already open for the current `message_id`, then record it
  - keep state read/write best-effort so a failure never crashes the lifecycle hook
  - for `project-rule-placement`, fingerprint semantic user/assistant text plus normalized successful placement-relevant action kinds; exclude raw tool arguments and failed calls
- Must not:
  - require `payload.assistant_response` to exist; Jcode may omit it, so `last_user_message` must remain sufficient semantic evidence
- Record completion:
  - state-schema, turn-boundary, or suppression-behavior changes update this SSOT plus the option-gate SDD and gate-loop TDD records
- Related records:
  - `.lazy-harness/spec/platform/option-gate-discipline.md`
  - `.lazy-harness/spec/platform/project-rule-router.md`
  - `.lazy-harness/tests/bdd-trigger-option-gate-loop-bypass.md`
  - `.lazy-harness/tests/project-rule-placement-gate-loop.md`

## Source of truth

Lifecycle option-gate helpers that need same-turn duplicate suppression use:

```text
$LAZY_RUNTIME_ROOT/state/open-gates.json
```

This file is runtime state, not institutional memory. It is safe to regenerate and should not be treated as a canonical record. Canonical behavior is defined by this SSOT and the SDD contract.

## State schema

```json
{
  "last_message_id": "<jcode response.completed message_id>",
  "open_fingerprints": {
    "<helper>:<fingerprint>": {
      "first_seen_message_id": "<message_id>",
      "first_seen_ts": "<UTC timestamp>"
    }
  }
}
```

## Contract

- `message_id` is the turn boundary.
- When `message_id` changes, `open_fingerprints` is cleared.
- A helper may emit an option-gate reminder only if `(helper, fingerprint)` is not already present for the current `message_id`.
- After emitting, the helper records `(helper, fingerprint)` in this file.
- State read/write failures are best-effort and must not crash the lifecycle hook.
- Helpers must not require `payload.assistant_response` because Jcode `response.completed` may omit assistant text; helpers may include it when present.
- Project-rule placement fingerprints use semantic `last_user_message`/optional `assistant_response` text plus normalized successful placement-relevant action kinds. Raw tool arguments, read paths, unrelated tools, and failed calls are excluded from the fingerprint input.
- Known helper prefixes:
  - `bdd:<fingerprint>` for BDD scenario option-gate triggers.
  - `project-rule-placement:<fingerprint>` for project rule placement STOP reminders.

## Implementation map

- Status: `verified-runtime-helper`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/gate-fingerprint.sh` — owns read/write/check/record behavior for `open-gates.json`.
  - `.lazy-harness/scripts/gate-state.ts` — CLI runtime helper for inspecting and clearing stale `open-gates.json` entries during readiness cleanup.
  - `.lazy-harness/bin/lazy` — dispatches `lazy gate-state list|clear-stale`.
  - `.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh` — uses `gate-fingerprint.sh` with BDD fingerprints.
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — writes compatible `project-rule-placement:<fingerprint>` entries directly because its Python implementation runs inside one helper process.
  - `.lazy-harness/scripts/self-test.py` — validates same-turn suppression and new-turn re-fire in `check_bdd_trigger_loop_suppression` and `check_project_rule_placement_helper`.
- Flow:
  1. A loop-prone helper computes a deterministic fingerprint from its stable, contract-approved trigger inputs.
  2. Project-rule placement uses semantic text plus successful relevant action kinds; other helpers keep their own SDD-defined inputs.
  3. It checks whether the helper-prefixed key already exists for the current `message_id`.
  4. If already open, it exits silently.
  5. If new, it emits the gate/STOP reminder and records the fingerprint.
  6. The next `message_id` clears prior entries.
- Protection:
  - `.lazy-harness/scripts/self-test.py` `check_bdd_trigger_loop_suppression`
  - `.lazy-harness/scripts/self-test.py` `check_project_rule_placement_helper` — same-turn suppression plus tool/path-only and failed-call fingerprint exclusion
  - `.lazy-harness/scripts/self-test.py` `check_gate_state_cli_and_record_audit_source_guard`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/option-gate-discipline.md`
  - SDD: `.lazy-harness/spec/platform/project-rule-router.md`
  - TDD: `.lazy-harness/tests/bdd-trigger-option-gate-loop-bypass.md`
  - TDD: `.lazy-harness/tests/project-rule-placement-gate-loop.md`

## Discovery capture — project-rule fingerprint narrowing

- Primary canonical record: `.lazy-harness/tests/project-rule-placement-gate-loop.md`.
- SSOT delta: only `project-rule-placement:<fingerprint>` input composition changes; the file path, state schema, message boundary, and best-effort behavior remain unchanged.
- SDD/TDD links are updated; BDD/DDD/ADR have no independent canonical delta.
