# SDD — Bounded Validation Governor (`lazy validate`)

Status: active
Layer: SDD
Date: 2026-06-18

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 검증 governor
  - validation governor
  - 검증 한도
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
  - emit runtime-neutral `LAZY_PROGRESS` lines to stderr during execution so long-running validation has visible progress without corrupting JSON stdout
  - reuse full-regression evidence only when a conservative regression-relevant workspace fingerprint matches exactly
  - exclude `.lazy-harness/evidence/**` from the full-regression fingerprint because capsules summarize validation output; the fast tier still runs after every edit
  - register recommend-level `bounded-validation-orchestration` capability/policy guidance so agents use `lazy check` while editing and one `lazy validate --plan standard` after the final mutation
  - reserve direct `lazy test` for explicit fresh full-regression requests or commit/push/release gates
  - run audited independent self-test checks in bounded process workers by default, isolate worker runtime state, serialize fixed-path checks, preserve registry-order output, and provide `--jobs=1` fallback
  - preserve `.lazy-harness/bin/lazy check` as fast static validation and `.lazy-harness/bin/lazy test` as the full regression gate
  - keep harness-integrity plans bounded to lazy-harness commands unless a user request, host test strategy, or product-code impact explicitly calls for downstream app typecheck/lint/build/E2E
- Must not:
  - silently replace full regression claims with fast checks
  - reuse full-regression evidence across changed `HEAD`, regression-relevant working-tree diff/status, untracked files, source/tests/contracts/graph, or canonical `.lazy-harness` body; only runtime/derived files and `.lazy-harness/evidence/**` are excluded
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
8. Non-dry-run execution emits `LAZY_PROGRESS {json}` lines to stderr at plan start, step start, and step completion. `--progress=off` or `LAZY_VALIDATE_PROGRESS=0` disables these lines.
9. Full-regression evidence cache is conservative and applies only to full-regression steps. Fast static checks still run every time.
10. Cache keys include cache version, resolved host-root identity, step command, scope, git `HEAD`, regression-relevant git diff/status, untracked-file hash, canonical `.lazy-harness` content hash, dependency manifests/locks, and Python/Bun/Git executable-version signatures. Volatile runtime/derived paths and `.lazy-harness/evidence/**` are excluded; source, tests, contracts, policies, graph, and canonical records remain fingerprint inputs. Cache miss, unavailable tool signature, cache read/write error, or fingerprint uncertainty falls back to running `lazy test`.
11. Cache storage is runtime state at `$LAZY_RUNTIME_ROOT/state/validation-evidence-cache.json`, defaulting to `.lazy-harness/state/validation-evidence-cache.json`, and is ignored by git. In worktrees where `.lazy-harness` is a symlink, the cache path is considered protected when the `.lazy-harness` boundary itself is ignored, even if `git check-ignore` refuses nested symlink pathspecs.
12. `--evidence-cache=off` or `LAZY_VALIDATE_EVIDENCE_CACHE=0` disables reuse and storage for full-regression evidence.
13. Agent edit loops use `lazy check`; after the final mutation they use one `lazy validate --plan standard`. Writing an evidence capsule after a green full run does not itself require another full run.
14. `self-test.py` defaults to at most four audited process workers and rejects `--jobs`/`LAZY_TEST_JOBS` values outside 1–4. Static/isolated checks, PID-qualified live fixtures, and stable-repository readers run in separate phases; fixed-path/canonical-state checks remain serial. `--jobs=1` preserves the historical serial fail-fast path.

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

Progress output is intentionally not included in stdout JSON. It is emitted on stderr so automation can parse stdout as JSON while Pi/OMP and other runtime consumers can render progress without a Jcode-specific protocol.

When evidence is reused, the full-regression step status is `reused`, `fullRegression` remains true, and `evidenceReused` is true. This is a full-regression evidence reuse, not a fast-check substitution.

Markdown output is a compact human-readable summary of the same plan and step results.

## Implementation map

- Primary files:
  - `.lazy-harness/spec/platform/bounded-validation-governor.md` — this SDD contract.
  - `.lazy-harness/tests/bounded-validation-governor.md` — regression contract.
  - `.lazy-harness/tests/test-strategy.xml` — canonical fast/focused/standard/release and worker boundaries.
  - `.lazy-harness/scripts/validation-governor.py` — bounded plan builder/executor.
  - `$LAZY_RUNTIME_ROOT/state/validation-evidence-cache.json` — runtime-only validation evidence cache.
  - `.gitignore` — ignores the default runtime cache path.
  - `.lazy-harness/bin/lazy` — exposes `lazy validate`.
  - `.lazy-harness/scripts/self-test.py` — audited resource-phase process execution, serial fallback, and regression fixtures.
  - `.lazy-harness/ssot/capabilities.json` / `.lazy-harness/ssot/policies.json` — recommend-level bounded validation orchestration guidance.
  - `packages/lazy-harness-pi/prompts/lazy-harness.md` — edit-loop/final-boundary prompt guidance.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — `/lazy-check`, `/lazy-validate`, and explicit fresh `/lazy-test` commands.
  - `.lazy-harness/AGENTS.md` / `AGENTS.md` — compact global validation grammar.
  - `.lazy-harness/spec/platform/lazy-cli-entrypoint.md` — canonical CLI command list.
  - `.lazy-harness/spec/platform/fast-validation-tier.md` — related fast/static validation tier.
  - `.lazy-harness/planning/workflow-churn-reduction-plan.md` — measured churn, approved process-pool direction, and rollout evidence.
- Key symbols:
  - `validation-governor.py#main`
  - `validation-governor.py#build_result`
  - `validation-governor.py#plan_steps`
  - `validation-governor.py#run_step`
  - `validation-governor.py#emit_progress`
  - `validation-governor.py#workspace_fingerprint`
  - `validation-governor.py#dependency_fingerprint`
  - `validation-governor.py#toolchain_fingerprint`
  - `validation-governor.py#command_signature`
  - `validation-governor.py#is_full_regression_irrelevant_path`
  - `validation-governor.py#evidence_key`
  - `validation-governor.py#cached_step_result`
  - `validation-governor.py#store_step_result`
  - `self-test.py#run_check_captured`
  - `self-test.py#main`
  - `self-test.py#check_bounded_validation_governor_cli`
- Flow:
  1. Agent uses `lazy check` during mutation loops and focused validation only for changed behavior.
  2. After the final mutation, agent chooses one explicit standard/release plan; direct `lazy test` is reserved for an explicit fresh full boundary.
  3. Governor deduplicates commands and enforces a global budget.
  4. Fast static check runs normally.
  5. If a full-regression step appears, the governor fingerprints regression-relevant state while ignoring runtime/derived files and evidence-capsule bodies.
  6. Cache hit reuses full-regression evidence; cache miss or uncertainty runs `lazy test` and stores successful evidence.
  7. `lazy test` runs audited checks in bounded resource-separated process phases, then serializes fixed-path checks and emits output in registry order.
  8. Host-root, dependency, and toolchain signatures prevent cross-host or stale-environment cache reuse; release-grade validation requires explicit opt-in.
- Tests:
  - `python3 -m py_compile .lazy-harness/scripts/validation-governor.py`
  - `.lazy-harness/bin/lazy validate --plan fast --files .lazy-harness/fixtures/project-map-v2/example-node.json --format=json`
  - `.lazy-harness/bin/lazy validate --plan release --format=json` should fail without `--allow-release`.
  - `.lazy-harness/bin/lazy validate --plan release --dry-run --format=json` should list the release plan without executing it.
  - `.lazy-harness/bin/lazy validate --plan fast --format=json` should keep stdout JSON parseable and emit `LAZY_PROGRESS` on stderr.
  - `.lazy-harness/bin/lazy validate --plan standard --format=json` should store full-regression evidence on a miss, then reuse it on the same regression-relevant fingerprint.
  - evidence-only path classification should preserve cache reuse; source/test/spec/graph paths must remain fingerprint-relevant.
  - `.lazy-harness/bin/lazy validate --plan standard --evidence-cache=off --format=json` should never reuse evidence.
  - `python3 .lazy-harness/scripts/self-test.py --scope host --light --jobs 4` should run audited phases with deterministic registry-order output.
  - `python3 .lazy-harness/scripts/self-test.py --scope framework --jobs 1` remains the serial fallback.

## Cross-layer links

- TDD: `.lazy-harness/tests/bounded-validation-governor.md`
- SDD: `.lazy-harness/spec/platform/fast-validation-tier.md`
- SDD: `.lazy-harness/spec/platform/lazy-cli-entrypoint.md`
- Planning: `.lazy-harness/planning/workflow-churn-reduction-plan.md`
- SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`

## Discovery capture

- DDD: no domain/business model change.
- SDD: this record defines the new CLI contract.
- BDD: agent-visible validation behavior changes from ad hoc repeated full matrices to fast edit loops plus one final standard boundary.
- TDD: `.lazy-harness/tests/bounded-validation-governor.md` protects plan selection, capability/policy surfacing, evidence-only reuse, source/test misses, worker isolation, serial fallback, and bounded parallel execution.
- ADR: ADR 0016 is amended operationally: commit remains light, push remains full, while each self-test invocation may execute audited checks concurrently without weakening scope.
- SSOT: `bounded-validation-orchestration` is recommend-level; full regression remains `lazy test`, release readiness remains explicit and bounded.
