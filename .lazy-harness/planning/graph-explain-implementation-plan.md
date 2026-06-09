# Graph Explain Implementation Plan

Status: phase3-path-backed-implemented
Date: 2026-06-08
Layer: Planning
Related SDD: `.lazy-harness/spec/platform/graph-explain.md`
Related TDD: `.lazy-harness/tests/graph-explain.md`
Related SDD: `.lazy-harness/spec/platform/graph-query.md`
Related SDD: `.lazy-harness/spec/platform/graph-path.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related Planning: `.lazy-harness/planning/retrieval-architecture-holistic-review.md`
Related Planning: `.lazy-harness/planning/graph-index-migration-considerations.md`
Related evidence: `.lazy-harness/evidence/2026-06-08-graph-explain-phase1-downstream-sync.md`
Related evidence: `.lazy-harness/evidence/2026-06-09-graph-explain-phase2-markdown-downstream-sync.md`

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
  - keep JSON/Markdown explain limited to cited structural statements
  - keep path-backed support limited to bounded graph path packets unless a new option gate/ADR expands scope
  - keep all statements support-backed and citation-backed
  - preserve graph query/path outputs and cue-only/read-only policy while implementing explain
  - preserve query/path outputs and self-tests
  - run focused tests, full framework self-test, downstream sync/smoke, and evidence capture after implementation
- Must not:
  - implement explain in the design-only record commit
  - add semantic authority, `requiredRead`, `optionalRead`, confidence, required reads, next action, risk, gate, or intent classification
  - implement MCP, daemon, watch mode, prompt/reminder injection, or Graphify vendoring
  - change lifecycle/read-debt/overview/option-gate policy
- Record completion:
  - design-only completion updates SDD/TDD/Planning/manifest/graph rows and verified the pre-implementation command boundary.
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
- Focused smoke confirmed the Phase 0 pre-implementation command boundary before source changes.

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
   - Phase 0 pre-implementation command boundary holds,
   - current graph query/path focused checks still pass,
   - full framework self-test passes.
7. Commit and push design-only records.

Exit criteria:

- Design-only records are committed and pushed.
- No source implementation exists yet.
- Phase 0 pre-implementation command boundary holds until the separate source slice.

## Phase 1 — Minimal JSON structural packet

Status: implemented and downstream-validated

Evidence:

- Source implementation commit `dfd11ffe676500ad928c61789034835a81097ef1` (`feat(graph): implement graph explain phase 1`) passed focused graph explain checks, full framework self-test, commit hook lazy test, source smoke, origin push, and 16/16 initialized downstream host sync/smoke validation.
- Evidence capsule: `.lazy-harness/evidence/2026-06-08-graph-explain-phase1-downstream-sync.md`.

Tasks:

1. Extend `parseArgs` in `.lazy-harness/scripts/graph-query.ts` to allow `command: 'explain'` only in this implementation commit.
2. Add types:
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

## Phase 2 — Markdown renderer

Status: implemented and downstream-validated

Evidence:

- Source implementation commit `4208c85758fac89ff22b5edcddefad358d547d2a` (`feat(graph): render graph explain markdown`) passed focused graph explain JSON/Markdown checks, full framework self-test, commit hook lazy test, source smoke, origin push, and 16/16 initialized downstream host JSON/Markdown sync/smoke validation.
- Evidence capsule: `.lazy-harness/evidence/2026-06-09-graph-explain-phase2-markdown-downstream-sync.md`.

Tasks:

1. Implement `renderExplainMarkdown` from the same JSON packet.
2. Ensure every bullet includes citation/support labels.
3. Add cue-only/read-evidence caveat at top and bottom.
4. Keep output compact under `--limit` and `--max-statements`.

Exit criteria:

- Markdown output is human-readable and support-backed.
- No uncited narrative paragraphs are emitted.

## Phase 3 — Optional path support

Status: implemented and downstream-synced

Evidence: `.lazy-harness/evidence/2026-06-09-graph-explain-phase3-path-downstream-sync.md` records 16/16 downstream hosts synced to source commit `e8a0ca872b8e531fb0ca7e4ac2250cf613ce9941` and smoke-validated JSON/Markdown `--include-paths` output with path packets, edge-backed path support, `candidate_context` boundary wording, zero-edge/self path non-evidence, and no forbidden semantic-authority fields.

Tasks:

1. Add `--include-paths` support.
2. Select bounded endpoint pairs from graph-query candidates.
3. Call `buildGraphPath` only as cited support.
4. Treat `candidate_context` as structural fallback only.
5. Do not promote zero-edge/self paths into path support or invented `bounded_path` relations.
6. Do not claim semantic connection or causality.

Exit criteria:

- Path-backed statements explain relation/provenance only.
- Path-backed statements use only edge-backed paths; zero-edge/self paths are path packet context, not path evidence.
- Source and downstream graph-path fixtures remain linked.

## Phase 4 — Validation and downstream sync

Status: completed for Phase 1 JSON implementation, Phase 2 Markdown implementation, and Phase 3 path-backed implementation.

Evidence: `.lazy-harness/evidence/2026-06-08-graph-explain-phase1-downstream-sync.md` records 16/16 downstream hosts synced to source commit `dfd11ffe676500ad928c61789034835a81097ef1` and smoke-validated `graph-query.explain` structural JSON with cited statements and no forbidden semantic-authority fields.

Evidence: `.lazy-harness/evidence/2026-06-09-graph-explain-phase2-markdown-downstream-sync.md` records 16/16 downstream hosts synced to source commit `4208c85758fac89ff22b5edcddefad358d547d2a` and smoke-validated both JSON and Markdown output with cited/support-backed statements and no forbidden semantic-authority fields.

Evidence: `.lazy-harness/evidence/2026-06-09-graph-explain-phase3-path-downstream-sync.md` records 16/16 downstream hosts synced to source commit `e8a0ca872b8e531fb0ca7e4ac2250cf613ce9941` and smoke-validated JSON/Markdown `--include-paths` output with path packets, edge-backed path support, `candidate_context` boundary wording, zero-edge/self path non-evidence, and no forbidden semantic-authority fields.

Focused validation:

```bash
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=json --limit=8
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=json --limit=8 --include-paths
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
| Zero-edge/self path is over-read | SDD/TDD require explain to skip zero-edge/self paths for `support.kind=path` and forbid invented `bounded_path` relations |
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

- Status: implemented-phase3-path-backed
- Primary files:
  - `.lazy-harness/planning/graph-explain-implementation-plan.md` — this plan.
  - `.lazy-harness/spec/platform/graph-explain.md` — JSON/Markdown/path-backed command contract.
  - `.lazy-harness/tests/graph-explain.md` — JSON/Markdown/path-backed regression fixtures.
  - `.lazy-harness/scripts/graph-query.ts` — implements `GraphExplainResult` types, `buildGraphExplain`, JSON output, `renderExplainMarkdown`, `explainPathTargets`, `buildExplainPathPackets`, and `pathPacketSupport`.
  - `.lazy-harness/scripts/self-test.py` — implements `check_graph_explain_cli` JSON/Markdown/path-backed regression coverage, including zero-edge/self path non-evidence and `candidate_context` boundary wording.
  - `.lazy-harness/bin/lazy` — advertises `graph explain <term-or-file>` JSON/Markdown.
  - `.lazy-harness/manifests/init-categories.json` — graph explain record and evidence sync entries.
  - `.lazy-harness/knowledge/graph.jsonl` — graph explain implementation/test/evidence graph rows.
  - `.lazy-harness/evidence/2026-06-08-graph-explain-phase1-downstream-sync.md` — downstream sync/smoke evidence capsule.
  - `.lazy-harness/evidence/2026-06-09-graph-explain-phase2-markdown-downstream-sync.md` — downstream JSON/Markdown sync/smoke evidence capsule.
  - `.lazy-harness/evidence/2026-06-09-graph-explain-phase3-path-downstream-sync.md` — downstream JSON/Markdown `--include-paths` sync/smoke evidence capsule.
  - `.lazy-harness/evidence/2026-06-09-graph-explain-token-savings-accuracy.md` — token-savings (98.3% reduction) and citation-accuracy (100%) measurement evidence capsule.
- Current symbols:
  - `GraphExplainResult`
  - `GraphExplainStatement`
  - `GraphExplainSupport`
  - `buildGraphExplain`
  - `renderExplainMarkdown`
  - `explainPathTargets`
  - `buildExplainPathPackets`
  - `pathPacketSupport`
  - `check_graph_explain_cli`
- Current protection:
  - `check_graph_explain_cli` verifies JSON shape, Markdown caveats/support/citations, recursive forbidden-field absence, `--include-paths` path packets/path support statements, zero-edge/self path non-evidence, `candidate_context` boundary wording, and read-only behavior.
- Graph ids:
  - `kg_graph_explain_structural_plan_20260608`
  - `kg_graph_explain_phase1_cli_20260608`
  - `kg_graph_explain_phase1_self_test_20260608`
  - `kg_graph_explain_phase1_downstream_sync_20260608`
  - `kg_graph_explain_phase2_markdown_cli_20260609`
  - `kg_graph_explain_phase2_markdown_self_test_20260609`
  - `kg_graph_explain_phase2_downstream_sync_20260609`
  - `kg_graph_explain_phase3_path_cli_20260609`
  - `kg_graph_explain_phase3_path_self_test_20260609`
  - `kg_graph_explain_phase3_path_downstream_sync_20260609`

## Layer completeness impact

- DDD: no new domain entity.
- BDD: LLM-owned record retrieval remains unchanged.
- SDD: `.lazy-harness/spec/platform/graph-explain.md` defines the JSON/Markdown/path-backed command contract.
- TDD: `.lazy-harness/tests/graph-explain.md` defines JSON/Markdown/path-backed fixtures.
- ADR: not needed for cue-only Phase 3 path-backed implementation. Required before semantic authority, Graphify vendoring, MCP/daemon/watch, prompt/reminder injection, or lifecycle policy changes.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains controlling.
- Planning: this record tracks phased implementation.

## Discovery capture

- Captured user-confirmed option A as durable SDD/TDD/Planning records instead of chat-only state.
- Captured that `lazy graph explain` Phase 3 adds bounded path-backed support from existing `GraphPathResult` packets while preserving cue-only semantics.
- Captured future ADR boundary for semantic authority or runtime/dependency expansion.

## Rule placement

- Rule: implement graph explain only as cited structural explanation, in phases, after design records are committed.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/graph-explain-implementation-plan.md`
- Why not AGENTS.md: implementation sequencing and validation details belong in planning/source/test records, not prompt grammar.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed option A
