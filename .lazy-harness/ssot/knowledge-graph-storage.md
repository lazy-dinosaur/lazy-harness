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
7. Blocking source-search hooks are not the primary mechanism; M45 private instructions plus lazy map/find/retrieval-audit and real record/source/test reads are the normal path. Removed graph query/path/explain CLI is not an active path.
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

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/ssot/knowledge-graph-storage.md` — SSOT for candidate/draft/canonical graph paths and mutability.
  - `.lazy-harness/spec/platform/progressive-knowledge-graph.md` — SDD contract for graph records, evidence, links, and retrieval behavior.
  - `.lazy-harness/knowledge/README.md` — host-visible graph store policy.
  - `.lazy-harness/schemas/knowledge-candidate.schema.json` — candidate schema.
  - `.lazy-harness/schemas/knowledge-graph-record.schema.json` — graph record schema.
  - `.lazy-harness/schemas/implementation-index.schema.json` — generated implementation index schema.
- Key symbols:
  - `KnowledgeCandidate` (`.lazy-harness/spec/platform/progressive-knowledge-graph.md`) — candidate contract.
  - `KnowledgeGraphRecord` (`.lazy-harness/spec/platform/progressive-knowledge-graph.md`) — canonical/draft graph contract.
  - `KnowledgeEvidence` (`.lazy-harness/spec/platform/progressive-knowledge-graph.md`) — evidence contract used by graph facts.
  - `KnowledgeLink` (`.lazy-harness/spec/platform/progressive-knowledge-graph.md`) — graph edge/link contract.
- Flow:
  1. Conversation/code/test facts enter `candidates.jsonl` and `graph-drafts.jsonl`.
  2. Confirmed facts append/supersede records in `graph.jsonl`.
  3. Layer docs project human-readable explanations.
  4. Implementation maps add file/symbol edges and optional generated cache references.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` — validates JSONL parse and schema metadata.
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke` — validates schema metadata and ADR/document freshness.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
  - ADR: `.lazy-harness/decisions/0028-progressive-knowledge-graph-backbone.md`
  - ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
- Machine index:
  - graph ids: `pending`
  - generated index key: `pending until implementation-index generator exists`
