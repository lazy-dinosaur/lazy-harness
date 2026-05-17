# Spec — lazy-sync Drift Detection Contract

- Layer: SDD
- Date: 2026-05-17
- Related: scripts/lazy-sync.ts, ADR 0035 (queue-close mandate), tests/tdd-cross-verify-forcegate-loop.md

## Purpose

`lazy-sync` copies framework files (`scripts/`, `hooks/`, `schemas/`, `triggers/`, `manifests/`) from a canonical source repo (`/home/lazydino/dev/lazy-harness`) to host copies (e.g. `/home/lazydino/dev/medivance/.lazy-harness/`). Its drift detector must answer one question: "is the host out of date relative to the source?"

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

## Implementation map

- **Function**: `detectDrift` — `.lazy-harness/scripts/lazy-sync.ts` line ~205
- **Helper**: `isSourceWorkingTreeDirty` — same file line ~193 (added 2026-05-17). Runs `git status --porcelain -- .lazy-harness` in source repo, returns true if any output. Catches `execSync` failure and returns false (treats unreadable git as clean).
- **Caller**: `main` — same file line ~411. Reads `drift.status`, branches on `equal` (fast-path) vs everything else.
- **Force gate**: `main` line ~421. `(ahead|divergent) && !args.force → error exit 2`.
- **Marker storage**: `state/synced-from-commit` JSON file in the host. Written after each successful sync.

### Related records

- ADR 0035 — queue-close mandate (companion lifecycle rule for option-gate hygiene).
- tests/tdd-cross-verify-forcegate-loop.md — TDD regression that proved the drift gap (`Already in sync` false-positive let stale `tdd-cross-verify.ts` keep looping on medivance).
- ssot/rule-sources.md — keeps the rule body inside `.lazy-harness/`, not host-local notes.

## Verification

```bash
# Sanity: edit a script in source, do NOT commit, run lazy-sync.
cd /home/lazydino/dev/lazy-harness
echo '// touch' >> .lazy-harness/scripts/lazy-sync.ts
bun .lazy-harness/scripts/lazy-sync.ts --target ~/dev/medivance
# Expected: status=ahead, message=Source working-tree ... dirty, exit 2.

bun .lazy-harness/scripts/lazy-sync.ts --target ~/dev/medivance --force
# Expected: proceeds, [Summary] updated >= 1.
```

## Non-goals

- This contract does **not** introduce per-file content hashing. A dirty working tree is the only new signal. If higher precision is needed (e.g. detect changes between two committed branches that lazy-sync should consider drift), that is a future spec.
- `--force` still does not bypass safety checks for `user-owned` files in the destination — those keep their existing override semantics.
