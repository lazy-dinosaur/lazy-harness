# Evidence: Graph Explain Phase 2 Markdown downstream sync

## Scope

This evidence capsule records cross-host sync and smoke validation for lazy-harness source commit `4208c85758fac89ff22b5edcddefad358d547d2a` (`feat(graph): render graph explain markdown`).

In scope:

- Sync the clean source checkout `/home/lazydino/dev/lazy-harness` to every initialized downstream host discovered under `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`.
- Verify each downstream host marker JSON has `syncedFromCommit` equal to `4208c85758fac89ff22b5edcddefad358d547d2a`.
- Verify managed Phase 2 graph-explain files match source hashes:
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/graph-query.ts`
  - `.lazy-harness/scripts/self-test.py`
  - `.lazy-harness/spec/platform/graph-explain.md`
  - `.lazy-harness/tests/graph-explain.md`
  - `.lazy-harness/planning/graph-explain-implementation-plan.md`
  - `.lazy-harness/spec/platform/graph-query.md`
  - `.lazy-harness/manifests/init-categories.json`
- Verify Phase 2 graph seed rows are present downstream:
  - `kg_graph_explain_phase2_markdown_cli_20260609`
  - `kg_graph_explain_phase2_markdown_self_test_20260609`
- Verify `lazy help` advertises `graph explain <term-or-file> [--format=json|md]`.
- Verify JSON smoke returns `mode=graph-query.explain`, `explanationKind=structural`, 1..5 cited statements with support/citations, and zero forbidden semantic-authority fields.
- Verify Markdown smoke returns `# Graph explain`, cue-only/read-evidence warnings, `## Statements`, support/citations on statement bullets, LLM/searcher semantic-authority caveat, and no stale Phase 1 Markdown boundary phrase.

Out of scope:

- Product app behavior, product unit/e2e suites, and downstream product commits.
- Pushing downstream repositories.
- Treating graph-explain output as proof that real evidence was read.
- Implementing path-backed explain statements, MCP, daemon, watch mode, prompt/reminder injection, lifecycle/read-debt policy changes, or semantic authority.

## Environment

- Date: 2026-06-09
- Source root: `/home/lazydino/dev/lazy-harness`
- Source branch: `feature/map-first-record-navigation`
- Source commit synced: `4208c85758fac89ff22b5edcddefad358d547d2a`
- Source commit title: `feat(graph): render graph explain markdown`
- Host discovery: `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`, excluding the source checkout itself.
- Aggregate artifact: `/tmp/lazy-harness-graph-explain-phase2-markdown-sync/20260609T002238Z/summary.json`
- Background sync task: `5580968kd5`

## Commands

Source validation before sync:

```bash
python3 .lazy-harness/scripts/self-test.py --scope framework
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=md --limit=3 --max-statements=3
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
  --limit=5 \
  --max-statements=5
<host>/.lazy-harness/bin/lazy graph explain \
  'workflow compression not safety reduction' \
  --format=md \
  --limit=5 \
  --max-statements=5
```

Marker interpretation:

```bash
python3 - <<'PY_MARKER'
import json
marker = json.load(open('<host>/.lazy-harness/state/synced-from-commit'))
assert marker['syncedFromCommit'] == '4208c85758fac89ff22b5edcddefad358d547d2a'
PY_MARKER
```

## Results

Source validation:

- `python3 .lazy-harness/scripts/self-test.py --scope framework` completed successfully: 77 ran, 0 skipped.
- Commit hook for `4208c85758fa` reported `✅ .lazy-harness/bin/lazy test all green`.
- Source smoke returned Markdown with `# Graph explain`, cue-only/read-evidence warnings, support/citations on 3 statement bullets, and semantic-authority caveat.
- Source branch `feature/map-first-record-navigation` was pushed to origin.

Aggregate sync/smoke summary:

```json
{
  "summary": "/tmp/lazy-harness-graph-explain-phase2-markdown-sync/20260609T002238Z/summary.json",
  "source": "4208c85758fa",
  "total": 16,
  "ok": 16,
  "failed": []
}
```

Per-host result summary:

| Host | JSON mode | JSON state | JSON statements | Markdown statements | No forbidden keys | Marker ok |
|---|---|---|---:|---:|---|---|
| `medivance` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance-homepage` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance-pwa` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance-pwa.fix-chat-error` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance.feat-action-card-design-alignment` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance.feat-calendar-renewal` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance.feat-director-screen-redesign` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance.feat-hospital-hours-schedule-sync` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance.fix-chat-patient-share-read-policy` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance.fix-emr-patient-sync` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance.fix-gemini-webapi-3-5-flash` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance.fix-manual-therapy-treatment-document` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance.fix-reservation-block-all-cell-border` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance.fix-reservation-sheet` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance.fix-reservation-sheet-treatment-record` | graph-query.explain | explained | 5 | 5 | yes | yes |
| `medivance.fix-reservation-sheet-updates` | graph-query.explain | explained | 5 | 5 | yes | yes |

## Interpretation

- Graph Explain Phase 2 synced and smoke-validated on 16/16 initialized downstream hosts.
- graph explain Phase 2 evidence specifically covers both JSON and Markdown downstream smoke behavior.
- JSON/Markdown validation passed on every initialized downstream host.
- Every downstream JSON smoke produced structural `graph-query.explain` output with cited support-backed statements and no forbidden semantic-authority fields.
- Every downstream Markdown smoke produced cited/support-backed human-readable output and preserved cue-only/read-evidence/semantic-authority caveats.
- Managed Phase 2 files hash-matched source, and Phase 2 graph seed rows were present downstream.
- This evidence does not relax overview/read-debt/lifecycle/prompt/option-gate rules and does not make graph output semantic authority.

## Reproduce

1. From `/home/lazydino/dev/lazy-harness`, confirm source commit:

   ```bash
   git rev-parse 4208c85758fac89ff22b5edcddefad358d547d2a
   ```

2. Re-run source validation:

   ```bash
   python3 .lazy-harness/scripts/self-test.py --scope framework
   .lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=json --limit=5 --max-statements=5
   .lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=md --limit=5 --max-statements=5
   ```

3. Discover downstream hosts and run the sync/smoke shape from the Commands section for each host.
4. Inspect `/tmp/lazy-harness-graph-explain-phase2-markdown-sync/20260609T002238Z/summary.json` while it is retained locally.

## Related records

- `.lazy-harness/spec/platform/graph-explain.md`
- `.lazy-harness/tests/graph-explain.md`
- `.lazy-harness/planning/graph-explain-implementation-plan.md`
- `.lazy-harness/spec/platform/graph-query.md`
- `.lazy-harness/tests/graph-query.md`
- `.lazy-harness/spec/lazy-sync-drift-detection.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- `.lazy-harness/ssot/cli-tool-boundary.md`
- `.lazy-harness/knowledge/graph.jsonl#kg_graph_explain_phase2_downstream_sync_20260609`

## Retention / privacy

- This capsule stores summaries, file paths, host names, commit hashes, aggregate validation counts, and per-host smoke counts only.
- Raw full logs remain in `/tmp` and Jcode background-task storage and are not canonical framework truth.
- No secrets, credentials, personal data, raw transcripts, raw assistant responses, or unrelated product data are included.
