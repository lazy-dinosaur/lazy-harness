# TDD — Relevant Record Query CLI equals-form flags

Status: accepted
Layer: TDD
Date: 2026-06-01
Related SDD: `.lazy-harness/spec/platform/relevant-record-query.md`
Related implementation: `.lazy-harness/scripts/relevant-record-query.ts`

## Regression

Downstream dogfood smoke in `/home/lazydino/dev/medivance` and `/home/lazydino/dev/medivance-pwa` found that:

```bash
.lazy-harness/bin/lazy context --message "release workflow PR description" --format=md
```

printed usage and exited 2.

The root cause was that `.lazy-harness/bin/lazy` documents `--format=json|md` style options, but `relevant-record-query.ts` only accepted separated value flags such as `--format json`.

## Expected behavior

Relevant Record Query value flags accept both spellings:

```bash
--message "PR body"
--message="PR body"
--format json
--format=json
--token-budget 300
--token-budget=300
--layer SSOT
--layer=SSOT
--status active
--status=active
--limit 1
--limit=1
--root /path/to/host
--root=/path/to/host
```

Boolean flags such as `--require-digest` remain standalone.

## Protection

`.lazy-harness/scripts/self-test.py#check_relevant_record_query_cli` runs both separated-value and equals-form invocations against a temporary host fixture with a Rule digest record.

The equals-form fixture asserts:

- return code is 0,
- JSON output parses,
- `--layer=SSOT`, `--status=active`, and `--limit=1` are respected,
- the expected `.lazy-harness/ssot/pr-description-format.md` record is returned.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/scripts/relevant-record-query.ts` — CLI parser for relevant record query and `lazy context` backend.
  - `.lazy-harness/scripts/self-test.py` — regression coverage in `check_relevant_record_query_cli`.
  - `.lazy-harness/spec/platform/relevant-record-query.md` — SDD contract documenting dual CLI flag spellings.
  - `.lazy-harness/bin/lazy` — user-facing `context --message "..." [--format=json|md]` dispatcher whose documented style triggered the regression smoke.
- Key symbols:
  - `parseArgs` (`.lazy-harness/scripts/relevant-record-query.ts`) — accepts `--flag value` and `--flag=value` for value flags.
  - `check_relevant_record_query_cli` (`.lazy-harness/scripts/self-test.py`) — protects digest query output and equals-form argument parsing.
- Flow:
  1. User or hook calls `.lazy-harness/bin/lazy context --message="..." --format=json`.
  2. `lazy context` delegates to `relevant-record-query.ts --root "$HOST_ROOT" ...`.
  3. `parseArgs` normalizes separated and equals-form flags into one `CliOptions` object.
  4. Query returns compact Markdown or JSON digest instead of usage/exit 2.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_relevant_record_query_cli`
  - `.lazy-harness/scripts/self-test.py#check_message_received_hook_context_injection`
  - downstream smoke after source sync: `.lazy-harness/bin/lazy context --message="..." --format=md`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/relevant-record-query.md`
  - SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - Planning: `.lazy-harness/planning/record-query-context-loop-transition-plan.md`
- Machine index:
  - graph ids: `kg_relevant_record_query_equals_flags_tdd`, `kg_relevant_record_query_equals_flags_impl`, `kg_relevant_record_query_equals_flags_self_test`
  - generated index: `pending generated implementation-index refresh; canonical graph rows are appended in .lazy-harness/knowledge/graph.jsonl`

## Layer completeness

- DDD: no domain vocabulary change.
- SDD: updated `.lazy-harness/spec/platform/relevant-record-query.md` because CLI input contract changed.
- BDD: no user-facing app behavior change; this affects harness CLI behavior before responses.
- TDD: this record plus self-test regression coverage.
- ADR: no new design decision; still within ADR 0041 organic direction where this CLI is explicit/manual helper support, while default `message.received` uses direct-search prompting.
- SSOT: no source-of-truth/config ownership change.

## Discovery capture

- Planning: downstream sync validation exposed this CLI ergonomics bug before final reporting.
- Follow-up: after the fix, resync downstream hosts to a new source commit and rerun host lazy tests plus `lazy context` smoke.
