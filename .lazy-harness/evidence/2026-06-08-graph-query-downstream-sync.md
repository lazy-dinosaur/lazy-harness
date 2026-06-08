# Evidence: Graph Query downstream host sync

## Scope

This evidence capsule records the cross-host sync and smoke validation for lazy-harness source commit `4b20a02244b28d61ac0f14e7ad33f8a9740ead4a` (`Add lazy graph query prototype`).

In scope:

- Sync the source checkout `/home/lazydino/dev/lazy-harness` to every initialized downstream host discovered under `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`.
- Verify each downstream host marker points at source commit `4b20a02244b28d61ac0f14e7ad33f8a9740ead4a`.
- Verify managed graph-query files match source hashes:
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/graph-query.ts`
  - `.lazy-harness/spec/platform/graph-query.md`
  - `.lazy-harness/tests/graph-query.md`
  - `.lazy-harness/manifests/init-categories.json`
- Verify `lazy help` advertises `graph query <term-or-file>`.
- Verify `lazy graph query 'retrieval coverage audit' --format=json --limit=20` returns `mode=graph-query.query`, `resultState=mapped`, DDD/BDD/SDD/TDD/SSOT candidates, and no forbidden semantic-authority fields.

Out of scope:

- Product app behavior, product unit/e2e suites, and downstream product commits.
- Pushing downstream repositories.
- Treating graph-query output as proof that real evidence was read.

## Environment

- Date: 2026-06-08
- Source root: `/home/lazydino/dev/lazy-harness`
- Source branch: `feature/map-first-record-navigation`
- Source commit synced: `4b20a02244b28d61ac0f14e7ad33f8a9740ead4a`
- Source commit title: `Add lazy graph query prototype`
- Host discovery: `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`, excluding the source checkout itself.
- Aggregate summary artifact: `/tmp/lazy-harness-graph-query-downstream-sync/20260608T072408Z/summary.json`

## Commands

Source validation before sync:

```bash
python3 .lazy-harness/scripts/self-test.py --scope framework
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

Sync and smoke shape:

```bash
bun /home/lazydino/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts \
  --from /home/lazydino/dev/lazy-harness \
  --target <host> \
  --force \
  --quiet

<host>/.lazy-harness/bin/lazy help
<host>/.lazy-harness/bin/lazy graph query 'retrieval coverage audit' --format=json --limit=20
```

## Results

Source validation:

- `python3 .lazy-harness/scripts/self-test.py --scope framework` completed successfully.
- Commit hook for `4b20a02` also reported `✅ .lazy-harness/bin/lazy test all green`.

Discovered downstream hosts: 14.

Aggregate sync/smoke summary:

```json
{
  "summary": "/tmp/lazy-harness-graph-query-downstream-sync/20260608T072408Z/summary.json",
  "source": "4b20a02244b2",
  "total": 14,
  "ok": 14,
  "failed": []
}
```

Per-host result summary:

| Host | Result | Candidate counts | Graph bytes |
|---|---:|---|---:|
| `medivance` | ok | records=20, source=20, tests=12, graph=20 | 60,967 |
| `medivance-homepage` | ok | records=20, source=20, tests=12, graph=20 | 61,662 |
| `medivance-pwa` | ok | records=20, source=20, tests=12, graph=20 | 60,967 |
| `medivance-pwa.fix-chat-error` | ok | records=20, source=20, tests=12, graph=20 | 60,967 |
| `medivance.feat-calendar-renewal` | ok | records=20, source=20, tests=12, graph=20 | 60,967 |
| `medivance.feat-director-screen-redesign` | ok | records=20, source=20, tests=12, graph=20 | 60,967 |
| `medivance.fix-chat-patient-share-read-policy` | ok | records=20, source=20, tests=12, graph=20 | 60,967 |
| `medivance.fix-emr-patient-sync` | ok | records=20, source=20, tests=12, graph=20 | 60,967 |
| `medivance.fix-gemini-webapi-3-5-flash` | ok | records=20, source=20, tests=12, graph=20 | 60,967 |
| `medivance.fix-manual-therapy-treatment-document` | ok | records=20, source=20, tests=12, graph=20 | 60,967 |
| `medivance.fix-reservation-block-all-cell-border` | ok | records=20, source=20, tests=12, graph=20 | 60,967 |
| `medivance.fix-reservation-sheet` | ok | records=20, source=20, tests=12, graph=20 | 60,967 |
| `medivance.fix-reservation-sheet-treatment-record` | ok | records=20, source=20, tests=12, graph=20 | 60,967 |
| `medivance.fix-reservation-sheet-updates` | ok | records=20, source=20, tests=12, graph=20 | 60,967 |

## Interpretation

- The graph-query prototype source commit synced and smoke-validated on 14/14 initialized downstream hosts.
- Each downstream smoke produced mapped graph-query output with all five layer categories present and zero forbidden semantic-authority fields.
- This does not justify lifecycle, prompt packet, or overview-hard-block policy changes; the benchmark in `.lazy-harness/planning/graph-query-prototype-implementation-plan.md` still shows graph-query is not yet a token-reduction win versus retrieval-audit.

## Reproduce

1. From `/home/lazydino/dev/lazy-harness`, confirm source commit:

   ```bash
   git rev-parse HEAD
   ```

2. Re-run source validation:

   ```bash
   python3 .lazy-harness/scripts/self-test.py --scope framework
   ```

3. Discover downstream hosts and run the sync/smoke shape from the Commands section for each host.
4. Inspect `/tmp/lazy-harness-graph-query-downstream-sync/20260608T072408Z/summary.json` while it is retained locally.

## Related records

- `.lazy-harness/planning/graph-query-prototype-implementation-plan.md`
- `.lazy-harness/spec/platform/graph-query.md`
- `.lazy-harness/tests/graph-query.md`
- `.lazy-harness/spec/lazy-sync-drift-detection.md`
- `.lazy-harness/knowledge/graph.jsonl#kg_graph_query_downstream_sync_20260608`

## Retention / privacy

- This capsule stores summaries, file paths, host names, commit hashes, and aggregate validation counts only.
- Raw full logs remain in `/tmp` and are not canonical framework truth.
- No secrets, credentials, personal data, raw transcripts, raw assistant responses, or unrelated product data are included.
