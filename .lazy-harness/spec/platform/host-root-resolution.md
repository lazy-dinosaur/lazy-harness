# Host Root Resolution for Symlinked Worktrees

Status: accepted
Layer: SDD
Date: 2026-05-16
Related SSOT: `.lazy-harness/ssot/project-identity.md`
Related SDD: `.lazy-harness/spec/platform/record-before-session-history.md`

## Purpose

Lazy-harness commands must validate the host worktree where the user invoked the command, not the physical checkout that owns a symlinked `.lazy-harness` script file.

This matters for PR/worktree flows where `.lazy-harness` or `.jcode/harness/05-lazy-harness.md` can resolve through symlinks to another checkout.

## Bug pattern

```text
user runs pre-push / lazy test in PR worktree
  → .lazy-harness/bin/lazy resolves script physical path
  → doctor.py/self-test.py use pathlib.Path(__file__).resolve().parents[2]
  → ROOT becomes another checkout
  → validation reads wrong generated/source state
```

## Contract

1. `.lazy-harness/bin/lazy` prefers an explicit `LAZY_HOST_ROOT` when present and valid.
2. Without `LAZY_HOST_ROOT`, `.lazy-harness/bin/lazy` resolves the caller host root with `git rev-parse --show-toplevel`.
3. It exports `LAZY_HOST_ROOT=<resolved host root>` for delegated scripts.
4. Python validators (`doctor.py`, `self-test.py`) must prefer `LAZY_HOST_ROOT` over `__file__.resolve().parents[2]`.
5. Pre-push must set `LAZY_HOST_ROOT=$REPO_ROOT` and clear `GIT_DIR` / `GIT_WORK_TREE` before invoking lazy-harness validation, because Git hook env can poison nested temp git fixtures.
6. Lifecycle hooks must prefer `LAZY_HOST_ROOT` before `git rev-parse --show-toplevel`, because some hook/test contexts can make git refuse worktree discovery.
7. If no caller git root with `.lazy-harness` exists, fallback to the script-location parent keeps direct framework execution working.
8. Subcommands and hooks must still execute from the resolved host root so relative paths are host-local.

## Non-goals

- Do not make downstream host app state part of the lazy-harness source repo.
- Do not follow sibling repos for host knowledge.
- Do not make symlink target checkout the default validation root when a caller worktree is present.

## Validation

Self-test must cover a temporary git worktree whose `.lazy-harness` is a symlink to another lazy-harness directory. Running `.lazy-harness/bin/lazy version` from that temp worktree must report the temp git root as `host_root`, and Python validators imported through the symlink must expose `ROOT == LAZY_HOST_ROOT`. The regression must include inherited `GIT_DIR` / `GIT_WORK_TREE` values pointing at another repository, with `LAZY_HOST_ROOT` taking precedence.

## Discovery capture

- DDD: none.
- SDD: this contract governs CLI/script root resolution and pre-push validation environment boundaries.
- BDD: user-visible behavior is that PR worktree validation checks the PR worktree, not the primary checkout, and push does not fail from leaked git fixture env.
- TDD: `check_lazy_host_root_resolution` protects symlink/worktree root handling and inherited git-env isolation; `check_pre_push_uses_canonical_lazy_cli` protects pre-push env clearing; `check_tool_execute_before_hook` protects hook deny behavior through `LAZY_HOST_ROOT`.
- ADR: no separate trade-off needed unless root resolution expands beyond git worktrees.
- SSOT: project identity still forbids treating downstream installed copies as source of truth.
- Planning: none.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/host-root-resolution.md` — this SDD contract.
  - `.lazy-harness/bin/lazy` — prefers explicit `LAZY_HOST_ROOT`, otherwise resolves caller git root and exports `LAZY_HOST_ROOT`.
  - `.lazy-harness/hooks/pre-push.sh` — sets `LAZY_HOST_ROOT=$REPO_ROOT` and clears inherited git hook env for validation.
  - `.lazy-harness/scripts/doctor.py` — uses `LAZY_HOST_ROOT` before script physical path.
  - `.lazy-harness/scripts/self-test.py` — uses `LAZY_HOST_ROOT` before script physical path and includes regression coverage.
  - `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` — uses `LAZY_HOST_ROOT` before git root discovery.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — uses `LAZY_HOST_ROOT` before git root discovery.
- Key symbols:
  - `LAZY_HOST_ROOT` — environment variable carrying caller host root.
  - `GIT_DIR` / `GIT_WORK_TREE` — git hook variables that must not leak into lazy-harness nested fixture subprocesses.
  - `check_lazy_host_root_resolution` (`.lazy-harness/scripts/self-test.py`) — symlink/worktree and inherited git-env regression test.
  - `check_pre_push_uses_canonical_lazy_cli` (`.lazy-harness/scripts/self-test.py`) — pre-push canonical CLI and git-env clearing contract test.
- Flow:
  1. User invokes `lazy` from a git worktree or Git invokes `pre-push` with hook env.
  2. Pre-push computes `REPO_ROOT`, sets `LAZY_HOST_ROOT`, and clears `GIT_DIR` / `GIT_WORK_TREE` for validation subprocesses.
  3. Launcher prefers `LAZY_HOST_ROOT`, otherwise resolves caller git root and exports `LAZY_HOST_ROOT`.
  4. Python validators use the env root for `ROOT` and `.lazy-harness` path calculations.
  5. Lifecycle hooks use the same env root before asking git for the worktree.
  6. Validation and gates read the intended worktree, while nested temp git fixtures are isolated from the outer push env.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `GIT_DIR=$(git rev-parse --git-dir) GIT_WORK_TREE=$(git rev-parse --show-toplevel) .lazy-harness/bin/lazy test`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - SSOT: `.lazy-harness/ssot/project-identity.md`
  - SDD: `.lazy-harness/spec/platform/record-before-session-history.md`
- Machine index:
  - graph ids: `kg_sdd_host_root_resolution`
  - generated index key: `pending until implementation-index generator exists`
