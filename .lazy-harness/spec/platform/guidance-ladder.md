# SDD — Guidance Ladder and Hard-stop Promotion

Status: accepted
Date: 2026-06-01
Layer: SDD
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related SSOT: `.lazy-harness/ssot/rule-lifecycle.md`
Related SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`
Related SDD: `.lazy-harness/spec/platform/response-rule-audit.md`
Related TDD: `.lazy-harness/tests/guidance-ladder-hard-stop-promotion.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - deciding whether a stored lazy-harness rule should stay surfaced/audited or become a hard stop
  - adding, reviewing, or removing hard-stop behavior in framework lifecycle hooks
  - interpreting Phase 6 of the organic hybrid rule guidance plan
  - evaluating downstream host behavior when lazy-harness is used for project work
- Must:
  - keep normal guidance on the pre-response digest + response.completed audit path by default
  - require explicit promotion evidence before any concrete hard stop is introduced
  - require hard stops to be narrow, reversible, fixture-protected, and tied to a canonical record
  - keep generic destructive shell safety separate from project/team policy hard-stop promotion
  - keep clean/satisfied turns silent
- Must not:
  - reintroduce broad edit/write blocking as the default rule recall mechanism
  - encode project/team policy as bash, gh, dev-cli, or MCP-specific adapters without a promotion record
  - promote a hard stop only because a rule exists
- Record completion:
  - changes to guidance levels, promotion criteria, audit fields, or hard-stop fixtures update this SDD, `.lazy-harness/ssot/rule-lifecycle.md`, ADR 0041, and Phase 6 tests
- Related records:
  - `.lazy-harness/spec/platform/response-rule-audit.md`
  - `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
  - `.lazy-harness/tests/guidance-ladder-hard-stop-promotion.md`

## Purpose

Phase 6 defines the guidance ladder for lazy-harness rule recall.

The framework should help agents use durable records while working in host projects, but it should not jump from "record exists" to "tool hard-blocks action". Most rules should be surfaced before the response and audited after the response. A hard stop is the last rung.

## Guidance ladder

| Level | Name | Meaning | Default? |
|---|---|---|---|
| L0 | `captured` | Rule exists in canonical `.lazy-harness` record. | yes |
| L1 | `digest-ready` | Rule has compact `## Rule digest` and can be retrieved. | yes |
| L2 | `surfaced` | Rule appears in `message.received` pre-response context when relevant. | yes |
| L3 | `audited` | `response.completed` can detect strong missed-rule or missing-record evidence. | yes |
| L4 | `warn-escalated` | Repeated or high-risk misses produce stronger response audit guidance. | case-by-case |
| L5 | `hard-stop-promoted` | A narrow blocking boundary exists and is justified by promotion evidence. | rare |

Phase 7 Context Delivery required-read audit is an L3 advisory-only path. It may print `ADVISORY` when a correlated packet journal row, mutation evidence, and missing read/search evidence align. It is not L4 escalation and cannot become L5 without dogfood miss/risk evidence plus the promotion record below.

2026-06-01 update: Context Delivery read-debt has one active L5 boundary in `.lazy-harness/spec/platform/context-delivery-contract.md`. It is not broad edit/write blocking. It blocks only action tools for a correlated packet with concrete `requiredRead` paths and sufficient confidence, while read/search tools remain allowed.

## Hard-stop promotion criteria

A concrete hard stop may be introduced only when every criterion is documented:

1. **User-confirmed mandatory boundary**
   - The boundary is not inferred by the framework alone.
2. **Miss/risk evidence**
   - Repeated dogfood miss, high-cost miss, irreversible action, or security/data-loss risk.
3. **Existing softer coverage**
   - Relevant digest/audit coverage exists or the record explains why it cannot be sufficient.
4. **Fixture exists**
   - A self-test or fixture proves both block and allow cases.
5. **Narrow scope**
   - The boundary is as small as possible and avoids tool adapter sprawl.
6. **Rollback path**
   - The record explains how to disable, downgrade, or retire the hard stop.
7. **Canonical ownership**
   - The promotion is recorded in `.lazy-harness/{spec,ssot,decisions,tests}/**`, not `.jcode` or memory alone.

## Promotion record section

A promoted hard stop must include a `## Hard-stop promotion` section in its canonical owner record.

Required fields:

```md
## Hard-stop promotion

- Status: active | proposed | retired
- Boundary: <exact boundary being blocked>
- Scope: framework-global | host-project | team-policy
- User confirmation: <who/when/what was confirmed>
- Evidence: <repeated miss, high-cost risk, irreversible action, or security/data-loss risk>
- Existing softer coverage: <digest/audit coverage or why it is insufficient>
- Fixture: <path to self-test/fixture proving block and allow cases>
- Narrowness: <why this does not become broad tool-specific policy>
- Rollback: <how to disable/downgrade/remove>
```

The fixture path must exist. Retired promotions should keep enough history to explain why they were removed.

## Audit command

`.lazy-harness/scripts/hard-stop-promotion-audit.py` scans hard-stop promotion sections and reports missing promotion evidence.

Usage:

```bash
python3 .lazy-harness/scripts/hard-stop-promotion-audit.py --root . --format md
python3 .lazy-harness/scripts/hard-stop-promotion-audit.py --root . --format json --strict
```

`--strict` exits nonzero when active/proposed promotion sections are invalid.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/guidance-ladder.md` — this SDD contract.
  - `.lazy-harness/scripts/hard-stop-promotion-audit.py` — promotion section scanner/checker.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — L3 digest/packet advisory audit helper.
  - `.lazy-harness/scripts/self-test.py` — Phase 6 fixtures and source scan.
  - `.lazy-harness/tests/guidance-ladder-hard-stop-promotion.md` — TDD record.
  - `.lazy-harness/ssot/rule-lifecycle.md` — SSOT lifecycle and promotion policy.
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` — architecture decision and Phase 6 note.
- Key symbols:
  - `extract_sections` (`hard-stop-promotion-audit.py`) — finds `## Hard-stop promotion` sections outside code fences.
  - `validate_section` (`hard-stop-promotion-audit.py`) — checks required fields and fixture path existence.
  - `packet_required_paths` (`check-response-rule-audit.py`) — Phase 7 advisory-only required-read evidence extraction.
  - `check_guidance_ladder_hard_stop_promotion` (`self-test.py`) — protects valid/invalid fixture behavior and source scan.
- Flow:
  1. A rule stays on L0-L3 by default.
  2. A repeated/high-cost/irreversible miss is observed.
  3. A canonical owner record adds `## Hard-stop promotion` with required evidence.
  4. Fixture proves block and allow cases.
  5. Audit script validates the promotion metadata.
  6. Only then should implementation add a narrow hard stop.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_guidance_ladder_hard_stop_promotion`
  - `.lazy-harness/scripts/self-test.py#check_context_delivery_packet_journal_phase7`
  - `python3 .lazy-harness/scripts/hard-stop-promotion-audit.py --strict`
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - SSOT: `.lazy-harness/ssot/rule-lifecycle.md`
  - TDD: `.lazy-harness/tests/guidance-ladder-hard-stop-promotion.md`
- Machine index:
  - graph ids: `kg_phase6_guidance_ladder_sdd`, `kg_phase6_hard_stop_promotion_audit_impl`, `kg_phase6_guidance_ladder_self_test`

## Rule placement

- Rule: hard stops are the last rung of the lazy-harness guidance ladder and require explicit promotion evidence before implementation.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/guidance-ladder.md`
- Why not AGENTS.md: this is platform lifecycle policy, not base agent grammar.
- Why not `.jcode`: this must sync as shared framework behavior, not local/private Jcode wiring.
- Confirmation: user approved continuing Phase 6 according to the existing plan on 2026-06-01.

## Discovery capture

- DDD: none.
- SDD: updated, this file defines the guidance ladder and promotion record contract.
- BDD: none for app UI; agent-visible behavior is default surfaced/audited guidance and rare hard stops.
- TDD: `.lazy-harness/tests/guidance-ladder-hard-stop-promotion.md` added.
- ADR: ADR 0041 updated with Phase 6 note.
- SSOT: `.lazy-harness/ssot/rule-lifecycle.md` and `.lazy-harness/ssot/harness-enforcement-policy.md` updated.
- Planning: `.lazy-harness/planning/record-query-context-loop-transition-plan.md` updated after validation.
