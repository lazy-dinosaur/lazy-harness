# Graph Explain Implementation Plan

Status: accepted-design-not-implemented
Date: 2026-06-08
Layer: Planning
Related SDD: `.lazy-harness/spec/platform/graph-explain.md`
Related TDD: `.lazy-harness/tests/graph-explain.md`
Related SDD: `.lazy-harness/spec/platform/graph-query.md`
Related SDD: `.lazy-harness/spec/platform/graph-path.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related Planning: `.lazy-harness/planning/retrieval-architecture-holistic-review.md`
Related Planning: `.lazy-harness/planning/graph-index-migration-considerations.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: framework-global
- User-confirmed option: A, Cited structural explanation
- Applies when:
  - planning the first `lazy graph explain` implementation slice
  - deciding whether explain can be added without semantic authority or policy relaxation
  - sequencing source, tests, records, sync, and evidence for graph explain
- Must:
  - keep the first explain slice design-only until this plan, SDD, and TDD are committed
  - implement only cited structural explanation in the future source slice
  - keep all statements support-backed and citation-backed
  - preserve `lazy graph explain` unsupported behavior until implementation begins
  - preserve query/path outputs and self-tests
  - run focused tests, full framework self-test, downstream sync/smoke, and evidence capture after implementation
- Must not:
  - implement explain in the design-only record commit
  - add semantic authority, `requiredRead`, `optionalRead`, confidence, required reads, next action, risk, gate, or intent classification
  - implement MCP, daemon, watch mode, prompt/reminder injection, or Graphify vendoring
  - change lifecycle/read-debt/overview/option-gate policy
- Record completion:
  - design-only completion updates SDD/TDD/Planning/manifest/graph rows and verifies `lazy graph explain` remains unsupported.
  - implementation completion later updates source/self-test/help/evidence/downstream sync together.

## Direction lock

This plan implements user-confirmed option A:

> `lazy graph explain` should become a cited structural explanation helper only.

The planned command explains indexed structure, not meaning. It says why candidates appeared, which fields/edges/provenance support them, and what structural gaps exist.

It must not say what the user means, what must be read, how confident the system is, whether a relation is causal, or what action to take next.

## Phase 0 — Design records, current slice

Status: completed
Completed: 2026-06-08
Evidence:

- Design-only records committed and pushed in `e056634` (`Docs: add graph explain structural design records`).
- Full framework self-test passed before commit (`python3 .lazy-harness/scripts/self-test.py --scope framework`, task `610228ra1x`, exit 0) and commit hook reported `✅ .lazy-harness/bin/lazy test all green`.
- Focused smoke confirmed `lazy graph explain` still exits unsupported with the explicit prototype-slice message.

Tasks:

1. Create `.lazy-harness/spec/platform/graph-explain.md`.
2. Create `.lazy-harness/tests/graph-explain.md`.
3. Create `.lazy-harness/planning/graph-explain-implementation-plan.md`.
4. Add manifest entries for the three records.
5. Add knowledge graph rows linking the plan, SDD, and TDD.
6. Validate:
   - records exist,
   - required phrases exist,
   - manifest JSON parses,
   - graph JSONL parses and has no duplicate ids,
   - `lazy graph explain` remains unsupported,
   - current graph query/path focused checks still pass,
   - full framework self-test passes.
7. Commit and push design-only records.

Exit criteria:

- Design-only records are committed and pushed.
- No source implementation exists yet.
- `lazy graph explain` still fails with the unsupported prototype-slice message.

## Phase 1 — Minimal JSON structural packet, future implementation

Tasks:

1. Extend `parseArgs` in `.lazy-harness/scripts/graph-query.ts` to allow `command: 'explain'` only in this implementation commit.
2. Add planned types:
   - `GraphExplainResult`
   - `GraphExplainStatement`
   - `GraphExplainSupport`
3. Implement `buildGraphExplain(root, query, limit, maxStatements, includePaths, fresh)`:
   - call `buildGraphQuery`,
   - convert seeds, matched fields, citations, graph edges, and candidate lists into structural statements,
   - include gaps if query output is partial/gap,
   - never infer user intent or required reads.
4. Add recursive forbidden-field guard in source tests.
5. Keep JSON compact and bounded.

Exit criteria:

- JSON output passes shape tests.
- Every statement has support and citations.
- No forbidden semantic fields appear.

## Phase 2 — Markdown renderer, future implementation

Tasks:

1. Implement `renderExplainMarkdown` from the same JSON packet.
2. Ensure every bullet includes citation/support labels.
3. Add cue-only/read-evidence caveat at top and bottom.
4. Keep output compact under `--limit` and `--max-statements`.

Exit criteria:

- Markdown output is human-readable and support-backed.
- No uncited narrative paragraphs are emitted.

## Phase 3 — Optional path support, future implementation

Tasks:

1. Add `--include-paths` support.
2. Select bounded endpoint pairs from graph-query candidates.
3. Call `buildGraphPath` only as cited support.
4. Treat `candidate_context` as structural fallback only.
5. Do not claim semantic connection or causality.

Exit criteria:

- Path-backed statements explain relation/provenance only.
- Source and downstream graph-path fixtures remain linked.

## Phase 4 — Validation and downstream sync, future implementation

Focused validation:

```bash
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=json --limit=8
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=md --limit=8 --include-paths
.lazy-harness/bin/lazy graph explain 'zzzz-missing-term' --format=json --limit=8
python3 - <<'PY'
# recursive forbidden-key check
PY
python3 - <<'PY'
# read-only mutation check for temp host
PY
```

Full validation:

```bash
python3 .lazy-harness/scripts/self-test.py --scope framework
```

Downstream validation:

- Sync to initialized hosts.
- Smoke `lazy graph explain 'workflow compression not safety reduction' --format=json --limit=8`.
- Verify no forbidden semantic fields.
- Verify output is structural/cited.
- Record evidence capsule.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Explain becomes semantic authority | Output contract forbids confidence, intent, required reads, gates, risks, next actions, and candidate meanings |
| Uncited prose sneaks in | TDD requires every statement to have support/citations |
| Candidate_context is over-read | SDD/TDD require candidate_context explanation to say only that an endpoint path appeared in the other query packet |
| Token output grows | `--limit` and `--max-statements` cap query packet, path packet, and statement count |
| Path/query regress | Existing graph query/path focused tests remain part of acceptance |
| Policy relaxation by accident | No lifecycle/read-debt/overview/option-gate changes allowed in this plan |

## Non-goals

- No Graphify vendoring.
- No Python runtime dependency.
- No MCP or daemon.
- No watch mode.
- No prompt/reminder injection.
- No read-debt or overview policy changes.
- No semantic summary or action recommendation.

## Implementation map

- Status: planned
- Primary files:
  - `.lazy-harness/planning/graph-explain-implementation-plan.md` — this plan.
  - `.lazy-harness/spec/platform/graph-explain.md` — planned command contract.
  - `.lazy-harness/tests/graph-explain.md` — planned regression fixtures.
  - `.lazy-harness/scripts/graph-query.ts` — future implementation location.
  - `.lazy-harness/scripts/self-test.py` — future focused self-test location.
  - `.lazy-harness/bin/lazy` — future help/dispatcher wording if needed.
  - `.lazy-harness/manifests/init-categories.json` — design record sync entries.
  - `.lazy-harness/knowledge/graph.jsonl` — design graph rows.
- Planned symbols:
  - `GraphExplainResult`
  - `GraphExplainStatement`
  - `GraphExplainSupport`
  - `buildGraphExplain`
  - `renderExplainMarkdown`
  - `check_graph_explain_cli`
- Current protection:
  - Existing graph-query/path self-tests keep `lazy graph explain` unsupported.
- Planned graph id:
  - `kg_graph_explain_structural_plan_20260608`

## Layer completeness impact

- DDD: no new domain entity.
- BDD: LLM-owned record retrieval remains unchanged.
- SDD: `.lazy-harness/spec/platform/graph-explain.md` defines the planned command contract.
- TDD: `.lazy-harness/tests/graph-explain.md` defines pre-implementation and future fixtures.
- ADR: not needed for design-only or cue-only implementation. Required before semantic authority, Graphify vendoring, MCP/daemon/watch, prompt/reminder injection, or lifecycle policy changes.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains controlling.
- Planning: this record tracks phased implementation.

## Discovery capture

- Captured user-confirmed option A as durable SDD/TDD/Planning records instead of chat-only state.
- Captured that `lazy graph explain` remains unsupported until a future implementation commit.
- Captured future ADR boundary for semantic authority or runtime/dependency expansion.

## Rule placement

- Rule: implement graph explain only as cited structural explanation, in phases, after design records are committed.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/graph-explain-implementation-plan.md`
- Why not AGENTS.md: implementation sequencing and validation details belong in planning/source/test records, not prompt grammar.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed option A
