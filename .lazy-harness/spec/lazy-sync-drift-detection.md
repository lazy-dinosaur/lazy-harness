# Spec — lazy-sync Drift Detection Contract

- Layer: SDD
- Date: 2026-05-17
- Related: scripts/lazy-sync.ts, ADR 0035 (queue-close mandate), tests/tdd-cross-verify-forcegate-loop.md

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 싱크 드리프트
  - sync drift
  - lazy sync 검증
  - 동기화 검사
- Applies when:
  - running or debugging `lazy sync`, or deciding whether a host is in sync with the framework source
  - the source `.lazy-harness` tree is dirty, managed files were renamed/deleted, or host knowledge seed merge must be explicitly skipped
- Must:
  - report `ahead` (error/exit 2) when the source `.lazy-harness` working tree is dirty, even if marker SHA equals source HEAD
  - auto-sync only on `behind`; everything else exits 2 without `--force`
  - sync Category A and registry seeds; merge `knowledge/*.jsonl` by default, but skip only those JSONL stores when `--skip-knowledge-seeds` is explicit
- Must not:
  - reintroduce retired retrieval-purpose capabilities or overwrite host-owned capability/knowledge rows
  - create, append, or conflict-record any host `knowledge/*.jsonl` when `--skip-knowledge-seeds` is set
- Record completion:
  - drift-status, merge, or prune rule changes update this SDD and the lazy-sync regression tests
- Related records:
  - `.lazy-harness/tests/lazy-sync-dirty-false-positive.md`
  - `.lazy-harness/decisions/0035-interview-queue-close-mandate.md`

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

### Managed directory prune and host-owned seed behavior (added 2026-06-02; opt-out added 2026-07-23)

For Category A manifest directory entries, `lazy-sync` must remove stale destination files that still match the managed `glob`/`exclude` rules but no longer exist in the source directory. This prevents renamed or deleted framework fixtures from remaining in downstream hosts as false context.

Exception: `knowledge/` JSONL files are host-local append-only stores. By default they are seed-merged, not overwritten or pruned: missing source seed rows are appended to the host file, while host-local graph/candidate rows are preserved.

`--skip-knowledge-seeds` is an explicit rollout safety option. It skips only `knowledge/*.jsonl` processing in both dry-run and live modes: existing files stay byte-identical, missing files stay absent, and no adjacent `*.conflicts.jsonl` sidecars are created. `knowledge/README.md`, all other Category A files, and the host-owned capability/policy registries still sync normally. The successful sync marker still advances to the source commit; a later opt-in seed merge at the same commit therefore requires `--force`.

`ssot/capabilities.json` and `ssot/policies.json` are also host-owned. When the manifest includes the framework seed registries, `lazy-sync` merges missing source ids without deleting or overwriting host-local entries. The knowledge opt-out does not disable these registry merges.

Every framework-owned seed capability (`owner=framework-global`) `sourceRecord` that is synced into host `ssot/capabilities.json` must also be present in the Category A manifest, or have a host-safe `targetPath` mirror. Host-owned capabilities are deliberately excluded from this framework manifest rule because their records are owned by the downstream project. Otherwise host `lazy capability audit` or framework self-tests can fail immediately after a successful capability seed merge.

## Implementation map

- **Function**: `detectDrift` — `.lazy-harness/scripts/lazy-sync.ts`; classifies source/host marker drift before sync.
- **Caller**: `main` — parses `--skip-knowledge-seeds`, reports the active mode, and passes it into Category A sync.
- **Marker storage**: `state/synced-from-commit` JSON file in the host. Written after each successful sync, including knowledge-seed opt-out runs.
- **Managed directory prune**: `syncCategoryA` walks destination Category A directories and removes stale managed files, except host-owned `knowledge/` JSONL stores.
- **Knowledge seed merge**: `mergeJsonlSeed` appends missing source JSONL rows by default; `syncCategoryA(..., skipKnowledgeSeeds=true)` bypasses every `knowledge/*.jsonl` merge.
- **Capability/policy seed merge**: `mergeCapabilitiesSeed` and `mergePoliciesSeed` append missing framework ids while preserving host-local entries.
- **Protection**: `.lazy-harness/scripts/self-test.py#check_lazy_sync_prunes_stale_managed_files` proves opt-out byte identity, no conflict sidecars, normal non-knowledge sync, and unchanged default merge behavior.

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

# Host has an existing ssot/capabilities.json with project-specific entries, then sync.
# Expected: host capability ids remain and missing framework capability ids are appended.

# Host requires knowledge JSONL to remain untouched during a framework rollout.
bun .lazy-harness/scripts/lazy-sync.ts --target /path/to/host-project-a --force --skip-knowledge-seeds
# Expected: graph/candidates/other knowledge JSONL bytes remain unchanged; no conflict sidecars; Category A and registry seeds still update.
```

## Non-goals

- This contract does **not** introduce per-file content hashing. A dirty working tree is the only new signal. If higher precision is needed (e.g. detect changes between two committed branches that lazy-sync should consider drift), that is a future spec.
- `--force` still does not bypass safety checks for `user-owned` files in the destination — those keep their existing override semantics.
- `--skip-knowledge-seeds` is not a permanent registry preference. It is a per-run opt-out; the normal source marker still advances.
