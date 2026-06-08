# Graph Query Prototype Implementation Plan

Status: implemented-slice-1
Date: 2026-06-08
Layer: Planning
Related Planning: `.lazy-harness/planning/retrieval-architecture-holistic-review.md`
Related Planning: `.lazy-harness/planning/graph-index-migration-considerations.md`
Related SDD: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
Related SDD: `.lazy-harness/spec/platform/record-index-header.md`
Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
Related SSOT: `.lazy-harness/ssot/implementation-map-storage.md`

## Rule digest

- Status: proposed
- Layer: Planning
- Scope: framework-global
- Applies when:
  - implementing the first TS/Bun `lazy graph query` prototype
  - deciding exact files, test gates, and non-deviation constraints for Graphify-style retrieval
  - evaluating whether the next work is prototype-sized or a large architecture change
- Must:
  - keep the first slice additive, read-only, cue-only, and TypeScript/Bun based
  - create/refresh SDD and TDD before implementation changes land
  - use existing inputs only: `knowledge/graph.jsonl`, `record-index`, optional `implementation-index`
  - preserve canonical record/source/test authority and generated/non-canonical boundary
  - measure tokens, tool count, latency, missed-layer rate, and false-block impact before changing lifecycle/batch policy
  - sync and verify downstream hosts after committed framework changes
- Must not:
  - replace `lazy map`, `retrieval-audit`, or overview-first behavior in the prototype slice
  - relax/remove `check-overview-batch-order.py` in the prototype slice
  - inject graph/overview packets into reminders in the prototype slice
  - vendor Graphify/Python, add Go/Rust, add MCP/daemon, or add persistent service in the prototype slice
  - treat graph query output as semantic authority or required-read proof
- Record completion:
  - implementation completion updates this plan, SDD, TDD, BDD/SSOT if behavior/boundary changes, graph rows, manifest/sync evidence, and benchmark artifacts.

## Direction lock

This plan is only for **prototype slice 1**:

> Add `lazy graph query <text>` as a read-only, cue-only TS/Bun CLI over existing generated/canonical inputs.

The following are explicitly out of scope until benchmark evidence and separate approval:

- `lazy graph path`
- `lazy graph explain`
- compact overview packet injection
- lifecycle policy changes
- overview hard-block relaxation
- Python/Graphify vendoring
- Go/Rust rewrite
- MCP server / daemon

If implementation pressure pushes toward any out-of-scope item, stop and open an option gate or ADR.

## Why this is the right next slice

- It directly targets the current weakness: `lazy map` is mostly 1-hop cue aggregation.
- It is small enough to be additive and reversible.
- It gives real benchmark evidence before changing policy.
- It ports Graphify principles without importing its Python runtime.
- It keeps generated graph output non-canonical.

## Phase 0 — Contract and test design first

### 0.1 Add SDD contract

Create `.lazy-harness/spec/platform/graph-query.md`.

Required contract points:

- CLI:
  - `lazy graph query <text> [--format=json|md] [--limit=N] [--depth=N] [--fresh]`
- Output mode:
  - `mode: graph-query.query`
- Output fields:
  - `query`
  - `coverage` or `resultState`: `mapped | partial | gap`
  - `seeds`: matched records/features/graph rows/source hints
  - `subgraph`: nodes + edges with provenance
  - `candidates`: record/source/test/graph ids
  - `citations`: record paths / graph row ids / generated index paths
  - `fallback`: recommended `lazy map`, `retrieval-audit`, and grep commands
  - `notes`: cue-only / non-canonical / read real evidence reminder
- Forbidden fields:
  - `requiredRead`, `optionalRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, `candidateMeanings`
- Boundary:
  - generated graph query output never satisfies search/read debt by itself
  - output is a compact cited context packet, not a final answer

### 0.2 Add TDD contract

Create `.lazy-harness/tests/graph-query.md`.

Fixture matrix:

| Fixture | Scenario | Expected |
|---|---|---|
| `graph_query_mapped_retrieval_audit` | query hits retrieval audit records | returns DDD/BDD/SDD/TDD/SSOT record candidates and graph citations |
| `graph_query_gap` | query has no match | `resultState=gap`, fallback commands present |
| `graph_query_related_expansion_depth_1` | seed record has related records and graph hints | includes 1-hop related records and graph ids |
| `graph_query_no_semantic_fields` | any output | forbidden semantic-authority fields absent recursively |
| `graph_query_cache_freshness` | cache absent/stale or `--fresh` passed | rebuilds from canonical inputs safely |
| `graph_query_help_and_dispatcher` | `lazy help` and `lazy graph query` | dispatcher routes to TS script and help advertises command |

### 0.3 Update BDD/SSOT only if needed

For prototype slice 1:

- BDD update is optional unless behavior wording needs to mention graph query as an allowed cue source.
- SSOT update is optional unless generated/non-canonical boundary needs new wording.
- Do not update lifecycle policy yet.

## Phase 1 — Build read-only TS/Bun CLI

### 1.1 New source file

Add `.lazy-harness/scripts/graph-query.ts`.

Implementation shape:

1. Parse args:
   - subcommand: `query`
   - query text
   - `--format=json|md`
   - `--limit=N`
   - `--depth=N`, default `1`, max `2` for prototype
   - `--fresh`
2. Load inputs:
   - use `buildRecordIndex(root)` or fresh cache logic from `record-map.ts`
   - read `.lazy-harness/knowledge/graph.jsonl`
   - read `.lazy-harness/generated/implementation-index.json` if present and valid enough
3. Normalize terms:
   - lowercase tokens
   - split query and path-like terms
   - keep exact path/file tokens
4. Seed matching:
   - records: title, path, aliases, surface terms, digest fields, implementation hints, graph ids
   - graph rows: id, relation, source, target, path, source text
   - features from record-index project profile
   - implementation index file paths/symbol names
5. Expand graph:
   - depth 1 from seed nodes via graph row source/target/path/id
   - include record relatedRecords and implementation hints
   - cap output by `--limit` and deterministic sort
6. Emit compact packet:
   - JSON and markdown formats
   - candidate records/source/tests/graph ids
   - citations and fallback commands
   - notes that output is cue-only

### 1.2 Dispatcher

Update `.lazy-harness/bin/lazy`:

- help:
  - `graph query <text> [--format=json|md] [--limit=N] [--depth=N] [--fresh]`
- case:
  - `graph)` routes to `bun "$SCRIPTS/graph-query.ts" --root "$HOST_ROOT" "$@"`

### 1.3 No lifecycle changes

Do not touch:

- `.lazy-harness/hooks/lifecycle/helpers/check-overview-batch-order.py`
- message reminder injection
- response.completed lifecycle behavior

## Phase 2 — Self-test and validation

### 2.1 Self-test function

Add `check_graph_query_cli()` to `.lazy-harness/scripts/self-test.py` near record-index/retrieval-audit checks.

Required assertions:

- file exists: `.lazy-harness/scripts/graph-query.ts`
- `lazy help` advertises graph query
- temp fixture host builds:
  - DDD record
  - BDD record
  - SDD graph-query/retrieval record
  - TDD record
  - SSOT boundary record
  - graph row linking record to source/test
  - optional implementation-index fixture
- `lazy graph query 'retrieval coverage audit' --format=json --limit=20` returns:
  - mode `graph-query.query`
  - `mapped`
  - DDD/BDD/SDD/TDD/SSOT record candidates
  - source/test candidates
  - graph citations
  - no forbidden semantic-authority fields
- gap query returns fallback commands
- markdown output includes cue-only warning

### 2.2 Full validation commands

Run in order:

```bash
python3 -m py_compile .lazy-harness/scripts/self-test.py
bun .lazy-harness/scripts/graph-query.ts --root "$PWD" query 'retrieval coverage audit' --format=json --limit=20
.lazy-harness/bin/lazy graph query 'retrieval coverage audit' --format=md --limit=20
python3 .lazy-harness/scripts/self-test.py --scope framework
```

### 2.3 Benchmark

After prototype passes self-test, run a benchmark comparing:

1. current `lazy map --overview + lazy map + retrieval-audit + reads`
2. new `lazy graph query + reads`
3. raw full record read baseline

Metrics:

- estimated tokens
- tool calls
- local runtime
- candidate count
- missing DDD/BDD/SDD/TDD/SSOT layer count
- forbidden-field violations
- false positive candidate count if measurable

## Phase 3 — Record completion and sync

After implementation:

1. [x] Update `.lazy-harness/spec/platform/graph-query.md` with Implementation map.
2. [x] Update `.lazy-harness/tests/graph-query.md` with self-test function names.
3. [x] Add graph rows:
   - implementation row for `graph-query.ts`
   - test row for `check_graph_query_cli`
   - dispatcher row for `lazy graph query`
4. [x] Ensure `init-categories.json` syncs the script and records:
   - `scripts/*.ts` already syncs source
   - add SDD/TDD graph-query records explicitly if needed
5. [x] Commit source + records.
6. [ ] Sync 14 downstream hosts.
7. [ ] Verify each downstream host:
   - marker matches source commit
   - `lazy graph query 'retrieval coverage audit'` returns mapped
   - DDD/BDD/SDD/TDD/SSOT candidates present
   - no forbidden fields

## Phase 4 — Decision checkpoint before bigger changes

Only after prototype + benchmark:

- If graph query reduces tokens/tool calls and improves layer coverage:
  - propose `lazy graph path`
  - propose `lazy graph explain`
  - propose compact overview packet
  - propose relaxing hard overview batch block to context-aware warning/deny
- If graph query is not better:
  - keep current `lazy map`/`retrieval-audit`
  - do not relax overview hard block
  - document why Graphify-style retrieval was not justified

## Non-deviation checklist

Before every implementation commit, verify:

- [x] No lifecycle policy changed.
- [x] No overview hard block changed.
- [x] No prompt/reminder packet injection added.
- [x] No Graphify/Python vendoring added.
- [x] No Go/Rust runtime added.
- [x] No generated output treated as canonical truth.
- [x] SDD/TDD records updated before/with source.
- [x] Output has no forbidden semantic-authority fields in focused self-test design.
- [x] Full self-test passes.

## Slice 1 implementation progress

- Implemented `.lazy-harness/scripts/graph-query.ts` and dispatcher help/route for `lazy graph query`.
- Added `.lazy-harness/scripts/self-test.py#check_graph_query_cli` for mapped/partial/gap, related layer candidates, no semantic fields, read-only behavior, markdown warnings, and unsupported `path`/`explain` boundaries.
- Added SDD/TDD manifest sync entries and graph JSONL implementation/test/dispatcher/sync rows.
- Benchmark is recorded below; downstream sync remains follow-up work before any lifecycle/batch/prompt policy proposal.

## Benchmark snapshot — 2026-06-08 slice 1

Query: `retrieval coverage audit`; local source repo; JSON output; approximate token estimate = chars/4.

| Surface | Runtime | Bytes | Est. tokens | Records | Source | Tests | Graph ids | Missing layers | Forbidden fields |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| `lazy map` query, limit 8 | 151ms | 17,460 | 4,362 | 0 | 0 | 0 | 0 | DDD, BDD, SDD, TDD, SSOT | 0 |
| `lazy retrieval-audit`, limit 8 | 156ms | 5,881 | 1,469 | 8 | 8 | 8 | 7 | TDD, SSOT | 0 |
| `lazy graph query`, limit 8 | 166ms | 25,887 | 6,468 | 8 | 8 | 8 | 8 | none | 0 |
| `lazy graph query`, limit 20 | 186ms | 61,004 | 15,240 | 20 | 20 | 14 | 20 | none | 0 |

Interpretation:

- Graph query improves cross-layer candidate coverage in this benchmark, especially DDD/BDD/SDD/TDD/SSOT completeness.
- Graph query is not yet a token-reduction win versus retrieval-audit, so no lifecycle, batch, or prompt policy should change from this benchmark alone.
- Before proposing `path`, `explain`, overview-packet injection, or overview hard-block relaxation, reduce graph-query payload size or prove a workflow-level token/tool-call win with real read-followup measurements.

## Discovery capture

- DDD: no new domain term yet; existing `searchable-record-memory` applies.
- SDD: new graph-query contract required before implementation.
- BDD: no behavior change in slice 1; may add graph query as cue source if wording requires.
- TDD: new graph-query regression record and self-test function required.
- ADR: not required for slice 1 because it is additive/read-only; required before lifecycle/batch policy changes.
- SSOT: existing generated/non-canonical boundary applies; update only if graph query output introduces a new generated store.
- Planning: this file is the execution plan and direction lock.

## Rule placement

- Rule: The first graph-query step must be an additive TS/Bun prototype that proves value before changing lifecycle/batch policy.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/graph-query-prototype-implementation-plan.md`
- Why not SDD only: this is sequencing and direction-lock planning; SDD/TDD are Phase 0 deliverables.
- Why not ADR yet: no irreversible architectural policy decision in prototype slice 1.
- Confirmation: user requested a detailed plan and explicitly warned not to diverge from direction.
