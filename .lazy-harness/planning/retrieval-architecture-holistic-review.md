# Retrieval Architecture Holistic Review

Status: active
Date: 2026-06-08
Layer: Planning
Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/record-index-header.md`
Related SDD: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
Related Planning: `.lazy-harness/planning/graph-index-migration-considerations.md`
Related Planning: `.lazy-harness/planning/jcode-graph-memory-tool-integration.md`
Related SSOT: `.lazy-harness/ssot/implementation-map-storage.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: framework-global
- Applies when:
  - evaluating whether `lazy map --overview` should be a hard sequential gate, soft guidance, or prompt/reminder context
  - Graphify adoption evaluation: vendoring Graphify code vs porting Graphify principles
  - prototype-sized implementation vs big-change boundary for graph query rollout
  - comparing current `record-map` shallow candidate retrieval with Graphify-style graph query/path/explain traversal
  - deciding whether to adopt Graphify by vendoring code or porting its principles
  - deciding whether batching is safe for overview/query/read workflows
  - deciding whether overview text should be injected into reminders instead of forcing another tool call
- Must:
  - preserve canonical record/source/test reads before semantic reliance
  - treat generated indexes and Graphify-style outputs as cue-only/non-canonical
  - distinguish local CLI latency from LLM token/context savings
  - evaluate dogfood friction, not only theoretical correctness
  - consider a soft/depth-aware workflow before keeping a hard batch block
  - prefer porting Graphify principles into TypeScript/Bun before considering wholesale Python vendoring
  - keep the first `lazy graph query` slice additive/read-only before changing lifecycle or batch policy
- Must not:
  - forget the user concern that hard-blocking batch may be low value if the workflow is still shallow
  - inject full graphs or full overview into every prompt without measuring token cost
  - make Graphify or generated index canonical truth
  - block useful parallel reads chosen after enough context is available
- Record completion:
  - final decision updates BDD, SDD, TDD, SSOT/ADR if needed, helper source, self-test, sync manifest if downstream behavior changes.

## User-confirmed concerns to preserve

The user asked not to forget these points:

1. The current approach may be too shallow: it shows an index/overview and then asks the agent to manually choose tokens, rather than letting the system traverse deeply.
2. Hard-blocking `batch` around overview may not help much if agents can still do suboptimal sequential searches afterward.
3. It may be better to include a compact overview/reminder in the prompt rather than forcing a separate overview tool call every time.
4. Graphify should be considered as a reference for how to solve this: persistent generated graph, query/path/explain/MCP tools, compact subgraph output, cache/watch behavior.
5. The goal is not just rule compliance; the flow must be practically faster, lower-token, and less annoying while still safe.

## Current state assessment

### Graphify adoption note

- Graphify clone verification already read source at commit `8a04560bf5d5eaeef8e466bce084270b7f68faae`.
- License is MIT, so copying/adapting is legally permissive if copyright/license notice is preserved.
- Package is Python (`graphifyy`, CLI entrypoint `graphify = graphify.__main__:main`, `requires-python >=3.10`), while lazy-harness core tooling is TypeScript/Bun.
- Therefore the preferred first implementation is **port the principles and data flow**, not wholesale vendoring:
  - persistent generated graph/cache,
  - query/path/explain commands,
  - compact cited subgraph/context output,
  - stale/missing fallback to canonical records/source/tests,
  - generated/non-canonical boundary.
- Direct vendoring remains possible later, but should be a separate ADR because it introduces Python runtime/dependency/package maintenance into lazy-harness.

### What is working

- `record-index` builds a deterministic, rebuildable cache over record metadata and graph hints.
- `lazy map --overview` gives whole-structure inventory.
- `lazy map <term>` gives 1-hop matches plus drill-down candidates.
- `retrieval-audit` exposes structural gaps and related layer candidates.
- Cross-layer related records now surface DDD/BDD/SDD/TDD/SSOT candidates.
- Downstream sync currently carries retrieval/index foundation records and the overview batch guard.

### What is weak

- `record-map` is mostly **1-hop cue aggregation**:
  - matched records,
  - related records,
  - source/test hints,
  - graph row fields.
- It does not yet implement Graphify-style deep traversal:
  - no `path A B`,
  - no `explain node`,
  - no BFS/DFS subgraph expansion from seed nodes,
  - no scored context packet with citations,
  - no persistent query service/MCP tool.
- The overview-first hard guard protects order, but may be over-strict if a better architecture provides enough context up front or a query tool can expand from seed terms safely.
- Reminder injection of full overview would cost tokens; a compact inventory digest or dynamic packet may be better than full overview text.

## Options under consideration

### Option A — Keep hard sequential overview guard

Pros:
- Strictly preserves current record-first protocol.
- Prevents obviously premature dependent queries.

Cons:
- Dogfood friction is high.
- Does not solve shallow traversal.
- Agent may still perform inefficient sequential calls.

### Option B — Replace hard block with soft warning / post-turn lint

Pros:
- Allows practical parallelism.
- Still records misuse through response.completed or doctor/self-test.

Cons:
- Allows mistakes during the active turn.
- Requires strong final verification to catch missed layers.

### Option C — Compact overview packet in reminder + allow batching

Pros:
- Agent has initial inventory without a tool call.
- Reduces need for hard block.
- Could allow dependent query planning in one batch because the overview is already available.

Cons:
- Adds prompt tokens every turn.
- Needs token budget/quality measurement.
- Must stay cue-only and avoid semantic authority.

### Option D — Graphify-style query/path/explain tool first, then relax overview guard

Pros:
- Addresses the real weakness: shallow traversal.
- Tool returns compact cited subgraph/context from a persistent generated memory.
- Can support `query`, `path`, `explain`, `neighbors`, and stale-safe fallback.

Cons:
- More implementation work.
- Needs schema/version/stale tests.
- Must preserve generated/non-canonical boundary.

## Recommended direction

Recommended: **D + C, then reassess B**.

1. Build a Graphify-inspired internal query tool over existing record-index/graph/generated implementation index:
   - `lazy graph query <text>` or `lazy index query <text>`
   - `lazy graph explain <node-or-path>`
   - `lazy graph path <from> <to>`
   - output compact cited subgraph/context packet
2. Add a compact overview digest to reminder or lifecycle packet, not full overview.
3. Once the agent has either compact overview or graph query context available, change hard overview-batch denial into a more nuanced rule:
   - deny only when no overview/context packet exists,
   - warn when overview is batched but no dependent evidence read follows,
   - allow parallel reads after packet/overview evidence exists.

## Scope sizing

The next step should be treated as a **prototype-sized implementation**, not the full architecture migration.

### Prototype-sized / safe first slice

- Add a TS/Bun CLI over existing generated/canonical inputs, e.g. `.lazy-harness/scripts/graph-query.ts`.
- Add `lazy graph query <text>` first.
- Use existing inputs only:
  - `.lazy-harness/knowledge/graph.jsonl`,
  - `.lazy-harness/generated/record-index.json` or fresh `record-index.ts` rebuild,
  - `.lazy-harness/generated/implementation-index.json` when present.
- Output a compact cue-only cited context packet.
- Do not change lifecycle policy yet.
- Do not remove `lazy map` or `retrieval-audit`.
- Do not vendor Graphify/Python.

This first slice is **medium-small** because it is additive, read-only, and can be guarded by self-test without changing agent policy.

### Big-change boundary

It becomes a large architectural change only when one of these happens:

- Replace overview-first policy with graph-query-first policy.
- Relax or remove `check-overview-batch-order.py` hard block.
- Inject compact overview/graph packets into every reminder/prompt.
- Add a persistent daemon/MCP server.
- Vendor Graphify or introduce Python/Go/Rust runtime dependencies.
- Make generated graph output influence semantic authority instead of remaining cue-only.

Therefore: implement `lazy graph query` as an additive TS/Bun prototype first, benchmark it, then decide whether the larger policy/runtime change is justified.

## Evaluation plan

1. Measure prompt overhead of a compact overview packet vs full `lazy map --overview`.
2. Prototype a `lazy graph query` over existing `knowledge/graph.jsonl`, record-index, and generated indexes.
3. Compare three flows on real tasks:
   - current hard overview-first flow,
   - compact reminder overview + batched follow-up,
   - graph query/path/explain + minimal reads.
4. Metrics:
   - input tokens,
   - tool call count,
   - local latency,
   - missed DDD/BDD/SDD/TDD/SSOT layers,
   - user-visible friction,
   - false block rate.

## Implementation map

- Status: planned
- Primary files:
  - `.lazy-harness/scripts/record-map.ts` — current 1-hop overview/drill-down CLI.
  - `.lazy-harness/scripts/record-index.ts` — generated record/source cache.
  - `.lazy-harness/scripts/retrieval-coverage-audit.ts` — structural coverage audit.
  - `.lazy-harness/hooks/lifecycle/helpers/check-overview-batch-order.py` — current hard batch guard.
  - `.lazy-harness/planning/graph-index-migration-considerations.md` — Graphify source-verified constraints.
  - `.lazy-harness/planning/jcode-graph-memory-tool-integration.md` — graph memory tool concept.
  - future `.lazy-harness/scripts/graph-query.ts` or `.lazy-harness/scripts/index-query.ts` — deep query/path/explain prototype.
- Key observations:
  - `record-map.ts#buildDrilldown` collects 1-hop related/source/test/graph ids only.
  - Graphify source implements persistent graph outputs, cache, MCP query tools, BFS/DFS-like context rendering, and advisory assistant hooks.
- Tests / protection:
  - current `check_tool_execute_before_hook` protects hard overview guard.
  - future tests should cover compact overview packet token budget, graph query citations, path/explain output, stale index fallback, and false block rate.
- Machine index:
  - graph ids: pending until prototype/decision.

## Discovery capture

- DDD: none yet; existing `searchable-record-memory` terms apply.
- SDD: candidate deep graph query/path/explain contract needed.
- BDD: candidate revised retrieval behavior needed for compact overview / graph query / parallel-safe workflow.
- TDD: candidate tests for false block rate, compact overview token budget, graph query citation/path/explain, and stale fallback.
- ADR: likely required if changing from hard overview guard to soft/depth-aware policy.
- SSOT: generated/non-canonical boundary remains `implementation-map-storage`; may need a new SSOT for reminder packet contents.
- Planning: this file captures the current open design review and user concerns.

## Rule placement

- Rule: The open question is not whether to ignore record-first behavior; it is whether record-first should be implemented as hard sequential overview, compact reminder context, or Graphify-style query/path/explain traversal.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/retrieval-architecture-holistic-review.md`
- Why not final BDD/SDD yet: user has not chosen the policy; current content is a planning review and design option set.
- Confirmation: user-requested holistic review, pending final option decision.
