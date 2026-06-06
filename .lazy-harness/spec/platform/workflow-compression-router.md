# Workflow Compression Router SDD — Superseded

Status: superseded
Layer: SDD
Superseded by: `.lazy-harness/ssot/cli-tool-boundary.md`
Related ADR: `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md`

## Rule digest

- Status: superseded
- Layer: SDD
- Scope: framework-global
- Applies when:
  - reading historical task-router/workflow-compression records
- Must:
  - treat the route classifier and route telemetry as removed/deferred
  - use `.lazy-harness/ssot/cli-tool-boundary.md` for current policy
- Must not:
  - reintroduce `lazy route`, route-summary, route-audit, or response.completed route telemetry without a new LLM-first ADR/SDD
- Record completion:
  - current CLI boundary changes update `.lazy-harness/ssot/cli-tool-boundary.md` and affected SDD/TDD records

## Supersession

The previous router classified raw user text into intent, risk, gate, record search, record capture, and validation axes. That conflicts with the current rule that CLI programs are tools only and the LLM/searcher owns semantic judgment after reading evidence.

## Replacement

Use deterministic candidate retrieval, graph/navigation maps, generated indexes, measurement, and validation tools. Do not let lifecycle hooks or CLIs decide importance, required reads, record-write need, gates, risk, or next action from user text.

## Implementation map

- Removed source:
  - task-router script and fixtures.
- Replacement records:
  - `.lazy-harness/ssot/cli-tool-boundary.md`
  - `.lazy-harness/spec/platform/context-delivery-contract.md`
  - `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md`
- Protection:
  - `.lazy-harness/scripts/self-test.py`
