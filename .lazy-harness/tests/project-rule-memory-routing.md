# Project Rule Memory Routing Regression

Status: accepted
Layer: TDD
Date: 2026-05-17
Related SDD: `.lazy-harness/spec/platform/project-rule-router.md`
Related SSOT: `.lazy-harness/ssot/rule-sources.md`

## Regression

A project/team workflow rule can be mistakenly stored through Jcode `memory.remember` as a preference. That makes the rule invisible to lazy-harness root-bound record search, bypasses implementation maps/graph edges, and repeats the same failure in future sessions or other hosts.

Observed pattern:

```text
User corrects: this is a project rule, not personal memory
Agent saves memory preference anyway
Agent later manually patches one host record instead of improving the framework guard
```

## Required protection

- `check-project-rule-placement.sh` must inspect `recent_tool_calls` for Jcode `memory.remember`.
- If the memory content looks like project/team workflow, ownership, source-of-truth, forbidden mutation, worktree, cwd, or `bun wt` policy, the helper must STOP.
- Same-turn `.lazy-harness` writes do not excuse the mistaken memory write. The memory must be forgotten and canonical record updated.
- Personal/local preferences remain allowed when they do not look like project/team policy.

## Layer completeness gate

- DDD: no domain/business terminology impact.
- SDD: project-rule router contract updated.
- BDD: user-visible behavior is that agents stop immediately instead of saying “saved to memory” for project rules.
- TDD: this record and `check_project_rule_placement_helper` protect the memory-misrouting regression.
- ADR: no new trade-off decision; ADR 0031/0032/0034 already require root-bound record convergence and correction capture.
- SSOT: rule placement registry updated to forbid Jcode memory as canonical project/team policy storage.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — detects project-rule `memory.remember` and emits STOP.
  - `.lazy-harness/scripts/self-test.py` — fixture blocks Medivance worktree/cwd rule stored in memory.
  - `.lazy-harness/spec/platform/project-rule-router.md` — SDD contract for memory misuse.
  - `.lazy-harness/ssot/rule-sources.md` — canonical placement registry forbidding memory for host/team policy.
- Key symbols:
  - `MEMORY_TOOLS`
  - `MEMORY_RULE_CUES`
  - `check_project_rule_placement_helper`
- Flow:
  1. Agent/user discusses a project/team rule.
  2. If agent calls `memory.remember` with rule-like content, response-completed helper emits STOP.
  3. Agent must `memory forget` the mistaken entry and create/update `.lazy-harness` canonical record.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/project-rule-router.md`
  - SSOT: `.lazy-harness/ssot/rule-sources.md`
- Machine index:
  - graph ids: `kg_tdd_project_rule_memory_routing`, `kg_hook_project_rule_memory_gate`, `kg_test_project_rule_memory_gate`
  - generated index key: `pending until implementation-index generator exists`
