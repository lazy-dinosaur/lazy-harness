# SDD — Graph Path

Status: accepted
Date: 2026-06-08
Layer: SDD
Related SDD: `.lazy-harness/spec/platform/graph-query.md`
Related TDD: `.lazy-harness/tests/graph-path.md`
Related Planning: `.lazy-harness/planning/graph-path-implementation-plan.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related ADR: `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md`
Related evidence: `.lazy-harness/evidence/2026-06-08-graph-query-coverage-ranking-hardening.md`
Related evidence: `.lazy-harness/evidence/2026-06-08-graph-path-downstream-sync.md`
Related evidence: `.lazy-harness/evidence/2026-06-08-graph-path-portability-sync.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - implementing or changing `lazy graph path`
  - using existing graph-query nodes/edges to show bounded paths between two terms or files
  - porting Graphify-style `path` behavior into lazy-harness without vendoring Graphify
- Must:
  - remain additive, read-only, cue-only, deterministic, and TypeScript/Bun based
  - reuse existing inputs only: record-index, `.lazy-harness/knowledge/graph.jsonl`, feature navigation, and optional generated implementation index
  - return compact bounded paths with nodes, edges, endpoint candidates, citations, fallback commands, and explicit cue-only notes
  - cap path search by `--max-depth`, `--limit`, and `--max-paths`
  - preserve the LLM/searcher as semantic authority; graph path output is navigation evidence only
  - include no `requiredRead`, `optionalRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, or `candidateMeanings` fields
- Must not:
  - expand `lazy graph explain` beyond its separate SDD/TDD/plan slice, or add MCP, daemon, watch mode, or prompt/reminder injection
  - relax overview/read-debt/lifecycle/prompt/option-gate policy
  - treat a path as proof that evidence was read or as proof of causality
  - invent edges that are not already present in query subgraphs or confirmed/generated indexes
  - mutate canonical records, graph JSONL, generated caches, runtime journals, or user memory
- Record completion:
  - source changes update this SDD, related TDD, plan, `graph-query.ts`, dispatcher/help text if needed, self-test, graph rows, manifest sync entries, evidence, and downstream sync verification together.

## CLI contract

Command:

```bash
.lazy-harness/bin/lazy graph path '<from>' '<to>' [--format=json|md] [--limit=N] [--max-depth=N] [--max-paths=N]
```

Arguments:

- `<from>`: term, record path, source/test path, or graph node label cue.
- `<to>`: term, record path, source/test path, or graph node label cue.

Flags:

- `--format=json|md` — default `md`.
- `--limit=N` — caps endpoint candidate searches and displayed paths; default `8`.
- `--max-depth=N` — bounded BFS depth; default `4`, max `6` in this slice.
- `--max-paths=N` — number of paths to return; default `3`, max `10` in this slice.
- `--fresh` — accepted for parity with `graph query`, but must not write generated caches.

Unsupported in this path slice:

- graph explain Markdown/path-backed statements unless the separate graph-explain records say otherwise
- daemon/MCP/watch mode
- prompt/reminder packet injection

## Output shape

JSON output must include:

- `mode: graph-query.path`
- `from`
- `to`
- `resultState: linked | partial | gap`
- `coverage.gaps`: structural gaps only, e.g. `no-from-candidates`, `no-to-candidates`, `no-paths`
- `endpoints.fromCandidates`
- `endpoints.toCandidates`
- `paths`: array of compact bounded paths
  - each path has `nodes`, `edges`, `length`, and `provenance`
- `subgraph.nodes`
- `subgraph.edges`
- `citations`
- `fallback`
- `notes`

Path node fields:

- `id`
- `kind`
- `label`
- `path` when available
- `provenance`

Path edge fields:

- `source`
- `target`
- `relation`
- `provenance`

## Semantics

`lazy graph path` is a bounded graph navigation helper. It answers:

> “Which indexed/cited edges connect these two cues?”

It does **not** answer:

- what the user means,
- what must be read,
- whether the connection is semantically sufficient,
- whether one node causes another,
- or what the next action should be.

It explicitly **does not satisfy read evidence**; agents must still read real records/source/tests before relying on any path.

## Path search model

Implementation should:

1. Build endpoint candidate subgraphs by running the existing graph-query builder for `<from>` and `<to>`.
2. Merge nodes/edges from both bounded cue subgraphs.
3. Reinforce endpoint record-to-record edges from record-index related records and implementation hints so direct endpoint links are not lost when query subgraph edge output is capped.
4. Add confirmed graph JSONL / implementation-index edges that touch candidate nodes when already represented in graph-query output.
5. Run deterministic bounded BFS over compact node ids with immediate target-neighbor detection.
6. If direct/indexed BFS finds no path, add `candidate_context` fallback edges only when one endpoint path already appears in the other endpoint's graph-query candidate packet. This is cue-only portability support for hosts that have source graph rows but not every source record file.
7. Return shortest paths first, then stable lexicographic tie-breakers.
8. If no path exists, return endpoint candidates plus fallback commands, not a semantic conclusion.

## Implementation map

- Status: implemented
- Primary files:
  - `.lazy-harness/spec/platform/graph-path.md` — this SDD.
  - `.lazy-harness/tests/graph-path.md` — regression contract.
  - `.lazy-harness/planning/graph-path-implementation-plan.md` — implementation plan.
  - `.lazy-harness/scripts/graph-query.ts` — implements `lazy graph path` parser, bounded path builder, BFS, JSON output, and Markdown rendering.
  - `.lazy-harness/bin/lazy` — advertises graph path and routes graph subcommands to graph-query.ts.
  - `.lazy-harness/scripts/self-test.py` — regression fixture and read-only/no-semantic-field protection.
- Key symbols:
  - `GraphPathResult`
  - `buildGraphPath`
  - `reinforceEndpointRecordEdges`
  - `addCandidateOverlapEdges`
  - `findBoundedPaths`
  - `renderPathMarkdown`
  - `parseArgs`
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework` and focused `check_graph_path_cli` protect the contract.
- Machine index:
  - graph id: `kg_graph_path_cli_20260608`

## Layer completeness impact

- DDD: no new domain entity; existing searchable record memory applies.
- BDD: no user behavior automation change; LLM-owned retrieval boundary applies.
- SDD: this record defines graph path contract.
- TDD: `.lazy-harness/tests/graph-path.md` and self-test protect behavior.
- ADR: no new ADR because path is an approved Graphify-inspired next slice, not a policy change.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains controlling.
- Planning: `.lazy-harness/planning/graph-path-implementation-plan.md` tracks execution.

## Rule placement

- Rule: `lazy graph path` is a read-only graph-navigation helper, not a semantic authority or policy relaxation.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/graph-path.md`
- Why not AGENTS.md: CLI output contract and implementation details belong in SDD/TDD/source, not always-loaded prompt grammar.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private Jcode-only wiring.
- Confirmation: user-confirmed option A
