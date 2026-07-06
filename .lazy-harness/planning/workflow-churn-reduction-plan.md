# Planning — Workflow Churn Reduction (pre-commit scope, capture-gate FP, batched capture)

Status: proposed-plan (2026-07-05; per-step execution approval required — ADR 0038)
Layer: Planning
Source: 2026-07-05 graph-hygiene session — user frustration + measured evidence that a routine session burned ~57min on pre-commit self-test alone (31 commits × 111s), plus 13+ capture-gate false positives.
Consolidates candidates: `candidate-precommit-test-scope-optimization-20260705`, `candidate-draft-first-batched-capture-20260705`, `candidate-parallel-atomic-append-capture-20260705`, `candidate-workflow-parallel-subagents-and-batching-20260705`, `candidate-host-worktree-symlink-propagation-20260705`.

## Problem (measured)

- `lazy test` (self-test.py --scope framework, 84 checks) = **111s**. NOT process startup (bun cold-start=2ms, one script=27ms). ~85% is ~8 heavy lifecycle/integration checks: lifecycle fixture intake 20.6s, lifecycle parity 18.7s, 5d-5 lifecycle hook 14.1s, response.completed telemetry 13.2s (top4=60%), Pi package layout 6.2s, retrieval-workflow-benchmark 5.7s, affected-test-runner 4.1s, lazy-sync prune 3.1s.
- pre-commit runs the FULL suite regardless of change scope → a `candidates.jsonl`/`.md`-only commit pays the same 111s as a lifecycle code change.
- Capture-gate (analysis-discovery-capture) fired 13+ false positives on recap / already-captured / in-turn-write turns.
- Net: churn = (many small commits) × (111s each) + (gate interruptions).

## Fixes (priority order)

### Fix 1 — pre-commit scope to changed areas (biggest win, low risk)

- pre-commit hook computes `git diff --cached --name-only`; if only record/doc/candidate paths changed (layer `.md`, `knowledge/*.jsonl`, planning, retrospective) and NOT `scripts/**`/`hooks/**`/`manifests/**`/`packages/**`/`bin/lazy`/schemas → run a LIGHT gate (`record-lint` + `graph-hygiene` + schema/JSON validation, ~5-10s).
- Heavy lifecycle/pi-package/benchmark checks run only when their code changed, or always at pre-PUSH.
- Implement: self-test gains a `--light`/scoped mode (subset of checks); pre-commit hook selects mode by diff. ADR 0016 says commit=blocking gate, not commit=full-suite — consistent.
- Safety: record-only changes cannot break hook/lifecycle code checks (those test code, not records). Needs a TDD fixture proving the light gate still catches record-lint/graph-hygiene regressions.

### Fix 2 — capture-gate false-positive suppression

- `hooks/lifecycle/helpers/check-analysis-discovery-capture` (+ Pi adapter payload): before emitting STOP, inspect this turn's `recent_tool_calls` `edit_target` for a write to `.lazy-harness/knowledge/candidates.jsonl`, any `.lazy-harness/<layer>` record, or retro feedback → treat the capture obligation as satisfied and do not fire. Also suppress on pure-recap turns (no lazy-root mutation this turn).
- Already backlogged: `.lazy-harness/planning/analysis-discovery-capture-backlog.md`, `.lazy-harness/tests/capture-gate-false-positive.md` (pattern promoted ×3+ earlier; 13+ instances 2026-07-05).

### Fix 3 — draft-first batched capture (behavioral + tooling)

- During work, append facts cheaply to the DRAFT tier (`candidates.jsonl`/`graph-drafts.jsonl`) with no gate and no commit; main agent verifies + promotes to canonical and commits ONCE per logical unit at turn end. Compounds with Fix 1 (fewer commits × cheaper commits).
- Optional add-on: parallel read-only subagents for multi-target investigation; parallel cheap-model atomic single-line appends to the draft tier (safe per POSIX O_APPEND); single-writer only for in-place edits + canonical promotion (`candidate-parallel-atomic-append-capture`).

## Sequencing

Fix 1 (mechanical, ~90% of a record-only commit's time removed, low risk) → Fix 2 (helper logic, removes gate interruptions) → Fix 3 (behavioral + optional parallel tooling).

## Discovery capture

- ADR: candidate — gate-scope policy (pre-commit vs pre-push subset) needs an ADR; amends/relies on ADR 0016.
- SDD: candidate — self-test scope modes contract; capture-gate suppression contract (pre-response-rule-context / analysis-discovery-capture-gate).
- TDD: candidate — light-gate still catches record-lint/graph-hygiene regressions; capture-gate suppression fixtures.
- Planning: this record.
- DDD/BDD/SSOT: none.

## Rule placement

- Rule: how the commit/push gate scopes checks + when the analysis-discovery-capture gate fires.
- Scope: framework-global.
- Primary record: this plan (proposed); on execution → ADR (gate-scope) + `.lazy-harness/scripts/self-test.py` + lifecycle helper + `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md` amendment.
- Confirmation: needs-option-gate (which fix to implement first; light-gate check subset).
