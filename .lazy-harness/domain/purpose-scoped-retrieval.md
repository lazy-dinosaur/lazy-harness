# Purpose-Scoped Retrieval

Status: accepted
Layer: DDD
Date: 2026-06-10
Related ADR: `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`

## Domain vocabulary

**Context retrieval** is the broad activity of finding host context before answering, planning, or editing.

**Fact retrieval** asks “what is true about this project?” It uses records, implementation maps, source, tests, config, and graph/source indexes as cues.

**Operating-rule retrieval** asks “how should I act in this project?” It starts with `.lazy-harness/rules/**`, `lazy rules`, and `lazy capability` surfaces.

**Test retrieval** asks “what validation/test surfaces matter?” It starts with TDD records, source tests, and validation capabilities.

**Purpose-scoped retrieval** means the LLM/user explicitly chooses a purpose and the retrieval tool searches only the smallest relevant cue space before widening.

## Rule digest

- Status: active
- Layer: DDD
- Scope: framework-global
- Applies when:
  - discussing record search vs context retrieval
  - changing retrieval CLI behavior
  - deciding whether broad record search is token waste
- Must:
  - treat records as one retrieval space, not the universal starting point
  - keep purpose selection explicit and LLM/user-owned
  - preserve cue-only boundaries
- Must not:
  - use CLI output as semantic authority
  - infer purpose from raw prompts in lifecycle hooks
- Record completion:
  - changes update ADR/BDD/SDD/TDD and SSOT CLI boundary together

## Implementation map

- Source:
  - `.lazy-harness/scripts/purpose-find.ts`
- Records:
  - `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`
  - `.lazy-harness/behavior/purpose-scoped-retrieval.md`
  - `.lazy-harness/tests/purpose-scoped-retrieval.md`
- Tests:
  - `.lazy-harness/scripts/self-test.py#check_purpose_scoped_retrieval_cli`
