# TDD — Record Lint

Status: accepted
Date: 2026-06-24
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/record-lint.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - adding or changing `record-lint` checks, enums, or commit-gate enforcement
  - protecting canonical-record digest-format and reference integrity
- Must:
  - verify `lazy record-lint --format=json` shape (mode/inspected/issueCount/counts/issues)
  - verify a malformed fixture record produces the expected issue codes and `--fail-on-issues` exits non-zero
  - verify the framework's own canonical records pass `record-lint --fail-on-issues` (commit-gate enforcement)
  - verify example paths inside fenced code blocks are NOT flagged as broken references
- Must not:
  - require network, mutate records, or assert a dev-time hard gate
- Record completion:
  - changes update this TDD, `.lazy-harness/spec/platform/record-lint.md`, the script, dispatcher, self-test, and manifest together
- Related records:
  - `.lazy-harness/spec/platform/record-lint.md`

## Regression fixtures

| Fixture | Input | Expected |
|---|---|---|
| `record_lint_shape` | `lazy record-lint --format=json` | mode=`record-lint`, numeric `inspected`/`cleanRecords`/`issueCount`, `counts` object, `issues` array |
| `record_lint_detects_malformed` | temp host with a spec record lacking `## Rule digest` and one citing a missing `.md` | issues include `missing-rule-digest` and `broken-record-ref`; `--fail-on-issues` exits 2 |
| `record_lint_fenced_examples_ok` | temp record whose only missing `.md` paths are inside a ``` fence | no `broken-record-ref` for fenced paths |
| `record_lint_framework_clean` | framework source `lazy record-lint --fail-on-issues` | exits 0 (all canonical records pass) |

## Acceptance assertions

Self-test must verify:

1. `.lazy-harness/spec/platform/record-lint.md`, `.lazy-harness/tests/record-lint.md`, `.lazy-harness/scripts/record-lint.ts` exist.
2. `lazy record-lint --format=json` returns valid JSON with `mode == "record-lint"`.
3. A temp fixture with a missing digest + a broken `.md` ref yields `missing-rule-digest` and `broken-record-ref`, and `--fail-on-issues` exits non-zero.
4. A `.md` path that exists only inside a fenced code block is NOT flagged.
5. The framework's own canonical records pass `lazy record-lint --fail-on-issues` (exit 0) — commit-gate enforcement.

## Validation commands

```bash
.lazy-harness/bin/lazy record-lint --format=md
.lazy-harness/bin/lazy record-lint --fail-on-issues
python3 .lazy-harness/scripts/self-test.py --scope framework
```

## Implementation map

- Status: verified
- Primary files:
  - `.lazy-harness/tests/record-lint.md` — this record.
  - `.lazy-harness/spec/platform/record-lint.md` — contract.
  - `.lazy-harness/scripts/record-lint.ts` — validator.
  - `.lazy-harness/scripts/self-test.py` — `check_record_lint_cli`.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_record_lint_cli`
- Machine index:
  - graph ids: `kg_record_lint_cli_20260624`, `kg_record_lint_self_test_20260624`

## Layer completeness impact

- DDD: none.
- BDD: commit-time failure on malformed/decayed canonical records.
- SDD: `.lazy-harness/spec/platform/record-lint.md` defines the contract.
- TDD: this record + self-test.
- ADR: ADR 0041 governs the organic/commit-gate enforcement model.
- SSOT: digest format remains `.lazy-harness/spec/platform/record-digest-format.md`.
- Planning: `.lazy-harness/planning/discovery-vs-loading-followups-20260624.md`.
