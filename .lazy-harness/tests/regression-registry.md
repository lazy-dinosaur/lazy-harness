# TDD — Fix-Commit Regression Registry

Status: active
Layer: TDD

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - changing the Fix-commit regression gate reader, the `lazy regression` writer/lint, or the registry contract
  - verifying that a spaced (`"sha": "x"`) registry entry satisfies the gate
- Must:
  - verify the reader satisfies the gate from a spaced JSON entry and still STOPs when the sha is absent
  - verify `candidates.jsonl` does not satisfy the gate
  - verify `lazy regression add` rejects non-40-hex sha, `<...>` placeholders, and `pending` test stubs, writes canonical JSON, and dedups
  - verify `lazy regression lint` flags placeholder/pending/bad-sha/empty-field/invalid-json entries
- Must not:
  - require network, mutate shared host registries, or assert a dev-time hard git gate
- Record completion:
  - changes to reader/writer/lint/gate update this TDD plus its SDD, script/hook, dispatcher, self-test, and manifest
- Related records:
  - `.lazy-harness/spec/platform/regression-registry.md`

## Regression target

The Fix-commit regression gate must recognize an existing registry entry regardless of JSON whitespace (the original bug: reader grepped `"sha":"$SHA"` while writers emit `"sha": "$SHA"`, so the STOP advisory looped forever), and all writes must go through a validated CLI that cannot introduce placeholder garbage or malformed shas.

## Protected fixtures

| Case | Trigger | Expected |
|---|---|---|
| `regression_reader_spaced_entry_satisfies` | temp host, `Fix:` HEAD, registry line `{"sha": "<sha>", ...}` (spaced) | hook emits no STOP (sha found via JSON parse) |
| `regression_reader_absent_sha_stops` | `Fix:` HEAD whose sha is not in registry | hook emits a STOP advisory pointing at `lazy regression add` |
| `regression_reader_candidates_not_satisfying` | sha present only in `candidates.jsonl`, not `registry.jsonl` | hook still STOPs (auto-stub does not satisfy) |
| `regression_reader_non_fix_silent` | non-`Fix:` HEAD | hook silent (exit 0) |
| `regression_add_rejects_bad_sha` | `regression add --sha pending ...` | exit 2, nothing appended |
| `regression_add_rejects_placeholder` | `regression add --test "<test_path>" ...` | exit 2, nothing appended |
| `regression_add_writes_and_dedups` | valid `regression add`, then re-run same sha | first appends canonical JSON; second is a no-op |
| `regression_lint_flags_garbage` | registry with placeholder/pending/bad-sha/empty entries | lint reports the matching codes; `--fail-on-issues` exits 2 |

## Acceptance assertions

Self-test must verify:

1. A spaced registry entry for the `Fix:` HEAD sha makes the reader silent.
2. An absent sha makes the reader emit STOP.
3. A sha present only in `candidates.jsonl` does NOT satisfy the gate.
4. `lazy regression add` rejects `pending`/short sha and `<...>`/`pending:` test placeholders (exit 2, no write).
5. A valid `lazy regression add` appends one canonical line and a duplicate sha is a no-op.
6. `lazy regression lint --fail-on-issues` flags garbage entries and exits non-zero.

## Validation commands

```bash
python3 .lazy-harness/scripts/self-test.py --scope framework
.lazy-harness/bin/lazy regression lint --format=md
```

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-fix-regression.sh` — reader under test.
  - `.lazy-harness/scripts/regression.ts` — writer/lint under test.
  - `.lazy-harness/scripts/self-test.py#check_fix_regression_registry` — executable fixtures.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/regression-registry.md`
  - ADR: ADR 0016/0041 (advisory gate; no new dev-time hard gate).

## Layer completeness

- SDD: `.lazy-harness/spec/platform/regression-registry.md`.
- BDD: visible behavior is the STOP advisory on an unregistered Fix commit; no separate BDD record.
- SSOT: registry format lives in the SDD; registry data is host-owned runtime — no SSOT ownership change.
- DDD: no domain term change.

## Rule placement

- Rule: the regression gate reader is JSON-parse (whitespace agnostic) and writes go through the validated `lazy regression add` CLI; regression coverage protects both.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/regression-registry.md`
- Why not AGENTS.md: this is regression coverage, not prompt grammar.
- Why not local notes: shared framework behavior for all hosts.
- Confirmation: user-confirmed
