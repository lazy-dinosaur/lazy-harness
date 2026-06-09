# Evidence: Graph Explain Token Savings + Citation Accuracy

## Scope

This capsule records a focused, read-only measurement answering the user request to verify, code-side, how many tokens `lazy graph explain` saves and how accurate it is.

In scope:

- Measure the `graph explain` Markdown surface token cost vs. the read cost of every record/file it cites, first for four representative framework queries and then for an expanded 27-scenario matrix.
- Measure citation accuracy: fraction of explain citation/support references that resolve to a real graph row/source/target, real on-disk file, real `feature-navigation.xml` feature id, or output-local `queryPacket.subgraph.edges` edge id.
- Validate gap-query behavior (no false citations on missing/unrelated terms, including Korean text).
- Validate path-backed (`--include-paths`) accuracy.
- Validate feature-id, layer-record, source-path, record-path, graph-id, and `--max-statements` bound scenarios.
- Confirm the existing explain contract guard (`check_graph_explain_cli`) still passes.

Out of scope:

- Lifecycle, prompt, overview, option-gate, or read-debt policy changes.
- Proving semantic sufficiency of any candidate set (explain stays cue-only).
- New permanent CLI surface (this is an ad-hoc measurement, not a shipped command).

## Environment

- Date: 2026-06-09
- Source root: `/home/lazydino/dev/lazy-harness`
- Source branch: `feature/map-first-record-navigation`
- Explain implementation commit baseline: `e8a0ca8` (`feat(graph): add path-backed graph explain support`), records synced through `e5c082b`.
- Token estimate: `bytes/4` (same convention as `retrieval-workflow-benchmark.ts`).
- Measurement scripts (temp, read-only): `/tmp/explain-bench/measure.py` and `/tmp/explain-matrix.py`.
- Graph index size at measurement time: graph ids=467, sources=406, targets=310; plus 9 feature ids from `feature-navigation.xml`.
- Re-audit note: rerun on the same source branch after committing this evidence capsule kept the four-query headline result (`98.3%` Markdown-vs-full-cited-read reduction and `64/64` citation references real), but current cited-file sizes changed the full-read proxy from 265,534 to 265,724 tokens because the manifest/records grew. Expanded matrix rerun after user challenge covered 27 scenarios and produced `97.7%` Markdown-vs-full-cited-read reduction with `410/410` real structural references.

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

# Expanded scenario matrix (post-question re-audit)
python3 /tmp/explain-matrix.py
cat /tmp/explain-matrix-summary.json

# Contract guard
python3 .lazy-harness/scripts/self-test.py --scope framework
```

## Results

Per-query (limit=8, Markdown surface vs. cited-record read proxy):

| Query | State | Stmts | Explain tok | Cited files | Read tok | Savings tok | Savings % | Refs | Real | Accuracy % |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| retrieval coverage audit | explained | 8 | 1116 | 6 | 121014 | 119898 | 99.1 | 16 | 16 | 100.0 |
| workflow compression not safety reduction | explained | 8 | 1190 | 5 | 104384 | 103194 | 98.9 | 16 | 16 | 100.0 |
| capability registry | explained | 8 | 1120 | 6 | 25036 | 23916 | 95.5 | 16 | 16 | 100.0 |
| lazy sync drift detection | explained | 8 | 1113 | 5 | 15290 | 14177 | 92.7 | 16 | 16 | 100.0 |

Aggregate:

- Explain surface tokens (Markdown): 4,539
- Cited-record read tokens (proxy): 265,724
- Token savings: 261,185 (98.3% reduction)
- Citation references: 64
- References resolving to a real graph row / real file / real feature id: 64
- Citation accuracy: 100.0%

Robustness:

- Gap query `zzzz-missing-term-xyz`: `resultState=gap`, 0 statements, gaps listed (`no-seeds`, `no-citations`, `no-structural-statements`, ...). No false citation on a missing term.
- Path-backed (`--include-paths`): 8 statements, 3 path packets, 16/16 references real (100.0%).

Validation:

- `python3 .lazy-harness/scripts/self-test.py --scope framework` passed: `ran=77, skipped=0`, exit 0.
- The explain contract guard `check_graph_explain_cli` (cited/structural JSON+Markdown, recursive forbidden-field absence, `--include-paths` packets, zero-edge/self path non-evidence, `candidate_context` boundary wording, read-only behavior) remained green.

Expanded scenario matrix after user re-challenge:

- Scenario count: 27
- Categories covered: original benchmark, feature ids/aliases, DDD/BDD/SDD/TDD/ADR/SSOT/planning layer queries, source-path queries, record-path query, graph-id queries, path-backed queries, `--max-statements` bound cases, and two gap/unrelated queries including Korean text.
- Passed scenarios: 27/27
- Result states: 25 explained, 2 gap
- Citation/support references: 410/410 resolved to a real on-disk path, real graph row/source/target, real feature id, or output-local `queryPacket.subgraph.edges` edge id.
- Citation accuracy: 100.0% under the structural-reference definition.
- Forbidden semantic-authority fields: 0 occurrences.
- Missing statement support/citations: 0 occurrences.
- Read-only watched files mutated: 0 (`graph.jsonl`, `record-index.json`, `implementation-index.json`).
- Non-gap aggregate, Markdown explain vs. full cited-file read proxy: 29,860 tokens vs. 1,292,086 tokens, 97.7% reduction.
- Non-gap aggregate, Markdown explain vs. graph-query JSON helper payload: 57.3% smaller.
- Non-gap aggregate, JSON explain vs. graph-query JSON helper payload: 94.8% larger, because JSON explain embeds `queryPacket` plus structural statements/path packets.

Important diagnostic from the expanded matrix:

- A first expanded run appeared to fail the `--max-statements=20` bound case because the resolver did not count output-local compact edge ids like `g:...--relation-->r:...` as real.
- Source inspection showed graph-edge statements intentionally cite `queryPacket.subgraph.edges` compact source/target ids. After adding that local-edge check, the bound case resolved 40/40 references and the whole matrix passed 27/27.
- This means the correct structural accuracy definition is not only "global graph row or on-disk file"; it is "real on-disk path, real graph row/source/target, real feature id, or real output-local subgraph edge id".

Additional re-audit comparison against `graph query` helper payloads:

- Total `graph explain --format=md` tokens across the four queries: 4,539
- Total `graph explain --format=json` tokens across the four queries: 18,147
- Total `graph query --format=json` tokens across the four queries: 12,013
- Markdown explain is 62.2% smaller than graph-query JSON helper payloads in this sample.
- JSON explain is 51.1% larger than graph-query JSON helper payloads because it embeds the query packet plus explanation statements. Therefore the 98.3% headline must be read as Markdown explain vs. full cited-record reads, not JSON explain vs. graph-query helper output.

Measurement-script correctness note:

- A first run reported 87.5% accuracy on two queries because the resolver did not yet include `feature-navigation.xml` feature ids. The two "unresolved" references (`capability-registry`, `sync-install-update`) are real feature ids with `provenance: feature-navigation` that explain cited correctly. After adding feature ids to the resolver, accuracy is 100.0%. The gap was in the measurement script, not in explain output.

## Interpretation

What this evidence supports:

- The `graph explain` Markdown surface is a large structural-retrieval token win against the full-cited-record-read proxy: ~1,100 tokens per query versus 15k–121k tokens to read every cited record, a 98.3% aggregate reduction on the four measured queries.
- Explain is structurally faithful in the expanded 27-scenario matrix: every citation/support reference resolved to a real on-disk path, real graph row/source/target, real feature id, or real output-local subgraph edge id (100.0%, 410/410). Combined with the gap-query results, explain did not invent structure in the tested scenarios.
- Compared to `graph query --format=json` helper output only, Markdown explain is smaller in this sample, but JSON explain is larger because it carries both queryPacket and structural statements. Use the 98.3% number only for the Markdown-vs-full-cited-record-read proxy.

What this evidence does not support:

- It does not prove explain candidates are semantically sufficient for a real task. Explain is cue-only; the LLM/searcher must still read real records/source/tests.
- It does not prove universal behavior over every possible query. It now covers a 27-scenario framework matrix, not just the original 4-query sample, but it remains a representative test matrix.
- "Accuracy" here means citation/structure fidelity (no hallucinated references), not semantic correctness, intent, or sufficiency. The expanded matrix uses the corrected structural-reference definition: on-disk path, graph row/source/target, feature id, or output-local subgraph edge id.
- The token-savings figure is a read-cost proxy (sum of cited record bytes), not a measured end-to-end agent transcript. Current re-audit total is 265,724 proxy tokens; the original 265,534 value was from the immediately preceding snapshot before the evidence/manifest growth.
- It does not authorize relaxing overview-first/read-debt policy or adding semantic authority.

## Reproduce

1. From `/home/lazydino/dev/lazy-harness`, run `python3 /tmp/explain-bench/measure.py` (temp artifact; the resolver loads graph ids/sources/targets from `.lazy-harness/knowledge/graph.jsonl` and feature ids from `.lazy-harness/project/feature-navigation.xml`).
2. Confirm current aggregate: explain Markdown tokens ~4,539, cited-record read proxy tokens ~265,724, savings ~98.3%, accuracy 100.0%.
3. Run the gap query and confirm `resultState=gap` with 0 statements.
4. Run `--include-paths` and confirm 100% reference resolution.
5. Run `python3 .lazy-harness/scripts/self-test.py --scope framework` and confirm `ran=77, skipped=0`, exit 0.
6. For the expanded scenario matrix, run `python3 /tmp/explain-matrix.py` while the temp artifact is retained and confirm 27/27 scenarios pass, 410/410 references resolve, no forbidden fields appear, no watched files mutate, and non-gap Markdown-vs-full-read proxy reduction is ~97.7%.
7. Treat output as measurement evidence only; real task work still requires reading actual records/source/tests.

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
