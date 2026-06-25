# Implementation map storage SSOT

Status: accepted
Layer: SSOT
Related spec: `.lazy-harness/spec/platform/implementation-map-standard.md`
Related ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`

## Rule digest

- Status: active
- Layer: SSOT
- Scope: framework-global
- Applies when:
  - storing or updating implementation maps across Markdown records, graph facts, and the generated index
  - deciding which layer owns an implementation fact or whether the generated index is canonical
- Must:
  - keep Markdown layer docs as the human report with an `Implementation map` section when implementation exists or is planned
  - treat `knowledge/graph.jsonl` as canonical machine-readable facts; prefer supersession over overwrite
  - treat `generated/implementation-index.json` as derived cache, deletable/regenerable, never canonical
  - source function/class/component names from verified inspection (LSP/AST/outline/read), not loose regex
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
  - `.lazy-harness/scripts/implementation-map-audit.ts` — read-only audit and Jcode prompt generator.
  - `.lazy-harness/bin/lazy` — exposes `lazy impl-map` command.
  - `.lazy-harness/schemas/implementation-index.schema.json` — generated index schema.
- Key symbols:
  - `implementation-map-audit.ts:parseArgs` — parses audit options.
  - `implementation-map-audit.ts:audit` — scans layer Markdown records.
  - `implementation-map-audit.ts:printJcodePrompt` — emits migration prompt for Jcode-assisted runs.
- Flow:
  1. Layer docs hold human implementation reports.
  2. `knowledge/graph.jsonl` holds confirmed file/symbol/edge facts.
  3. `generated/implementation-index.json` caches rebuildable AI/LSP retrieval data.
  4. `lazy impl-map` audits host records without editing them.
- Tests / protection:
  - `.lazy-harness/bin/lazy impl-map --format=json` — smoke-validates audit output.
  - `python3 .lazy-harness/scripts/self-test.py` — validates schema metadata and CLI invariants.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
  - SDD: `.lazy-harness/spec/platform/implementation-map-migration.md`
- Machine index:
  - graph ids: `pending`
  - generated index key: `pending until implementation-index generator exists`
