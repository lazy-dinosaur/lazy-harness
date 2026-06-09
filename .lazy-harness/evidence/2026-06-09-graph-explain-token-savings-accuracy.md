# Evidence: Graph Explain Token Savings + Citation Accuracy

## Scope

This capsule records a focused, read-only measurement answering the user request to verify, code-side, how many tokens `lazy graph explain` saves and how accurate it is.

In scope:

- Measure the `graph explain` Markdown surface token cost vs. the read cost of every record/file it cites, for four representative framework queries.
- Measure citation accuracy: fraction of explain citation/support references that resolve to a real graph row, real on-disk file, or real `feature-navigation.xml` feature id.
- Validate gap-query behavior (no false citations on a missing term).
- Validate path-backed (`--include-paths`) accuracy.
- Confirm the existing explain contract guard (`check_graph_explain_cli`) still passes.

Out of scope:

- Lifecycle, prompt, overview, option-gate, or read-debt policy changes.
- Proving semantic sufficiency of any candidate set (explain stays cue-only).
- New permanent CLI surface (this is an ad-hoc measurement, not a shipped command).

## Environment

- Date: 2026-06-09
- Source root: `/home/lazydino/dev/lazy-harness`
- Source branch: `main`
- Explain implementation commit baseline: `e8a0ca8` (`feat(graph): add path-backed graph explain support`), records synced through `e5c082b`.
- Token estimate: `bytes/4` (same convention as `retrieval-workflow-benchmark.ts`).
- Measurement script (temp, read-only): `/tmp/explain-bench/measure.py`.
- Graph index size at measurement time: graph ids=467, sources=406, targets=310; plus 9 feature ids from `feature-navigation.xml`.

## Commands

```bash
# Live surface sizes
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=md --limit=8 | wc -c
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=json --limit=8 | wc -c

# Focused token-savings + accuracy measurement (4 queries)
python3 /tmp/explain-bench/measure.py

# Gap query: must emit zero statements / zero citations
.lazy-harness/bin/lazy graph explain 'zzzz-missing-term-xyz' --format=json --limit=8

# Path-backed accuracy
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=json --limit=8 --include-paths

# Contract guard
python3 .lazy-harness/scripts/self-test.py --scope framework
```

## Results

Per-query (limit=8, Markdown surface vs. cited-record read proxy):

| Query | State | Stmts | Explain tok | Cited files | Read tok | Savings tok | Savings % | Refs | Real | Accuracy % |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| retrieval coverage audit | explained | 8 | 1116 | 6 | 120919 | 119803 | 99.1 | 16 | 16 | 100.0 |
| workflow compression not safety reduction | explained | 8 | 1190 | 5 | 104384 | 103194 | 98.9 | 16 | 16 | 100.0 |
| capability registry | explained | 8 | 1120 | 6 | 24941 | 23821 | 95.5 | 16 | 16 | 100.0 |
| lazy sync drift detection | explained | 8 | 1113 | 5 | 15290 | 14177 | 92.7 | 16 | 16 | 100.0 |

Aggregate:

- Explain surface tokens (Markdown): 4,539
- Cited-record read tokens (proxy): 265,534
- Token savings: 260,995 (98.3% reduction)
- Citation references: 64
- References resolving to a real graph row / real file / real feature id: 64
- Citation accuracy: 100.0%

Robustness:

- Gap query `zzzz-missing-term-xyz`: `resultState=gap`, 0 statements, gaps listed (`no-seeds`, `no-citations`, `no-structural-statements`, ...). No false citation on a missing term.
- Path-backed (`--include-paths`): 8 statements, 3 path packets, 16/16 references real (100.0%).

Validation:

- `python3 .lazy-harness/scripts/self-test.py --scope framework` passed: `ran=77, skipped=0`, exit 0.
- The explain contract guard `check_graph_explain_cli` (cited/structural JSON+Markdown, recursive forbidden-field absence, `--include-paths` packets, zero-edge/self path non-evidence, `candidate_context` boundary wording, read-only behavior) remained green.

Measurement-script correctness note:

- A first run reported 87.5% accuracy on two queries because the resolver did not yet include `feature-navigation.xml` feature ids. The two "unresolved" references (`capability-registry`, `sync-install-update`) are real feature ids with `provenance: feature-navigation` that explain cited correctly. After adding feature ids to the resolver, accuracy is 100.0%. The gap was in the measurement script, not in explain output.

## Interpretation

What this evidence supports:

- The `graph explain` Markdown surface is a large structural-retrieval token win: ~1,100 tokens per query versus 14k–121k tokens to read every cited record, a 98.3% aggregate reduction on the four measured queries.
- Explain is structurally faithful: every citation/support reference resolved to a real graph row, real on-disk file, or real feature id (100.0%, 64/64). Combined with the gap-query result, explain does not invent structure.
- The win is consistent with prior `graph_query` retrieval benchmark evidence: explain is a thin cited layer over the same query packet.

What this evidence does not support:

- It does not prove explain candidates are semantically sufficient for a real task. Explain is cue-only; the LLM/searcher must still read real records/source/tests.
- "Accuracy" here means citation/structure fidelity (no hallucinated references), not semantic correctness, intent, or sufficiency.
- The token-savings figure is a read-cost proxy (sum of cited record bytes), not a measured end-to-end agent transcript.
- It does not authorize relaxing overview-first/read-debt policy or adding semantic authority.

## Reproduce

1. From `/home/lazydino/dev/lazy-harness`, run `python3 /tmp/explain-bench/measure.py` (temp artifact; the resolver loads graph ids/sources/targets from `.lazy-harness/knowledge/graph.jsonl` and feature ids from `.lazy-harness/project/feature-navigation.xml`).
2. Confirm aggregate: explain tokens ~4,539, read tokens ~265k, savings ~98.3%, accuracy 100.0%.
3. Run the gap query and confirm `resultState=gap` with 0 statements.
4. Run `--include-paths` and confirm 100% reference resolution.
5. Run `python3 .lazy-harness/scripts/self-test.py --scope framework` and confirm `ran=77, skipped=0`, exit 0.
6. Treat output as measurement evidence only; real task work still requires reading actual records/source/tests.

## Related records

- `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- `.lazy-harness/spec/platform/graph-explain.md`
- `.lazy-harness/tests/graph-explain.md`
- `.lazy-harness/planning/graph-explain-implementation-plan.md`
- `.lazy-harness/evidence/2026-06-09-graph-explain-phase3-path-downstream-sync.md`
- `.lazy-harness/evidence/2026-06-08-retrieval-workflow-benchmark.md`
- `.lazy-harness/ssot/cli-tool-boundary.md`
- `.lazy-harness/scripts/self-test.py#check_graph_explain_cli`

## Retention / privacy

- This capsule stores aggregate metrics, command names, query labels, paths, and counts only.
- No raw user prompt, transcript, assistant response, personal data, credentials, or unrelated product data are included.
- The temporary `/tmp/explain-bench/` measurement script and JSON summary are not canonical framework truth.

## Rule placement

- Rule: Token-savings/accuracy measurement results are evidence capsules, not policy-changing rules.
- Scope: framework-global
- Primary record: `.lazy-harness/evidence/2026-06-09-graph-explain-token-savings-accuracy.md`
- Why not AGENTS.md: benchmark evidence is point-in-time validation data, not always-loaded prompt grammar.
- Why not `.jcode`: shared framework evidence, not local/private Jcode-only execution preference.
- Confirmation: inferred-from-record
