# Implementation map storage SSOT

Status: accepted
Layer: SSOT
Related spec: `.lazy-harness/spec/platform/implementation-map-standard.md`
Related ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`

## Rule digest

- Status: active
- Layer: SSOT
- Scope: framework-global
- Aliases:
  - 임플맵 저장 위치
  - 어디에 매핑
  - graph 저장소
- Applies when:
  - storing or updating implementation maps across Markdown records, graph facts, and the generated index
  - deciding which layer owns an implementation fact or whether the generated index is canonical
- Must:
  - keep Markdown layer docs as the human report with an `Implementation map` section when implementation exists or is planned
  - treat `knowledge/graph.jsonl` as canonical machine-readable facts; prefer supersession over overwrite
  - treat `generated/implementation-index.json` as derived cache, deletable/regenerable, never canonical
  - source function/class/component names from verified inspection (LSP/AST/outline/read), not loose regex
  - author framework-owned Category A implementation references against the framework source checkout; in installed hosts, resolve manifest `targetPath` relocations and treat intentionally non-distributed source refs as not applicable only for those framework-owned records
  - keep host-owned records strict against the active host root; distribution awareness must never suppress a genuinely missing host-owned implementation path
- Must not:
  - let framework sync overwrite host implementation maps or generated index data
- Record completion:
  - storage-path or mutability changes update this SSOT plus `spec/platform/implementation-map-standard.md` and ADR 0030
- Related records:
  - `.lazy-harness/spec/platform/implementation-map-standard.md`
  - `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`

## Source of truth paths

| Purpose | Path | Owner | Mutability |
|---|---|---|---|
| Human implementation summaries | `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/**/*.md` | AI + user-confirmed record workflow | narrow append/update |
| Canonical implementation graph facts | `.lazy-harness/knowledge/graph.jsonl` | `knowledge-graph.ts` / confirmed manual updates | append-only events, supersession over overwrite |
| Draft implementation graph facts | `.lazy-harness/knowledge/graph-drafts.jsonl` | `knowledge-intake.ts` / future implementation indexer | append-only/dedupe |
| Generated implementation index | `.lazy-harness/generated/implementation-index.json` | future LSP/AST/outline indexer | derived, overwrite-on-regenerate |
| Generated index schema | `.lazy-harness/schemas/implementation-index.schema.json` | framework | versioned |

## Invariants

1. Markdown layer docs are the human-readable report and must include an `Implementation map` section when implementation exists or is planned.
2. `knowledge/graph.jsonl` is the canonical machine-readable graph for confirmed file/symbol/edge facts.
3. `generated/implementation-index.json` is not canonical. It is an AI/LSP retrieval cache and may be deleted/regenerated.
4. Function/class/component names must come from verified source inspection such as LSP, AST, outline, or direct file read. Do not infer by loose regex alone.
5. If generated index conflicts with Markdown or graph records, inspect source and then update/supersede the graph or mark the generated index stale.
6. Host-specific implementation maps belong to the host `.lazy-harness`; framework sync must not overwrite host records or generated implementation index data.
7. Framework-owned Category A records keep source-checkout implementation paths as canonical authoring truth; they are not rewritten per downstream layout.
8. In an installed host, `lazy impl-map` identifies framework-owned records and source-to-target relocations from `.lazy-harness/manifests/init-categories.json`. A mapped target must exist; an unmapped source-only ref is not applicable to that host audit.
9. Host-owned records do not receive this exemption: their clean Primary/Future paths remain strict active-host existence checks.

## Empty / missing index tolerance

`generated/implementation-index.json` may be absent until an indexer exists or has run.

When absent, agents should:

1. use Markdown record `Implementation map` sections,
2. query/read `knowledge/graph.jsonl`,
3. inspect source via search/LSP/outline,
4. only then update records.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/ssot/implementation-map-storage.md` — SSOT for ADR 0030 storage paths and mutability rules.
  - `.lazy-harness/spec/platform/implementation-map-standard.md` — SDD standard for the three-layer implementation-map contract.
  - `.lazy-harness/spec/platform/implementation-map-migration.md` — migration/audit guide for existing host records.
  - `.lazy-harness/scripts/implementation-map-audit.ts` — read-only distribution-aware audit and agent prompt generator.
  - `.lazy-harness/scripts/manifest-path-matcher.ts` — canonical Category A glob/exclude matcher shared with sync.
  - `.lazy-harness/scripts/lazy-sync.ts` — Category A copy/prune consumer of the shared matcher.
  - `.lazy-harness/bin/lazy` — exposes `lazy impl-map` command.
  - `.lazy-harness/schemas/implementation-index.schema.json` — generated index schema.
- Key symbols:
  - `parseArgs` (`.lazy-harness/scripts/implementation-map-audit.ts`) — parses audit options.
  - `loadDistributionContext` / `manifestTargetFor` / `refState` / `isFrameworkSourceRoot` (`.lazy-harness/scripts/implementation-map-audit.ts`) — resolves exact/directory Category A ownership, target relocation, source-marker safety, and strict host-owned checks.
  - `shouldIncludeManifestPath` (`.lazy-harness/scripts/manifest-path-matcher.ts`) — shared glob/exclude authority.
  - `auditRecord` / `audit` (`.lazy-harness/scripts/implementation-map-audit.ts`) — scans layer records and computes distribution-aware advisory drift.
  - `printAgentPrompt` (`.lazy-harness/scripts/implementation-map-audit.ts`) — emits migration prompts.
- Flow:
  1. Layer docs hold human implementation reports.
  2. `knowledge/graph.jsonl` holds confirmed file/symbol/edge facts.
  3. `generated/implementation-index.json` caches rebuildable AI/LSP retrieval data.
  4. `lazy impl-map` audits source/installed-host records without editing them and uses the Category A manifest only to interpret framework-owned distribution paths.
- Tests / protection:
  - `.lazy-harness/bin/lazy impl-map --format=json` — smoke-validates audit output.
  - `.lazy-harness/scripts/self-test.py#check_impl_map_status_drift` — validates source strictness, installed-host source-only/relocated refs, and genuine mapped/host-owned missing refs.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
  - SDD: `.lazy-harness/spec/platform/implementation-map-migration.md`
- Machine index:
  - graph ids: `kg_impl_map_distribution_aware_audit_20260818`, `kg_impl_map_distribution_aware_test_20260818`
  - generated index key: `pending until implementation-index generator exists`

## Discovery capture — distribution-aware host audit

- DDD: none because implementation-map vocabulary is unchanged.
- SDD: updated in `.lazy-harness/spec/platform/implementation-map-standard.md` with manifest-aware installed-host audit semantics.
- BDD: none because no product-visible workflow changed; only advisory accuracy changed.
- TDD: updated through `.lazy-harness/scripts/self-test.py#check_impl_map_status_drift` with source/installed-host distribution fixtures.
- ADR: none because the user selected the already-planned ownership-aware direction without introducing a new storage architecture.
- SSOT: updated here because source-checkout ownership, installed `targetPath` resolution, and strict host-owned boundaries are canonical storage/path truth.
- Planning: updated in `.lazy-harness/planning/2026-07-23-framework-implementation-map-drift-handoff.md`.
