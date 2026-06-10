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
7. `message.received` writes sanitized generic search/read-debt rows without raw user messages or raw record bullets.
8. Packet-aware response audit stays silent when root-bound search/read evidence exists and emits `ADVISORY` rather than `STOP` when correlated generic search-debt lacks evidence.
9. Pre-action read/search-debt permit blocks action tools when a correlated static debt row lacks prior root-bound search/read evidence.
10. The permit stays silent for read/search tools, for action after all required paths were evidenced, and for clean/no-packet turns.
11. Pre-action search-debt permit blocks action tools when a correlated self-resolve packet has fallback searches but no prior root-bound search evidence.
12. Search-debt permit stays silent for search tools, explicit searcher handoff, and action after search evidence exists.
13. Response audit emits advisory whenever a correlated search-debt packet reaches response.completed without root-bound search evidence, and stays silent when search evidence exists.
14. Read/search evidence can come from `.jcode/hooks/tool-events.jsonl` when lifecycle `recent_tool_calls` omits prior Read/Search calls; this prevents false-positive action blocks after the agent already satisfied requiredRead/search-debt.
15. Tool-events fallback must not accept same-session events from a different message when current `message_id` is present.
16. Tool-events fallback must not accept evidence older than the correlated search/read-debt row epoch.
17. Packet journal matching must not accept a same-session packet from a different message when current `message_id` is present.
18. Packet journal matching must not accept a same-message packet from a different session when current `session_id` is present.
19. Category A sync manifest must include `.lazy-harness/tests/response-rule-audit.md` so host self-tests carry the response audit TDD fixture, not only the SDD contract.
20. Generic search-debt guard must treat unknown external MCP-like action as action until root-bound local search evidence exists; no concrete tool/Figma adapter names may be required.
21. Runtime/generator/fixture surfaces must remain host-agnostic: downstream host/product aliases and app-specific path taxonomy are forbidden outside allowed dogfood/history records.
22. Response audit must advise for every correlated search-debt packet that reaches response.completed without root-bound search evidence; it must stay silent once root-bound search evidence exists.
23. Response audit must stay silent when correlated search-debt has safe purpose-scoped find evidence, and must still advise for `architecture`/`full` purpose-only evidence.
24. Response audit emits advisory-only feedback when a recent tool action matches a `warn|block` capability `discouragedActions` entry and no prior `lazy rules resolve` / `lazy capability resolve` evidence exists. It stays silent when resolve evidence exists or no discouraged action matches.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — source of sanitized surfaced digest journal rows.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — response.completed audit helper.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — pre-action packet-scoped permit helper.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — legacy chain wiring.
  - `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` — pre-action wrapper for read-debt permit and legacy search gate.
  - `.lazy-harness/scripts/lifecycle-check.py` — shadow/orchestrator chain wiring.
  - `.lazy-harness/scripts/self-test.py` — `check_response_rule_audit_from_surfaced_digest`, `check_read_debt_permit_generic_external_action`, and `check_framework_runtime_no_host_product_hardcoding` fixtures.
  - `.lazy-harness/manifests/init-categories.json` — Category A sync manifest entry for this TDD record, preventing host copies from carrying the SDD without its regression fixture.
- Flow:
  1. Test fixture writes a host-local PR description digest record.
  2. Test runs `on-message-received.sh` with a stable `message_id`.
  3. Test verifies system-reminder body and sanitized journal.
  4. Test runs `check-response-rule-audit.py` with matching `message_id` and PR creation evidence.
  5. Test checks STOP output for missing PR headings, then silence for a compliant body.
  6. Test writes a manual harness-enforcement journal row and checks record-completion miss vs captured cases.
  8. Test runs `check-read-debt-permit.py` against packet evidence for read-debt action-block, read-allow, satisfied-action silence, and mixed batch block cases.
  9. Test runs `check-read-debt-permit.py` against packet evidence for search-debt action-block, search-tool allow, searcher handoff allow, and satisfied-action silence cases.
  10. Test runs `check-read-debt-permit.py` and `check-response-rule-audit.py` with empty lifecycle `recent_tool_calls` plus same-message/session `.jcode/hooks/tool-events.jsonl` Read/Search events to prevent the false-positive reported on 2026-06-01.
  11. Test runs `check-read-debt-permit.py` and `check-response-rule-audit.py` with same-session/different-message events and pre-packet events to prevent over-accepting stale evidence.
  12. Test runs `check-read-debt-permit.py` and `check-response-rule-audit.py` with same-session/different-message packets and same-message/different-session packets to prevent parallel session/turn packet contamination.
  13. Test runs `check-response-rule-audit.py` against packet evidence for no-mutation, missing-read/search advisory, satisfied-read/search silence, and uncorrelated silence cases.
  14. `check_response_rule_audit_from_surfaced_digest` asserts both this TDD record exists in source and `init-categories.json` syncs `tests/response-rule-audit.md` to hosts.
  15. `check_read_debt_permit_generic_external_action` writes search-debt packet evidence and verifies an unknown external MCP-like action emits root-bound search guard output until `agentgrep` evidence exists.
  16. `check_framework_runtime_no_host_product_hardcoding` scans runtime/generator/fixture surfaces for downstream host/product aliases, concrete tool adapters, and app-specific path taxonomy leaks.
  17. `check_context_delivery_packet_journal_phase7` includes all-search-debt completion cases: no search evidence emits advisory even without mutation/assistant-response cues; the same turn with `agentgrep` evidence stays silent.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_response_rule_audit_from_surfaced_digest`
  - `.lazy-harness/scripts/self-test.py#check_context_delivery_packet_journal_phase7`
  - `.lazy-harness/scripts/self-test.py#check_read_debt_permit_generic_external_action`
  - `.lazy-harness/scripts/self-test.py#check_framework_runtime_no_host_product_hardcoding`
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py`
  - `.lazy-harness/manifests/init-categories.json#tests/response-rule-audit.md`
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
- SSOT: `.lazy-harness/manifests/init-categories.json` is updated as the Category A sync source for this TDD fixture; no ownership/env/schema source change.

## Discovery capture

- Planning: `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md` Phase 4 status should be updated after validation.
