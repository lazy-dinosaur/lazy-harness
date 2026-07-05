# TDD — Prompt Budget Measurement

Status: accepted
Date: 2026-06-06
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/prompt-budget.md`
Related plan: `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - 예산 회귀
- Applies when:
  - adding or changing prompt budget measurement
  - changing prompt surfaces that affect `.lazy-harness/AGENTS.md`, `.jcode/harness/**`, skill prompts, or `message.received` injection
  - tightening prompt budget thresholds after dogfood evidence
- Must:
  - protect `prompt-budget.py` JSON and Markdown output shapes
  - verify the rendered `message.received` measurement includes line and token estimates
  - verify the measurement uses isolated runtime state and does not emit the synthetic fixture message
  - allow current over-target prompt size during Phase 1 while failing severe transition-threshold regressions
  - keep project-local skill prompts as measured advisory surfaces, not broad hard failures
  - verify `lazy prompt-budget --format=md` dispatch works
- Must not:
  - require Phase 1 to shorten prompts
  - make prompt budget warnings into broad runtime hard stops
  - require host-owned `SKILL.md` prompts to be shortened or rewritten
  - require external tokenizer packages
  - store raw user messages or transcripts
- Record completion:
  - changes to test thresholds, output fields, privacy assertions, or prompt-budget command behavior update this TDD record and `.lazy-harness/spec/platform/prompt-budget.md`
- Related records:
  - `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - `.lazy-harness/tests/record-decision-broker.md`

## Regression target

Phase 1 should add measurement only. Existing hook behavior must remain unchanged:

- `message.received` output remains static for all non-empty messages.
- Direct-search debt journal rows are still written by the hook itself.
- Prompt budget measurement renders the hook in a temporary runtime root, not in the host's runtime journal.

## Self-test coverage

`python3 .lazy-harness/scripts/self-test.py` must include checks that:

1. `.lazy-harness/spec/platform/prompt-budget.md` exists.
2. `.lazy-harness/tests/prompt-budget.md` exists.
3. `.lazy-harness/scripts/prompt-budget.py` exists.
4. `python3 .lazy-harness/scripts/prompt-budget.py --root . --format=json` returns valid JSON.
5. JSON includes:
   - `schemaVersion = 1.0`,
   - top-level `status`,
   - `surfaces`,
   - `duplicates`,
   - `renderedMessageReceived.tokenEstimate`,
   - `renderedMessageReceived.lineCount`.
6. Output does not contain the synthetic fixture message.
7. `renderedMessageReceived.tokenEstimate` is below the Phase 1 transition hard ceiling.
8. `.lazy-harness/bin/lazy prompt-budget --format=md` prints a human-readable report with line counts, token estimate, duplicate findings, and status.
9. A 500+ line host-local `.jcode/skills/**/SKILL.md` fixture is reported as `skill-prompt` with `enforcement=advisory`, `rawStatus=fail`, `status=warn`, and does not make the top-level status `fail`.
10. Generated `.jcode/harness/05-lazy-harness.md` is pointer-only and must not duplicate the full `.lazy-harness/AGENTS.md` grammar already loaded through root `AGENTS.md`.

## Acceptance command

```bash
python3 .lazy-harness/scripts/self-test.py
.lazy-harness/bin/lazy doctor --profile=smoke
.lazy-harness/bin/lazy prompt-budget --format=md
python3 .lazy-harness/scripts/prompt-budget.py --root . --format=json
```

## Rollback

Phase 1 is additive. Revert the prompt-budget commit to remove:

- `.lazy-harness/spec/platform/prompt-budget.md`
- `.lazy-harness/tests/prompt-budget.md`
- `.lazy-harness/scripts/prompt-budget.py`
- `lazy prompt-budget` dispatch
- self-test additions

Runtime hook behavior is unchanged, so rollback should not require runtime journal migration.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/tests/prompt-budget.md` — this TDD record.
  - `.lazy-harness/spec/platform/prompt-budget.md` — measurement contract.
  - `.lazy-harness/scripts/prompt-budget.py` — measured script under test.
  - `.lazy-harness/scripts/self-test.py` — test harness.
  - `.lazy-harness/bin/lazy` — command dispatch.
- Key symbols:
  - `estimate_tokens` (`prompt-budget.py`) — deterministic tokenizer-free estimate.
  - `render_message_received` (`prompt-budget.py`) — isolated hook render.
  - `find_duplicate_blocks` (`prompt-budget.py`) — duplicate grammar heuristic.
  - `check_prompt_budget_measurement` (`self-test.py`) — regression fixture.
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py`
- Machine index:
  - graph ids: `pending`
  - generated index key: `pending until implementation-index generator exists`

## Rule placement

- Rule: prompt budget measurement must be test-protected and must not change runtime behavior in Phase 1.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/prompt-budget.md`
- Why not AGENTS.md: this is regression strategy, not always-loaded grammar.
- Why not `.jcode`: this is shared framework source validation.

## Discovery capture

- DDD: none.
- SDD: `.lazy-harness/spec/platform/prompt-budget.md` defines the contract.
- BDD: no user-visible behavior change in Phase 1.
- TDD: this record defines regression coverage.
- ADR: no new decision; implements ADR 0041 compression direction.
- SSOT: no new source-of-truth beyond budgets in SDD.
- Planning: Phase 1 of `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`.

## Map-first prompt guidance

The `message.received` prompt may include map-first traversal examples as long as:

- static equality remains true for all non-empty messages;
- no raw user-text classifier is introduced;
- rendered token estimate remains under the framework source dogfood threshold protected by `check_message_received_hook_context_injection`;
- `lazy prompt-budget --format=json` reports a passing `renderedMessageReceived` surface.
