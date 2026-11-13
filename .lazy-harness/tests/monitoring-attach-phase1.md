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
containment/symlink/current-byte revocation. Synthetic sources and injected classifier only.
Manifest state/rule suites do not apply: persistence and rules/memory are not instantiated.
Fake conformance is not a claim of provider quality, real-host qualification or hard termination.

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
