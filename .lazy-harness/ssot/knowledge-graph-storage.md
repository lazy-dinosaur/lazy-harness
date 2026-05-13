# Knowledge graph storage SSOT

Status: proposed
Layer: SSOT
Related spec: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
Related plan: `.lazy-harness/plans/progressive-knowledge-graph-pipeline.md`

## Source of truth paths

These paths are the single source of truth for progressive knowledge graph storage:

| Purpose | Path | Owner | Mutability |
|---|---|---|---|
| Raw candidates | `.lazy-harness/knowledge/candidates.jsonl` | `knowledge-intake.ts` | append-only |
| Graph drafts | `.lazy-harness/knowledge/graph-drafts.jsonl` | `knowledge-intake.ts` / `knowledge-graph.ts` | append-only/dedupe |
| Canonical graph | `.lazy-harness/knowledge/graph.jsonl` | `knowledge-graph.ts` | append-only events, supersession over overwrite |
| Generated implementation index | `.lazy-harness/generated/implementation-index.json` | future LSP/AST/outline indexer | derived, overwrite-on-regenerate |
| Candidate schema | `.lazy-harness/schemas/knowledge-candidate.schema.json` | framework | versioned |
| Graph record schema | `.lazy-harness/schemas/knowledge-graph-record.schema.json` | framework | versioned |
| Implementation index schema | `.lazy-harness/schemas/implementation-index.schema.json` | framework | versioned |

## Invariants

1. `graph.jsonl` is the machine-readable canonical backbone.
2. DDD/SDD/BDD/TDD/ADR/SSOT documents are human-readable projections and explanations.
3. Conversation knowledge may be captured automatically as candidate/draft only.
4. Canonical confirmation requires explicit confirmation or a future auditable safe rule.
5. Conflicts are represented as graph state, not silent overwrites.
6. Supersession preserves old records with `status=superseded` and a `supersedes` link.
7. Blocking source-search hooks are not the primary mechanism; M45 private instructions and graph query are the normal path.
8. Implementation maps use the ADR 0030 three-layer model: Markdown summary, JSONL graph facts, generated implementation index cache.
9. `generated/implementation-index.json` is derived and non-canonical; absence is valid until generated.

## Empty-container tolerance

The following files may be empty JSONL containers during KG-0:

```text
.lazy-harness/knowledge/candidates.jsonl
.lazy-harness/knowledge/graph-drafts.jsonl
.lazy-harness/knowledge/graph.jsonl
```

Empty files are valid and mean no knowledge has been captured yet.
