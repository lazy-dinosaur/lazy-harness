# Evidence: Record Map downstream host sync

## Scope

This evidence capsule records the cross-host sync and validation for lazy-harness source commit `f560375aeb11cf6d0c38de05c947e8a9e0175803` (`Add lazy record map drilldown CLI`).

In scope:

- Sync the source checkout `/home/lazydino/dev/lazy-harness` to every initialized downstream host discovered under `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`.
- Verify each downstream host marker points at source commit `f560375aeb11cf6d0c38de05c947e8a9e0175803`.
- Verify `lazy help` advertises `map <term-or-file>`.
- Verify `lazy map record map --format=json --limit=1` returns `mode=record-map.inspect`.
- Verify pre-commit and pre-push hook files contain the `lazy test all green` commit/push gate wording.
- Run downstream lazy-harness self-test where possible, and classify host-local environment prerequisites separately.

Out of scope:

- Product app behavior, product unit/e2e suites, and product commits in downstream hosts.
- Pushing downstream host repositories.
- Storing raw full logs from `/tmp`; only summaries and reproducible paths are retained.

## Environment

- Date: 2026-06-07
- Source root: `/home/lazydino/dev/lazy-harness`
- Source branch: `feature/map-first-record-navigation`
- Source commit synced: `f560375aeb11cf6d0c38de05c947e8a9e0175803`
- Source commit title: `Add lazy record map drilldown CLI`
- Host discovery: `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`, excluding the source checkout itself.
- Initial run summary artifact: `/tmp/lazy-harness-downstream-sync/20260607T091137Z/summary.json`
- Targeted rerun summary artifact: `/tmp/lazy-harness-downstream-sync-rerun/20260607T092104Z/summary.json`

## Commands

Source validation before sync:

```bash
.lazy-harness/bin/lazy test
```

Downstream discovery:

```bash
python3 - <<'PY'
from pathlib import Path
source = Path('/home/lazydino/dev/lazy-harness').resolve()
for marker in sorted(Path('/home/lazydino/dev').glob('*/.lazy-harness/state/synced-from-commit')):
    host = marker.parents[2].resolve()
    if host != source:
        print(host)
PY
```

Sync and validation script shape:

```bash
bun /home/lazydino/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts \
  --from /home/lazydino/dev/lazy-harness \
  --target <host> \
  --force \
  --quiet

<host>/.lazy-harness/bin/lazy help
<host>/.lazy-harness/bin/lazy map 'record map' --format=json --limit=1
<host>/.lazy-harness/bin/lazy test
```

Final aggregate marker/help/map/hook check:

```bash
python3 - <<'PY'
import json, subprocess
from pathlib import Path
source=Path('/home/lazydino/dev/lazy-harness')
sha=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'], text=True).strip()
rows=[]
for marker in sorted(Path('/home/lazydino/dev').glob('*/.lazy-harness/state/synced-from-commit')):
    host=marker.parents[2]
    if host.resolve()==source.resolve(): continue
    data=json.load(open(marker))
    help_text=subprocess.check_output([str(host/'.lazy-harness/bin/lazy'),'help'], cwd=host, text=True)
    map_out=subprocess.check_output([str(host/'.lazy-harness/bin/lazy'),'map','record map','--format=json','--limit=1'], cwd=host, text=True)
    obj=json.loads(map_out)
    precommit=(host/'.lazy-harness/hooks/pre-commit-guard.sh').read_text(errors='ignore')
    prepush=(host/'.lazy-harness/hooks/pre-push.sh').read_text(errors='ignore')
    row={
      'name':host.name,
      'markerOk':data.get('syncedFromCommit')==sha,
      'helpOk':'map <term-or-file>' in help_text,
      'mapOk':obj.get('mode')=='record-map.inspect',
      'hookOk':'lazy test all green' in precommit and 'lazy test all green' in prepush,
    }
    row['ok']=all([row['markerOk'],row['helpOk'],row['mapOk'],row['hookOk']])
    rows.append(row)
print(json.dumps({'source':sha[:12], 'total':len(rows), 'ok':sum(r['ok'] for r in rows), 'failed':[r for r in rows if not r['ok']], 'rows':rows}, ensure_ascii=False, indent=2))
PY
```

## Results

Source validation:

- `.lazy-harness/bin/lazy test` completed with `lazy-harness self-test ok (scope=framework, ran=72, skipped=0)`.
- Commit hook for `f560375` also reported `✅ .lazy-harness/bin/lazy test all green`.

Discovered downstream hosts: 14.

Final marker/help/map/hook aggregate:

```json
{
  "source": "f560375aeb11",
  "total": 14,
  "ok": 14,
  "failed": []
}
```

Host rows:

- `medivance` — marker/help/map/hook `ok`
- `medivance-homepage` — marker/help/map/hook `ok`
- `medivance-pwa` — marker/help/map/hook `ok`; targeted default `lazy test` rerun `ok`
- `medivance-pwa.fix-chat-error` — marker/help/map/hook `ok`
- `medivance.feat-calendar-renewal` — marker/help/map/hook `ok`
- `medivance.feat-director-screen-redesign` — marker/help/map/hook `ok`; targeted default `lazy test` rerun `ok`
- `medivance.fix-chat-patient-share-read-policy` — marker/help/map/hook `ok`
- `medivance.fix-emr-patient-sync` — marker/help/map/hook `ok`; `lazy test` requires host product env `VITE_DIRECT_URL`; targeted rerun with dummy `VITE_DIRECT_URL=postgresql://lazy:lazy@localhost:5432/lazy` returned `ok`
- `medivance.fix-gemini-webapi-3-5-flash` — marker/help/map/hook `ok`
- `medivance.fix-manual-therapy-treatment-document` — marker/help/map/hook `ok`
- `medivance.fix-reservation-block-all-cell-border` — marker/help/map/hook `ok`
- `medivance.fix-reservation-sheet` — marker/help/map/hook `ok`
- `medivance.fix-reservation-sheet-treatment-record` — marker/help/map/hook `ok`
- `medivance.fix-reservation-sheet-updates` — marker/help/map/hook `ok`

Initial full per-host lazy-test run:

- 11/14 hosts passed immediately.
- `medivance-pwa` failed once on N2.5 session-cache fixture but a targeted default rerun passed.
- `medivance.feat-director-screen-redesign` failed once in the lazy-sync prune fixture while copying `knowledge/candidates.jsonl`, then a targeted default rerun passed after sync state settled.
- `medivance.fix-emr-patient-sync` failed host doctor package-health because Prisma config could not resolve `VITE_DIRECT_URL`; targeted rerun with a dummy value passed.

Targeted rerun summary:

```json
{
  "ok": 3,
  "total": 3,
  "rows": [
    {"name":"medivance-pwa","mode":"default","returncode":0,"ok":true},
    {"name":"medivance.feat-director-screen-redesign","mode":"default","returncode":0,"ok":true},
    {"name":"medivance.fix-emr-patient-sync","mode":"dummy-env","returncode":0,"ok":true}
  ]
}
```

## Interpretation

The sync reached every initialized downstream host discovered under `/home/lazydino/dev` and updated each `.lazy-harness/state/synced-from-commit` marker to `f560375aeb11cf6d0c38de05c947e8a9e0175803`.

The smoke checks prove:

- `lazy map` is available in all synced hosts.
- `lazy map record map --format=json --limit=1` runs in all synced hosts.
- The managed pre-commit/pre-push hook files in all synced hosts contain the `lazy test all green` gate wording.
- `lazy-sync` marker storage and managed Jcode/hook refresh behavior matched `.lazy-harness/spec/lazy-sync-drift-detection.md`.

Known caveats:

- `medivance.fix-emr-patient-sync` needs a product environment variable (`VITE_DIRECT_URL`) for host doctor package-health. This is a host/product prerequisite, not a framework sync-marker/help/map/hook failure.
- Initial PWA/director failures were transient or state-sensitive because targeted default reruns passed without source changes.
- This evidence does not prove downstream product app behavior.

Confidence: high for framework sync/marker/help/map/hook propagation; medium for per-host `lazy test` because product env can affect host-scope doctor checks.

## Reproduce

1. From `/home/lazydino/dev/lazy-harness`, confirm source commit:

   ```bash
   git rev-parse HEAD
   ```

2. Discover initialized hosts by marker:

   ```bash
   find /home/lazydino/dev -maxdepth 2 -path '*/.lazy-harness/state/synced-from-commit' -print | sort
   ```

3. For each host except `/home/lazydino/dev/lazy-harness`, run `lazy-sync --force --quiet` from source.
4. Verify marker/help/map/hook checks using the aggregate script in `## Commands`.
5. Run `<host>/.lazy-harness/bin/lazy test`; for `medivance.fix-emr-patient-sync`, provide `VITE_DIRECT_URL` if package-health needs Prisma config loading.

## Related records

- `.lazy-harness/spec/lazy-sync-drift-detection.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- `.lazy-harness/evidence/2026-06-06-searchable-record-memory-host-sync.md`
- `.lazy-harness/domain/searchable-record-memory.md`
- `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- `.lazy-harness/spec/platform/record-index-header.md`
- `.lazy-harness/tests/record-index-header.md`
- `.lazy-harness/ssot/cli-tool-boundary.md`
- Commit: `f560375 Add lazy record map drilldown CLI`

## Retention / privacy

No secrets, credentials, personal data, raw transcripts, or product data are stored in this capsule. Host names and paths are local development paths. Raw stdout/stderr logs remain transient under `/tmp/lazy-harness-downstream-sync*` and are summarized here instead of embedded.
