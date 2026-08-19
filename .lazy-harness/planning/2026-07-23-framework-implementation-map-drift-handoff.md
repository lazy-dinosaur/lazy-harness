# Planning — Framework implementation-map source/host ownership drift handoff

Status: implemented-source-verified — downstream host sync/audit pending
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

## 2026-08-18 approved direction

After the drift recurred in a Medivance product hotfix session, the user selected **Distribution-aware (Recommended)**. The audit will identify framework-owned records from Category A manifest entries, resolve manifest `targetPath` relocations, treat absent unmapped refs as source-only only for those framework-owned records in an installed host, and preserve strict active-root checks for host-owned records. Syncing every source ref and rewriting every record per host layout were rejected.

## Deferred implementation slice

The earlier follow-up separation is now closed by the approved distribution-aware work unit:
1. **Implemented:** framework-owned/source-only and host-owned/strict semantics are encoded in the SDD/SSOT without per-record path rewrites.
2. **Implemented:** `.lazy-harness/spec/platform/implementation-map-standard.md` and `.lazy-harness/ssot/implementation-map-storage.md` own the contract.
3. **Implemented:** `implementation-map-audit.ts` resolves exact and directory Category A refs only for framework-owned installed records.
4. **Implemented:** manifest `targetPath` relocation wins over stale source-form collisions; missing targets remain drift.
5. **Reviewed by corpus fixture:** source-only package/planning/PRD paths remain source-authored and installed-host-clean.
6. **Implemented:** synthetic fixtures cover source/host mode, sync-marker source safety, directory globs/excludes, collisions, relocation, and genuine missing refs.
7. **Source verified:** focused status-drift tests and full framework regression pass; downstream host sync/audit remains before release closure.

## Acceptance criteria

- Source-root and downstream-host audits produce no false drift for intentionally source-only or manifest-relocated references.
- A genuinely missing reference in its declared verification root still produces `verified-status-files-missing`.
- Framework-owned records remain source-authored and arrive through `lazy sync`; no downstream Category A patch is required.
- The four confirmed records and any additional same-pattern records receive reviewed path classification.
- Existing advisory/non-blocking semantics remain unchanged.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/planning/2026-07-23-framework-implementation-map-drift-handoff.md` — durable framework-source plan and rollout status.
  - `.lazy-harness/scripts/implementation-map-audit.ts` — distribution-aware status-drift audit.
  - `.lazy-harness/scripts/manifest-path-matcher.ts` — shared Category A glob/exclude semantics.
  - `.lazy-harness/scripts/lazy-sync.ts` — sync consumer of the shared matcher.
  - `.lazy-harness/manifests/init-categories.json` — source-to-host exact/directory/`targetPath` ownership map.
  - `.lazy-harness/spec/platform/implementation-map-standard.md` — audit contract.
  - `.lazy-harness/ssot/implementation-map-storage.md` — source/host ownership truth.
  - `.lazy-harness/scripts/self-test.py` — source/installed-host distribution fixtures.
- Key symbols:
  - `loadDistributionContext` / `manifestTargetFor` / `isFrameworkOwnedRecord` / `refState` (`implementation-map-audit.ts`) — resolve installed framework refs without weakening host-owned checks.
  - `isFrameworkSourceRoot` (`implementation-map-audit.ts`) — prevents self-target sync markers from misclassifying the standalone source.
  - `shouldIncludeManifestPath` (`manifest-path-matcher.ts`) — shared exact directory glob/exclude behavior.
  - `check_impl_map_status_drift` (`self-test.py`) — collision, directory, relocation, source-marker, and strict-missing regression matrix.
- Flow:
  1. Framework source authors Category A record refs against the source checkout.
  2. Sync copies or relocates exact/directory items through the manifest and shared matcher.
  3. Installed-host audit identifies framework-owned records from the same manifest.
  4. Mapped refs require their installed target; unmapped refs are not-applicable only for framework-owned installed records.
  5. Host-owned records and standalone source roots retain strict active-root checks.
- Tests / protection:
  - Focused serial framework light suite passed, including status-drift and helper fixtures.
  - Framework standard/full regression passed before downstream deployment.
  - Temporary real `lazy-init` installed-host audit reported zero drift candidates.
  - Downstream Medivance audit remains the final rollout receipt.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
  - TDD: `.lazy-harness/scripts/self-test.py#check_impl_map_status_drift`
  - ADR: none; the user selected the existing ownership-aware direction without a new architectural trade-off.
- Machine index:
  - graph ids: `kg_impl_map_status_drift_cli_20260626`, `kg_impl_map_status_drift_self_test_20260626`, `kg_impl_map_distribution_aware_audit_20260818`, `kg_impl_map_distribution_aware_test_20260818`

## Rule placement

- Rule: installed-host impl-map audits use Category A distribution mappings only for framework-owned records; host-owned records remain strict.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/2026-07-23-framework-implementation-map-drift-handoff.md`
- Why not Medivance canonical records: the affected files are framework-owned Category A copies and must not be patched downstream.
- Confirmation: user selected follow-up separation on 2026-07-23, then selected **Distribution-aware (Recommended)** for implementation on 2026-08-18.

## Discovery capture

- DDD: no independent delta; searchable-record terminology is unchanged.
- SDD: updated in `.lazy-harness/spec/platform/implementation-map-standard.md` with distribution-aware advisory semantics.
- BDD: none because no product-visible workflow changed.
- TDD: updated through source/installed-host regression fixtures in `check_impl_map_status_drift`.
- ADR: none because no new architecture trade-off was introduced.
- SSOT: updated in `.lazy-harness/ssot/implementation-map-storage.md` with source/host ownership truth.
- Planning: updated by this durable framework-source handoff.
