# TDD — Retrieval Workflow Benchmark

Status: verified
Date: 2026-06-15
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related plan: `.lazy-harness/planning/retrieval-workflow-benchmark-plan.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - adding or changing retrieval workflow benchmark measurement
  - comparing `lazy map` and `lazy retrieval-audit` after graph query/path/explain CLI removal
  - using benchmark results as evidence before workflow/prompt/lifecycle proposals
- Must:
  - protect JSON and Markdown output shapes
  - verify output is read-only, deterministic enough for self-test, and privacy-safe
  - verify forbidden semantic-authority fields are absent recursively
  - verify benchmark compares `map` and `map_plus_retrieval_audit`
  - verify `map_plus_retrieval_audit` is measured as two post-overview helper calls
  - verify candidate counts, layer coverage, follow-up read simulation, and aggregate totals exist
  - verify dispatcher help exposes `retrieval-workflow-benchmark`
- Must not:
  - require or call removed `lazy graph query/path/explain` commands
  - assert policy relaxation, next action, required reads, confidence, risk, or intent
  - write runtime journals, generated indexes, records, or memory
- Record completion:
  - changes update this TDD, SDD, source, dispatcher, self-test, manifest, and graph rows together.

## Regression fixtures

| Fixture | Input | Expected |
|---|---|---|
| `retrieval_workflow_benchmark_shape` | default benchmark JSON | mode/schema/querySet/surfaces/summary/policyBoundary present |
| `retrieval_workflow_benchmark_surfaces` | default query set | each query has `map` and `map_plus_retrieval_audit` surfaces |
| `retrieval_workflow_benchmark_counts` | default query set | helper bytes/tokens, candidate counts, layer coverage, follow-up read count/bytes, and total estimated tokens are numeric |
| `retrieval_workflow_benchmark_no_semantic_fields` | recursive JSON walk | no forbidden semantic-authority fields appear |
| `retrieval_workflow_benchmark_read_only` | temp host fixture | benchmark does not mutate canonical graph, generated caches, or runtime files |
| `retrieval_workflow_benchmark_dispatcher` | `lazy help` and `lazy retrieval-workflow-benchmark --format=md` | help advertises command and markdown report prints measurement-only warning |

Forbidden keys anywhere in output:

```text
requiredRead optionalRead confidence intent risk gate nextAction candidateMeanings
```

## Acceptance assertions

Self-test must verify:

1. `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md` exists.
2. `.lazy-harness/tests/retrieval-workflow-benchmark.md` exists.
3. `.lazy-harness/scripts/retrieval-workflow-benchmark.ts` exists.
4. `.lazy-harness/bin/lazy retrieval-workflow-benchmark --format=json --limit=8` returns valid JSON.
5. `schemaVersion == "1.0"` and `mode == "retrieval-workflow-benchmark"`.
6. Default query set includes at least `retrieval coverage audit` and `workflow compression not safety reduction`.
7. Every query contains surfaces `map` and `map_plus_retrieval_audit` only.
8. Recursive forbidden-key check passes.
9. `map_plus_retrieval_audit.helperCalls == 2`.
10. Follow-up read simulation reports `recordPaths`, `readCount`, `bytes`, `estimatedTokens`, and `coveredLayers`.
11. Markdown output contains `measurement-only` and `does not change lifecycle/prompt/overview policy`.
12. Source validation can run the benchmark without mutating `.lazy-harness/knowledge/graph.jsonl` or `.lazy-harness/generated/record-index.json`; benchmark invokes `lazy map --fresh` for the measured map surface.

## Validation commands

Focused validation:

```bash
.lazy-harness/bin/lazy retrieval-workflow-benchmark --format=json --limit=8
.lazy-harness/bin/lazy retrieval-workflow-benchmark --format=md --limit=8
python3 -m py_compile .lazy-harness/scripts/self-test.py
```

Full validation:

```bash
python3 .lazy-harness/scripts/self-test.py --scope framework
```

## Interpretation guard

A benchmark result is evidence for further discussion only. It is not approval to:

- skip `lazy map --overview`,
- skip real record/source/test reads,
- change lifecycle hooks,
- reintroduce graph-query output into prompts automatically,
- implement graph `path`/`explain`,
- or change option-gate/read-debt rules.

## Implementation map

- Status: verified
- Primary files:
  - `.lazy-harness/tests/retrieval-workflow-benchmark.md` — this TDD record.
  - `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md` — measurement contract.
  - `.lazy-harness/scripts/retrieval-workflow-benchmark.ts` — CLI implementation.
  - `.lazy-harness/bin/lazy` — dispatcher/help wiring.
  - `.lazy-harness/scripts/self-test.py` — regression fixture.
- Key symbols:
  - `check_retrieval_workflow_benchmark_cli`
  - `buildBenchmark`
  - `measureQuery`
  - `simulateFollowupRead`
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
- Machine index:
  - graph ids: `kg_retrieval_workflow_benchmark_cli_20260608`, `kg_retrieval_workflow_benchmark_self_test_20260608`, `kg_retrieval_workflow_benchmark_evidence_20260608`, `kg_retrieval_workflow_benchmark_manifest_20260608`

## Layer completeness impact

- DDD: no new terms.
- BDD: confirms LLM-owned retrieval behavior remains unchanged and real reads remain required.
- SDD: `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md` defines contract.
- TDD: this record and self-test protect benchmark behavior after graph CLI removal.
- ADR: none for measurement-only helper; ADR needed before policy changes.
- SSOT: CLI boundary remains `.lazy-harness/ssot/cli-tool-boundary.md`.
- Planning: graph CLI rollback intent captured separately.
