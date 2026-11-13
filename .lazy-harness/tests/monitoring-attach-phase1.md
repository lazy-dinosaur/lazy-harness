# TDD — Monitoring phase-1 attachment

## Rule digest

- Status: active
- Layer: TDD
- Scope: host-project
- Aliases:
  - monitoring phase1 conformance
  - default off monitoring regression
- Applies when:
  - changing the phase-1 monitoring composition, ports or pinned module
- Must:
  - run offline fake-classifier tests with no real model/provider calls
  - verify malformed manifests and unsupported majors refuse before composition
  - verify off installs nothing and observe executes no jobs/reports/injection
  - run module read-record and in-memory worker conformance against selected implementations
  - protect private metadata allowlist/permissions/retention/cap/XDG/off behavior and nonfatal log failures
  - verify status uses no model, stale results are discarded, completed fences resume and lifetime budgets do not reset
- Related records:
  - `.lazy-harness/spec/platform/monitoring-thin-consumer.md`
  - `.lazy-harness/tests/test-strategy.xml`

## Protection and scope

`bun run test:monitoring-attach` exercises manifest validation/major refusal, stage and unavailable
module rejection, the host ledger's five grouped input-port probes, chosen worker's 24 conformance
checks, exact Jev-only identity, native choice/bool mapping, stored-credential options/zero retries,
zero/lifetime budget gates, pre-cancel/uncertainty, observe frame selection/fencing and catalog
containment/symlink/current-byte revocation. Additional regressions exercise installed observe
startup through ctx.modelRegistry (method receiver preserved), missing/old registries and unavailable
or wrong models failing closed, no runtime SDK/eval import, no package-local SDK pin, and zero
default-budget calls. Synthetic sources and injected classifier only.
Manifest state/rule suites do not apply: persistence and rules/memory are not instantiated.
Fake conformance is not a claim of provider quality, real-host qualification or hard termination.

## PR #38 SDK resolution correction (2026-11-13)

Parent's clean-main verification overrides the earlier incorrect pre-existing-failure report:
check_pi_package_layout_and_contract failed because the PR-local SDK 1.5.0 and root 0.85.1
loader were mixed in fabric-reader-policy-sdk.test.ts. Remove only the local pin; root remains
0.85.1. Protect with that real-SDK offline test and full lazy test, not only fake classifier tests.
The unrelated prompt narrowing and tsconfig changes are reverted. Retain the Node transform flag:
a strip-only capture probe fails on the module's diagnostics.ts constructor parameter properties;
the configured test:pi-capture target must remain green. No model calls are permitted.

## OBSERVE measurement regressions (2026-11-13)

Fake-only tests cover strict log field allowlist and sentinel body/conversation/credential exclusion,
selected document versions and reported usage/confidence, 0700/0600 modes, 2 MiB cap (small cap
fixture), age pruning, XDG default and off behavior, unsafe project path/nonfatal log errors and
file-symlink refusal. Status is exercised through real command registration and no classifier calls.
Compaction holds a fake raw call across a before fence: its late result produces no accepted run;
completion resumes new input, keeps prior reservations, exhausts the same lifetime budget and
shutdown closes admission. Failed compaction and tree completion are covered; fork replacement
keeps safe reload-only behavior. Native module trace projection additionally protects skip/defer,
refused and failure outcomes. Existing ledger/worker conformance and no-provider transport tests stay.

Acceptance commands: `bun run test:monitoring-attach`, `bun run test:pi-capture`, the offline
`packages/lazy-harness-pi/tests/fabric-reader-policy-sdk.test.ts`, `bun run typecheck:pi`, full
`.lazy-harness/bin/lazy test` with inherited `PI_FABRIC_LINEAGE` unset in its child environment,
`lazy record-lint`, explicit `lazy check --files ...`, final standard validation, and privacy/diff
scan. No network classifier, live activation, merge, module-source or lockfile mutation is authorized.

## Layer completeness matrix

| Layer | Decision | Reason |
|---|---|---|
| SDD | updated | Primary phase-1 composition/port/config contract in monitoring-thin-consumer.md. |
| BDD | no independent delta | Diagnostic status command and fence lifecycle are component contracts captured in SDD; no parent delivery or user task flow changes. |
| SSOT | no independent delta | Config ownership/defaults are part of the new component contract; no global env/schema ownership change. |
| DDD | no independent delta | Existing monitoring read/receipt/stage semantics reused. |

## Regression: long session stopped at session_start (2026-11-13)

- Symptom: live `/monitoring status` showed `attached: false`, `reason: scope_or_catalog_unavailable`, `framesSeen: 1`, `judgements: 0` on a 7,261-message session; no observe log was created.
- Cause: observer default `maxMessages` 128 / `tailMessages` 0 marked the snapshot unavailable; the attach treated that as a scope/catalog failure.
- Protection: `monitoring-attach-phase1.test.ts` 'long real sessions stay observable through tail snapshots' (600-message fake session, session_start + input judges, attached stays true); reason split `frame_unavailable`.
- Layer matrix: SDD updated (monitoring-thin-consumer.md long-session section); BDD no independent delta; SSOT no independent delta; DDD no independent delta.

## Implementation map

- Status: implemented
- Primary files: `packages/lazy-harness-pi/tests/monitoring-attach-phase1.test.ts`.
- Tests / protection: `package.json` target `test:monitoring-attach`, included by `test:pi-capture` and hence the existing full regression adapter check.
- Contract: `.lazy-harness/spec/platform/monitoring-thin-consumer.md`.
- Machine graph ids: `kg_monitoring_attach_phase1_tests`, `kg_monitoring_observe_telemetry_tests`.
- Related source: `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/observation.ts` (`createObservation`), `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/observe-log.ts` (`createObserveLog`), `index.ts` (`composeObserve`, `installMonitoringPhase1`), `model.ts` (`createPiModelBinding`).
