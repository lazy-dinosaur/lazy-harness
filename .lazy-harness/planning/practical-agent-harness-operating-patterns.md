# Practical Agent Harness Operating Patterns

Status: accepted-reference
Layer: Planning
Created: 2026-05-18
Source: online research requested by user, plus existing `.lazy-harness/knowledge/upstream-references/oh-my-openagent-analysis.md`
Related planning: `.lazy-harness/planning/external-agent-harness-reference.md`
Related ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`

## Purpose

This record captures practical operating patterns for high-quality agent harness behavior: collaboration, subagents, swarm/team usage, persistent records, handoff artifacts, verification loops, and what agents should read/write during real work.

It is a reference landscape, not an implementation decision. Concrete adoption requires a follow-up ADR/spec/test plan.

## Core principle

Multi-agent orchestration is a cost, not a feature. Add agents only when they provide one of these concrete benefits:

1. **Separation of concerns**: planner/coder/reviewer/verifier see the work from different lenses.
2. **Parallelism**: independent files, independent hypotheses, independent review dimensions.
3. **Specialization**: different prompts, models, tools, or permission boundaries.
4. **Safety**: unprivileged workers propose, privileged coordinator/committer verifies and merges.

If none apply, use one agent plus strong records and validation.

## Deep-agent four pillars

External references converge on four pillars for long-running coding agents:

| Pillar | Practical meaning | Lazy-harness mapping |
|---|---|---|
| Explicit planning | Plan/todo is an inspectable artifact, not only chat text | `.lazy-harness/planning/**`, `todo`, option-gate decisions |
| Subagent delegation | Focused workers run in isolated context and return summaries | Jcode `subagent`, future SearchProvider/SubagentSearch, reviewer/searcher/coder roles |
| Persistent memory | Important state lives outside context window | `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning,knowledge}/`, graph JSONL, commits |
| Context engineering | Short entry instructions point to layered records and skills | `.lazy-harness/AGENTS.md` as grammar, records as vocabulary |

Remove any pillar and long tasks degrade: plans get forgotten, context saturates, handoffs lose state, or agents guess local conventions.

## Recommended collaboration shapes

### 1. Single-agent loop

Use for small, sequential, low-risk tasks.

Pattern:

1. Read relevant records.
2. Plan/todo.
3. Implement.
4. Run focused validation.
5. Update record if new fact/decision was confirmed.
6. Commit.

### 2. Orchestrator plus focused subagents

Use when the main context would be polluted by searches, reviews, or broad analysis.

Best subagent tasks:

- read-only codebase search and summarization,
- docs/OSS research,
- independent review,
- test execution / log summarization,
- visual inspection,
- second-opinion debugging.

Rules:

- Main agent owns intent, plan, final synthesis, and record updates.
- Subagents receive enough task-specific context because they do not inherit the full parent conversation.
- Subagents should return concise conclusions, evidence paths, and recommended next steps, not raw dumps.
- Prefer high parallelism for read-only subagents; limit write/build/test parallelism to avoid conflicts/backpressure.

### 3. Planner → executor → reviewer/verifier

Default multi-agent pattern for non-trivial implementation.

Roles:

- **Planner**: expands intent into constraints, plan, success criteria, and risk points. Should avoid over-specifying implementation details too early.
- **Executor/Coder**: implements one coherent chunk against the plan.
- **Reviewer/Verifier**: checks against original intent, code quality, tests, regression risk, and missing record updates.
- **Integrator/Coordinator**: owns final merge/commit/report and resolves conflicts.

Lazy-harness should map these to lifecycle layers rather than free-form personas.

### 4. Agent team / swarm

Use only when workers need peer-to-peer communication or dynamic shared task claiming.

Strong use cases:

- parallel PR review by separate lenses: security, performance, test coverage,
- competing-hypothesis debugging,
- cross-layer feature where frontend/backend/tests are independent enough,
- broad research where teammates challenge each other.

Avoid swarms for:

- one-line fixes,
- sequential tasks,
- same-file edits,
- docs-only tasks,
- tasks with tight dependencies.

Practical team size: start with 3 agents. Scale to 3-5 only when task boundaries are clean. More agents create coordination overhead and can reduce quality.

## Shared state and records

Good harnesses treat the repository as the system of record.

### State agents should read before acting

1. Relevant `.lazy-harness` layer records.
2. Current plan/todo/progress artifact.
3. Recent git history for handoff context.
4. Test strategy or validation record when changing code.
5. Ownership/SSOT records before touching config/schema/contracts.

### State agents should write after discovering facts

| Discovery | Target |
|---|---|
| Domain term/rule | `.lazy-harness/domain/**` |
| API/component/tool contract | `.lazy-harness/spec/**` |
| UI/user flow | `.lazy-harness/behavior/**` |
| Regression/test protection | `.lazy-harness/tests/**` |
| Why/trade-off | `.lazy-harness/decisions/**` |
| Source of truth/ownership/config/schema | `.lazy-harness/ssot/**` |
| Multi-step backlog/reference landscape | `.lazy-harness/planning/**` or `.lazy-harness/knowledge/candidates.jsonl` |
| Machine-readable relationship | `.lazy-harness/knowledge/graph.jsonl` |

### Scratchpad / notepad pattern

The oh-my-openagent reference uses per-plan notepads:

- `learnings.md`: conventions and successful patterns,
- `decisions.md`: architectural choices,
- `issues.md`: blockers/gotchas,
- `verification.md`: test and validation outcomes,
- `problems.md`: unresolved debt.

Lazy-harness candidate mapping: `.lazy-harness/notepads/<plan>/` or a planning subdirectory. This is useful for long tasks but should not replace canonical DDD/SDD/BDD/TDD/ADR/SSOT records.

## Session lifecycle pattern

Recommended lifecycle for long or resumable work:

1. **Orient**: read records, plan/progress, recent git log.
2. **Setup**: start/check environment.
3. **Baseline verify**: ensure current state works before edits.
4. **Select one coherent task**: highest-priority incomplete unit.
5. **Implement**: keep scope focused.
6. **Verify**: unit/integration/UI/e2e as appropriate.
7. **Review**: separate verifier or self-review with concrete criteria.
8. **Update state**: records, progress notes, graph facts, candidate backlog.
9. **Commit**: descriptive message doubles as handoff artifact.
10. **Clean exit**: working tree and next task are clear.

For multi-session tasks, commit messages should record: implemented work, passing tests, unresolved issues, and next priority.

## Verification and backpressure

Agents self-report success too optimistically. Good harnesses add backpressure:

- typecheck/lint/unit tests,
- focused regression tests,
- Playwright/browser UI verification when UI changes,
- static/security checks for risky changes,
- reviewer/critic agent that returns structured feedback,
- hook gates that block completion if todo/tests/records are incomplete.

OpenHands critic pattern: after an agent finishes, a critic scores result quality; if score is below threshold, the harness sends follow-up feedback and retries until threshold or max iterations.

Lazy-harness equivalent should prefer deterministic checks first, LLM critic second, and user option-gate when judgment/ambiguity remains.

## Hooks and gates worth studying

| Hook/gate | Purpose |
|---|---|
| Pre-tool dangerous command gate | block destructive commands before execution |
| Task-created gate | reject vague/oversized tasks |
| Task-completed gate | prevent marking complete without tests/records |
| Teammate/subagent idle gate | nudge worker to summarize, update state, or continue |
| Record-before-tool gate | enforce `.lazy-harness` search/read before host-specific action |
| Compaction/context injector | re-inject plan/progress/records after context compression |
| Todo continuation gate | prevent premature final answer while work remains |
| Drift detector | catch agents drifting from original intent or layer rules |

## Tool/MCP design pattern

MCP/tool reliability depends heavily on descriptions.

Good tool definitions should include:

- exact purpose,
- required/optional parameters,
- expected value formats,
- examples,
- constraints and side effects,
- when to prefer or avoid the tool,
- timeout/approval behavior.

Lazy-harness implication: framework tools and future MCP servers should optimize for agent legibility, not just human API cleanliness.

## Checkpoints and recovery

Useful patterns:

- commit after each successful task,
- use git tags or known-good markers,
- use worktrees for parallel/isolated tasks,
- consider shadow-git checkpoints for experimental agent edits,
- record progress and verification before compaction or session end.

Cline/Roo-style checkpoint restore is especially useful when agents explore alternate implementations or UI changes.

## Anti-patterns

- Adding agents because it looks sophisticated.
- Letting multiple agents edit the same files without ownership boundaries.
- Letting subagents dump raw grep/log output into the parent context.
- Relying on chat memory instead of repo records.
- Allowing agents to mark tasks complete without executable verification.
- Huge top-level instruction files that become encyclopedias instead of maps.
- Treating LLM critic output as stronger than deterministic test failure.
- Adopting external dependency/runtime without ADR.

## Candidate lazy-harness follow-ups

1. Define `notepad`/scratchpad storage convention for long plans.
2. Add a Planning/SDD record for subagent task prompt contract: required context, deliverable shape, evidence format.
3. Add a Swarm/Team usage policy: when to use single agent, subagent, swarm, or worktree parallel session.
4. Add completion gate criteria for multi-agent tasks: tests + record update + final coordinator synthesis.
5. Prototype critic/reviewer loop that uses deterministic checks first and LLM review second.
6. Define tool description quality checklist for lazy-harness MCP/tools.
7. Add trace/replay fields for subagent outputs, verification, and record mutations.

## Implementation map

- Status: `planned`
- Primary files:
  - `.lazy-harness/planning/practical-agent-harness-operating-patterns.md` — canonical reference for practical collaboration/subagent/swarm/record-use patterns.
  - `.lazy-harness/planning/external-agent-harness-reference.md` — broader landscape of external harnesses and frameworks.
  - `.lazy-harness/knowledge/upstream-references/oh-my-openagent-analysis.md` — existing extracted reference for role-based orchestration, notepad, hooks, and team mode.
  - `.lazy-harness/AGENTS.md` — current record-first lifecycle grammar.
  - `.lazy-harness/scripts/jcode-wiring.ts` — generated Jcode routing policy for practical subagent profiles.
- Key symbols:
  - `routingPolicy` (`.lazy-harness/scripts/jcode-wiring.ts`) — emits default subagent routing guidance for generated Jcode harness.
- Flow:
  1. External research identifies recurring practical harness patterns.
  2. This record maps them to lazy-harness lifecycle concepts.
  3. Future implementation should graduate specific patterns into ADR/SDD/TDD records before code changes.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` — validates JSONL/record invariants after additions.
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke` — smoke-validates framework health.
- Ownership boundaries:
  - Owner/upstream: Claude Code, CodeBolt, OpenHands, Cline/Roo, community harness references remain external sources.
  - This host may change: lazy-harness planning, specs, hooks, generated Jcode wiring after ADR/spec approval.
  - This host must not change without explicit confirmation: project/team canonical workflow policies for downstream hosts.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
  - Planning: `.lazy-harness/planning/external-agent-harness-reference.md`
  - Knowledge: `.lazy-harness/knowledge/upstream-references/oh-my-openagent-analysis.md`
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
- Machine index:
  - graph ids: `kg_practical_agent_harness_operating_patterns_doc`, `kg_practical_agent_harness_patterns_related_external_reference`, `kg_practical_agent_harness_patterns_omo_source`
  - generated index key: `pending until implementation-index generator exists`
