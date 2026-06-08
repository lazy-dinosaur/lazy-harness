# TDD — Graph Explain

Status: accepted-design-not-implemented
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
  - implementing or changing future `lazy graph explain`
  - changing graph explain output shape, structural statement generation, or Markdown rendering
  - checking whether graph explain remains cue-only and non-authoritative
- Must:
  - protect `lazy graph explain` remains unsupported until the implementation slice starts
  - protect planned JSON and Markdown output shapes after implementation
  - protect every structural statement has citations/support
  - protect `resultState: explained | partial | gap`
  - protect no semantic-authority fields recursively
  - protect read-only behavior: no canonical records, graph JSONL, generated caches, runtime journal, or user memory mutation
  - protect graph query/path behavior remains unchanged when explain is added
- Must not:
  - allow required-read, optional-read, confidence, intent, risk, gate, next-action, or candidate-meaning fields
  - allow uncited narrative explanation
  - allow explain output to satisfy read evidence or declare causality
  - allow explain implementation before SDD/TDD/plan validation is committed
- Record completion:
  - implementation changes update this TDD, SDD, plan, source, self-test, help/dispatcher, manifest, graph rows, and downstream evidence.

## Current pre-implementation fixture

| Fixture id | Scenario | Expected |
|---|---|---|
| `graph_explain_still_unsupported` | `lazy graph explain 'workflow compression not safety reduction' --format=json` before implementation | command fails with explicit unsupported prototype-slice message |
| `graph_explain_records_exist_before_implementation` | User confirms option A | SDD/TDD/plan records exist and describe cited structural explanation only |
| `graph_explain_forbidden_fields_contract` | Planned JSON output contract | forbidden field list is present and recursively enforced by future tests |

## Future implementation fixture matrix

| Fixture id | Scenario | Expected |
|---|---|---|
| `graph_explain_explained_query` | Query has graph-query mapped candidates | `resultState=explained`; statements cite matched fields, records, graph rows, and citations |
| `graph_explain_gap` | Query has no structural candidates | `resultState=gap`; structural gaps and fallback commands present |
| `graph_explain_partial_uncited_path` | Query mapped but optional path evidence unavailable | `resultState=partial`; statements still cite query support; no path sufficiency claim |
| `graph_explain_include_paths` | `--include-paths` requested and path exists | statements may include path support and edge provenance, still cue-only |
| `graph_explain_candidate_context_boundary` | Path support contains `candidate_context` fallback | statement says endpoint path appeared in the other query packet; does not claim semantic connection |
| `graph_explain_no_semantic_fields` | Any JSON output | recursive absence of `requiredRead`, `optionalRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, `candidateMeanings` |
| `graph_explain_read_only` | Running explain in temp host | canonical records, graph JSONL, generated caches, and runtime files unchanged |
| `graph_explain_markdown_citations` | Markdown output | every bullet has citation/support text and cue-only/read-evidence caveat |
| `graph_explain_query_path_regression` | Existing query/path fixtures after explain implementation | `graph query` and `graph path` self-tests still pass |

## Acceptance assertions for future `check_graph_explain_cli`

Self-test must verify:

1. `.lazy-harness/spec/platform/graph-explain.md` exists.
2. `.lazy-harness/tests/graph-explain.md` exists.
3. `.lazy-harness/planning/graph-explain-implementation-plan.md` exists.
4. Before implementation, `lazy graph explain` fails with the unsupported message.
5. After implementation, JSON output has `mode=graph-query.explain`, `explanationKind=structural`, and bounded `statements`.
6. Each statement has non-empty `support` and `citations`.
7. Recursive forbidden-key check passes.
8. Explain does not mutate canonical records, graph JSONL, generated caches, runtime journals, or user memory.
9. Markdown output contains cue-only and does not satisfy read evidence warnings.
10. Existing graph-query and graph-path focused tests still pass.

## Validation commands

Pre-implementation validation:

```bash
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=json
python3 - <<'PY'
from pathlib import Path
for p in [
  '.lazy-harness/spec/platform/graph-explain.md',
  '.lazy-harness/tests/graph-explain.md',
  '.lazy-harness/planning/graph-explain-implementation-plan.md',
]:
  assert Path(p).exists(), p
PY
python3 .lazy-harness/scripts/self-test.py --scope framework
```

Future focused validation:

```bash
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=json --limit=8
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=md --limit=8 --include-paths
.lazy-harness/bin/lazy graph explain 'zzzz-missing-term' --format=json --limit=8
python3 - <<'PY'
# recursive forbidden key assertion against explain output
PY
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

- Status: planned
- Primary files:
  - `.lazy-harness/tests/graph-explain.md` — this TDD record.
  - `.lazy-harness/spec/platform/graph-explain.md` — planned output contract.
  - `.lazy-harness/planning/graph-explain-implementation-plan.md` — phased implementation plan.
  - `.lazy-harness/scripts/graph-query.ts` — planned implementation location.
  - `.lazy-harness/scripts/self-test.py` — planned `check_graph_explain_cli` regression protection.
  - `.lazy-harness/bin/lazy` — planned help/dispatcher update if implementation starts.
- Planned symbols:
  - `GraphExplainResult`
  - `GraphExplainStatement`
  - `buildGraphExplain`
  - `renderExplainMarkdown`
  - `check_graph_explain_cli`
- Current protection:
  - `check_graph_query_cli` and `check_graph_path_cli` verify `lazy graph explain` remains unsupported.
- Planned graph id:
  - `kg_graph_explain_structural_tdd_20260608`

## Layer completeness impact

- DDD: no new domain entity; Searchable Record Memory remains controlling for cue-only interpretation.
- BDD: no user-facing flow change; LLM-owned record retrieval remains controlling.
- SDD: `.lazy-harness/spec/platform/graph-explain.md` defines planned contract.
- TDD: this record defines pre-implementation and future fixtures.
- ADR: no new ADR for design-only records; required before semantic authority, MCP, daemon, watch mode, Graphify vendoring, or lifecycle/prompt policy changes.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains controlling.
- Planning: `.lazy-harness/planning/graph-explain-implementation-plan.md` tracks implementation.

## Rule placement

- Rule: Graph explain tests must prove explanation output is cited, structural, read-only, and non-authoritative.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/graph-explain.md`
- Why not AGENTS.md: regression fixtures and output-shape checks belong in TDD/source, not always-loaded prompt grammar.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed option A
