# TDD — lazy-sync False-Positive "Already in sync" on Dirty Source

- Layer: TDD (regression)
- Date: 2026-05-17
- Related: spec/lazy-sync-drift-detection.md, ADR 0035, tests/tdd-cross-verify-forcegate-loop.md

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
