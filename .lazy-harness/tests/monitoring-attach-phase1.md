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

## Fabric compaction coexistence regression (2026-11-14, approved)

Primary contract: `.lazy-harness/spec/platform/monitoring-thin-consumer.md#fabric-compaction-coexistence`.
Module tests protect long kept tails, UTF-8/JSON/hash-inclusive byte ceilings, deterministic
section prefixes and omission counts, tailMessages 0 compatibility, and a 10000-byte catalog
that still reaches the fake judge within 16384 bytes. Summary is context, not own/region material.
Host attachment test protects attached=true across pre/terminal fences, paused/rebuilding/ready
transitions, old result discard, resumed window and unchanged lifetime reservation. Report test
protects recursive readiness allowlisting and rejection of arbitrary body fields.

The private faux Pi 1.5.0 + pi-fabric 0.135.2 harness is reused with keepRecentTokens 20000 in
Fabric-only and monitoring-before/after runs. Assert identical summary/firstKeptEntryId/tokensBefore,
manual result and Fabric hook result, bounded separate snapshot summary, next fake judgement
containing `[summary]`, no material_limit, fence handler undefined returns, stale held completion,
and readiness at each boundary. Network namespace + runtime/fetch/net/tls sentinels fail closed;
zero real model calls. Metadata-only results/reproduction pointers are in
`.lazy-harness/evidence/monitoring-core/compaction-summary-coverage.md`; raw frames stay private.

| Layer | Independent delta / primary location |
| --- | --- |
| SDD | Summary coverage/budgets and status readiness in the existing thin-consumer SDD. |
| BDD | No independent delta beyond status semantics in primary SDD; observe remains non-delivering. |
| SSOT | No independent delta; ownership/default activation/token retention unchanged. Explicit observer share is SDD contract. |
| DDD | No independent delta; existing compaction/monitoring vocabulary retained. |

Implementation map: host `monitoring/index.ts` (`composeObserve`, `OBSERVER_LIMITS`), vendor
`observer.ts` (`readObservationSnapshot`), `compaction-summary.ts` (`boundedSummary`) and
`monitoring-core-realtime-material.ts` (`regionLines`, `RealtimeMaterialWindow.capture`);
protected by attachment/report tests plus vendor summary-coverage/summary-material tests.
Validation: monitoring attach/capture, Reader SDK, Pi typecheck, full lazy test with inherited
PI_FABRIC_LINEAGE unset, record-lint, changed-file check, diff/privacy scan. No new dependencies.

## Enable/disable/config controls (2026-11-14, approved A)

`packages/lazy-harness-pi/tests/monitoring-manage.test.ts` uses temporary project roots and fake
settings; no real classifier/provider is called. It protects defaults accepted by the real parser
and catalog (including copies of the actual default records), missing-default messages, custom ids/
budgets/read format, no-default-docs, per-doc/total/count/path/UTF-8/symlink refusal, unsafe config
refusal, overwrite diff/force, dry-run no mutation, disable config-only removal and idempotence,
config off/valid/invalid output, strict options, both read-format detection branches, CLI dispatcher
and synced-host source lookup, and Pi delegation via the shared helper with a throwing reload/model
context. Off still has no monitoring hooks/vendor loads; it now has a control/status command.

Offline fixture isolation: `monitoring-manage.test.ts` gives the config-off/valid/invalid case an empty, temporary `XDG_CONFIG_HOME` and restores it after use. `monitoring-attach-phase1.test.ts` gives the private metadata sink a canonical temporary state directory so macOS's `/var` alias does not trigger the deliberate symlink-ancestor refusal. Neither fixture reads a personal monitoring config or changes production logging/admission.

| Layer | Fixture repair impact |
| --- | --- |
| SDD | No independent delta; config precedence and log-path refusal unchanged. |
| BDD | No independent delta; user-visible behavior unchanged. |
| SSOT | No independent delta; no config defaults or ownership changed. |
| DDD | No independent delta. |

Implementation map: `manageMonitoring`, `detectReadFormat`, `handleMonitoringControl` in
`packages/lazy-harness-pi/extensions/lazy-harness/monitoring/manage.ts`, CLI `monitoring` in
`.lazy-harness/scripts/monitoring.ts`, registered via `.lazy-harness/bin/lazy`, Pi `load.ts` and
`index.ts`. `package.json` includes the new test in `test:monitoring-attach`; capture and full regression
already invoke that target. Existing install tests now expect the off control command, not hooks.

| Layer | Independent delta / primary location |
| --- | --- |
| SDD | Enable/disable/config API and visible control flow are specified in `.lazy-harness/spec/platform/monitoring-thin-consumer.md`. |
| BDD | No separate semantic delta beyond the command contract in the primary SDD; no monitoring delivery/judgement change. |
| SSOT | No ownership or parser-default change; explicit opt-in presets are in the primary SDD. |
| DDD | No independent delta; existing monitoring terms unchanged. |

Acceptance is offline: monitoring/capture suites, real Reader SDK test, Pi typecheck, full `lazy test`
with inherited `PI_FABRIC_LINEAGE` unset for child runs, record-lint, changed-file check, diff/privacy
scan; no deps/lockfile changes and no shared-checkout commands. No live smoke is authorized.

## Global allowlist and automatic catalog (2026-11-14, approved A)

Primary contract: `.lazy-harness/spec/platform/monitoring-thin-consumer.md#global-resolution-and-automatic-catalog-2026-11-14-user-approved-a`.
`packages/lazy-harness-pi/tests/monitoring-global.test.ts` uses temp HOME/XDG_CONFIG_HOME and project
roots. It protects strict schema/nested keys/types/stages/budgets, project > global > off precedence,
realpath allowlisting including alias cwd/entries, paired all consent flags, digest/size/path catalog
ordering, 16-doc/8-KiB/12-KiB ceilings, file/directory symlink refusal, invalid UTF-8/empty catalogs,
empty/invalid zero classifier lookup/calls/imports, private permissions, defaults-only/add/remove,
dry-run/force/no-project-writes, Pi current-root controls/reload reminders, and source status.
The real dispatcher is exercised offline; fake Pi registries fail if looked up on the off path.

| Layer | Independent delta / primary location |
| --- | --- |
| SDD | Global authority resolution, config/control API and automatic admission in existing thin-consumer SDD. |
| BDD | No separate delta beyond visible CLI/Pi controls specified in primary SDD; observe remains non-delivering. |
| SSOT | New global config schema/permissions owned by the primary component contract; no separate record or ownership change. |
| DDD | No independent delta; existing monitoring/project/catalog vocabulary retained. |

Implementation map: `global.ts` (`parseGlobalConfig`, `resolveMonitoring`, `automaticCatalog`),
`global-manage.ts` (`manageGlobalMonitoring`), `manage.ts` (`handleMonitoringControl`), `load.ts` and
`index.ts` (`installOptionalMonitoring`, `installMonitoringPhase1`). Existing monitoring/capture/full
regression chain includes this suite. Required validation: monitoring attach, Pi capture, Reader SDK,
Pi typecheck, full lazy test with inherited PI_FABRIC_LINEAGE unset, changed-file check and privacy/diff
scan. Full suite comparison uses a separate clean worktree at origin/main 2a3a9b8; known single
`check_record_lint_cli` failure references missing host-validation draft, not modified in this batch.

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

## Offline report collector and status snapshot (2026-11-14 A1)

`packages/lazy-harness-pi/tests/monitoring-report.test.ts` protects nested v1/schema allowlisting,
config and status projection, home redaction, credential-pattern refusal, Git/linked-worktree and
symlink output refusal, private atomic output permissions, plain status compatibility, explicit
status save (0600 file / 0700 directory) and unavailable bootstrap save without vendor/model calls.
Synthetic collector tests cover UTC today/yesterday tail limits, snapshot age, missing Pi version,
summary nearest-rank percentiles and missing reported costs, strict CLI options, and issue dry-run
argv generation without any gh execution. All fixtures/state/sample artifacts are external temporary
files; no real report/experiment results enter Git. Registered in test:monitoring-attach, transitively
Pi capture and full regression. Child test runs unset inherited PI_FABRIC_LINEAGE explicitly.

| Layer | Decision | Reason |
| --- | --- | --- |
| SDD | updated | Existing monitoring-thin-consumer.md owns collector, snapshot, privacy and Implementation map. |
| BDD | no independent delta | Manual diagnostic handoff documented in README/template and component SDD; no task/delivery behavior changes. |
| SSOT | no independent delta | Existing monitoring ownership and private state/config semantics retained. |
| DDD | no independent delta | Existing observe outcomes, stage and budget vocabulary reused. |

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

## Regression: material_limit blocked every live input (2026-11-13)

- Symptom: observe log lines `outcome: skipped`, `errorClass: selection_material_unavailable`, `modelCalls: 0` for each live input after the long-session fix.
- Cause: host material options combined `historyTurns: 4` with `historyMode: 'since-last'`; the extra history blob (up to 8,192 bytes, unbudgeted) plus the 9,832-byte catalog exceeded the 16,384-byte window (`material_limit`).
- Protection: 'realistic catalog + long messages still judge' in `monitoring-attach-phase1.test.ts` (two catalog files ~9.8 KiB, 300 messages of ~1.5 KiB); verified to FAIL with `historyTurns: 4` restored and pass with the fix.
- Layer matrix: SDD updated (monitoring-thin-consumer.md material budget section); BDD no independent delta; SSOT no independent delta; DDD no independent delta.

## Regression: classifier failure reason was swallowed (2026-11-13)

- Symptom: live observe line `outcome: failed`, `errorClass: classifier_uncertain`, `modelCalls: 1`, no reported usage; no reason anywhere.
- Protection: 'classifier failure records a bounded failure class (no provider text)' — fake classifier returns `stopReason: error` with a 401 message; status shows `lastFailure: stop_error_auth_401`, no provider text, classifier stopped.
- Layer matrix: SDD updated (monitoring-thin-consumer.md classifier failure detail); BDD no independent delta; SSOT no independent delta; DDD no independent delta.

## Regression: 1 s selection job deadline aborted live judgements (2026-11-13)

- Symptom: live observe `failed`, `errorClass: classifier_uncertain:aborted`, latency ~1,072 ms; classifier stopped; next input `refused` / `no_admitted_decision`.
- Cause: realtime selection default `jobTimeoutMs` 1,000 ms < real Jev latency on the U1 view.
- Protection: 'a judgement slower than one second is not aborted by the selection job deadline' (fake classifier delays 1,500 ms); fails with the default deadline (`lastFailure: aborted`), passes with the fix.
- Layer matrix: SDD updated (monitoring-thin-consumer.md selection job deadline); BDD no independent delta; SSOT no independent delta; DDD no independent delta.

## Regression: window event budget stopped long-session judging (2026-11-13)

- Symptom: live status `window.state: stopped`, `lastReason: event_budget`, `framesSeen` 3,769, no further observe lines.
- Cause: module window/coordinator `maxEvents` 2,048 counts every frame (streaming deltas included) and stops permanently.
- Protection: 'event budget: a long-running session keeps judging after more than 2048 frames' (2,100 message_update frames then an input); fails with renewal disabled (0 calls), passes with renewal (`window.renewals` 1).
- Layer matrix: SDD updated (monitoring-thin-consumer.md window renewal); BDD no independent delta; SSOT no independent delta; DDD no independent delta.

## Regression: mid-run message left no observe line (2026-11-14)

- Symptom: live status showed 3 judged skips; a message sent while the agent was answering had no observe line and no reason.
- Cause: queued inputs advance the coordinator intent; untraced notes (`material_or_permission_not_visible`, `deferred`, `intent_changed`) never reached the log.
- Protection: 'queued follow-up/steer inputs are logged as skipped with a reason' (normal prompt, then followUp and steer during a run): one final per frame, follow-up logged `queued_input_followUp:<reason>`; fails with the sweep disabled. The trace-projection test now uses a separate frame for the selection failure (one final per frame).
- Layer matrix: SDD updated (monitoring-thin-consumer.md skip reasons and queued inputs); BDD no independent delta; SSOT no independent delta; DDD no independent delta.

## Regression: fresh clone could not load Pi extension (2026-11-14)

- Cause: unconditional monitoring imports resolved the empty submodule before the off check;
  installers also omitted recursive submodule initialization and its frozen dependencies.
- Protection: `packages/lazy-harness-pi/tests/monitoring-install.test.ts` imports a temporary full
  extension copy with vendor absent, empty or a missing transitive import, at absent/off/observe
  stages. Non-monitoring hooks still register; explicit observe stays off with exactly one warning
  and status/install hint. An injected loader proves off never imports and initiating session_start
  is replayed once, with later input/session events forwarded. Helper and global/local wrapper
  dry-runs stay offline and do not create a missing source.
- Layer completeness matrix for this regression:

| Layer | Decision | Reason |
|---|---|---|
| SDD | updated | Primary monitoring-thin-consumer.md install and vendor-unavailable component/status contract. |
| BDD | no independent delta | Setup checklist documents this same component contract; no active delivery/user-task flow introduced. |
| SSOT | no independent delta | Config ownership/defaults, credentials and lockfiles remain unchanged. |
| DDD | no independent delta | Existing stage/read/receipt semantics reused. |

## Implementation map

- Status: implemented
- Primary files: `packages/lazy-harness-pi/tests/monitoring-attach-phase1.test.ts`.
- Tests / protection: `package.json` target `test:monitoring-attach`, included by `test:pi-capture` and hence the existing full regression adapter check.
- Contract: `.lazy-harness/spec/platform/monitoring-thin-consumer.md`.
- Machine graph ids: `kg_monitoring_attach_phase1_tests`, `kg_monitoring_observe_telemetry_tests`.
- Related source: `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/observation.ts` (`createObservation`), `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/observe-log.ts` (`createObserveLog`), `index.ts` (`composeObserve`, `installMonitoringPhase1`), `model.ts` (`createPiModelBinding`).
