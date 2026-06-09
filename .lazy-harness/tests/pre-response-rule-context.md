# TDD — Pre-response Compact Static Prompt

Status: accepted
Date: 2026-06-06
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
Related SDD: `.lazy-harness/spec/platform/prompt-budget.md`
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related plan: `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - changing `.lazy-harness/hooks/lifecycle/on-message-received.sh`
  - compacting or expanding the default `message.received` prompt
  - changing search/read debt journaling or pre-action evidence behavior
- Must:
  - keep `message.received` prompt static for all non-empty user messages until an explicit opt-in semantic mode is accepted
  - keep shell/CLI hook code free of raw user-text semantic classifiers
  - keep direct-search debt journaling sanitized and free of raw user messages
  - keep the compact rendered body within the normal prompt-budget target for framework source dogfood
  - preserve the generic evidence guard behavior: block action before root-bound search/read evidence and allow after evidence
- Must not:
  - reintroduce per-layer sample dumps into the default prompt
  - run deleted query helpers, subagents, or `jcode run` inside default `message.received`
  - treat CLI/index output as proof that the LLM/searcher performed direct search
  - add broad edit/write hard stops as prompt-compression work
- Record completion:
  - changes to compact prompt phrases, static equality, no-classifier checks, token ceiling, or debt journal semantics update this TDD record and `.lazy-harness/spec/platform/pre-response-rule-context.md`

## Regression cases

1. Non-empty smalltalk and implementation-like messages render identical prompt bodies.
2. Empty message produces no output.
3. Rendered body contains:
   - `REMINDER. Harness-first search/read debt before response.`
   - `harness-first-static`
   - `static transport; no user-text classification`
   - `no CLI/index semantic authority`
   - `Inventory counts:`
   - `Derived indexes:`
   - `Pointers:`
   - `Protocol: choose real candidate records`
   - `3-5 option gate`
   - `generic evidence guard`
4. Rendered body does not contain older verbose prompt fragments:
   - `Harness inventory (actual files first, compact)`
   - `sample:`
   - `Evidence examples`
   - `find .lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning} -maxdepth 2 -type f`
5. Rendered token estimate is at or below 600 in framework source self-test.
6. Journal row has `event = message.received.direct-search-debt`, `fallbackSearchCount = 1`, `instructionLevel = harness-first-static`, and no raw user text.
7. Generic read-debt permit still blocks action before root-bound harness/source evidence and allows action after such evidence.

## Implementation map

- Primary files:
  - `.lazy-harness/tests/pre-response-rule-context.md` — this regression record.
  - `.lazy-harness/spec/platform/pre-response-rule-context.md` — SDD contract.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — compact prompt renderer and debt journal writer.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — generic evidence guard.
  - `.lazy-harness/scripts/self-test.py` — executable regression fixtures.
  - `.lazy-harness/scripts/prompt-budget.py` — token/line measurement.
- Key symbols:
  - `harness_inventory_lines` (`on-message-received.sh` embedded Python) — renders compact counts/pointers.
  - `check_message_received_hook_context_injection` (`self-test.py`) — protects compact prompt behavior.
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy prompt-budget --format=md`

## Layer completeness impact

- SDD: pre-response prompt transport contract changed from verbose static inventory to compact static inventory.
- BDD: agent-visible system reminder is shorter but carries the same search/read/option-gate behavior.
- SSOT: capability/hard-stop policy unchanged; no new block level.
- DDD: no domain/business rule change.

## Rule placement

- Rule: the default `message.received` prompt may be compact, but it must remain static, non-semantic, search/read-first, and evidence-guard compatible.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/pre-response-rule-context.md`
- Why not AGENTS.md: this is regression coverage for platform behavior, not always-loaded grammar.
- Why not `.jcode`: this is shared framework source validation, not local/private wiring.

## Discovery capture

- DDD: none.
- SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md` updated.
- BDD: compact prompt changes visible agent guidance but not user-facing product UI.
- TDD: this record covers the regression.
- ADR: no new ADR; implements ADR 0041 without changing its model.
- SSOT: no capability level or hard-stop policy change.
- Planning: Phase 2 of `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`.
