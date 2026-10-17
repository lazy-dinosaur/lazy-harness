# Harness fixture runtime scratch isolation regression

## Rule digest
- Status: active
- Layer: TDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - harness fixture runtime isolation
  - copy_harness_fixture
  - fixture scratch exclusion
- Applies when: self-test copies a host `.lazy-harness` tree into a disposable fixture or lifecycle setup allocates temporary hosts.
- Must: omit only top-level runtime `tmp`; preserve nested canonical fixture directories named `tmp`; keep broken canonical links fail-closed; own allocations from creation through setup and hand off only after successful return; clean completed allocations on setup failure/cancellation while preserving the original exception.
- Must not: remove source files, skip lifecycle assertions, or copy temporary PR review snapshots as canonical input.

## Confirmed failure and preserved repair

Existing Medivance validation hit ENOENT on dangling skill links and ENOSPC while lifecycle tests recursively copied `.lazy-harness/tmp/pr-review`. The user had approved a narrow fixture-copy repair. The later full harness rollout exposed that its reviewed source lacked this deployed local overlay; transport/source greens did not prove overlay preservation. The affected deployment was rolled back before this integration.

The current user explicitly selected preservation of that existing protection in a separate integration candidate, then validation and full installed-host rollout. Use the pre-apply archive as the exact code baseline; do not copy the paused architecture fixture's independent `Path(tmp).resolve()` proposal, relax lifecycle assertions or alter Reader metadata.


The user also selected **남은 보호까지 완료** after all seven C382 installs were applied and Mobile exposed a second copy path: `lifecycle-parity-runner.py#copy_host` copied top-level runtime scratch inside the lifecycle fixture itself. The installed Mobile probe timed out at 120s; a stage/stack diagnostic passed fixture isolation and intake but still timed out at 240s during the response integration. These are incomplete verification receipts, not source assertion passes. Apply the identical root-only exclusion in the private parity copier, retain its original ignore patterns, clean up only its newly owned failed-copy directory, and extend the same BOTH regression with the same positive/nested/negative fixtures. Do not omit or weaken either original integration.
`copy_harness_fixture` preserves each caller's original ignore tuple and excludes only root runtime scratch. Both lifecycle test bodies and their BOTH registrations remain active. The new BOTH regression proves root runtime dangling links are excluded, nested canonical `fixtures/tmp` survives, and a broken canonical link still raises a failure.

## Layer completeness

- SDD: no independent delta; only private fixture preparation is protected, with no public API/IPC/component change.
- BDD: no independent delta; production/user flows and all existing lifecycle assertions are unchanged.
- SSOT: no independent ownership/config/schema delta; distributing this framework TDD through Category A preserves the existing protection, not authority over host knowledge.
- DDD: no independent domain or business-rule delta; runtime scratch is not canonical fixture input.

## Implementation map

- `.lazy-harness/scripts/self-test.py#copy_harness_fixture`: root-only `tmp` exclusion while retaining existing caller ignore patterns and canonical-link failure.
- `.lazy-harness/scripts/self-test.py#check_harness_fixture_runtime_isolation`: positive runtime-scratch and nested-canonical checks plus negative broken-canonical-link protection; registered BOTH.
- `.lazy-harness/scripts/lifecycle-parity-runner.py#copy_host`: applies the same top-level runtime-only exclusion to the nested parity copy; preserves canonical nested tmp and fail-closed links; cleans up its own failed-copy output.
- `.lazy-harness/scripts/self-test.py#check_lifecycle_fixture_intake_cli`: original `.cache/logs/state/node_modules` ignore tuple and assertions preserved.
- `.lazy-harness/scripts/self-test.py#check_response_completed_no_auto_route_telemetry`: original `.cache/state` ignore tuple and assertions preserved; BOTH unchanged.
- `.lazy-harness/manifests/init-categories.json`: explicit Category A distribution of this regression asset.
- `.lazy-harness/knowledge/graph.jsonl`: verified implementation and protection links.
- Related scope authority: `.lazy-harness/decisions/0026-doctor-self-test-scope-separation.md`.

## Validation boundary

Earlier installed integration and authenticated Reader acceptance remain separate deployment evidence. This allocation correction is being prepared from published86 in the exact user-confirmed shared-object worktree; only the cleanup source/test/TDD/graph delta is included. The original dirty/index, active installed source and retained large data are preserved. Candidate validation/publication/installed receipts are pending until their actual results are consumed.

## Allocation ownership correction

### Purpose and confirmed boundary
The user approved fixing leaked lifecycle setup directories, then explicitly chose **코드 반영 후 정리** and confirmed `/Users/lazydino/.pi/agent/local-packages/lazy-harness-cleanup-source`, branch `fix/lifecycle-temp-cleanup`, based on remote86. Git objects are shared, not cloned with application/dependency trees. Existing large tmp/benchmark/pilot/rollback areas are not deleted; owner/retention classification and exact itemized deletion approval remain separate.

### Changed behavior and implementation map
- `.lazy-harness/scripts/lifecycle-check.py#sandbox_root` owns its new directory throughout copy, initialization and context preparation. Setup exception/cancellation removes it and re-raises the original error; success transfers ownership to `main`'s existing `finally`.
- `.lazy-harness/scripts/lifecycle-parity-runner.py#copy_host` retains the published root-only runtime-scratch ignore rule and canonical-link failure behavior, while owning copy/initialization failures until successful return.
- `.lazy-harness/scripts/lifecycle-parity-runner.py#run_fixture` enters cleanup scope before either allocation and releases only completed hosts, so second-allocation failure also cleans the first host. Original parity comparison, assertions and result shape remain unchanged.
- `tests/lazy-harness/lifecycle-temp-cleanup.test.ts` uses the existing Bun `*.test.ts` / `test:run` discovery convention, compiling the actual Python function AST with controlled I/O rather than replacing the algorithm or claiming full CLI acceptance. Ten setup/cancel/normal cases plus bounded-fixture and source-preservation tests check exception identity, zero retained allocations, root runtime/nested canonical tmp semantics and unchanged source bytes. It copies no application/dependency tree and cleans its own empty fixture.
- `.lazy-harness/knowledge/graph.jsonl` appends three verified ownership/protection edges without rewriting prior or legacy rows. No generated-cache bulk migration is included.

### Layer completeness for this correction
| Layer | Judgment |
|---|---|
| SDD | no independent delta; only private allocation ownership changes, with no public API/IPC or result-contract change |
| BDD | no independent delta; user flows and lifecycle/parity assertions remain intact |
| SSOT | no independent delta; no ownership/config/schema rule changes, and distributing the existing TDD does not grant host knowledge authority |
| DDD | no independent delta; no domain/business-rule changes |

### Validation and publication capsule
The older original working-tree repair passed focused12/0 in160ms and standard91/0 in365.309s; that historical result is not substituted for this86-based source. The exact publication candidate's focused target actually passed12/0 (56 expectations,163ms), and its deliberate checkpoint checked5 files with errors0/warnings0. Final standard, normal commit/push and installed receipts must be consumed from their actual terminal/runtime results before claiming those boundaries complete; source green never certifies installed hosts or authenticated Reader acceptance. Keep later progress/evidence in the existing primary performance plan and runtime capture rather than mutate unchanged validated source just to record a status. No new paid Reader/Parent, unrelated global package change, force push or forced session reload is included.
