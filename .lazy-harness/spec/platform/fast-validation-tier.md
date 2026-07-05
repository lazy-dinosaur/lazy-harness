# SDD — Fast Validation Tier (`lazy check`)

Status: active
Layer: SDD
Date: 2026-06-18

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 빠른 검증
  - fast validation
  - 검증 티어
- Applies when:
  - agents need quick feedback after editing harness records/source/tests
  - `lazy test` is too slow for every edit loop
  - choosing between formatter/static checks, affected tests, and full regression
- Must:
  - expose `.lazy-harness/bin/lazy check` as a fast static validation tier
  - validate changed files by default and explicit files with `--files`
  - keep JSON/XML/JSONL parse, Python compile, shell syntax, graph-id, manifest-path, fixture canonical-record, root-bound path, and `git diff --check` coverage lightweight
  - state clearly that `lazy check` is not full regression and does not replace `.lazy-harness/bin/lazy test`
  - keep `.lazy-harness/bin/lazy test` as the full framework/host regression gate
  - keep harness integrity validation separate from downstream product validation; product-wide `typecheck`, lint, build, or E2E must be justified by user request, host test strategy, or product-code impact, not by a generic "cover all bases" impulse
- Must not:
  - weaken pre-push/full release validation
  - silently skip unknown static parse failures
  - become a semantic authority for project rules or record meaning
  - scan sibling repos or paths outside the current host root

## Contract

`lazy check` is the day-to-day fast tier:

```bash
.lazy-harness/bin/lazy check
.lazy-harness/bin/lazy check --files .lazy-harness/manifests/init-categories.json --format=json
.lazy-harness/bin/lazy check --all
```

Default behavior:

1. Resolve the current host root exactly like other `lazy` commands.
2. Determine changed files from staged, unstaged, and untracked git files.
3. Run `git diff --check` unless `--no-diff-check` is passed.
4. Validate changed files with static file-type checks only.
5. Return JSON/Markdown containing `fullRegression: false` and a note to run `lazy test` for full coverage.

`lazy check --all` still means fast static validation over `.lazy-harness/**`; it does **not** run the full self-test suite.

## Tiering model

| Tier | Command | Intended time | Purpose |
|---|---|---:|---|
| Fast static | `lazy check` | seconds | Changed-file parse/syntax/path hygiene before iterating. |
| Affected | `lazy affected` / future `lazy test --affected` | focused | Related test subset chosen from changed files. |
| Full regression | `lazy test` | slower | Reproducible framework/host regression gate before commit/sync/release. |

## Implementation map

- Primary files:
  - `.lazy-harness/spec/platform/fast-validation-tier.md` — this SDD.
  - `.lazy-harness/tests/fast-validation-tier.md` — regression contract.
  - `.lazy-harness/scripts/lazy-check.py` — fast static validator implementation.
  - `.lazy-harness/bin/lazy` — dispatches `check` to the script.
  - `.lazy-harness/scripts/self-test.py` — protects CLI wiring and behavior fixtures.
  - `.lazy-harness/spec/platform/lazy-cli-entrypoint.md` — lists the canonical CLI command.
- Key symbols:
  - `lazy-check.py#main`
  - `self-test.py#check_fast_validation_tier_cli`
- Flow:
  1. Agent edits harness/source files.
  2. Agent runs `lazy check` for fast static feedback.
  3. Agent runs focused/affected validation as needed.
  4. Agent runs `lazy test` before claiming full regression safety.
- Tests:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy check --files .lazy-harness/fixtures/project-map-v2/example-node.json --format=json`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/lazy-cli-entrypoint.md`
  - SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`
  - Planning: `.lazy-harness/planning/performance-optimization-plan.md`

## Discovery capture

- DDD: no domain model change.
- SDD: adds fast validation tier contract.
- BDD: agent/user behavior changes from “run full lazy test after every edit” to “run fast check while iterating, full test at safety boundaries.”
- TDD: `.lazy-harness/tests/fast-validation-tier.md` protects CLI and failure behavior.
- ADR: no new ADR; this refines existing CLI/test contracts without changing full-gate semantics.
- SSOT: full regression remains mandatory for final safety claims.
- Planning: performance work can continue with affected-test tiering after this fast static tier.
