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
- Applies when: self-test copies a host `.lazy-harness` tree into a disposable fixture.
- Must: omit only top-level runtime `tmp`; preserve nested canonical fixture directories named `tmp`; keep broken canonical links fail-closed.
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

Integration checks and installed-host results are pending until actual receipts are consumed. A successful source test does not certify all host overlays or authenticated Reader acceptance. Keep host records, app/Git work and other paused source lanes untouched; no remote publication or extra paid runtime is implied by this record.
