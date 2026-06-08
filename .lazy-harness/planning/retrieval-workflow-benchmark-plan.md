# Retrieval Workflow Benchmark Plan

Status: completed
Date: 2026-06-08
Layer: Planning
Related SDD: `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md`
Related TDD: `.lazy-harness/tests/retrieval-workflow-benchmark.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related ADR: `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md`
Related graph-query plan: `.lazy-harness/planning/graph-query-prototype-implementation-plan.md`

## Goal

Measure whether `lazy graph query` produces workflow-level retrieval cost improvements after the payload compactness slice.

Workflow-level means measuring post-overview helper calls, helper bytes/tokens, latency, structural candidate coverage, and a deterministic follow-up record-read simulation. It does **not** mean deciding what the user intended or proving required reads were semantically sufficient.

## Direction lock

Allowed:

- Add a read-only measurement CLI.
- Compare `map`, `map_plus_retrieval_audit`, and `graph_query` surfaces.
- Use deterministic candidate paths/counts and file byte sizes.
- Add self-test protection.
- Record benchmark evidence.

Forbidden in this slice:

- No lifecycle hook changes.
- No prompt injection changes.
- No overview hard-block relaxation.
- No raw user-text classifier.
- No `path`/`explain` implementation.
- No policy claim that graph query replaces real record/source/test reads.

## Implementation steps

1. [x] Create SDD `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md`.
2. [x] Create TDD `.lazy-harness/tests/retrieval-workflow-benchmark.md`.
3. [x] Implement `.lazy-harness/scripts/retrieval-workflow-benchmark.ts`.
4. [x] Wire `.lazy-harness/bin/lazy retrieval-workflow-benchmark` help/dispatcher.
5. [x] Add `.lazy-harness/scripts/self-test.py#check_retrieval_workflow_benchmark_cli`.
6. [x] Add manifest sync entries for SDD/TDD/plan if needed.
7. [x] Add graph rows.
8. [x] Run focused benchmark and full self-test.
9. [x] Record evidence capsule with aggregate benchmark interpretation.
10. [x] Commit and downstream sync if validation passes.

## Benchmark model

Queries:

- `retrieval coverage audit`
- `workflow compression not safety reduction`
- `capability registry`
- `lazy sync drift detection`

Surfaces:

- `map`: one post-overview helper call.
- `map_plus_retrieval_audit`: two post-overview helper calls.
- `graph_query`: one post-overview helper call.

Measured values:

- helper bytes and estimated tokens
- elapsed ms
- candidate record/source/test/graph counts
- DDD/BDD/SDD/TDD/SSOT structural coverage from record candidate paths
- simulated follow-up record reads to cover the five layers
- total estimated tokens = helper tokens + simulated follow-up read tokens

## Acceptance

- CLI JSON and Markdown work.
- No forbidden semantic-authority fields.
- Benchmark is read-only.
- Source self-test passes.
- Output includes policy-boundary warning.
- Evidence states what the benchmark proves and does not prove.

## Benchmark result — 2026-06-08

Focused benchmark output:

- JSON bytes: 26,839
- `map` total estimated tokens: 168,057
- `map_plus_retrieval_audit` total estimated tokens: 173,874
- `graph_query` total estimated tokens: 74,236
- `graph_query` vs `map_plus_retrieval_audit`: helper calls -4, helper tokens -16,076, total tokens -99,638
- `graph_query` vs `map`: helper calls 0, helper tokens -10,547, total tokens -93,821

Validation:

- `python3 .lazy-harness/scripts/self-test.py --scope framework` passed.
- Self-test count: scope=framework, ran=75, skipped=0.
- Evidence capsule: `.lazy-harness/evidence/2026-06-08-retrieval-workflow-benchmark.md`.
- Downstream sync/smoke: source commit `f77e073f700cb55895afa6aa8094317c4591e89b`, 14/14 hosts ok, failed 0.
- Downstream artifact: `/tmp/lazy-harness-retrieval-workflow-benchmark-sync/20260608T084456Z/summary.json`.

Interpretation:

- The deterministic proxy supports graph-query as a lower-cost post-overview retrieval helper.
- This still does not change lifecycle/prompt/overview/read-debt/option-gate policy.

## Rule placement

- Rule: Workflow-level benchmark is a transient measurement plan that can justify future discussion but cannot change lifecycle/prompt/overview behavior by itself.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/retrieval-workflow-benchmark-plan.md`
- Why not AGENTS.md: this is execution sequencing and benchmark methodology, not durable always-loaded prompt grammar.
- Why not `.jcode`: this is shared framework planning, not local/private Jcode workflow.
- Confirmation: user-approved next-stage execution inferred from graph-query plan and current request.

## Discovery capture

- DDD: no new domain entity; existing searchable record memory terms apply.
- BDD: no behavior change; benchmark must preserve LLM-owned retrieval.
- SDD: new retrieval workflow benchmark output contract created.
- TDD: new retrieval workflow benchmark regression record created.
- ADR: not required unless benchmark leads to policy proposal.
- SSOT: CLI tool boundary controls semantic authority.
- Planning: this file tracks the slice.
