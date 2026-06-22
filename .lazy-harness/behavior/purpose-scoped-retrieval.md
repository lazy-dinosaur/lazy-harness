# BDD — Map-First Retrieval

Status: accepted
Layer: BDD
Date: 2026-06-22
Related DDD: `.lazy-harness/domain/purpose-scoped-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`
Related TDD: `.lazy-harness/tests/purpose-scoped-retrieval.md`

## Rule digest

- Status: active
- Layer: BDD
- Scope: framework-global
- Applies when:
  - an agent chooses where to look for context
  - an agent differentiates project facts, expectations, contracts, validation, ownership, and source links
- Must:
  - start from `lazy map --overview` for host/project map inventory
  - let the LLM choose concrete map nodes from returned feature ids, record paths, graph ids, source paths, and test paths
  - use `lazy map <node>` only to expand a copied concrete node
  - read real record/source/test files before relying on any candidate
  - use `lazy rules resolve` / `lazy capability resolve` for operating-rule/action policy lookup
- Must not:
  - use `lazy find --purpose ...`
  - pass raw user text or long natural-language strings to `lazy map`
  - invent `--query` for `lazy map`
  - classify raw user text in lifecycle hooks
- Record completion:
  - behavior changes update SDD/TDD/DDD/ADR together

## Scenarios

### Scenario 1 — Project map overview first

Given the agent needs host-specific context
When it runs `lazy map --overview`
Then it sees feature anchors, layer records, graph relations, generated indexes, and drill-down candidates
And the LLM chooses which concrete node to inspect next.

### Scenario 2 — Concrete node traversal

Given the overview surfaces `record-source-indexing`
When the agent runs `lazy map record-source-indexing`
Then the CLI expands nearby records/source/tests/graph ids
And the agent reads actual files before answering.

### Scenario 3 — Free-form query rejected

Given the user says a long natural-language request
When the agent passes that whole request to `lazy map`
Then `lazy map` fails with a message to start from overview and use concrete map nodes.

### Scenario 4 — Rule lookup remains separate

Given the agent needs to know how to act under project policy
When it needs operating-rule guidance
Then it uses `lazy rules resolve` or `lazy capability resolve`, not fact/source search.

## Implementation map

- Source:
  - `.lazy-harness/scripts/record-map.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh`
- Tests:
  - `.lazy-harness/tests/purpose-scoped-retrieval.md`
  - `.lazy-harness/scripts/self-test.py#check_purpose_scoped_retrieval_cli`
