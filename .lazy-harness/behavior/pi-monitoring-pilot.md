# BDD — Manual local monitoring-pilot controls
> Pre-migration record: code/script/test/fixture paths below describe the layout of lazy-harness branch `work/monitoring-engine-v2` (221553d) before the monitoring implementation moved to `lazy-dinosaur/lazy-harness-monitoring`; evidence stays in lazy-harness (ADR 0062). Canonical monitoring records now live on lazy-harness main (see `.lazy-harness/ssot/monitoring-records-ownership.md`).

Status: implementation/readiness focused-verified; final standard tracked by primary SDD; real pilot not run
Layer: BDD

## Rule digest

- Status: advisory
- Layer: BDD
- Scope: host-project
- Confidence: medium
- Aliases:
  - 수동 관측 시험
  - lazy-monitor
  - manual monitoring pilot
- Applies when:
  - explaining or testing explicit load/start/status/stop/reset of the P5 local text-only pilot
- Must:
  - remain off until the user explicitly loads the separate extension and starts an idle interactive session run
  - collect only post-start user/assistant text and tool identity/status metadata, in bounded local RAM
  - distinguish readiness tests from an actual user-data pilot and normal Pi transcript/provider behavior
  - clear owned raw buffers and cancel work at stop, limits and scope transitions; expose outstanding diagnostic bytes if raw work ignores abort
- Must not:
  - start the pilot automatically, persist or export pilot text, inject model context or run semantic/business handlers
  - collect tool argument/result bodies, history/system-prompt bodies, thinking/signatures/images or provider raw/error payloads
- Record completion:
  - implementation and validation evidence updates `.lazy-harness/spec/platform/pi-monitoring-observation.md`; independent control-flow changes update this record
- Related records:
  - `.lazy-harness/spec/platform/pi-monitoring-observation.md`
  - `.lazy-harness/planning/monitoring-core-live-integration-plan.md`

## Confirmed scope

The user selected conversation text plus tool name/status, local RAM only, common bounds10minutes/500events/1MiB (first reached stops), and manual start after readiness. A separate execution choice approved implementation/synthetic validation only. No actual collection has started. This BDD exists for the independent human-visible command-flow delta; the existing SDD remains the primary implementation/evidence narrative.

## Scenarios

### Explicit load remains off

Given Pi1.3 and the source checkout, the user may later explicitly load the ready extension with `pi --extension .lazy-harness/scripts/monitoring-core-pilot.ts`. Loading registers `/lazy-monitor` but does not start collection or timers. Shared package entrypoint/settings are unchanged. This is not automatic activation in the current agent session.

### Manual start after readiness

When the user enters `/lazy-monitor start` in an idle interactive Pi UI, the extension starts a new bounded run for that native session/root. Busy/non-interactive start is rejected. Only future finalized user/assistant text and tool start/end metadata enter the buffer. No previous history, prompt checkpoint or raw tool data is copied. Native leaf-at-hook identity is not a final-provider-payload assertion.

### Status is metadata only

`/lazy-monitor status` displays state/reason, scope/run identity, limits, counts, retained bytes/frames, queue and physical diagnostic status through terminal notification. It does not display the buffered text or append a model-visible message/session entry.

### Stop/reset and limits

`/lazy-monitor stop` stops admission, aborts diagnostics and clears owned raw ring/queue. `/lazy-monitor reset` also clears the metadata counters/run identity.10minutes/500events/1MiB are upper bounds; per-frame/queue/deadline guards can be tighter and report omission/overflow. These caps measure serialized UTF8 data, not total RSS. No silent truncation or forced-memory-zeroization claim.

An uncooperative diagnostic can retain its single permitted frame until raw settlement. Status reports physical activity/outstanding bytes; restart is rejected until it settles. No late acknowledgement counts as received. The user's main operation is not awaited by diagnostics.

### Scope changes are off, not auto-resumed

Session change/shutdown, tree navigation and compaction stop and clear the run. Reload creates a new default-off instance. A new manual start is required afterward. No raw text restoration or background resumption occurs.

## Privacy boundary

RAM-only/no additional transmission applies to this monitoring component's extra copy/diagnostics. It neither disables nor changes Pi's normal provider calls or native session-transcript persistence. The SDK remains conversation authority. No semantic model, P3 material worker or P4 handler is run on real data by this pilot.

## Verification and limits

Mechanical command/UI gating and forbidden-getter/history API tests plus actual SDK synthetic event/readiness tests pass. An actual TypeScript file-loader test confirms registration and OFF state. No real interactive user-data pilot or UI visual inspection has been performed. Final validation status belongs to the primary SDD, not this BDD progress header.

## Implementation map

- `.lazy-harness/scripts/monitoring-core-pilot.ts`: `manualMonitoringPilot` default export and `createManualPilotExtension` register the explicit command and lifecycle callbacks; `ManualMonitoringPilot` owns start/record/stop/reset, field minimization, bounded buffer/queue/diagnostics and status.
- Flow: explicit source-file load -> OFF command registration -> manual idle/UI start -> pre-buffer field selection -> local frame/receipt -> metadata status/stop/reset. No shared runtime config mutation.
- `tests/lazy-harness/monitoring-core-pilot.test.ts`: command/data/lifecycle and independent allowed-frame/receiver assertions.
- `packages/lazy-harness-pi/tests/support/monitoring-sdk-fixture.ts`: optional explicit extensionPaths -> actual SDK additionalExtensionPaths; default fixture behavior is unchanged.
- `.lazy-harness/evidence/monitoring-core/pi-observer-p5-readiness-report.json` and `.lazy-harness/evidence/monitoring-core/pi-observer-p5-loader-report.json`: separate synthetic event and actual-file-loader proof receipts.
- `.lazy-harness/knowledge/graph.jsonl` plus `.lazy-harness/generated/implementation-index.json`: verified source/control/test edges; generated cache is not authority.
