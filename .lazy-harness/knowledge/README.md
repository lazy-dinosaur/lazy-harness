# knowledge/

Progressive knowledge graph storage.

This directory is the machine-readable backbone for reusable lazy-harness knowledge. It complements, but does not replace, human-facing DDD/SDD/BDD/TDD/ADR/SSOT documents.

## Files

| File | Purpose |
|---|---|
| `candidates.jsonl` | Raw reusable knowledge candidates from conversation, code, tests, user corrections, hooks, or manual capture. |
| `graph-drafts.jsonl` | Candidate graph records that are not canonical yet. |
| `graph.jsonl` | Confirmed canonical graph records. |

## Policy

- Candidate/draft capture may be automatic.
- Canonical graph promotion requires explicit confirmation or a future validated safe rule.
- Conflicts create conflict/supersession records, never silent overwrites.
- Human-facing layer docs remain under `domain/`, `spec/`, `behavior/`, `tests/`, `decisions/`, and `ssot/`.

See:

- `.lazy-harness/plans/progressive-knowledge-graph-pipeline.md`
- `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
- `.lazy-harness/ssot/knowledge-graph-storage.md`
- `.lazy-harness/decisions/0028-progressive-knowledge-graph-backbone.md`
