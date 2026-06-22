# SDD — Retrieval Coverage Audit

Status: accepted
Date: 2026-06-08
Layer: SDD
Related DDD: `.lazy-harness/domain/searchable-record-memory.md`
Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related SDD: `.lazy-harness/spec/platform/record-index-header.md`
Related TDD: `.lazy-harness/tests/retrieval-coverage-audit.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - `lazy map` output is empty, ambiguous, or too narrow
  - an agent needs to prove it considered fallback grep/read coverage before relying on absence
  - adding generated navigation/query surfaces such as Graphify-style indexes
- Must:
  - provide a read-only coverage audit over record-index, feature navigation, and graph surfaces
  - report structural gaps such as no record/source/test/graph candidates
  - emit overview/concrete-map-node/fallback-grep commands as evidence cues
  - state that the LLM/searcher remains the semantic search engine and must read real records/source/tests
  - keep output deterministic, compact, and capped by `--limit`
- Must not:
  - decide user intent, risk, confidence, gates, required reads, next action, or candidate meanings
  - treat absence of CLI matches as semantic proof that knowledge is absent
  - mutate canonical records, generated indexes, runtime journals, or user memory
- Record completion:
  - changes update this SDD, TDD, CLI dispatcher/help, source, self-test, and graph rows together.

## CLI contract

Command:

```bash
.lazy-harness/bin/lazy retrieval-audit '<term-or-file>' --format=json --limit=8
```

Output shape:

- `mode: retrieval-coverage-audit`
- `coverage.state`: `mapped | partial | gap`
- `coverage.gaps`: structural gap labels only, e.g. `no-map-matches`, `no-record-candidates`, `no-source-candidates`, `no-test-candidates`, `no-graph-candidates`
- `matches`: feature/record/graph matches and matched fields
- `candidates`: record/source/test/graph candidates and fallback search terms, including top-level Related layer record paths surfaced from matched records
- `commands`: overview, concrete map-node commands copied from structural candidates, and fallback grep command
- `notes`: cue-only/LLM-owned semantic authority reminder

Forbidden fields: `requiredRead`, `optionalRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, `candidateMeanings`.

## Behavior

1. LLM/searcher starts with `lazy map --overview`.
2. If concrete map traversal is empty or suspiciously narrow, LLM/searcher may call `lazy retrieval-audit <query>` as a read-only coverage backstop.
3. Audit reports whether map/index/graph surfaces yielded structural entrypoints.
4. When matched records declare top-level Related DDD/BDD/SDD/TDD/ADR/SSOT links, audit includes those paths as cue-only record candidates so search and final verification can check for missing impacted layers.
5. For `gap` or `partial`, LLM/searcher follows concrete map-node candidates and fallback grep, then reads real record/source/test files.
6. If evidence remains missing or ambiguous, LLM/searcher uses an option gate or MultiCandidate record-decision packet. The audit itself never becomes the answer.

## Implementation map

- Status: verified
- Primary files:
  - `.lazy-harness/scripts/retrieval-coverage-audit.ts` — read-only CLI implementation.
  - `.lazy-harness/bin/lazy` — exposes `lazy retrieval-audit`.
  - `.lazy-harness/scripts/record-index.ts` — provides deterministic record/feature/graph index input, including top-level Related layer record paths.
  - `.lazy-harness/scripts/self-test.py` — regression coverage.
- Key symbols:
  - `buildAudit`
  - `RetrievalCoverageAudit`
  - `coverage.state`
  - `coverage.gaps`
- Flow:
  1. CLI builds a fresh record index from canonical records, feature navigation, and graph rows.
  2. CLI matches query against structural fields only.
  3. CLI emits gap labels, candidate paths, related-record paths, and fallback commands.
  4. LLM/searcher reads the surfaced files and remains the semantic authority.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_retrieval_coverage_audit_cli`
  - `.lazy-harness/tests/retrieval-coverage-audit.md`
- Machine index:
  - graph ids: `kg_retrieval_coverage_audit_cli_20260608`, `kg_retrieval_coverage_audit_self_test_20260608`, `kg_record_index_top_level_related_parser_20260608`, `kg_retrieval_audit_cross_layer_related_self_test_20260608`

## Layer completeness impact

- DDD: `searchable-record-memory` terminology remains unchanged; retrieval audit is a new tool over existing memory/index concepts.
- SDD: this record defines the CLI contract.
- BDD: `llm-owned-record-retrieval` behavior is reinforced: CLI is a cue provider, LLM reads and judges; search/final validation must check related layer candidates for missing DDD/BDD/SSOT/TDD impacts.
- TDD: `.lazy-harness/tests/retrieval-coverage-audit.md` and self-test protect gap/partial/mapped behavior.
- ADR: no new trade-off decision; ADR 0041 already defines CLI/LLM boundary.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains canonical.

## Rule placement

- Rule: Retrieval coverage audit is a framework-global read-only CLI that surfaces structural coverage gaps and fallback commands without semantic authority.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/retrieval-coverage-audit.md`
- Why not AGENTS.md: this is a tool contract with implementation/test mapping; AGENTS may point to the workflow but should not be the only canonical store.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed
