# Jcode Graph Memory Tool Integration

Status: exploratory
Date: 2026-05-15
Related candidate: `.lazy-harness/knowledge/candidates.jsonl` entries `ki_graphify_external_graph_backend_d4313176da`, `ki_jcode_session_graph_context_2532d74e13`
Related ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
Related ADR: `.lazy-harness/decisions/0028-progressive-knowledge-graph-backbone.md`
Related SSOT: `.lazy-harness/ssot/implementation-map-storage.md`

## User-confirmed correction

The intended Jcode integration is **not** to inject the whole graph into every session.

The intended structure is:

```text
Jcode session
  → receives a graph/search tool
  → queries an external/per-project brain memory device on demand
  → receives only the relevant subgraph/context for the current task
```

In the user's words: give Jcode a search tool and brain/memory device, not the full graph contents.

## Design implication

The graph/index should behave like an external memory subsystem:

- persistent per project,
- queryable through tools,
- compact result output,
- citation/evidence aware,
- stale-safe with source fallback,
- separate from canonical records.

## Non-goals

- Do not paste full `graph.json` or `implementation-index.json` into session context.
- Do not make generated index canonical truth.
- Do not require OAuth/remote service for local lazy-harness core.
- Do not merge all projects into one un-namespaced memory by default.

## Candidate architecture

```text
.lazy-harness records + source code
  ↓ build/update
per-project memory store
  - .lazy-harness/generated/implementation-index.json
  - optional graph DB / SQLite / graphify-out adapter
  ↓ query tool
Jcode tool: lazy index query / lazy graph query / SearchProvider
  ↓ compact cited results
agent reads only relevant records/files
```

## Tool contract sketch

Potential commands:

```bash
lazy index build              # build/update derived memory
lazy index query "..."        # fast symbol/file/record candidates
lazy graph query "..."        # confirmed graph + candidate context
lazy graph path A B           # relationship/path query
lazy graph explain X          # explain node with citations
```

Potential Jcode integration:

- expose the commands through a skill or tool wrapper,
- session instructions say "query graph memory first when available",
- no large graph payload in prompt,
- result includes paths, record ids, confidence, and fallback suggestions.

## Migration stance

This design keeps migration manageable because:

- canonical records migrate,
- memory/index stores rebuild,
- generated schemas can change by rebuild rather than data migration,
- per-project namespace prevents cross-host contamination.

## Discovery capture

- DDD: none.
- SDD: graph memory tool contract candidate.
- BDD: future agent behavior: query memory before broad source search.
- TDD: future tests for query result compactness, stale fallback, and no full-graph prompt injection.
- ADR: possible decision if adopting tool-backed memory over session-context injection.
- SSOT: implementation-map storage already requires generated index to remain derived.
- Planning: this file records the clarified architecture.

## Rule placement

- Rule: Jcode graph integration should use a queryable memory/search tool, not full graph session injection.
- Scope: framework-global | host-project
- Primary record: `.lazy-harness/planning/jcode-graph-memory-tool-integration.md`
- Why not AGENTS.md: this is an architecture candidate, not universal thin grammar yet.
- Why not `.jcode`: the design affects framework/Jcode integration semantics, not a local-only preference.
- Confirmation: user-confirmed

## Implementation map

- Status: `planned`
- Primary files:
  - future `.lazy-harness/scripts/implementation-index.ts` — build/query local derived memory.
  - future `.lazy-harness/scripts/graph-query.ts` — query graph/candidates with citations.
  - `.lazy-harness/scripts/search-provider.ts` — SearchProvider abstraction target.
  - `.lazy-harness/bin/lazy` — command dispatcher.
- Key symbols:
  - future `lazy index query` — fast search tool for Jcode.
  - future `lazy graph query` — graph-backed memory query.
- Flow:
  1. Session receives tool affordance and small instruction.
  2. Agent queries memory on demand.
  3. Tool returns compact cited subgraph/context.
  4. Agent reads canonical records/source only for confirmation or detail.
- Tests / protection:
  - future self-test for no full graph injection.
  - future query fixtures for stale/missing generated index fallback.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
  - ADR: `.lazy-harness/decisions/0028-progressive-knowledge-graph-backbone.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
- Machine index:
  - graph ids: `pending`
  - generated index key: `pending until memory query tool exists`
