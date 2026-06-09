# Evidence: Graph Explain Phase 3 path-backed downstream sync

## Scope

This evidence capsule records cross-host sync and smoke validation for lazy-harness source commit `e8a0ca872b8e531fb0ca7e4ac2250cf613ce9941` (`feat(graph): add path-backed graph explain support`).

In scope:

- Sync the clean source checkout `/home/lazydino/dev/lazy-harness` to every initialized downstream host discovered under `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`.
- Verify each downstream host marker JSON has `syncedFromCommit` equal to `e8a0ca872b8e531fb0ca7e4ac2250cf613ce9941`.
- Verify managed Phase 3 graph-explain files match source hashes:
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/graph-query.ts`
  - `.lazy-harness/scripts/self-test.py`
  - `.lazy-harness/spec/platform/graph-explain.md`
  - `.lazy-harness/tests/graph-explain.md`
  - `.lazy-harness/planning/graph-explain-implementation-plan.md`
  - `.lazy-harness/planning/graph-path-implementation-plan.md`
  - `.lazy-harness/spec/platform/graph-query.md`
  - `.lazy-harness/spec/platform/project-rule-router.md`
  - `.lazy-harness/manifests/init-categories.json`
- Verify Phase 3 graph seed rows are present downstream:
  - `kg_graph_explain_phase3_path_cli_20260609`
  - `kg_graph_explain_phase3_path_self_test_20260609`
  - `kg_test_project_rule_placement_env_isolation_20260609`
- Verify `lazy graph explain --help` advertises path-backed structural packet support and has no stale unsupported-path-backed phrase.
- Verify JSON smoke returns `mode=graph-query.explain`, `explanationKind=structural`, cited/support-backed statements, `pathPackets`, edge-backed path support, no `no-path-evidence` gap, and zero forbidden semantic-authority fields.
- Verify path-backed guardrails: no invented `bounded_path` relation, no zero-edge/self path promoted into `support.kind=path`, and `candidate_context` wording stays limited to endpoint presence in the other query packet plus semantic-boundary language.
- Verify Markdown smoke returns `# Graph explain`, `## Path packets`, `path-backed:` support lines, support/citations on statement bullets, read-evidence/semantic-authority caveats, and no stale future-slice phrase.

Out of scope:

- Product app behavior, product unit/e2e suites, and downstream product commits.
- Pushing downstream repositories.
- Treating graph-explain output as proof that real evidence was read.
- Semantic authority, confidence scoring, gate/next-action recommendation, MCP, daemon, watch mode, prompt/reminder injection, Graphify vendoring, or lifecycle/read-debt policy changes.

## Environment

- Date: 2026-06-09
- Source root: `/home/lazydino/dev/lazy-harness`
- Source branch: `feature/map-first-record-navigation`
- Source commit synced: `e8a0ca872b8e531fb0ca7e4ac2250cf613ce9941`
- Source commit title: `feat(graph): add path-backed graph explain support`
- Host discovery: `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`, excluding the source checkout itself.
- Aggregate corrected smoke artifact: `/tmp/lazy-harness-graph-explain-phase3-path-corrected-smoke/20260609T014641Z/summary.json`
- Corrected smoke artifact directory: `/tmp/lazy-harness-graph-explain-phase3-path-corrected-smoke/20260609T014641Z`
- Corrected smoke background task: `601869t7to`
- Earlier over-strict sync/smoke task: `359430j18j`; it synced hosts successfully but used two false-negative checks that the corrected smoke replaced.

## Commands

Source validation before sync:

```bash
.lazy-harness/bin/lazy graph explain --help
.lazy-harness/bin/lazy graph explain \
  'workflow compression not safety reduction' \
  --format=json \
  --include-paths \
  --limit=8 \
  --max-statements=8
.lazy-harness/bin/lazy graph explain \
  'workflow compression not safety reduction' \
  --format=md \
  --include-paths \
  --limit=8 \
  --max-statements=8
python3 .lazy-harness/scripts/self-test.py --scope framework
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

Clean sync shape per host:

```bash
bun /home/lazydino/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts \
  --from /home/lazydino/dev/lazy-harness \
  --target <host> \
  --force \
  --quiet
```

Corrected smoke shape per host:

```bash
<host>/.lazy-harness/bin/lazy graph explain --help
<host>/.lazy-harness/bin/lazy graph explain \
  'workflow compression not safety reduction' \
  --format=json \
  --include-paths \
  --limit=8 \
  --max-statements=8
<host>/.lazy-harness/bin/lazy graph explain \
  'workflow compression not safety reduction' \
  --format=md \
  --include-paths \
  --limit=8 \
  --max-statements=8
```

Marker interpretation:

```bash
python3 - <<'PY_MARKER'
import json
marker = json.load(open('<host>/.lazy-harness/state/synced-from-commit'))
assert marker['syncedFromCommit'] == 'e8a0ca872b8e531fb0ca7e4ac2250cf613ce9941'
PY_MARKER
```

## Results

Source validation:

- Focused source JSON/Markdown `--include-paths` checks passed.
- Focused zero-edge guard passed: no invented `bounded_path` relation and no zero-edge/self path promoted into path support.
- Focused temp-host `candidate_context` smoke passed: statement said endpoint path appeared in the other query packet and preserved the semantic boundary.
- `python3 .lazy-harness/scripts/self-test.py --scope framework` completed successfully: 77 tests ran, 0 skipped.
- Commit hook for `e8a0ca872b8e` reported `✅ .lazy-harness/bin/lazy test all green`.
- Source branch `feature/map-first-record-navigation` was pushed to origin.

Aggregate corrected downstream smoke summary:

```json
{
  "summary": "/tmp/lazy-harness-graph-explain-phase3-path-corrected-smoke/20260609T014641Z/summary.json",
  "artifactDir": "/tmp/lazy-harness-graph-explain-phase3-path-corrected-smoke/20260609T014641Z",
  "source": "e8a0ca872b8e",
  "total": 16,
  "ok": 16,
  "failed": []
}
```

Per-host result summary:

| Host | JSON mode | JSON state | JSON statements | Path packets | Path supports | Markdown statements | Marker ok |
|---|---|---|---:|---:|---:|---:|---|
| `medivance` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance-homepage` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance-pwa` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance-pwa.fix-chat-error` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance.feat-action-card-design-alignment` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance.feat-calendar-renewal` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance.feat-director-screen-redesign` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance.feat-hospital-hours-schedule-sync` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance.fix-chat-patient-share-read-policy` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance.fix-emr-patient-sync` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance.fix-gemini-webapi-3-5-flash` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance.fix-manual-therapy-treatment-document` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance.fix-reservation-block-all-cell-border` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance.fix-reservation-sheet` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance.fix-reservation-sheet-treatment-record` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |
| `medivance.fix-reservation-sheet-updates` | graph-query.explain | explained | 8 | 3 | 3 | 8 | yes |

Additional corrected smoke assertions:

- All 16 hosts had marker match for `e8a0ca872b8e531fb0ca7e4ac2250cf613ce9941`.
- All 16 hosts had no managed file hash mismatches for the Phase 3 file set.
- All 16 hosts had required new graph seed rows present.
- All 16 hosts produced 3 path packets, 3 edge-backed path packets, and 3 path support statements.
- All 16 hosts had `candidate_context` path statements with the required semantic-boundary wording.
- All 16 hosts had no zero-edge-only target promoted into path support.
- All 16 hosts had no forbidden semantic-authority keys in JSON output.
- Existing changed seed rows with preexisting IDs were conflict-preserved in downstream `graph.jsonl.conflicts.jsonl`, which is expected lazy-sync behavior for host-local graph history preservation.

## Interpretation

The corrected smoke proves that commit `e8a0ca872b8e531fb0ca7e4ac2250cf613ce9941` can be synced to all currently initialized downstream hosts and that the synced `lazy graph explain --include-paths` command preserves the Phase 3 structural contract across those hosts.

It specifically supports the claims that:

- `--include-paths` produces downstream `pathPackets` and path-backed statements when edge-backed indexed paths exist.
- `candidate_context` remains a structural fallback explanation and does not claim semantic connection or causality.
- zero-edge/self paths are not turned into path evidence.
- JSON/Markdown output remains cue-only and does not include semantic-authority fields.

It does not prove product app behavior, product test suites, or that any agent has read the cited records/source/tests. Evidence capsules support, but do not supersede, the SDD/TDD/source records.

The earlier task `359430j18j` used two over-strict checks: it hashed one host-owned/non-manifest test record and checked an older Markdown caveat phrase. Corrected task `601869t7to` removed those false-negative assumptions and is the durable aggregate used for this capsule.

## Reproduce

1. Check out `/home/lazydino/dev/lazy-harness` at or after commit `e8a0ca872b8e531fb0ca7e4ac2250cf613ce9941`.
2. Run the source focused checks and `python3 .lazy-harness/scripts/self-test.py --scope framework`.
3. Discover downstream hosts with `.lazy-harness/state/synced-from-commit` under `/home/lazydino/dev/*`.
4. For each host, run `bun /home/lazydino/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts --from /home/lazydino/dev/lazy-harness --target <host> --force --quiet`.
5. Run `lazy graph explain --help`, JSON `--include-paths`, and Markdown `--include-paths` smoke commands from each host.
6. Compare with `/tmp/lazy-harness-graph-explain-phase3-path-corrected-smoke/20260609T014641Z/summary.json` if it is still retained locally.

## Related records

- `.lazy-harness/spec/platform/graph-explain.md`
- `.lazy-harness/tests/graph-explain.md`
- `.lazy-harness/planning/graph-explain-implementation-plan.md`
- `.lazy-harness/spec/platform/graph-path.md`
- `.lazy-harness/tests/graph-path.md`
- `.lazy-harness/spec/lazy-sync-drift-detection.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- `.lazy-harness/tests/evidence-capsule-standard.md`
- `.lazy-harness/knowledge/graph.jsonl`
- `.lazy-harness/manifests/init-categories.json`
- Source commit: `e8a0ca872b8e531fb0ca7e4ac2250cf613ce9941`

## Retention / privacy

This capsule stores summarized validation evidence, command shapes, host names, commit hashes, and artifact paths. It does not include secrets, credentials, personal data, raw transcripts, raw assistant responses, raw tool-event payloads, or product data. The `/tmp/lazy-harness-graph-explain-phase3-path-corrected-smoke/20260609T014641Z` artifacts are local ephemeral smoke summaries; retain or delete them according to local disk policy.
