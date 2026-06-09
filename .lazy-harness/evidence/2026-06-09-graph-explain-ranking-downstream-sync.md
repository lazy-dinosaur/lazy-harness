# Evidence: Graph Explain Ranking + Hybrid Boundary Downstream Sync

## Scope

This capsule records cross-host sync and smoke validation for lazy-harness source commit `4014591` (`fix(graph): scope graph explain accuracy thresholds to source checkout`).

In scope:

- Sync the clean source checkout `/home/lazydino/dev/lazy-harness` to every initialized downstream host discovered under `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`.
- Verify each downstream host marker JSON has `syncedFromCommit` equal to source commit `4014591`'s full SHA.
- Verify selected managed files for graph-explain ranking hardening and dynamic hybrid boundary match source hashes.
- Verify required graph seed rows are present downstream:
  - `kg_graph_explain_ranking_hardening_plan_20260609`
  - `kg_graph_explain_ranking_hardening_phase4_20260609`
  - `kg_graph_explain_accuracy_benchmark_20260609`
  - `kg_dynamic_llm_hybrid_graph_boundary_20260609`
- Verify downstream `lazy help` advertises `graph-explain-accuracy-benchmark`.
- Verify downstream `lazy graph explain 'workflow compression not safety reduction' --format=json --limit=8 --max-statements=8` returns cue-only structural output with statements and no forbidden semantic-authority fields.
- Verify downstream `lazy graph-explain-accuracy-benchmark --format=json` runs as schema/policy smoke without source gold thresholds, has `mode=graph-explain-accuracy-benchmark`, `schemaVersion=1.0`, measurement-only boundary, zero forbidden-field scenarios, and no watched-file mutation.

Out of scope:

- Product app behavior, product unit/e2e suites, and downstream product commits.
- Running source gold thresholds on downstream product hosts. The gold labels target source framework records/evidence, so `--fail-on-thresholds` is source-checkout-only.
- Treating graph output as evidence that real records/source/tests were read.
- Semantic authority, confidence, gate/next-action recommendations, MCP, daemon, watch mode, or Graphify vendoring.

## Environment

- Date: 2026-06-09
- Source root: `/home/lazydino/dev/lazy-harness`
- Source branch: `feature/map-first-record-navigation`
- Source commit synced: `4014591` (`fix(graph): scope graph explain accuracy thresholds to source checkout`)
- Remote push: `origin/feature/map-first-record-navigation` updated through `4014591`
- Host discovery: `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`, excluding source checkout itself.
- Aggregate sync/smoke artifact: `/tmp/lazy-harness-graph-ranking-downstream-sync/20260609T055540Z/summary.json`
- Artifact directory: `/tmp/lazy-harness-graph-ranking-downstream-sync/20260609T055540Z`
- Background task: `540341glkv`
- Earlier task `9456665pmf` timed out and exposed a false deployment-gate assumption: source gold thresholds must not be required on downstream product hosts. That finding was fixed in commit `4014591` and this corrected smoke uses schema/policy checks downstream.

## Commands

Push source branch:

```bash
git push origin feature/map-first-record-navigation
```

Source validation after source-only threshold fix:

```bash
.lazy-harness/bin/lazy graph-explain-accuracy-benchmark --format=json --fail-on-thresholds
python3 .lazy-harness/scripts/self-test.py --scope framework
cd /home/lazydino/dev/medivance
.lazy-harness/bin/lazy graph-explain-accuracy-benchmark --format=json
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

Core sync/smoke retry script:

```bash
python3 /tmp/lazy-harness-downstream-sync-graph-ranking-core.py
```

Per-host sync shape:

```bash
bun /home/lazydino/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts \
  --from /home/lazydino/dev/lazy-harness \
  --target <host> \
  --force \
  --quiet
```

Per-host smoke shape:

```bash
<host>/.lazy-harness/bin/lazy help
<host>/.lazy-harness/bin/lazy graph explain \
  'workflow compression not safety reduction' \
  --format=json \
  --limit=8 \
  --max-statements=8
<host>/.lazy-harness/bin/lazy graph-explain-accuracy-benchmark --format=json
```

## Results

Corrected downstream core sync/smoke summary:

```json
{
  "summaryPath": "/tmp/lazy-harness-graph-ranking-downstream-sync/20260609T055540Z/summary.json",
  "artifactDir": "/tmp/lazy-harness-graph-ranking-downstream-sync/20260609T055540Z",
  "sourceShort": "4014591",
  "total": 16,
  "syncOk": 16,
  "markerOk": 16,
  "hashOk": 16,
  "graphRowsOk": 16,
  "helpOk": 16,
  "explainOk": 16,
  "accuracySmokeOk": 16,
  "failed": []
}
```

Hosts validated:

| Host | Sync | Marker | Hash | Graph rows | Help | Explain JSON | Accuracy smoke |
|---|---|---|---|---|---|---|---|
| `medivance` | ok | ok | ok | ok | ok | ok | ok |
| `medivance-homepage` | ok | ok | ok | ok | ok | ok | ok |
| `medivance-pwa` | ok | ok | ok | ok | ok | ok | ok |
| `medivance-pwa.fix-chat-error` | ok | ok | ok | ok | ok | ok | ok |
| `medivance.feat-action-card-design-alignment` | ok | ok | ok | ok | ok | ok | ok |
| `medivance.feat-calendar-renewal` | ok | ok | ok | ok | ok | ok | ok |
| `medivance.feat-director-screen-redesign` | ok | ok | ok | ok | ok | ok | ok |
| `medivance.feat-hospital-hours-schedule-sync` | ok | ok | ok | ok | ok | ok | ok |
| `medivance.fix-chat-patient-share-read-policy` | ok | ok | ok | ok | ok | ok | ok |
| `medivance.fix-emr-patient-sync` | ok | ok | ok | ok | ok | ok | ok |
| `medivance.fix-gemini-webapi-3-5-flash` | ok | ok | ok | ok | ok | ok | ok |
| `medivance.fix-manual-therapy-treatment-document` | ok | ok | ok | ok | ok | ok | ok |
| `medivance.fix-reservation-block-all-cell-border` | ok | ok | ok | ok | ok | ok | ok |
| `medivance.fix-reservation-sheet` | ok | ok | ok | ok | ok | ok | ok |
| `medivance.fix-reservation-sheet-treatment-record` | ok | ok | ok | ok | ok | ok | ok |
| `medivance.fix-reservation-sheet-updates` | ok | ok | ok | ok | ok | ok | ok |

Source validation summary:

- Source `graph-explain-accuracy-benchmark --fail-on-thresholds` passed with micro recall 100.0%, macro recall 100.0%, strict P@8 53.6%, MRR 100.0%, nDCG 92.9%, layer recall 100.0%, negative hit scenarios 0, gap accuracy 100.0%, forbidden-field scenarios 0, watched files mutated 0.
- Source framework self-test passed: 78 tests ran, 0 skipped.
- `medivance` downstream schema/policy smoke passed without source thresholds: mode `graph-explain-accuracy-benchmark`, 8 scenarios, forbidden-field scenarios 0, watched-file mutations `[]`.
- Commit hook for `4014591` reported `✅ .lazy-harness/bin/lazy test all green`.

## Interpretation

This evidence supports the claim that graph-explain ranking hardening, the source-only gold accuracy benchmark guard, and the dynamic hybrid graph boundary were pushed to the remote feature branch and synced to all 16 initialized downstream hosts discovered under `/home/lazydino/dev`.

It specifically supports:

- Source commit `4014591` is pushed and downstream markers match it.
- Managed graph-explain ranking/benchmark/boundary files match source hashes on every downstream host.
- Required graph seed rows exist in downstream `knowledge/graph.jsonl` stores.
- Downstream hosts expose the new `graph-explain-accuracy-benchmark` command.
- Downstream `graph explain` remains cue-only and emits no forbidden semantic-authority fields.
- Downstream accuracy benchmark command is usable as schema/policy smoke. Source gold thresholds remain source-checkout-only and are not a downstream deployment gate.

It does not prove product app behavior or product test suites. It also does not prove that downstream agents read the cited records/source/tests. Graph output remains generated/cue-only; canonical records/source/tests plus validation remain the source of truth.

## Reproduce

1. Check out `/home/lazydino/dev/lazy-harness` at commit `4014591` or later on `feature/map-first-record-navigation`.
2. Run source validation:
   ```bash
   .lazy-harness/bin/lazy graph-explain-accuracy-benchmark --format=json --fail-on-thresholds
   python3 .lazy-harness/scripts/self-test.py --scope framework
   ```
3. Discover initialized downstream hosts under `/home/lazydino/dev/*` with `.lazy-harness/state/synced-from-commit`.
4. For each host, run `lazy-sync --force --quiet` from source to target.
5. For each host, verify marker/hash/graph rows/help/explain/accuracy-smoke as in `/tmp/lazy-harness-downstream-sync-graph-ranking-core.py`.
6. Compare with `/tmp/lazy-harness-graph-ranking-downstream-sync/20260609T055540Z/summary.json` if local artifacts are retained.

## Related records

- `.lazy-harness/spec/platform/graph-explain.md`
- `.lazy-harness/tests/graph-explain.md`
- `.lazy-harness/planning/graph-explain-ranking-hardening-plan.md`
- `.lazy-harness/spec/lazy-sync-drift-detection.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- `.lazy-harness/tests/evidence-capsule-standard.md`
- `.lazy-harness/ssot/cli-tool-boundary.md`
- `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- `.lazy-harness/evidence/2026-06-09-graph-explain-token-savings-accuracy.md`
- Source commit: `4014591`

## Retention / privacy

This capsule stores summarized validation evidence, host names, command shapes, commit hashes, and local artifact paths. It does not include secrets, credentials, personal data, raw transcripts, raw assistant responses, raw tool-event payloads, or product data. The `/tmp/lazy-harness-graph-ranking-downstream-sync/20260609T055540Z` artifacts are local ephemeral smoke summaries; retain or delete according to local disk policy.

## Rule placement

- Rule: downstream product hosts should smoke `graph-explain-accuracy-benchmark` schema/policy without source gold thresholds; source gold threshold gates remain framework-source-only.
- Scope: framework-global deployment evidence
- Primary record: `.lazy-harness/evidence/2026-06-09-graph-explain-ranking-downstream-sync.md`
- Why not AGENTS.md: deployment evidence and benchmark interpretation, not prompt grammar.
- Why not `.jcode`: shared framework deployment evidence, not local/private Jcode preference.

## Discovery capture

- DDD: none.
- SDD: `.lazy-harness/spec/platform/graph-explain.md` already updated for source-only threshold/downstream smoke boundary.
- BDD: no new user-visible product flow; dynamic hybrid retrieval behavior already captured in `.lazy-harness/behavior/llm-owned-record-retrieval.md`.
- TDD: `.lazy-harness/tests/graph-explain.md` protects source-only threshold and downstream smoke boundary.
- ADR: none for this deployment; future Graphify watch/MCP/daemon adoption remains separate ADR scope.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains canonical semantic-boundary source.
- Planning: `.lazy-harness/planning/graph-explain-ranking-hardening-plan.md` records implementation and dynamic hybrid direction.
