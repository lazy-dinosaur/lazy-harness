# Graph-Inspired Index Migration Considerations

Status: exploratory
Date: 2026-05-15
Related candidate: `.lazy-harness/knowledge/candidates.jsonl` entry `ki_graphify_external_graph_backend_d4313176da`
Confirmed external reference: <https://github.com/safishamsi/graphify>
Related ADR: `.lazy-harness/decisions/0028-progressive-knowledge-graph-backbone.md`
Related ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
Related SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
Related SDD: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`

## Question

If lazy-harness adopts a Graphify-inspired derived index/query system, will migration become difficult?

User-confirmed reference (2026-06-08): Graphify means `safishamsi/graphify`, described by its README as a Claude Code skill that reads files, builds a persistent graph, emits `graphify-out/graph.json`, `graph.html`, wiki/Obsidian outputs, supports query/path/explain commands, incremental update/cache, watch mode, MCP, and claims large token reduction versus rereading raw files.

Source-verified reference (2026-06-08): cloned `https://github.com/safishamsi/graphify` at commit `8a04560bf5d5eaeef8e466bce084270b7f68faae` on branch `v8` into `/tmp/lazy-harness-graphify-20260608T025932Z` and read `README.md`, `pyproject.toml`, `ARCHITECTURE.md`, `docs/how-it-works.md`, `graphify/__main__.py`, `graphify/build.py`, `graphify/export.py`, `graphify/wiki.py`, `graphify/serve.py`, `graphify/watch.py`, `graphify/mcp_ingest.py`, `graphify/querylog.py`, and related tests/search hits.

Verified facts from source:

- Package is `graphifyy` with CLI entrypoint `graphify = graphify.__main__:main`.
- Default output directory is `graphify-out` via `GRAPHIFY_OUT`; README documents `graph.html`, `GRAPH_REPORT.md`, and `graph.json`.
- Architecture pipeline is `detect → extract → build_graph → cluster → analyze → report → export`, with plain dict/NetworkX handoffs and stated side effects outside only `graphify-out/`.
- `graphify-out/cache/` is SHA256 cache; docs state reruns skip unchanged files.
- `graphify.serve` exposes MCP stdio/http query tools over `graph.json`; source implements query scoring, BFS/DFS subgraph rendering, context filters, reload checks, and sanitized output.
- Installed assistant hooks/instructions nudge agents toward `graphify query`, `graphify explain`, and `graphify path` when `graphify-out/graph.json` exists, but this is advisory guidance.
- Export code writes generated graph artifacts and wiki/Obsidian-style outputs; these remain generated navigation/query surfaces for lazy-harness, not canonical records.

## Current migration boundary

Canonical data today:

- `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/**`
- `.lazy-harness/knowledge/graph.jsonl` for confirmed graph facts
- host-specific records stay in the host repo and must not be overwritten by framework sync

Derived/rebuildable data today:

- `.lazy-harness/generated/**`
- future `.lazy-harness/generated/implementation-index.json`
- optional external `graphify-out/**` if ever used

## Migration risks

1. **Derived index accidentally becomes source of truth**
   - Risk: agents trust generated edges more than records.
   - Mitigation: generated index must include `derived: true`, source commit/hash metadata, and stale/fallback behavior.

2. **Schema lock-in**
   - Risk: changing node/edge format requires migrating large generated files.
   - Mitigation: generated index schema changes should prefer rebuild over migration.

3. **Host sync overwrite**
   - Risk: lazy-sync overwrites host-local graph/index data.
   - Mitigation: Category A sync may ship indexer code and schemas only; it must not copy generated host index contents.

4. **Rename/delete drift**
   - Risk: old file nodes remain after refactors.
   - Mitigation: index stores file hashes plus path inventory; rebuild prunes deleted paths and marks stale edges.

5. **Confirmed graph vs generated graph conflict**
   - Risk: generated edge says X, confirmed graph says Y.
   - Mitigation: confirmed graph wins; generated edge becomes candidate/conflict, never silent overwrite.

6. **Cross-project contamination**
   - Risk: one host's graph facts leak into another host.
   - Mitigation: per-project index by default. Global graph is opt-in and must namespace project identity.

7. **OAuth / external service coupling**
   - Risk: if Graphify-style OAuth/remote service becomes required, offline/local framework portability weakens.
   - Mitigation: core indexer remains local/offline; OAuth is optional adapter only.

## Safer architecture

```text
canonical records/code
  ↓ local incremental indexer
.lazy-harness/generated/implementation-index.json
  ↓ query/SearchProvider
source-read fallback when stale/missing
  ↓ user-confirmed promotion only
.lazy-harness/knowledge/graph.jsonl + layer records
```

Graphify-style outputs should therefore be treated as generated navigation/query surfaces unless and until a separate ADR promotes a specific subset into canonical lazy-harness graph facts. The LLM/searcher remains the semantic search engine; Graphify-style CLI output is index/cue/evidence.

## Rule placement

- Rule: `safishamsi/graphify` is the confirmed external reference for Graphify-inspired graph/index migration discussions; any adoption must preserve generated/non-canonical boundary until separately approved.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/graph-index-migration-considerations.md`
- Why not AGENTS.md: this is exploratory architecture/reference context, not a universal operating instruction.
- Why not `.jcode`: this is shared lazy-harness planning knowledge, not local/private Jcode wiring.
- Confirmation: user-confirmed

## Migration strategy

Prefer **rebuild over migrate** for generated data:

1. Keep canonical record migration as the only durable migration path.
2. Version generated index schemas.
3. On schema mismatch, delete/rebuild generated index rather than transform it.
4. Keep graph drafts/candidates append-only and schema-validated.
5. Promote only user-confirmed or code-verified facts to canonical graph.

## Decision pressure

Graphify-inspired internal indexing is attractive for speed, but should only proceed if the first implementation proves:

- generated index is optional and disposable,
- missing/stale index has safe fallback,
- lazy-sync does not move host generated contents,
- query latency improves on a real host such as medivance,
- self-test/doctor catch stale schema and JSON parse errors.

## Discovery capture

- DDD: none.
- SDD: candidate internal indexing contract needed if implemented.
- BDD: none yet.
- TDD: future regression tests needed for stale/missing index fallback and schema rebuild.
- ADR: possible ADR if choosing internal Graphify-inspired indexer over direct Graphify dependency.
- SSOT: implementation-map storage already says generated index is derived/non-canonical.
- Planning: this file captures migration considerations before implementation.

## Implementation map

- Status: `planned`
- Primary files:
  - `.lazy-harness/ssot/implementation-map-storage.md` — current source-of-truth for generated index mutability.
  - `.lazy-harness/spec/platform/progressive-knowledge-graph.md` — current graph/query contract.
  - `.lazy-harness/schemas/implementation-index.schema.json` — existing generated index schema target.
  - future `.lazy-harness/scripts/implementation-index.ts` — possible local incremental indexer.
- Key symbols:
  - future `lazy index build` — rebuild/incremental generated index command.
  - future `lazy index query` — fast query command.
- Flow:
  1. Canonical records/code remain primary.
  2. Indexer creates derived cache.
  3. SearchProvider queries cache first.
  4. Stale/missing/conflicting cache falls back to source and record reads.
- Tests / protection:
  - future self-test fixtures for schema mismatch, file delete, stale hash, and fallback behavior.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0028-progressive-knowledge-graph-backbone.md`
  - ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
  - SDD: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
- Machine index:
  - graph ids: `pending`
  - generated index key: `pending until indexer exists`
