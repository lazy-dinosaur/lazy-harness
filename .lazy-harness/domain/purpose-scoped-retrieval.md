# Map-First Retrieval Vocabulary

Status: accepted
Layer: DDD
Date: 2026-06-22
Related ADR: `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`

## Domain vocabulary

**Context retrieval** is the activity of recovering host/project context before answering, planning, or editing.

**Project map traversal** means starting from a project-map/index overview, choosing a concrete node, and following linked records/source/tests.

**Map node** means a concrete feature id, record path, graph id, source path, or test path surfaced by `lazy map --overview` or a canonical record.

**LLM-owned search** means the model/searcher chooses meanings, candidate records, and next reads from map evidence, record bodies, source, tests, and root-bound search. The CLI does not own semantic search.

**Purpose-scoped find** was the retired idea that a CLI could search a small purpose-specific space from a query. Dogfood showed this encouraged CLI-owned search and is no longer active.

## Rule digest

- Status: active
- Layer: DDD
- Scope: framework-global
- Applies when:
  - discussing record search vs project map traversal
  - changing retrieval CLI behavior
  - deciding whether helpers should accept raw user text
- Must:
  - treat records as project-map branches, not isolated search hits
  - keep meaning selection LLM/searcher-owned
  - preserve cue-only boundaries for generated/index/map output
- Must not:
  - use CLI output as semantic authority
  - infer purpose from raw prompts in lifecycle hooks
  - reintroduce `lazy find --purpose ...` as a default retrieval path
- Record completion:
  - changes update ADR/BDD/SDD/TDD and SSOT CLI boundary together

## Implementation map

- Source:
  - `.lazy-harness/scripts/record-map.ts`
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh`
- Records:
  - `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`
  - `.lazy-harness/behavior/purpose-scoped-retrieval.md`
  - `.lazy-harness/tests/purpose-scoped-retrieval.md`
- Tests:
  - `.lazy-harness/scripts/self-test.py#check_purpose_scoped_retrieval_cli`
