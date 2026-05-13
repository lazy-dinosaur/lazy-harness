# Implementation map storage SSOT

Status: accepted
Layer: SSOT
Related spec: `.lazy-harness/spec/platform/implementation-map-standard.md`
Related ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`

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
