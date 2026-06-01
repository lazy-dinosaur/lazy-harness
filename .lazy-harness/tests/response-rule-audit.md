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

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — source of sanitized surfaced digest journal rows.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — response.completed audit helper.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — legacy chain wiring.
  - `.lazy-harness/scripts/lifecycle-check.py` — shadow/orchestrator chain wiring.
  - `.lazy-harness/scripts/self-test.py` — `check_response_rule_audit_from_surfaced_digest` fixture.
- Flow:
  1. Test fixture writes a host-local PR description digest record.
  2. Test runs `on-message-received.sh` with a stable `message_id`.
  3. Test verifies system-reminder body and sanitized journal.
  4. Test runs `check-response-rule-audit.py` with matching `message_id` and PR creation evidence.
  5. Test checks STOP output for missing PR headings, then silence for a compliant body.
  6. Test writes a manual harness-enforcement journal row and checks record-completion miss vs captured cases.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_response_rule_audit_from_surfaced_digest`
  - `.lazy-harness/bin/lazy test`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/response-rule-audit.md`
  - SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`
  - ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
- Machine index:
  - graph ids: `kg_response_rule_audit_tdd_record`, `kg_response_rule_audit_self_test`

## Layer completeness

- DDD: no domain term or business rule change.
- SDD: `.lazy-harness/spec/platform/response-rule-audit.md` added for the lifecycle contract.
- BDD: user-visible behavior changes only when a surfaced rule is missed; otherwise no output.
- TDD: this record and self-test fixture protect the regression surface.
- ADR: implements existing ADR 0041; no new trade-off decision.
- SSOT: implements existing harness enforcement policy; no ownership/config source change.

## Discovery capture

- Planning: `.lazy-harness/planning/record-query-context-loop-transition-plan.md` Phase 4 status should be updated after validation.
