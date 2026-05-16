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

1. `.lazy-harness/bin/lazy` resolves the caller host root with `git rev-parse --show-toplevel` first.
2. It exports `LAZY_HOST_ROOT=<caller git root>` for delegated scripts.
3. Python validators (`doctor.py`, `self-test.py`) must prefer `LAZY_HOST_ROOT` over `__file__.resolve().parents[2]`.
4. If no caller git root with `.lazy-harness` exists, fallback to the script-location parent keeps direct framework execution working.
5. Subcommands must still execute from the resolved host root so relative paths are host-local.

## Non-goals

- Do not make downstream host app state part of the lazy-harness source repo.
- Do not follow sibling repos for host knowledge.
- Do not make symlink target checkout the default validation root when a caller worktree is present.

## Validation

Self-test must cover a temporary git worktree whose `.lazy-harness` is a symlink to another lazy-harness directory. Running `.lazy-harness/bin/lazy version` from that temp worktree must report the temp git root as `host_root`, and Python validators imported through the symlink must expose `ROOT == LAZY_HOST_ROOT`.

## Discovery capture

- DDD: none.
- SDD: this contract governs CLI/script root resolution.
- BDD: user-visible behavior is that PR worktree validation checks the PR worktree, not the primary checkout.
- TDD: `check_lazy_host_root_resolution` protects symlink/worktree root handling.
- ADR: no separate trade-off needed unless root resolution expands beyond git worktrees.
- SSOT: project identity still forbids treating downstream installed copies as source of truth.
- Planning: none.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/host-root-resolution.md` — this SDD contract.
  - `.lazy-harness/bin/lazy` — resolves caller git root and exports `LAZY_HOST_ROOT`.
  - `.lazy-harness/scripts/doctor.py` — uses `LAZY_HOST_ROOT` before script physical path.
  - `.lazy-harness/scripts/self-test.py` — uses `LAZY_HOST_ROOT` before script physical path and includes regression coverage.
- Key symbols:
  - `LAZY_HOST_ROOT` — environment variable carrying caller host root.
  - `check_lazy_host_root_resolution` (`.lazy-harness/scripts/self-test.py`) — symlink/worktree regression test.
- Flow:
  1. User invokes `lazy` from a git worktree.
  2. Launcher resolves caller git root and exports `LAZY_HOST_ROOT`.
  3. Python validators use the env root for `ROOT` and `.lazy-harness` path calculations.
  4. Validation reads the intended worktree.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - SSOT: `.lazy-harness/ssot/project-identity.md`
  - SDD: `.lazy-harness/spec/platform/record-before-session-history.md`
- Machine index:
  - graph ids: `kg_sdd_host_root_resolution`
  - generated index key: `pending until implementation-index generator exists`
