# BDD — Agent-Owned Target Context Transition

Status: accepted
Layer: BDD
Date: 2026-08-26
Related ADR: `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md`
Related SDD: `.lazy-harness/spec/platform/project-operating-rulebook.md`
Related TDD: `.lazy-harness/tests/project-operating-rulebook.md`
Related Planning: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`

## Rule digest

- Status: active
- Layer: BDD
- Scope: framework-global
- Aliases:
  - agent-owned CLI fallback
  - target worktree transition
  - 직접 CLI 전환
  - 사용자에게 lazy-move 떠넘기지 않기
- Applies when:
  - the user has approved work in a concrete target worktree or project root
  - the preferred session-switch tool reports that direct switching is unavailable
  - the agent can launch a root-bound Pi/agent CLI in the approved target cwd
- Must:
  - launch the available target-root CLI itself before asking the user to type a transition command
  - keep the target CLI as the sole writer in that target worktree and require target-root grounding before mutation
  - report the launched session handle, preserve all existing dirty/untracked state, and supervise startup until the first target-root action is observed
  - treat a process-level `running` state as insufficient proof of implementation progress while trust, authentication, or startup errors may still block it
  - stop and surface the blocker only when no approved agent-owned CLI path is available or launch fails
- Must not:
  - offload a recoverable context transition to the user
  - claim that implementation is progressing solely because the CLI process is running
  - invent a target path, cross the current root directly, create a second writer, or treat CLI delegation as integration approval
- Record completion:
  - changes to the preferred/discouraged action contract update the typed policy, capability binding, ADR, SDD, and TDD together
- Related records:
  - `.lazy-harness/ssot/rule-sources.md`
  - `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md`
  - `.lazy-harness/spec/platform/project-operating-rulebook.md`
  - `.lazy-harness/tests/project-operating-rulebook.md`

## Correction capture

The user corrected an agent that stopped after `lazy_move_project` reported `ctx.switchSession` unavailable and told the user to run `/lazy-move` manually. The agent already had an approved target path and an available `interactive_shell` Pi CLI, so the remaining transition was agent-owned work.

Confirmed correction:

- `lazy_move_project` remains the preferred direct switch attempt when it can switch the current session.
- If it cannot switch, the agent launches Pi/another approved coding CLI itself in the already approved target cwd.
- A manual user command is a last fallback, not the default handoff.
- This correction changes orchestration behavior only; it does not claim a defect in the switch tool, authorize cross-root reads by the current Parent, or relax single-writer/root-bound rules.
- Runtime evidence on 2026-08-26: the first dispatch remained at the project-trust prompt for 19 minutes; after the approved target was trusted, duplicate project/global `lazy_move_project` tools caused exit 1. The Parent then relaunched with the CLI-recommended `pi -ne` boundary and verified `git status` plus `.lazy-harness/AGENTS.md` activity before reporting progress.

## Scenario: direct switch unavailable, CLI available

**Given** the user approved a concrete target worktree and implementation scope,  
**and** the direct switch tool reports that its runtime cannot switch sessions,  
**and** an agent-owned interactive/dispatch CLI can run with that target as `cwd`,  
**when** the Parent continues the work,  
**then** it launches the target-root CLI itself,  
**and** the Parent supervises trust/authentication/startup prompts for the already approved target,  
**and** the target CLI first performs its own map/read grounding,  
**and** the Parent verifies an actual target-root action before reporting implementation progress or the session handle instead of requiring the user to type `/lazy-move`.

## Scenario: no safe CLI fallback

**Given** the target is not user-approved or cannot be verified,  
**or** the CLI facility is unavailable or launch fails,  
**when** the Parent cannot create a safe root-bound worker,  
**then** it stops, records the blocker, and asks for the minimum required user action without inventing a path or bypass.

## Typed operating guidance

- Policy: `agent-owned-target-context-transition`
- Capability: `agent-owned-target-context-transition`
- Level: `default` (advisory resolver; no blocking lifecycle hook)
- Preferred action: launch `interactive_shell`/approved coding CLI in the approved target cwd.
- Discouraged action: ask the user to run `/lazy-move` while an agent-owned target CLI is available.
- Fallback: report a concrete launch/approval blocker; never cross the current root directly.

Mechanical policy resolution guides action selection. It does not prove the target CLI grounded correctly, preserve semantic quality, clear Parent read debt, or authorize mutation beyond the approved scope.

## Rule placement

- Rule: after direct session switching fails, an available agent-owned target-root CLI is the default fallback before manual user handoff.
- Scope: framework-global.
- Primary record: `.lazy-harness/behavior/agent-owned-target-context-transition.md`.
- Why not AGENTS.md: the machine-action preference belongs in typed policy/capability storage and this BDD; the shared grammar already routes operating rules there.
- Why not local notes: this is reusable project/framework behavior, not a private Pi shortcut.
- Confirmation: user-confirmed on 2026-08-26.

## Discovery capture

- DDD: none — no domain entity, term, or business invariant changes.
- SDD: updated — the operating-rule resolver exposes the preferred/discouraged target-transition actions.
- BDD: updated — this record owns the corrected user-facing transition flow.
- TDD: updated — policy/capability resolution and fallback boundaries are protected in the rulebook regression record.
- ADR: updated — ADR 0055 records the Parent orchestration responsibility and rejected user-offload path.
- SSOT: updated — canonical semantics and action binding live in `policies.json` and `capabilities.json`.
- Planning: updated — the Reader experiment plan records the correction and direct CLI launch.

## Implementation map

- Status: `configured-guidance`
- Primary files:
  - `.lazy-harness/behavior/agent-owned-target-context-transition.md` — canonical corrected behavior and scenarios.
  - `.lazy-harness/ssot/policies.json#agent-owned-target-context-transition` — typed default behavior semantics.
  - `.lazy-harness/ssot/capabilities.json#agent-owned-target-context-transition` — preferred/discouraged action binding.
  - `.lazy-harness/spec/platform/project-operating-rulebook.md` — resolver contract.
  - `.lazy-harness/tests/project-operating-rulebook.md` — regression expectations.
  - `.lazy-harness/scripts/self-test.py#check_project_operating_rulebook_cli/check_policy_machinery_v2` — source policy/capability linkage, resolver, generated view, fixture portability, and sync protection.
  - `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md` — Parent responsibility decision.
- Key identifiers:
  - policy `agent-owned-target-context-transition`
  - capability `agent-owned-target-context-transition`
  - preferred action `interactive_shell spawn Pi in approved target cwd`
- Flow:
  1. Resolve/attempt the approved direct project/session transition.
  2. If switching is unavailable, resolve the target-transition operating capability.
  3. Launch one target-root CLI writer and require target-root grounding.
  4. Report the handle and continue supervision; use manual handoff only after a concrete fallback failure.
- Tests / protection:
  - `.lazy-harness/bin/lazy policy audit --format=json`
  - `.lazy-harness/bin/lazy capability audit --format=json`
  - `.lazy-harness/bin/lazy capability resolve --intent handling_unavailable_session_switch --action 'ask user to run /lazy-move when interactive CLI is available' --format=json`
  - `.lazy-harness/bin/lazy test`
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md`
  - SDD: `.lazy-harness/spec/platform/project-operating-rulebook.md`
  - TDD: `.lazy-harness/tests/project-operating-rulebook.md`
  - Planning: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`
- Machine index:
  - graph id: `kg_agent_owned_target_context_transition_20260826`
