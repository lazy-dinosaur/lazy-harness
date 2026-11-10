# SDD — Pi synthetic monitoring pipeline and manual-pilot readiness
> Pre-migration record: code/script/test/fixture paths below describe the layout of lazy-harness branch `work/monitoring-engine-v2` (221553d) before the monitoring implementation moved to `lazy-dinosaur/lazy-harness-monitoring`; evidence stays in lazy-harness (ADR 0062). Canonical monitoring records now live on lazy-harness main (see `.lazy-harness/ssot/monitoring-records-ownership.md`).

Status: existing baseline/A retained; additive B material/native-selection controlled structure focused-SDK/strict/fast/final-standard qualified; real-model semantics, live activation and OAuth-worker remain unqualified
Layer: SDD

## Rule digest

- Status: advisory
- Layer: SDD
- Scope: host-project
- Confidence: medium
- Aliases:
  - 공식 컨텍스트 읽기 연결
  - Pi monitoring observer
  - 관측 스냅샷
  - Pi monitoring module factory
  - explicit module registration
  - physical callback drain
- Applies when:
  - implementing/testing the opt-in observer, settled synthetic bridge/test triggers or explicitly loaded manual text-only pilot readiness using official Pi APIs
  - qualifying the opt-in source-host realtime preparation coordinator independently of the diagnostic snapshot observer
  - composing explicitly admitted transient material, per-module source grants and purpose-built native classifier selection without activating the host
- Must:
  - remain off by default; the observer performs no inference, business writes or context transformations; module assembly may invoke only host-supplied judge/delivery ports after explicit start permission
  - derive session/leaf/branch provenance from SDK and label host observation IDs separately from native entry IDs
  - distinguish projection, conversation-hook and with-system-hook stages; never equate them with final provider payload
  - report bounded-data gaps, stale/cancelled/error/timeout/overflow explicitly
  - keep slow consumer work outside awaited lifecycle/stream handlers and preserve physical concurrency until actual settlement
  - keep realtime intent/source/job validity distinct from ordinary per-request steps, without weakening the existing diagnostic snapshot lease
  - keep raw bodies in grant-filtered versioned references, not common event metadata; preserve partial/source provenance and checked selected-reference receipts
- Must not:
  - enable the live host automatically, modify shared capture/reader wiring, or add a second transcript authority
  - record thinking text, opaque signatures, image bytes, provider raw data or headers in this first scope
  - interpret observed/handled callback outcomes as main-agent delivery or business-action acceptance
- Related records:
  - `.lazy-harness/planning/monitoring-core-live-integration-plan.md`
  - `.lazy-harness/spec/platform/monitoring-core.md`
  - `.lazy-harness/tests/test-strategy.xml`

## Approval and source facts

The user selected official API connection for session-attached P0–P2. Only isolated actual SDK sessions with synthetic input/faux provider/tools are allowed in this work. External inference0, actual-user transcript collection0, model-context mutation0, business writes0. Existing package manifest and shared lazy-harness entrypoint are not changed to activate this helper.

Official Pi1.3 SDK docs, extension docs, session-format/message-types docs and exact exported declarations were read. SDK-owned session.messages/systemPrompt/subscribe exist; extension contexts supply ReadonlySessionManager/buildSessionProjection/getBranch/getSessionId/getLeafId and getSystemPrompt. A context handler has conversation only; context_with_system follows prompt/tool restoration but later handlers can still change it. This is a hook-position view, not a final provider-payload proof.

The installed AgentSession implementation emits message_end to extensions and public subscribers BEFORE appending the finalized message entry. Therefore a message_end payload may be complete while canonical projection still precedes that message. turn_end supplies native messageEntryId/toolResultEntryIds after persistence. agent_end is not final quiescence; agent_settled is the final notification boundary.

## Component contract

A separate helper exports a default-disabled registration factory and a bounded in-memory observer. It subscribes only when explicitly enabled and starts session resources from session_start. Handlers return undefined and never modify input/messages/results or request continuation. No tool/command/flag is auto-registered.

Each frame carries a host-generated observation identity/cursor, actual SDK session/leaf/branch provenance, event kind, sanitized payload and immutable snapshot. The ID is an observation correlation, not a fabricated native message entry. context/context_with_system payloads are tagged by stage. Canonical snapshots follow current projection, not all entries. Missing/oversized data is marked unavailable; silent partial context is forbidden.

Text, tool identifiers/arguments, errors and text results are in declared synthetic test scope. Thinking availability/redaction metadata may appear, but thinking body/signatures, image bytes and raw provider payload/headers are omitted. This is not a claim of full private model-context access.

An asynchronous bounded diagnostic consumer receives frames with an AbortSignal and a currentness lease. Session replacement, branch/tree/compaction, abort and shutdown invalidate queued/active leases; unsupported replacement fails closed before reading the new snapshot. Foreground hooks do not await asynchronous consumer work. This is NOT CPU/process isolation: a synchronous blocking consumer still blocks JavaScript's event loop and is outside this proof. Logical timeout reports independently while the physical slot remains until work settles. Queue/ring limits, eviction counters and explicit overflow statuses avoid silent indefinite growth. A handled diagnostic callback is not a downstream delivery receipt.

## P0 observed-channel matrix

| Source | Scope/normalization | Proof obligation |
|---|---|---|
| input | raw-at-handler input metadata/text; distinct from accepted user message | not double-counted as user.input |
| message_start/update/end | role/text/terminal metadata; only finalized user/tool-result end maps to user.input/tool.result | pending vs finalized and pre-persist timing visible |
| tool_call/result and tool_execution_* | position-specific technical observations; native toolCallId/parentToolCallId preserved | no duplicate canonical tool.result trigger |
| context | conversation-only-at-hook, no system claim | compare with actual projection and final fake-provider context |
| context_with_system | full transcript at this handler position | later transformer can differ; observer must not alter it |
| turn_end | finalized native entry IDs | IDs resolve in canonical manager |
| agent_end / agent_settled | low-level run vs final idle boundary | queued steer/recovery not called final prematurely |
| session/tree/compaction/shutdown | identity/version transition | stale work and old-session disposal cannot affect replacement |
| thinking/images/raw provider | body excluded; availability only where applicable | omission markers, not a claim to see all thoughts |

## Pi 1.5.0 observable-channel inventory (task154, read-only)

User-approved read-only survey before fixing which events monitoring watches; supersedes the Pi 1.3 basis of the P0 matrix above for the installed runtime. Sources read: installed `docs/extensions.md` (Events, ExtensionAPI `sendMessage`/`sendUserMessage`/`appendEntry`/`events`, Calling Other Tools) and `docs/sdk.md`; host `packages/lazy-harness-pi/extensions/lazy-harness/monitoring-observer.ts#observationEvents`, `packages/lazy-harness-pi/monitoring/declaration.ts` (watch), `.lazy-harness/scripts/monitoring-engine-runtime.ts#watchModuleFromDeclaration`, U1/U6 declarations. No code change, no model call.

Run order (docs): `input` → skill/template expansion → `before_agent_start` → `agent_start` → per turn [`turn_start` → model request: `context` → `context_with_system` → `before_provider_headers` → `before_provider_request` → `after_provider_response` → `provider_stream_event` + `message_start/update/end`; per executed tool: `tool_execution_start` → `tool_call` → `tool_execution_update` → `tool_result` → `tool_execution_end`] → `turn_end` → `agent_end` → (more work loops) → `agent_before_settle` → `agent_settled`.

| Group | Event | What it carries / can do | Observer registers |
|---|---|---|---|
| User | `input` | raw text before expansion, `source` interactive/rpc/extension, `streamingBehavior` steer/followUp; transform/handle | yes |
| User | `user_bash` | `!`/`!!` user shell command; can intercept | **no** |
| Run | `before_agent_start` | `messageType` user/custom, expanded prompt, system prompt options; can inject a message / patch the prompt | **no** |
| Run | `agent_start` / `agent_end` | low-level run bounds; `agent_end` is not final | yes |
| Run | `agent_before_settle` | final actionable boundary: append entries, request one continuation | **no** |
| Run | `agent_settled` | final, notification-only | yes |
| Turn | `turn_start` / `turn_end` | one model response + its tools; `turn_end` sees the persisted message and tool results and can append `custom_message`/`context_edit` and continue | yes |
| Message | `message_start/update/end` | every message (user, assistant, toolResult, custom); `update` = streaming deltas; `end` can replace | yes |
| Tool | `tool_execution_start/update/end` | args, partial output, final result/isError/duration; `end` covers every finalized call incl. blocked/invalid | yes |
| Tool | `tool_call` | before execution; mutate input or block | yes |
| Tool | `tool_result` | modify result | yes |
| Request | `context` / `context_with_system` | before EVERY model call; modify messages (the injection seam) | yes |
| Request | `before_provider_headers/request`, `after_provider_response`, `provider_stream_event`, `cache_warming_decision` | provider payload/transport level (debug) | no |
| Session | `session_start/shutdown`, `_before_switch/fork/tree`, `session_tree`, `_before_compact`, `session_compact(_failed)` | lifecycle, compaction entry, tree navigation | yes |
| Session | `session_info_changed` | session name | no |
| Model | `model_select`, `thinking_level_select` | model/level change | yes |
| Other | `ui_prompt_start/end`, `project_trust`, `resources_discover`, `mcp_servers_change` | UI waits, startup/resources | no |

Non-hook channels and paths that bypass `input`: extension commands (`/name`) skip `input` entirely; user steer arrives as `input` with `streamingBehavior: steer`; `pi.sendUserMessage` arrives as `input` with `source: extension`; `pi.sendMessage` (custom message, `deliverAs` steer/followUp/nextTurn) and `turn_end`/`agent_before_settle` `custom_message` drafts become user-role model messages WITHOUT `input` (visible as `message_*` and, when they start a run, `before_agent_start` `messageType: custom`); nested tool calls (`ctx.executeTool`) emit tool events with `parentToolCallId` but never appear in the transcript; `pi.appendEntry` data is persisted but not model context; `pi.events` is an inter-extension bus; SDK `session.subscribe` reports the same lifecycle in-process; `SessionManager`/session JSONL is the authority for finalized context, branches and compaction. The lazy-harness extension itself registers `session_start/shutdown`, `input`, `before_agent_start`, `tool_call`, `tool_result`, `context`, `agent_end` and injects `<system-reminder>` user-role content, so harness-authored text must be told apart from the user's. Not investigated here: subagent/peer sessions (own runtimes).

Current use: the observer registers 27 events, notification-only (never returns a value), normalizing `message_end` by role to `user.input` / `assistant.message` / `tool.result` and `tool_call`/`tool_result` to `tool.call.observed`/`tool.result.observed`; the legacy consumer (`monitoring-core-observation.ts`) judges only `agent_settled` windows of `message_end`. v2 modules declare `watch.events`: U1 `['input']`, U6 `['tool_call','message_end']`. The v2 engine is not yet wired to the live observer (S8). Missing registrations that matter for monitoring: `before_agent_start` (expanded prompt, custom-triggered runs), `agent_before_settle` (final actionable check), `user_bash`.

Update (task154, user-instructed “빠진 훅 다 추가”): `observationEvents` now also registers `before_agent_start`, `agent_before_settle`, `user_bash`, `session_info_changed`, `ui_prompt_start/end`, `before_provider_headers`, `before_provider_request`, `after_provider_response`, `cache_warming_decision`, `resources_discover` (38 events, still notification-only; returning undefined keeps every input/payload/decision). Deliberately not registered: `project_trust` (a handler must return a trust decision and it runs before any session context), `mcp_servers_change` (handling it makes this extension the MCP connector), `provider_stream_event` (awaited per raw chunk while each `record` reads a conversation snapshot; `message_update` already covers streaming). Focused tests: observer, module, realtime, realtime-selection, observation — 132 pass / 0 fail.

## Verification

Use actual installed SDK through explicit test-only `PI_MONITORING_SDK_ENTRY`; absent means integration is skipped, not qualified. Never fake the whole SessionManager/AgentSession to claim real integration. In-memory settings/credentials and normal-case managers plus owned temp resource paths prevent real project/session discovery. Actual runtime new/shutdown uses an explicitly owned synthetic temp session directory, never the real transcript store. The official faux provider scripts text/tool/abort/compaction fixtures. A network tripwire fails any actual fetch. Compare an independent raw event collector and actual provider-facing context against observer frames and persisted SDK projection. Optional test-only `PI_MONITORING_REPORT` writes the controlled proof receipt; neither variable activates production observation.

Protect default-disabled behavior, user/text/tool/error streams, exact source IDs, final-message pre-persistence distinction, context edits/branches/compaction, session rebind and late shutdown, slow/failing/aborted consumers, timeout physical slots, overflow, bounds and immutable snapshots. No measured synthetic transport result is a live-host deployment or semantic classifier qualification.

## Actual SDK-chain accuracy evidence pointer

The approved synthetic SDK-source→actual Jev→material/test-effect qualification is now measured, not merely proposed. Its authoritative metrics, residual failures, Contested gold boundary and limits are in [monitoring-core-reliability](../../tests/monitoring-core-reliability.md), “Actual SDK-source qualification result”. This adds evidence, not a runtime API/permission change. No real-data pilot is active and local-only P5 readiness is not an integrated semantic-product claim.

## Explicit Pi module assembly API

Primary completion surface: `packages/lazy-harness-pi/extensions/lazy-harness/monitoring-module.ts` exports `PiMonitoringModule`, `createPiMonitoringModule`, `PiMonitoringModuleOptions`, `MonitoringModuleRegistration`, `MonitoringStartPermit` and `MonitoringBridgePort`. It composes the existing observer and a host-injected existing bridge; it does not implement a second core or change the shared package entrypoint/manifest. The source-checkout convenience composition `createSourceHostMonitoringModule` in `packages/lazy-harness-pi/examples/monitoring-core/module.ts` registers the two existing reference modules against the same `MonitoringObservationBridge`.

- Setup: declare goal + immutable reference catalogue, bounded limits, `createBridge`, receiver and optional `JudgeBatchPort`; register module metadata/host grants/destination before start. Duplicate IDs/count excess are rejected; existing core grant validation precedes any SDK snapshot read. Constructor/registration metadata is frozen independently of caller mutation.
- `extension(pi)` registers notifications once and returns no event transformation/continuation. It does not start collection. Pi1.3 unsubscribe handles are owned by this instance and detached on dispose/partial setup failure; foreign handlers are untouched.
- `start(ctx, {source:'sdk-exposed-context', judge:'host-port', delivery:'host-port'})` is an explicit trusted-host declaration. This source scope includes sanitized current projection/history/system-prompt and exposed text/tool arguments/results. It is NOT the narrower P5 future-text/tool-metadata-only policy. Missing/narrower permission is rejected before reading context. The API declaration is not a sandbox and does not itself establish human approval or authorize real-data use.
- One instance owns one bounded, immutable-catalogue lifetime. Registration closes at start. Failed/start/stop/dispose cannot reset budgets through restart. `invalidateContext()` stops work; a changed goal/catalogue requires a new explicitly configured scope. Caller-owned HTTP/USD ledgers must remain cumulative and are never implicitly reset by a new instance. No semantic query parser, automatic corpus lookup, file watcher or default model is installed.
- SDK session shutdown/before-switch/before-fork and replacement identity stop the instance without automatically binding another session. Other observer invalidation/overflow/timeout/current-projection rules remain unchanged.
- `stop()` invalidates observer/core leases. Every reserved judge/processor/receiver callback rechecks running state and its AbortSignal immediately before actual dispatch; receiver dispatch also checks its source lease. This closes the stop-between-reservation-and-microtask window without freeing a physical slot early. `dispose()` is idempotent and detaches owned hooks. Raw promises remain tracked until actual settlement; `idle(signal?)` waits observer work and returned port promises. Aborting that wait cancels only observation, not physical work. Do not await this drain from inside a callback it tracks. No forced JS cancellation, immediate memory erasure, rollback or process isolation is claimed.
- `frames`, `reports` and `getStatus()` expose bounded provenance, per-source/per-module outcomes and pending callbacks; disposed instances stop exposing frames/reports. A handled/processed/idle status is not by itself an accepted material, executed business write or completed user task. Receiver guards/idempotent conditional commit and any actual classifier accounting remain host responsibilities.

Verification: the new tests cover default-off/no-read, permission narrowing, grant-before-read, immutable registration/catalogue, scope transition, owned unsubscribe, throwing ports, physical judge/processor/receiver retention and late-result rejection. Actual SDK1.3 probes exercise two judged modules plus a third registered module and source-file loading. Scripted judge/native-input parity tests do not create a new semantic accuracy score; the existing frozen baseline and residual failures stay in the primary TDD. No real-user start or additional paid classification is performed by this work.

## Pi module final validation capsule

The explicit module/source-host composition is implemented and qualified within the declared bounded synthetic scope.16 distinct component protections across initial/targeted runs, final dispatch/raw-drain/SDK/file-loader6 PASS/0 FAIL/47 assertions/0.909s, final strict PASS. Final standard900: fresh framework91, skipped0, errors[], 434.654s, evidenceReused=false. Condensed actual receipt: `.lazy-harness/evidence/monitoring-core/pi-module-factory-standard.json`; bounded runtime source: `/tmp/pi-fabric-shell-1cmqXb/output.log`. This evidence-only closure does not rerun passing tests. The existing semantic baseline/Contested label remain unchanged; additional paid classifier HTTP0 and actual-user collection/host activation0. This is a usable explicit Pi factory/API, not an automatic daemon, private-thought reader or production/business-success guarantee.

## Implementation map

- Status: implemented and focused-verified for the approved synthetic scope; not imported/activated by the shared entrypoint.
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring-observer.ts`: `createPiObservationExtension` registers only when enabled; `readObservationSnapshot` reads current SDK projection/branch; `PiMonitoringObserver` owns immutable frames, epoch/binding invalidation and one bounded physical consumer slot. Flow: SDK hook -> sanitized stage-labelled snapshot/frame -> non-awaited diagnostic queue -> explicit outcome. It does not call MonitoringCore or deliver to the main agent; per-module selection/delivery is P3.
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring-module.ts`: `PiMonitoringModule`/`createPiMonitoringModule`, `MonitoringBridgePort`, `MonitoringModuleRegistration`, `MonitoringStartPermit`, `PiMonitoringModuleOptions`; owns explicit one-lifetime start/registration/observer/hooks/raw-port drain, and delegates to one existing host bridge/core.
- `packages/lazy-harness-pi/examples/monitoring-core/module.ts`: `createSourceHostMonitoringModule` composes the same existing bridge and reference modules; source-checkout entry, not an auto-loaded extension. `README.md` in that directory shows typed host-port integration and scope/receipt limits.
- `packages/lazy-harness-pi/tests/monitoring-module.test.ts` and `.lazy-harness/evidence/monitoring-core/pi-module-factory-report.json`:16 distinct protected cases across initial/targeted runs (initial15 plus dispatch-reservation race), actual SDK1.3/source-file-loader/parity, final strict PASS, no new model HTTP. New component final standard is tracked in the primary TDD; no production activation.
- `packages/lazy-harness-pi/tests/monitoring-observer.test.ts`: bridge protections and actual-SDK acceptance.
- `packages/lazy-harness-pi/tests/support/monitoring-sdk-fixture.ts`: explicit SDK import with Bun import-condition resolution, official faux provider, in-memory credentials/settings, owned synthetic temp directories, and independent raw event collector. `assertReconciled` checks every actual scenario's order/count/IDs/native session+leaf/message view; no whole-SDK stub.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts`: existing governed hooks read for compatibility; unchanged.
- `.lazy-harness/knowledge/graph.jsonl`: seven source-confirmed component/symbol/protection/fixture/receipt edges appended without migrating or rewriting existing facts. The same verified batch is appended to `.lazy-harness/generated/implementation-index.json` as derived cache only; this is not a full-corpus regeneration or new authority.

- `.lazy-harness/scripts/monitoring-core-observation.ts`: `MonitoringObservationBridge` integrates existing observer frame snapshots with `MonitoringCore`; `materialContentHash` defines the wire digest. No observer/core implementation rewrite or runtime shared-hook activation.
- `tests/lazy-harness/monitoring-core-observation.test.ts`:19 mechanical guards and10 actual-SDK receiver scenarios; reused `monitoring-sdk-fixture.ts` remains unchanged.
- `.lazy-harness/evidence/monitoring-core/pi-observer-p3-report.json`: actual10-case SDK1.3 proof, external fetch attempts0, no live host or semantic classifier qualification.

- `.lazy-harness/scripts/monitoring-core-trigger.ts`: `SyntheticTriggerRegistry` is an explicit stopped-by-default P3 material target; grant-constrained registration and source/digest/idempotency/currentness gate controlled code handlers and distinct execution results. The calling core owns timeout/physical concurrency; the target adds active/lifetime/record bounds and no hidden queue.
- `tests/lazy-harness/monitoring-core-trigger.test.ts`:15 mechanical guards plus12 actual SDK cases; independent effect ledger preserves compaction seed effects and separately partitions each tested transition rather than deleting evidence.
- `.lazy-harness/evidence/monitoring-core/pi-observer-p4-report.json`: source→module→handoff→effect→execution actual proof, no real-data/paid-inference/business writes.

- `.lazy-harness/scripts/monitoring-core-pilot.ts`: `ManualMonitoringPilot`, `createManualPilotExtension` and default `manualMonitoringPilot` provide explicit source-file load + `/lazy-monitor` registration, pre-buffer allowlisting and local-only bounded diagnostics. No imports from full-context observer/core/bridge/trigger.
- `tests/lazy-harness/monitoring-core-pilot.test.ts`:9 mechanical +10 actual-SDK readiness cases across two focused runs; real user-data pilot not performed.
- `packages/lazy-harness-pi/tests/support/monitoring-sdk-fixture.ts`: optional extensionPaths/additionalExtensionPaths test seam, default path unchanged; actual file-loader proof.
- `.lazy-harness/behavior/pi-monitoring-pilot.md`: only the independent visible manual-control flow; this SDD remains the primary evidence capsule.

## Additive A realtime preparation contract — qualified source-host seam

This new component is distinct from the existing settled observer/bridge and is not auto-exported as a standalone engine or installed in the active host. `RealtimeMonitoringCoordinator` in `.lazy-harness/scripts/monitoring-core-realtime.ts` owns explicit single-use start/stop/dispose, watch admission, async preparation, source/permission checks, physical slots and a bounded prepared-data mailbox. `createPiRealtimeTap` is opt-in and must be installed AFTER the existing observer; it reads the newly recorded immutable frame, not arbitrary raw event fields. It ignores pre-session notifications, requires fresh ordered frames and native session identity, returns undefined, and owns unsubscribe cleanup. No existing observer/core/bridge/shared entrypoint/manifest/auth source changed.

- Intent epoch advances on observed user input or explicit host-owned advanceIntent; logical step advances on context only. context_with_system is the same step. Diagnostic frame.epoch and a changing whole projection hash are not used as realtime watch leases.
- Session/binding mismatch, cursor gaps/conflicting identity, explicit stop/observed abort and session replacement stop the watch scope. Branch/tree/compaction/model-setting transitions invalidate generation. These checks are not disabled merely because ordinary context no longer cancels realtime work.
- Host metadata ports provide permission, initial source dependency IDs/versions and current versions. Every job has at least one dependency; added preparation dependencies cannot erase the initial set. Currentness is checked at admission, execution, ready publication, handoff and via the offered guard. A metadata callback is required to be synchronous/cheap; this is not automatic filesystem watching, origin authentication or a hostile-code sandbox.
- Queue/physical concurrency/jobs/events, frames, mailbox bytes/count, dependencies, traces and timers are bounded. Queued message updates coalesce by generation/epoch/step; queued tool updates additionally use native toolCallId. Coalescing does not fabricate final text. Logical cancellation/timeout never releases an active raw promise's physical slot before settlement; synchronous blocking host code can still block JavaScript.
- takeReady('context') offers only at a current available context stage; takeReady('module') can offer after normal agent_settled if scope/grants/dependencies still hold. Pending context material is not automatically discarded solely for no next request. There is no cross-epoch cache, automatic continuation/steer/abort, injection, business write or actual model call. Offered data is not delivery/business acceptance; consumers must use currentness and their own receipts.
- Current source observer omission remains explicit: tool_execution_update partialResult bodies are not copied into the existing sanitized frame payload. A proves early progress-event/metadata dispatch, NOT complete streamed tool-output material. B must define the admitted material/source contract before making that claim. Thinking/signature/image/raw-provider omissions remain unchanged.

Focused qualification:95 PASS/0FAIL/641 assertions/2.81s; strict new-source/test typing PASS; fast check2720 PASS; standard PASS 468.26s, evidenceReused=false, fullRegression=true, ran=91, skipped=0. Actual installed SDK1.3.0/native faux4 proves early progress dispatch and late module readiness, work crossing two context steps, exactly one ready handoff at context step2 without provider-input mutation, and native steer invalidation. External fetch/model/user-data/main-injection/live-activation0. Actual receipts `.lazy-harness/evidence/monitoring-core/realtime-A/sdk-report.json`, `focused.json`, `standard.json`, `identity.json`; all5 post-focused source identities unchanged. Primary TDD owns the proof/4-layer matrix. This is A structural qualification only, not model semantic accuracy, OAuth worker or production performance.

### A Implementation map

- `.lazy-harness/scripts/monitoring-core-realtime.ts`: RealtimeMonitoringCoordinator/start/accept/advanceIntent/takeReady/stop/dispose/idle/getStatus; createPiRealtimeTap. Reuses parseMonitoringJsonData/freezeMonitoringData, existing observationEvents/immutable frames, no second observer.
- `tests/lazy-harness/monitoring-core-realtime.test.ts`: mechanical guards plus required actual-SDK acceptance, explicit blocked fetch and independent source/handoff expectations; uses existing createSdkFixture without changing it.
- Existing `monitoring-observer.ts`, `monitoring-core.ts`, `monitoring-core-observation.ts` and their protections remain intact. Graph IDs prefix kg_monitoring_realtime_a_; generic generated implementation-index owner remains pending and no canonical fact is hand-written into that cache.

Discovery capture / Rule placement: the TDD remains one proof primary; this SDD has the independent new component input/lifetime/handoff contract delta. SSOT roles/auth/data consent and DDD rules are unchanged; no live UI/BDD activation or global operating policy is introduced.

## Additive B material and native selection contract — controlled structure

The user-approved bounded B continuation adds source-host helpers only, not package auto-exports or active-host wiring. `RealtimeMaterialWindow` / `createPiMaterialTap` own admitted transient evidence; `RealtimeSelectionBridge` / `createRealtimeSelectionPipeline` compose existing Core and native ModelRouter. Import/default-off installs no hooks or model work. The factory takes explicit material kinds/tool-field admission, module watch events/reference kinds/grants/questions/destinations, host-bound model configuration/backend ceilings and a live per-module permission callback. There is no registry/provider/auth discovery, general worker invocation or paid model call in qualification.

- Install order is diagnostic observer -> B material tap -> A realtime tap. The B tap separately reads raw tool partialResult content TEXT only when tool-progress was explicitly admitted. Unadmitted image/thinking/signature/details/raw-provider fields are not copied. Existing observer frames remain unchanged. Native session/binding/cursor/event provenance stays distinct from B material IDs and Core request IDs.
- Material kinds namespace each logical source, including coexisting event-meta and text from one frame. User/final assistant text, assistant partials, tool result/progress, explicit tool fields and separately supplied host references become versioned refs only by admission. The common Core event payload contains only sourceEvent metadata. Existing per-module grant filtering is the only route by which bodies enter native judgement views; missing current material cannot fall back to snapshot/system prompt/raw event data.
- Partial refs include provisional=true and partial provenance; a callback's supplied text is preserved, not assumed to be a complete cumulative tool transcript. Finalization removes the corresponding partial source. Identical hook/final tool-result copies keep content versions despite provenance progression; ordinary context/context_with_system does not clear evidence. Observed input/scope changes clear transient material. For a host-owned manual intent change call pipeline.advanceIntent(), which resets this window AND advances A; the low-level coordinator counter alone is not the composite API. Lifetime/model budgets do not reset with intent.
- Native-classifier judge profiles must be explicitly routed/admitted, role=judge, and protocol-compatible; structured-json/general-worker profiles reject instead of silently substituting for a purpose-built decision model. Model brands are not hard-coded. Existing native run/skip/defer and reference questions/decoding, profile fingerprints, limits and raw work ownership remain authoritative. Technical omissions/errors are not fabricated semantic skip/defer.
- Every usable run must select a current admitted source. Existing Core reads selected actual refs with matching id/kind/version/content and stages `monitoring.selected-material` with an internal verified proposal receipt. Packets bind module/destination, request/event/scope, profile identity/fingerprint, selected exact text/content and source provenance. Only those packets enter A's module-ready batch; neither offered data nor an internal receipt is downstream delivery/business success. Source/grant/lease checks repeat before read/staging, after physical drain and through ready/offer guards; a revoked selected-module grant invalidates the batch even if another module remains permitted.
- B holds nested raw judge promises until actual settlement before returning its A preparation promise. Logical Core/model timeout cannot conceal physical work or recycle A slots. Factory disposal attempts every tap/owner; normal completion does not automatically cancel still-valid non-injection material. No context injection, automatic steer/continuation, cross-epoch cache or worker effects are added.
- Material defaults:32 sources/16KiB encoded content/8KiB per source/256 frame associations/2048 observed events/64 text blocks/128 diagnostic rows. Selection defaults:64 lifetime requests/4 active requests/8 modules/64KiB scoped view/48KiB output/256 diagnostic rows/10s Core deadline. Existing A/model limits also apply; dependency capacity must cover the admitted source ceiling plus its scope token. Overflow/unavailable/gap fails closed rather than silently cropping meaning. Metadata/source-version callbacks remain trusted cheap host contracts, not filesystem watching or hostile-code isolation. Captured dependency freshness is not proof that every later unrelated message was semantically reconsidered.

### B Implementation map

- `.lazy-harness/scripts/monitoring-core-realtime-material.ts`: RealtimeMaterialWindow and createPiMaterialTap; admitted exact text/field extraction, material identity/content versions, transient lifecycle and dependency guards.
- `.lazy-harness/scripts/monitoring-core-realtime-selection.ts`: RealtimeSelectionBridge and createRealtimeSelectionPipeline; immutable per-module metadata, native-profile admission, existing Core/ModelRouter composition, checked material packets, physical drain, paired manual intent and subscription ownership.
- `tests/lazy-harness/monitoring-core-realtime-selection.test.ts`:26 controlled cases including4 required actual SDK1.3.0/faux cases and explicit blocked external fetch; source/view/read/packet expectations are independent of scripted outputs.
- Reused unchanged A/observer/Core/router/adapters/SDK fixture; canonical evidence/matrix/initial failure/limits in `.lazy-harness/tests/monitoring-core-reliability.md`, receipts under `.lazy-harness/evidence/monitoring-core/realtime-B/`, graph prefix kg_monitoring_realtime_b_. Generated index owner remains pending, not fabricated as canonical proof.

Qualification boundary: B26/0FAIL/110 assertions/1.143s and strict PASS establish controlled structure only. Four actual SDK cases exercise admitted partial text, assistant text, tool result across2 contexts and native steer/raw join. Real judge semantics/latency, Pi OAuth Luna worker, main-context injection, business receipts and live pilot remain unqualified/unapproved; old quality scores/ledgers/gold remain unchanged. TDD primary owns final regression closure. This SDD is the independent component API delta, not a new operating rule.

## Additive C1 realtime execution handoff — CPU qualified, no live worker

User approved the concrete current A/B ready-offer→purpose-specific handler→independent execution-result checkpoint. NEW `.lazy-harness/scripts/monitoring-core-realtime-execution.ts` exports source-local experimental `RealtimeExecutionConsumer` and typed RealtimeExecutionPorts/Invocation/Record/Limits. Existing Core/A/B/diagnostic observer/settled bridge/trigger registry/router/auth/gold/shared loader remain unchanged. Not a new public JSON schema/package export, mandatory search/UI/Luna stage, live installation or business executor.

### Contract and accountable owner

Host explicitly starts an enabled single-lifetime consumer, supplies a stable trusted port identity, current target-binding revision, per-packet permission and actual registered-target execute callback. The Host retains routing/registration/grant/input-meaning ownership; C1 has no registerHandler/worker catalogue/model transport. Binding revisions must change when the Host replaces/unregisters targets. Host callbacks must be cheap/honest about versions and permissions; no hostile-Host protection or unobserved-ABA detection is claimed.

consume(RealtimeOffer, optional caller AbortSignal) takes ONLY the existing module channel. It snapshots JSON data without getters, checks exact candidate digest and batch/frame/intent-epoch/generation identity, per-packet structural meaning and size/count ceilings, and rechecks currentness/permissions before actual callback and after raw return. It preserves existing A/B whole-offer invalidation; receiver-specific permission/malformed result/target failure can remain module-local. It does not reclassify raw run/skip/defer or bypass checked-reference requirements in B. Module targets still validate semantic input/effects themselves.

The old MaterialEnvelope.source.settlementId refers to the settled path and is unavailable for early realtime delivery. C1 therefore DOES NOT fabricate one or modify SyntheticTriggerRegistry to accept invented source metadata. It reuses existing TriggerResult/TriggerInvocation typed execution-result semantics through a packet-native Host port. No new source authenticity/approval authority is supplied by an offer digest, valid packet or successful receipt.

### Execution, scope and physical lifetime

Request identity and physical capacity are reserved BEFORE callback dispatch, including reentry; exact duplicates reuse physical work and changed same-ID input is rejected. A duplicate has its own caller/source observation lease: cancelling that duplicate denies only its receipt, not the original execution. The handler gets only its own frozen admitted packet plus executionId/packet-only contentHash/offerId/signal/isCurrent, never the full batch/candidate bodies or other-module/whole-batch hashes. Correlation IDs are Host-issued C1 execution IDs, not native SDK entry IDs.

Target result must match execution/request/content identity, return an allowed executed/rejected/unknown status, and include an effectId to obtain a controlled executed receipt. Missing/mismatched/unknown results remain unverified. Errors use fixed redacted reasons. An acknowledgement is not business success; an independent fixture effect ledger is the actual controlled proof. Trusted/uncooperative handlers may commit before a later invalidation, so C1 cannot roll back effects or prove atomic external writes.

Defaults:64 lifetime executions/2 physical active/128 retained records/65536 candidate bytes/8 packets. Excess capacity rejects without an extra hidden queue. stop/dispose/source validity/grant/binding/caller cancellation prevent valid late receipt; observed invalidity latches for that work. Aborted/uncooperative raw callbacks KEEP active capacity until settlement. idle waits physical drain; aborting idle cancels only observation. No second timer/worker scheduler is added; Host bounds/cancels the actual target operation. No CPU/process isolation: synchronous blocking target code can block JavaScript, and callers must not await this work inside foreground lifecycle hooks.

### Implementation map and proof boundary

- New RealtimeExecutionConsumer owns bounded handoff/currentness/dedup/raw drain/receipt verification only. RealtimeExecutionPorts remains a trusted per-purpose Host adapter, not a new configuration registry.
- New `tests/lazy-harness/monitoring-core-realtime-execution.test.ts` actually runs existing createRealtimeSelectionPipeline/Window/Coordinator/SelectionBridge/Core with scripted model responses, then real in-memory target callbacks. Positive witness:2 different purposes,1 scripted native judge, selected material counts1/2,2 independently reconciled synthetic effects BEFORE agent_settled. A third target configuration works without consumer/Core purpose branches (not a hot-plugin proof).
-37 distinct CPU cases across initial36 and changed-duplicate-only2(one recheck), final strict/import pass; no actual SDK session/model/network/business effect or live loader activation. Primary reliability TDD/matrix and c1-checkpoint/c1-standard own exact execution history/terminal status. Existing generic SDK/old P4/A/B/semantic scores are not recounted or replaced. Actual worker/OAuth/native runtime end-to-end/main-context/live qualification remains separate.
- Canonical graph kg_monitoring_realtime_c1_* maps only verified source-local exports, type dependencies, protection and capsule. Derived implementation index remains stale for additions; exact source/MD/graph fallback, no manually invented cache truth.

## Additive Pi-worker Host adapter — offline qualified; bounded native consumption observed

`createPiWorkerExecutionPorts` in `.lazy-harness/scripts/monitoring-core-pi-worker.ts` is a source-local experimental adapter for EXISTING C1 RealtimeExecutionPorts, not a public package export, Core router/worker catalogue, autoloaded extension or permission authority. Host explicitly supplies SDK/session facade, model/runtime/cwd/agentDir, admission/revision/permission and feature resolution. No ambient session/discovery/network at factory construction. Offline contracts and the actual installed Pi1.4/openai-codex/gpt-6-luna OAuth route now have bounded two-synthetic-purpose Host-port consumption evidence, primary in `.lazy-harness/tests/monitoring-core-pi-worker.md` and native-checkpoint. This is observed availability/transport for those cases, NOT universal SDK authenticity, full native A/B/Core/D/live qualification, real-provider failure matrix or server token/cost/quota enforcement. No interface/invariant changes accompany this runtime evidence update.

PiWorkerFeature owns exact module/destination, instructions, cloned TypeBox input schema, required admitted material IDs, strict semantic validateInput and actual execute/effect callback. Worker receives bounded feature/schema metadata, then only exact own-packet material reads through the sole custom read_material tool; payload projection is id/kind/version/text only. No file/web/shell/extra resources or model-origin execution/effect IDs. Additional tools or model fallback deny before prompt. Empty extension/skill/prompt/context discovery plus in-memory session/settings, retry/compaction off, prompt expansion off preserve the proposed isolated worker boundary. This is trusted Host/SDK integration, NOT a hostile-code sandbox.

Latest successful authoritative assistant message_end stop must match the SDK getter's final text; error/aborted/length/toolUse, missing event or stale getter cannot qualify partial JSON. Thinking content is not collected. The existing bounded JSON parser, feature schema, actual tool read IDs and Host meaning/source/currentness are independent gates. Target executes only after worker idle/abort/drain/disposal and a fresh currentness/admission check; receipt echoes C1 execution/request/content identity and requires an actual Host effectId. Revocation latches; SDK/target errors redact. Source has no independent queue/registry or rollback promise.

PiWorkerLimits defaults: timeoutMs15000/maxInputBytes65536/maxOutputBytes16384/maxReads8/maxTurns4; safe finite integer bounds and shared parser effective128KiB ceiling apply, no silent truncation. maxTurns is LOGICAL, not provider HTTP requests/tokens/cost. Cancellation/timeout retains raw SDK creation/prompt/idle/abort (including abort begun during cleanup) and target work until settlement; C1 still owns physical capacity and admission. The Host must keep execution off foreground lifecycle hooks. Later native execution requires separately admitted exact model/provider-request/token/tool/time/retry/drain controls; this offline component is not paid/native worker qualification.

Implementation map: verified source exports PiWorkerSession/PiWorkerSdk/PiWorkerLimits/PiWorkerContext/PiWorkerFeature/PiWorkerHost/createPiWorkerExecutionPorts; existing C1 Host port and generic invokeWorker/router remain unchanged. `tests/lazy-harness/monitoring-core-pi-worker.test.ts` covers offline safety/protocol and existing A/B→C1→new port→independent test ledger; primary `.lazy-harness/tests/monitoring-core-pi-worker.md` owns38-case actual proof, failure history,4-layer matrix and final receipt. No production config/credential/schema/provider/manifest change. Derived index additions stay explicitly stale; canonical source/MD/graph remain evidence.

## Rule placement

- Rule: P0–P4 synthetic pipeline and P5 manual-pilot readiness are component contracts, not automatic real-data activation or a new global operating policy.
- Scope: layer-fact
- Primary record: `.lazy-harness/spec/platform/pi-monitoring-observation.md`
- Why not AGENTS.md: component boundaries and source coverage are not universal agent grammar.
- Why not local notes: shared framework API/protection belongs in canonical records.
- Confirmation: user-confirmed (selected scope; exact implementation verified by tests before completion)


## P3 synthetic bridge contract — approved and focused-verified

The native option selected synthetic P3 implementation, including focused/strict validation and final standard900. This record remains the primary component contract; the existing integration plan owns only the approved staged proposal. No external inference, actual-user-data collection, main-context mutation, business writes or P4–P6 authority is added.

The explicit source-host bridge will reuse `MonitoringCore` and existing module contracts. It reads the observer's already bounded immutable frame ring at `agent_settled`, reconciles source cursors and current canonical membership, then passes only each original event's sanitized content plus allowed versioned host references. It does not add a second transcript store, mutate the observer or treat its stale-skipping diagnostic queue as a reliable source spool. Missing frame ranges, unavailable data, superseded branches/bindings and aborted runs must defer visibly. Settlement-only latency is deliberate in this slice; it is not an in-turn live selector.

The controlled target is an independent synthetic in-memory receiver, not the main agent. Its material envelope includes destination, source observation/session/binding/cursor/settlement/context identity, original core proposal identity and a SHA256 digest over the envelope without that digest. It acknowledges exact request identity, destination, content digest and record ID. `recorded` requires both core currentness and the observer lease before and after handoff plus a valid receiver acknowledgement. Receipt does not certify a business operation; an uncooperative receiver cannot be forcibly rolled back.

A scripted JudgeBatchPort is a transport test double, not semantic keyword classification or a new model-accuracy result. Explicit processor watches/reference/action grants constrain each view. No whole transcript is copied into the generic event payload. Fixed approved synthetic host references are versioned; selected bodies and IDs must match what the independent receiver actually records.

Source: `.lazy-harness/scripts/monitoring-core-observation.ts` is an explicit source-host proof library: runtime imports only the adjacent core; observer types are erased. `MonitoringObservationBridge.consume` reconciles the existing frame ring at settlement, `process` constructs source-bound core inputs and `deliver` validates the independent target acknowledgement. `materialContentHash` documents the exact SHA256/JSON wire rule. Protection: `tests/lazy-harness/monitoring-core-observation.test.ts` uses the existing actual-SDK fixture and separately implemented receiver. No Pi package activation/import/wiring change is made.

## P4 controlled test-trigger contract — implemented and focused-verified

The user said “좋아 계속 진행해봐” after the assistant explicitly named the next P4 path: received material -> allowed test handler -> independently confirmed execution result. That continuation is interpreted narrowly as execution approval of the already recorded P4 synthetic shadow-trigger stage, not P5/P6, paid inference, real transcripts, main-agent injection or business writes. Retain the established zero-disclosure constraints and bounded final standard900 strategy; do not run a known-insufficient300s attempt first.

An explicit source-host registry is the P3 material receiver. It maps exact declared material kind+destination to trusted registered handlers and explicit allowed processor IDs; registration cannot exceed host grants. No model-generated code or command is executed. A third handler is registered without module-specific branches in core, observer or bridge.

Each controlled test handler receives immutable material, a host-issued execution correlation, AbortSignal and a currentness guard. It performs only a synthetic in-memory effect, then returns an execution receipt binding execution ID, original request ID, content hash and an effect ID. An independent test-owned effect ledger must actually contain that effect with the exact received material. Material receipt alone is never reported as proof of an action.

Default registry is stopped. Stop/unregister/replacement invalidate in-flight work. Duplicate requests are deduped within this bounded registry instance; conflicting identity/content is rejected. No cross-process exactly-once guarantee. Handler failures/unknown or malformed execution results do not manufacture success or erase another handler's result. Physical concurrency remains held by the calling core stage until the actual handler settles; the target itself rejects excess active/lifetime/input budgets rather than spawning an unbounded queue. No extra timeout authority duplicates the core's stage timer.

The commit guard must be checked by trusted handlers immediately before their synchronous test effect. This fixture does not prove atomic external commits or undo an uncooperative handler's already committed effect. Test driver independently reconciles source event, selected bodies, receiver handoff, actual test state and acknowledged execution across needed/unneeded/deferred scripts, duplicate replay, cancellation, tree/compaction/session changes and failure isolation.

Implementation: `.lazy-harness/scripts/monitoring-core-trigger.ts` exports `SyntheticTriggerRegistry`. `registerHandler` narrows exact kind/destination/processor host grants; `receive` verifies the source-linked material digest, reserves request identity before trusted/reentrant invocation and bounds active/lifetime work. `execute` awaits actual handler settlement, verifies effect-linked execution result and returns a distinct material receipt. Protection: `tests/lazy-harness/monitoring-core-trigger.test.ts` independently records source, handoff, actual in-memory effect and execution receipt. Existing core, observer, P3 bridge and shared runtime entrypoint were not edited for P4.

## P5 manual-pilot readiness contract — approved, real pilot not started

The native questionnaire selected post-start user/assistant TEXT plus tool name/status only, local RAM10minutes/500events/1MiB (first limit stops), and manual start after readiness. A second native execution selection approved implementation/synthetic verification/standard900 ONLY. No actual-user-data collection or automatic activation is authorized by that selection.

Add a separate explicitly loaded source-host extension `.lazy-harness/scripts/monitoring-core-pilot.ts` and protected test `tests/lazy-harness/monitoring-core-pilot.test.ts`. The installed official extension guide supports `pi --extension ./file.ts` and default factories. Do not modify shared index/settings/manifest/capture/reader/core/observer/bridge/trigger wiring. Default factory registration starts no timer, task, watcher or data collection. Commands `/lazy-monitor start|status|stop|reset` are human controls; start requires idle interactive UI, not a model-callable tool or inferred user-text intent.

The field allowlist applies BEFORE copy/hash/ring/queue: future finalized user/assistant text; tool name/call identity/status metadata. No tool arguments/result bodies, history/system-prompt/context APIs, thinking/signature/image/raw-provider/error bodies or full-message JSON. Native session/leaf-at-hook identity stays distinct from a host observation ID; message_end remains a pre-persist observation, not provider-final context.

Approved caps measure serialized UTF8 retained DATA, not process RSS/heap. Additional narrow per-frame/queue/diagnostic-deadline caps may only tighten the chosen maximums and must expose omitted/overflow/cancelled outcomes. Local diagnostic target only; never call P3 semantic workers or P4 handlers on real data. Stop/reset/deadline/event/data cap/session switch/shutdown clears owned raw ring/queue and aborts active diagnostic work. An uncooperative callback can retain its one permitted frame until actual settlement; report outstanding bytes/physical slot, reject restart while it settles, and do not claim forced memory zeroization or CPU isolation.

Readiness tests must independently observe the allowed frame/receipt, throw on any forbidden getter/full-history API access, prove default-off/timers0 and exact command gating, exercise all caps/stop/reset/slow/error/scope changes, and use the actual SDK/faux provider for synthetic event sequences. Actual P5 pilot remains unperformed until the user later loads the extension and starts it. Readiness evidence is not a live-session success claim; P6 remains out of scope.

## P5 readiness evidence capsule — real pilot remains OFF/unperformed

- Initial focused:18 PASS/0 FAIL,163 expectations,985ms (9 mechanical +9 actual SDK). One type-only expectation was widened from a literal-union array to string[]; functional green checks were not rerun unchanged. Added separate ACTUAL TypeScript file-loader case:1 PASS/0 FAIL,5 expectations,675ms. Total distinct protected cases19 (9 mechanical +10 actual SDK), not a claim of one combined19-case run. Final strict source/test/fixture typing PASS.
- Actual receipts: `.lazy-harness/evidence/monitoring-core/pi-observer-p5-readiness-report.json` (nine scenarios) and `.lazy-harness/evidence/monitoring-core/pi-observer-p5-loader-report.json` (one actual explicit source-file-loader scenario). Both use installed SDK1.3 official faux provider and fetch-denial tripwire. No actual-user data/pilot or additional inference occurred.
- Allowed future user/assistant text exactly matches an independent receiver; forbidden context/history API reads0. Actual tool trace admits2 metadata frames while argument/result sentinel and thinking bodies are absent from the owned ring and target. Pre-buffer getter sentinels protect against reading raw inputs/results/signatures/images/context APIs before filtering. Loading the source file registers the command with errors0 but leaves frame/data counts0.
- Actual session/tree/compaction clears owned data and remains off; later programmatic SYNTHETIC rearm captures only new two-frame text traces. This is not a live human-start trial. Command idle/TUI gating is mechanically tested; actual headless start is denied. Slow/failing diagnostics preserve foreground response and do not generate late received receipts. Event cap stops admission and clears owned text without cancelling main execution.
- Caps/stop/deadline/reset, queue overflow, failed/incorrect ack, no early restart while one physical diagnostic frame remains, and default-off/timers0 are protected. Stop also cancels owned diagnostic timers. Claimed bytes are serialized UTF8 retained data, not whole-process heap; uncooperative external references cannot be forcibly zeroized.
- Privacy scope: no extra observer file transcript, transmission/model calls or main-context writes. Normal Pi provider operation/native transcript retention is unchanged; the SDK remains conversation authority. This clarification does not authorize a new disclosure or mutate existing session settings.
- Readiness behavior delta is independently recorded in `.lazy-harness/behavior/pi-monitoring-pilot.md`. No independent DDD/business or global SSOT ownership/config delta; fixed component caps and test-only report/SDK parameters stay with this component. Graph/cache facts are source-verified, not a full-corpus regeneration.
- Pre-standard checkpoint: fast static PASS (2629 checked), record-lint201/201 clean,issue0, final strict typing PASS. The coherent pilot/test/optional-fixture/SDD/independent-BDD/graph/cache batch is complete; no real pilot has been started.
- Final standard900 readiness: PASS. Actual task `efd9be9a-1c3b-45bb-b40b-113eaa862f07`, `ok=true`, `fullRegression=true`, `evidenceReused=false`, `errors=[]`,421.96s. Fast-static passed2.257s; fresh full-self-test passed403.156s: framework91/0skipped/jobs4. Actual CLI JSON saved at `.lazy-harness/evidence/monitoring-core/pi-observer-p5-readiness-standard-900.json`; original log `/tmp/pi-fabric-shell-PyiaGF/output.log`. Synthetic completion-turn write was blocked; no bypass, and this armed continuation closes evidence only. Source/tests/config unchanged after green. This is manual-pilot FEATURE readiness, NOT new semantic accuracy or a real-session P5 pilot; the user's accuracy-testing correction is captured in `.lazy-harness/tests/monitoring-core-reliability.md`. No repeat regression is required for this capsule update.
- Organization review: changed new pilot/test plus optional fixture loader seam only. One class owns RAM/timers/queue; factory owns commands/lifecycle; no shared index/settings/manifest/capture/reader/observer/core/bridge/trigger edits or architecture-profile inference.

## P4 evidence capsule

- Focused:27 PASS/0 FAIL,323 expectations,1369ms;15 mechanical guards plus12 ACTUAL SDK1.3 scenarios. Strict typing PASS after two type-only test corrections (sync/async receiver return and optional execution ID); passing functional behavior was not rerun unchanged. Actual report: `.lazy-harness/evidence/monitoring-core/pi-observer-p4-report.json`.
- Two scripted run modules:2 target handoffs,2 independently observed memory effects,2 verified execution receipts. Skip/defer each produce0 handoffs/effects/executions. A third registered audit module handles the canonical native tool result without core/bridge/observer feature branches:3 handlers,4 actual effects total.
- End-to-end duplicate replay keeps handler invocations/effects at2, not4. Concurrent/reentrant target replay also reserves identity before invoking code. Failed candidate handler preserves the other module's one valid effect; failure and result mismatch are not successful execution receipts.
- Actual wrong execution hash case observes2 physical effects but only1 verified execution and1 unverified result. This deliberately preserves the distinction between an effect that happened and evidence that may be acknowledged; no rollback or atomic business commit is claimed.
- Actual session/tree/compaction transitions each yield0 effects from blocked superseded work, then2 effects in the new scope. Previously committed compaction seed effects remain in the independent ledger and are reconciled too. SDK abort produces0 handler invocations/effects. Logical deadline retains physical test-handler slots until raw settlement and produces0 late verified executions.
- Default stopped, exact grant routes, denied tamper/source/processor, malformed/unknown/rejected/absent result, unregister/replacement, stop/start budget continuity, bounded active/lifetime/input/record retention and failure isolation are protected. Dedupe is registry-instance-local only.
- Pre-standard checkpoint: fast static PASS (2623 checked); record-lint200/200 clean,issue0; strict source/test typing PASS. Coherent source/tests/SDD/graph/cache batch is complete. Only post-green evidence-capsule/status closure remains after the final report.
- Final standard900: PASS. Actual task `9672ba24-e036-4b08-a4e4-0a2164d2456d`, `ok=true`, `fullRegression=true`, `evidenceReused=false`, `errors=[]`,429.478s. Fast-static passed2.26s; fresh full-self-test passed407.224s: framework91/0skipped/jobs4. Actual CLI JSON saved at `.lazy-harness/evidence/monitoring-core/pi-observer-p4-standard-900.json`; original log `/tmp/pi-fabric-shell-UXq4yr/output.log`. This is P4's own fresh validation. Synthetic completion-turn writes were blocked by `not-armed(synthetic-turn)/empty-output` even after map/read; no bypass was used. User continuation enabled current armed-turn evidence-only closure. Source/tests/config unchanged after green; no redundant regression is required. P5 real-session pilot/P6 live delivery and semantic classifier qualification remain unselected.
- Discovery capture and organization review: this primary SDD owns P4 component semantics/protection/evidence; existing Planning contains the continuation boundary. One registry owns exact routes/request reservations/execution receipts; the existing core owns logical deadlines and physical slots; the test owns all synthetic effects. New source/tests only, no architecture-profile inference, line-count split, shared-hook changes or global operating rule.

## P3 evidence capsule

- Final focused checkpoint:29 PASS/0 FAIL,290 expectations,1354ms;19 mechanical guards and10 ACTUAL SDK1.3 scenarios. Strict source/test typing PASS. Actual case report: `.lazy-harness/evidence/monitoring-core/pi-observer-p3-report.json`.
- Independent receiver verifies/recomputes body digest, records actual material, and asserts selected reference ID/version/body plus original source identity/cursor. The normal text trace produces4 receipts, tool/error6, queued-steer8. Excluded-reference bodies do not reach the receiver. This is scripted selection execution, not semantic judgement accuracy.
- Actual replacement/tree/compaction in-flight cases produce old receipts0 and new receipts4 each. Wrong target hash produces attempts4 but recorded0: physical observation is not falsely reported as verified acknowledgement. Ring overflow17 and unavailable-source20 are surfaced as omission/defer with received0. Abort receives0.
- Settled-only bridge reconciles the retained source ring rather than modifying the P0–P2 diagnostic callback policy. A current frame may be unavailable and thus never invoke the diagnostic consumer: the observer's explicit unavailable outcome, not a fabricated bridge receipt, is the evidence in that case. No in-turn/live-latency or lossless-overflow guarantee.
- Reference count/bytes, frame/source/material size, batch lifetime and report retention are bounded. Duplicate settlement does not redeliver; conflicting IDs/order/gaps defer visibly. Cooperative cancellation and logical receiver timeout retain the core's physical slot until actual settlement, with no late recorded receipt. A failed module does not erase others' valid receipts.
- Pre-standard checkpoint: fast static PASS (2619 checked); record-lint200/200 clean,issue0; shared runtime entrypoint has no import/activation of the P3 bridge. Source/test/contract/graph/cache mutation batch is complete.
- Final standard900: PASS. Actual task `f06e87be-2bcc-465e-ae97-b0bd4ce16229`, `ok=true`, `fullRegression=true`, `evidenceReused=false`, `errors=[]`,437.944s. Fast-static passed2.268s; fresh full-self-test passed416.043s: framework91/0skipped/jobs4. Actual CLI JSON saved at `.lazy-harness/evidence/monitoring-core/pi-observer-p3-standard-900.json`; original log `/tmp/pi-fabric-shell-jRFkOq/output.log`. This is P3's fresh validation, not reuse of P0–P2 evidence. Synthetic completion-turn writes were blocked by `not-armed(synthetic-turn)/empty-output` even after map/read; no bypass was used. The subsequent user continuation allowed current armed-turn evidence-only closure. Source/tests/config are unchanged after green; no redundant regression is required. P4–P6/live activation and semantic classifier qualification remain outside this proof.
- Development repairs: test expectations now use the existing module wire shape `{id,version,content}` and SDK text-block input; actual compaction proof seeds enough history BEFORE the blocked target so compaction itself invalidates that batch. No production classifiers or thresholds were tuned.
- Organization review: changed new source/tests only. One bridge owns scan cursor/core lifetime/ack verification; existing observer owns bounded source memory and the independent test receiver owns observed material. Runtime core reuse, type-only observer import and no shared entrypoint mutation keep ownership narrow. No inferred architecture profile or line-count refactor.

## P0–P2 evidence capsule

- Focused final:16 PASS/0 FAIL,81 Bun expectations,859ms;8 mechanical protections plus8 ACTUAL SDK1.3.0 scenarios. The independent Node assertions additionally reconcile every actual trace's event count/order, unique observation IDs, native session/leaf, message view and provided native tool/entry IDs.
- Receipt: `.lazy-harness/evidence/monitoring-core/pi-observer-p0p2-report.json` (eight actual scenario proofs, network fetch attempts0). Handler timing is a synthetic observation, not a live p95 SLO.
- Strict source/test typing: PASS after the final reconciliation-helper addition. Fast static PASS (2613 checked); record-lint200/200 clean, issue0.
- Initial standard attempt: FAILED by bounded timeout. Actual task `0f2f216a-c5f6-47e8-a6fa-efb9b272de12` exited1 after300.105s; fast-static passed2.335s and full-self-test timed out after275.432s. Original log `/tmp/pi-fabric-shell-8srmoa/output.log` remains preserved. This attempt itself was not green and does not establish the status of every individual assertion.
- Final standard900: PASS. Actual task `3f3e32df-9e8d-4486-a295-23e1f40d7e75`, `ok=true`, `fullRegression=true`, `evidenceReused=false`, `errors=[]`,435.506s. Fast-static passed3.403s and fresh full-self-test passed409.562s: framework91/0skipped/jobs4. Actual CLI JSON preserved at `.lazy-harness/evidence/monitoring-core/pi-observer-standard-900.json`, original log `/tmp/pi-fabric-shell-TZbUma/output.log`. This closes only the approved synthetic P0–P2 proof and framework validation, not P3–P6, operational reliability or activation.
- Evidence-only closure: the synthetic completion turn blocked artifact/capsule writes with `not-armed(synthetic-turn)/empty-output`, including after map/read recovery. No bypass was used. The user then requested continuation; the current armed work-unit turn saved the report and capsule after current readback. Source/tests/config remain unchanged; a post-green evidence-capsule update does not require another full regression.
- Retry approval: user said “계속해줘” immediately after the recommended900s standard retry was offered. User-confirmed scope is one retry of the SAME standard with `--max-seconds=900`; release/new model calls/actual transcript collection/operational activation are not added. Prior300s timeout remains preserved; no focused green checks or source edits are repeated to consume time.
- During development the technical `tool_result` hook collided with the canonical terminal `tool.result` kind. It now emits `tool.result.observed`; only finalized tool-result message_end emits `tool.result`. The one-result assertion prevents duplicate semantic triggering. `tool_call` is similarly position-labelled `tool.call.observed`.
- P0 access/coverage, P1 actual synthetic source collection and P2 lifecycle guards remain verified. P3 selection/material receiver is implemented/focused-verified in the explicit source-host bridge above, with its own final-standard status below. P4 downstream trigger, P5 real-data pilot and P6 operational delivery/actions remain outside this work.
- Production entrypoint/manifest unchanged; no live host activated, external inference0, actual-user transcript collection0, business writes0. This proof does not qualify semantic module reliability, full model thoughts or final-provider payload equivalence.

### Layer completeness decision

| Layer | Independent semantic delta | Disposition |
|---|---|---|
| SDD | Official-API observation/lifecycle, settled material acknowledgement and controlled test-trigger execution contract | This primary record and its source/tests/graph/cache |
| BDD | Independent human-visible explicit load/start/status/stop/reset flow for P5 readiness | `.lazy-harness/behavior/pi-monitoring-pilot.md`; actual real pilot still not run |
| SSOT | No production config/ownership/storage authority change; test-only SDK/report parameters are owned by this component proof | no independent delta |
| DDD | No domain entity/business rule changed | no independent delta |

Protection cases and the development collision stay with this API qualification; no duplicate canonical TDD narrative or global testing-policy change is introduced.

### Discovery capture and organization review

- Discovery capture: required source facts, source-stage limitations and completed-slice evidence are captured in this primary SDD; the existing integration plan links here. No separate research/candidate promotion.
- Observe-only code-organization review: changed new files only; one observer owns binding/epoch/queue outcomes, the fixture owns isolated SDK resources and the tests own expectations. No inferred architecture profile, line-count split, untouched rewrite or second transcript authority.


## Opt-in late-result carry mailbox (task140)

`ContextCarryMailbox` in `.lazy-harness/scripts/monitoring-core-context-mailbox.ts` holds prepared READ-ONLY context material. `take(scope, now, firstRequestOfTurn)` delivers items of the current turn, or carries an item from the previous turn only at the next turn's first request with an origin/age label; it drops on session/branch change, dependency version change, age > `maxAgeMs` or more than `maxCarryTurns` (0..1), never delivers twice and refuses duplicate ids. It installs no hooks, timers or network, never classifies user text and does not change the coordinator's intent_changed invalidation. Not wired into the live host. Primary evidence: `.lazy-harness/tests/monitoring-core-pi-context-delivery.md`.

## Parent report delivery (task146, engine v2 S6)

`createParentReportDelivery` connects runtime reports to the main model input through `ContextCarryMailbox` and a `context_with_system` extension: turns counted on `input`, branch scope renewed on tree/compaction, report keeps its trigger turn. Not wired into the live host. Evidence: `.lazy-harness/tests/monitoring-engine-v2-contract.md`.

## Inline worker mode (task144, engine v2 S5)

`createPiWorkerExecutionPorts` accepts `mode: { inline: true }`: admitted material bodies are inlined in the prompt and no tools are offered, so one dispatch produces the feature input; validation/receipt rules are unchanged and the default read_material protocol is untouched. Evidence: `.lazy-harness/tests/monitoring-engine-v2-contract.md`.

## Module runtime and judgement log (task143, engine v2 S3/S4)

`MonitoringModuleRuntime` (`.lazy-harness/scripts/monitoring-engine-runtime.ts`) turns a trigger (declared module matched + selected evidence) into the module's effective jobs and enforces engine rules: loop guard (own-module origin or depth ≥ 1), canonical idempotency keys (per-event / per-subject / module-ledger) recorded even when uncertain, `ApprovedBudgetGate` (explicit user approval, per-run reservation of declared caps, in-run consumption limits), uncertain effect = terminal stop, risk-tier output limits (proposal cannot execute effects; read-only cannot execute or propose), user-chosen report mode. `watchModuleFromDeclaration` maps a v2 declaration onto the existing selection bridge (the bridge already batches all modules of an event into one judge call). `JudgementLog` (`monitoring-engine-judgement-log.ts`) keeps one entry per module task with bounded entries/age; without content consent it keeps only ids, kinds, selection and digests. Source-local; nothing wired into the live host. Evidence: `.lazy-harness/tests/monitoring-engine-v2-contract.md`.

## Per-message history and default redaction (task142, engine v2 S2)

`RealtimeMaterialWindow` adds `historyMode: 'blob' | 'message'` (default blob = unchanged). In message mode each prior message line becomes its own `conversation-history` material with `historyIndex`, provenance = the input frame, newest kept first within the remaining source-count and byte budgets (oldest dropped; the window never fails because of history). Every observation-derived material passes `redactSecrets` (`.lazy-harness/scripts/monitoring-core-redaction.ts`) before it is stored: an engine rule, not a module option; host-supplied base references are not rewritten. Evidence: `.lazy-harness/tests/monitoring-engine-v2-contract.md`.

## Opt-in recent conversation history material (task136)

`RealtimeMaterialWindow` accepts `historyTurns` (0..8, default 0: unchanged). When >0 and the `conversation-history` kind is admitted, each `input` frame adds one material derived from that frame's canonical projection: prior turns only (user, assistant, tool call, tool result lines), line clip 800 chars, oldest lines dropped to fit `maxSourceBytes`, provenance owner=observation with the input frame id. It is replaced on the next input and never reused across intents. Modules must explicitly grant the kind. This is synthetic-evaluation scope; collecting history from real sessions exceeds the current P5 consent and needs a separate decision. Primary evidence: `.lazy-harness/tests/monitoring-core-e2e-acceptance.md`.

## Bounded native main-input handoff proof — D1 evidence only

Primary `.lazy-harness/tests/monitoring-core-pi-context-delivery.md` and its native result record qualify ready/stale context delivery through actual isolated SDK hooks AND final model HTTP input plus independent consumer response. The explicit operational Host fixture reuses prior worker receipts as fresh Host-owned dependencies; it is NOT a new observer transformation/public context-injector API or a fresh native judgement/worker pipeline. Existing observer/Core interfaces/default-off/shared entrypoints remain unchanged. No full C/D/live/token/SLA guarantee follows from this bounded proof.

## Step2b additive host Bridge input projection contract — mock qualification only

### Implementation map

`RealtimeInputProjection` in `.lazy-harness/scripts/monitoring-core-realtime-selection.ts` is an optional `RealtimeSelectionOptions.inputProjection` runtime host port: fixed opaque evidenceId/contractId, cheap sourceVersion(id), synchronous capture({input,window,modules,referenceKinds,evidenceRevision,contractRevision}) returning the existing `WindowProjectionSource`. It does NOT belong to JSON configuration, does not supply authentication/approval authenticity, and does not enable a worker or live host. IDs/callback identities are fixed at construction while genuine owner revisions remain live. Missing/malformed/colliding ownership fails closed.

`RealtimeSelectionBridge.dependencies` includes both registered metadata deps before A starts; public sourceVersion resolves only those IDs plus delegated Window body/scope IDs. The factory's opt-in dependency ceiling is maxSources+3 (caller-insufficient limits reject), absent-port stays maxSources+1. Capture must match the admitted frame and exact body/scope/metadata dependency set before any model dispatch; version values enter the opt-in context digest. Captured source and per-module prepared batches stay only in existing Work until physical drain.

Existing source projection and Router prepare handle the admitted group. The Bridge passes the narrow plain tasks/request result, preserving Router codec/accepted-subset reindex/final-byte cost reservation and raw lifetime ownership. An opt-in read-only fence before original estimate/invoke reuses current job/lease/permissions/source/metadata/profile/request checks and passes the unchanged final request through. No new cost, queue or transport owner is introduced; SDK generic model/backend independence and host credential selection are unchanged.

After actual Core reads, existing batch.checkRunEvidence must allow a packet. Successful opt-in `RealtimeSelectionPacket` adds optional projectionVersion; missing/unchecked required roles or approval suppress that packet rather than authorizing it from native run alone. Absent-port behavior/packet keys retain the old path; A continues to invalidate metadata-stale ready offers.

Protection and exact validation rollup: `tests/lazy-harness/monitoring-core-selection-projection.test.ts`, primary `.lazy-harness/tests/monitoring-core-reliability.md`, checkpoint `.lazy-harness/evidence/monitoring-core/bridge-projection-checkpoint.json` and separately terminal standard receipt. Actual SDK/model/worker/source authenticity and semantic quality are unqualified; this is synthetic mechanical integration, not live activation. Graph facts kg_monitoring_bridge_projection_* map source/export/protection/evidence; generated cache is stale and must not override verified source/Markdown/graph. Existing Core/A/Window/Router/source-provider/auth/settings remain unchanged.
