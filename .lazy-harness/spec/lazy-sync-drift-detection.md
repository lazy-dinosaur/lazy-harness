# Spec — lazy-sync Drift Detection Contract

- Layer: SDD
- Date: 2026-05-17
- Related: scripts/lazy-sync.ts, ADR 0035 (queue-close mandate), tests/tdd-cross-verify-forcegate-loop.md

## Purpose

`lazy-sync` copies framework files (`scripts/`, `hooks/`, `schemas/`, `triggers/`, `manifests/`) from a canonical source repo (`/home/lazydino/dev/lazy-harness`) to host copies (e.g. `/path/to/host-project-a/.lazy-harness/`). Its drift detector must answer one question: "is the host out of date relative to the source?"

## Contract

`detectDrift(sourceRoot, targetRoot) → DriftStatus`:

| Status      | Trigger                                                          | Default action  | --force action     |
|-------------|------------------------------------------------------------------|-----------------|--------------------|
| `equal`     | host marker SHA == source HEAD SHA **AND** source tree is clean  | skip sync       | force sync         |
| `ahead`     | source HEAD ancestor-of host, OR source HEAD == host with **dirty source tree** | error (exit 2) | force sync         |
| `behind`    | host marker SHA ancestor-of source HEAD                          | run sync        | run sync           |
| `divergent` | neither side is ancestor                                         | error (exit 2)  | force sync         |
| `unknown`   | missing marker or unreadable git                                 | warn            | force sync         |

### Dirty-tree rule (added 2026-05-17)

If `git status --porcelain -- .lazy-harness` in the source repo is non-empty, the detector reports `ahead` with message `Source working-tree has uncommitted .lazy-harness changes (dirty)`, even when the marker SHA matches source HEAD.

Rationale: the previous implementation only compared committed SHAs, so a workflow of "edit `scripts/foo.ts` in source repo, immediately run lazy-sync to host" silently reported `Already in sync` and skipped the copy step. The host stayed stale until the source change was committed.

### --force semantics

`--force` overrides any non-`equal` drift status, including the new `ahead-dirty` variant. With `--force`, lazy-sync always proceeds to the file-copy phase. Without `--force`, only `behind` runs sync automatically; everything else exits with code 2.

### Managed directory prune and local wiring refresh (added 2026-06-02)

For Category A manifest directory entries, `lazy-sync` must remove stale destination files that still match the managed `glob`/`exclude` rules but no longer exist in the source directory. This prevents renamed or deleted framework fixtures from remaining in downstream hosts as false context.

Exception: `knowledge/` JSONL files are host-local append-only stores. They are seed-merged, not overwritten or pruned: missing source seed rows are appended to the host file, while host-local graph/candidate rows are preserved.

After file sync, `installJcodeWiring` must refresh lazy-harness managed blocks in `.jcode/config.toml` when their marker comments are present. User-owned config content remains preserved, but managed hook blocks should receive updated framework wording/commands instead of staying stale forever.

## Implementation map

- **Function**: `detectDrift` — `.lazy-harness/scripts/lazy-sync.ts` line ~205
- **Helper**: `isSourceWorkingTreeDirty` — same file line ~193 (added 2026-05-17). Runs `git status --porcelain -- .lazy-harness` in source repo, returns true if any output. Catches `execSync` failure and returns false (treats unreadable git as clean).
- **Caller**: `main` — same file line ~411. Reads `drift.status`, branches on `equal` (fast-path) vs everything else.
- **Force gate**: `main` line ~421. `(ahead|divergent) && !args.force → error exit 2`.
- **Marker storage**: `state/synced-from-commit` JSON file in the host. Written after each successful sync.
- **Managed directory prune**: `syncCategoryA` walks the destination directory for each Category A directory item and removes files that match that item's managed globs but are absent from the source, except `knowledge/` JSONL stores.
- **Knowledge seed merge**: `mergeJsonlSeed` appends missing source seed JSONL rows into host `knowledge/*.jsonl` without removing or overwriting host-local rows.
- **Jcode managed block refresh**: `installJcodeWiring` refreshes marked lazy-harness blocks, including the generic search/read evidence guard block, while leaving unmarked user-owned config sections intact.

### Related records

- ADR 0035 — queue-close mandate (companion lifecycle rule for option-gate hygiene).
- tests/tdd-cross-verify-forcegate-loop.md — TDD regression that proved the drift gap (`Already in sync` false-positive let stale `tdd-cross-verify.ts` keep looping on host-project-a).
- ssot/rule-sources.md — keeps the rule body inside `.lazy-harness/`, not host-local notes.

## Verification

```bash
# Sanity: edit a script in source, do NOT commit, run lazy-sync.
cd /home/lazydino/dev/lazy-harness
echo '// touch' >> .lazy-harness/scripts/lazy-sync.ts
bun .lazy-harness/scripts/lazy-sync.ts --target /path/to/host-project-a
# Expected: status=ahead, message=Source working-tree ... dirty, exit 2.

bun .lazy-harness/scripts/lazy-sync.ts --target /path/to/host-project-a --force
# Expected: proceeds, [Summary] updated >= 1.

# Rename/delete a managed fixture in source, then sync.
# Expected: old managed fixture is removed from the host, current fixture exists.

# Host has extra knowledge/graph.jsonl rows, then sync.
# Expected: host rows remain, missing source seed rows are appended.
```

## Non-goals

- This contract does **not** introduce per-file content hashing. A dirty working tree is the only new signal. If higher precision is needed (e.g. detect changes between two committed branches that lazy-sync should consider drift), that is a future spec.
- `--force` still does not bypass safety checks for `user-owned` files in the destination — those keep their existing override semantics.
