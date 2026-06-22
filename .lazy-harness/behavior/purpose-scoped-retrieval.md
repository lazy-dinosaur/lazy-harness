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
  - ask a 3-5 option gate or state the missing prerequisite when no concrete node exists
  - use `lazy rules resolve` / `lazy capability resolve` for operating-rule/action policy lookup
- Must not:
  - use keyword grep/rg/find fallback after map traversal
  - use `lazy find --purpose ...`
  - pass raw user text or long natural-language strings to `lazy map`
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

### Scenario 3 — Free-form query and keyword fallback rejected

Given the user says a long natural-language request
When the agent passes that whole request to `lazy map` or reaches for grep/rg/find fallback after the overview
Then the flow rejects the query/fallback path and requires a concrete map node, option gate, or missing-prerequisite statement.

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
