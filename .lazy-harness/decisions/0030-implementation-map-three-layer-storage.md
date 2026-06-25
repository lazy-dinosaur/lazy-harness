# ADR 0030 — Implementation Map Three-Layer Storage

Status: accepted
Date: 2026-05-13

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Applies when:
  - writing or updating an implemented DDD/SDD/BDD/TDD/ADR/SSOT record
  - recording how an implementation works and which files/symbols matter
  - designing machine-readable knowledge or generated retrieval caches
- Must:
  - include a concise `Implementation map` (files, key symbols, flow, tests, cross-layer links) in implemented records
  - store confirmed file/symbol/edge facts in `knowledge/graph.jsonl` as the canonical machine backbone
  - treat `generated/implementation-index.json` as a derived, rebuildable cache, not canonical truth
  - take symbol names from verified source inspection, not loose regex inference
- Must not:
  - replace human-readable records with JSON
- Record completion:
  - implementation-map structure changes update this ADR plus the implementation-map SDD and storage SSOT
- Related records:
  - `.lazy-harness/spec/platform/implementation-map-standard.md`
  - `.lazy-harness/ssot/implementation-map-storage.md`
  - `.lazy-harness/planning/scr-601-implementation-map-needs-map.md`

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

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/implementation-map-standard.md` — Markdown implementation-map contract.
  - `.lazy-harness/ssot/implementation-map-storage.md` — storage/source-of-truth policy for Markdown, graph JSONL, and generated cache.
  - `.lazy-harness/knowledge/graph.jsonl` — canonical machine-readable implementation graph facts.
  - `.lazy-harness/schemas/implementation-index.schema.json` — schema for the derived implementation index cache.
  - `.lazy-harness/scripts/implementation-map-audit.ts` — read-only audit that finds records needing implementation maps.
  - `.lazy-harness/generated/implementation-index.json` — derived cache, not canonical truth.
- Key symbols:
  - `auditRecord`, `audit`, `summarize` (`implementation-map-audit.ts`) — dynamic implementation-map migration audit.
  - `printMarkdown`, `printJcodePrompt` (`implementation-map-audit.ts`) — read-only migration guidance renderers.
- Flow:
  1. Humans/agents write canonical implementation maps in Markdown records.
  2. Confirmed file/symbol/edge facts are also stored in `knowledge/graph.jsonl`.
  3. Generated caches under `.lazy-harness/generated/` may be rebuilt and are never canonical truth.
  4. `lazy impl-map` scans current records dynamically to identify missing maps for migration.
- Tests / protection:
  - `lazy impl-map --format=json` validates the dynamic audit output.
  - `lazy graph-hygiene --format=json` validates JSONL graph health.
  - `python3 .lazy-harness/scripts/self-test.py` protects graph-hygiene CLI, record-index graph IDs, and implementation-map related records through broader self-test coverage.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
  - Planning: `.lazy-harness/planning/scr-601-implementation-map-needs-map.md`
- Machine index:
  - graph ids: `kg_adr0030_impl_map_standard`, `kg_adr0030_impl_map_audit`
  - generated index key: `.lazy-harness/generated/implementation-index.json`
