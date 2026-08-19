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
  - keep the first-grounding `message.received` body static across non-empty user messages and free of raw user-text semantic classifiers
  - keep direct-search debt journaling sanitized and free of raw user messages
  - keep the rendered body at or below 300 estimated tokens in framework source dogfood
  - keep non-empty hook payload transport intact when inherited `TMPDIR` is missing/unusable by falling back to `/tmp`; this must pass inside the default parallel self-test phase as well as serial fallback
  - preserve first-grounding guard behavior: block mutation before root-bound map/read evidence and allow after evidence
  - preserve Pi/OMP work-unit reuse: overview + directly read governing-record hashes suppress later normal-turn prompt/debt replay while unchanged
  - preserve invalidation: changed/deleted governing records or explicit steer require fresh grounding; late pre-steer results remain stale
  - keep the host-migration probe (`helpers/host_migration_state.py`) bounded + fail-open and host-state-derived only: identical user messages must render identical bodies for a given host state; a lint timeout/error must omit the line, never break the reminder
- Must not:
  - reintroduce per-layer sample dumps into the default prompt
  - run deleted query helpers, subagents, or `jcode run` inside default `message.received`
  - treat CLI/index output as proof that the LLM/searcher performed direct search
  - add broad edit/write hard stops as prompt-compression work
  - replay full inventory, policy/capability catalogs, mapped records, or context resolver results on every normal message or read operation
- Record completion:
  - changes to compact prompt phrases, static equality, no-classifier checks, token ceiling, or debt journal semantics update this TDD record and `.lazy-harness/spec/platform/pre-response-rule-context.md`

## Regression cases

1. Non-empty smalltalk and implementation-like messages render the same static first-grounding body.
2. Empty message produces no output.
3. Rendered body contains the work-unit grounding boundary, one overview + concrete-node protocol, unchanged-evidence reuse, no-micro-edit validation rule, and closure capture pointer.
4. Rendered body excludes inventory counts, generated-index/pointer dumps, mapped record lists, operating-rule catalogs, and source resolver results.
5. Rendered token estimate is at or below 300 in framework source self-test.
6. First grounding journals `message.received.search-read-debt` with sanitized hashes and no raw user text.
7. Generic read-debt permit blocks the first mutation before root-bound evidence and allows after concrete evidence.
8. Pi/OMP fake runtime observes one overview result plus one directly read governing record, then a later normal turn returns `status=reused-work-unit` with no system-prompt replay.
9. Reads/searches never trigger `on-context.sh`; the first successful mutation triggers one pointer-only body of at most five lines.
10. Changing a cached governing record or sending an explicit non-extension steer invalidates reuse; late old-epoch results cannot restore it.
11. Running the hook with a non-existent inherited `TMPDIR` still emits the same static body and journals debt through the `/tmp` payload-file fallback; default `--jobs 4` validation must not report correlated empty-hook failures.
## Implementation map

- Primary files:
  - `.lazy-harness/tests/pre-response-rule-context.md` — this regression record.
  - `.lazy-harness/spec/platform/pre-response-rule-context.md` — SDD contract.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — compact prompt renderer and debt journal writer.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — generic evidence guard.
  - `.lazy-harness/scripts/self-test.py` — executable regression fixtures, including Pi/OMP post-steer evidence epoch behavior.
  - `.lazy-harness/scripts/prompt-budget.py` — token/line measurement.
- Key symbols:
  - `workUnitEvidenceValid` / `observeWorkUnitEvidence` (`packages/lazy-harness-pi/extensions/lazy-harness/index.ts`) — cache and verify overview + governing-record hashes.
  - `check_message_received_hook_context_injection` (`self-test.py`) — protects pointer-only first-grounding body and sanitized journal.
  - `check_pi_package_layout_and_contract` (`self-test.py`) — protects reuse, mutation-only context injection, record-change invalidation, and steer reset.
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
