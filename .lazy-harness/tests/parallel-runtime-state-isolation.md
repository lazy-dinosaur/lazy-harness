# Parallel Runtime State Isolation Regression

Status: accepted
Layer: TDD
Date: 2026-06-03
Related SDD: `.lazy-harness/spec/platform/runtime-and-shared-state.md`
Related SSOT: `.lazy-harness/ssot/runtime-and-shared-state.md`
Related ADR: `.lazy-harness/decisions/0002-conflict-resolution-protocol.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - 병렬 상태 격리
  - runtime isolation
- Applies when:
  - parallel agents/sessions or a secondary worktree symlink `.lazy-harness` to a primary checkout
  - concurrent commit/validation in the same worktree, or routing runtime journals/caches/logs
- Must:
  - write packet journals, read-debt checks, timing/compare/shadow logs, and `open-gates.json` to the caller's session runtime root
  - dedupe identical canonical JSONL payloads (including idless rows) and record same-id conflicts in `*.conflicts.jsonl`; use a worktree-local git-action lock for pre-commit/pre-push
- Must not:
  - write runtime state under the symlink target `.lazy-harness/state`, causing false cross-session contamination
- Record completion:
  - changes to runtime-root routing or conflict handling update this TDD plus the runtime-and-shared-state SDD and SSOT
- Related records:
  - `.lazy-harness/spec/platform/runtime-and-shared-state.md`
  - `.lazy-harness/ssot/runtime-and-shared-state.md`
  - `.lazy-harness/decisions/0002-conflict-resolution-protocol.md`

## Regression

When a secondary git worktree symlinks `.lazy-harness` to a primary checkout, lifecycle hooks used to write these runtime file classes under the symlink target's legacy state/log directories:

- search/read-debt journals
- Record Decision shadow journals
- open-gate caches
- hook timing logs

This made multiple agents/sessions look contaminated even when product git indexes were isolated. A second failure mode is same-worktree concurrent commit/validation: two agents can launch `git commit`/pre-commit validation at the same time, interleaving hook logs and diagnosis.

## Required protection

- Message received packet journals must land in the caller worktree/session runtime root, not the symlink target `.lazy-harness/state`.
- Tool-before read-debt checks must read the same session runtime root.
- Response-completed timing/compare/record-decision shadow logs must land in runtime roots.
- Gate-fingerprint `open-gates.json` must be runtime-local.
- Shared durable JSONL append helpers must dedupe identical canonical JSON payloads, including idless rows, and record same-id/different-payload conflicts in `*.conflicts.jsonl`.
- Pre-commit/pre-push must use a worktree-local git-action lock to avoid concurrent validation in the same worktree.

## Layer completeness

- SDD: `.lazy-harness/spec/platform/runtime-and-shared-state.md` defines the contract.
- BDD: user-visible effect is that parallel agents can work without false contamination warnings from shared runtime state.
- SSOT: `.lazy-harness/ssot/runtime-and-shared-state.md` owns the root/path source of truth.
- DDD: no domain/business terminology impact.
- ADR: ADR 0002 already covers no silent conflict handling.

## Implementation map

- Primary files:
  - `.lazy-harness/scripts/runtime-paths.ts`
  - `.lazy-harness/hooks/lifecycle/helpers/runtime_paths.py`
  - `.lazy-harness/hooks/lifecycle/helpers/runtime-paths.sh`
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh`
  - `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh`
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh`
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py`
  - `.lazy-harness/hooks/lifecycle/helpers/check-record-decision-shadow.py`
  - `.lazy-harness/hooks/lifecycle/helpers/gate-fingerprint.sh`
  - `.lazy-harness/scripts/gate-state.ts`
  - `.lazy-harness/hooks/pre-commit-guard.sh`
  - `.lazy-harness/hooks/pre-push.sh`
  - `.lazy-harness/scripts/self-test.py`
- Test symbols:
  - `check_parallel_runtime_state_isolation`
  - `check_shared_jsonl_conflict_visible` protects TypeScript/Python helper dedupe for idless identical payloads and same-id conflict visibility.
