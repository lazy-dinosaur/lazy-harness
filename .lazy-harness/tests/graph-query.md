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
  - protect fallback command output for gaps/partials
  - protect no semantic-authority fields recursively
  - protect read-only behavior: no canonical record, graph, generated cache, runtime journal, or user memory mutation
  - protect help/dispatcher wiring for `lazy graph query`
- Must not:
  - allow path/explain/MCP/daemon/lifecycle behavior in prototype slice 1
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
| `graph_query_slice_boundary` | User tries `lazy graph path` or `lazy graph explain` in slice 1 | command fails with explicit unsupported-in-prototype message |

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
8. `lazy graph path` and `lazy graph explain` fail explicitly in slice 1.
9. Markdown output contains cue-only / read real evidence warning.

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
  3. Assertions verify mapped/partial/gap states, related layer candidates, source/test/graph citations, no forbidden keys, no mutation, and unsupported path/explain boundary.
- Machine index:
  - graph ids: `kg_graph_query_cli_20260608`, `kg_graph_query_self_test_20260608`, `kg_graph_query_manifest_20260608`

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
