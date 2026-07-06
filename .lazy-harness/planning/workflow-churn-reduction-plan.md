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
- Implement: self-test gains a `--light`/scoped mode (subset of checks); pre-commit hook selects mode by diff. CORRECTION (2026-07-05, grounded in ADR 0016): ADR 0016's 2026-05-19 amendment (lines 72-73) EXPLICITLY specifies BOTH `pre-commit-guard.sh` AND `pre-push` run the full `.lazy-harness/bin/lazy test` — i.e. the full 84-check suite runs at commit AND again at push (2× redundancy, by design). So making pre-commit a LIGHT subset is an ADR 0016 AMENDMENT (change 'both gates full' → 'pre-commit light/scoped, pre-push full'), NOT merely 'consistent with' it. Standard defense-in-depth: cheap gate at commit, thorough at push.
- Safety: record-only changes cannot break hook/lifecycle code checks (those test code, not records). Needs a TDD fixture proving the light gate still catches record-lint/graph-hygiene regressions.
- **APPLIED 2026-07-05 (user-approved):** `self-test.py --light` (skips `HEAVY_CHECK_NAMES` ~22 measured-heavy checks; framework scope 111s→16s), wired into `pre-commit-guard.sh` (both invocation paths); `pre-push.sh` keeps full. ADR 0016 §0b + ADR 0022 + cli-tool-boundary + bin/lazy help amended. ADR 0011 negative test: broken `logs/actions.jsonl` line → `--light` rc=1 (blocks), restore → rc=0. NOTE: this is the fixed-heavy-set variant, NOT the diff-scoped variant originally sketched above — simpler + errs toward more checking at commit (new checks default light-included).

### Fix 1b — parallelize the full self-test (process pool) — arguably the best single lever (keeps full coverage)

- The 85 checks run sequentially (`for check, tag in checks: check()` — a check registry exists). Most are isolated (14 `TemporaryDirectory` + `__tmp_..._{os.getpid()}` pid-scoped fixtures). Run them concurrently via a PROCESS pool (`ProcessPoolExecutor`) — NOT threads: fixtures are `os.getpid()`-scoped, so threads (shared pid) collide; separate processes get distinct pids.
- `fail()` raises `SystemExit(1)`; workers must catch it per-check and collect failures (do not abort the pool); report all failures at the end.
- Expected: 111s → bounded by the slowest single check (~20s: lifecycle intake) + overhead ≈ 25-35s on a multi-core box, with FULL coverage preserved (unlike the Fix 1 subset).
- REQUIRED pre-step: audit for checks that write SHARED repo state (generated indexes, the real `knowledge/graph.jsonl`, canonical files) rather than a tempdir/pid-scoped path — run those few serially or isolate them; everything else parallel. Governed by ADR 0022/0026 (framework-owned self-test scope).
- Best combo: Fix 1 (record-only commits → light subset) + Fix 1b (when the full suite runs, run it parallel).

### Fix 2 — capture-gate false-positive suppression

- `hooks/lifecycle/helpers/check-analysis-discovery-capture` (+ Pi adapter payload): before emitting STOP, inspect this turn's `recent_tool_calls` `edit_target` for a write to `.lazy-harness/knowledge/candidates.jsonl`, any `.lazy-harness/<layer>` record, or retro feedback → treat the capture obligation as satisfied and do not fire. Also suppress on pure-recap turns (no lazy-root mutation this turn).
- Already backlogged: `.lazy-harness/planning/analysis-discovery-capture-backlog.md`, `.lazy-harness/tests/capture-gate-false-positive.md` (pattern promoted ×3+ earlier; 13+ instances 2026-07-05).

### Fix 3 — draft-first batched capture (behavioral + tooling)

- During work, append facts cheaply to the DRAFT tier (`candidates.jsonl`/`graph-drafts.jsonl`) with no gate and no commit; main agent verifies + promotes to canonical and commits ONCE per logical unit at turn end. Compounds with Fix 1 (fewer commits × cheaper commits).
- Optional add-on: parallel read-only subagents for multi-target investigation; parallel cheap-model atomic single-line appends to the draft tier (safe per POSIX O_APPEND); single-writer only for in-place edits + canonical promotion (`candidate-parallel-atomic-append-capture`).

## Sequencing

Fix 1 (mechanical, ~90% of a record-only commit's time removed, low risk) → Fix 2 (helper logic, removes gate interruptions) → Fix 3 (behavioral + optional parallel tooling).

## 2026-07-05 applied — host pre-push #1 bottleneck fixed (measured on medivance)

A host session profiled pre-PUSH (not pre-commit) on medivance: `.lazy-harness/bin/lazy test` = **441s**, of which **`check_lazy_sync_prunes_stale_managed_files` = 309.7s (72%)**. Root cause: that check runs `bun lazy-sync.ts --from <ROOT> --target <temp> --force` = a FULL managed-tree sync/prune, cost linear in host size (371 records). Other slow BOTH checks: doctor C17 negative 39s, lifecycle intake 20s, doctor D07 package-health 18.7s, retrieval benchmark 13.3s, response.completed telemetry 13.2s.

APPLIED (user-approved option gate): tag `check_lazy_sync_prunes_stale_managed_files` BOTH → FRAMEWORK_ONLY (self-test.py) + ADR 0026 amendment (Record completion rule). It re-verifies framework lazy-sync code; hosts get that verification on the framework source, so re-running it per host push is redundant + O(host-size). Verified: `--scope host` skips it (ran 58→57), `--scope framework` still runs it (ran 84). Effect: host pre-push 441s → ~130s once hosts `lazy update`. NOT changed: the other slow BOTH checks (doctor/lifecycle/benchmark/telemetry) — left for per-check evaluation (user chose #1-only scope).

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
