# Project-specific Rule Discovery Router Backlog

Status: proposed
Date: 2026-05-15
Related SSOT: `.lazy-harness/ssot/project-identity.md`
Related ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
Related ADR: `.lazy-harness/decisions/0031-root-bound-record-convergence.md`

## Problem

Different projects have different rules. The current model says:

- `AGENTS.md` is shared grammar.
- `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/` stores host vocabulary and source-of-truth facts.
- `.jcode/harness/20-project-rules.md` stores Jcode-local workflow notes.

However, agents can still misclassify where a new project-specific rule belongs. Example from user feedback: a PR/worktree tracker rule was treated as a local `.jcode/harness/20-project-rules.md` pointer, but the rule may be a broader project rule that should be discoverable from `.lazy-harness` records across sessions and hosts.

## Goal

Add a framework-level rule router so agents do not decide rule placement ad hoc.

The router should answer:

1. Is this rule framework-global grammar?
2. Is this host project identity/ownership/source-of-truth?
3. Is this team/project operating policy that should live in `.lazy-harness` records?
4. Is this Jcode-local private workflow that belongs in `.jcode/harness/20-project-rules.md`?
5. Is this transient plan/backlog that belongs in `.lazy-harness/planning/`?

## Proposed design

### 1. Rule source registry

Create a host-local SSOT record, for example:

- `.lazy-harness/ssot/rule-sources.md`

It should define canonical locations and priority:

1. Current explicit user request
2. Nested/private `.jcode` instructions for local Jcode workflow
3. `.lazy-harness/ssot/project-identity.md`
4. `.lazy-harness/ssot/rule-sources.md`
5. Layer records: DDD/SDD/BDD/TDD/ADR/SSOT
6. Shared `.lazy-harness/AGENTS.md` grammar

### 2. Rule placement matrix

Add an SDD/platform standard such as:

- `.lazy-harness/spec/platform/project-rule-router.md`

Suggested mapping:

| Rule type | Primary location |
|---|---|
| Framework-common agent behavior | `.lazy-harness/AGENTS.md` |
| Host identity, source-of-truth, ownership, forbidden mutation | `.lazy-harness/ssot/project-identity.md` or dedicated SSOT |
| Team/project operating policy shared by all agents | `.lazy-harness/ssot/rule-sources.md` or relevant ADR/SSOT |
| Domain/business language | `.lazy-harness/domain/**` |
| API/component/data contract | `.lazy-harness/spec/**` |
| User-visible workflow | `.lazy-harness/behavior/**` |
| Regression/protection expectation | `.lazy-harness/tests/**` |
| Trade-off/why decision | `.lazy-harness/decisions/**` |
| Local Jcode-only preference/workflow | `.jcode/harness/20-project-rules.md` |
| Multi-step work plan/backlog | `.lazy-harness/planning/**` |

### 3. Option gate for ambiguous placement

If a rule could belong to both `.lazy-harness` and `.jcode`, stop with options:

A. `.lazy-harness/ssot/...` shared project rule (Recommended for team/project policy)
B. `.lazy-harness/decisions/...` trade-off/why decision
C. `.lazy-harness/planning/...` transient backlog/plan
D. `.jcode/harness/20-project-rules.md` local private Jcode workflow
E. 직접 입력

### 4. Lifecycle/helper support

Add or extend a helper to detect phrases like:

- “rules differ by project”
- “AGENTS.md 수정해야?”
- “프로젝트 규칙”
- “이건 어디에 기록?”
- “.jcode에 넣을까 .lazy-harness에 넣을까”

If the response chooses `.jcode` without a rule-source judgement, warn/stop and ask for placement confirmation.

## Acceptance criteria

- New project-specific rule discussions result in a durable `.lazy-harness` record or an explicit `.jcode` local-only judgement.
- Agents no longer default to `.jcode/harness/20-project-rules.md` for project policies that should be shared.
- Self-test covers at least:
  - project rule + no placement judgement -> gate fires,
  - rule-source judgement with `.lazy-harness/ssot` -> pass,
  - local Jcode-only judgement -> pass.

## Discovery capture

- DDD: none, this is not a domain/business term issue.
- SDD: candidate `.lazy-harness/spec/platform/project-rule-router.md`.
- BDD: none unless exposed as a user-facing flow later.
- TDD: candidate self-test for rule placement gate.
- ADR: candidate decision if implementation proceeds.
- SSOT: candidate `.lazy-harness/ssot/rule-sources.md`.
- Planning: this backlog created.

## Implementation map

- Status: `planned`
- Primary files:
  - `.lazy-harness/planning/project-rule-discovery-router-backlog.md` — this backlog.
  - `.lazy-harness/ssot/project-identity.md` — current split between AGENTS, records, and `.jcode`.
  - `.lazy-harness/decisions/0024-ai-first-framework-redesign.md` — `AGENTS.md = grammar, record = vocabulary`.
  - `.lazy-harness/decisions/0031-root-bound-record-convergence.md` — Jcode-local workflow notes only in `.jcode/harness/20-project-rules.md`.
- Key symbols:
  - `projectRules` (`.lazy-harness/scripts/jcode-wiring.ts`) — generates generic `.jcode/harness/20-project-rules.md` template.
- Flow:
  1. User raises or corrects a project-specific rule.
  2. Agent consults rule source registry and placement matrix.
  3. Agent writes the correct `.lazy-harness` record or records local-only `.jcode` judgement.
  4. Ambiguous placement triggers option gate.
- Tests / protection:
  - planned self-test fixture for project rule placement.
- Cross-layer links:
  - SSOT: `.lazy-harness/ssot/project-identity.md`
  - ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
  - ADR: `.lazy-harness/decisions/0031-root-bound-record-convergence.md`
- Machine index:
  - graph ids: `pending`
  - generated index key: `pending until implementation-index generator exists`
