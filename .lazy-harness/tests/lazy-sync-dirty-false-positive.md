# TDD — lazy-sync False-Positive "Already in sync" on Dirty Source

- Layer: TDD (regression)
- Date: 2026-05-17
- Related: spec/lazy-sync-drift-detection.md, ADR 0035, tests/tdd-cross-verify-forcegate-loop.md

## Rule digest

- Status: needs-review
- Layer: TDD
- Scope: framework-global
- Aliases:
  - sync 오탐
  - dirty false positive
  - 싱크 회귀
- Applies when:
  - running `lazy-sync` from a source repo with uncommitted `.lazy-harness` changes
  - drift detection wrongly reports "Already in sync", or editing lazy-sync drift logic
- Must:
  - detect a dirty source working tree before the SHA-equality fast path and return `ahead` (dirty), letting `--force` proceed
- Must not:
  - report `equal: Already in sync` and skip sync when the source has uncommitted `.lazy-harness` changes
- Record completion:
  - add a sandboxed automated dirty-source fixture, then update this record's status from `needs-review`
- Related records:
  - `.lazy-harness/spec/lazy-sync-drift-detection.md`
  - `.lazy-harness/tests/tdd-cross-verify-forcegate-loop.md`

## Failure observed

Workflow:

1. Edit `.lazy-harness/scripts/tdd-cross-verify.ts` in source repo (`~/dev/lazy-harness`).
2. Do NOT commit.
3. Run `bun .lazy-harness/scripts/lazy-sync.ts --from ~/dev/lazy-harness --target ~/dev/medivance --force`.

Expected: host receives the new `tdd-cross-verify.ts` (containing the `forceGate = questions.length > 0` fix).

Actual (pre-fix): drift status reported `equal: Already in sync`, sync phase skipped, host kept the buggy version. AI had to `cp` files manually to break the loop on the medivance side.

Root cause: `detectDrift()` only compared the source HEAD commit SHA to the host marker SHA. Working-tree changes in the source repo were invisible. When the user edited but did not commit the script, both SHAs matched and `equal` short-circuited the sync.

## Regression case

```bash
cd /home/lazydino/dev/lazy-harness

# 1. Mutate a tracked file in source without committing.
echo "// regression touch $(date)" >> .lazy-harness/scripts/lazy-sync.ts

# 2. Run sync against any initialized host.
bun .lazy-harness/scripts/lazy-sync.ts --target ~/dev/medivance 2>&1 | head -5
# Pass criterion:
#   [Drift] ahead: Source working-tree has uncommitted .lazy-harness changes (dirty)
#   Error: drift detected (ahead). Use --force to proceed.

# 3. --force should still let it through.
bun .lazy-harness/scripts/lazy-sync.ts --target ~/dev/medivance --force 2>&1 | tail -5
# Pass criterion:
#   [Summary]
#     updated:   >= 1

# 4. Restore.
git checkout -- .lazy-harness/scripts/lazy-sync.ts
```

If step 2 reports `equal: Already in sync`, the regression has returned.

## Fix

`.lazy-harness/scripts/lazy-sync.ts`:

- New helper `isSourceWorkingTreeDirty(sourceRoot)` runs `git status --porcelain -- .lazy-harness` in the source repo.
- In `detectDrift`, after the SHA equality check, call the helper. If dirty, return `ahead` with message `Source working-tree has uncommitted .lazy-harness changes (dirty)` instead of `equal`.
- `--force` short-circuits the existing `ahead/divergent` error path, so no additional gate changes were needed.

## Manual verification log (2026-05-17)

- `bun .lazy-harness/scripts/lazy-sync.ts --target ~/dev/medivance` (no force) → `Drift] ahead: ... dirty / Error: drift detected (ahead). Use --force to proceed.`
- `bun .lazy-harness/scripts/lazy-sync.ts --target ~/dev/medivance --force` → `[Summary] updated: 4 / ✓ Synced.`

## Non-coverage

This regression is not yet wired into `self-test.py`. Doing so would require a sandboxed source/host pair so the test does not mutate the live repos. Left as future work; for now the manual recipe above is the contract.

## Implementation map

- Status: `needs-review`
- Primary files:
  - `.lazy-harness/tests/lazy-sync-dirty-false-positive.md` — regression record and manual reproduction contract.
  - `.lazy-harness/scripts/lazy-sync.ts` — drift detection implementation and sync entrypoint.
  - `.lazy-harness/spec/lazy-sync-drift-detection.md` — SDD contract for dirty source tree detection and force semantics.
- Key symbols:
  - `isSourceWorkingTreeDirty` (`.lazy-harness/scripts/lazy-sync.ts`) — runs `git status --porcelain -- .lazy-harness` in the source repo and returns true for uncommitted framework changes.
  - `detectDrift` (`.lazy-harness/scripts/lazy-sync.ts`) — checks matching source/host SHAs and returns `ahead` with the dirty-source message when the source worktree is dirty.
  - `main` (`.lazy-harness/scripts/lazy-sync.ts`) — logs drift status, exits on `ahead` without `--force`, and proceeds to sync when forced.
- Flow:
  1. User edits a source `.lazy-harness` file without committing.
  2. `detectDrift` sees matching SHAs but calls `isSourceWorkingTreeDirty` before the `equal` fast-path.
  3. Dirty source returns `ahead`, preventing silent “Already in sync” unless `--force` is supplied.
  4. With `--force`, `main` proceeds through the copy/prune/marker update flow.
- Tests / protection:
  - Manual regression recipe in this record remains the direct dirty-source protection.
  - `.lazy-harness/spec/lazy-sync-drift-detection.md#verification` mirrors the manual expected commands and outcomes.
  - `.lazy-harness/scripts/self-test.py#check_lazy_sync_prunes_stale_managed_files` protects adjacent lazy-sync managed prune/seed-merge behavior, not this dirty-source regression.
  - No sandboxed automated dirty-source fixture exists yet; keep this map `needs-review` until one is added.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/lazy-sync-drift-detection.md`
  - TDD: `.lazy-harness/tests/lazy-sync-dirty-false-positive.md`
- Machine index:
  - graph ids: `kg_lazy_sync_dirty_false_positive_source`, `kg_lazy_sync_dirty_false_positive_tdd`
  - generated index key: `pending`
