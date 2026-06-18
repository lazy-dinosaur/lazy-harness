# TDD — Bounded Validation Governor (`lazy validate`)

Status: active
Layer: TDD
Date: 2026-06-18

## Regression target

`lazy validate` must prevent accidental long-running validation multiplication by making validation plans explicit, bounded, and release-gated.

## Protected fixtures

| Case | Trigger | Expected |
|---|---|---|
| `validate_help` | `.lazy-harness/bin/lazy help` | Help lists `validate [--plan=fast|standard|release]`. |
| `validate_fast_json` | `lazy validate --plan fast --files .lazy-harness/fixtures/project-map-v2/example-node.json --format=json` | Exits 0, reports `bounded: true`, `plan: fast`, one passed fast-static step, and `fullRegression: false`. |
| `validate_release_requires_opt_in` | `lazy validate --plan release --format=json` | Exits non-zero and reports `release plan requires --allow-release or --dry-run`. |
| `validate_release_dry_run` | `lazy validate --plan release --dry-run --format=json` | Exits 0, lists planned release steps, does not execute them, and shows `fullRegression: true` because the plan includes one full test. |
| `validate_budget_cap` | `lazy validate --plan fast --max-seconds=3601 --format=json` | Exits non-zero and reports that budgets over 3600 must be split. |
| `validate_deadline_zero` | `lazy validate --plan fast --max-seconds=0 --format=json` | Exits non-zero without running `lazy check`, step status is `skipped` with `deadline-exhausted`. |
| `validate_progress_json_safe` | `lazy validate --plan fast --format=json` | Stdout remains parseable JSON and stderr contains `JCODE_PROGRESS` rows. |
| `validate_progress_off` | `lazy validate --plan fast --progress=off --format=json` | Stdout remains parseable JSON and stderr contains no `JCODE_PROGRESS` rows. |

## Acceptance assertions

1. `lazy validate` dispatches from `.lazy-harness/bin/lazy` to `.lazy-harness/scripts/validation-governor.py`.
2. `fast` is the default plan and does not run full regression.
3. `standard` contains exactly one full-regression step in dry-run output.
4. `release` cannot execute without `--allow-release`.
5. All plans include a total budget and reject `--max-seconds > 3600`.
6. Dry-run output must be available for release plans without starting expensive commands.
7. Full regression claims remain tied to `lazy test` execution or planned full-regression steps, not to fast static checks.
8. Long-running non-dry-run plans emit progress to stderr, never stdout, so JSON consumers and Jcode background progress can both work.

## Implementation map

- Primary files:
  - `.lazy-harness/tests/bounded-validation-governor.md` — this TDD.
  - `.lazy-harness/spec/platform/bounded-validation-governor.md` — SDD contract.
  - `.lazy-harness/scripts/validation-governor.py` — implementation.
  - `.lazy-harness/bin/lazy` — CLI dispatch/help.
  - `.lazy-harness/scripts/self-test.py` — regression fixtures.
  - `.lazy-harness/manifests/init-categories.json` — syncs the SDD/TDD and script through Category A.
- Key symbols:
  - `validation-governor.py#main`
  - `validation-governor.py#build_result`
  - `validation-governor.py#plan_steps`
  - `validation-governor.py#emit_progress`
  - `self-test.py#check_bounded_validation_governor_cli`
- Validation commands:
  - `python3 -m py_compile .lazy-harness/scripts/validation-governor.py`
  - `.lazy-harness/bin/lazy validate --plan fast --files .lazy-harness/fixtures/project-map-v2/example-node.json --format=json`
  - `.lazy-harness/bin/lazy validate --plan fast --progress=off --files .lazy-harness/fixtures/project-map-v2/example-node.json --format=json`
  - `.lazy-harness/bin/lazy validate --plan release --dry-run --format=json`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`

## Layer completeness

- SDD: `.lazy-harness/spec/platform/bounded-validation-governor.md`.
- BDD: user-facing validation flow is now explicit bounded plan selection instead of ad hoc repeated full matrices.
- SSOT: full regression remains `.lazy-harness/bin/lazy test`; release validation requires explicit opt-in.
- ADR: no new ADR.
- DDD: no domain/business term impact.
