# SDD — Retrieval Workflow Benchmark

Status: verified
Date: 2026-06-08
Layer: SDD
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related ADR: `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md`
Related SDD: `.lazy-harness/spec/platform/graph-query.md`, `.lazy-harness/spec/platform/retrieval-coverage-audit.md`, `.lazy-harness/spec/platform/prompt-budget.md`
Related TDD: `.lazy-harness/tests/retrieval-workflow-benchmark.md`
Related plan: `.lazy-harness/planning/retrieval-workflow-benchmark-plan.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - measuring whether `lazy graph query` reduces retrieval workflow cost after payload compactness
  - comparing `lazy map`, `lazy retrieval-audit`, and `lazy graph query` as cue-only helper surfaces
  - collecting evidence before any lifecycle/prompt/overview policy proposal
- Must:
  - remain read-only and deterministic
  - measure helper output bytes, approximate tokens, elapsed milliseconds, candidate counts, layer coverage, and simulated follow-up read counts/bytes
  - keep the LLM/searcher as semantic authority; output is measurement only
  - compare post-overview helper paths because `lazy map --overview` remains mandatory/common
  - include no `requiredRead`, `optionalRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, or `candidateMeanings` fields
  - preserve privacy by storing only command metrics, paths/counts, aggregate byte counts, and no raw user text/transcripts
- Must not:
  - classify raw user text
  - decide whether graph query should replace harness-first search/read debt
  - decide user intent, risk, gate, required reads, or next action
  - mutate canonical records, generated indexes, runtime journals, or memory
- Record completion:
  - changes update this SDD, `.lazy-harness/tests/retrieval-workflow-benchmark.md`, `.lazy-harness/scripts/retrieval-workflow-benchmark.ts`, `.lazy-harness/bin/lazy`, `.lazy-harness/scripts/self-test.py`, manifest sync entries, and graph rows together.

## CLI contract

Command:

```bash
.lazy-harness/bin/lazy retrieval-workflow-benchmark [--format=json|md] [--limit=N] [--queries=q1,q2]
```

Default query set should include representative framework retrieval cases:

- `retrieval coverage audit`
- `workflow compression not safety reduction`
- `capability registry`
- `lazy sync drift detection`

Output shape:

- `schemaVersion: "1.0"`
- `mode: "retrieval-workflow-benchmark"`
- `root`
- `querySet`
- `notes`
- `surfaces`: per-query metrics for:
  - `map`
  - `map_plus_retrieval_audit`
  - `graph_query`
- `summary`: aggregate metrics and deltas
- `policyBoundary`: stable text stating this is measurement-only and does not change lifecycle/prompt/overview policy

Per-surface metrics:

- `helperCalls`: number of post-overview helper commands in the measured path
- `helperBytes`
- `helperEstimatedTokens`: deterministic approximation `ceil(bytes / 4)`
- `elapsedMs`
- `resultState`: structural state if available
- `candidateCounts`: record/source/test/graph counts
- `layerCoverage`: DDD/BDD/SDD/TDD/SSOT booleans from candidate record paths only
- `followupRead`: deterministic simulation of the smallest candidate record prefix needed to cover DDD/BDD/SDD/TDD/SSOT, plus file byte/token totals
- `totalEstimatedTokens`: helper estimated tokens + follow-up read estimated tokens

Forbidden fields anywhere in output:

```text
requiredRead optionalRead confidence intent risk gate nextAction candidateMeanings
```

## Measurement semantics

The benchmark measures **post-overview retrieval helper cost**. This is the canonical `post-overview helper cost` benchmark for comparing retrieval helper paths. The mandatory overview step is common and remains unchanged, so it is not counted in the compared helper paths.

Measured paths:

1. `map`: run `lazy map <query> --format=json --limit=N --fresh` so the benchmark rebuilds from source in-process without refreshing generated record-index cache.
2. `map_plus_retrieval_audit`: run map plus `lazy retrieval-audit <query> --format=json --limit=N` and merge candidates.
3. `graph_query`: run `lazy graph query <query> --format=json --limit=N`.

Follow-up read simulation:

- Uses candidate record paths only.
- Walks candidate order until DDD/BDD/SDD/TDD/SSOT are covered or candidates are exhausted.
- Counts bytes from files that exist inside the current host root.
- This is **not** semantic proof that those are the correct reads; it is a deterministic cost proxy.

## Implementation map

- Status: verified
- Primary files:
  - `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md` — this SDD contract.
  - `.lazy-harness/tests/retrieval-workflow-benchmark.md` — TDD fixture contract.
  - `.lazy-harness/scripts/retrieval-workflow-benchmark.ts` — read-only measurement CLI.
  - `.lazy-harness/bin/lazy` — dispatcher/help entry.
  - `.lazy-harness/scripts/self-test.py` — regression fixture.
  - `.lazy-harness/scripts/record-map.ts` — measured helper, invoked with `--fresh` to avoid generated cache writes.
  - `.lazy-harness/scripts/retrieval-coverage-audit.ts` — measured helper.
  - `.lazy-harness/scripts/graph-query.ts` — measured helper.
- Key symbols planned:
  - `buildBenchmark`
  - `measureQuery`
  - `simulateFollowupRead`
  - `RetrievalWorkflowBenchmark`
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_retrieval_workflow_benchmark_cli`
- Machine index:
  - graph ids: `kg_retrieval_workflow_benchmark_cli_20260608`, `kg_retrieval_workflow_benchmark_self_test_20260608`, `kg_retrieval_workflow_benchmark_evidence_20260608`, `kg_retrieval_workflow_benchmark_manifest_20260608`

## Layer completeness impact

- DDD: no new domain term; existing Searchable Record Memory applies.
- BDD: reinforces LLM-owned retrieval behavior, no behavior automation change.
- SDD: this record defines measurement output and boundaries.
- TDD: `.lazy-harness/tests/retrieval-workflow-benchmark.md` and self-test protect measurement-only behavior.
- ADR: no new ADR required for measurement-only helper; ADR required before policy relaxation.
- SSOT: CLI semantic boundary remains `.lazy-harness/ssot/cli-tool-boundary.md`.
- Planning: `.lazy-harness/planning/retrieval-workflow-benchmark-plan.md` tracks execution.

## Rule placement

- Rule: Retrieval workflow benchmark is a read-only measurement helper for comparing cue surfaces, not a semantic authority or policy-changing router.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md`
- Why not AGENTS.md: output contract and measurement details belong in SDD/TDD/source, not always-loaded prompt grammar.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-approved next-stage execution inferred from graph-query plan and current request.
