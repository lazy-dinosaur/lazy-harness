# SDD — Jcode Typed Review Routing

Status: deprecated-history
Superseded by: `.lazy-harness/decisions/0059-pi-primary-jcode-decommission.md`
Date: 2026-08-04
Layer: SDD
Related TDD: `.lazy-harness/tests/jcode-typed-review-routing.md`

## Rule digest

- Status: deprecated
- Layer: SDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - typed Jcode reviewer routing
  - reviewer high Oracle max
  - GPT-5.6 Sol review route
- Surface terms:
  - jcode-typed-review-model-routing
  - check-agent-model-routing.py
  - `[reviewer]`
  - `[oracle]`
- Applies when:
  - spawning a typed Jcode reviewer or Oracle worker
  - validating model/effort routing for high-risk review roles
- Must:
  - route `[reviewer]` to GPT-5.6 Sol with high effort
  - route `[oracle]` to GPT-5.6 Sol with max effort
  - reject GPT-5.5 and wrong efforts for typed review roles
  - inspect structured spawn arguments only
  - load route model/effort/label configuration only from an active `level=block`, `runtime.mode=typed-agent-routing` policy
  - stop blocking immediately when that policy is demoted, retired, or disabled
  - remain silent for untyped non-review labels
- Must not:
  - classify user prose or ordinary implementation roles as typed review routes
  - silently downgrade a typed reviewer or Oracle
- Record completion:
  - routing model, effort, label, bypass, or helper changes update this SDD and TDD
- Related records:
  - `.lazy-harness/tests/jcode-typed-review-routing.md`

## Contract

The shared pre-tool chain invokes `check-agent-model-routing.py` for structured swarm/agent spawn calls. The helper loads exact label/model/effort routes from the host policy registry and validates them before the runtime creates the worker. It is silent unless the policy remains `level=block` with `runtime.mode=typed-agent-routing` and `runtime.blocks=true`.

| Label prefix | Model | Effort |
|---|---|---|
| `[reviewer]` | GPT-5.6 Sol | `high` |
| `[oracle]` | GPT-5.6 Sol | `max` |

The policy is framework-global and may be seed-merged into trusted lazy-harness hosts. This SDD and its TDD are portable policy dependencies; project/team policy remains host-owned.

## Hard-stop promotion

- Status: active
- Boundary: block structured typed reviewer or Oracle spawns whose model or effort differs from the approved GPT-5.6 Sol route.
- Scope: framework-global
- User confirmation: user confirmed GPT-5.6 Sol high for reviewer and GPT-5.6 Sol max for Oracle on 2026-08-03.
- Evidence: prior orchestration selected GPT-5.5 despite GPT-5.6 Sol availability; focused routing fixtures and live spawn evidence established the correct route.
- Existing softer coverage: personal/global routing prompts documented the preference but did not prevent an explicitly wrong typed spawn request.
- Fixture: .lazy-harness/tests/jcode-typed-review-routing.md
- Narrowness: only structured spawn payloads with exact `[reviewer]` or `[oracle]` label prefixes are inspected; user text and untyped roles are out of scope.
- Rollback: demote/retire `jcode-typed-review-model-routing`, set `runtime.blocks=false`, remove it from the shared pre-tool chain, or adopt a later user-confirmed typed route. The helper reads policy state on each invocation.

## Implementation map

- Status: `implemented-policy-driven`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-agent-model-routing.py`
  - `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh`
  - `.lazy-harness/ssot/policies.json#jcode-typed-review-model-routing`
  - `.lazy-harness/ssot/capabilities.json#jcode-typed-review-model-routing`
- Protection:
  - `.lazy-harness/tests/jcode-typed-review-routing.md`
  - `.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter`
- Machine index:
  - graph ids: `kg_jcode_typed_review_routing_guard_20260803`, `kg_jcode_typed_review_routing_test_20260803`

## Rule placement

- Rule: typed review roles use exact GPT-5.6 Sol effort routes and reject explicit downgrades.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/jcode-typed-review-routing.md`
- Why not runtime prompt only: prompts are advisory; this is a structured spawn contract with a promoted block boundary.
- Confirmation: user-confirmed 2026-08-03.

## Discovery capture

- DDD: no independent delta.
- SDD: this portable contract owns typed spawn routing semantics.
- BDD: no product UI flow.
- TDD: `.lazy-harness/tests/jcode-typed-review-routing.md`.
- ADR: architectural decision remains in source history; no host ADR duplication is required.
- SSOT: typed policy/capability registries bind the contract.
- Planning: no deferred backlog in this portability repair.
