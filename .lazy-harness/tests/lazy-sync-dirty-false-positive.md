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
  - drift detection wrongly reports "Already in sync", or a rollout must avoid any host knowledge JSONL mutation
- Must:
  - detect a dirty source working tree before the SHA-equality fast path and return `ahead` (dirty), letting `--force` proceed
  - make `--skip-knowledge-seeds` preserve every host `knowledge/*.jsonl` byte and avoid conflict sidecars while normal Category A and registry sync continues
- Must not:
  - report `equal: Already in sync` and skip sync when the source has uncommitted `.lazy-harness` changes
  - merge knowledge rows or create `*.conflicts.jsonl` when the explicit opt-out is active
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

## Knowledge seed opt-out regression (2026-07-23)

A host rollout exposed that the normal, intentional seed merge would append framework rows and record conflicts in host-owned `knowledge/graph.jsonl` and `knowledge/candidates.jsonl`. The rollout required a per-run exception that updates framework Category A without mutating those stores.

The sandboxed `check_lazy_sync_prunes_stale_managed_files` fixture now protects both modes:

1. Seed graph and candidate JSONL files with host-only rows.
2. Run `lazy-sync --force --quiet --skip-knowledge-seeds`.
3. Require graph/candidate byte identity and zero `knowledge/*.conflicts.jsonl` sidecars.
4. Require normal managed-file prune/copy, `knowledge/README.md`, and capability seed merge to continue.
5. Run the default sync and require source knowledge seeds to merge while host rows survive.

The opt-out is per run. It does not disable capability/policy registry merges, and the source marker still advances.

## Fix

`.lazy-harness/scripts/lazy-sync.ts`:

- `isSourceWorkingTreeDirty(sourceRoot)` runs `git status --porcelain -- .lazy-harness` in the source repo.
- `detectDrift` checks the dirty source before returning the SHA-equality fast path.
- `parseArgs` exposes `--skip-knowledge-seeds` as an explicit Boolean option.
- `syncCategoryA(..., skipKnowledgeSeeds)` bypasses only `knowledge/*.jsonl`; it still copies non-JSONL knowledge files and syncs all other Category A/registry items.
- `--force` still short-circuits the existing `ahead/divergent` error path.

## Manual verification log (2026-05-17)

- `bun .lazy-harness/scripts/lazy-sync.ts --target ~/dev/medivance` (no force) → `Drift] ahead: ... dirty / Error: drift detected (ahead). Use --force to proceed.`
- `bun .lazy-harness/scripts/lazy-sync.ts --target ~/dev/medivance --force` → `[Summary] updated: 4 / ✓ Synced.`

## Non-coverage

The dirty-source regression itself is not yet sandboxed, so this record remains `needs-review`. The adjacent knowledge-seed opt-out is automated in `check_lazy_sync_prunes_stale_managed_files`; that fixture does not claim to close the dirty-tree coverage gap.

## Implementation map

- Status: `needs-review`
- Primary files:
  - `.lazy-harness/tests/lazy-sync-dirty-false-positive.md` — regression record and manual reproduction contract.
  - `.lazy-harness/scripts/lazy-sync.ts` — drift detection implementation and sync entrypoint.
  - `.lazy-harness/spec/lazy-sync-drift-detection.md` — SDD contract for dirty source tree detection and force semantics.
- Key symbols:
  - `isSourceWorkingTreeDirty` (`.lazy-harness/scripts/lazy-sync.ts`) — detects uncommitted framework changes.
  - `detectDrift` (`.lazy-harness/scripts/lazy-sync.ts`) — prevents a dirty source from returning `equal`.
  - `parseArgs` (`.lazy-harness/scripts/lazy-sync.ts`) — accepts the explicit knowledge-seed opt-out.
  - `syncCategoryA` (`.lazy-harness/scripts/lazy-sync.ts`) — skips only knowledge JSONL merges when requested; default merge and other Category A behavior remain unchanged.
  - `main` (`.lazy-harness/scripts/lazy-sync.ts`) — reports the mode, passes the opt-out, and still updates the marker.
- Flow:
  1. User edits source or prepares a host rollout.
  2. Drift logic rejects an unforced dirty/ahead source.
  3. A normal forced sync merges missing knowledge seeds.
  4. A forced sync with `--skip-knowledge-seeds` bypasses knowledge JSONL while all other Category A/registry work continues.
- Tests / protection:
  - Manual dirty-source recipe in this record remains the direct dirty-tree protection.
  - `.lazy-harness/spec/lazy-sync-drift-detection.md#verification` mirrors expected commands and outcomes.
  - `.lazy-harness/scripts/self-test.py#check_lazy_sync_prunes_stale_managed_files` protects opt-out byte identity, no conflict sidecars, continued capability merge, marker advancement, and unchanged default knowledge merge.
  - `.lazy-harness/evidence/2026-07-23-knowledge-safe-placement-rollout.md` records source validation, independent review, and byte-safe rollout to the three approved dogfood hosts.
  - No sandboxed automated dirty-source fixture exists yet; keep this map `needs-review` until one is added.
- Layer completeness:
  - SDD: independent delta in `.lazy-harness/spec/lazy-sync-drift-detection.md` defines the new CLI/merge contract.
  - BDD: no independent delta; this is framework CLI safety, not a product-visible workflow.
  - SSOT: no independent delta; host ownership and marker/registry source-of-truth paths are unchanged.
  - DDD: no independent delta; no domain vocabulary or business invariant changed.

## Discovery capture

- DDD: none; the sync flag adds no business/domain rule.
- SDD: updated in `.lazy-harness/spec/lazy-sync-drift-detection.md` for the opt-in CLI and merge boundary.
- BDD: none; no product-visible user workflow changed.
- TDD: updated in this record and `.lazy-harness/scripts/self-test.py`.
- ADR: none; the approved narrow opt-out fits the existing Category A sync architecture without a new architectural trade-off.
- SSOT: none; knowledge ownership, marker ownership, manifest ownership, and registry ownership remain unchanged.
- Planning: the separate implementation-map ownership drift discovered during rollout is captured in `.lazy-harness/planning/2026-07-23-framework-implementation-map-drift-handoff.md`; no skip-flag-specific backlog remains.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/lazy-sync-drift-detection.md`
  - TDD: `.lazy-harness/tests/lazy-sync-dirty-false-positive.md`
- Machine index:
  - graph ids: `kg_lazy_sync_dirty_false_positive_source`, `kg_lazy_sync_dirty_false_positive_tdd`
  - generated index key: `pending`
