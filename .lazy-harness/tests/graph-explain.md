# TDD — Graph Explain

Status: accepted-phase1-json
Date: 2026-06-08
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/graph-explain.md`
Related SDD: `.lazy-harness/spec/platform/graph-query.md`
Related SDD: `.lazy-harness/spec/platform/graph-path.md`
Related Planning: `.lazy-harness/planning/graph-explain-implementation-plan.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- User-confirmed option: A, Cited structural explanation
- Applies when:
  - implementing or changing `lazy graph explain`
  - changing graph explain output shape, structural statement generation, or Markdown/path rendering boundaries
  - checking whether graph explain remains cue-only and non-authoritative
- Must:
  - protect Phase 1 JSON packet shape for `mode=graph-query.explain`
  - protect every structural statement has citations/support
  - protect `resultState: explained | partial | gap`
  - protect no semantic-authority fields recursively
  - protect read-only behavior: no canonical records, graph JSONL, generated caches, runtime journal, or user memory mutation
  - protect graph query/path behavior remains unchanged when explain is added
  - protect Markdown and path-backed statements remain explicit future-slice boundaries until implemented
- Must not:
  - allow required-read, optional-read, confidence, intent, risk, gate, next-action, or candidate-meaning fields
  - allow uncited narrative explanation
  - allow explain output to satisfy read evidence or declare causality
  - allow Markdown/path-backed explain output before their separate slices are implemented
- Record completion:
  - implementation changes update this TDD, SDD, plan, source, self-test, help/dispatcher, manifest, graph rows, and downstream evidence.

## Phase 1 fixture matrix

| Fixture id | Scenario | Expected |
|---|---|---|
| `graph_explain_explained_query` | Query has graph-query mapped candidates | `resultState=explained` or `partial`; statements cite matched fields, records, graph rows, or citations |
| `graph_explain_gap` | Query has no structural candidates | `resultState=gap`; structural gaps and fallback commands present |
| `graph_explain_no_semantic_fields` | Any JSON output | recursive absence of `requiredRead`, `optionalRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, `candidateMeanings` |
| `graph_explain_read_only` | Running explain in source checkout | canonical records, graph JSONL, generated caches, and runtime files unchanged |
| `graph_explain_include_paths_phase1_boundary` | `--include-paths` requested in Phase 1 | `coverage.gaps` includes `no-path-evidence` and `pathPackets=[]` |
| `graph_explain_markdown_phase2_boundary` | `--format=md` requested in Phase 1 | command fails with explicit Phase 2 boundary message |
| `graph_explain_query_path_regression` | Existing query/path fixtures after explain implementation | `graph query` and `graph path` self-tests still pass |

## Future fixture matrix

| Fixture id | Scenario | Expected |
|---|---|---|
| `graph_explain_markdown_citations` | Markdown output after Phase 2 | every bullet has citation/support text and cue-only/read-evidence caveat |
| `graph_explain_include_paths` | `--include-paths` implemented in Phase 3 and path exists | statements may include path support and edge provenance, still cue-only |
| `graph_explain_candidate_context_boundary` | Path support contains `candidate_context` fallback | statement says endpoint path appeared in the other query packet; does not claim semantic connection |

## Acceptance assertions for `check_graph_explain_cli`

Self-test must verify:

1. `.lazy-harness/spec/platform/graph-explain.md` exists.
2. `.lazy-harness/tests/graph-explain.md` exists.
3. `.lazy-harness/planning/graph-explain-implementation-plan.md` exists.
4. JSON output has `mode=graph-query.explain`, `explanationKind=structural`, and bounded `statements`.
5. Each statement has non-empty `support` and `citations`.
6. Recursive forbidden-key check passes.
7. Explain does not mutate canonical records, graph JSONL, generated caches, runtime journals, or user memory.
8. `--include-paths` reports `no-path-evidence` with empty `pathPackets` until Phase 3.
9. `--format=md` fails with the Phase 2 boundary message until Markdown is implemented.
10. Existing graph-query and graph-path focused tests still pass.

## Validation commands

Phase 1 focused validation:

```bash
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=json --limit=8 --max-statements=8
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=json --limit=8 --include-paths
.lazy-harness/bin/lazy graph explain 'zzzz-missing-term' --format=json --limit=8
python3 - <<'PY'
import json, subprocess
out = subprocess.check_output(['.lazy-harness/bin/lazy','graph','explain','workflow compression not safety reduction','--format=json','--limit=8'])
payload = json.loads(out)
assert payload['mode'] == 'graph-query.explain'
assert payload['explanationKind'] == 'structural'
assert payload['statements']
PY
python3 .lazy-harness/scripts/self-test.py --scope framework
```

## Interpretation guard

A graph explain packet is a structural explanation only. It is not:

- required-read proof,
- confidence,
- semantic sufficiency,
- causal proof,
- option-gate decision,
- or next-action guidance.

## Implementation map

- Status: implemented-phase1-json
- Primary files:
  - `.lazy-harness/tests/graph-explain.md` — this TDD record.
  - `.lazy-harness/spec/platform/graph-explain.md` — output contract.
  - `.lazy-harness/planning/graph-explain-implementation-plan.md` — phased implementation plan.
  - `.lazy-harness/scripts/graph-query.ts` — implements parser, Phase 1 types, `buildGraphExplain`, and JSON output.
  - `.lazy-harness/scripts/self-test.py` — implements `check_graph_explain_cli` regression protection.
  - `.lazy-harness/bin/lazy` — advertises graph explain Phase 1 JSON.
- Key symbols:
  - `GraphExplainResult`
  - `GraphExplainStatement`
  - `GraphExplainSupport`
  - `buildGraphExplain`
  - `check_graph_explain_cli`
- Future symbols:
  - `renderExplainMarkdown`
  - path-backed explain support via `GraphPathResult`
- Graph ids:
  - `kg_graph_explain_structural_tdd_20260608`
  - `kg_graph_explain_phase1_cli_20260608`
  - `kg_graph_explain_phase1_self_test_20260608`

## Layer completeness impact

- DDD: no new domain entity; Searchable Record Memory remains controlling for cue-only interpretation.
- BDD: no user-facing flow change; LLM-owned record retrieval remains controlling.
- SDD: `.lazy-harness/spec/platform/graph-explain.md` defines Phase 1 contract.
- TDD: this record defines Phase 1 and future fixtures.
- ADR: no new ADR for Phase 1 because it does not relax policy or add runtime/dependency architecture; required before semantic authority, MCP, daemon, watch mode, Graphify vendoring, or lifecycle/prompt policy changes.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains controlling.
- Planning: `.lazy-harness/planning/graph-explain-implementation-plan.md` tracks remaining phases.

## Rule placement

- Rule: Graph explain tests must prove explanation output is cited, structural, read-only, and non-authoritative.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/graph-explain.md`
- Why not AGENTS.md: regression fixtures and output-shape checks belong in TDD/source, not always-loaded prompt grammar.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed option A
