# TDD — Response Rule Audit

Status: accepted
Layer: TDD
Date: 2026-06-01
Related SDD: `.lazy-harness/spec/platform/response-rule-audit.md`
Related SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`

## Protected behavior

Phase 4 must connect surfaced pre-response records to post-response audit without turning successful turns into noise.

Regression fixtures cover:

1. `message.received` writes sanitized journal state after surfacing a digest.
2. The journal stores record paths/titles/bullets/hash metadata, but not raw user message text.
3. If a PR description rule was surfaced and a PR artifact is created without `Why:`, `What:`, and `Task:` headings, `response.completed` emits a concise audit message.
4. If the PR artifact contains the required headings, audit stays silent.
5. If a surfaced record has record-completion obligations and the turn changes harness/source behavior without durable `.lazy-harness` capture, audit emits a concise record-completion message.
6. If same-turn durable record capture is visible, audit stays silent.
7. `lazy context-delivery --journal` writes sanitized packet evidence without raw user messages or raw record bullets.
8. Packet-aware response audit stays silent without mutation, stays silent when required-read evidence exists, and emits `ADVISORY` rather than `STOP` when a correlated packet has required reads and mutation lacks read/search evidence.
9. Pre-action read-debt permit blocks action tools when a correlated packet has concrete requiredRead paths and no prior read/search evidence.
10. The permit stays silent for read/search tools, for action after all required paths were evidenced, and for clean/no-packet turns.
11. Pre-action search-debt permit blocks action tools when a correlated self-resolve packet has fallback searches but no prior root-bound search evidence.
12. Search-debt permit stays silent for search tools, explicit searcher handoff, and action after search evidence exists.
13. Response audit emits advisory when a search-debt packet is followed by mutation without search evidence, and stays silent when search evidence exists.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — source of sanitized surfaced digest journal rows.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — response.completed audit helper.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — pre-action packet-scoped permit helper.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — legacy chain wiring.
  - `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` — pre-action wrapper for read-debt permit and legacy search gate.
  - `.lazy-harness/scripts/lifecycle-check.py` — shadow/orchestrator chain wiring.
  - `.lazy-harness/scripts/self-test.py` — `check_response_rule_audit_from_surfaced_digest` and `check_context_delivery_packet_journal_phase7` fixtures.
- Flow:
  1. Test fixture writes a host-local PR description digest record.
  2. Test runs `on-message-received.sh` with a stable `message_id`.
  3. Test verifies system-reminder body and sanitized journal.
  4. Test runs `check-response-rule-audit.py` with matching `message_id` and PR creation evidence.
  5. Test checks STOP output for missing PR headings, then silence for a compliant body.
  6. Test writes a manual harness-enforcement journal row and checks record-completion miss vs captured cases.
  7. Test runs `context-delivery.ts --journal` in a host fixture and checks sanitized packet evidence.
  8. Test runs `check-read-debt-permit.py` against packet evidence for read-debt action-block, read-allow, satisfied-action silence, and mixed batch block cases.
  9. Test runs `check-read-debt-permit.py` against packet evidence for search-debt action-block, search-tool allow, searcher handoff allow, and satisfied-action silence cases.
  10. Test runs `check-response-rule-audit.py` against packet evidence for no-mutation, missing-read/search advisory, satisfied-read/search silence, and uncorrelated silence cases.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_response_rule_audit_from_surfaced_digest`
  - `.lazy-harness/scripts/self-test.py#check_context_delivery_packet_journal_phase7`
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py`
  - `.lazy-harness/bin/lazy test`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/response-rule-audit.md`
  - SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`
  - ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
- Machine index:
  - graph ids: `kg_response_rule_audit_tdd_record`, `kg_response_rule_audit_self_test`

## Layer completeness

- DDD: no domain term or business rule change.
- SDD: `.lazy-harness/spec/platform/response-rule-audit.md` captures digest and packet-advisory lifecycle contracts.
- BDD: user-visible behavior changes only when a surfaced rule is missed; otherwise no output.
- TDD: this record and self-test fixtures protect the regression surface.
- ADR: implements existing ADR 0041; no new trade-off decision.
- SSOT: implements existing harness enforcement policy; no ownership/config source change.

## Discovery capture

- Planning: `.lazy-harness/planning/record-query-context-loop-transition-plan.md` Phase 4 status should be updated after validation.
