# TDD — Graph Query Prototype

Status: accepted
Date: 2026-06-08
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/graph-query.md`
Related DDD: `.lazy-harness/domain/searchable-record-memory.md`
Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
Related SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related Planning: `.lazy-harness/planning/graph-query-prototype-implementation-plan.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - implementing or changing `lazy graph query`
  - changing graph query output, record-index inputs, graph JSONL handling, or dispatcher/help wiring
  - evaluating whether Graphify-style deep query prototype remains cue-only and non-canonical
- Must:
  - protect mapped, partial, and gap result states
  - protect DDD/BDD/SDD/TDD/SSOT related-record candidate surfacing
  - protect compact subgraph nodes/edges with provenance/citations
  - protect payload compactness so `--limit` bounds seeds/subgraph/citations and compact node ids avoid repeating full paths in edge endpoints
  - protect fallback command output for gaps/partials
  - protect no semantic-authority fields recursively
  - protect read-only behavior: no canonical record, graph, generated cache, runtime journal, or user memory mutation
  - protect help/dispatcher wiring for `lazy graph query`
- Must not:
  - allow explain/MCP/daemon/lifecycle behavior in the query/path prototype boundary
  - allow required-read, optional-read, confidence, intent, risk, gate, next-action, or candidate-meaning fields
  - treat graph query output as proof of evidence read
- Record completion:
  - implementation changes update this TDD, SDD, self-test, source, CLI help, graph rows, manifest sync entries, and benchmark evidence.
  - Slice 1 completion is source+test verified; benchmark evidence remains a follow-up before larger retrieval policy changes.

## Fixture matrix

| Fixture id | Scenario | Expected |
|---|---|---|
| `graph_query_mapped_retrieval_audit` | Query hits a retrieval audit SDD with related DDD/BDD/SSOT/TDD and graph row | `resultState=mapped`; candidates include DDD/BDD/SDD/TDD/SSOT records, source/test files, graph id, and citations |
| `graph_query_related_expansion_depth_1` | Seed record declares top-level Related layer records and implementation hints | output includes 1-hop related records and provenance edges, capped deterministically by `--limit` |
| `graph_query_gap` | Query has no structural match | `resultState=gap`; `no-seeds` and fallback commands present |
| `graph_query_partial` | Query matches records but lacks source/test or graph candidates | `resultState=partial`; structural gaps identify missing candidate categories |
| `graph_query_no_semantic_fields` | Any JSON output | forbidden semantic-authority fields absent recursively |
| `graph_query_read_only` | Running graph query in temp host | canonical records, graph JSONL, generated caches, and runtime files remain unmodified |
| `graph_query_help_and_dispatcher` | `lazy help` and `lazy graph query` | help advertises graph query; dispatcher routes through `.lazy-harness/scripts/graph-query.ts` |
| `graph_query_payload_compactness` | Source query `retrieval coverage audit` with JSON `--limit=20` | payload is materially below the slice-1 61,004-byte baseline, keeps DDD/BDD/SDD/TDD/SSOT candidates, caps seeds/nodes/edges/citations by `--limit`, and emits no edge endpoint containing a full `.lazy-harness/` path |
| `graph_query_layer_bridge_coverage` | Source query `workflow compression not safety reduction` with JSON `--limit=8` | candidates include DDD, BDD, SDD, TDD, and SSOT record paths by using verified bridge/protection records, while no forbidden semantic-authority fields appear |
| `graph_query_workflow_benchmark_coverage` | `lazy retrieval-workflow-benchmark --format=json --limit=8` | `graph_query` full layer coverage improves beyond the 1/4 baseline and total estimated tokens remain below `map_plus_retrieval_audit` |

## Self-test design

Add `check_graph_query_cli()` to `.lazy-harness/scripts/self-test.py` near record-index and retrieval-audit tests.

The fixture host must include:

- `.lazy-harness/domain/searchable-record-memory.md`
- `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- `.lazy-harness/spec/graph-query.md` or retrieval-like SDD fixture with top-level `Related DDD/BDD/SSOT/TDD`
- `.lazy-harness/ssot/cli-tool-boundary.md`
- `.lazy-harness/tests/graph-query.md`
- `.lazy-harness/knowledge/graph.jsonl` row linking the SDD to source/test implementation
- optional `.lazy-harness/generated/implementation-index.json` entry for a symbol/file citation

Required self-test assertions:

1. `lazy help` contains `graph query <term-or-file>`.
2. `.lazy-harness/scripts/graph-query.ts` exists.
3. `lazy graph query 'retrieval coverage audit' --format=json --limit=20` returns:
   - `mode = graph-query.query`
   - `resultState = mapped`
   - DDD/BDD/SDD/TDD/SSOT candidate record paths
   - source and test candidates
   - graph id citation
   - at least one subgraph node and edge
4. `lazy graph query 'zzzz-missing-token' --format=json` returns `gap` and fallback commands.
5. `lazy graph query 'orphan graph fixture' --format=json` returns `partial` with missing category gaps.
6. Recursive forbidden-key check passes for mapped/partial/gap outputs.
7. Running graph query does not write/modify generated record-index cache or canonical graph JSONL in the temp host.
8. `lazy graph path` and `lazy graph explain` are separate cue-only commands and must not alter graph query output semantics.
9. Markdown output contains cue-only / read real evidence warning.
10. Source benchmark query `lazy graph query 'retrieval coverage audit' --format=json --limit=20` stays compact relative to the 61,004-byte slice-1 baseline without losing five-layer candidate coverage.
11. Source query `lazy graph query 'workflow compression not safety reduction' --format=json --limit=8` returns DDD/BDD/SDD/TDD/SSOT record candidates.
12. Workflow benchmark `graph_query` full layer coverage improves from the 1/4 baseline without losing its token win over `map_plus_retrieval_audit`.

## Validation commands

Focused validation:

```bash
bun .lazy-harness/scripts/graph-query.ts --root "$PWD" query 'retrieval coverage audit' --format=json --limit=20
.lazy-harness/bin/lazy graph query 'retrieval coverage audit' --format=md --limit=20
python3 -m py_compile .lazy-harness/scripts/self-test.py
```

Full validation:

```bash
python3 .lazy-harness/scripts/self-test.py --scope framework
```

Benchmark validation after correctness:

```bash
# compare raw full record read vs lazy map/retrieval-audit vs lazy graph query token/tool/latency/missing-layer metrics
```

Payload compactness acceptance:

- `retrieval coverage audit` JSON `--limit=20` should be below 40,000 bytes in the current source checkout after slice-2 optimization.
- `seeds.length <= limit`, `subgraph.nodes.length <= limit`, `subgraph.edges.length <= limit`, and `citations.length <= limit`.
- Edge `source`/`target` ids should be compact ids, not full record/source/test paths; full paths remain in nodes/candidates/citations.
- This compactness threshold is a benchmark guard, not a lifecycle/prompt policy gate.

Layer coverage hardening acceptance:

- Coverage bridge records must be existing canonical records, not generated placeholder records.
- DDD/BDD bridge candidates may use the generic retrieval-boundary records because graph query itself is a retrieval helper.
- TDD bridge candidates must come from a matched TDD record or verified protection relation.
- Benchmark improvements are evidence for future discussion only; they do not relax overview/read-debt/lifecycle/prompt policy.

## Implementation map

- Status: verified
- Primary files:
  - `.lazy-harness/spec/platform/graph-query.md` — SDD contract under test.
  - `.lazy-harness/tests/graph-query.md` — this TDD record.
  - `.lazy-harness/scripts/graph-query.ts` — CLI implementation.
  - `.lazy-harness/bin/lazy` — dispatcher/help wiring.
  - `.lazy-harness/scripts/self-test.py` — self-test function `check_graph_query_cli`.
  - `.lazy-harness/scripts/record-index.ts` — input provider.
  - `.lazy-harness/knowledge/graph.jsonl` — graph row input.
  - `.lazy-harness/generated/implementation-index.json` — optional generated input.
- Key symbols:
  - `check_graph_query_cli`
  - `buildGraphQuery`
  - `GraphQueryResult`
  - `resultState`
- Flow:
  1. Self-test builds a temp host fixture.
  2. Dispatcher invokes graph-query CLI through `lazy graph query`.
  3. Assertions verify mapped/partial/gap states, related layer candidates, source/test/graph citations, no forbidden keys, no mutation, supported path/explain dispatch boundaries, and semantic-authority absence.
- Machine index:
  - graph ids: `kg_graph_query_cli_20260608`, `kg_graph_query_self_test_20260608`, `kg_graph_query_manifest_20260608`, `kg_graph_query_payload_compactness_20260608`, `kg_graph_query_coverage_ranking_hardening_20260608`, `kg_graph_query_coverage_ranking_plan_20260608`

## Layer completeness impact

- DDD: no new terms; existing searchable-record-memory DDD applies.
- BDD: no behavior change in slice 1; graph query is protected as a cue-only retrieval surface.
- SDD: `.lazy-harness/spec/platform/graph-query.md` defines contract.
- TDD: this record and `check_graph_query_cli` protect prototype behavior.
- ADR: no ADR required for additive/read-only prototype; required before path/explain/lifecycle/batch/prompt/runtime changes.
- SSOT: generated/non-canonical and CLI/LLM authority boundaries remain canonical.
- Planning: direction lock remains `.lazy-harness/planning/graph-query-prototype-implementation-plan.md`.

## Rule placement

- Rule: Graph query prototype regression tests must prove cue-only subgraph retrieval, related layer coverage, no semantic authority, no mutation, and slice-boundary enforcement.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/graph-query.md`
- Why not AGENTS.md: this is fixture/test contract detail, not prompt grammar.
- Why not ADR: additive read-only prototype does not decide long-term architecture policy.
- Why not `.jcode`: shared lazy-harness regression behavior, not local/private Jcode wiring.
- Confirmation: user-approved implementation plan.
