# TDD — Retrieval Coverage Audit

Status: accepted
Date: 2026-06-08
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/retrieval-coverage-audit.md`
Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related SDD: `.lazy-harness/spec/platform/record-index-header.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - implementing or changing `lazy retrieval-audit`
  - changing `lazy map` or `record-index` output that retrieval audit consumes
  - evaluating whether a concrete map traversal gap has adequate fallback/read coverage
- Must:
  - protect `mapped`, `partial`, and `gap` coverage states
  - protect fallback command output for empty/partial coverage
  - protect cue-only/no semantic-authority output shape
  - protect that retrieval audit is read-only and does not mutate canonical records or generated caches
  - protect help/dispatcher wiring for `lazy retrieval-audit`
- Must not:
  - allow required-read, optional-read, confidence, intent, risk, gate, next-action, or candidate-meaning fields
  - treat an empty audit as proof of absence
  - record audit output as canonical knowledge by itself
- Record completion:
  - implementation changes update SDD, this TDD, self-test, source, CLI help, and graph rows.

## Fixture matrix

| Fixture id | Scenario | Expected |
|---|---|---|
| `retrieval_audit_mapped` | Query matches feature/record/graph and has record/source/test candidates | `coverage.state=mapped`, no gaps, candidates populated, concrete map-node commands use surfaced ids/paths |
| `retrieval_audit_cross_layer_related_records` | Query matches an SDD that declares top-level Related DDD/BDD/SSOT/TDD links | related DDD/BDD/SDD/SSOT/TDD record paths all appear in `candidates.recordPaths` |
| `retrieval_audit_partial` | Query matches a record but has no source/test hints | `coverage.state=partial`, structural gap labels include source/test gaps, fallback commands present |
| `retrieval_audit_gap` | Query has no matches | `coverage.state=gap`, `no-map-matches` and fallback grep command present; no raw-query `lazy map` command is emitted |
| `retrieval_audit_no_semantic_fields` | Any audit output | Forbidden semantic-authority fields are absent recursively |
| `retrieval_audit_help_wiring` | `lazy help` | command is advertised and routes through `.lazy-harness/bin/lazy` |

## Implementation map

- Status: verified
- Primary files:
  - `.lazy-harness/scripts/retrieval-coverage-audit.ts` — CLI under test.
  - `.lazy-harness/bin/lazy` — dispatcher/help wiring.
  - `.lazy-harness/scripts/self-test.py` — fixture and assertions.
  - `.lazy-harness/spec/platform/retrieval-coverage-audit.md` — SDD contract.
- Key symbols:
  - `check_retrieval_coverage_audit_cli`
  - `RetrievalCoverageAudit`
  - `coverage.state`
  - `coverage.gaps`
- Flow:
  1. Self-test builds a temp host with feature navigation, records, and graph row.
  2. `lazy retrieval-audit` runs mapped/partial/gap queries through the dispatcher.
  3. Assertions verify coverage state, cross-layer related-record candidates, candidate/fallback fields, and absence of semantic-authority fields.
- Machine index:
  - graph ids: `kg_retrieval_coverage_audit_cli_20260608`, `kg_retrieval_coverage_audit_self_test_20260608`, `kg_record_index_top_level_related_parser_20260608`, `kg_retrieval_audit_cross_layer_related_self_test_20260608`

## Layer completeness impact

- DDD: no new domain terms beyond searchable record memory; related DDD paths must be surfaced when linked.
- SDD: `.lazy-harness/spec/platform/retrieval-coverage-audit.md` defines the contract.
- BDD: LLM-owned retrieval behavior now explicitly requires search-time and final verification-time missing layer checks.
- TDD: this record and `check_retrieval_coverage_audit_cli` protect behavior.
- ADR: no new decision beyond ADR 0041 CLI/LLM boundary.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains canonical.

## Rule placement

- Rule: Retrieval coverage audit regression tests must prove structural coverage gaps and fallback commands without semantic authority.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/retrieval-coverage-audit.md`
- Why not AGENTS.md: this is test contract detail, not prompt grammar.
- Why not `.jcode`: shared lazy-harness regression behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed
