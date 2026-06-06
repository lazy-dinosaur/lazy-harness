# TDD — Operational State Packet

Status: accepted
Date: 2026-06-06
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/operational-state-packet.md`
Related schema: `.lazy-harness/schemas/operational-state-packet.schema.json`
Related plan: `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - changing `lazy operational-state`, packet schema, fallback behavior, or hook wiring boundaries
- Must:
  - validate `lazy operational-state --message "..." --format=json` emits schema-shaped JSON
  - verify raw message text is not present in packet output
  - verify missing generated context-index cache reports `fallback-needed` and still exits 0
  - verify no default lifecycle hook invokes operational-state
- Must not:
  - allow hard-block decisions in the packet
  - allow automatic message.received integration without explicit SDD/TDD update
- Related records:
  - `.lazy-harness/spec/platform/operational-state-packet.md`
  - `.lazy-harness/spec/platform/context-delivery-contract.md`
- Implementation hints:
  - Files: `.lazy-harness/scripts/operational-state.ts`, `.lazy-harness/schemas/operational-state-packet.schema.json`, `.lazy-harness/bin/lazy`, `.lazy-harness/scripts/self-test.py`
  - Tests: `.lazy-harness/scripts/self-test.py#check_operational_state_packet_phase6`

## Regression cases

1. CLI output includes `schemaVersion`, `source`, `taskKind`, read arrays, capabilities, evidence, risk, and notes.
2. Raw message string passed with `--message` does not appear in JSON or Markdown output.
3. Missing `.lazy-harness/generated/context-index.json` yields `fallback-needed` note and exit 0.
4. Lifecycle hooks do not call `operational-state`.
5. Packet uses record paths and reasons for read entries.
6. `lazy-evidence-capsule` appears only when the current host registry defines that host-owned capability; framework-source scope requires it, downstream host scope may omit it.

## Layer completeness gate

- SDD: affected; `.lazy-harness/spec/platform/operational-state-packet.md` defines contract.
- BDD: no UI/user-flow impact.
- SSOT: no canonical ownership change.
- DDD: no domain/business vocabulary impact.
- ADR: no new decision needed; current change implements an approved plan phase.

## Implementation map

- Status: `phase-6-implemented`
- Primary files:
  - `.lazy-harness/tests/operational-state-packet.md` — this TDD record.
  - `.lazy-harness/spec/platform/operational-state-packet.md` — SDD contract.
  - `.lazy-harness/schemas/operational-state-packet.schema.json` — schema.
  - `.lazy-harness/scripts/operational-state.ts` — CLI implementation.
  - `.lazy-harness/bin/lazy` — dispatch.
  - `.lazy-harness/scripts/self-test.py` — regression checks.
- Key symbols:
  - `buildOperationalState` (`operational-state.ts`)
  - `check_operational_state_packet_phase6` (`self-test.py`)
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy operational-state --message "validate evidence" --format=json`
