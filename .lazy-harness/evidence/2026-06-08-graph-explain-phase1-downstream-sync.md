# Evidence: Graph Explain Phase 1 downstream sync

## Scope

This evidence capsule records cross-host sync and smoke validation for lazy-harness source commit `dfd11ffe676500ad928c61789034835a81097ef1` (`feat(graph): implement graph explain phase 1`).

In scope:

- Sync the clean source checkout `/home/lazydino/dev/lazy-harness` to every initialized downstream host discovered under `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`.
- Verify each downstream host marker JSON has `syncedFromCommit` equal to `dfd11ffe676500ad928c61789034835a81097ef1`.
- Verify managed graph-explain files match source hashes:
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/graph-query.ts`
  - `.lazy-harness/scripts/self-test.py`
  - `.lazy-harness/spec/platform/graph-explain.md`
  - `.lazy-harness/tests/graph-explain.md`
  - `.lazy-harness/planning/graph-explain-implementation-plan.md`
  - `.lazy-harness/manifests/init-categories.json`
- Verify graph-explain graph seed rows are present downstream:
  - `kg_graph_explain_structural_design_20260608`
  - `kg_graph_explain_structural_tdd_20260608`
  - `kg_graph_explain_structural_plan_20260608`
  - `kg_graph_explain_design_manifest_20260608`
  - `kg_graph_explain_phase1_cli_20260608`
  - `kg_graph_explain_phase1_self_test_20260608`
  - `kg_graph_explain_phase1_dispatcher_20260608`
- Verify `lazy help` advertises `graph explain <term-or-file>`.
- Verify `lazy graph explain 'workflow compression not safety reduction' --format=json --limit=8 --max-statements=8` returns `mode=graph-query.explain`, `explanationKind=structural`, `resultState` in `explained | partial | gap`, 1..8 cited statements with support/citations, and zero forbidden semantic-authority fields.

Out of scope:

- Product app behavior, product unit/e2e suites, and downstream product commits.
- Pushing downstream repositories.
- Treating graph-explain output as proof that real evidence was read.
- Implementing Markdown rendering, path-backed explain statements, MCP, daemon, watch mode, prompt/reminder injection, or lifecycle/read-debt policy changes.

## Environment

- Date: 2026-06-08
- Source root: `/home/lazydino/dev/lazy-harness`
- Source branch: `feature/map-first-record-navigation`
- Source commit synced: `dfd11ffe676500ad928c61789034835a81097ef1`
- Source commit title: `feat(graph): implement graph explain phase 1`
- Host discovery: `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`, excluding the source checkout itself.
- Initial aggregate artifact: `/tmp/lazy-harness-graph-explain-phase1-sync/20260608T235202Z/summary.json`
- Corrected aggregate artifact: `/tmp/lazy-harness-graph-explain-phase1-sync/20260608T235202Z/corrected-summary.json`
- Background sync task: `722751j911`

## Commands

Source validation before sync:

```bash
python3 .lazy-harness/scripts/self-test.py --scope framework
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=json --limit=3 --max-statements=3
git push origin feature/map-first-record-navigation
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

<host>/.lazy-harness/bin/lazy help
<host>/.lazy-harness/bin/lazy graph explain \
  'workflow compression not safety reduction' \
  --format=json \
  --limit=8 \
  --max-statements=8
```

Corrected marker interpretation:

```bash
python3 - <<'PY_MARKER'
import json
marker = json.load(open('<host>/.lazy-harness/state/synced-from-commit'))
assert marker['syncedFromCommit'] == 'dfd11ffe676500ad928c61789034835a81097ef1'
PY_MARKER
```

## Results

Source validation:

- `python3 .lazy-harness/scripts/self-test.py --scope framework` completed successfully: 77 ran, 0 skipped.
- Commit hook for `dfd11ffe6765` reported `✅ .lazy-harness/bin/lazy test all green`.
- Source smoke returned `graph-query.explain explained structural` with 3 bounded statements for the compact command.
- Source branch `feature/map-first-record-navigation` was pushed to origin.

Aggregate sync/smoke summary:

```json
{
  "summary": "/tmp/lazy-harness-graph-explain-phase1-sync/20260608T235202Z/corrected-summary.json",
  "originalSummary": "/tmp/lazy-harness-graph-explain-phase1-sync/20260608T235202Z/summary.json",
  "source": "dfd11ffe6765",
  "total": 16,
  "ok": 16,
  "failed": []
}
```

The initial raw summary reported `0/16 ok` only because the ad-hoc checker compared the entire JSON marker file to the SHA string. The canonical contract in `.lazy-harness/spec/lazy-sync-drift-detection.md` says `.lazy-harness/state/synced-from-commit` is a JSON file; the corrected summary reads `syncedFromCommit` and verifies all 16 markers.

Per-host result summary:

| Host | Mode | State | Statements | No forbidden keys | Marker ok |
|---|---|---|---:|---|---|
| `medivance` | graph-query.explain | explained | 8 | yes | yes |
| `medivance-homepage` | graph-query.explain | explained | 8 | yes | yes |
| `medivance-pwa` | graph-query.explain | explained | 8 | yes | yes |
| `medivance-pwa.fix-chat-error` | graph-query.explain | explained | 8 | yes | yes |
| `medivance.feat-action-card-design-alignment` | graph-query.explain | explained | 8 | yes | yes |
| `medivance.feat-calendar-renewal` | graph-query.explain | explained | 8 | yes | yes |
| `medivance.feat-director-screen-redesign` | graph-query.explain | explained | 8 | yes | yes |
| `medivance.feat-hospital-hours-schedule-sync` | graph-query.explain | explained | 8 | yes | yes |
| `medivance.fix-chat-patient-share-read-policy` | graph-query.explain | explained | 8 | yes | yes |
| `medivance.fix-emr-patient-sync` | graph-query.explain | explained | 8 | yes | yes |
| `medivance.fix-gemini-webapi-3-5-flash` | graph-query.explain | explained | 8 | yes | yes |
| `medivance.fix-manual-therapy-treatment-document` | graph-query.explain | explained | 8 | yes | yes |
| `medivance.fix-reservation-block-all-cell-border` | graph-query.explain | explained | 8 | yes | yes |
| `medivance.fix-reservation-sheet` | graph-query.explain | explained | 8 | yes | yes |
| `medivance.fix-reservation-sheet-treatment-record` | graph-query.explain | explained | 8 | yes | yes |
| `medivance.fix-reservation-sheet-updates` | graph-query.explain | explained | 8 | yes | yes |

## Interpretation

- Graph Explain Phase 1 synced and smoke-validated on 16/16 initialized downstream hosts.
- Every downstream smoke produced JSON `graph-query.explain` structural output with cited statements and no forbidden semantic-authority fields.
- Managed graph-explain files hash-matched source, and graph seed rows were present downstream.
- The marker correction is a validation-script correction, not a framework behavior issue: `lazy-sync` wrote the documented JSON marker format.
- This evidence does not relax overview/read-debt/lifecycle/prompt/option-gate rules and does not make graph output semantic authority.

## Reproduce

1. From `/home/lazydino/dev/lazy-harness`, confirm source commit:

   ```bash
   git rev-parse dfd11ffe676500ad928c61789034835a81097ef1
   ```

2. Re-run source validation:

   ```bash
   python3 .lazy-harness/scripts/self-test.py --scope framework
   .lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=json --limit=8 --max-statements=8
   ```

3. Discover downstream hosts and run the sync/smoke shape from the Commands section for each host.
4. Inspect `/tmp/lazy-harness-graph-explain-phase1-sync/20260608T235202Z/corrected-summary.json` while it is retained locally.

## Related records

- `.lazy-harness/spec/platform/graph-explain.md`
- `.lazy-harness/tests/graph-explain.md`
- `.lazy-harness/planning/graph-explain-implementation-plan.md`
- `.lazy-harness/spec/platform/graph-query.md`
- `.lazy-harness/tests/graph-query.md`
- `.lazy-harness/spec/lazy-sync-drift-detection.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- `.lazy-harness/ssot/cli-tool-boundary.md`
- `.lazy-harness/knowledge/graph.jsonl#kg_graph_explain_phase1_downstream_sync_20260608`

## Retention / privacy

- This capsule stores summaries, file paths, host names, commit hashes, aggregate validation counts, and per-host smoke counts only.
- Raw full logs remain in `/tmp` and Jcode background-task storage and are not canonical framework truth.
- No secrets, credentials, personal data, raw transcripts, raw assistant responses, or unrelated product data are included.
