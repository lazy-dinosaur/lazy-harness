# SDD — Bounded Validation Governor (`lazy validate`)

Status: active
Layer: SDD
Date: 2026-06-18

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - agents need to choose between fast, full, and release-grade validation
  - validation already has green evidence and another full matrix would duplicate work
  - release/readiness validation may run long or cross multiple hosts
- Must:
  - expose `.lazy-harness/bin/lazy validate` as the bounded validation governor
  - default to fast validation, not release/readiness matrices
  - enforce a total `--max-seconds` budget and reject budgets over 3600 seconds
  - require explicit `--allow-release` before executing `--plan release`
  - support `--dry-run` so agents can inspect expensive plans without starting them
  - preserve `.lazy-harness/bin/lazy check` as fast static validation and `.lazy-harness/bin/lazy test` as the full regression gate
- Must not:
  - silently replace full regression claims with fast checks
  - run release-grade readiness validation by default
  - allow unbounded validation workflows
  - scan outside the current host root

## Contract

`lazy validate` is the validation governor:

```bash
.lazy-harness/bin/lazy validate --plan fast --files .lazy-harness/scripts/validation-governor.py --format=json
.lazy-harness/bin/lazy validate --plan standard --max-seconds=300
.lazy-harness/bin/lazy validate --plan release --dry-run --format=json
.lazy-harness/bin/lazy validate --plan release --allow-release --max-seconds=900
```

Plans:

| Plan | Default budget | Steps | Purpose |
|---|---:|---|---|
| `fast` | 60s | `lazy check` | Day-to-day edit loop validation. |
| `standard` | 300s | `lazy check` then one `lazy test` | Commit/sync boundary validation without multiplying full tests. |
| `release` | 900s | `lazy check`, one `lazy test`, smoke doctor, record audit, graph hygiene, lifecycle parity | Explicit release/readiness validation only. |

Execution rules:

1. The runner builds the plan from existing lazy commands.
2. Duplicate command signatures are skipped before execution.
3. If the global deadline is exhausted before a step starts, the step is skipped with `deadline-exhausted` and the run fails.
4. If a step exceeds remaining budget, the step is marked `timeout` and the run fails.
5. A failed step stops later steps.
6. `--plan release` exits non-zero unless `--allow-release` or `--dry-run` is present.
7. `--max-seconds` over 3600 exits non-zero and tells the caller to split validation into bounded chunks.

## Output

JSON output includes:

- `ok`
- `plan`
- `bounded: true`
- `maxSeconds`
- `elapsedSeconds`
- `dryRun`
- `releaseAllowed`
- `fullRegression`
- `steps[]` with command, status, exit code, elapsed time, tail output, and reason
- `errors[]`
- `notes[]`

Markdown output is a compact human-readable summary of the same plan and step results.

## Implementation map

- Primary files:
  - `.lazy-harness/spec/platform/bounded-validation-governor.md` — this SDD contract.
  - `.lazy-harness/tests/bounded-validation-governor.md` — regression contract.
  - `.lazy-harness/scripts/validation-governor.py` — bounded plan builder/executor.
  - `.lazy-harness/bin/lazy` — exposes `lazy validate`.
  - `.lazy-harness/scripts/self-test.py` — fixture coverage.
  - `.lazy-harness/spec/platform/lazy-cli-entrypoint.md` — canonical CLI command list.
  - `.lazy-harness/spec/platform/fast-validation-tier.md` — related fast/static validation tier.
  - `.lazy-harness/planning/performance-optimization-plan.md` — source of the user correction and performance backlog.
- Key symbols:
  - `validation-governor.py#main`
  - `validation-governor.py#build_result`
  - `validation-governor.py#plan_steps`
  - `validation-governor.py#run_step`
  - `self-test.py#check_bounded_validation_governor_cli`
- Flow:
  1. Agent needs validation.
  2. Agent chooses an explicit plan: fast, standard, or release.
  3. Governor deduplicates commands and enforces a global budget.
  4. Release-grade validation requires explicit opt-in.
  5. Result reports whether full regression actually ran.
- Tests:
  - `python3 -m py_compile .lazy-harness/scripts/validation-governor.py`
  - `.lazy-harness/bin/lazy validate --plan fast --files .lazy-harness/fixtures/project-map-v2/example-node.json --format=json`
  - `.lazy-harness/bin/lazy validate --plan release --format=json` should fail without `--allow-release`.
  - `.lazy-harness/bin/lazy validate --plan release --dry-run --format=json` should list the release plan without executing it.
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`

## Cross-layer links

- TDD: `.lazy-harness/tests/bounded-validation-governor.md`
- SDD: `.lazy-harness/spec/platform/fast-validation-tier.md`
- SDD: `.lazy-harness/spec/platform/lazy-cli-entrypoint.md`
- Planning: `.lazy-harness/planning/performance-optimization-plan.md`
- SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`

## Discovery capture

- DDD: no domain/business model change.
- SDD: this record defines the new CLI contract.
- BDD: user-facing validation behavior changes from ad hoc repeated full matrices to explicit bounded plan selection.
- TDD: `.lazy-harness/tests/bounded-validation-governor.md` protects plan selection, release opt-in, budget cap, dry-run, and fast execution.
- ADR: no new ADR; this implements an accepted planning correction without changing enforcement philosophy.
- SSOT: full regression remains `lazy test`; release readiness remains explicit and bounded.
