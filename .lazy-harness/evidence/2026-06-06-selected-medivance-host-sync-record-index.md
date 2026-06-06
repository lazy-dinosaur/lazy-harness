# Evidence — selected Medivance host sync to record-index migration

- Date: 2026-06-06
- Source root: `/home/lazydino/dev/lazy-harness`
- Source branch: `feature/prompt-runtime-compression-plan`
- Source commit synced: `30e9866487f221c464fbbbd9d8e4bdc2f9cf196f` (`30e9866 Complete implementation map migration`)
- Scope: user-selected existing hosts only: `medivance`, `medivance-pwa`, `medivance-homepage`.
- Non-scope: `/home/lazydino/dev/medivance-hompage` is not an existing git checkout; other initialized `/home/lazydino/dev/*` hosts were not re-synced in this pass.

## Commands

```bash
SOURCE=/home/lazydino/dev/lazy-harness
for host in /home/lazydino/dev/medivance /home/lazydino/dev/medivance-pwa /home/lazydino/dev/medivance-homepage; do
  bun "$SOURCE/.lazy-harness/scripts/lazy-sync.ts" --from "$SOURCE" --target "$host" --force --quiet
  "$host/.lazy-harness/bin/lazy" help | grep record-index
  ! "$host/.lazy-harness/bin/lazy" help | grep context-index
  (cd "$host" && .lazy-harness/bin/lazy record-index --format=json)
  (cd "$host" && .lazy-harness/bin/lazy record-audit --format=json)
  (cd "$host" && .lazy-harness/bin/lazy impl-map --format=json)
  (cd "$host" && python3 .lazy-harness/scripts/doctor.py --profile smoke)
  (cd "$host" && .lazy-harness/bin/lazy test)
done
```

- Raw logs: `/tmp/lazy-harness-selected-host-sync-20260606230913/`

## Results

```json
{
  "total": 3,
  "ok": 3,
  "failed": []
}
```

| Host | Marker | record-index | context-index | help context-index | lazy test | Notes |
|---|---:|---:|---:|---:|---:|---|
| `medivance` | `30e9866487f2` | yes | no | 0 | pass (`scope=host`, ran=54, skipped=18) | branch `dev...origin/dev [ahead 1]`; log `/tmp/lazy-harness-selected-host-sync-20260606230913/medivance.log` |
| `medivance-pwa` | `30e9866487f2` | yes | no | 0 | pass (`scope=host`, ran=54, skipped=18) | branch `main...origin/main`; log `/tmp/lazy-harness-selected-host-sync-20260606230913/medivance-pwa.log` |
| `medivance-homepage` | `30e9866487f2` | yes | no | 0 | pass (`scope=host`, ran=54, skipped=18) | branch `develop...origin/develop`; log `/tmp/lazy-harness-selected-host-sync-20260606230913/medivance-homepage.log` |

## Interpretation

- The three selected Medivance hosts now point at source commit `30e9866`, not the older cleanup marker `34c1ef2`.
- The active host framework copies contain canonical `record-index` tooling and no active `context-index` command/source/schema/cache path.
- Host `lazy test` passes on all three selected hosts. The tests include record-index generator Phase 3, context-tier/evidence capsule checks, message.received inventory-first search-debt injection, response rule audit, and N2.5 hook/AGENTS invariants.
- Host product application behavior was not tested. This evidence is limited to lazy-harness sync and host-level harness smoke/self-test validation.
- Host-local `knowledge/*.jsonl` and unmarked user-owned Jcode files are preserved per lazy-sync contract.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/scripts/lazy-sync.ts` — performs Category A sync, stale managed file pruning, marker update, and Jcode wiring repair.
  - `.lazy-harness/spec/lazy-sync-drift-detection.md` — drift/force/prune/marker contract.
  - `.lazy-harness/evidence/2026-06-06-selected-medivance-host-sync-record-index.md` — current selected-host evidence.
  - `/tmp/lazy-harness-selected-host-sync-20260606230913/*.log` — transient command logs for this run.
- Key symbols:
  - `main` (`lazy-sync.ts`) — detects drift, syncs Category A, removes known managed stale files, updates marker, and installs Jcode wiring.
  - `syncCategoryA` (`lazy-sync.ts`) — copies framework-owned managed files/directories.
  - `removeKnownRemovedManagedFiles` (`lazy-sync.ts`) — prunes old `context-index` and other removed managed artifacts.
- Flow:
  1. Source `/home/lazydino/dev/lazy-harness` at `30e9866` syncs to each selected host with `--force`.
  2. Host marker `.lazy-harness/state/synced-from-commit` updates to `30e9866`.
  3. Host help and file checks verify `record-index` is present and `context-index` is absent.
  4. Each host runs record-index, record-audit, impl-map, doctor smoke, and `lazy test`.
- Tests / protection:
  - Source self-test protects lazy-sync stale managed file pruning and host-local graph row preservation.
  - Host `lazy test` passed on all three selected hosts.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/lazy-sync-drift-detection.md`
  - ADR: `.lazy-harness/decisions/0027-standalone-source-of-truth-repository.md`
  - Planning: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md#scr-701--sync-cleanup-to-hosts`
- Machine index:
  - graph ids: `kg_selected_medivance_host_sync_30e9866`, `kg_selected_medivance_host_sync_validation`

## Discovery capture

- DDD: none.
- SDD: existing lazy-sync drift/prune/marker contract remains sufficient.
- BDD: none; no product UI/app behavior tested.
- TDD: host `lazy test` pass recorded; no new regression fixture needed.
- ADR: no new trade-off; follows ADR 0027 standalone source-of-truth policy.
- SSOT: source repo remains canonical; host `.lazy-harness` edits are not source-of-truth changes.
- Planning: SCR-701 gains a latest selected-host sync follow-up marker for `30e9866`.
