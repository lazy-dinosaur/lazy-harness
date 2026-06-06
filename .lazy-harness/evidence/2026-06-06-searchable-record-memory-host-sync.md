# Evidence: Searchable record memory cleanup host sync

## Scope

This evidence capsule records the cross-host sync/dogfood validation for the corrected searchable record memory cleanup.

In scope:

- Sync lazy-harness source commit `34c1ef2` to initialized downstream hosts with `.lazy-harness/state/synced-from-commit`.
- Verify deleted query-helper artifacts are pruned.
- Verify `lazy help` no longer exposes deleted helper commands.
- Verify each host's active `message.received` hook output does not advertise removed indexes/helpers.

Out of scope:

- Product app tests in each downstream host.
- Host-local `.jcode` or app code commits.
- Future Record Index Header/cache/parser implementation.

## Environment

- Date: 2026-06-06
- Source root: `/home/lazydino/dev/lazy-harness`
- Source branch: `feature/prompt-runtime-compression-plan`
- Source commit synced: `34c1ef2 Docs: Mark cleanup retrieval tasks done`
- Host discovery: `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit` marker.

## Commands

```bash
# Source validation already completed before sync:
python3 .lazy-harness/scripts/self-test.py
.lazy-harness/bin/lazy prompt-budget --format=md
bun .lazy-harness/scripts/graph-hygiene.ts --format=json

# Host sync and smoke loop:
for host in /home/lazydino/dev/*; do
  [ -f "$host/.lazy-harness/state/synced-from-commit" ] || continue
  bun .lazy-harness/scripts/lazy-sync.ts --from /home/lazydino/dev/lazy-harness --target "$host" --force --quiet
  "$host/.lazy-harness/bin/lazy" help | grep -E 'context --message|context-delivery|context-dogfood' && fail
  cd "$host" && .lazy-harness/hooks/lifecycle/on-message-received.sh < payload.json
  # hook output checked for absence of relevant-record-index, context-index.json=missing,
  # context-delivery, relevant-record-query
 done
```

Raw per-host logs are transient under `/tmp/lazy-harness-host-sync/*.log` in the originating session.

## Results

Summary:

```json
{
  "total": 13,
  "ok": 13,
  "failed": []
}
```

Host rows:

- `medivance` — status `ok`, marker `34c1ef2`, staleFiles `0`, helpBad `0`, hookBad `0`
- `medivance-homepage` — status `ok`, marker `34c1ef2`, staleFiles `0`, helpBad `0`, hookBad `0`
- `medivance-pwa` — status `ok`, marker `34c1ef2`, staleFiles `0`, helpBad `0`, hookBad `0`
- `medivance-pwa.fix-chat-error` — status `ok`, marker `34c1ef2`, staleFiles `0`, helpBad `0`, hookBad `0`
- `medivance.feat-calendar-renewal` — status `ok`, marker `34c1ef2`, staleFiles `0`, helpBad `0`, hookBad `0`
- `medivance.fix-chat-patient-share-read-policy` — status `ok`, marker `34c1ef2`, staleFiles `0`, helpBad `0`, hookBad `0`
- `medivance.fix-emr-patient-sync` — status `ok`, marker `34c1ef2`, staleFiles `0`, helpBad `0`, hookBad `0`
- `medivance.fix-gemini-webapi-3-5-flash` — status `ok`, marker `34c1ef2`, staleFiles `0`, helpBad `0`, hookBad `0`
- `medivance.fix-manual-therapy-treatment-document` — status `ok`, marker `34c1ef2`, staleFiles `0`, helpBad `0`, hookBad `0`
- `medivance.fix-reservation-block-all-cell-border` — status `ok`, marker `34c1ef2`, staleFiles `0`, helpBad `0`, hookBad `0`
- `medivance.fix-reservation-sheet` — status `ok`, marker `34c1ef2`, staleFiles `0`, helpBad `0`, hookBad `0`
- `medivance.fix-reservation-sheet-treatment-record` — status `ok`, marker `34c1ef2`, staleFiles `0`, helpBad `0`, hookBad `0`
- `medivance.fix-reservation-sheet-updates` — status `ok`, marker `34c1ef2`, staleFiles `0`, helpBad `0`, hookBad `0`

## Interpretation

The cleanup sync reached every initialized downstream host discovered under `/home/lazydino/dev` except the source checkout itself and the markerless path-only backup.

The smoke checks prove:

- Host sync markers now point at `34c1ef2`.
- Deleted query-helper files/directories were pruned from synced framework copies.
- Deleted helper CLI commands are not advertised by `lazy help`.
- Active host `message.received` hook output no longer includes removed helper/index names.

This does not prove product-level app behavior or future record-index/cache parser correctness.

## Reproduce

1. From `/home/lazydino/dev/lazy-harness`, run the host discovery loop above.
2. Confirm each initialized host has marker `34c1ef2` or later.
3. Confirm stale file/help/hook checks return zero.
4. Re-run source validation commands if source records changed.

## Related records

- `.lazy-harness/prd/searchable-record-context-retrieval-prd.md`
- `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`
- `.lazy-harness/spec/platform/search-read-debt-contract.md`
- `.lazy-harness/spec/platform/pre-response-rule-context.md`
- `.lazy-harness/ssot/cli-tool-boundary.md`
- `.lazy-harness/spec/lazy-sync-drift-detection.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`

## Retention / privacy

No secrets, credentials, personal data, raw transcripts, or app data are stored here. Host names and paths are local development paths only. Large raw logs remain transient in `/tmp` and are summarized above.
