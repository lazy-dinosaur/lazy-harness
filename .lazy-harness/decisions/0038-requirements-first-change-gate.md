# ADR 0038 — Requirements-first Change Gate and Stale Approval Semantics

Status: accepted
Date: 2026-05-21

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Applies when:
  - user describes a problem or still-forming requirement, or adds a constraint/correction after a plan
  - before mutating code, records, config, schema, or git state
- Must:
  - separate requirement gathering, plan proposal, execution approval, and implementation stages
  - mutate only for the latest explicitly approved plan
  - on any new constraint after approval, stop, summarize revised requirements, and request fresh approval
- Must not:
  - treat confirmation phrases ("맞지?", "이해하지?", "그지?") as execution approval
- Record completion:
  - changes to the change-gate stages or stale-approval triggers update this ADR and `.lazy-harness/AGENTS.md`
- Related records:
  - `.lazy-harness/decisions/0019-ambiguous-detection-force-gate.md`
  - `.lazy-harness/decisions/0035-interview-queue-close-mandate.md`
  - `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md`

## Context

Lazy-harness already has option-gate discipline: when multiple choices exist, the agent must ask the user to choose and must not self-select.

However, a repeated failure mode remains:

1. The user describes a problem or partially formed requirement.
2. The agent jumps directly to a concrete modification plan.
3. The user adds another constraint or correction.
4. The agent treats the earlier plan or approval as still valid and continues.

This is not solved by option-gate alone. Option-gate protects choice selection, but it does not prove that the requirement itself is stable enough to plan or execute.

A recent example involved therapist/staff color assignment behavior. The user's actual requirement evolved through corrections:

- preserve an existing staff color across sheets,
- avoid duplicate colors for newly added staff,
- do not derive therapist colors from department colors,
- avoid visually similar colors when possible,
- do not implement until the user confirms the plan.

The important failure was not just a wrong color algorithm. The agent moved toward implementation before the requirement was fully collected.

## Decision

Introduce a Requirements-first change gate.

Before mutating code, records, config, schema, or git state, the agent must distinguish four stages:

1. Requirement gathering
   - Capture the user's problem, intent, constraints, exceptions, and success criteria.
   - Ask clarifying questions when requirements are still moving.
   - Do not finalize implementation details yet.
2. Plan proposal
   - Once requirements are stable enough, propose what files, records, contracts, or tests would change and why.
   - Include risks, alternatives, and validation plan when relevant.
3. Execution approval
   - Proceed only after the user explicitly approves the current plan.
   - Approval examples: "진행해", "수정해", "적용해", "A 로 해", "좋아 진행".
   - Confirmation phrases like "맞지?", "이해하지?", "그지?" are not execution approval.
4. Implementation
   - Run mutating tools only for the latest approved plan.
   - Do not use stale approvals.

## Stale approval rule

Any new constraint after approval reopens requirements unless the user explicitly says it does not affect the plan.

Stale triggers include:

- "아니"
- "잠깐"
- "그게 아니라"
- "수정하기 전에"
- new business rule
- new exception
- new priority
- new safety condition
- correction of the agent's interpretation

When approval is stale, the agent must stop implementation, summarize the revised requirements, update the plan, and request fresh execution approval.

## Relationship to option-gate

Option-gate answers:

> Which option should the agent choose?

Requirements-first gate answers:

> Is the requirement stable enough to propose or execute any option?

Therefore this gate runs before option-gate when the user's intent is still forming.

## Exceptions

- Read-only investigation is allowed before execution approval.
- Trivial mechanical edits may proceed when the user has already given a concrete, unambiguous edit request and no new constraints are being introduced.
- Emergency rollback or safety-preserving interruption may proceed if delay would cause harm, but the agent must explain afterward and record the reason.

## Subagent and swarm propagation

Coordinators must pass the latest requirement summary, approval status, and stale triggers to subagents.

If the user adds a new constraint while subagents are working, the coordinator must treat assigned implementation tasks as stale and stop, revise, or reassign them before continuing.

## Consequences

### Positive

- Prevents premature implementation.
- Keeps user corrections from being treated as minor comments.
- Separates requirement validation from execution approval.
- Makes "계획을 같이 세우고 내가 진행을 요구할 때 진행" a first-class harness rule.

### Negative

- Adds one more pause point.
- Can slow down trivial tasks if applied too broadly.
- Hook enforcement would be prone to false positives, so initial adoption should be documentation/ADR only.

## Implementation map

- `.lazy-harness/AGENTS.md`
  - Adds operational Requirements-first change gate under §2.3.
- `.lazy-harness/decisions/0038-requirements-first-change-gate.md`
  - Canonical decision and stale approval semantics.
- Future candidate:
  - A lifecycle helper may detect obvious violations only after dogfood examples accumulate.

## Cross-layer links

- Related: ADR 0019 option-gate discipline.
- Related: ADR 0035 interview queue close mandate.
- Related: ADR 0037 workflow compression, not safety reduction.

## Discovery capture

- DDD: none.
- SDD: agent workflow contract changes.
- BDD: user-agent collaboration flow changes.
- TDD: no immediate lifecycle helper test; future candidate after dogfood.
- ADR: this record.
- SSOT: no config/schema changes.
