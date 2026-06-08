# Evidence: Graph Query Coverage and Ranking Hardening

## Scope

This evidence capsule records graph-query coverage/ranking hardening after the retrieval workflow benchmark showed `graph_query` was a workflow-cost win but had full DDD/BDD/SDD/TDD/SSOT follow-up coverage for only 1 of 4 benchmark queries.

In scope:

- Deterministic layer bridge/ranking improvements in `lazy graph query`.
- Verification that `workflow compression not safety reduction` graph-query candidates include DDD/BDD/SDD/TDD/SSOT at `--limit=8`.
- Verification that workflow benchmark `graph_query` full-layer coverage improves beyond the 1/4 baseline.
- Verification that graph-query keeps its token win over `map_plus_retrieval_audit`.
- Verification that existing compactness and no-semantic-authority guards remain intact.

Out of scope:

- `lazy graph path` or `lazy graph explain` implementation.
- Lifecycle, prompt, overview hard-block, read-debt, or option-gate policy changes.
- Treating bridge records as required-read proof.
- Inventing generated/fake DDD/BDD records.

## Environment

- Date: 2026-06-08
- Source root: `/home/lazydino/dev/lazy-harness`
- Previous benchmark commit: `78fca52 Record workflow benchmark downstream sync`
- Validation command: `python3 .lazy-harness/scripts/self-test.py --scope framework`

## Commands

```bash
bun .lazy-harness/scripts/graph-query.ts --root "$PWD" query 'workflow compression not safety reduction' --format=json --limit=8
bun .lazy-harness/scripts/graph-query.ts --root "$PWD" query 'retrieval coverage audit' --format=json --limit=20
.lazy-harness/bin/lazy retrieval-workflow-benchmark --format=json --limit=8
python3 .lazy-harness/scripts/self-test.py --scope framework
```

## Results

Focused graph query:

```text
workflow graph bytes 13046
coverage {'DDD': True, 'BDD': True, 'SDD': True, 'TDD': True, 'SSOT': True}
retrieval compact bytes 29751 state mapped
```

Workflow benchmark after hardening:

```text
aggregate {'map': 170594, 'map_plus_retrieval_audit': 176460, 'graph_query': 68713}
full coverage graph 4 / 4
```

Self-test:

```text
lazy-harness self-test ok (scope=framework, ran=75, skipped=0)
```

Downstream sync and adjusted smoke validation:

```text
source a8dea0c2180a
total 14
ok 14
failed []
summary /tmp/lazy-harness-graph-query-coverage-hardening-adjusted-sync/20260608T123646Z/summary.json
```

Downstream smoke criteria:

- marker commit and sourceRoot match source commit `a8dea0c2180a23e3982f76ce477356a525621e03`,
- managed graph-query/source/test/record/manifest files hash-match source,
- `lazy graph query 'workflow compression not safety reduction' --format=json --limit=8` returns `mapped` and includes DDD/BDD/SDD/TDD/SSOT candidates,
- graph-query output has no forbidden semantic-authority fields,
- `lazy retrieval-workflow-benchmark --format=json --limit=8` remains measurement-only and keeps `graph_query` token win over `map_plus_retrieval_audit`,
- graph/record-index files do not mutate during the smoke.

Note: downstream hosts have host-local record differences. The source benchmark acceptance remains `graph_query.fullLayerCoverageCount == 4/4`; downstream smoke validates direct graph-query five-layer coverage plus benchmark token win rather than requiring every host-local aggregate benchmark to be exactly 4/4.

## Before / after

| Metric | Before coverage hardening | After coverage hardening |
|---|---:|---:|
| `graph_query` full-layer coverage | 1/4 | 4/4 |
| `graph_query` total estimated tokens | 74,236 | 68,713 |
| `map_plus_retrieval_audit` total estimated tokens | 173,874 | 176,460 |
| `graph_query` token delta vs map-plus | -99,638 | -107,747 |
| `retrieval coverage audit` compact payload guard | below 40,000 bytes | 29,751 bytes |

## Interpretation

What this evidence supports:

- Graph-query layer bridge/ranking hardening fixed the measured full-layer coverage miss for the benchmark query set.
- The token/tool-cost advantage over `map_plus_retrieval_audit` was preserved and improved in this deterministic proxy.
- The hardening stayed inside the cue-only boundary: no forbidden semantic-authority fields, no policy change, no `path`/`explain` implementation.

What this evidence does not support by itself:

- It does not approve relaxing mandatory overview/search/read evidence rules.
- It does not make bridge records semantic proof that the right evidence was read.
- It does not approve lifecycle or prompt injection changes.
- It does not authorize `lazy graph path` or `lazy graph explain` without a new SDD/TDD/plan slice.

## Reproduce

1. Run the commands in the Commands section.
2. Confirm:
   - workflow graph query includes DDD/BDD/SDD/TDD/SSOT record paths,
   - retrieval compact payload remains below 40,000 bytes,
   - workflow benchmark `graph_query.fullLayerCoverageCount == 4`,
   - `graph_query.totalEstimatedTokens < map_plus_retrieval_audit.totalEstimatedTokens`,
   - full self-test passes.
3. For downstream smoke, confirm the adjusted sync summary while retained locally:

   ```bash
   cat /tmp/lazy-harness-graph-query-coverage-hardening-adjusted-sync/20260608T123646Z/summary.json
   ```

## Retention / privacy

- This capsule stores aggregate metrics, command names, and validation summaries only.
- No raw user prompt, transcript, credentials, personal data, or unrelated product data are included.
- Temporary benchmark outputs are not canonical framework truth.

## Related records

- `.lazy-harness/spec/platform/graph-query.md`
- `.lazy-harness/tests/graph-query.md`
- `.lazy-harness/planning/graph-query-coverage-ranking-hardening-plan.md`
- `.lazy-harness/evidence/2026-06-08-retrieval-workflow-benchmark.md`
- `.lazy-harness/ssot/cli-tool-boundary.md`
- `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- `.lazy-harness/domain/searchable-record-memory.md`
- `.lazy-harness/knowledge/graph.jsonl#kg_graph_query_coverage_ranking_hardening_20260608`

## Rule placement

- Rule: Coverage/ranking hardening evidence is validation evidence, not a policy-changing rule.
- Scope: framework-global
- Primary record: `.lazy-harness/evidence/2026-06-08-graph-query-coverage-ranking-hardening.md`
- Why not AGENTS.md: point-in-time validation evidence is not prompt grammar.
- Why not `.jcode`: shared framework evidence, not local/private Jcode-only execution preference.
- Confirmation: inferred-from-record
