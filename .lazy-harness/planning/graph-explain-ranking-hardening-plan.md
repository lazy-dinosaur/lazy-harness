# Graph Explain Ranking Hardening Plan

Status: planned-reviewed
Date: 2026-06-09
Layer: Planning
Related SDD: `.lazy-harness/spec/platform/graph-query.md`
Related SDD: `.lazy-harness/spec/platform/graph-explain.md`
Related TDD: `.lazy-harness/tests/graph-query.md`
Related TDD: `.lazy-harness/tests/graph-explain.md`
Related Planning: `.lazy-harness/planning/graph-query-coverage-ranking-hardening-plan.md`
Related Planning: `.lazy-harness/planning/retrieval-architecture-holistic-review.md`
Related Planning: `.lazy-harness/planning/graph-index-migration-considerations.md`
Related evidence: `.lazy-harness/evidence/2026-06-09-graph-explain-token-savings-accuracy.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## Goal

Improve Graphify-style top-context selection for `lazy graph query` / `lazy graph explain` without changing the cue-only, non-canonical, read-real-evidence boundary.

User-approved direction: implement the improvement only after planning, baseline validation, and independent review.

## Current verified baseline

Commands rerun before this plan:

```bash
python3 /tmp/graph-explain-gold-accuracy.py
.lazy-harness/bin/lazy retrieval-workflow-benchmark --format=json --limit=8
```

Gold-labeled graph-explain retrieval/ranking baseline:

- Scenario count: 8 total, 7 non-gap gold-labeled + 1 Korean unrelated gap.
- Gold labels: 33 human-selected must-include paths.
- Micro recall: `31/33 = 93.9%`.
- Macro recall: `94.3%`.
- Strict Precision@8: `21.4%`.
- MRR: `46.7%`.
- nDCG: `55.4%`.
- Layer recall: `100.0%`.
- Negative contamination: `0/8` scenarios.
- Gap accuracy: `100.0%`.
- Current interpretation: broad retrieval is good; top-k ranking and statement ordering are weak.

Retrieval workflow benchmark baseline:

- `graph_query.totalEstimatedTokens`: `69,170`.
- `graph_query.fullLayerCoverageCount`: `4/4`.
- `map_plus_retrieval_audit.totalEstimatedTokens`: `255,217`.
- `graph_query` remains the workflow token winner and must not regress above the audit path.

Representative rank failures:

- `retrieval-workflow-benchmark` gold records are found, but many rank around `11-16`, giving strict P@8 `0.0` for that scenario.
- `graph-explain-contract` canonical SDD/TDD/plan appear around ranks `8-10` after manifest/evidence/source statements.
- `workflow-compression` bridge records are found but may rank much lower than directly matched ADR/source/evidence records.
- `lazy-sync-drift-detection` misses selected plan/evidence records, even though spec/source paths are found.

## Independent review summary

Reviewer conclusion: direction is right, but implementation must be tightened.

Risks called out:

1. **Overfitting gold labels** — keep labels in fixtures, avoid query-specific special cases.
2. **Graph-row dominance** — current explain statement order can let graph rows consume top slots before canonical records.
3. **Bridge records displacing exact matches** — layer bridges are useful, but should fill missing layers after direct matches.
4. **Boundary regression** — scores must be internal only; output must not emit confidence, required-read, importance, or semantic labels.
5. **Token creep** — score/provenance reasons must be capped and compactness must stay a gate.

Reviewer-recommended strategy:

- Use one deterministic internal `candidateScore` ledger keyed by canonical path/id.
- Direct path/title/slug/alias/feature/route phrase matches dominate.
- Evidence propagation from graph rows, implementation hits, citations, and path packets adds capped support with decay.
- Layer bridge records are fill slots only, capped at 1-2 slots for missing layers.
- Statement ranking must be separate from seed order, sorted by target candidate score.
- Prefer canonical record/source/test/planning/evidence statements before generic graph-row statements when scores are comparable.
- Dedupe by canonical target path/id.

## Direction lock

Allowed in this slice:

- Add a permanent gold-labeled retrieval accuracy benchmark fixture/script.
- Add deterministic internal scoring/ranking in `graph-query.ts`.
- Reorder candidate arrays and graph-explain statements using internal scores.
- Preserve current output shape while improving ordering.
- Update SDD/TDD/self-test/evidence/graph rows/manifest if implementation changes.

Forbidden in this slice:

- No Graphify vendoring, Python runtime, MCP server, daemon, watch mode, prompt injection, overview/read-debt policy relaxation, or lifecycle hook behavior changes.
- No semantic-authority output fields: `requiredRead`, `optionalRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, `candidateMeanings`, `importance`, or score fields.
- No hard-coded query-specific boosting for the gold fixture.
- No fake records or synthetic canonical facts to improve metrics.
- No weakening of existing self-test, token compactness, gap, read-only, or no-forbidden-field guards.

## Proposed implementation plan

### Phase 0 — Permanent benchmark first

Create permanent fixture and runner before changing ranking:

- Fixture file, e.g. `.lazy-harness/fixtures/graph-explain-gold-accuracy.json`.
- Script, e.g. `.lazy-harness/scripts/graph-explain-accuracy-benchmark.ts`.
- CLI or test entrypoint can be private to `lazy test` first; no new public command required unless useful.

Metrics:

- micro/macro recall
- strict Precision@8
- MRR
- nDCG
- layer recall
- negative contamination count
- gap accuracy
- token/byte compactness
- read-only watched-file hashes
- recursive forbidden-field absence

### Phase 1 — Candidate score ledger

Inside `graph-query.ts`, introduce internal-only scoring:

- Key by canonical path/id.
- Add direct match signals:
  - exact path or basename match
  - title/slug/alias/feature/route phrase coverage
  - query token coverage in path/title/header before body/digest
- Add supporting signals:
  - record-index related records
  - graph row source/target/path links
  - implementation-index file/symbol hits
  - citations and existing candidate arrays
- Add decay/caps:
  - repeated evidence from same source type has diminishing returns
  - cap provenance/reasons for internal diagnostics only
  - deterministic tie-break: score desc, directness tier, layer priority for named contracts, path lexicographic

Output must not expose scores unless a future debug-only artifact is separately approved.

### Phase 2 — Direct-match-first, bridge-as-fill ranking

Reorder `candidates.recordPaths`, `sourceFiles`, `testFiles`, and graph-explain statement targets:

1. direct exact path/title/feature/contract matches
2. source/test/planning/evidence tied to direct records
3. graph row/path support linked to those records
4. missing-layer bridge fills, capped and only when direct result lacks that layer
5. generic graph-row/support statements

Layer bridge policy:

- Fill missing layer slots only after direct matches.
- Cap to 1-2 bridge slots per output window.
- Never push direct exact SDD/TDD/Planning/evidence records below top 8.

### Phase 3 — Statement ranking independent of seed order

Build structural statements as candidates, then rank/dedupe them:

- Dedupe by canonical target path/id.
- Prefer `record`, `source`, `test`, `path`/`candidate_context`, then `graph-edge`/`graph-row` when scores are comparable.
- Keep every statement support-backed and citation-backed.
- Keep `--max-statements` cap deterministic.
- Preserve path-backed boundary: zero-edge/self paths are not path evidence; `candidate_context` remains endpoint-presence only.

### Phase 4 — Evidence links for sync/drift gaps

The gold baseline shows `lazy-sync-drift-detection` misses selected plan/evidence paths.

Fix by adding real graph/record links only if justified by existing records:

- Link `.lazy-harness/spec/lazy-sync-drift-detection.md` to selected sync plan/evidence when the records truly describe that workflow.
- Do not create fake links for metric wins.
- Update Implementation map / graph rows with source-read evidence.

## Acceptance gates

### Must not regress

- Micro recall `>= 31/33`.
- Macro recall `>= 94%`.
- Layer recall `= 100%`.
- Negative contamination scenarios `= 0`.
- Gap accuracy `= 100%`.
- Existing `retrieval-workflow-benchmark` `graph_query.fullLayerCoverageCount >= 4/4`.
- `graph_query.totalEstimatedTokens <= 72,629` (current `69,170` plus 5%).
- `graph_query.totalEstimatedTokens < map_plus_retrieval_audit.totalEstimatedTokens`.
- Recursive forbidden semantic-authority field check passes.
- Read-only mutation guard passes.
- Full framework self-test passes.

### Initial ranking improvement target

- Strict Precision@8 `>= 50%`.
- MRR `>= 70%`.
- nDCG `>= 75%`.
- No gold-labeled scenario with strict P@8 `0.0` unless the scenario is explicitly marked broad/non-top-k by fixture metadata.

### Stretch target after first pass

- Strict Precision@8 `>= 65%`.
- nDCG `>= 85%`.

## Validation commands

```bash
# Baseline/benchmark runner after Phase 0 and after each ranking change
.lazy-harness/bin/lazy graph explain 'retrieval workflow benchmark graph query map retrieval audit token followup read' --format=json --limit=20 --max-statements=20
.lazy-harness/bin/lazy graph explain 'graph explain contract semantic authority citation support path-backed' --format=json --limit=20 --max-statements=20
.lazy-harness/bin/lazy graph explain 'workflow compression not safety reduction' --format=json --limit=20 --max-statements=20
.lazy-harness/bin/lazy graph explain '강아지 산책 날씨 완전 무관한 문장' --format=json --limit=20 --max-statements=20

# Permanent benchmark once created
bun .lazy-harness/scripts/graph-explain-accuracy-benchmark.ts --format=json

# Existing workflow and framework guards
.lazy-harness/bin/lazy retrieval-workflow-benchmark --format=json --limit=8
python3 .lazy-harness/scripts/self-test.py --scope framework
.lazy-harness/bin/lazy test
```

## Cross-layer impact assessment

- DDD: no new domain concept required unless the permanent benchmark introduces a named retrieval-quality term; if so, add to searchable-record-memory terminology.
- BDD: user-visible behavior remains cue-only navigation; no workflow/policy relaxation.
- SDD: graph-query/graph-explain contracts need updates if ranking order or benchmark output becomes part of contract.
- TDD: add permanent gold accuracy fixture and self-test/benchmark guard.
- ADR: not required unless adopting Graphify vendoring/MCP/prompt policy changes; those are forbidden in this slice.
- SSOT: `cli-tool-boundary.md` remains controlling boundary; scores stay internal and output non-authoritative.

## Implementation map

- Planning record: `.lazy-harness/planning/graph-explain-ranking-hardening-plan.md`.
- Candidate implementation file: `.lazy-harness/scripts/graph-query.ts`.
- Candidate benchmark fixture: `.lazy-harness/fixtures/graph-explain-gold-accuracy.json`.
- Candidate benchmark script: `.lazy-harness/scripts/graph-explain-accuracy-benchmark.ts`.
- Existing validation source: `.lazy-harness/scripts/self-test.py`.
- Existing SDD/TDD records:
  - `.lazy-harness/spec/platform/graph-query.md`
  - `.lazy-harness/spec/platform/graph-explain.md`
  - `.lazy-harness/tests/graph-query.md`
  - `.lazy-harness/tests/graph-explain.md`
- Existing evidence baseline: `.lazy-harness/evidence/2026-06-09-graph-explain-token-savings-accuracy.md`.

## Discovery capture

- User asked to improve and harden top/ranking behavior in a Graphify-inspired way.
- Baseline verification and independent review were completed before implementation.
- Plan outcome: implementation is not started yet; next step is Phase 0 permanent benchmark, then ranking changes behind measurable gates.

## Rule placement

- Rule: Graphify-style ranking hardening must use internal deterministic scores only, keep output cue-only/non-authoritative, and be gated by gold-labeled ranking metrics plus existing read-only/no-forbidden-field guards.
- Scope: framework-global planning
- Primary record: `.lazy-harness/planning/graph-explain-ranking-hardening-plan.md`
- Why not AGENTS.md: this is an implementation plan and acceptance criteria, not always-loaded prompt grammar.
- Why not `.jcode`: shared framework retrieval architecture work, not local/private Jcode preference.
