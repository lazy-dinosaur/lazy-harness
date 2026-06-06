# SDD — Operational State Packet

Status: accepted
Date: 2026-06-06
Layer: SDD
Related plan: `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`
Related schema: `.lazy-harness/schemas/operational-state-packet.schema.json`
Related SDD: `.lazy-harness/spec/platform/context-delivery-contract.md`
Related SDD: `.lazy-harness/spec/platform/context-tier-manifest.md`
Related SDD: `.lazy-harness/spec/platform/evidence-capsule-standard.md`
Related SSOT: `.lazy-harness/ssot/capability-registry.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - explicitly running `lazy operational-state` to summarize current host context pointers
  - prototyping compact runtime context views before dogfood/default integration
  - checking whether generated context indexes exist or source-scan fallback is needed
- Must:
  - keep `lazy operational-state` explicit/manual in this phase
  - emit a non-canonical packet that points to records/files by path and reason
  - report `fallback-needed` when generated context-index cache is missing instead of failing
  - omit raw user messages/transcripts from packet output
  - keep packet output advisory and non-blocking
  - update schema, SDD, CLI dispatch, and self-test together when packet shape changes
- Must not:
  - wire operational-state into default `message.received`, response hooks, or hard gates
  - store or journal raw `--message` content
  - treat generated indexes or packet contents as canonical truth over records/source
  - output hard-block decisions
- Record completion:
  - changes to packet fields, taskKind/risk enums, generated-index fallback semantics, or runtime consumers update this SDD, schema, and self-test coverage
- Related records:
  - `.lazy-harness/spec/platform/context-delivery-contract.md`
  - `.lazy-harness/spec/platform/context-tier-manifest.md`
  - `.lazy-harness/spec/platform/evidence-capsule-standard.md`
  - `.lazy-harness/ssot/capability-registry.md`
- Implementation hints:
  - Files: `.lazy-harness/scripts/operational-state.ts`, `.lazy-harness/schemas/operational-state-packet.schema.json`, `.lazy-harness/bin/lazy`, `.lazy-harness/scripts/self-test.py`
  - Tests: `.lazy-harness/scripts/self-test.py`

## Purpose

The Operational State Packet is a compact, explicit command output that summarizes likely useful context for the current host without changing prompt/runtime defaults.

It answers:

```text
Given an optional message and current host records, which record/file/capability/evidence pointers are likely useful, and is generated context cache missing?
```

## Packet shape

The stable logical shape is defined by `.lazy-harness/schemas/operational-state-packet.schema.json`.

Top-level fields:

- `schemaVersion`
- `generatedAt`
- `source.canonicalInputs`
- `source.generatedInputs`
- `taskKind`
- `requiredReads`
- `recommendedReads`
- `capabilities`
- `evidence`
- `risk`
- `notes`

No top-level or nested field may contain raw message text.

## Task kind and risk

Task kind is a best-effort explicit CLI heuristic, not semantic authority:

- `implementation`
- `planning`
- `validation`
- `recording`
- `unknown`

Risk is advisory:

- `low`
- `medium`
- `high`
- `unknown`

The CLI may use the provided message to classify these coarse fields, but the packet must not expose or persist the raw message.

## Runtime behavior

Phase 6 behavior:

- manual command only: `.lazy-harness/bin/lazy operational-state --message "..." --format=json`,
- no default `message.received` use,
- not wired into message.received or response hooks by default,
- no journaling,
- no automatic evidence writing,
- no hard block output,
- generated context-index absence produces a note containing `fallback-needed` and source-scan fallback still succeeds.

## Implementation map

- Status: `phase-6-implemented`
- Primary files:
  - `.lazy-harness/spec/platform/operational-state-packet.md` — this SDD contract.
  - `.lazy-harness/tests/operational-state-packet.md` — TDD/regression record for explicit CLI behavior, missing generated-index fallback, no raw message output, and no hook wiring.
  - `.lazy-harness/schemas/operational-state-packet.schema.json` — packet schema.
  - `.lazy-harness/scripts/operational-state.ts` — explicit manual packet generator.
  - `.lazy-harness/bin/lazy` — dispatches `lazy operational-state`.
  - `.lazy-harness/project/feature-navigation.xml` — maps operational-state assets under `context-delivery-indexing`.
  - `.lazy-harness/manifests/init-categories.json` — syncs SDD/TDD/schema/script/dispatcher assets.
  - `.lazy-harness/scripts/self-test.py` — validates CLI, schema invariants, fallback note, no raw message leakage, and no hook wiring.
  - `.lazy-harness/knowledge/graph.jsonl` — records implementation/protection links.
- Key symbols:
  - `buildOperationalState` (`operational-state.ts`) — builds packet from source-scan context index, capability registry, evidence assets, and generated-index presence.
  - `check_operational_state_packet_phase6` (`self-test.py`) — protects Phase 6 behavior.
- Flow:
  1. User/agent explicitly runs `lazy operational-state` with optional `--message`.
  2. CLI builds or reads context-index metadata in memory and checks generated cache presence.
  3. CLI emits advisory required/recommended reads, matching capabilities, evidence pointers, risk, and notes.
  4. Caller still reads canonical records/source before acting.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy operational-state --message "validate evidence" --format=json`
  - `.lazy-harness/bin/lazy doctor --profile=smoke`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/context-delivery-contract.md`
  - SDD: `.lazy-harness/spec/platform/context-tier-manifest.md`
  - SDD: `.lazy-harness/spec/platform/evidence-capsule-standard.md`
  - SSOT: `.lazy-harness/ssot/capability-registry.md`
  - Planning: `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`
- Machine index:
  - graph ids: `kg_operational_state_packet_specifies_contract`, `kg_operational_state_packet_implemented_by_script`, `kg_operational_state_packet_protected_by_self_test`

## Discovery capture

- DDD: none.
- SDD: this record defines packet semantics.
- BDD: no user-visible UI flow change.
- TDD: `.lazy-harness/tests/operational-state-packet.md` protects CLI behavior.
- ADR: no new decision; implements Phase 6 of the approved compression plan.
- SSOT: no new canonical ownership; packet is derived/advisory.
- Planning: Phase 6 of `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`.
