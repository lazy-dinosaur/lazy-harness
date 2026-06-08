# Graph Query Coverage and Ranking Hardening Plan

Status: validated
Date: 2026-06-08
Layer: Planning
Related SDD: `.lazy-harness/spec/platform/graph-query.md`
Related TDD: `.lazy-harness/tests/graph-query.md`
Related evidence: `.lazy-harness/evidence/2026-06-08-retrieval-workflow-benchmark.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
Related DDD: `.lazy-harness/domain/searchable-record-memory.md`

## Goal

Improve `lazy graph query` candidate ranking and layer bridge coverage after the workflow benchmark showed `graph_query` is a workflow-cost win but has full DDD/BDD/SDD/TDD/SSOT coverage for only 1 of 4 benchmark queries.

## Current measured baseline

Command:

```bash
.lazy-harness/bin/lazy retrieval-workflow-benchmark --format=json --limit=8
```

Baseline summary:

- `graph_query` total estimated tokens: `74,236`
- `map_plus_retrieval_audit` total estimated tokens: `173,874`
- `graph_query` full layer coverage: `1/4`
- Miss pattern:
  - `workflow compression not safety reduction`: graph_query misses DDD, BDD, TDD.
  - `capability registry`: graph_query misses DDD, BDD.
  - `lazy sync drift detection`: graph_query misses DDD, BDD.

## Hypothesis

The misses are not from graph-query failure to find topical SDD/SSOT/ADR records. They are mostly from missing or low-ranked cross-layer bridge records:

- Generic retrieval-boundary DDD/BDD records are relevant to graph-query output because graph-query itself is a retrieval helper:
  - DDD: `.lazy-harness/domain/searchable-record-memory.md`
  - BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- Some TDD records are matched by text or protection relationship but rank outside the small `--limit=8` record candidate budget.

## Direction lock

Allowed:

- Add deterministic layer bridge candidate surfacing in `graph-query.ts`.
- Add layer-aware ordering that preserves direct topical matches while reserving room for verified missing-layer bridges.
- Add self-test assertions and benchmark validation.
- Update SDD/TDD/graph rows/manifest/evidence.

Forbidden:

- No `lazy graph path` or `lazy graph explain` implementation.
- No overview/read-debt/lifecycle/prompt policy change.
- No generated or inferred fake DDD/BDD records.
- No semantic-authority fields such as `requiredRead`, `confidence`, `risk`, `gate`, `nextAction`, or candidate meaning labels.
- No benchmark metric weakening to hide misses.

## Implementation steps

1. [x] Update SDD `.lazy-harness/spec/platform/graph-query.md` with layer bridge/ranking hardening contract.
2. [x] Update TDD `.lazy-harness/tests/graph-query.md` with layer bridge and benchmark coverage fixtures.
3. [x] Implement graph-query layer bridge candidates:
   - add DDD/BDD retrieval-boundary bridge records when record candidates exist and those layers are missing,
   - add matched/protection TDD bridge records when query text or graph/protection records justify them,
   - order direct matches first but reserve small room for missing-layer bridge records.
4. [x] Add self-test assertions:
   - `workflow compression not safety reduction` graph query includes five layers at `--limit=8`,
   - workflow benchmark graph_query full layer coverage improves beyond 1/4,
   - graph_query remains below map_plus_retrieval_audit total tokens,
   - forbidden semantic-authority fields remain absent.
5. [x] Run focused validation and full framework self-test.
6. [x] Record benchmark result and graph rows.
7. [ ] Commit and downstream sync if validation passes.

## Acceptance

- `lazy graph query 'workflow compression not safety reduction' --format=json --limit=8` includes DDD, BDD, SDD, TDD, and SSOT record candidates.
- `lazy retrieval-workflow-benchmark --format=json --limit=8` reports `graph_query` full-layer coverage greater than `1/4`.
- `graph_query` total estimated tokens remain below `map_plus_retrieval_audit` total estimated tokens.
- `retrieval coverage audit` graph query `--limit=20` stays below the existing 40,000-byte compactness guard.
- `python3 .lazy-harness/scripts/self-test.py --scope framework` passes.

## Validation result — 2026-06-08

Focused validation:

- `lazy graph query 'workflow compression not safety reduction' --format=json --limit=8`
  - bytes: 13,046
  - record candidate coverage: DDD/BDD/SDD/TDD/SSOT all present
- `lazy graph query 'retrieval coverage audit' --format=json --limit=20`
  - bytes: 29,751
  - compactness guard: below 40,000 bytes
- `lazy retrieval-workflow-benchmark --format=json --limit=8`
  - `graph_query` full layer coverage: 4/4, improved from 1/4 baseline
  - `graph_query` total estimated tokens: 68,713
  - `map_plus_retrieval_audit` total estimated tokens: 176,460
  - token win preserved: `graph_query` remains lower by 107,747 estimated tokens

Full validation:

- `python3 .lazy-harness/scripts/self-test.py --scope framework` passed.
- self-test count: scope=framework, ran=75, skipped=0.

Interpretation:

- Coverage/ranking hardening met the slice acceptance criteria.
- This still does not approve lifecycle/prompt/overview/read-debt/option-gate policy relaxation.

## Plan self-review

- This plan addresses the measured bottleneck directly: layer coverage misses, not token size.
- It preserves Graphify-inspired direction while staying inside lazy-harness boundaries.
- It does not use CLI output as semantic authority.
- It does not change policy, lifecycle hooks, prompt injection, or overview hard-block behavior.
- It uses existing canonical DDD/BDD records as bridges, not newly invented generated facts.

## Discovery capture

- DDD: existing `.lazy-harness/domain/searchable-record-memory.md` applies; no new DDD term required.
- BDD: existing `.lazy-harness/behavior/llm-owned-record-retrieval.md` applies; no user-visible behavior automation change.
- SDD: `.lazy-harness/spec/platform/graph-query.md` updated.
- TDD: `.lazy-harness/tests/graph-query.md` updated.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains controlling.
- ADR: no ADR required because this is retrieval-helper quality, not policy change.
- Evidence: benchmark result will update evidence only after validation.

## Rule placement

- Rule: Graph-query coverage/ranking hardening is a transient implementation plan that can improve benchmark coverage but cannot change lifecycle/prompt/overview/read-debt policy.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/graph-query-coverage-ranking-hardening-plan.md`
- Why not AGENTS.md: this is execution sequencing and benchmark acceptance, not durable always-loaded prompt grammar.
- Why not `.jcode`: this is shared lazy-harness framework planning, not local/private Jcode-only wiring.
- Confirmation: user-approved next-step execution.
