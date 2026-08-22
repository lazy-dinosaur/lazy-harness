# ADR 0058 — Jcode Typed Review Model Routing

Status: retired
Superseded by: `.lazy-harness/decisions/0059-pi-primary-jcode-decommission.md`
Date: 2026-08-03
Layer: ADR

## Rule digest

- Status: deprecated
- Layer: ADR
- Scope: framework-global
- Confidence: high
- Aliases:
  - Jcode 리뷰 모델
  - reviewer high
  - oracle max
  - GPT-5.5 리뷰 금지
- Surface terms:
  - `[reviewer]`
  - `[oracle]`
  - GPT-5.6 Sol
  - swarm review routing
- Applies when:
  - delegating an independent code review or escalating a high-risk verification in Jcode
  - selecting a model or reasoning effort for a reviewer or Oracle swarm worker
- Must:
  - route `[reviewer]` to GPT-5.6 Sol with `high` effort
  - route `[oracle]` to GPT-5.6 Sol with `max` effort
  - use Oracle selectively for the hardest quality-first verification
- Must not:
  - route typed review work to GPT-5.5
  - run Oracle for every routine review
- Record completion:
  - review-route, effort, or escalation changes update this ADR and the Jcode adapter SDD/TDD
- Related records:
  - `.lazy-harness/decisions/0012-oracle-sisyphus-audit-cascade.md`
  - `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
  - `.lazy-harness/spec/platform/jcode-agent-adapter.md`
  - `.lazy-harness/tests/jcode-agent-adapter.md`

## Context

The global Jcode defaults already selected GPT-5.6 Sol, but a coordinator explicitly spawned a review worker with `model: "gpt-5.5"`. The runtime therefore obeyed the stale per-call override and bypassed the intended newer-model routing.

The user selected GPT-5.6 Sol for all GPT review work, then confirmed `high` for the normal reviewer and `max` for Oracle escalation. Current OpenAI guidance supports `high` for difficult agentic coding, names code review as an `xhigh` candidate when measured gains justify it, and reserves `max` for the hardest quality-first workloads rather than a global default.

## Decision

1. The normal independent review role uses a structured `[reviewer]` label, `model=gpt-5.6-sol`, and `effort=high`.
2. Oracle uses a structured `[oracle]` label, `model=gpt-5.6-sol`, and `effort=max`.
3. Oracle is an escalation route for DB, concurrency, payments, deployment, security, P1/P2 findings, unresolved reviewer uncertainty, or conflicting evidence.
4. Routine flow is coordinator/implementer → fresh read-only reviewer → correction → fresh reviewer verification. Oracle is added only when escalation criteria apply.
5. A pre-tool structural guard rejects typed labels with any other model/effort. Untyped swarm tasks remain unaffected.
6. Runtime-local Jcode prompt files mirror this policy and point back to this canonical ADR; they are not the source of truth.

## Consequences

- Review workers can no longer silently downgrade to GPT-5.5 when the typed label convention is used.
- Routine reviews retain a bounded high-effort cost profile.
- Oracle spends maximum reasoning only where marginal correctness materially matters.
- Coordinators must use the exact typed label prefixes for enforcement to apply.

## Hard-stop promotion

- Status: retired
- Boundary: Jcode `swarm` spawn calls whose structured label begins exactly `[reviewer]` or `[oracle]`
- Scope: framework-global
- User confirmation: user approved GPT-5.6 Sol reviewer high and Oracle max on 2026-08-03
- Evidence: a live coordinator explicitly spawned a GPT-5.5 reviewer despite GPT-5.6 global defaults and prior prompt guidance
- Existing softer coverage: global default/swarm model and prompt guidance already selected GPT-5.6, but explicit per-call override bypassed both
- Fixture: `.lazy-harness/tests/jcode-agent-adapter.md`
- Narrowness: inspect only tool name, spawn action, exact label prefix, model, and effort; never inspect user text or task prose
- Rollback: remove the helper from the pre-tool chain, demote the policy to recommend, and retain prompt-only routing
- Superseded by: `.lazy-harness/spec/platform/jcode-typed-review-routing.md` now owns the portable executable hard-stop contract and fixture; this ADR retains the route/effort trade-off decision history.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-agent-model-routing.py` — structural typed-route guard.
  - `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` — invokes the guard before tool execution.
  - `~/.jcode/swarm-prompt.md` — machine-local routing mirror and label convention.
  - `~/.jcode/prompt-overlay.md` — machine-local role guidance mirror.
- Key symbols:
  - `main` (`check-agent-model-routing.py`) — validates structured swarm spawn model and effort.
  - `normalized_model` (`check-agent-model-routing.py`) — accepts bare and route-qualified GPT-5.6 Sol identifiers.
- Flow:
  1. Coordinator selects a typed reviewer or Oracle role.
  2. Jcode pre-tool payload carries structured swarm spawn arguments.
  3. The guard permits only the approved model/effort pair for that prefix.
  4. The worker runs read-only review and reports evidence to the coordinator.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter` — rejects GPT-5.5/wrong effort and permits approved routes.
  - `.lazy-harness/tests/jcode-agent-adapter.md` — regression contract.
- Ownership boundaries:
  - Canonical decision rationale: this ADR.
  - Portable executable policy contract: `.lazy-harness/spec/platform/jcode-typed-review-routing.md` plus typed policy/capability registries.
  - Machine-local files may mirror routing but must not become an independent policy authority.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/jcode-agent-adapter.md`
  - SDD: `.lazy-harness/spec/platform/jcode-typed-review-routing.md`
  - TDD: `.lazy-harness/tests/jcode-agent-adapter.md`
  - TDD: `.lazy-harness/tests/jcode-typed-review-routing.md`
  - ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
- Machine index:
  - graph ids: `kg_jcode_typed_review_routing_guard_20260803`, `kg_jcode_typed_review_routing_test_20260803`

## Rule placement

- Rule: typed Jcode reviewer and Oracle roles have fixed GPT-5.6 Sol effort routes.
- Scope: framework-global.
- Primary record: `.lazy-harness/decisions/0058-jcode-typed-review-model-routing.md`.
- Why not AGENTS.md: the detailed model trade-off and escalation rationale belong in an ADR.
- Why not local notes: Jcode prompt files are runtime mirrors only; canonical policy remains in `.lazy-harness`.
- Confirmation: user-confirmed on 2026-08-03.

## Discovery capture

- DDD: no independent delta.
- SDD: Jcode pre-tool contract gains a typed review-routing guard.
- BDD: no product-visible flow.
- TDD: Jcode adapter regression gains allow/deny cases.
- ADR: this record owns the routing and effort trade-off.
- SSOT: typed operating policy and capability bindings are added to the canonical registries.
- Planning: existing orchestration references remain supporting material; no separate rollout plan is required.
