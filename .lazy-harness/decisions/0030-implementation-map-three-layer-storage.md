# ADR 0030 — Implementation Map Three-Layer Storage

Status: accepted
Date: 2026-05-13

## Context

User feedback identified a gap in record-as-output behavior: records said what was decided or meant, but did not consistently preserve how the implementation works, which files exist, and which functions/classes/components matter.

Human-readable Markdown alone is not enough for future AI/LSP-style retrieval. Machine-readable implementation facts and a generated search index are also useful, but replacing records with JSON would conflict with lazy-harness' human-readable record principle.

## Decision

Use a three-layer implementation map model:

1. **Markdown layer docs** remain the human-readable report and canonical explanation.
   - Every implemented DDD/SDD/BDD/TDD/ADR/SSOT record should include a concise `Implementation map` section.
2. **`knowledge/graph.jsonl`** stores confirmed machine-readable file/symbol/edge facts.
   - This is the canonical machine backbone for AI search and cross-layer mapping.
3. **`generated/implementation-index.json`** is a derived retrieval cache.
   - It is optimized for AI/LSP/AST/outline lookup and can be regenerated.
   - It is not canonical truth.

## Required implementation-map contents

Layer docs should include, when applicable:

- primary files
- key symbols/functions/classes/components
- implementation flow
- tests/protection
- cross-layer links
- graph ids and generated index key

## Consequences

### Positive

- Humans can read the implementation report without opening many files.
- AI agents can query structured graph facts before guessing from source.
- Future LSP-backed indexing has a clear output target.
- Generated caches can be rebuilt without damaging canonical records.

### Negative / Trade-offs

- Records become slightly longer.
- Agents must maintain two canonical projections: Markdown explanation and graph facts.
- Until the generated indexer exists, `generated/implementation-index.json` may be absent or stale.

### Mitigations

- Markdown `Implementation map` should stay concise.
- Detailed file/symbol edges belong in `knowledge/graph.jsonl`.
- Generated index is explicitly derived and non-canonical.
- Function/symbol names must come from verified source inspection, not loose regex inference.

## Validation

- `AGENTS.md` record-as-output rules reference the implementation map requirement.
- SDD standard: `.lazy-harness/spec/platform/implementation-map-standard.md`
- SSOT storage: `.lazy-harness/ssot/implementation-map-storage.md`
- Schema: `.lazy-harness/schemas/implementation-index.schema.json`
