# SDD — Graph Query Prototype

Status: accepted
Date: 2026-06-08
Layer: SDD
Related DDD: `.lazy-harness/domain/searchable-record-memory.md`
Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
Related SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related SDD: `.lazy-harness/spec/platform/record-index-header.md`
Related SDD: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
Related TDD: `.lazy-harness/tests/graph-query.md`
Related Planning: `.lazy-harness/planning/graph-query-prototype-implementation-plan.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - implementing or changing the additive TS/Bun `lazy graph query` prototype
  - using existing record-index / graph JSONL / generated implementation index inputs to produce compact retrieval context
  - evaluating Graphify-style query behavior before path/explain/lifecycle policy changes
- Must:
  - keep the prototype additive, read-only, cue-only, and deterministic
  - use existing inputs only: canonical records through record-index, `.lazy-harness/knowledge/graph.jsonl`, and optional generated implementation index
  - surface compact cited subgraph/context candidates for records, source files, tests, graph rows, and implementation-index hits
  - keep default JSON output compact enough for read-followup workflows by using compact deterministic node ids, capped provenance arrays, and `--limit`-bounded seeds/subgraph/citations
  - include related DDD/BDD/SDD/TDD/SSOT records when linked from matched records
  - preserve layer bridge candidates when a matched retrieval/framework topic has verified DDD/BDD/TDD records that define how retrieval should be interpreted or protected
  - emit fallback commands for gaps/partials
  - cap output by `--limit` and prototype depth by `--depth` max 2
  - state that LLM/searcher remains the semantic authority and must read real evidence
- Must not:
  - replace `lazy map`, `retrieval-audit`, or overview-first behavior
  - relax/remove overview hard block or change lifecycle/prompt reminder behavior
  - vendor Graphify/Python, add Go/Rust, add MCP/daemon, or add persistent service
  - mutate canonical records, generated indexes, runtime journals, or user memory
  - decide user intent, risk, confidence, gates, required reads, next action, or candidate meanings
  - treat graph query output as proof that evidence was read
- Record completion:
  - source changes update this SDD, related TDD, CLI dispatcher/help, self-test, graph rows, manifest sync entries, and benchmark evidence together.
  - Slice 1 completion is source+test verified; benchmark evidence remains a separate follow-up before larger policy changes.

## CLI contract

Command:

```bash
.lazy-harness/bin/lazy graph query '<term-or-file>' --format=json --limit=20 --depth=1
```

Supported flags:

- `--format=json|md` — default `md`
- `--limit=N` — caps records/graph rows/source/test candidates per category; default `8`
- `--depth=N` — graph expansion depth; default `1`, max `2` in prototype slice 1
- `--fresh` — rebuild record-index inputs from canonical records before query

Unsupported in prototype slice 1:

- `lazy graph path`
- `lazy graph explain`
- daemon/MCP server
- prompt/reminder packet injection

## Output shape

JSON output must include:

- `mode: graph-query.query`
- `query`
- `resultState: mapped | partial | gap`
- `coverage.gaps`: structural gaps only, e.g. `no-seeds`, `no-record-candidates`, `no-source-candidates`, `no-test-candidates`, `no-graph-candidates`
- `seeds`: matched records, graph rows, source files, and implementation-index entries with matched fields
- `subgraph.nodes`: deterministic cue-only nodes with `id`, `kind`, `label`, `path`, and `provenance`
- `subgraph.edges`: deterministic cue-only edges with `source`, `target`, `relation`, and `provenance`
- `candidates.recordPaths`
- `candidates.sourceFiles`
- `candidates.testFiles`
- `candidates.graphIds`
- `citations`: record paths, graph row ids, generated index names, and source paths that justify candidates
- `fallback`: overview, lazy map query, retrieval-audit, and grep commands
- `notes`: cue-only / generated-non-canonical / read real evidence reminders

Compactness constraints:

- Node ids should be stable compact identifiers, not full record/source/test paths. Full paths remain available through node `path`, candidates, and citations.
- Source/test node `label` should be a short display label when `path` already carries the full path.
- Per-node and per-edge `provenance` arrays should be capped deterministically; full provenance is a cue, not canonical evidence.
- Default `query --format=json --limit=20` for the source benchmark query `retrieval coverage audit` should target a materially smaller payload than the 2026-06-08 slice-1 baseline of 61,004 bytes while preserving DDD/BDD/SDD/TDD/SSOT candidate coverage.

Forbidden fields anywhere in output:

- `requiredRead`
- `optionalRead`
- `confidence`
- `intent`
- `risk`
- `gate`
- `nextAction`
- `candidateMeanings`

## Behavior

1. LLM/searcher may use `lazy graph query <term>` after the required overview or when evaluating whether deeper traversal can reduce manual token selection.
2. The CLI builds or loads deterministic record-index inputs.
3. The CLI matches query tokens against record metadata, graph rows, feature records, and optional implementation index entries.
4. The CLI expands a compact subgraph from seed nodes up to `--depth`.
5. The CLI emits cited candidates and fallback commands.
6. The LLM/searcher reads the surfaced real records/source/tests before relying on the result.
7. `gap` or `partial` output is not evidence of absence; it is a fallback cue.

## Layer coverage and ranking hardening

Workflow benchmark slice 1 showed `graph_query` was a workflow-cost win but only had full DDD/BDD/SDD/TDD/SSOT follow-up coverage for 1 of 4 benchmark queries. Coverage hardening must therefore improve candidate ordering and related-layer bridge surfacing without making graph query a semantic authority.

Allowed hardening:

- deterministic layer bridge records that are already canonical and relevant to retrieval-helper interpretation, such as:
  - DDD: `.lazy-harness/domain/searchable-record-memory.md`
  - BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- deterministic protection bridge records when query terms match a TDD record title/body or a matched record declares a related TDD/protection record.
- layer-aware ordering that keeps direct matches first, but reserves room inside `--limit` for missing DDD/BDD/TDD/SSOT candidates when they are verified bridges.

Forbidden hardening:

- inventing topic-specific DDD/BDD records that do not exist,
- hiding missing coverage by changing the benchmark metric,
- adding `requiredRead`, `confidence`, `risk`, `intent`, `gate`, `nextAction`, or candidate meaning labels,
- treating bridge records as mandatory proof of evidence read.

Acceptance for coverage hardening:

- `lazy retrieval-workflow-benchmark --format=json --limit=8` should improve `graph_query` full-layer follow-up coverage from the 1/4 baseline while preserving the token win over `map_plus_retrieval_audit`.
- `lazy graph query 'workflow compression not safety reduction' --format=json --limit=8` should include DDD, BDD, SDD, TDD, and SSOT record candidates without forbidden semantic-authority fields.
- Output should stay under the existing source compactness guard for `retrieval coverage audit` JSON `--limit=20`.

## Direction lock

Prototype slice 1 is intentionally narrow:

- Add `lazy graph query` only.
- Do not add `path` or `explain` yet.
- Do not change lifecycle/batch/reminder policy.
- Do not introduce new runtime language or persistent service.
- Benchmark before proposing larger policy changes.

## Implementation map

- Status: verified
- Primary files:
  - `.lazy-harness/scripts/graph-query.ts` — read-only graph query CLI.
  - `.lazy-harness/bin/lazy` — dispatcher/help route for `lazy graph query`.
  - `.lazy-harness/scripts/record-index.ts` — existing deterministic record-index input.
  - `.lazy-harness/knowledge/graph.jsonl` — existing canonical graph JSONL rows.
  - `.lazy-harness/generated/implementation-index.json` — optional generated input.
  - `.lazy-harness/scripts/self-test.py` — regression fixture.
  - `.lazy-harness/tests/graph-query.md` — TDD contract.
- Key symbols:
  - `buildGraphQuery`
  - `GraphQueryResult`
  - `resultState`
  - `subgraph.nodes`
  - `subgraph.edges`
- Flow:
  1. Query text is tokenized without assigning semantic authority.
  2. Records, graph rows, and optional generated indexes are matched as cue surfaces.
  3. Matching seeds expand to 1-hop or 2-hop cue subgraph nodes/edges.
  4. Candidates and citations are emitted in deterministic order.
  5. LLM/searcher reads real evidence and remains semantic authority.
- Tests / protection:
  - `.lazy-harness/tests/graph-query.md`
  - `.lazy-harness/scripts/self-test.py#check_graph_query_cli`
- Machine index:
  - graph ids: `kg_graph_query_cli_20260608`, `kg_graph_query_self_test_20260608`, `kg_graph_query_manifest_20260608`, `kg_graph_query_payload_compactness_20260608`, `kg_graph_query_coverage_ranking_hardening_20260608`, `kg_graph_query_coverage_ranking_plan_20260608`

## Payload compactness benchmark history

Baseline, 2026-06-08 slice 1, source query `retrieval coverage audit`, JSON `--limit=20`:

- bytes: 61,004
- estimated tokens: 15,240
- largest contributors: `subgraph` 25,581 bytes, `citations` 9,444 bytes, `seeds` 7,211 bytes
- candidate coverage: DDD/BDD/SDD/TDD/SSOT present

Optimization target for slice 2:

- reduce the same benchmark payload materially without removing candidate lists, citations, subgraph nodes/edges, or forbidden-field protection
- keep graph query cue-only; do not use payload compactness as a reason to relax harness-first search/read debt

Slice-2 result, 2026-06-08, same source query and `--limit=20`:

- bytes guard: below 40,000
- latest focused observations: about 29.6 KB
- estimated tokens from observation: about 7.4k
- reduction from baseline observation: about 31 KB, about 51%
- note: exact byte count may drift slightly as records/graph rows change; the stable acceptance guard is below 40,000 bytes
- collection caps: `seeds=20`, `subgraph.nodes=20`, `subgraph.edges=20`, `citations=20`
- edge endpoint compactness: no edge `source`/`target` contains full `.lazy-harness/`, `src/`, or `tests/` path text
- candidate coverage: DDD/BDD/SDD/TDD/SSOT present
- validation: `python3 .lazy-harness/scripts/self-test.py --scope framework` passed

## Layer completeness impact

- DDD: no new domain term; existing `Searchable Record Memory`, `Record Map`, `LLM-owned retrieval`, `Semantic authority`, and `Deterministic cache` terms apply.
- BDD: no lifecycle behavior change in slice 1; graph query is another cue source that still requires real evidence reads.
- SDD: this record defines the prototype contract.
- TDD: `.lazy-harness/tests/graph-query.md` and self-test must protect behavior before source is considered complete.
- ADR: no ADR required for additive read-only prototype; ADR required before lifecycle/batch/reminder/runtime policy changes.
- SSOT: generated/non-canonical boundary remains canonical in `.lazy-harness/ssot/implementation-map-storage.md` and `.lazy-harness/ssot/cli-tool-boundary.md`.
- Planning: `.lazy-harness/planning/graph-query-prototype-implementation-plan.md` remains direction lock.

## Rule placement

- Rule: `lazy graph query` is a prototype read-only graph context CLI that surfaces cited cue-only subgraph candidates before larger retrieval policy changes.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/graph-query.md`
- Why not BDD only: this is a CLI contract and output schema.
- Why not ADR: no irreversible policy/runtime change in prototype slice 1.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-approved plan, direction lock preserved.
