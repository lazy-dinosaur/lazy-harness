# Git Hook Environment Isolation Regression

Status: accepted
Layer: TDD
Date: 2026-05-16
Related SDD: `.lazy-harness/spec/platform/host-root-resolution.md`

## Regression

A push command can execute pre-push with `GIT_DIR` and `GIT_WORK_TREE` in the environment. If lazy-harness validation inherits those variables, `self-test.py` temporary git fixtures resolve the outer repository instead of their temp repository. The observed failure was `check_lazy_host_root_resolution` reporting the real worktree as `host_root` while the fixture expected `/tmp/lazy_host_root_*`.

## Required protection

- Pre-push must invoke validation with `LAZY_HOST_ROOT=$REPO_ROOT`.
- Pre-push must clear `GIT_DIR` and `GIT_WORK_TREE` for `.lazy-harness/bin/lazy test` and direct `self-test.py` fallback.
- `.lazy-harness/bin/lazy` must prefer valid `LAZY_HOST_ROOT` over git discovery.
- Self-test must include a poisoned git-env fixture where `GIT_DIR` / `GIT_WORK_TREE` point at another repository while `LAZY_HOST_ROOT` points at the temp host.
- Self-test lifecycle hook fixtures must redirect layer-impact validation appends to a temp `LAZY_HARNESS_VALIDATIONS_FILE` so `.lazy-harness/logs/validations.jsonl` stays clean.

## Layer completeness gate

- DDD: no domain/business terminology impact.
- SDD: host-root resolution contract updated in `.lazy-harness/spec/platform/host-root-resolution.md`.
- BDD: user-visible push behavior should no longer fail because self-test fixture reads the outer push env.
- TDD: this record and `check_lazy_host_root_resolution` / `check_pre_push_uses_canonical_lazy_cli` protect the regression.
- ADR: existing ADR 0022/0026/0027 cover framework-owned validation, scope separation, and standalone source-of-truth. No new trade-off decision.
- SSOT: no schema/config/env source-of-truth change beyond the SDD env-boundary contract.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/pre-push.sh` — sets `LAZY_HOST_ROOT=$REPO_ROOT` and clears `GIT_DIR` / `GIT_WORK_TREE` for validation subprocesses.
  - `.lazy-harness/bin/lazy` — prefers valid `LAZY_HOST_ROOT` before git worktree discovery.
  - `.lazy-harness/scripts/self-test.py` — asserts pre-push env clearing contract and poisoned git-env root resolution, and redirects hook validation logs during fixtures.
  - `.lazy-harness/scripts/layer-impact-gate.ts` — honors `LAZY_HARNESS_VALIDATIONS_FILE` for append-validation output.
  - `.lazy-harness/spec/platform/host-root-resolution.md` — SDD contract for host-root/env behavior.
- Key symbols:
  - `check_pre_push_uses_canonical_lazy_cli`
  - `check_lazy_host_root_resolution`
  - `LAZY_HOST_ROOT`
  - `LAZY_HARNESS_VALIDATIONS_FILE`
  - `GIT_DIR` / `GIT_WORK_TREE`
- Flow:
  1. Git invokes pre-push with potential hook env.
  2. Hook resolves repo root, exports `LAZY_HOST_ROOT`, and clears `GIT_DIR` / `GIT_WORK_TREE` for validation.
  3. Lazy CLI validates the explicit host root.
  4. Python validators and temp git fixtures no longer inherit outer git metadata.
  5. Self-test hook fixtures append validation observations to temporary JSONL files, not the tracked validation log.
- Tests / protection:
  - `GIT_DIR=$(git rev-parse --git-dir) GIT_WORK_TREE=$(git rev-parse --show-toplevel) .lazy-harness/bin/lazy test`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/host-root-resolution.md`
  - ADR: `.lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md`
  - ADR: `.lazy-harness/decisions/0026-doctor-self-test-scope-separation.md`
  - ADR: `.lazy-harness/decisions/0027-standalone-source-of-truth-repository.md`
- Machine index:
  - graph ids: `kg_tdd_git_hook_env_isolation`, `kg_prepush_clears_git_env`, `kg_test_git_env_isolation`
  - generated index key: `pending until implementation-index generator exists`
