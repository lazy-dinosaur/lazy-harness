# Graph CLI Rollback Plan

Status: executed-in-progress
Date: 2026-06-15
Layer: Planning
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md`
Related TDD: `.lazy-harness/tests/retrieval-workflow-benchmark.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: framework-global
- Applies when:
  - reverting Graphify-inspired `lazy graph query/path/explain` CLI behavior
  - restoring the default retrieval workflow to `lazy map`, `lazy find`, `retrieval-audit`, grep/source/test reads, and real record reads
- Must:
  - remove graph query/path/explain command routing and implementation files
  - remove active SDD/TDD/evidence rows that require graph query/path/explain commands
  - keep non-graph retrieval improvements such as record-index/map, purpose-scoped retrieval, rulebook/capability work, and retrieval-audit
  - preserve the cue-only/non-semantic-authority boundary for remaining CLI helpers
  - validate help output, removed-command failure, benchmark output, and framework self-test
- Must not:
  - reset the whole branch to `da6417b` or `main` because that would discard unrelated useful changes
  - leave active tests requiring removed graph commands
  - let deleted graph rows remain as active implementation evidence

## Execution summary

User-confirmed intent: return to pre-graph-CLI retrieval behavior, not merely hide graph CLI from prompts.

Implemented direction:

- Remove `.lazy-harness/scripts/graph-query.ts`.
- Remove `.lazy-harness/scripts/graph-explain-accuracy-benchmark.ts`.
- Remove `lazy graph ...` and `lazy graph-explain-accuracy-benchmark` dispatcher/help entries.
- Remove active graph query/path/explain SDD/TDD records and evidence capsules.
- Update retrieval workflow benchmark to compare `map` and `map_plus_retrieval_audit` only.
- Update purpose-scoped retrieval fallback commands to use `lazy map` and grep instead of removed graph query.
- Filter active `knowledge/graph.jsonl` rows that refer to removed graph CLI commands/files.

## Implementation map

- `.lazy-harness/bin/lazy` — removed graph command routing/help.
- `.lazy-harness/scripts/retrieval-workflow-benchmark.ts` — removed graph query benchmark surface.
- `.lazy-harness/scripts/purpose-find.ts` — removed graph query fallback command suggestions.
- `.lazy-harness/scripts/self-test.py` — removed graph query/path/explain/accuracy tests and updated benchmark assertions.
- `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md` — updated benchmark contract after removal.
- `.lazy-harness/tests/retrieval-workflow-benchmark.md` — updated regression expectations after removal.
- `.lazy-harness/ssot/cli-tool-boundary.md` — updated active cue helper list.
- `.lazy-harness/knowledge/graph.jsonl` — removed active graph CLI implementation/evidence rows.

## Discovery capture

- DDD: none.
- BDD: existing LLM-owned retrieval behavior remains, with graph CLI no longer an active helper.
- SDD: graph query/path/explain SDDs removed; retrieval benchmark SDD updated.
- TDD: graph query/path/explain TDDs removed; retrieval benchmark TDD updated.
- ADR: none.
- SSOT: CLI boundary updated.
- Planning: this rollback plan captures the user-confirmed removal decision and execution checklist.
