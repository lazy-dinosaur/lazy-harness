# Planning — Workflow Churn Reduction (pre-commit scope, capture-gate FP, batched capture)

Status: mixed — Fix 1, bounded process validation, host pre-push scope, primary-canonical-record guard, bounded-validation orchestration, Fix 2b/2c/2d are applied and deployed; Fix 3 and remaining Fix 2 work remain proposed
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
- Best combo: Fix 1 (record-only commits → light subset) + Fix 1b (when the full suite runs, run audited checks in bounded process phases).

#### Applied 2026-07-23 — validation orchestration + bounded process phases

User approved the full improvement after a Medivance session ran a 147.5-second host `lazy test`, edited evidence records, then selected another full `lazy test`. Root cause was a framework integration gap: `lazy validate` and `lazy check` existed, but no capability/policy surfaced them as the preferred agent path; validation-evidence policies emphasized proving completion, Pi exposed only `/lazy-test`, evidence capsules invalidated the full cache, and self-test remained sequential.

Applied:

1. recommend-level `bounded-validation-orchestration` capability/policy;
2. AGENTS and Pi prompt guidance: `lazy check` during edits, focused checks for changed behavior, one `lazy validate --plan standard` after the final mutation, direct `lazy test` only for explicit fresh full regression or commit/push/release gates;
3. Pi `/lazy-check` and `/lazy-validate` commands, with `/lazy-test` explicitly described as fresh/full;
4. cache version 3 excludes only runtime/derived paths and `.lazy-harness/evidence/**`, while binding evidence to resolved host root, dependency manifests/locks, and Python/Bun/Git signatures; source, tests, contracts, policy, graph, planning, and canonical layer records remain regression-relevant;
5. self-test defaults to at most four process workers across separately audited static/isolated, PID-fixture, and stable-repository-reader phases; fixed-path/canonical-state checks stay serial, worker runtime roots are isolated, output is emitted in registry order, and `--jobs=1` preserves serial fail-fast fallback.

Focused measurement before final closure: host-scope light validation completed `ran=51, skipped=35` with `--jobs 4` in **12.993s**. This is not the final full-suite performance measurement; final standard validation remains the single closure boundary.

### Fix 2 — capture-gate false-positive suppression

- `hooks/lifecycle/helpers/check-analysis-discovery-capture` (+ Pi adapter payload): before emitting STOP, inspect this turn's `recent_tool_calls` `edit_target` for a write to `.lazy-harness/knowledge/candidates.jsonl`, any `.lazy-harness/<layer>` record, or retro feedback → treat the capture obligation as satisfied and do not fire. Also suppress on pure-recap turns (no lazy-root mutation this turn).
- Already backlogged: `.lazy-harness/planning/analysis-discovery-capture-backlog.md`, `.lazy-harness/tests/capture-gate-false-positive.md` (pattern promoted ×3+ earlier; 13+ instances 2026-07-05).

### Fix 2b — applied 2026-08-18: once-per-turn re-grounding and resolver de-duplication

- Dogfood symptom: a one-line Medivance source correction caused the Pi session to stop after each file operation, re-read the full mid-turn reminder, manually chain eight capability intents, and rediscover nearby code before continuing.
- Confirmed framework root cause: `index.ts#tool_result` set `pendingRegroundByRoot` after every successful file operation even when `regroundBodyByRoot` already held the turn's injected body. `operating_rule_catalog.py` simultaneously told the agent to resolve any matching-looking intent `FIRST`, although source context had already resolved exact mechanical intents.
- User-confirmed repair: preserve all pre-existing dirty/canonical work in `rescue/main-dirty-20260818` (`129e90c`), rebase `main` onto `origin/main`, then fix the framework source before downstream sync.
- Applied behavior: successful file operations collapse into at most one `context` reminder per normal turn; later same-turn operations do not restart discovery. `before_agent_start` and explicit steer boundaries reset the cache and permit one fresh reminder.
- Applied resolver guidance: the full catalog is discovery-only; never resolve every listed intent or chain resolver calls; resolve only one immediate rule-governed intent when needed; reuse already-resolved source guidance.
- Protection/rollout: Pi fake runtime covers pre-context batching, failed-hook retry, same-turn suppression, fresh-turn reset, and explicit steer reset; catalog fixtures protect no-chain/no-rerun copy. Canonical source is committed/pushed first, then Medivance receives the framework update without direct edits to copied framework files.

### Fix 2c — applied 2026-08-18: eliminate validation after each micro-edit

- User correction: the primary complaint was not only repeated context re-grounding; the harmful loop was `one tiny edit → test/check → one tiny edit → test/check`. The first `5e8530d` push did not yet remove that validation cadence.
- Confirmed framework cause: `bounded-validation-orchestration` matched `iterating_after_edit`; capability actions, policy summary, Pi prompt, skill, test strategy, and SDD repeatedly said to use `lazy check` "during edit loops", while the SDD explicitly said the fast tier runs "after every edit". Agents could reasonably interpret those surfaces as a validation command after every micro-edit even though full `lazy test` repetition was forbidden.
- Applied framework behavior: remove `iterating_after_edit`; explicitly prohibit any validation command after each micro-edit; finish a coherent mutation batch first; run one `lazy check` at a deliberate checkpoint; run focused/affected validation at most once per changed-behavior batch when needed; run one standard plan only after the final mutation.
- Host deployment completed 2026-08-18 after one corrected rollback of the premature all-clear. Initial sync/scoped checks exposed three installed-host gaps under serial full regression: two paraphrased source-exact capability actions, seed-preserved host `tests/test-strategy.xml` without `never after every micro-edit`, and a framework self-test that unconditionally read absent source-only `packages/lazy-harness-pi` paths. Upstream `bb149aa` now checks Pi package surfaces only when that source package root exists, while always checking distributed host surfaces. The fix was pushed and synced sequentially to Medivance, Medivance PWA, and Medivance Homepage; each marker is `bb149aa08ad4`, each exact capability/test-strategy convergence passed scoped `lazy check`, and each serial `LAZY_TEST_JOBS=1 lazy test` passed `scope=host, ran=59, skipped=29`. Product files and branches remained untouched.
- Protection: bounded validation regression checks capability/policy triggers and actions, AGENTS, Pi prompt, lazy-test skill, test strategy, SDD/TDD wording, and generated policy explanation.

### Fix 2d — implemented/validated 2026-08-19: work-unit grounding and token-output compaction

- User diagnosis: the dominant token cost is not one static prompt alone but repeated `map → record/source/test read → model round-trip → test output → reread/revalidation`, multiplied across normal turns and subagents. The current session reproduced it: short follow-ups repeatedly triggered overview traversal, several record reads, and the full mid-turn catalog reminder.
- User-selected direction: **근본 수정** and full execution/rollout approval. Cache one overview plus directly read governing-record content hashes for the active Pi/OMP work unit; reuse unchanged evidence across normal messages; invalidate on new session, explicit steer, or changed/deleted governing record. Real new-scope judgement remains LLM-owned.
- Prompt boundary: first-grounding `message.received` body target <=300 tokens with no inventory/catalog replay. `on-context.sh` becomes a five-line pointer-only body triggered only after the first successful mutation, never after reads/searches. Explicit steer creates one fresh grounding packet instead of inheriting a reused packet or scheduling a second context reminder.
- Validation boundary: preserve one coherent mutation batch, one focused checkpoint when needed, and one final standard validation. Green output in conversation is status/count/time only; detailed output stays captured unless failure or explicit request.
- Protection: prompt budget thresholds 100–300/600/800, static/no-classifier hook fixture, Pi fake-runtime reuse + record-fingerprint invalidation + steer reset, mutation-only context retry, and compact-green guidance checks.
- Closure evidence: framework standard validation GREEN (`fast-static-check` + full self-test, 73.902s). Prompt budget GREEN at 184 estimated first-grounding tokens versus the measured 985-token catalog-expanded body (81.3% reduction); valid later normal Pi/OMP turns inject 0 system-prompt tokens. Upstream `01692a3` was pushed and synced sequentially to Medivance PWA, Medivance Homepage, and Medivance root; each explicit serial `LAZY_TEST_JOBS=1 lazy test --scope host` passed (`ran=59`, `skipped=29`). Product Git status remained unchanged, and Homepage's three named host-owned records were hash-preserved across sync.

### Fix 3 — draft-first batched capture (behavioral + tooling)

- During work, append facts cheaply to the DRAFT tier (`candidates.jsonl`/`graph-drafts.jsonl`) with no gate and no commit; main agent verifies + promotes to canonical and commits ONCE per logical unit at turn end. Compounds with Fix 1 (fewer commits × cheaper commits).
- Optional add-on: parallel read-only subagents for multi-target investigation; parallel cheap-model atomic single-line appends to the draft tier (safe per POSIX O_APPEND); single-writer only for in-place edits + canonical promotion (`candidate-parallel-atomic-append-capture`).

## Sequencing

Fix 1 (commit cost) → Fix 1b (bounded full validation) → Fix 2b (single re-grounding) → Fix 2c (no micro-edit validation) → Fix 2d (work-unit evidence reuse/token compaction) are applied. Remaining Fix 2 and Fix 3 stay separately approval-gated.

## 2026-07-05 applied — host pre-push #1 bottleneck fixed (measured on medivance)

A host session profiled pre-PUSH (not pre-commit) on medivance: `.lazy-harness/bin/lazy test` = **441s**, of which **`check_lazy_sync_prunes_stale_managed_files` = 309.7s (72%)**. Root cause: that check runs `bun lazy-sync.ts --from <ROOT> --target <temp> --force` = a FULL managed-tree sync/prune, cost linear in host size (371 records). Other slow BOTH checks: doctor C17 negative 39s, lifecycle intake 20s, doctor D07 package-health 18.7s, retrieval benchmark 13.3s, response.completed telemetry 13.2s.

APPLIED (user-approved option gate): tag `check_lazy_sync_prunes_stale_managed_files` BOTH → FRAMEWORK_ONLY (self-test.py) + ADR 0026 amendment (Record completion rule). It re-verifies framework lazy-sync code; hosts get that verification on the framework source, so re-running it per host push is redundant + O(host-size). Verified: `--scope host` skips it (ran 58→57), `--scope framework` still runs it (ran 84). Effect: host pre-push 441s → ~130s once hosts `lazy update`. NOT changed: the other slow BOTH checks (doctor/lifecycle/benchmark/telemetry) — left for per-check evaluation (user chose #1-only scope).

## 2026-07-13 approved rollout — primary canonical record guard

Status: guard + two sample cleanups validated; scoped source commit/push and all-known-dogfood-host sync in progress; 7-day dogfood measurement runs through 2026-07-20.

A read-only Medivance seven-day audit found 106 recently modified record/knowledge files; 100 recent Markdown records contained 6,172/16,974 lines (36.4%) in digest/map/placement/capture/completeness structure. Representative problems were one reservation time-step invariant repeated across SDD/BDD/SSOT, detailed validation/review history accumulating in canonical planning, and a sheet-option SSOT whose digest conflicted with its later sections. These are mtime/current-size proxies because the downstream `.lazy-harness/` tree is ignored; they are not per-commit record diffs.

Approved guard:

1. one logical work unit chooses one primary canonical narrative record by default;
2. another layer is promoted only for an independent semantic delta, not mere relatedness;
3. `no independent delta` is a complete layer-completeness outcome;
4. MultiCandidate packets remain lossless review input but never authorize multi-record promotion;
5. durable repeated validation/progress detail uses at most one evidence capsule, otherwise no-record/transient;
6. semantic-delta judgement stays LLM-owned — no shell hook or raw-text classifier may guess it.

Rollout: amend ADR 0033 + record-write/layer-completeness/broker/evidence contracts and fixtures in the framework source; sync sequentially to Medivance; inspect code before resolving the sheet-option record conflict; consolidate only that sample and the reservation time-step sample; then measure seven days before considering draft-first tooling.

Success targets: median primary canonical records per logical work unit ≤ 1; every additional layer has an explicit independent-delta reason; no repeated validation transcript in canonical records; no contradiction in records touched by the sample cleanup.

Out of scope: bulk Medivance corpus rewrite, conflict-journal dedupe implementation, graph legacy migration, push/release, UI runtime, or database work.

### Applied evidence and dogfood baseline

- Framework guard, policy, helper, broker, co-change records, and fixtures passed the 84-check framework suite and final independent review.
- The user selected conflict-free downstream sync after simulation showed a normal seed sync would append 59 already-known conflicts; Medivance received the two new graph ids with conflict/candidate counts unchanged.
- Sheet option cleanup made the code/test/ADR-backed 2026-07-08 rule canonical; reservation time-step now has one active SSOT narrative plus deprecated SDD/BDD pointers.
- A host test exposed nested-sync overreach into arbitrary host-local policy sources; the framework fixture now preserves those policies but portability-audits only framework seed + fixture policies.
- Final Medivance evidence: focused Vitest 2 files/7 tests pass; host self-test `ran=57, skipped=27`; record lint 0; policy audit pass.
- Detailed commands/results: `.lazy-harness/evidence/2026-07-13-primary-canonical-record-rollout.md`.
- Measurement window: 2026-07-13 through 2026-07-20. Re-audit the four success targets above after the window; do not claim the behavioral targets before then.

### 2026-07-13 deployment completion correction

The user clarified that this framework rollout is not complete while it exists only as a dirty source tree or a single-host dogfood copy. Completion for this slice requires:

1. stage only the primary-canonical-record rollout, excluding unrelated shared-worktree changes;
2. commit and push the canonical `/home/lazydino/dev/lazy-harness` source;
3. sync and validate all known dogfood hosts: Medivance, Medivance PWA, and Medivance Homepage;
4. defer any busy host until its active writer releases `.lazy-harness`, then reconcile before sync.

This deployment completion does not wait for the 7-day effectiveness verdict; the post-change dogfood measurement remains a separate pending follow-up.

## Discovery capture

- ADR: ADR 0033 and ADR 0046 updated for the approved primary-record/typed-policy guard; process-pool and remaining gate-scope changes stay candidate.
- SDD: record-write, layer-completeness, evidence-capsule, record-decision-broker, and policy-machinery contracts updated for the approved slice.
- TDD: existing self-test and broker TDD protect four-layer matrix, synced-host policy audit, exact MultiCandidate preservation, and advisory promotion guidance.
- SSOT: `primary-canonical-record` added to canonical `.lazy-harness/ssot/policies.json` at recommend level.
- Planning: this record tracks applied guard/sample cleanup, the active 7-day measurement window, and still-proposed slices separately.
- DDD/BDD: no independent delta.

## Rule placement

- Rule: reduce workflow churn without weakening record recall — use scoped validation plus one primary canonical narrative record by default; independently changed layers remain explicit.
- Scope: framework-global.
- Primary record: this mixed-status plan; ADR 0033 owns the primary-record decision and ADR 0046 owns typed policy storage.
- Confirmation: Fix 1 and the Medivance host test-scope correction were previously approved/applied; the primary-record guard → sample cleanup → 7-day dogfood rollout was user-approved on 2026-07-13. Fix 1b, capture-gate suppression, and draft-first tooling still require separate approval.

## Discovery capture — Fix 2b

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: updated in `.lazy-harness/spec/platform/pi-agent-package.md` for once-per-turn cadence and resolver reuse.
- BDD: none because no independent product flow changed.
- TDD: updated in `.lazy-harness/tests/pi-agent-package.md` plus the Pi fake-runtime fixture.
- ADR: updated in `.lazy-harness/decisions/0048-operating-rule-storage-apply-repair.md` because R3 was narrowed from repeated file-op surfacing to one bounded turn reminder.
- SSOT: none because registry ownership, schema, levels, and storage remain unchanged.
- Planning: updated here as the user-selected primary canonical work-unit record.

## Discovery capture — Fix 2c

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: updated in bounded/fast validation contracts and the canonical test strategy.
- BDD: none because no independent product-visible flow changed; this is framework agent-operation behavior.
- TDD: updated in the bounded validation regression contract and self-test.
- ADR: no new architectural decision; ADR 0016's bounded validation direction is clarified rather than replaced.
- SSOT: updated in framework capability/policy registries by removing `iterating_after_edit` and changing the canonical guidance.
- Planning: updated here as the primary work-unit narrative; source fix `bb149aa` and all three source-exact host deployments are complete with serial full host regression evidence.

## Discovery capture — Fix 2d

- DDD: no independent domain vocabulary or business invariant delta.
- SDD: work-unit grounding updates pre-response, search/read-debt, Pi package, prompt-budget, and bounded-validation contracts.
- BDD: LLM-owned retrieval now reuses unchanged governing evidence across normal follow-ups; steer and record drift invalidate it.
- TDD: pre-response, pre-action, Pi package, prompt-budget, code-organization, bounded-validation, and self-test fixtures protect the new runtime boundary.
- ADR: ADR 0041 and ADR 0048 are amended because per-turn organic recall/catalog replay is replaced by work-unit-scoped grounding.
- SSOT: no capability kind/level or canonical registry ownership change; explicit resolver surfaces remain intact.
- Planning: this record is the primary canonical narrative for the user-approved implementation and rollout.
- Rule placement: framework-global agent operating/runtime rule; canonical decisions in ADR 0041/0048, executable contracts in SDD/TDD, no duplicate policy-registry entry.
