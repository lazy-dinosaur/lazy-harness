# ADR 0028 — Progressive Knowledge Graph Backbone

- **Status**: Accepted
- **Date**: 2026-05-13
- **Related**: ADR 0024 (AI-first framework redesign), ADR 0027 (standalone source-of-truth repository)
- **Plan**: `.lazy-harness/plans/progressive-knowledge-graph-pipeline.md`
- **Spec**: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
- **SSOT**: `.lazy-harness/ssot/knowledge-graph-storage.md`

## Context

Dogfooding showed two gaps:

1. M45 private instruction loading now makes `.jcode/*` rules visible and reliable enough to shape agent behavior without fragile blocking source-search hooks.
2. Knowledge intake Stage 1 can detect reusable knowledge candidates, but it does not yet make those facts durable, queryable, correctable, or connected to validation.

The user goal is a development environment that improves as it is used:

```text
use the harness more
→ capture more accurate project knowledge
→ retrieve it before future work
→ correct stale/wrong knowledge
→ validate against the graph
```

A markdown-only append strategy is insufficient because it is hard for tooling to query, link, validate, and detect conflicts. A blocking-hook strategy is also insufficient because it is brittle, can loop, and fires after the model has already chosen a bad action.

## Decision

Adopt a progressive knowledge graph as the machine-readable backbone for all DDD/SDD/BDD/TDD/ADR/SSOT knowledge.

Key decisions:

1. All DDD/SDD/BDD/TDD/ADR/SSOT knowledge may be represented as graph records with `layer`, `subject`, `predicate`, `object`, `evidence`, `links`, `status`, and `provenance`.
2. Human-facing layer docs remain as projections/explanations, not the only storage form.
3. Conversation and code discoveries may be automatically captured as candidates and graph drafts.
4. Canonical graph confirmation must be explicit unless a future safe rule is separately designed and validated.
5. Incorrect knowledge is corrected through conflict/supersession records, not silent overwrite.
6. M45 private instructions are the primary behavior mechanism for record-first usage.
7. Blocking source-search hooks are not the primary mechanism and should remain removed/minimized.

## Consequences

### Positive

- Future agents can query confirmed graph facts before source guessing.
- Validation can trace DDD → SDD → BDD → TDD → ADR → SSOT relationships.
- Bad or stale knowledge can be detected, marked, and superseded without losing history.
- The harness can improve with use while preserving auditability.

### Negative / Trade-offs

- More schema and CLI surface area must be maintained.
- Confirmation flow adds friction before candidate facts become canonical.
- Graph records and human-readable docs can drift unless projection/validation is implemented.

## Implementation order

1. KG-0: create storage directories, JSONL containers, schemas.
2. KG-1: extend `knowledge-intake.ts --capture` to append candidates and graph drafts.
3. KG-2: confirm/reject candidates into canonical graph.
4. KG-3: conflict detection and supersession.
5. KG-4: graph query/context output.
6. KG-5: projection into DDD/SDD/BDD/TDD/ADR/SSOT docs.
7. KG-6: M45 private rule integration.
8. KG-7: validation graph integration.

## Non-negotiable invariants

- `--plan` writes nothing.
- `--capture` never writes canonical graph.
- confirmed graph records are append/supersede, not overwritten.
- ambiguous layer selection produces A/B/C/D/custom ask.
- JSONL stores must parse under doctor/self-test.
- Medivance dogfooding must pass after framework sync.
