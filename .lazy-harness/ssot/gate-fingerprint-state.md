# Gate Fingerprint State

Status: accepted
Layer: SSOT
Date: 2026-05-18
Related SDD: `.lazy-harness/spec/platform/option-gate-discipline.md`
Related SDD: `.lazy-harness/spec/platform/project-rule-router.md`
Related TDD: `.lazy-harness/tests/bdd-trigger-option-gate-loop-bypass.md`
Related TDD: `.lazy-harness/tests/project-rule-placement-gate-loop.md`

## Source of truth

Lifecycle option-gate helpers that need same-turn duplicate suppression use:

```text
.lazy-harness/state/open-gates.json
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
- Helpers must not depend on `payload.assistant_response` because jcode `response.completed` payload does not include assistant text in production.
- Known helper prefixes:
  - `bdd:<fingerprint>` for BDD scenario option-gate triggers.
  - `project-rule-placement:<fingerprint>` for project rule placement STOP reminders.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/gate-fingerprint.sh` — owns read/write/check/record behavior for `open-gates.json`.
  - `.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh` — uses `gate-fingerprint.sh` with BDD fingerprints.
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — writes compatible `project-rule-placement:<fingerprint>` entries directly because its Python implementation runs inside one helper process.
  - `.lazy-harness/scripts/self-test.py` — validates same-turn suppression and new-turn re-fire in `check_bdd_trigger_loop_suppression` and `check_project_rule_placement_helper`.
- Flow:
  1. A loop-prone helper computes a deterministic fingerprint from stable trigger inputs.
  2. It checks whether the helper-prefixed key already exists for the current `message_id`.
  3. If already open, it exits silently.
  4. If new, it emits the gate/STOP reminder and records the fingerprint.
  5. The next `message_id` clears prior entries.
- Protection:
  - `.lazy-harness/scripts/self-test.py` `check_bdd_trigger_loop_suppression`
  - `.lazy-harness/scripts/self-test.py` `check_project_rule_placement_helper`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/option-gate-discipline.md`
  - SDD: `.lazy-harness/spec/platform/project-rule-router.md`
  - TDD: `.lazy-harness/tests/bdd-trigger-option-gate-loop-bypass.md`
  - TDD: `.lazy-harness/tests/project-rule-placement-gate-loop.md`
