# ADR 0042 — Use Record Index as the Canonical Cache/Listing Name

- Status: Accepted
- Date: 2026-06-06
- Trigger: SCR-401 option gate. User selected Option A: rename the future cache/listing surface from `context-index` to `record-index` to avoid obsolete context-helper architecture language.

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Applies when:
  - naming future deterministic cache/listing tools for Record Index Header metadata
  - deciding whether to keep, deprecate, or alias `context-index`
  - updating SDD/TDD/tasks/plan/report before parser/cache implementation
  - evaluating whether cache/listing command names imply semantic authority
- Must:
  - use `record-index` as the canonical future command/cache/schema naming surface
  - describe the tool scope as deterministic record-authored metadata listing/cache generation only
  - keep `context-index` absent from active command/source/schema/cache paths after SCR-402 Option A unless a new option gate explicitly reopens compatibility
  - keep parser/cache implementation covered by tests and no raw-message query interface
  - update SDD/TDD/SSOT/planning together when implementation migration changes
- Must not:
  - introduce new canonical `context-*` naming for searchable record memory
  - accept raw user-message input for record-index cache/listing
  - output requiredRead, confidence, intent, risk, gate, nextAction, candidateMeanings, or equivalent semantic-authority fields
  - treat a generated record-index hit as proof of evidence read
- Record completion:
  - implementation of this ADR updates `.lazy-harness/spec/platform/record-index-header.md`, `.lazy-harness/tests/record-index-header.md`, `.lazy-harness/ssot/cli-tool-boundary.md`, `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`, generated docs, and graph rows.
- Related records:
  - `.lazy-harness/domain/searchable-record-memory.md`
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md`
  - `.lazy-harness/spec/platform/record-index-header.md`
  - `.lazy-harness/tests/record-index-header.md`
  - `.lazy-harness/ssot/cli-tool-boundary.md`
  - `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`

## Context

Earlier cleanup deleted raw-user-message query helpers and removed stale Context Delivery / relevant-record-query architecture. The remaining deterministic cache/listing concept was still described in places as `context-index` because a source file and CLI command already existed.

That name is risky because it can be read as a continuation of the deleted context-helper architecture. The domain model now uses these terms instead:

- Searchable Record Memory
- Record-authored metadata
- Record Index Header
- LLM-owned retrieval
- Deterministic cache

The user selected Option A in SCR-401: canonical future naming should be `record-index`.

## Decision

Use **`record-index`** as the canonical future name for the deterministic cache/listing surface that indexes record-authored metadata.

Scope:

```text
record-index
→ deterministic listing/cache of canonical record-authored metadata
→ no raw user-message query
→ no semantic authority fields
→ no evidence-debt satisfaction by cache hit alone
```

Compatibility:

- SCR-402 Option A implemented the clean replacement path: active `context-index` command/source/schema/cache paths are removed and no compatibility alias remains.
- Historical references may remain in this ADR, migration plans, and absence/regression tests only.
- Any future compatibility alias proposal requires a new option gate and tests because it would change the selected Option A outcome.

## Alternatives considered

### A. Rename canonical surface to `record-index` — selected

Pros:

- Matches DDD terminology and Record Index Header contract.
- Avoids deleted `context-*` architecture language.
- Makes cache/listing scope clearer: records, not semantic context.

Cons:

- Requires migration of existing CLI/source/docs.
- May need transitional alias handling for synced hosts.

### B. Keep `context-index`

Pros:

- Smaller code change.
- Existing command already exists.

Cons:

- Keeps obsolete architecture language.
- Makes future agents more likely to reintroduce context-helper semantics.

Rejected.

### C. Remove `context-index` immediately and add only `record-index`

Pros:

- Cleanest final state.

Cons:

- Higher sync/compatibility risk.
- Larger implementation step than SCR-401 should decide.

Selected in SCR-402 and implemented as the active outcome.

### D. Skip naming decision and start record-audit warnings

Pros:

- Avoids immediate cache naming work.

Cons:

- Leaves parser/cache naming ambiguity unresolved.

Rejected because parser/cache work should not proceed with ambiguous names.

## Consequences

- SCR-401 can move to done.
- SCR-402 can move from blocked to todo/planned implementation work, but code changes remain not started.
- Future SDD/TDD/schema/CLI/docs should say canonical `record-index`, not canonical `context-index`.
- The implementation must prove no raw-message query input and no semantic authority outputs.
- If SCR-402 chooses to keep `context-index` temporarily, it is compatibility/deprecated only.

## Implementation map

- Status: `decision-only`
- Primary records:
  - `.lazy-harness/decisions/0042-record-index-cache-naming.md` — this ADR.
  - `.lazy-harness/ssot/cli-tool-boundary.md` — SSOT boundary and SCR-401 decision summary.
  - `.lazy-harness/spec/platform/record-index-header.md` — SDD future parser/cache constraints.
  - `.lazy-harness/tests/record-index-header.md` — TDD future command/no raw-message fixtures.
  - `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` — SCR-401/SCR-402 status.
- Code implementation:
  - none in this ADR commit.
  - implemented files include `.lazy-harness/bin/lazy`, `.lazy-harness/scripts/record-index.ts`, `.lazy-harness/schemas/record-index.schema.json`, `.lazy-harness/generated/README.md`, `.lazy-harness/scripts/self-test.py`, and lazy-sync stale path pruning.
- Protection:
  - existing self-test protects no deleted helper commands and static search/read debt.
  - future SCR-402 tests must protect canonical `record-index`, compatibility alias behavior if any, and no raw-message query.
- Cross-layer links:
  - DDD: `.lazy-harness/domain/searchable-record-memory.md`
  - BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
  - SDD: `.lazy-harness/spec/platform/record-index-header.md`
  - TDD: `.lazy-harness/tests/record-index-header.md`
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
  - Planning: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- Machine index:
  - graph ids: `kg_record_index_name_adr_0042`, `kg_record_index_canonical_name_bounds_scr402`

## Layer completeness impact

- DDD: existing terminology already supports Record Index naming; no DDD change required now.
- BDD: existing LLM-owned retrieval scenarios still apply; no BDD change required now.
- SDD: updated to make canonical future cache/listing name `record-index`.
- TDD: updated to reserve canonical-name/compatibility/no-message fixtures.
- ADR: this record captures the naming trade-off.
- SSOT: updated to record canonical name and boundary.
- Planning: SCR-401 done; SCR-402 unblocked as implementation planning/work.

## Rule placement

- Rule: canonical naming and compatibility trade-off for future cache/listing command belongs in ADR because it records a design choice between alternatives.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0042-record-index-cache-naming.md`
- Why not SSOT only: the SSOT states the boundary, but the naming trade-off and rejected alternatives need an ADR.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private wiring.
- Confirmation: user selected Option A on 2026-06-06.

## Discovery capture

- DDD: no change; existing `.lazy-harness/domain/searchable-record-memory.md` terms support decision.
- BDD: no change; existing `.lazy-harness/behavior/llm-owned-record-retrieval.md` scenarios remain binding.
- SDD: updated in `.lazy-harness/spec/platform/record-index-header.md`.
- TDD: updated in `.lazy-harness/tests/record-index-header.md`.
- ADR: updated by this record.
- SSOT: updated in `.lazy-harness/ssot/cli-tool-boundary.md`.
- Planning: updated in `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` and implementation plan.
