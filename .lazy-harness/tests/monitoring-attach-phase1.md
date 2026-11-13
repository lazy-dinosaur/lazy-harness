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

## Layer completeness matrix

| Layer | Decision | Reason |
|---|---|---|
| SDD | updated | Primary phase-1 composition/port/config contract in monitoring-thin-consumer.md. |
| BDD | no independent delta | No stage activated or visible delivery; observe remains notification/selection only. |
| SSOT | no independent delta | Config ownership/defaults are part of the new component contract; no global env/schema ownership change. |
| DDD | no independent delta | Existing monitoring read/receipt/stage semantics reused. |

## Implementation map

- Status: implemented
- Primary files: `packages/lazy-harness-pi/tests/monitoring-attach-phase1.test.ts`.
- Tests / protection: `package.json` target `test:monitoring-attach`, included by `test:pi-capture` and hence the existing full regression adapter check.
- Contract: `.lazy-harness/spec/platform/monitoring-thin-consumer.md`.
- Machine graph id: `kg_monitoring_attach_phase1_tests`.
