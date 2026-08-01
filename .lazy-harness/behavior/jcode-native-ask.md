# BDD — Jcode Native Ask Interaction

Status: active-phase2
Date: 2026-08-01
Layer: BDD
Related ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
Related SDD: `.lazy-harness/spec/platform/jcode-agent-adapter.md`
Related TDD: `.lazy-harness/tests/jcode-agent-adapter.md`
Related planning: `.lazy-harness/planning/jcode-native-lifecycle-parity-plan.md`

## Rule digest

- Status: active
- Layer: BDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - Jcode native ask
  - selectable option gate
  - native interaction picker
  - Jcode 입력 요청
- Surface terms:
  - ask interaction_request interaction_answer interaction_cancel needs_input
- Applies when:
  - an agent needs one focused 3–5 option decision during a normal Jcode tool call
  - rendering or routing a lazy-harness option gate through Jcode
- Must:
  - show 3–5 stable options, at most one recommended marker, and optional custom input
  - pause the same tool call until a supported client selects, custom-answers, or cancels
  - return a typed answer and keep recommended as visual metadata only
  - suppress queued followups and auto-poke while the picker is open
  - return structured `needs_input` immediately when the runtime cannot interact
- Must not:
  - use command stdin as the interaction transport
  - auto-select the recommended option
  - hang headless or unsupported ACP clients
  - accept cross-session, duplicate, late, empty, oversized, or unknown-option answers
- Record completion:
  - visible picker/protocol/headless behavior changes update this BDD, Jcode adapter SDD, and TDD
- Related records:
  - `.lazy-harness/decisions/0019-ambiguous-detection-force-gate.md`
  - `.lazy-harness/decisions/0038-requirements-first-change-gate.md`
  - `.lazy-harness/spec/platform/option-gate-discipline.md`

## Scenario 1 — Local selectable option gate

Given a local Jcode TUI supports native interactions
And the agent calls `ask` with 3–5 valid options
When Jcode opens the interaction picker
Then arrow keys select an option
And Enter returns the selected stable option id to the same tool call
And the recommended marker never selects itself.

## Scenario 2 — Custom answer or cancellation

Given the ask call allows custom input
When the user enters custom mode and submits bounded non-empty text
Then the same tool call resumes with a typed custom answer.

When the user presses Escape
Then the same tool call resumes with `cancelled`
And cancellation is never interpreted as approval.

## Scenario 3 — Remote session isolation

Given a remote client advertised `native_interactions = true`
When the server emits an `interaction_request`
Then request id, session id, and tool-call id correlate the answer
And another session cannot answer it
And duplicate or late answers are rejected.

## Scenario 4 — Disconnect cannot orphan the tool

Given an interaction is pending
When the addressed client disconnects or its broker is replaced
Then Jcode sends a typed cancellation to the waiting tool call
And clears pending request ownership.

## Scenario 5 — Unsupported runtime returns needs-input

Given headless NDJSON or ACP has no proven native interaction capability
When the agent calls `ask`
Then Jcode does not wait for stdin
And returns/emits structured `needs_input` with the complete bounded request
And the caller can resume later through an explicit supported path.

## Scenario 6 — Continuation suppression

Given a native ask picker is open
When turn-end auto-poke, queued followup, or remote followup processing runs
Then no synthetic followup is dispatched
And normal continuation can resume only after the interaction closes.

## Implementation map

- Status: Jcode core committed at `eaa12fc30`; bounds hardening committed at `6597ac650`; source-build live picker proof pending.
- Jcode core:
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/tool/ask.rs` — validation, typed tool result, unsupported `needs_input` fallback.
  - `/home/lazydino/dev/jcode/crates/jcode-tool-core/src/lib.rs` — session interaction broker and open-state tracking.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/server/client_interactions.rs` — session-isolated answer/cancel routing.
  - `/home/lazydino/dev/jcode/crates/jcode-protocol/src/wire.rs` — capability, request, answer, and cancel wire types.
  - `/home/lazydino/dev/jcode/crates/jcode-tui/src/tui/interaction_picker.rs` — local/remote option and custom-input UI.
  - `/home/lazydino/dev/jcode/src/cli/commands.rs` — NDJSON `needs_input` event.
  - `/home/lazydino/dev/jcode/src/cli/acp.rs` — ACP structured raw output fallback.
- Protection:
  - Jcode ask, server interaction, protocol round-trip, picker, NDJSON, and ACP focused tests.
  - `.lazy-harness/tests/jcode-agent-adapter.md`.

## Layer completeness impact

- DDD: no independent delta.
- SDD: native tool, broker, protocol, and fallback interfaces have an independent delta.
- BDD: this record owns the visible picker/answer/cancel/needs-input flow.
- TDD: native interaction regressions have an independent delta.
- ADR: ADR 0056 already owns generic Jcode primitives and thin adapter boundaries.
- SSOT: no ownership/config source-of-truth delta.
- Planning: rollout and live proof remain in the parity plan.

## Rule placement

- Rule: Jcode option gates use a typed native picker when supported and structured `needs_input` otherwise.
- Scope: framework-global
- Primary record: `.lazy-harness/behavior/jcode-native-ask.md`
- Why not AGENTS.md: this is runtime-specific visible interaction behavior, not universal retrieval grammar.
- Confirmation: direction A and exact staged plan user-approved on 2026-08-01.

## Discovery capture

- DDD: no independent delta.
- SDD: updated through the linked Jcode adapter contract.
- BDD: this record is the primary visible-flow record.
- TDD: updated through the linked Jcode adapter regression record.
- ADR: no new trade-off beyond ADR 0056.
- SSOT: no independent delta.
- Planning: Phase 2 evidence remains in the parity plan.
