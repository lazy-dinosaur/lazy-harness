# Organic Hybrid Rule Guidance Plan

Status: approved-for-planning
Date: 2026-06-01
Layer: Planning
Related SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`

## User-confirmed direction

The user chose to back out the recent hard-gate implementation because it made the workflow feel too slow and too tool-attached.

Direction:

- Do not keep growing one-off enforcement attached directly to concrete tool surfaces like `bash`, `gh`, `dev-cli`, or GitHub MCP.
- Do not restore the 2026-05-19-era edit/write/multiedit blocking behavior as the primary solution if it makes iteration slow.
- Keep the goal of rule reliability, but pursue a more organic/free hybrid model.
- Treat the recent hard-gate implementation as a reverted experiment, not the target architecture.

## Working name

C+ v2 organic hybrid.

## Difference from C+ v1

C+ v1, reverted:

```text
blocking edit/write/multiedit hook restoration
+ runtime/dev-cli command guard
+ PR/runtime checks attached to tool surfaces
```

Why it was reverted:

- It restored force, but felt slower.
- It pushed the framework toward tool-specific patches.
- It did not match the desired organic/free agent experience.

C+ v2, target for design:

```text
ambient relevant rule context
+ graduated guidance ladder
+ lightweight action/journal continuity
+ very narrow hard stops only for irreversible or repeatedly failed boundaries
```

## Refined first-pass scope

User clarification on 2026-06-01:

- Ignore subagent/swarm handoff for the first pass.
- Focus on the core harness loop:
  1. lazy-harness-authored documents must be complete and placed in the right layer.
  2. relevant rules must be recognized before the response or plan.
  3. the agent should receive compact rule information rather than tool-specific instructions.
  4. response completion should audit whether important rules were ignored or records were not written.
  5. confirmed facts/rules/decisions should be recorded back into DDD/SDD/BDD/TDD/ADR/SSOT/planning as appropriate.

Core distinction:

- Mandatory record completion can remain strong/forced because it protects `.lazy-harness` memory itself.
- Non-record action guidance should be handled by pre-response relevant record query and response-completed audit, not by tool-specific rules.


This is the first implementation shape to design. Subagent handoff can reuse the same digest/journal later, but it is not part of the first pass.

## Hook strategy for first pass

Hooks are still central, but the policy surface should be response lifecycle, not tool-specific enforcement.

First-pass target:

1. pre-response relevant-record query or closest available message/prompt lifecycle equivalent,
2. compact digest injection before the answer/plan,
3. response.completed audit/backstop after the answer,
4. record completion feedback when confirmed information was not written,
5. inventory and migration plan for existing tool-attached project-policy checks.

Tool hooks should remain only for minimal safety/logging/transport while policy moves into the record query + response audit loop.

Comprehensive transition plan: `.lazy-harness/planning/record-query-context-loop-transition-plan.md`.

## Candidate structure

### 1. Ambient rule context

Before hard blocking, lazy-harness should help the agent naturally remember relevant records.

Possible mechanism:

- derive topic/action hints from user message and recent tool calls,
- resolve matching DDD/SDD/BDD/TDD/ADR/SSOT records,
- inject a small, ranked rule context into the next agent turn or side-channel,
- do this without forcing a specific tool adapter.

### 2. Graduated guidance ladder

Rules should have behavior levels:

```text
ambient → nudge → warn → ask → hard stop
```

Most rules should start as ambient/nudge/warn. They promote only when:

- user explicitly marks them mandatory,
- miss cost is high,
- repeated dogfood failure occurs,
- operation is irreversible or external mutation.

### 3. Soft action journal

Instead of a rigid ticket gate, maintain lightweight continuity:

```text
current intent
relevant records surfaced/read
required artifact expectations
validation evidence
stale approval markers
```

This journal can guide agents organically and support later enforcement if needed.

### 4. Narrow hard stops

Hard stops remain possible, but should be narrow and framework-level:

- destructive / irreversible operations,
- stale requirements approval,
- explicit user correction being ignored,
- repeated failure class that has been promoted after dogfood evidence.

Hard stops should not be implemented as one-off logic for every tool.

## Required next design work

Create an ADR/design comparison before implementation. It should compare:

1. tool-specific guard sprawl,
2. 2026-05-19-style broad blocking,
3. rigid Action Gate / ticket model,
4. ambient rule context,
5. graduated guidance ladder,
6. soft action journal,
7. C+ v2 organic hybrid.

## Validation requirements for future implementation

- Measure latency before/after.
- Verify source `self-test.py` and `doctor.py --profile smoke`.
- Dogfood sync/test on Medivance and Medivance PWA.
- Add fixtures proving rules surface before action without heavy per-tool blocking.
- Add fixtures proving high-risk promoted cases still hard-stop.

## Rule placement

- Rule: Replace the reverted tool-attached hard-gate experiment with a C+ v2 organic hybrid design exploration: ambient rule context, graduated guidance, soft journal continuity, and narrow hard stops.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/organic-hybrid-rule-guidance-plan.md`
- Why not AGENTS.md: this is a design/implementation plan, not final operational grammar.
- Why not `.jcode`: this is shared lazy-harness framework design, not local/private Jcode-only workflow.
- Confirmation: user-confirmed

## Discovery capture

- DDD: none.
- SDD: future spec likely for rule context resolver, guidance levels, and soft action journal.
- BDD: agent workflow should feel organic/free and not be slowed by broad blocking hooks.
- TDD: future tests needed for rule surfacing and narrow hard-stop promotion.
- ADR: required before implementation.
- SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md` remains the policy anchor.
- Planning: this document is the current plan.
