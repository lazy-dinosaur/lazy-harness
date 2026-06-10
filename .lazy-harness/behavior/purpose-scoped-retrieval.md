# BDD — Purpose-Scoped Retrieval

Status: accepted
Layer: BDD
Date: 2026-06-10
Related DDD: `.lazy-harness/domain/purpose-scoped-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`
Related TDD: `.lazy-harness/tests/purpose-scoped-retrieval.md`

## Rule digest

- Status: active
- Layer: BDD
- Scope: framework-global
- Applies when:
  - an agent chooses where to search for context
  - an agent differentiates project facts from operating rules or test validation needs
- Must:
  - start fact questions from records/source/test/config evidence
  - start operating-rule questions from rulebook/capability surfaces
  - start test questions from TDD/test/source-test/validation capability surfaces
  - escalate to broader records only when needed
- Must not:
  - require broad record sweeps for pure rulebook/test/capability lookup
  - classify raw user text in lifecycle hooks
- Record completion:
  - behavior changes update SDD/TDD/DDD/ADR together

## Scenarios

### Scenario 1 — Fact lookup uses records

Given the agent needs project contract or implementation facts
When it runs purpose-scoped retrieval with `--purpose fact`
Then it receives record/graph/source candidates
And still reads actual files before relying on them.

### Scenario 2 — Operating rule lookup avoids broad fact sweep

Given the agent needs to know how to act under project policy
When it runs `lazy find --purpose rulebook <query>`
Then rulebook and capability candidates are surfaced first
And broad DDD/SDD/ADR/SSOT records are not the default search space.

### Scenario 3 — Test lookup starts from tests

Given the agent needs validation or regression surfaces
When it runs `lazy find --purpose test <query>`
Then TDD records, source test files, and validation capabilities are surfaced first
And contract/behavior/config records are an escalation path only.

### Scenario 4 — Architecture remains broad

Given the agent is planning a design or mutation with cross-layer risk
When it runs `lazy find --purpose architecture <query>` or `--purpose full`
Then broad record/source/test/graph/rulebook/capability candidates are allowed.

## Implementation map

- Source:
  - `.lazy-harness/scripts/purpose-find.ts`
  - `.lazy-harness/bin/lazy`
- Tests:
  - `.lazy-harness/tests/purpose-scoped-retrieval.md`
  - `.lazy-harness/scripts/self-test.py#check_purpose_scoped_retrieval_cli`
