# knowledge/

Progressive knowledge graph storage.

This directory is the machine-readable backbone for reusable lazy-harness knowledge. It complements, but does not replace, human-facing DDD/SDD/BDD/TDD/ADR/SSOT documents.

## Files

| File | Purpose |
|---|---|
| `candidates.jsonl` | Raw reusable knowledge candidates from conversation, code, tests, user corrections, hooks, or manual capture. |
| `graph-drafts.jsonl` | Candidate graph records that are not canonical yet. |
| `graph.jsonl` | Confirmed canonical graph records, including implementation file/symbol/edge facts. |

## Policy

- Candidate/draft capture may be automatic.
- Canonical graph promotion requires explicit confirmation or a future validated safe rule.
- Conflicts create conflict/supersession records, never silent overwrites.
- During `lazy-sync`, JSONL files in `knowledge/` are seed-merged: framework seed rows may be appended if missing, but host-local rows must not be overwritten or pruned.
- Human-facing layer docs remain under `domain/`, `spec/`, `behavior/`, `tests/`, `decisions/`, and `ssot/`.
- Implementation maps use ADR 0030's three-layer model:
  1. Markdown `Implementation map` section in layer docs.
  2. Confirmed file/symbol/edge facts in `graph.jsonl`.
  3. Derived AI/LSP cache in `generated/implementation-index.json`.

See:

- `.lazy-harness/plans/progressive-knowledge-graph-pipeline.md`
- `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
- `.lazy-harness/spec/platform/implementation-map-standard.md`
- `.lazy-harness/ssot/knowledge-graph-storage.md`
- `.lazy-harness/ssot/implementation-map-storage.md`
- `.lazy-harness/decisions/0028-progressive-knowledge-graph-backbone.md`
- `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
