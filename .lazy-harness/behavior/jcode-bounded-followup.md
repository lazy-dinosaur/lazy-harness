# BDD — Jcode Bounded Turn Followup

Status: retired-history
Superseded by: `.lazy-harness/decisions/0059-pi-primary-jcode-decommission.md`
Date: 2026-08-01
Layer: BDD
Related ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
Related SDD: `.lazy-harness/spec/platform/jcode-agent-adapter.md`
Related TDD: `.lazy-harness/tests/jcode-agent-adapter.md`
Related planning: `.lazy-harness/planning/jcode-native-lifecycle-parity-plan.md`

## Rule digest

- Status: deprecated
- Layer: BDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - Jcode bounded followup
  - lifecycle continuation
  - system followup
  - Jcode 후속 실행
- Surface terms:
  - turn_followup followup fingerprint system-generated cancelled stopped
- Applies when:
  - a completed Jcode turn has one unresolved canonical lifecycle finding
  - local, remote, or headless Jcode presents or executes a system-generated continuation
- Must:
  - allow at most one synthetic continuation per originating real-user turn
  - present the continuation as system-generated and cancellable, never user-authored
  - stop for repeated fingerprints, open interactions, queued/new user input, cancellation, guardrails, or non-retryable errors
  - stop normally on missing, malformed, late, failed, timed-out, or oversized controller output
  - use shared app-core/server state so remote and headless bounds do not depend on TUI-only state
- Must not:
  - recursively grant a new allowance to the synthetic turn
  - confirm an option, approval, or consequential action on the user's behalf
  - claim full live parity before the local/remote/headless source-build matrix passes
- Record completion:
  - visible followup status, cancellation, or suppression behavior changes update this BDD, the adapter SDD, and TDD
- Related records:
  - `.lazy-harness/behavior/jcode-native-ask.md`
  - `.lazy-harness/decisions/0038-requirements-first-change-gate.md`

## Scenario 1 — One bounded local continuation

Given a local real-user turn has fully completed
And the trusted lifecycle controller returns one valid continuation
When Jcode claims the decision
Then it displays a system followup notice
And appends one bounded system-reminder message
And the synthetic turn receives no new followup allowance.

## Scenario 2 — Interaction and user input take precedence

Given a native ask is unresolved or new real user input is queued
When the turn followup controller would run
Then Jcode stops the continuation
And never treats recommended metadata, queued text, or cancellation as approval.

## Scenario 3 — Cancellation and guardrails stop execution

Given a followup is deciding or running
When the user cancels, a new message preempts it, a provider guardrail fires, or a deterministic non-retryable error occurs
Then Jcode stops only the synthetic followup
And reports cancelled or stopped lifecycle status without retrying it.

## Scenario 4 — Repeated or invalid decisions cannot loop

Given a followup fingerprint repeats or the controller output is missing, malformed, late, failed, timed out, or oversized
When Jcode evaluates the decision
Then no synthetic message is dispatched
And the originating turn terminates normally.

## Scenario 5 — Remote and headless behavior is explicit

Given a remote client or headless run-once path completes a real-user turn
When the shared app-core controller accepts a continuation
Then remote clients receive started/completed/cancelled/stopped lifecycle status
And headless execution returns the bounded followup output
And both paths use the same session-scoped bounds as local execution.

## Implementation map

- Status: Jcode core committed at `dcc8ed100`; focused static/controller/protocol tests pass; source-build live matrix pending.
- Jcode core:
  - `/home/lazydino/dev/jcode/crates/jcode-base/src/hooks/turn_followup.rs` — strict controller process, timeout, and byte bounds.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/turn_followup.rs` — shared origin, phase, fingerprint, cancellation, interaction, guardrail, and error state.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/agent/turn_followup.rs` — headless/server claim and execution flow.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/server/client_lifecycle_followup.rs` — new-input and cancel preemption.
  - `/home/lazydino/dev/jcode/crates/jcode-tui/src/tui/app/turn_followup.rs` — local system followup presentation.
  - `/home/lazydino/dev/jcode/crates/jcode-tui/src/tui/app/remote/turn_followup.rs` — remote lifecycle presentation.
- Lazy-harness adapter:
  - `.lazy-harness/scripts/jcode-adapter.ts` — trusted response-completed translation, stable fingerprint, evidence clearing, and duplicate-audit control.
  - `.lazy-harness/scripts/jcode-package.ts` — managed hook installation and honest doctor gap.
- Protection:
  - Jcode strict hook/config/controller/protocol focused tests.
  - `.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter`.
  - `.lazy-harness/tests/jcode-agent-adapter.md`.

## Layer completeness impact

- DDD: no independent delta.
- SDD: hook, controller, protocol, and adapter interfaces have an independent delta.
- BDD: this record owns visible system continuation, cancellation, and status behavior.
- TDD: bounded continuation regressions have an independent delta.
- ADR: ADR 0056 already owns generic Jcode primitives and thin adapter boundaries.
- SSOT: no ownership, schema, or runtime-root source-of-truth delta.
- Planning: rollout and live proof remain in the parity plan.

## Rule placement

- Rule: a completed Jcode turn may run one explicitly bounded system-generated continuation, subject to user input, interaction, cancellation, and failure precedence.
- Scope: framework-global
- Primary record: `.lazy-harness/behavior/jcode-bounded-followup.md`
- Why not AGENTS.md: this is runtime-specific visible lifecycle behavior, not universal per-turn grammar.
- Confirmation: direction A and exact staged plan user-approved on 2026-08-01.

## Discovery capture

- DDD: no independent delta.
- SDD: updated through the linked Jcode adapter contract.
- BDD: this record is the primary visible-flow record.
- TDD: updated through the linked adapter regression record.
- ADR: no new trade-off beyond ADR 0056.
- SSOT: no independent delta.
- Planning: Phase 3 evidence remains in the parity plan.
