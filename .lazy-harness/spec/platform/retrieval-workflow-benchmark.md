# SDD — Retrieval Workflow Benchmark

Status: verified
Date: 2026-06-15
Layer: SDD
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related ADR: `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md`
Related SDD: `.lazy-harness/spec/platform/retrieval-coverage-audit.md`, `.lazy-harness/spec/platform/prompt-budget.md`
Related TDD: `.lazy-harness/tests/retrieval-workflow-benchmark.md`
Related plan: `.lazy-harness/planning/retrieval-workflow-benchmark-plan.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - measuring post-overview retrieval helper cost after graph query/path/explain CLI removal
  - comparing `lazy map` and `lazy retrieval-audit` as cue-only helper surfaces
  - collecting evidence before any lifecycle/prompt/overview policy proposal
- Must:
  - remain read-only and deterministic
  - measure helper output bytes, approximate tokens, elapsed milliseconds, candidate counts, layer coverage, and simulated follow-up read counts/bytes
  - keep the LLM/searcher as semantic authority; output is measurement only
  - compare post-overview helper paths because `lazy map --overview` remains mandatory/common
  - additionally measure the `no_map` root-bound grep fallback path and the otherwise-excluded `overview` cost so map can be compared against skipping map
  - include no `requiredRead`, `optionalRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, or `candidateMeanings` fields
  - preserve privacy by storing only command metrics, paths/counts, aggregate byte counts, and no raw user text/transcripts
- Must not:
  - classify raw user text
  - reintroduce `lazy graph query`, `lazy graph path`, or `lazy graph explain` as benchmark surfaces
  - decide user intent, risk, gate, required reads, or next action
  - mutate canonical records, generated indexes, runtime journals, or memory
- Record completion:
  - changes update this SDD, `.lazy-harness/tests/retrieval-workflow-benchmark.md`, `.lazy-harness/scripts/retrieval-workflow-benchmark.ts`, `.lazy-harness/bin/lazy`, `.lazy-harness/scripts/self-test.py`, manifest sync entries, and graph rows together.

## CLI contract

Command:

```bash
.lazy-harness/bin/lazy retrieval-workflow-benchmark [--format=json|md] [--limit=N] [--queries=q1,q2]
```

Default node set should include representative concrete framework map nodes:

- `map-first-retrieval`
- `record-source-indexing`
- `capability-registry`
- `sync-install-update`

Output shape:

- `schemaVersion: "1.0"`
- `mode: "retrieval-workflow-benchmark"`
- `root`
- `querySet`
- `notes`
- `surfaces`: per-query metrics for:
  - `map`
  - `map_plus_retrieval_audit`
  - `no_map`
- `overview`: the otherwise-excluded mandatory `lazy map --overview` cost (command, helperBytes, helperEstimatedTokens, elapsedMs)
- `summary`: aggregate metrics per surface, `mapInclusive` (overview added back per task), and deltas (`mapPlusRetrievalAuditVsMap`, `noMapVsMap`, `noMapVsMapInclusive`)
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

The benchmark measures **post-overview retrieval helper cost** plus, since this revision, the otherwise-excluded `overview` cost and a `no_map` path that skips `lazy map` entirely. `map` and `map_plus_retrieval_audit` remain the canonical `post-overview helper cost` comparison; `overview` is reported separately and added back as `mapInclusive` so the map workflow can be compared honestly against `no_map`.

Measured paths:

1. `map`: run `lazy map <query> --format=json --limit=N --fresh` so the benchmark rebuilds from source in-process without refreshing generated record-index cache.
2. `map_plus_retrieval_audit`: run map plus `lazy retrieval-audit <query> --format=json --limit=N` and merge candidates.
3. `no_map`: run `grep -rliE <term-alternation> .lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning}`, the AGENTS.md root-bound fallback that skips `lazy map`. The grep pattern is a deterministic alternation of the query's split terms.

Overview cost:

- The overview reports the otherwise-excluded mandatory `lazy map --overview` cost once (command, bytes, tokens, elapsed); `mapInclusive` adds the overview tokens back per task.

Follow-up read simulation:

- Uses candidate record paths only.
- Walks candidate order until DDD/BDD/SDD/TDD/SSOT are covered or candidates are exhausted.
- Counts bytes from files that exist inside the current host root.
- This is **not** semantic proof that those are the correct reads; it is a deterministic cost proxy.
- The `no_map` candidate set is unranked and the alternation grep is intentionally broad, so its follow-up read total is a conservative upper bound that is sensitive to candidate ordering (record paths are sorted for determinism). Trust the `no_map` helper cost and candidate counts as the primary signal; the read-until-covered total overstates a real targeted agent read.

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
- Key symbols:
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
- SDD: this record defines measurement output and graph-CLI-removed boundaries.
- TDD: `.lazy-harness/tests/retrieval-workflow-benchmark.md` and self-test protect measurement-only behavior.
- ADR: no new ADR required for measurement-only helper; ADR required before policy relaxation.
- SSOT: CLI semantic boundary remains `.lazy-harness/ssot/cli-tool-boundary.md`.
- Planning: graph CLI rollback intent is captured in `.lazy-harness/knowledge/candidates.jsonl` and should be promoted to `.lazy-harness/planning/graph-cli-rollback-plan.md` if more work remains.

## Rule placement

- Rule: Retrieval workflow benchmark is a read-only measurement helper for comparing cue surfaces, not a semantic authority or policy-changing router.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md`
- Why not AGENTS.md: output contract and measurement details belong in SDD/TDD/source, not always-loaded prompt grammar.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private Jcode wiring.

## Discovery capture

- DDD: none.
- BDD: updated by implication only; graph CLI removal restores real record/source/test read emphasis.
- SDD: updated here.
- TDD: updated in `.lazy-harness/tests/retrieval-workflow-benchmark.md`.
- ADR: none.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` should no longer advertise graph query/path/explain as active cue helpers.
- Planning: graph CLI rollback captured as candidate/plan follow-up.
