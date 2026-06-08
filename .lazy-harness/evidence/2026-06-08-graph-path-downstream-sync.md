# Evidence: Graph Path downstream host sync

## Scope

This evidence capsule records the cross-host sync and smoke validation for lazy-harness source commit `ba16056a3364d001f8281311d25157336181c88b` (`feat(graph): add bounded graph path navigation`).

In scope:

- Sync the clean source checkout `/home/lazydino/dev/lazy-harness` to every initialized downstream host discovered under `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`.
- Verify each downstream host marker points at clean source commit `ba16056a3364d001f8281311d25157336181c88b`.
- Verify managed graph-path files match source hashes:
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/graph-query.ts`
  - `.lazy-harness/scripts/self-test.py`
  - `.lazy-harness/spec/platform/graph-path.md`
  - `.lazy-harness/tests/graph-path.md`
  - `.lazy-harness/planning/graph-path-implementation-plan.md`
  - `.lazy-harness/spec/platform/graph-query.md`
  - `.lazy-harness/tests/graph-query.md`
  - `.lazy-harness/manifests/init-categories.json`
- Verify source seed graph rows are present downstream:
  - `kg_graph_path_cli_20260608`
  - `kg_graph_path_dispatcher_20260608`
  - `kg_graph_path_self_test_20260608`
  - `kg_graph_path_manifest_20260608`
- Verify `lazy help` advertises `graph path <from> <to>`.
- Verify `lazy graph path 'workflow compression not safety reduction' '.lazy-harness/ssot/cli-tool-boundary.md' --format=json --limit=8 --max-depth=4` returns `mode=graph-query.path`, `resultState=linked`, at least one bounded path, endpoint candidates, and no forbidden semantic-authority fields.

Out of scope:

- Product app behavior, product unit/e2e suites, and downstream product commits.
- Pushing downstream repositories.
- Treating graph-path output as proof that real evidence was read, as causality proof, or as a required-read decision.
- Implementing `lazy graph explain`, MCP, daemon, watch mode, or prompt/reminder injection.

## Environment

- Date: 2026-06-08
- Source root: `/home/lazydino/dev/lazy-harness`
- Source branch: `feature/map-first-record-navigation`
- Source commit synced: `ba16056a3364d001f8281311d25157336181c88b`
- Source commit title: `feat(graph): add bounded graph path navigation`
- Host discovery: `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`, excluding the source checkout itself.
- Aggregate summary artifact: `/tmp/lazy-harness-graph-path-downstream-sync/20260608T133513Z/summary.json`
- Source full validation background task: `261737mjsl` (`python3 .lazy-harness/scripts/self-test.py --scope framework`, exit 0)
- Clean downstream sync background task: `713806bptv` (exit 0)

## Commands

Source validation before sync:

```bash
python3 .lazy-harness/scripts/self-test.py --scope framework
.lazy-harness/bin/lazy graph path 'workflow compression not safety reduction' '.lazy-harness/ssot/cli-tool-boundary.md' --format=json --limit=8 --max-depth=4
.lazy-harness/bin/lazy graph path 'zzzz-missing-from' 'zzzz-missing-to' --format=json --limit=8
.lazy-harness/bin/lazy graph explain 'workflow compression' --format=json
```

Downstream discovery:

```bash
python3 - <<'PY_DISCOVER'
from pathlib import Path
source = Path('/home/lazydino/dev/lazy-harness').resolve()
for marker in sorted(Path('/home/lazydino/dev').glob('*/.lazy-harness/state/synced-from-commit')):
    host = marker.parents[2].resolve()
    if host != source:
        print(host)
PY_DISCOVER
```

Clean sync and smoke shape:

```bash
# Source worktree was verified clean for .lazy-harness before syncing.
bun /home/lazydino/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts \
  --from /home/lazydino/dev/lazy-harness \
  --target <host> \
  --force \
  --quiet

<host>/.lazy-harness/bin/lazy help
<host>/.lazy-harness/bin/lazy graph path \
  'workflow compression not safety reduction' \
  '.lazy-harness/ssot/cli-tool-boundary.md' \
  --format=json \
  --limit=8 \
  --max-depth=4
```

## Results

Source validation:

- `python3 .lazy-harness/scripts/self-test.py --scope framework` completed successfully with exit 0, `ran=76`, `skipped=0`.
- The commit hook for `ba16056a3364` reported `✅ .lazy-harness/bin/lazy test all green`.
- Focused smoke returned `mode=graph-query.path`, `resultState=linked`, and at least one path for the workflow-compression → CLI-boundary fixture.
- `lazy graph explain` remained unsupported with the explicit prototype-slice message.

Discovered downstream hosts: 15.

Aggregate sync/smoke summary:

```json
{
  "summary": "/tmp/lazy-harness-graph-path-downstream-sync/20260608T133513Z/summary.json",
  "source": "ba16056a3364",
  "total": 15,
  "ok": 15,
  "failed": []
}
```

Per-host result summary:

| Host | Result | State | Paths | From candidates | To candidates | Nodes | Edges |
|---|---:|---|---:|---:|---:|---:|---:|
| `medivance` | ok | linked | 3 | 3 | 5 | 8 | 5 |
| `medivance-homepage` | ok | linked | 3 | 3 | 5 | 8 | 5 |
| `medivance-pwa` | ok | linked | 3 | 3 | 5 | 8 | 5 |
| `medivance-pwa.fix-chat-error` | ok | linked | 3 | 3 | 5 | 8 | 5 |
| `medivance.feat-calendar-renewal` | ok | linked | 3 | 3 | 5 | 8 | 5 |
| `medivance.feat-director-screen-redesign` | ok | linked | 3 | 3 | 5 | 8 | 5 |
| `medivance.feat-hospital-hours-schedule-sync` | ok | linked | 3 | 3 | 5 | 8 | 5 |
| `medivance.fix-chat-patient-share-read-policy` | ok | linked | 3 | 3 | 5 | 8 | 5 |
| `medivance.fix-emr-patient-sync` | ok | linked | 3 | 3 | 5 | 8 | 5 |
| `medivance.fix-gemini-webapi-3-5-flash` | ok | linked | 3 | 3 | 5 | 8 | 5 |
| `medivance.fix-manual-therapy-treatment-document` | ok | linked | 3 | 3 | 5 | 8 | 5 |
| `medivance.fix-reservation-block-all-cell-border` | ok | linked | 3 | 3 | 5 | 8 | 5 |
| `medivance.fix-reservation-sheet` | ok | linked | 3 | 3 | 5 | 8 | 5 |
| `medivance.fix-reservation-sheet-treatment-record` | ok | linked | 3 | 3 | 5 | 8 | 5 |
| `medivance.fix-reservation-sheet-updates` | ok | linked | 3 | 3 | 5 | 8 | 5 |

## Interpretation

- The clean graph-path implementation source commit synced and smoke-validated on 15/15 initialized downstream hosts.
- Each downstream smoke produced linked graph-path output with 3 returned paths, endpoint candidates, compact subgraph nodes/edges, and zero forbidden semantic-authority fields.
- This validates distribution and basic host portability of the `lazy graph path` helper only.
- This does not relax overview/read-debt/lifecycle/prompt/option-gate rules and does not make graph output semantic authority.
- The source commit message uses lazy-harness framework wording only; downstream Medivance `Internal-only` / hospital-user-facing phrasing is intentionally absent per `.lazy-harness/ssot/project-identity.md`.

## Reproduce

1. From `/home/lazydino/dev/lazy-harness`, confirm source commit:

   ```bash
   git rev-parse HEAD
   ```

2. Re-run source validation:

   ```bash
   python3 .lazy-harness/scripts/self-test.py --scope framework
   ```

3. Discover downstream hosts and run the clean sync/smoke shape from the Commands section for each host.
4. Inspect `/tmp/lazy-harness-graph-path-downstream-sync/20260608T133513Z/summary.json` while it is retained locally.

## Related records

- `.lazy-harness/spec/platform/graph-path.md`
- `.lazy-harness/tests/graph-path.md`
- `.lazy-harness/planning/graph-path-implementation-plan.md`
- `.lazy-harness/spec/platform/graph-query.md`
- `.lazy-harness/tests/graph-query.md`
- `.lazy-harness/spec/lazy-sync-drift-detection.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- `.lazy-harness/ssot/project-identity.md`
- `.lazy-harness/knowledge/graph.jsonl#kg_graph_path_downstream_sync_20260608`

## Retention / privacy

- This capsule stores summaries, file paths, host names, commit hashes, and aggregate validation counts only.
- Raw full logs remain in `/tmp` and Jcode background-task storage and are not canonical framework truth.
- No secrets, credentials, personal data, raw transcripts, raw assistant responses, or unrelated product data are included.
