# Rule Lifecycle and Binding

Status: accepted-with-phase5-supersession
Layer: SSOT
Date: 2026-05-26
Updated: 2026-06-01
Related SDD: `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
Related ADR: `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md`
Replacement ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Replacement SDD: `.lazy-harness/spec/platform/response-rule-audit.md`
Related TDD: `.lazy-harness/tests/rule-binding-pr-body-guard.md`

## Rule digest

- Status: active
- Layer: SSOT
- Scope: framework-global
- Applies when:
  - deciding how durable rules become future agent behavior
  - migrating tool-attached project policy to organic response lifecycle
  - interpreting rule lifecycle state after ADR 0041
- Must:
  - keep durable record capture mandatory for confirmed rules/corrections/contracts/decisions/regressions
  - treat non-record action guidance as surfaced/audited through response lifecycle by default
  - keep concrete tool hooks limited to generic transport, telemetry, destructive safety, and packet-scoped read-debt permits
  - require explicit Phase 6 promotion criteria before adding a new hard stop
- Must not:
  - leave enduring rules as unqueryable chat memory
  - encode project/team policy as bash, gh, dev-cli, or MCP-specific adapters by default
- Record completion:
  - changes to rule lifecycle state names, binding policy, or hard-stop promotion update this SSOT and linked ADR/SDD/TDD records
- Related records:
  - `.lazy-harness/ssot/harness-enforcement-policy.md`
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - `.lazy-harness/spec/platform/response-rule-audit.md`

## Purpose

A lazy-harness rule is not fully useful just because it is written in a record. Durable rule capture has two responsibilities:

1. Store the human-readable rule in the correct `.lazy-harness` layer.
2. Make it retrievable and auditable when the agent later needs it.

Before Phase 5, this SSOT used rule-binding hard stops as the main answer to action-time recall drift. Phase 5 keeps the recall problem but changes the default mechanism.

## Current lifecycle states

| State | Meaning |
|---|---|
| `captured` | Rule exists in a canonical record but has no digest/query/audit coverage yet. |
| `digest-ready` | Rule has a compact `## Rule digest` and can be surfaced by relevant-record query. |
| `surfaced` | Rule is expected to appear before relevant turns through `message.received` digest injection. |
| `audited` | `response.completed` can detect strong missed-rule or record-completion evidence, emit advisory-only Context Delivery required-read evidence checks, or journal silent Record Decision Packet shadow observations after fixtures. |
| `hard-stop-promoted` | A narrow blocking hook exists because Phase 6 criteria were met. Context Delivery read-debt permit is the active framework-global example. |
| `advisory-only` | Rule is intentionally not enforced/audited beyond guidance; this must be explicit. |
| `retired` | Rule is obsolete and should not be applied. |

Legacy states `bound` and `enforced` may still appear in old records. After Phase 5, they do not imply concrete tool-specific hard blocks unless a newer Phase 6 record explicitly promotes the boundary.

## Binding metadata after Phase 5

Old machine-readable bindings such as `.lazy-harness/ssot/rule-bindings.json` are historical/compatibility metadata. They are not the preferred way to add project/team policy.

Preferred metadata lives in:

- `## Rule digest` sections in the canonical record,
- related implementation map / graph facts,
- response-rule-audit fixtures when a miss pattern has strong evidence,
- packet evidence journal fixtures when Context Delivery required-read usage needs advisory dogfood observation,
- Record Decision Packet fixtures before broader post-turn record guidance,
- explicit Record Decision generator and shadow fixtures before broader `response.completed` advisory integration,
- explicit Context Broker dogfood collector rows before any stronger `response.completed` advisory/escalation integration,
- automatic `response.completed` shadow rows are ambient evidence; aggregate Medivance/PWA dogfood still requires explicit `lazy context-dogfood` execution,
- Phase 6 hard-stop promotion records only for rare high-risk boundaries.

## PR body rule after Phase 5

If a host contains `.lazy-harness/ssot/pr-description-format.md`, lazy-harness should not default to `gh pr create/edit` hard blocking.

Instead:

1. the PR description record should expose a compact digest,
2. `message.received` should surface it for PR-writing intent,
3. `response.completed` should audit PR artifact evidence for missing required headings,
4. successful turns should stay silent.

## Hard-stop promotion policy

A concrete tool/action hard stop may be added only after Phase 6 criteria are recorded:

- user-confirmed mandatory boundary,
- repeated dogfood miss or high-cost/irreversible risk,
- fixture exists,
- record explains why ambient/surfaced/audited guidance was insufficient,
- scope is narrow and rollback is clear.

Generic destructive shell safety is already allowed and is not considered project/team policy. Context Delivery read-debt permit is allowed only because the canonical Context Delivery SDD contains an active `## Hard-stop promotion` section and fixtures; it is packet-scoped and does not authorize broad edit/write blocking.

Phase 6 implementation lives in `.lazy-harness/spec/platform/guidance-ladder.md` and is validated by `.lazy-harness/scripts/hard-stop-promotion-audit.py`. A promoted hard stop must include a canonical `## Hard-stop promotion` section with the required fields from that SDD before implementation.

## Implementation map

- Status: `phase5-organic-lifecycle`
- Primary files:
  - `.lazy-harness/ssot/rule-lifecycle.md` — this SSOT.
  - `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md` — historical/superseded binding ADR.
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` — active architecture.
  - `.lazy-harness/spec/platform/rule-binding-action-boundary.md` — superseded compatibility SDD.
  - `.lazy-harness/spec/platform/guidance-ladder.md` — Phase 6 guidance ladder and hard-stop promotion criteria.
  - `.lazy-harness/spec/platform/response-rule-audit.md` — active response audit SDD.
  - `.lazy-harness/spec/platform/record-decision-broker.md` — Phase 8 post-turn record decision contract.
  - `.lazy-harness/spec/platform/context-broker-dogfood.md` — explicit dogfood collection contract before lifecycle integration.
  - `.lazy-harness/scripts/record-decision-broker.ts` — explicit post-turn Record Decision Packet generator.
  - `.lazy-harness/scripts/context-broker-dogfood.ts` — explicit Native Context Broker dogfood collector.
  - `.lazy-harness/scripts/context-delivery.ts` — deterministic packet producer and sanitized packet evidence collection for read-debt/audit.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — packet-scoped pre-action read-debt permit helper.
  - `.lazy-harness/scripts/hard-stop-promotion-audit.py` — promotion metadata audit command.
  - `.lazy-harness/hooks/lifecycle/helpers/check-rule-action-boundary.py` — no-op compatibility shim.
  - `.lazy-harness/scripts/jcode-wiring.ts` — generated bash safety-only hook.
  - `.lazy-harness/scripts/self-test.py` — Phase 5 regression coverage.
- Key symbols:
  - `checkBashHook` (`jcode-wiring.ts`) — destructive shell safety only.
  - `check_rule_action_boundary_legacy_no_project_policy` (`self-test.py`) — protects no project-policy block in legacy helper.
  - `check_response_rule_audit_from_surfaced_digest` (`self-test.py`) — protects PR miss replacement audit.
  - `check_context_delivery_packet_journal_phase7` (`self-test.py`) — protects advisory-only packet required-read evidence audit.
  - `check_record_decision_broker_phase8` (`self-test.py`) — protects post-turn record decision packet contract before runtime escalation.
  - `check_context_broker_dogfood_collector` (`self-test.py`) — protects sanitized dogfood collection before lifecycle integration.
  - `check_guidance_ladder_hard_stop_promotion` (`self-test.py`) — protects Phase 6 promotion criteria.
- Flow:
  1. Confirmed rule/correction/contract is recorded in canonical layer.
  2. Reusable guidance gets a `## Rule digest`.
  3. Relevant query surfaces the digest before future turns.
  4. Response audit catches strong missed-rule or missing-record evidence.
  5. Only Phase 6 evidence can promote a concrete hard stop.
- Protection:
  - `.lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy test`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Machine index:
  - graph ids: `kg_phase5_rule_lifecycle_organic_model`, `kg_phase5_rule_lifecycle_ssot`

## Rule placement

- Rule: durable rules should become queryable/auditable through the organic response lifecycle by default; concrete tool hard stops require explicit Phase 6 promotion.
- Scope: framework-global
- Primary record: `.lazy-harness/ssot/rule-lifecycle.md`
- Why not AGENTS.md: this is lifecycle/source-of-truth policy, not full runtime grammar.
- Why not `.jcode`: this is shared framework behavior.
- Confirmation: user approved Phase 5 on 2026-06-01.

## Discovery capture

- DDD: no domain vocabulary change.
- SDD: rule-binding action-boundary SDD superseded.
- BDD: no app UI behavior change.
- TDD: Phase 5 tests updated.
- ADR: ADR 0039 superseded by ADR 0041 for enforcement architecture.
- SSOT: this record updated.
