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
- Aliases:
  - 규칙 컨텍스트 회귀
  - pre-response 테스트
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
  - preserve Pi/OMP steer re-arming: prior evidence and late pre-steer results stay stale until a fresh post-steer map/read result
  - keep the host-migration probe (`helpers/host_migration_state.py`) bounded + fail-open and host-state-derived only: identical user messages must render identical bodies for a given host state; a lint timeout/error must omit the line, never break the reminder
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
   - `Map-first protocol:`
   - `lazy map --overview`
   - `choose the next concrete node yourself`
   - `map <feature-id|record-path|graph-id|source-path>`
   - `Do not pass raw user text`
   - `invented --query`
   - `3-5 option gate`
   - `generic evidence guard`
4. Rendered body does not contain older verbose prompt fragments:
   - `Harness inventory (actual files first, compact)`
   - `sample:`
   - `Evidence examples`
   - `find .lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning} -maxdepth 2 -type f`
5. Rendered token estimate is at or below 600 in framework source self-test after adding map-first retrieval guidance.
6. Journal row has `event = message.received.search-read-debt`, `fallbackSearchCount = 1`, `instructionLevel = harness-first-static`, and no raw user text.
7. Generic read-debt permit still blocks action before root-bound harness/source evidence and allows action after such evidence.
8. A non-extension mid-turn steer clears earlier evidence, ignores a late result from a pre-steer tool call, blocks the immediate action, and allows after a post-steer map/read call and result.

## Implementation map

- Primary files:
  - `.lazy-harness/tests/pre-response-rule-context.md` — this regression record.
  - `.lazy-harness/spec/platform/pre-response-rule-context.md` — SDD contract.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — compact prompt renderer and debt journal writer.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — generic evidence guard.
  - `.lazy-harness/scripts/self-test.py` — executable regression fixtures, including Pi/OMP post-steer evidence epoch behavior.
  - `.lazy-harness/scripts/prompt-budget.py` — token/line measurement.
- Key symbols:
  - `harness_inventory_lines` (`on-message-received.sh` embedded Python) — renders compact counts/pointers.
  - `check_message_received_hook_context_injection` (`self-test.py`) — protects compact prompt behavior.
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy prompt-budget --format=md`

## Layer completeness impact

- SDD: pre-response/search-read-debt contracts include the Pi/OMP mid-turn evidence epoch boundary.
- BDD: agent-visible steering guidance requires fresh post-steer evidence.
- SSOT: capability/hard-stop and CLI semantic-authority policies remain unchanged; no text or command classifier was added.
- DDD: searchable record memory defines instruction-scoped evidence.

## Rule placement

- Rule: the default `message.received` prompt may be compact, but it must remain static, non-semantic, purpose-scoped-search/read-first, and evidence-guard compatible.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/pre-response-rule-context.md`
- Why not AGENTS.md: this is regression coverage for platform behavior, not always-loaded grammar.
- Why not `.jcode`: this is shared framework source validation, not local/private wiring.

## Discovery capture

- DDD: `.lazy-harness/domain/searchable-record-memory.md` updated with instruction-scoped evidence.
- SDD: pre-response/search-read-debt/Pi package contracts updated.
- BDD: post-steer evidence freshness captured.
- TDD: this record, pre-action guard TDD, and Pi package TDD cover the regression.
- ADR: no new ADR; implements ADR 0041 without changing its semantic-authority model.
- SSOT: no capability level change and no command-specific policy branch.
- Planning: `SCR-702` tracks steer evidence re-arming.

## Phase 5 map-first prompt guidance

Additional regression assertions:

- non-empty messages still render identical bodies regardless of message text;
- rendered body teaches map-first traversal instead of purpose-scoped CLI search;
- rendered body says the LLM chooses concrete nodes from map output;
- rendered body forbids raw user text, long natural-language query strings, and invented `--query` flags for `lazy map`;
- prompt budget remains under the 600 token source-dogfood threshold.
