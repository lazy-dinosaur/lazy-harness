# Evidence: Graph Path portability sync

## Scope

This evidence capsule records the portable graph-path follow-up validation for lazy-harness source commit `625fe86746785d2b1c64c9f33ba919a93a1cd9c7` (`fix(graph): preserve direct endpoint paths`).

In scope:

- Verify the source graph-path regression remains `linked` through direct endpoint record hints (`hints_record`).
- Sync the clean source checkout `/home/lazydino/dev/lazy-harness` to every initialized downstream host discovered under `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`.
- Verify each downstream host marker points at clean source commit `625fe86746785d2b1c64c9f33ba919a93a1cd9c7`.
- Verify managed graph-path files match source hashes:
  - `.lazy-harness/scripts/graph-query.ts`
  - `.lazy-harness/scripts/self-test.py`
  - `.lazy-harness/spec/platform/graph-path.md`
  - `.lazy-harness/tests/graph-path.md`
- Verify source seed graph rows are present downstream:
  - `kg_graph_path_endpoint_edge_reinforcement_20260608`
  - `kg_graph_path_endpoint_edge_reinforcement_self_test_20260608`
  - `kg_graph_path_candidate_context_fallback_20260608`
  - `kg_graph_path_candidate_context_fallback_self_test_20260608`
- Verify `lazy graph path 'workflow compression not safety reduction' '.lazy-harness/ssot/cli-tool-boundary.md' --format=json --limit=8 --max-depth=4` returns `mode=graph-query.path`, `resultState=linked`, at least one bounded path, and no forbidden semantic-authority fields on downstream hosts that may not have the source repo's full record set.

Out of scope:

- Product app behavior, product unit/e2e suites, and downstream product commits.
- Pushing downstream repositories.
- Treating `candidate_context` as causality proof, semantic sufficiency, required-read proof, or confidence.
- Implementing `lazy graph explain`, MCP, daemon, watch mode, or prompt/reminder injection.

## Environment

- Date: 2026-06-08
- Source root: `/home/lazydino/dev/lazy-harness`
- Source branch: `feature/map-first-record-navigation`
- Source commit synced: `625fe86746785d2b1c64c9f33ba919a93a1cd9c7`
- Source commit title: `fix(graph): preserve direct endpoint paths`
- Host discovery: `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`, excluding the source checkout itself.
- Aggregate summary artifact: `/tmp/lazy-harness-graph-path-portable-sync/20260608T144234Z/summary.json`
- Full framework validation task: `3062316rub` (`python3 .lazy-harness/scripts/self-test.py --scope framework`, exit 0)
- Portable downstream sync task: `754892figa` (exit 0)

## Commands

Source validation before sync:

```bash
python3 .lazy-harness/scripts/self-test.py --scope framework
.lazy-harness/bin/lazy graph path 'workflow compression not safety reduction' '.lazy-harness/ssot/cli-tool-boundary.md' --format=json --limit=8 --max-depth=4
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
bun /home/lazydino/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts \
  --from /home/lazydino/dev/lazy-harness \
  --target <host> \
  --force \
  --quiet

<host>/.lazy-harness/bin/lazy graph path \
  'workflow compression not safety reduction' \
  '.lazy-harness/ssot/cli-tool-boundary.md' \
  --format=json \
  --limit=8 \
  --max-depth=4
```

## Results

Source validation:

- `python3 .lazy-harness/scripts/self-test.py --scope framework` completed successfully with exit 0.
- Commit hook for `625fe8674678` reported `✅ .lazy-harness/bin/lazy test all green`.
- Source smoke returned `mode=graph-query.path`, `resultState=linked`, and path relation `hints_record` for the workflow-compression → CLI-boundary fixture.
- Downstream smoke returned `mode=graph-query.path`, `resultState=linked`, and path relation `candidate_context` where downstream hosts have source graph rows but not every source record file.
- `lazy graph explain` remained unsupported with the explicit prototype-slice message.

Aggregate sync/smoke summary:

```json
{
  "summary": "/tmp/lazy-harness-graph-path-portable-sync/20260608T144234Z/summary.json",
  "source": "625fe8674678",
  "total": 15,
  "ok": 15,
  "failed": []
}
```

Per-host result summary:

| Host | Result | State | Paths | Relations |
|---|---:|---|---:|---|
| `medivance` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |
| `medivance-homepage` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |
| `medivance-pwa` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |
| `medivance-pwa.fix-chat-error` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |
| `medivance.feat-calendar-renewal` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |
| `medivance.feat-director-screen-redesign` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |
| `medivance.feat-hospital-hours-schedule-sync` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |
| `medivance.fix-chat-patient-share-read-policy` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |
| `medivance.fix-emr-patient-sync` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |
| `medivance.fix-gemini-webapi-3-5-flash` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |
| `medivance.fix-manual-therapy-treatment-document` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |
| `medivance.fix-reservation-block-all-cell-border` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |
| `medivance.fix-reservation-sheet` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |
| `medivance.fix-reservation-sheet-treatment-record` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |
| `medivance.fix-reservation-sheet-updates` | ok | linked | 3 | `candidate_context, candidate_context, candidate_context` |

## Interpretation

- The portable graph-path follow-up synced and smoke-validated on 15/15 initialized downstream hosts.
- Source keeps the stronger direct/indexed path (`hints_record`) when complete records are available.
- Downstream hosts without the source repo's full record set still get bounded cue-only connectivity through fallback `candidate_context` edges, but only after direct/indexed BFS fails and only when one endpoint path appears in the other endpoint's graph-query candidate packet.
- This validates portability and host-local record-set tolerance for `lazy graph path`.
- This does not relax overview/read-debt/lifecycle/prompt/option-gate rules and does not make graph output semantic authority.

## Reproduce

1. From `/home/lazydino/dev/lazy-harness`, confirm source commit:

   ```bash
   git rev-parse HEAD
   ```

2. Re-run source validation:

   ```bash
   python3 .lazy-harness/scripts/self-test.py --scope framework
   .lazy-harness/bin/lazy graph path 'workflow compression not safety reduction' '.lazy-harness/ssot/cli-tool-boundary.md' --format=json --limit=8 --max-depth=4
   ```

3. Discover downstream hosts and run the clean sync/smoke shape from the Commands section for each host.
4. Inspect `/tmp/lazy-harness-graph-path-portable-sync/20260608T144234Z/summary.json` while it is retained locally.

## Related records

- `.lazy-harness/spec/platform/graph-path.md`
- `.lazy-harness/tests/graph-path.md`
- `.lazy-harness/planning/graph-path-implementation-plan.md`
- `.lazy-harness/spec/platform/graph-query.md`
- `.lazy-harness/tests/graph-query.md`
- `.lazy-harness/spec/lazy-sync-drift-detection.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- `.lazy-harness/ssot/cli-tool-boundary.md`
- `.lazy-harness/knowledge/graph.jsonl#kg_graph_path_portability_sync_20260608`

## Retention / privacy

- This capsule stores summaries, file paths, host names, commit hashes, and aggregate validation counts only.
- Raw full logs remain in `/tmp` and Jcode background-task storage and are not canonical framework truth.
- No secrets, credentials, personal data, raw transcripts, raw assistant responses, or unrelated product data are included.
