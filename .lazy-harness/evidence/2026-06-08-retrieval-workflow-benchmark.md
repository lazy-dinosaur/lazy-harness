# Evidence: Retrieval Workflow Benchmark

## Scope

This evidence capsule records the first workflow-level retrieval benchmark after the graph-query payload compactness slice.

In scope:

- Compare post-overview helper paths for four representative framework queries:
  - `retrieval coverage audit`
  - `workflow compression not safety reduction`
  - `capability registry`
  - `lazy sync drift detection`
- Measure helper calls, helper bytes/tokens, deterministic follow-up record-read proxy, total estimated tokens, and full five-layer structural coverage count.
- Validate the benchmark helper is measurement-only, read-only, and has no forbidden semantic-authority fields.

Out of scope:

- Lifecycle, prompt, overview hard-block, option-gate, or read-debt policy changes.
- Proving semantic sufficiency of any candidate set.
- `lazy graph path` / `lazy graph explain` implementation.
- Raw user text classification or raw transcript analysis.

## Environment

- Date: 2026-06-08
- Source root: `/home/lazydino/dev/lazy-harness`
- Source branch: `feature/map-first-record-navigation`
- Preceding graph-query compactness commit: `25133d0 Compact lazy graph query payload`
- Benchmark command: `.lazy-harness/bin/lazy retrieval-workflow-benchmark --format=json --limit=8`
- Markdown command: `.lazy-harness/bin/lazy retrieval-workflow-benchmark --format=md --limit=8`

## Commands

```bash
.lazy-harness/bin/lazy retrieval-workflow-benchmark --format=json --limit=8
.lazy-harness/bin/lazy retrieval-workflow-benchmark --format=md --limit=8
python3 .lazy-harness/scripts/self-test.py --scope framework
```

## Results

Focused benchmark output:

```text
benchmark bytes 26839
aggregate totals {'map': 168057, 'map_plus_retrieval_audit': 173874, 'graph_query': 74236}
```

Aggregate metrics from JSON summary:

| Surface | Helper calls | Helper bytes | Helper est. tokens | Follow-up reads | Follow-up bytes | Follow-up est. tokens | Total est. tokens | Full layer coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `map` | 4 | 89,998 | 22,501 | 67 | 582,219 | 145,556 | 168,057 | 1/4 |
| `map_plus_retrieval_audit` | 8 | 112,111 | 28,030 | 68 | 583,372 | 145,844 | 173,874 | 1/4 |
| `graph_query` | 4 | 47,809 | 11,954 | 30 | 249,121 | 62,282 | 74,236 | 1/4 |

Deltas:

| Comparison | Helper call delta | Helper token delta | Total token delta |
|---|---:|---:|---:|
| `graph_query` vs `map_plus_retrieval_audit` | -4 | -16,076 | -99,638 |
| `graph_query` vs `map` | 0 | -10,547 | -93,821 |

Validation:

- `python3 .lazy-harness/scripts/self-test.py --scope framework` passed.
- Self-test count: scope=framework, ran=75, skipped=0.
- `retrieval workflow benchmark CLI ok` passed.
- The benchmark JSON recursively omitted forbidden semantic-authority fields.
- Markdown output included `measurement-only` and `does not change lifecycle/prompt/overview policy`.
- Read-only guard verified `.lazy-harness/knowledge/graph.jsonl` and `.lazy-harness/generated/record-index.json` did not mutate during the benchmark.

Downstream sync and smoke validation:

- Source commit synced: `f77e073f700cb55895afa6aa8094317c4591e89b` (`Add retrieval workflow benchmark`).
- Aggregate artifact: `/tmp/lazy-harness-retrieval-workflow-benchmark-sync/20260608T084456Z/summary.json`.
- Result: 14 downstream hosts discovered, 14 synced, 14 benchmark smokes passed, 0 failed.
- Smoke criteria: marker matches source commit, managed benchmark files hash-match source, `lazy help` advertises `retrieval-workflow-benchmark`, JSON benchmark output has `mode=retrieval-workflow-benchmark`, no forbidden semantic-authority fields, policy-boundary warning, read-only graph/record-index behavior, expected surfaces/helper call counts, and graph-query proxy win versus map-plus-retrieval-audit.

## Interpretation

What this evidence supports:

- `graph_query` is a workflow-level retrieval-cost win in this deterministic proxy compared with both `map` and `map_plus_retrieval_audit` for the four measured queries.
- The biggest proxy win comes from lower simulated follow-up read volume: 30 follow-up record reads for `graph_query` versus 67/68 for the other measured paths.
- `graph_query` also reduces helper payload tokens: 11,954 helper tokens versus 22,501 for `map` and 28,030 for `map_plus_retrieval_audit`.

What this evidence does not support by itself:

- It does not approve relaxing `lazy map --overview` or root-bound harness-first search/read debt.
- It does not prove graph-query candidates are semantically sufficient for a real task.
- It does not change lifecycle hooks, prompt packet injection, option gate behavior, or overview hard-blocks.
- It does not authorize `lazy graph path` or `lazy graph explain` implementation without a new SDD/TDD/plan slice.

## Reproduce

1. From `/home/lazydino/dev/lazy-harness`, run:

   ```bash
   .lazy-harness/bin/lazy retrieval-workflow-benchmark --format=json --limit=8
   .lazy-harness/bin/lazy retrieval-workflow-benchmark --format=md --limit=8
   python3 .lazy-harness/scripts/self-test.py --scope framework
   ```

   Downstream sync/smoke summary while retained locally:

   ```bash
   cat /tmp/lazy-harness-retrieval-workflow-benchmark-sync/20260608T084456Z/summary.json
   ```

2. Confirm JSON fields:

   - `mode == "retrieval-workflow-benchmark"`
   - surfaces include `map`, `map_plus_retrieval_audit`, and `graph_query`
   - policy boundary includes `measurement-only`
   - forbidden semantic-authority fields are absent

3. Treat output as measurement evidence only. Real task work still requires reading actual records/source/tests.

## Retention / privacy

- This capsule stores aggregate metrics, command names, query labels, paths, and counts only.
- No raw user prompt, transcript, personal data, credentials, or unrelated product data are included.
- Raw temporary benchmark output is not canonical framework truth.

## Related records

- `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md`
- `.lazy-harness/tests/retrieval-workflow-benchmark.md`
- `.lazy-harness/planning/retrieval-workflow-benchmark-plan.md`
- `.lazy-harness/ssot/cli-tool-boundary.md`
- `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md`
- `.lazy-harness/knowledge/graph.jsonl#kg_retrieval_workflow_benchmark_cli_20260608`

## Rule placement

- Rule: Workflow benchmark results are evidence capsules, not policy-changing rules.
- Scope: framework-global
- Primary record: `.lazy-harness/evidence/2026-06-08-retrieval-workflow-benchmark.md`
- Why not AGENTS.md: benchmark evidence is point-in-time validation data, not always-loaded prompt grammar.
- Why not `.jcode`: shared framework evidence, not local/private Jcode-only execution preference.
- Confirmation: inferred-from-record
