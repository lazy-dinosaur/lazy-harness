# TDD — Fast Validation Tier (`lazy check`)

Status: active
Layer: TDD
Date: 2026-06-18

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - 검증 티어 회귀
- Applies when:
  - running or implementing `lazy check` for fast changed-file static validation before full regression
- Must:
  - provide fast changed-file static validation that reports `fullRegression: false`
  - fail quickly on malformed changed JSON and reject explicit files outside the host root
- Must not:
  - treat `lazy check` as a full-regression replacement; full regression still requires `lazy test`
- Record completion:
  - changes to `lazy check` scope or output update this TDD plus the fast-validation-tier SDD
- Related records:
  - `.lazy-harness/spec/platform/fast-validation-tier.md`

## Regression target

`lazy check` must provide fast changed-file static validation without replacing the full `lazy test` regression gate.

## Protected fixtures

| Case | Trigger | Expected |
|---|---|---|
| `lazy_check_cli_help` | `.lazy-harness/bin/lazy help` | Help lists `check [--files F1,F2,...] [--all] [--format=md|json]`. |
| `lazy_check_positive_json` | `lazy check --files .lazy-harness/fixtures/project-map-v2/example-node.json --format=json` | Exits 0, reports `ok: true`, `fullRegression: false`, and checks the explicit fixture. |
| `lazy_check_negative_json` | temporary malformed JSON under host root | Exits non-zero and reports `json-parse` without running full self-test. |
| `lazy_check_root_bound` | explicit absolute path outside host root | Exits non-zero and reports `root-bound`. |
| `lazy_check_manifest_and_graph` | explicit `init-categories.json` / `graph.jsonl` | Runs manifest path/glob and graph duplicate-id checks when those files are selected. |
| `lazy_test_still_full_gate` | SDD/TDD text | Records state that `lazy check` is not a full regression replacement and `lazy test` remains the final safety gate. |

## Acceptance assertions

1. `lazy check` dispatches from `.lazy-harness/bin/lazy` to `.lazy-harness/scripts/lazy-check.py`.
2. JSON output includes `fullRegression: false`.
3. Malformed changed JSON fails quickly.
4. Outside-root explicit files fail root-bound validation.
5. `lazy check --all` remains static validation only.
6. Full regression claims still require `.lazy-harness/bin/lazy test`.

## Implementation map

- Primary files:
  - `.lazy-harness/tests/fast-validation-tier.md` — this TDD.
  - `.lazy-harness/spec/platform/fast-validation-tier.md` — SDD contract.
  - `.lazy-harness/scripts/lazy-check.py` — implementation.
  - `.lazy-harness/bin/lazy` — CLI dispatch/help.
  - `.lazy-harness/scripts/self-test.py` — regression coverage.
  - `.lazy-harness/manifests/init-categories.json` — syncs SDD/TDD/script through Category A.
- Key symbols:
  - `lazy-check.py#main`
  - `self-test.py#check_fast_validation_tier_cli`
- Validation commands:
  - `python3 -m py_compile .lazy-harness/scripts/lazy-check.py`
  - `.lazy-harness/bin/lazy check --files .lazy-harness/fixtures/project-map-v2/example-node.json --format=json`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`

## Layer completeness

- SDD: `.lazy-harness/spec/platform/fast-validation-tier.md`.
- BDD: user-facing validation behavior is a faster iterative command before full regression.
- SSOT: full regression remains `.lazy-harness/bin/lazy test` per CLI/enforcement records.
- ADR: no new ADR.
- DDD: no domain/business term impact.
