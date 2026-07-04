# ADR 0028 — Progressive Knowledge Graph Backbone

- **Status**: Accepted
- **Date**: 2026-05-13
- **Related**: ADR 0024 (AI-first framework redesign), ADR 0027 (standalone source-of-truth repository)
- **Plan**: `.lazy-harness/plans/progressive-knowledge-graph-pipeline.md`
- **Spec**: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
- **SSOT**: `.lazy-harness/ssot/knowledge-graph-storage.md`

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Aliases:
  - 지식 그래프
  - knowledge graph
  - graph.jsonl
  - 그래프 백본
  - edge 축적
- Applies when:
  - capturing, querying, correcting, or validating reusable project knowledge
  - designing knowledge-graph storage, candidate capture, or confirmation flow
  - representing DDD/SDD/BDD/TDD/ADR/SSOT facts as machine-readable records
- Must:
  - store knowledge as graph records (layer/subject/predicate/object/evidence/links/status/provenance); human docs are projections
  - require explicit confirmation before candidates become canonical graph facts
  - correct wrong knowledge via conflict/supersession records, not silent overwrite
  - rely on M45 private instructions for record-first behavior, not blocking source-search hooks
- Must not:
  - let `--plan` or `--capture` write the canonical graph, or overwrite confirmed records
- Record completion:
  - graph schema/CLI or storage changes update this ADR plus the knowledge-graph SDD and SSOT records
- Related records:
  - `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
  - `.lazy-harness/ssot/knowledge-graph-storage.md`
  - `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`

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

## Implementation map

- Status: `needs-review`
- Primary files:
  - `.lazy-harness/spec/platform/progressive-knowledge-graph.md` — SDD contract for candidate/draft/canonical graph records and implementation-map extensions.
  - `.lazy-harness/ssot/knowledge-graph-storage.md` — storage SSOT for candidates, graph drafts, canonical graph, and generated indexes.
  - `.lazy-harness/scripts/knowledge-intake.ts` — Stage 1 candidate detector and ask renderer; plan mode is read-only.
  - `.lazy-harness/scripts/graph-hygiene.ts` — read-only graph JSONL/path/id hygiene checker.
  - `.lazy-harness/knowledge/graph.jsonl` — canonical machine-readable graph rows for confirmed implementation facts.
  - `.lazy-harness/scripts/self-test.py` — knowledge-intake and graph-hygiene coverage.
- Key symbols:
  - `candidate`, `detectOne`, `analyze` (`knowledge-intake.ts`) — detect reusable knowledge candidates with confidence/options.
  - `inspect` (`graph-hygiene.ts`) — validates graph JSONL IDs, duplicate/missing IDs, comma-joined paths, and missing paths.
  - `check_knowledge_intake` and `check_graph_hygiene_cli` (`self-test.py`) — executable coverage for candidate detection and graph hygiene.
- Flow:
  1. Knowledge-intake plan mode detects candidate facts and emits ask/JSON output without writing records.
  2. Candidate and graph storage paths are defined by SDD/SSOT records.
  3. `graph.jsonl` stores confirmed implementation facts and is checked by graph-hygiene.
  4. Generated indexes remain derived/non-canonical.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` protects JSONL parse, schema metadata, knowledge-intake fixtures, and graph-hygiene CLI.
  - Keep this map `needs-review` because ADR 0028's later KG stages (promotion, conflict/supersession query/projection) are only partially implemented.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
  - SSOT: `.lazy-harness/ssot/knowledge-graph-storage.md`
  - ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
- Machine index:
  - graph ids: `kg_adr0028_knowledge_intake`, `kg_adr0028_graph_hygiene`, `kg_adr0028_storage_contract`
  - generated index key: `.lazy-harness/generated/implementation-index.json`
