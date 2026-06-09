# TDD — Graph Explain

Status: accepted-phase4-ranking-hardened
Date: 2026-06-08
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/graph-explain.md`
Related SDD: `.lazy-harness/spec/platform/graph-query.md`
Related SDD: `.lazy-harness/spec/platform/graph-path.md`
Related Planning: `.lazy-harness/planning/graph-explain-implementation-plan.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related evidence: `.lazy-harness/evidence/2026-06-08-graph-explain-phase1-downstream-sync.md`
Related evidence: `.lazy-harness/evidence/2026-06-09-graph-explain-phase2-markdown-downstream-sync.md`

## Rule digest

- Status: accepted-phase4-ranking-hardened
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
  - protect Markdown output remains support-backed/citation-backed and path-backed statements remain structural navigation cues only
- Must not:
  - allow required-read, optional-read, confidence, intent, risk, gate, next-action, or candidate-meaning fields
  - allow uncited narrative explanation
  - allow explain output to satisfy read evidence or declare causality
  - allow path-backed explain output to claim semantic connection, causality, required reads, or action guidance
- Record completion:
  - implementation changes update this TDD, SDD, plan, source, self-test, help/dispatcher, manifest, graph rows, and downstream evidence.

## Fixture matrix

| Fixture id | Scenario | Expected |
|---|---|---|
| `graph_explain_explained_query` | Query has graph-query mapped candidates | `resultState=explained` or `partial`; statements cite matched fields, records, graph rows, or citations |
| `graph_explain_gap` | Query has no structural candidates | `resultState=gap`; structural gaps and fallback commands present |
| `graph_explain_no_semantic_fields` | Any JSON output | recursive absence of `requiredRead`, `optionalRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, `candidateMeanings` |
| `graph_explain_read_only` | Running explain in source checkout | canonical records, graph JSONL, generated caches, and runtime files unchanged |
| `graph_explain_include_paths` | `--include-paths` requested and indexed paths exist | `pathPackets` has bounded `GraphPathResult` packets, at least one path-backed statement has `support.kind=path`, and no `no-path-evidence` gap |
| `graph_explain_markdown_citations` | `--format=md` requested in Phase 2 | Markdown output has cue-only/read-evidence caveat and every statement bullet has support/citations |
| `graph_explain_query_path_regression` | Existing query/path fixtures after explain implementation | `graph query` and `graph path` self-tests still pass |
| `graph_explain_no_zero_edge_path_evidence` | A selected path packet contains only zero-edge/self paths | no `support.kind=path` is emitted for that target and no invented `bounded_path` relation appears |
| `graph_explain_candidate_context_boundary` | Path support contains `candidate_context` fallback | statement says endpoint path appeared in the other query packet; does not claim semantic connection |
| `graph_explain_accuracy_benchmark` | Gold-labeled retrieval/ranking quality fixture in framework source checkout | source-only `graph-explain-accuracy-benchmark --fail-on-thresholds` passes micro/macro recall, P@8, MRR, nDCG, layer recall, gap, negative-contamination, no-forbidden-field, and read-only gates; downstream hosts smoke schema/policy without source gold thresholds |
| `graph_explain_dynamic_write_loop_boundary` | Agent has just changed canonical records/source/tests | graph explain remains a cue-only stale-cache-prone routing surface; validation and direct reads of changed canonical files remain required |

## Acceptance assertions for `check_graph_explain_cli`

Self-test must verify:

1. `.lazy-harness/spec/platform/graph-explain.md` exists.
2. `.lazy-harness/tests/graph-explain.md` exists.
3. `.lazy-harness/planning/graph-explain-implementation-plan.md` exists.
4. JSON output has `mode=graph-query.explain`, `explanationKind=structural`, and bounded `statements`.
5. Each statement has non-empty `support` and `citations`.
6. Recursive forbidden-key check passes.
7. Explain does not mutate canonical records, graph JSONL, generated caches, runtime journals, or user memory.
8. `--include-paths` attaches bounded `GraphPathResult` packets when indexed paths exist, and path-backed statements cite `support.kind=path`.
9. Zero-edge/self paths are not promoted into path evidence and no invented `bounded_path` relation appears.
10. `candidate_context` path support states only that an endpoint path appeared in the other query packet and explicitly preserves the semantic boundary.
11. `--format=md` emits Markdown with top/bottom caveats and statement bullets containing both support and citations.
12. Existing graph-query and graph-path focused tests still pass.
13. In the framework source checkout, `graph-explain-accuracy-benchmark --format=json --fail-on-thresholds` passes permanent gold-labeled retrieval/ranking gates: micro recall >= 0.939, macro recall >= 0.94, strict P@8 >= 0.5, MRR >= 0.7, nDCG >= 0.75, layer recall = 1, gap accuracy = 1, negative-hit scenarios = 0, forbidden-field scenarios = 0, and watched files unchanged. Downstream hosts should not run source gold thresholds as a deployment gate.
14. Dynamic write/read workflow interpretation remains protected by the same no-semantic-authority and read-only assertions: graph explain output cannot satisfy read evidence after mutation and cannot claim freshness, required reads, confidence, or next action.

## Validation commands

Focused validation:

```bash
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=json --limit=8 --max-statements=8
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=md --limit=8 --max-statements=8
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

- Status: implemented-phase3-path-backed
- Primary files:
  - `.lazy-harness/tests/graph-explain.md` — this TDD record.
  - `.lazy-harness/spec/platform/graph-explain.md` — output contract.
  - `.lazy-harness/planning/graph-explain-implementation-plan.md` — phased implementation plan.
  - `.lazy-harness/scripts/graph-query.ts` — implements parser, `buildGraphExplain`, JSON output, `renderExplainMarkdown`, `explainPathTargets`, `buildExplainPathPackets`, and `pathPacketSupport`.
  - `.lazy-harness/scripts/self-test.py` — implements `check_graph_explain_cli` regression protection for JSON, Markdown, `--include-paths` path packets, zero-edge/self path non-evidence, and `candidate_context` boundary wording.
  - `.lazy-harness/bin/lazy` — advertises graph explain JSON/Markdown.
  - `.lazy-harness/evidence/2026-06-08-graph-explain-phase1-downstream-sync.md` — downstream sync/smoke validation capsule for Phase 1 JSON baseline.
  - `.lazy-harness/evidence/2026-06-09-graph-explain-phase2-markdown-downstream-sync.md` — downstream sync/smoke validation capsule for Phase 2 Markdown.
- Key symbols:
  - `GraphExplainResult`
  - `GraphExplainStatement`
  - `GraphExplainSupport`
  - `buildGraphExplain`
  - `renderExplainMarkdown`
  - `explainPathTargets`
  - `buildExplainPathPackets`
  - `pathPacketSupport`
  - `check_graph_explain_cli`
- Graph ids:
  - `kg_graph_explain_structural_tdd_20260608`
  - `kg_graph_explain_phase1_cli_20260608`
  - `kg_graph_explain_phase1_self_test_20260608`
  - `kg_graph_explain_phase1_downstream_sync_20260608`
  - `kg_graph_explain_phase2_markdown_cli_20260609`
  - `kg_graph_explain_phase2_markdown_self_test_20260609`
  - `kg_graph_explain_phase3_path_cli_20260609`
  - `kg_graph_explain_phase3_path_self_test_20260609`
  - `kg_graph_explain_phase2_downstream_sync_20260609`

## Layer completeness impact

- DDD: no new domain entity; Searchable Record Memory remains controlling for cue-only interpretation.
- BDD: no user-facing flow change; LLM-owned record retrieval remains controlling.
- SDD: `.lazy-harness/spec/platform/graph-explain.md` defines JSON/Markdown/path-backed contract.
- TDD: this record defines JSON/Markdown/path-backed fixtures.
- ADR: no new ADR for Phase 3 because it does not relax policy or add runtime/dependency architecture; required before semantic authority, MCP, daemon, watch mode, Graphify vendoring, or lifecycle/prompt policy changes.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains controlling.
- Planning: `.lazy-harness/planning/graph-explain-implementation-plan.md` tracks remaining phases.

## Rule placement

- Rule: Graph explain tests must prove explanation output is cited, structural, read-only, and non-authoritative.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/graph-explain.md`
- Why not AGENTS.md: regression fixtures and output-shape checks belong in TDD/source, not always-loaded prompt grammar.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed option A
