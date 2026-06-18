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
  - emit `JCODE_PROGRESS` lines to stderr during execution so long-running validation has visible progress without corrupting JSON stdout
  - reuse full-regression evidence only when a conservative workspace fingerprint matches exactly
  - preserve `.lazy-harness/bin/lazy check` as fast static validation and `.lazy-harness/bin/lazy test` as the full regression gate
- Must not:
  - silently replace full regression claims with fast checks
  - reuse full-regression evidence across changed `HEAD`, working-tree diff/status, untracked files, or `.lazy-harness` body
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
.lazy-harness/bin/lazy validate --plan standard --progress=off --format=json
.lazy-harness/bin/lazy validate --plan standard --evidence-cache=off --format=json
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
8. Non-dry-run execution emits `JCODE_PROGRESS {json}` lines to stderr at plan start, step start, and step completion. `--progress=off` or `LAZY_VALIDATE_PROGRESS=0` disables these lines.
9. Full-regression evidence cache is conservative and applies only to full-regression steps. Fast static checks still run every time.
10. Cache keys include cache version, step command, scope, git `HEAD`, git diff hash, git status hash, untracked-file hash, and canonical `.lazy-harness` content hash. Volatile runtime/derived paths such as `.lazy-harness/state/**`, `.lazy-harness/logs/**`, `.lazy-harness/generated/**`, and `__pycache__` are excluded. Cache miss, cache read/write error, or fingerprint uncertainty falls back to running `lazy test`.
11. Cache storage is runtime state at `$LAZY_RUNTIME_ROOT/state/validation-evidence-cache.json`, defaulting to `.lazy-harness/state/validation-evidence-cache.json`, and is ignored by git.
12. `--evidence-cache=off` or `LAZY_VALIDATE_EVIDENCE_CACHE=0` disables reuse and storage for full-regression evidence.

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
- `evidenceReused`
- `steps[]` with command, status, exit code, elapsed time, tail output, and reason
- `errors[]`
- `notes[]`

Progress output is intentionally not included in stdout JSON. It is emitted on stderr so automation can parse stdout as JSON and the Jcode background task UI can still show progress.

When evidence is reused, the full-regression step status is `reused`, `fullRegression` remains true, and `evidenceReused` is true. This is a full-regression evidence reuse, not a fast-check substitution.

Markdown output is a compact human-readable summary of the same plan and step results.

## Implementation map

- Primary files:
  - `.lazy-harness/spec/platform/bounded-validation-governor.md` — this SDD contract.
  - `.lazy-harness/tests/bounded-validation-governor.md` — regression contract.
  - `.lazy-harness/scripts/validation-governor.py` — bounded plan builder/executor.
  - `$LAZY_RUNTIME_ROOT/state/validation-evidence-cache.json` — runtime-only validation evidence cache.
  - `.gitignore` — ignores the default runtime cache path.
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
  - `validation-governor.py#emit_progress`
  - `validation-governor.py#workspace_fingerprint`
  - `validation-governor.py#evidence_key`
  - `validation-governor.py#cached_step_result`
  - `validation-governor.py#store_step_result`
  - `self-test.py#check_bounded_validation_governor_cli`
- Flow:
  1. Agent needs validation.
  2. Agent chooses an explicit plan: fast, standard, or release.
  3. Governor deduplicates commands and enforces a global budget.
  4. Fast static check runs normally.
  5. If a full-regression step appears and cache is enabled, the governor checks conservative cached evidence.
  6. Cache hit reuses the full-regression evidence; cache miss or uncertainty runs `lazy test` and stores successful evidence.
  7. Release-grade validation requires explicit opt-in.
  8. Result reports whether full regression ran or was reused.
- Tests:
  - `python3 -m py_compile .lazy-harness/scripts/validation-governor.py`
  - `.lazy-harness/bin/lazy validate --plan fast --files .lazy-harness/fixtures/project-map-v2/example-node.json --format=json`
  - `.lazy-harness/bin/lazy validate --plan release --format=json` should fail without `--allow-release`.
  - `.lazy-harness/bin/lazy validate --plan release --dry-run --format=json` should list the release plan without executing it.
  - `.lazy-harness/bin/lazy validate --plan fast --format=json` should keep stdout JSON parseable and emit `JCODE_PROGRESS` on stderr.
  - `.lazy-harness/bin/lazy validate --plan standard --format=json` should store full-regression evidence on a miss, then reuse it on the same conservative fingerprint.
  - `.lazy-harness/bin/lazy validate --plan standard --evidence-cache=off --format=json` should never reuse evidence.
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
- TDD: `.lazy-harness/tests/bounded-validation-governor.md` protects plan selection, release opt-in, budget cap, dry-run, progress visibility, evidence cache safety, and fast execution.
- ADR: no new ADR; this implements an accepted planning correction without changing enforcement philosophy.
- SSOT: full regression remains `lazy test`; release readiness remains explicit and bounded.
