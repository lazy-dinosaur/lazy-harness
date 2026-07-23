# Planning — Framework implementation-map source/host ownership drift handoff

Status: queued-separate-from-placement-rollout
Date: 2026-07-23
Layer: Planning
Source observation: Medivance downstream host

## Rule digest

- Status: active
- Layer: Planning
- Scope: framework-global
- Aliases:
  - implementation-map distribution drift
  - source host path ownership
  - verified-status false positive
  - 임플맵 배포 오탐
- Applies when:
  - a framework-owned Category A record is `verified` in the source checkout but reports missing Primary files after downstream sync
  - `lazy impl-map` evaluates source-only package/planning/PRD paths or manifest-relocated framework ADRs from a host root
- Must:
  - distinguish source-checkout references from downstream-host references before changing map status
  - preserve source-verified status when source evidence is present; treat host-only absence as an ownership/path-scope candidate
  - fix the audit contract and regression fixtures in a separate approved work unit
- Must not:
  - demote source records solely because source-only files are intentionally not distributed to hosts
  - patch framework-owned Category A records in a downstream host
- Record completion:
  - ownership-aware path semantics and fixtures update this plan, the Implementation Map SDD/SSOT, affected records, and tests
- Related records:
  - `.lazy-harness/spec/platform/implementation-map-standard.md`
  - `.lazy-harness/ssot/implementation-map-storage.md`
  - `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`

## Confirmed evidence

The Medivance handoff was read from `.lazy-harness/planning/2026-07-23-framework-implementation-map-drift-handoff.md`. That host-local file is ignored/untracked by the product repository, so this framework-source plan is the durable follow-up owner.

Four synced framework records reproduce `verified-status-files-missing` from the Medivance root:

- `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- `.lazy-harness/domain/searchable-record-memory.md`
- `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`
- `.lazy-harness/tests/pre-action-search-evidence-guard.md`

The same four files are byte-identical to the framework source copies at the inspected rollout baseline. Source-root `lazy impl-map --format=json` reports all four clean, and all referenced source files exist there. Host-root `lazy impl-map --format=json` reports the missing-path candidates.

Verified causes:

1. `implementation-map-audit.ts::refExists` resolves only against the active host root plus a `.lazy-harness/` shorthand fallback.
2. `decisions/0034-analysis-discovery-plan-capture-gate.md` is intentionally distributed as `framework/operational-adrs/0034-analysis-discovery-plan-capture-gate.md` via `init-categories.json`.
3. `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` is framework source-package code and is not copied into the product host root.
4. `planning/searchable-record-context-retrieval-tasks.md` and `prd/searchable-record-context-retrieval-prd.md` exist in the framework source but are not Category A distribution items.

## Corrected diagnosis

This evidence does **not** prove that the source implementation maps are stale. It proves that the current advisory audit lacks source-vs-host ownership/path semantics and that some record path classifications are ambiguous after Category A distribution.

Blindly changing all four source statuses from `verified` to `needs-review` would discard valid source-checkout verification. A correct repair must state which root owns/verifies each reference or make the audit manifest/ownership-aware without violating root-bound host retrieval.

## Deferred implementation slice

The user selected **follow-up separation**. This slice is explicitly outside the current project-rule placement and `--skip-knowledge-seeds` rollout.

1. Choose a compact record syntax or metadata rule for downstream-distributed versus framework-source-only implementation references.
2. Update `.lazy-harness/spec/platform/implementation-map-standard.md` and `.lazy-harness/ssot/implementation-map-storage.md` before changing audit behavior.
3. Update `implementation-map-audit.ts` so host audits do not report intentional source-only references as missing while genuine host-path drift remains visible.
4. Reconcile manifest `targetPath` references, especially operational ADRs, without assuming host `decisions/` contains framework ADRs.
5. Audit every Category A framework record that lists `packages/lazy-harness-pi/**`, source-only planning/PRD files, or source-form ADR paths under `Primary files`.
6. Add a synthetic source/host distribution fixture covering source-clean, host-intentional-absence, manifest relocation, and genuine missing-host-file cases.
7. Run focused status-drift tests, framework full regression, and a downstream-host sync/audit fixture before release.

## Acceptance criteria

- Source-root and downstream-host audits produce no false drift for intentionally source-only or manifest-relocated references.
- A genuinely missing reference in its declared verification root still produces `verified-status-files-missing`.
- Framework-owned records remain source-authored and arrive through `lazy sync`; no downstream Category A patch is required.
- The four confirmed records and any additional same-pattern records receive reviewed path classification.
- Existing advisory/non-blocking semantics remain unchanged.

## Implementation map

- Status: `needs-review`
- Primary files:
  - `.lazy-harness/planning/2026-07-23-framework-implementation-map-drift-handoff.md` — durable framework-source backlog and corrected diagnosis.
  - `.lazy-harness/scripts/implementation-map-audit.ts` — current host-root-only path resolver and status-drift audit.
  - `.lazy-harness/manifests/init-categories.json` — source-to-host Category A path and `targetPath` mappings.
  - `.lazy-harness/spec/platform/implementation-map-standard.md` — future ownership/path-scope contract owner.
  - `.lazy-harness/ssot/implementation-map-storage.md` — future source/host ownership storage boundary.
  - `.lazy-harness/scripts/self-test.py` — future synthetic source/host drift fixture.
- Key symbols:
  - `refExists` (`.lazy-harness/scripts/implementation-map-audit.ts`) — currently checks only the active root and `.lazy-harness` shorthand.
  - `extractPrimaryFutureRefs` (`.lazy-harness/scripts/implementation-map-audit.ts`) — selects path tokens from Primary/Future sections without ownership metadata.
  - `auditRecord` (`.lazy-harness/scripts/implementation-map-audit.ts`) — emits `verified-status-files-missing` from unresolved refs.
- Flow:
  1. Framework record is verified in the source checkout.
  2. Category A copies the record, relocates selected ADRs, and omits source-only package/planning/PRD files.
  3. Host `lazy impl-map` resolves every Primary path only against the host root.
  4. Intentional source-only absence becomes a false advisory candidate.
  5. The deferred slice will add explicit ownership semantics and preserve genuine drift detection.
- Tests / protection:
  - Existing `.lazy-harness/scripts/self-test.py#check_impl_map_status_drift` covers only one-root present/missing behavior.
  - New source/host distribution coverage is required before this plan can close.
- Cross-layer links:
  - SDD candidate: `.lazy-harness/spec/platform/implementation-map-standard.md`
  - SSOT candidate: `.lazy-harness/ssot/implementation-map-storage.md`
  - TDD candidate: focused source/host status-drift fixture in `.lazy-harness/scripts/self-test.py` plus a promoted TDD record if the regression contract has an independent delta.
  - ADR: no independent decision yet; use an option gate if ownership syntax requires a new trade-off.
- Machine index:
  - existing graph ids: `kg_impl_map_status_drift_cli_20260626`, `kg_impl_map_status_drift_self_test_20260626`

## Rule placement

- Rule: framework-source implementation-map ownership drift belongs in a framework planning handoff until its SDD/SSOT semantics are separately approved.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/2026-07-23-framework-implementation-map-drift-handoff.md`
- Why not Medivance canonical records: the affected files are framework-owned Category A copies and must not be patched downstream.
- Confirmation: user selected **후속 분리 (Recommended)** on 2026-07-23.

## Discovery capture

- DDD: no independent delta; searchable-record terminology is unchanged.
- SDD: candidate for ownership-aware implementation-map path semantics; deferred to the separate work unit.
- BDD: no independent delta; no product-visible workflow changes.
- TDD: candidate for a source/host distribution regression fixture; deferred with the SDD.
- ADR: none yet; the current diagnosis does not choose a new architecture trade-off.
- SSOT: candidate for source/host verification-root ownership; deferred to the separate work unit.
- Planning: updated by this durable framework-source handoff.
