# Planning — Jcode Native Lifecycle Parity Primitives

Status: approved-in-progress
Date: 2026-08-01
Layer: Planning
Primary ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
Related SDD: `.lazy-harness/spec/platform/jcode-agent-adapter.md`, `.lazy-harness/spec/platform/pre-response-rule-context.md`
Related TDD: `.lazy-harness/tests/jcode-agent-adapter.md`
Related candidate: `candidate-jcode-native-lifecycle-parity-primitives-20260801T1219Z`

## Rule digest

- Status: active
- Layer: Planning
- Scope: transient-plan
- Confidence: high
- Aliases:
  - Jcode native parity primitives
  - before_model hook
  - native ask tool
  - bounded turn followup
  - Jcode lifecycle parity phase 2
- Applies when:
  - planning or implementing the user-confirmed A direction for closing Jcode context reinjection, option-gate UI, and bounded continuation gaps
  - changing Jcode core lifecycle/tool/protocol surfaces required by the lazy-harness thin adapter
- Must:
  - implement generic Jcode primitives first and keep lazy-harness policy outside Jcode
  - stage context injection, native ask, and bounded followup separately with focused validation and rollback after each phase
  - preserve exact trusted-root activation and root/session evidence isolation in the lazy-harness adapter
  - use GPT-5.6 Sol for GPT-routed planning, implementation, and review work; do not route this plan to older GPT models
  - obtain fresh user execution approval for this exact plan before source implementation
- Must not:
  - restore generated project-local `.jcode` policy wiring
  - make observer stdout authoritative or silently reinterpret detached hooks as blocking/injecting
  - let bounded continuation bypass an unresolved option gate, requirements-first approval, user cancellation, or irreversible-action confirmation
  - claim parity until local, remote, headless/ACP, adapter, and live-session evidence exists for the affected capability
- Record completion:
  - update phase status, changed files/symbols, validation evidence, residual gaps, and rollback state after every implemented phase
- Related records:
  - `.lazy-harness/decisions/0038-requirements-first-change-gate.md`
  - `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
  - `.lazy-harness/spec/platform/jcode-agent-adapter.md`
  - `.lazy-harness/tests/jcode-agent-adapter.md`
  - `.lazy-harness/planning/jcode-runtime-adapter-pilot.md`

## User-confirmed direction and approval state

- Direction: **A — staged generic Jcode primitives**, user-confirmed on 2026-08-01.
- Model correction: GPT-routed work must use **GPT-5.6 Sol**, not GPT-5.5; the incorrectly spawned GPT-5.5 reviewer was stopped and its output discarded.
- Current stage: Phase 1 Jcode core committed; thin-adapter integration and live validation in progress.
- Implementation approval: **granted by the user with option A on 2026-08-01T12:43:57Z**. This closes the ADR 0038 execution gate for the exact plan below.
- Independent review: a GPT-5.6 Sol reviewer completed a read-only seam/risk review. Its four corrections are incorporated below: inventory all duplicate provider loops, do not treat command stdin as ask transport, move followup ownership out of TUI-only state, and keep ACP interaction support explicitly unresolved until capability evidence exists.

## Objective

Close the three capability-specific Jcode gaps recorded by the current adapter pilot without coupling Jcode core to lazy-harness policy:

1. inject bounded dynamic context before the initial and post-tool provider calls,
2. pause a normal agent turn for a native selectable user answer and resume with that answer as the tool result,
3. request at most a bounded, user-cancellable follow-up turn after completion audit without bypassing gates.

The final shape is:

```text
Jcode generic primitives
  before_model context transport
  native ask/options transport
  bounded turn_followup transport
        ↓
lazy-harness Jcode thin adapter
        ↓
canonical .lazy-harness lifecycle scripts and records
```

## Non-goals

- No lazy-harness-specific rule engine, record semantics, or trust policy inside Jcode.
- No project-local `.jcode/**` policy generation.
- No broad synchronous conversion of existing observer hooks.
- No automatic semantic classification of raw user text by deterministic hooks.
- No unbounded agent loop or implicit approval of code, database, release, payment, or other consequential actions.
- No Pi/OMP behavior change unless an independent compatibility defect is proven.

## Phase 0 — Contracts and fixtures before implementation

### Jcode contracts

Define generic protocol types and explicit limits before wiring behavior:

- `BeforeModelDecision`: no injection or one bounded system-reminder block.
- `AskRequest` / `AskOption` / `AskAnswer`: stable request id, 3–5 options, optional recommended id, optional custom answer, and cancellation.
- `TurnFollowupDecision`: stop or one bounded continuation body with reason and stable fingerprint.
- Hook timeouts, stdout byte limits, malformed-output behavior, fail-open/fail-closed rules, cancellation, and recursion suppression.
- Capability reporting so local TUI, remote client, headless run, and ACP do not claim unsupported interactive behavior.

### Lazy-harness contracts

Before adapter source changes, amend after execution approval:

- Jcode adapter SDD with `before-model`, `ask`, and `turn-followup` capability contracts.
- Jcode adapter TDD with native parity and negative cases.
- ADR 0056 only if the accepted architecture meaning changes beyond the already confirmed generic-thin-adapter direction.
- Existing planning pilot to point at this follow-on plan rather than pretending the old bounded pilot already owns Jcode-core changes.

### Phase 0 exit criteria

- Protocol names, limits, failure semantics, and ownership boundaries are reviewable without source mutation ambiguity.
- No implementation begins while any of the three contracts has an unresolved security or lifecycle choice.

## Phase 1 — Generic synchronous `before_model` context transport

### Required behavior

Run a bounded synchronous hook immediately before **every actual provider request** within an agent turn:

- initial request after user input,
- request after successful tool results,
- retry/replay request only when its semantics require a newly computed reminder.

The hook may return one JSON injection block. Jcode appends it only to the dynamic system-prompt portion for that provider request. It must not mutate static prompt cache content or persist the injected body as canonical project memory.

Before editing a single loop, inventory every provider-request path used by local TUI, server/remote, headless, retry, and replay execution. If more than one loop exists, extract or reuse one shared request-boundary helper and test each caller. Patching only `run_turn_streaming_mpsc` is insufficient unless source inspection proves it is the sole path.

### Likely Jcode changes

- `crates/jcode-config-types/src/lib.rs`
  - extend `HooksConfig` with `before_model` and a dedicated timeout.
- `crates/jcode-base/src/config/default_file.rs`, `config/env_overrides.rs`, `config_tests.rs`
  - document, parse, and test config/env behavior.
- `crates/jcode-base/src/hooks.rs`
  - add a synchronous bounded context-dispatch function separate from observer and `pre_tool` gate semantics.
  - parse strict JSON, cap output, fail open on timeout/spawn/malformed output, and preserve recursion suppression.
- `crates/jcode-app-core/src/agent/turn_streaming_mpsc.rs#run_turn_streaming_mpsc`
  - invoke the hook at the provider-request boundary inside the model/tool loop so post-tool calls are covered.
- `crates/jcode-app-core/src/agent/prompting.rs`
  - merge one request-scoped reminder into `SplitSystemPrompt.dynamic_part` without overwriting the existing `current_turn_system_reminder`.
- agent/core hook tests
  - initial injection, post-tool reinjection, no-hook, empty output, malformed JSON, timeout, oversized output, provider retry, cache-shape assertions, and coverage for every inventoried provider loop.

### Lazy-harness integration

- Extend `.lazy-harness/scripts/jcode-adapter.ts` with `beforeModel`.
- For the initial request, surface the canonical pre-response/search instruction without making the adapter a semantic classifier.
- For post-tool requests, call `.lazy-harness/hooks/lifecycle/on-context.sh` with bounded successful recent tool evidence so relevant records and operating guidance can be re-surfaced.
- Extend `.lazy-harness/scripts/jcode-package.ts` managed config, doctor, smoke, exact removal, and conflict detection for the new hook key.
- Retain exact trusted-root gating and silent untrusted/non-lazy no-op.

### Phase 1 acceptance

- A fresh trusted Jcode session proves the reminder is included in the provider prompt before the first model call.
- A file-touching tool result proves `on-context.sh` output is included before the next model call.
- Local, server/remote, and headless provider paths all prove they pass through the same semantic before-model boundary.
- Untrusted roots and hook failures produce no context and do not break normal Jcode operation.
- Prompt cache telemetry proves static prompt stability and bounded dynamic growth.

### Phase 1 rollback

- Remove/disable only the new `before_model` config key and adapter command.
- Existing six-hook adapter behavior remains valid and installed config is byte-preserved outside the exact managed line.

## Phase progress

### Phase 0/1 evidence — 2026-08-01

- Provider-loop inventory found three real provider-request surfaces: app-core non-MPSC, app-core MPSC/server/headless, and the local TUI test-harness loop. All now call the same bounded `before_model` semantics through shared helpers.
- Jcode commit: `38036ca63` (`feat(hooks): add synchronous before-model context`).
- Core contract: strict deny-unknown-fields JSON, 32 KiB stdout cap, 3 s default timeout, recursion suppression, fail-open failures, `initial`/`post_tool` request kind, and dynamic-only prompt mutation.
- Focused validation passed: 11 hook tests, 2 extracted hook-config tests, `cargo check` for `jcode-base`, `jcode-app-core`, and `jcode-tui`, plus `cargo fmt --all --check`.
- Fast guardrails no longer report growth from the Phase 1 target files. The repository-wide guardrail remains red only for unrelated concurrent dirty changes in desktop/provider/todo/TUI files, so no baseline ratchet update was applied.
- Lazy-harness adapter now has managed `before_model` configuration, trusted-root initial/post-tool dispatch, strict normalized injection, and focused fixture coverage. Live source-build validation remains before the Phase 1 parity claim can close.

### Phase 2 evidence — 2026-08-01

- Jcode commit `eaa12fc30` adds the generic native `ask` tool, session broker, server/client capability negotiation and correlation, local/remote picker, disconnect cancellation, continuation suppression, NDJSON `needs_input`, and ACP structured fallback.
- Jcode commit `6597ac650` closes contract gaps by enforcing at most one recommended option and bounded question, id, label, description, and custom-answer sizes.
- Focused validation passes for ask validation/broker resume, cross-session and duplicate response rejection, wire round-trip, picker selection/cancel/custom bounds, and affected app-core/protocol/tool/TUI crates.
- The full 2,135-test TUI suite was intentionally stopped after unrelated tests hung concurrently for more than 13 minutes; focused native-interaction tests and affected crate checks replaced that non-diagnostic run. No test result was falsely reported as a Phase 2 failure.
- Visible behavior is canonical in `.lazy-harness/behavior/jcode-native-ask.md`. Source-build local/remote picker and reconnect proof remains in Phase 4 before full parity is claimed.

### Phase 3 evidence — 2026-08-01

- Jcode commit `dcc8ed100` adds a separately named strict `turn_followup` hook and app-core-owned bounded controller across local TUI, remote server/client, and headless run-once paths.
- The controller enforces one synthetic continuation per originating real-user turn and suppresses continuation for open native ask, queued/new user input, cancellation, provider guardrail, deterministic non-retryable errors, malformed/oversized/failed/timed-out hook output, and repeated fingerprints.
- Focused validation passes for affected crate compilation, strict hook/config behavior, five app-core controller/cancellation tests, and protocol lifecycle round-trip. Fast guardrails report only pre-existing unrelated oversized/test/swallowed-error ratchet failures; Phase 3 target files are flat or below the limit.
- Lazy-harness adapter emits strict bounded continuation JSON only for exact trusted roots, clears per-turn evidence at decision time, prevents duplicate stop audits, and preserves one final audit for an issued synthetic response. The focused adapter fixture and `lazy check` pass.
- Visible behavior is canonical in `.lazy-harness/behavior/jcode-bounded-followup.md`. Source-build local/remote/headless live proof remains in Phase 4 before full parity is claimed.

## Phase 2 — Native interactive `ask` / option-gate tool

### Required behavior

A normal-session built-in tool pauses the current tool call until the user chooses an option, enters a custom answer, or cancels. The answer returns as the same tool call's structured result so the model resumes with explicit user-confirmed input.

Input contract:

- concise question,
- 3–5 stable option ids and labels,
- at most one recommended option,
- optional custom answer,
- optional explanatory detail bounded by protocol limits.

### Likely Jcode changes

- `crates/jcode-app-core/src/tool/ask.rs` and `tool/mod.rs`
  - register the generic normal-session `ask` tool.
- `jcode-tool-core` / `ToolContext`
  - add an interaction broker handle rather than coupling the tool to TUI code.
- `crates/jcode-protocol/src/wire.rs`
  - add server-to-client `user_input_request` and client-to-server answer/cancel messages with request/session ids.
- server client lifecycle/control modules
  - own pending request registration, answer routing, disconnect handling, duplicate/late answer rejection, and session isolation.
- session persistence types
  - persist pending question metadata or a resumable cancellation state so reconnect/reload cannot orphan a blocked tool call.
- Jcode TUI app state and a focused inline picker component
  - render options, recommended marker, custom entry, cancellation, keyboard/mouse handling, and reconnect restoration.
- remote client event handling
  - render the same picker and send the answer over the wire.
- headless `run` / NDJSON
  - emit a stable `needs_input` event and terminate or pause according to an explicit CLI capability contract; never hang on absent UI.
- ACP adapter
  - treat native interaction support as unresolved until verified against the actual ACP capability surface; use a standards-compatible request only if the connected client advertises and proves it, otherwise return structured `needs_input` without claiming interactivity.

### Existing code to reuse carefully

- Existing TUI picker primitives can supply rendering/navigation patterns.
- Ambient `request_permission` supplies queue/notification lessons but must not be reused as-is: it is ambient-only, asynchronous, action-approval oriented, and does not return a normal tool result in the same interactive turn.
- Existing server request ids and session routing should be reused for correlation.
- Command stdin is not an ask transport: it cannot provide typed request correlation, same-tool-call suspension/resumption, session isolation, reconnect semantics, or capability reporting.

### Safety invariants

- While an ask request is open, todo auto-poke and lifecycle followup are suppressed.
- Only the addressed session/client may answer.
- Recommended is visual metadata, never an automatic selection.
- Cancellation is a normal structured answer and must not be interpreted as approval.
- Disconnect, reload, timeout, duplicate answer, and stale request cannot silently select an option.

### Phase 2 acceptance

- Local TUI: option selection, custom answer, and cancel all resume the same tool call correctly.
- Remote TUI/server: request and answer remain session-isolated and survive supported reconnect/reload behavior.
- Headless/ACP: unsupported interaction exits or pauses explicitly with machine-readable `needs_input`, never hangs.
- Lazy-Harness option gate uses native choices and stops until the answer arrives.

### Phase 2 rollback

- Remove the tool from advertised definitions and retain protocol backward compatibility for clients that ignore unknown events.
- Plain Markdown option gates remain the safe fallback.

## Phase 3 — Bounded `turn_followup` controller

### Required behavior

After a turn has fully completed, a separate synchronous controller may request one synthetic follow-up message. This is not a converted observer hook and does not make existing `turn_end` blocking.

Decision contract:

```json
{
  "continue": {
    "body": "bounded system reminder",
    "reason": "record_capture_incomplete",
    "fingerprint": "stable-id"
  }
}
```

### Likely Jcode changes

- `HooksConfig`, config docs/env/tests, and `hooks.rs`
  - add a separately named `turn_followup` controller with strict JSON and timeout semantics.
- app-core/server completion path
  - own the followup decision and dispatch only after the current turn commits and all tool results are stable.
- TUI local/remote continuation machinery
  - present and enqueue an app-core/server-owned decision; reuse the existing synthetic-message/auto-poke queue only where safe, with a distinct lifecycle-followup source and status.
- session/runtime state
  - track followup count, fingerprint, cancellation, and the pending-ask exclusion outside TUI-only state so remote and headless behavior remains consistent.
- CLI/UI
  - expose cancel/status and render lifecycle followups as system-generated, not user-authored messages.

### Mandatory bounds

- default maximum: one lifecycle followup per originating user turn,
- repeated fingerprint: stop,
- unresolved native ask or requirements/execution approval gate: stop,
- user cancellation or new real user input: stop,
- auth, billing, guardrail, provider, or non-retryable error: stop,
- no automatic consequential mutation or confirmation on the user's behalf,
- no continuation when the controller output is malformed, late, oversized, or unavailable.

### Lazy-harness integration

- Add `turnFollowup` to `jcode-adapter.ts` and a managed config key.
- Invoke the canonical response-completed/lifecycle decision path in a mode that returns a bounded followup decision rather than relying on detached `turn_end` stdout.
- Keep `turn_end` observer for advisory telemetry if still useful; prevent duplicate audit execution or duplicate record prompts.
- Add stable fingerprinting for identical unresolved audit findings.

### Phase 3 acceptance

- One incomplete record-capture audit generates exactly one followup and then stops after completion.
- Identical repeated audit output cannot loop.
- Open option gates, new user input, cancellation, or non-retryable failures prevent continuation.
- Local, remote, and headless behavior is explicit and tested.

### Phase 3 rollback

- Disable/remove only `turn_followup`; retain observer audit and manual follow-up behavior.
- Existing todo auto-poke remains independent.

## Phase 4 — Cross-runtime integration and parity proof

### Static and focused validation

Jcode repository:

1. `cargo fmt --check` or repository formatting target.
2. targeted hook/config/agent/tool/protocol/TUI tests per phase.
3. `cargo check` for affected crates.
4. `scripts/check_guardrails.sh --skip-slow` during focused iteration.
5. full guardrails and source rebuild before claiming completion.

Lazy-harness repository:

1. `.lazy-harness/bin/lazy check` during edit loops.
2. focused Jcode adapter self-test fixture.
3. Pi/OMP package non-regression fixture.
4. `.lazy-harness/bin/lazy jcode doctor --format=json` and smoke.
5. one final `.lazy-harness/bin/lazy validate --plan standard` after the last mutation.

### Live capability matrix

| Capability | Trusted local Jcode | Remote Jcode | Headless/ACP | Untrusted root | Pi/OMP regression |
|---|---|---|---|---|---|
| initial context injection | required | required | explicit capability | silent no-op | unchanged |
| post-tool re-grounding | required | required | explicit capability | silent no-op | unchanged |
| native ask | picker/custom/cancel | picker/custom/cancel | `needs_input` or negotiated support | not adapter-dependent | unchanged |
| bounded followup | exactly bounded | exactly bounded | explicit behavior | silent no-op | unchanged |

### Completion definition

The three old gaps may be removed from `lazy jcode doctor` only after their corresponding live matrix rows pass. Partial implementation must report partial capability honestly.

## Cross-repository sequencing and commits

1. Jcode Phase 0/1 contract + implementation + focused tests, commit in Jcode.
2. Lazy-harness Phase 1 adapter integration + records/tests, commit in lazy-harness.
3. Jcode Phase 2 native ask + local/remote/headless tests, commit in Jcode.
4. Lazy-harness option-gate integration + records/tests, commit in lazy-harness.
5. Jcode Phase 3 bounded followup + tests, commit in Jcode.
6. Lazy-harness audit/followup integration + records/tests, commit in lazy-harness.
7. Rebuild/install Jcode current channel, run live matrix, then final validations and close records.

Do not mix all three primitives into one unreviewable commit. Existing unrelated dirty changes in either repository must not be staged or rewritten.

## Stop conditions

Stop and request a revised decision if any occurs:

- `before_model` requires exposing or persisting raw conversation/tool-result content to external hooks,
- duplicate provider loops cannot be brought behind one tested semantic request boundary without a broader architecture decision,
- native ask cannot preserve session identity or avoid hanging headless/remote clients,
- native ask would require command stdin as its primary transport,
- followup cannot be bounded independently from ordinary auto-poke,
- followup correctness would depend on TUI-only state,
- Jcode protocol compatibility requires a breaking migration without a backward-compatible path,
- lazy-harness integration requires canonical policy inside Jcode or project-local `.jcode` regeneration,
- Pi/OMP semantics must change without an independent defect,
- another agent's dirty work conflicts with a required file,
- a new user constraint makes this plan stale.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| prompt/cache instability | dynamic-only injection, byte/token caps, cache-shape tests |
| hook latency | separate short timeout, timing telemetry, fail-open context path |
| prompt injection from arbitrary hooks | explicit user configuration, strict JSON, bounded system-reminder format, no implicit trust expansion |
| native ask deadlock | broker timeouts/cancel, capability negotiation, headless `needs_input`, reconnect tests |
| false ACP parity claim | default to structured `needs_input`; promote to native interaction only after protocol and live-client evidence |
| cross-session answer leak | request id + session id ownership, duplicate/late answer rejection |
| continuation loop | max one, stable fingerprint, ask/gate suppression, user cancel and real-input precedence |
| duplicate provider loops | inventory all call paths first, centralize the semantic request boundary, and test every caller |
| TUI-owned followup state | place decision/bounds in app-core/server session state; keep TUI as presentation and queue transport |
| duplicate completion audit | separate observer/controller roles and one canonical decision execution per turn |
| adapter security regression | preserve exact trusted-root gate, secret-free state, and untrusted silent no-op fixtures |
| large cross-repo change | phase commits, per-phase rollback, focused tests before integration |

## Implementation map

- Status: approved; Jcode Phases 1–3 and matching lazy-harness adapter transports implemented, source-build live proof and final closure in progress.
- Jcode source candidates verified by source read:
  - `/home/lazydino/dev/jcode/crates/jcode-base/src/hooks.rs` — current observer/gate execution boundary; future bounded synchronous context/followup contracts.
  - `/home/lazydino/dev/jcode/crates/jcode-config-types/src/lib.rs` — `HooksConfig`.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/agent/turn_execution.rs` — turn start/end lifecycle dispatch and existing per-turn system reminder input.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/agent/turn_streaming_mpsc.rs#run_turn_streaming_mpsc` — provider/tool loop and required before-model insertion seam.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/agent/prompting.rs#append_current_turn_system_reminder` — dynamic reminder composition.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/tool/mod.rs` — built-in tool registry.
  - `/home/lazydino/dev/jcode/crates/jcode-protocol/src/wire.rs` — server/client protocol.
  - `/home/lazydino/dev/jcode/crates/jcode-tui/src/tui/app/commands.rs` — existing bounded auto-poke machinery.
- Lazy-harness source candidates:
  - `.lazy-harness/scripts/jcode-adapter.ts` — runtime translation and trusted-root gate.
  - `.lazy-harness/scripts/jcode-package.ts` — managed hooks, doctor, smoke, remove.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — initial pre-response static transport.
  - `.lazy-harness/hooks/lifecycle/on-context.sh` — post-tool re-grounding injection.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — current advisory audit path.
  - `.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter` — adapter regression fixture.
- Planned flow:
  1. Jcode exposes generic capabilities.
  2. Lazy-Harness adapter translates them only for exact trusted roots.
  3. Canonical lifecycle scripts produce bounded context/decision bodies.
  4. Live capability evidence promotes partial support to verified parity.
- Tests / protection:
  - Jcode crate-level config/hook/agent/tool/protocol/TUI tests.
  - `.lazy-harness/tests/jcode-agent-adapter.md` and focused self-test.
  - Pi/OMP non-regression fixture.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
  - SDD: `.lazy-harness/spec/platform/jcode-agent-adapter.md`
  - TDD: `.lazy-harness/tests/jcode-agent-adapter.md`
  - SSOT: `.lazy-harness/ssot/runtime-and-shared-state.md`, `.lazy-harness/ssot/harness-enforcement-policy.md`

## Rule placement

- Rule: close Jcode parity gaps through staged generic runtime primitives and a thin trusted-root adapter, with no canonical policy inside Jcode.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/jcode-native-lifecycle-parity-plan.md`.
- Why not AGENTS.md: this is an unresolved implementation rollout, not permanent per-turn grammar.
- Why not `.jcode`: the work spans Jcode core and framework architecture and must remain visible in canonical project records.
- Confirmation: direction A and this exact implementation plan user-approved on 2026-08-01.

## Discovery capture

- DDD: no independent delta.
- SDD: independent deltas approved for Jcode adapter and native hook/tool contracts; update them phase-by-phase with implementation evidence.
- BDD: independent delta only if native ask creates a user-visible interaction contract requiring a dedicated scenario record.
- TDD: independent regression expansion approved and required phase-by-phase.
- ADR: current ADR 0056 already owns generic thin-adapter direction; amend or add an ADR only if implementation discovers a new trade-off.
- SSOT: no current ownership/config delta beyond already user-owned Jcode configuration; runtime state boundaries remain in existing SSOT.
- Planning: this record is the primary durable output of the confirmed A direction.
