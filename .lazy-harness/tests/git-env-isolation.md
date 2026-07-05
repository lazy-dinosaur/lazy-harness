# Git Hook Environment Isolation Regression

Status: accepted
Layer: TDD
Date: 2026-05-16
Related SDD: `.lazy-harness/spec/platform/host-root-resolution.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - git 환경 격리
  - env isolation
- Applies when:
  - a git hook or wrapper runs lazy validation with `GIT_DIR`/`GIT_WORK_TREE` in the environment
  - self-test builds temp git fixtures or host-root resolution must ignore inherited git env
- Must:
  - pre-commit/pre-push set `LAZY_HOST_ROOT` and clear `GIT_DIR`/`GIT_WORK_TREE` for validation subprocesses
  - lazy CLI prefers valid `LAZY_HOST_ROOT` over git discovery; self-test strips inherited git/runtime env from its process and children
- Must not:
  - let temp git fixtures inherit outer git hook env and resolve or mutate the caller repository
- Record completion:
  - changes to host-root/env boundary update this TDD plus the host-root-resolution SDD
- Related records:
  - `.lazy-harness/spec/platform/host-root-resolution.md`
  - `.lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md`
  - `.lazy-harness/decisions/0026-doctor-self-test-scope-separation.md`
  - `.lazy-harness/decisions/0027-standalone-source-of-truth-repository.md`

## Regression

A git hook or wrapper can execute validation with `GIT_DIR` and `GIT_WORK_TREE` in the environment. If lazy-harness validation inherits those variables, `self-test.py` temporary git fixtures resolve the outer repository instead of their temp repository. Observed failures include `check_lazy_host_root_resolution` reporting the real worktree as `host_root` while the fixture expected `/tmp/lazy_host_root_*`, and nested self-test git fixtures mutating or reading the outer repository configuration such as `core.bare` when hook env leaks into temp repos.

## Required protection

- Pre-commit and pre-push must invoke validation with `LAZY_HOST_ROOT=$REPO_ROOT`.
- Pre-commit and pre-push must clear `GIT_DIR` and `GIT_WORK_TREE` for `.lazy-harness/bin/lazy test` and direct `self-test.py` fallback.
- `.lazy-harness/bin/lazy` must prefer valid `LAZY_HOST_ROOT` over git discovery.
- Self-test must include a poisoned git-env fixture where `GIT_DIR` / `GIT_WORK_TREE` point at another repository while `LAZY_HOST_ROOT` points at the temp host. The fixture must also assert that `self-test.py` clears inherited git hook env from its own process and child helper envs, while preserving explicit sandbox overrides.
- Self-test lifecycle hook fixtures must redirect layer-impact validation appends to a temp `LAZY_HARNESS_VALIDATIONS_FILE` so `.lazy-harness/logs/validations.jsonl` stays clean.

## Layer completeness gate

- DDD: no domain/business terminology impact.
- SDD: host-root resolution contract updated in `.lazy-harness/spec/platform/host-root-resolution.md`.
- BDD: user-visible commit/push behavior should no longer fail or mutate the caller repository because self-test fixtures read the outer hook env.
- TDD: this record and `check_lazy_host_root_resolution` / `check_pre_push_uses_canonical_lazy_cli` protect the regression, including self-test child env cleanup and temp git fixture isolation.
- ADR: existing ADR 0022/0026/0027 cover framework-owned validation, scope separation, and standalone source-of-truth. No new trade-off decision.
- SSOT: no schema/config/env source-of-truth change beyond the SDD env-boundary contract.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/pre-commit-guard.sh` — sets `LAZY_HOST_ROOT=$REPO_ROOT` and clears `GIT_DIR` / `GIT_WORK_TREE` for commit validation subprocesses.
  - `.lazy-harness/hooks/pre-push.sh` — sets `LAZY_HOST_ROOT=$REPO_ROOT` and clears `GIT_DIR` / `GIT_WORK_TREE` for validation subprocesses.
  - `.lazy-harness/bin/lazy` — prefers valid `LAZY_HOST_ROOT` before git worktree discovery.
  - `.lazy-harness/scripts/self-test.py` — clears inherited lazy runtime and git hook env, asserts pre-commit/pre-push env clearing contract and poisoned git-env root resolution, runs temp git fixtures with clean env, and redirects hook validation logs during fixtures.
  - `.lazy-harness/scripts/layer-impact-gate.ts` — honors `LAZY_HARNESS_VALIDATIONS_FILE` for append-validation output.
  - `.lazy-harness/spec/platform/host-root-resolution.md` — SDD contract for host-root/env behavior.
- Key symbols:
  - `check_pre_push_uses_canonical_lazy_cli`
  - `check_lazy_host_root_resolution`
  - `LAZY_HOST_ROOT`
  - `LAZY_HARNESS_VALIDATIONS_FILE`
  - `INHERITED_ENV_KEYS_TO_CLEAR`
  - `env_without_lazy_runtime`
  - `GIT_DIR` / `GIT_WORK_TREE`
- Flow:
  1. Git invokes pre-commit/pre-push or a wrapper invokes lazy validation with potential hook env.
  2. Hook resolves repo root, exports `LAZY_HOST_ROOT`, and clears `GIT_DIR` / `GIT_WORK_TREE` for validation.
  3. Lazy CLI validates the explicit host root.
  4. `self-test.py` clears inherited lazy runtime and git hook variables from its process and uses `env_without_lazy_runtime` for temp git/helper subprocesses.
  5. Python validators and temp git fixtures no longer inherit outer git metadata.
  6. Self-test hook fixtures append validation observations to temporary JSONL files, not the tracked validation log.
- Tests / protection:
  - `GIT_DIR=$(git rev-parse --absolute-git-dir) GIT_WORK_TREE=$(git rev-parse --show-toplevel) .lazy-harness/bin/lazy test --scope framework`
  - poisoned external repo env with `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, and `GIT_COMMON_DIR` set while running `.lazy-harness/bin/lazy test --scope framework`; source `core.bare` / `core.worktree` must stay unchanged
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/host-root-resolution.md`
  - ADR: `.lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md`
  - ADR: `.lazy-harness/decisions/0026-doctor-self-test-scope-separation.md`
  - ADR: `.lazy-harness/decisions/0027-standalone-source-of-truth-repository.md`
- Machine index:
  - graph ids: `kg_tdd_git_hook_env_isolation`, `kg_prepush_clears_git_env`, `kg_test_git_env_isolation`
  - generated index key: `pending until implementation-index generator exists`

## 2026-06-04 Self-test child git env hardening

Status: accepted

A second reproduction showed that hook-level `env -u GIT_DIR -u GIT_WORK_TREE` is necessary but not sufficient. `self-test.py` also constructs many temp repositories and helper subprocesses, and some of them inherited `os.environ` directly. If a wrapper or interrupted hook leaves `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, or `GIT_COMMON_DIR` in the environment, nested temp git fixtures can still resolve the outer repository.

Additional protection:

- `self-test.py` defines `INHERITED_ENV_KEYS_TO_CLEAR` for lazy runtime and git hook variables.
- On startup, `self-test.py` removes those inherited keys from `os.environ` so subprocesses without explicit env no longer inherit poisoned git state.
- `env_without_lazy_runtime()` now strips those inherited keys first and then applies explicit overrides. This preserves intended fixture overrides such as `LAZY_RUNTIME_ROOT` for sandbox tests.
- All self-test temp `git` subprocesses now pass `env=env_without_lazy_runtime()`.
- Hook/helper subprocess fixtures now use `env_without_lazy_runtime(LAZY_HOST_ROOT=...)` instead of raw `{**os.environ, ...}`.
- `check_lazy_host_root_resolution` asserts both host-root precedence and self-test child env cleanup under a poisoned external git env.

Validation:

```bash
python3 -m py_compile .lazy-harness/scripts/self-test.py
GIT_DIR=<external .git> GIT_WORK_TREE=<external worktree> GIT_INDEX_FILE=<external index> GIT_COMMON_DIR=<external .git> LAZY_HOST_ROOT=$PWD .lazy-harness/bin/lazy test --scope framework
```

Result on 2026-06-04: framework self-test passed (`ran=77`, `skipped=0`) and source `core.bare` / `core.worktree` were unchanged.

Discovery capture:

- DDD: none.
- SDD: host-root/env contract updated in `.lazy-harness/spec/platform/host-root-resolution.md`.
- BDD: commit/push validation should no longer mutate or inspect the outer repo through leaked git env.
- TDD: this record and `check_lazy_host_root_resolution` protect the regression.
- ADR: no new decision.
- SSOT: no schema/config source-of-truth change beyond inherited env boundary.
- Planning: none.
