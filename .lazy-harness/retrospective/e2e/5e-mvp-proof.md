# 5e MVP Proof

Date: 2026-05-12
Branch: `experimental/lazy-harness`
Status: framework MVP proof complete, real host-project pilot pending

## Claim

Lazy-harness now has a framework-owned MVP path that can detect cross-layer work, ask structured questions, ingest human decisions, run TDD verification, perform aftershock re-analysis, integrate lifecycle hooks, and prove the flow through a feature-like walkthrough.

## Evidence

| Layer | Evidence |
|---|---|
| Trigger detection | `code-change.ts` orchestration + `detectors/{ddd,sdd,bdd,ssot}.ts` |
| Question queue | `interview-loop.ts --mode collect`, `.lazy-harness/questions/open.xml` |
| Answer ingestion | `interview-loop.ts --mode answer --apply`, `.lazy-harness/logs/decisions.jsonl` |
| TDD gate | `tdd-cross-verify.ts`, `check-tdd-cross-verify.sh` |
| Aftershock | `aftershock-reanalysis.ts`, depth cap + follow-up effects |
| Hook integration | `on-response-completed.sh` runs TDD, affected-test, and aftershock helpers |
| Walkthrough | `referral-priority-queue` reaches depth >= 2 in self-test |
| Validation | `lazy:test`, `lazy:doctor`, pre-push, and pushed `43622e8b` pass |

## 5e criteria status

| Criterion | Status | Notes |
|---|---|---|
| 5e-1 real host-project feature release | pending | Phase 5 close blocker. Must use actual feature branch artifact. |
| 5e-2 choose pattern | ready | Recommend `inside-out` for first real feature because code-trigger adapters and affected tests are strongest. |
| 5e-3 traceability links | partial | Fixture traceability exists: `traceability/referral-priority-queue.xml`. |
| 5e-4 conflict resolution assetized | pass | 5d-6 answer + aftershock decisions prove durable conflict handling. |
| 5e-5 metrics/insight recorded | pass-for-MVP | This proof, 5d retrospective, and post-MVP gap map record friction and limitation. |
| 5e-6 Phase 6 data | partial | Known data: hook injection semantics, fixture-scope pollution, affected-test command routing, aftershock heuristic limits. |

## Known limitations before declaring production-complete

1. 5d-6 is fixture-backed, not a shipped host-project feature.
2. TDD cross-verify v0 checks matching test existence, while `affected-test-runner.ts` now executes matching Vitest tests or opens a structured test-strategy gate.
3. Aftershock v0 maps effects to next layers heuristically, not via full artifact diff.
4. Hook output enters the LLM on a later lifecycle-injected turn, so user-facing orchestration must account for next-turn continuation.

## MVP conclusion

Framework MVP proof is complete and sufficient to proceed to a real host-project feature pilot. Phase 5 is not yet production-complete until 5e-1 through 5e-3 are completed on an actual feature branch. After that pilot, framework work must move to a standalone `lazy-harness` repository; see `.lazy-harness/plans/extract-to-lazy-harness-repo.md`.
