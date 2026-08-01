# ADR 0050 - Pi/OMP-Only Runtime: Decommission Jcode Wiring

Status: superseded
Date: 2026-06-24
Superseded by: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
Layer: ADR
Supersedes: `.lazy-harness/decisions/0006-directory-bridge-architecture.md`, `.lazy-harness/decisions/0007-agents-md-injection.md`, `.lazy-harness/decisions/0029-generated-project-local-jcode-wiring.md`
Related SDD: `.lazy-harness/spec/platform/pi-agent-package.md`, `.lazy-harness/spec/platform/host-root-resolution.md`
Related SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`, `.lazy-harness/ssot/runtime-and-shared-state.md`, `.lazy-harness/ssot/cli-tool-boundary.md`
Related TDD: `.lazy-harness/tests/pi-agent-package.md`
Related planning: `.lazy-harness/planning/discovery-vs-loading-followups-20260624.md`

## Rule digest

- Status: deprecated
- Layer: ADR
- Scope: framework-global
- Aliases:
  - jcode 폐선
  - jcode decommission
  - Pi OMP 전용
  - 런타임 정리
- Applies when:
  - wiring, removing, or auditing agent-runtime lifecycle integration
  - deciding which runtime delivers lazy-harness hooks, skills, commands, or grammar
  - bootstrapping a host (`lazy init`) or generating runtime wiring
- Must:
  - deliver lazy-harness lifecycle hooks through the Pi/OMP extension (`before_agent_start`, `tool_call`, `tool_result`, `agent_end`) — the single supported runtime surface
  - keep destructive-command blocking in the shared guard (`on-tool-execute-before.sh`) so Pi and OMP both deny `rm -rf /`, `dd of=/dev/*`, `mkfs /dev/*`
  - preserve historical jcode ADRs/planning as decision history; supersede, do not delete, ADR 0006/0007/0029
- Must not:
  - generate `.jcode/` wiring, regenerate jcode skill wrappers, or reintroduce a directory-bridge runtime
  - assume a jcode runtime exists in any active contract, self-test, or skill
- Record completion:
  - changes to runtime wiring, lifecycle bridges, or removal of jcode surfaces update this ADR plus the related SDD/SSOT/TDD
- Related records:
  - `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`
  - `.lazy-harness/decisions/0043-pi-native-package-in-source-repo.md`
  - `.lazy-harness/decisions/0047-pi-omp-shared-package-separate-install-ux.md`
  - `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
## Context

ADR 0006 (directory-bridge `.jcode/` ↔ `.lazy-harness/`), ADR 0007 (AGENTS.md injection via generated jcode files), and ADR 0029 (generated project-local jcode wiring) established Jcode as a first-class runtime that received lazy-harness hooks, skills, and grammar through a generated `.jcode/` directory.

The framework has since shipped a Pi/OMP agent package (`packages/lazy-harness-pi`, ADR 0043/0047) that delivers the same behavior through the official extension surface. A 2026-06-24 cross-runtime audit confirmed full parity:

- Lifecycle hooks: `message.received` → `before_agent_start`, `tool.execute.before` → `tool_call`, `response.completed` → `agent_end` (verified against `@earendil-works/pi-coding-agent` v0.80.2 and `@oh-my-pi/pi-coding-agent` v16.1.12; both emit `agent_end` once per prompt and expose `on`/`sendMessage`/`ctx.cwd`).
- Skills: the Pi/OMP package `skills/` set is a superset of `.jcode/skills/`.
- Commands and grammar: `/lazy-*` commands plus the `prompts/lazy-harness.md` reminder point at the canonical `.lazy-harness/AGENTS.md`.

The only jcode-side behavior without a Pi/OMP equivalent was the `jcode init` private safety hook `check-bash.sh` (destructive-command block) and `log-tool.sh` (tool logging). The destructive block is ported into the shared guard (so Pi/OMP gain it); tool logging is dropped because Pi/OMP keep their own session logs.

With parity complete, maintaining the `.jcode/` directory-bridge is duplicate runtime surface.

## Decision

Make Pi/OMP the only supported lazy-harness runtime and decommission jcode wiring. Executed in phases.

Phase 1 (done):

- `.jcode/` generation removed from `lazy-init` and `lazy-sync`, and the local `.jcode/` directory deleted (git-excluded, was regeneratable),
- `jcode-skill-install` post-init action and `--skip-jcode` flag removed,
- destructive-command blocking ported to `.lazy-harness/hooks/lifecycle/helpers/check-destructive-command.py`, chained first in `on-tool-execute-before.sh` so Pi/OMP `tool_call` denies destructive shell commands (replaces jcode-private `check-bash.sh`); `log-tool.sh` tool logging dropped (Pi/OMP keep their own session logs),
- 10 `check_jcode_*` framework self-tests removed; `check_destructive_command_block` added,
- ADR 0006/0007/0029 superseded (meta `superseded`, digest status `deprecated`) with a pointer here.

Phase 2 (executed 2026-06-25 — user-confirmed clean cutover):

- `.lazy-harness/scripts/jcode-wiring.ts` deleted (orphaned generator, no longer imported),
- the `jcode-local` Scope enum is renamed `local-only` in `record-index.ts`; project-rule-placement routing no longer uses `.jcode-local`,
- `pi compatibility: jcode` resolved by superseding `.lazy-harness/ssot/pi-mcp-parity.md` (the `~/.jcode/mcp.json` parity source no longer exists),
- `lazy-skill-create` retired: `.lazy-harness/scripts/skill-create.ts` deleted, the broken `lazy skill create` dispatcher removed from `.lazy-harness/bin/lazy`, `skills.xml` marks the skill retired,
- **Pi/OMP skill-authoring decision (no generator CLI)**: framework skills are hand-authored in the source package `packages/lazy-harness-pi/skills/<name>/SKILL.md` (framework-owned, ADR 0027 — source repo only). Host-local custom skills use Pi/OMP package loading: a host creates its own package `skills/` dir and attaches it via `.pi/settings.json` `packages: [...]` (Pi) or `omp plugin install <path>` (OMP). There is intentionally no host-side `lazy skill create` scaffolder; durable team/project policy stays in `.lazy-harness` records (AGENTS §2.4),
- `.lazy-harness/AGENTS.md` carries no `.jcode` local-notes guidance; `skills.xml` `.jcode/skills` strings remain only on retired-skill descriptions,
- stale `knowledge/graph.jsonl` edges to the deleted `jcode-wiring.ts` / `skill-create.ts` are superseded (`status: superseded`, pointer here); `generated/implementation-index.json` is a derived cache that rebuilds from the canonical graph.

Preserved as history (deprecate, do not delete):

- ADR 0006/0007/0029 (superseded); `.lazy-harness/spec/platform/jcode-skill-creation.md` (deprecated), `.lazy-harness/JCODE-INTEGRATION.md`, and historical jcode mentions in planning/retrospective records describe the former jcode wiring and are left intact as decision history.

## Consequences

- New hosts install only the Pi/OMP package; there is no `.jcode/` to generate.
- Destructive-command safety is now runtime-agnostic (shared guard), not jcode-private.
- Records and self-tests no longer assume a jcode runtime; doctor/record-lint/graph-hygiene must stay green after removal.
- Downstream hosts that still run Jcode keep using their own `.jcode/` (host-owned, regeneratable from history); the framework no longer ships or tests that path.

## Implementation map

- Status: phase-2-implemented (clean cutover 2026-06-25)
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-destructive-command.py` - destructive-command block (Pi/OMP via shared guard)
  - `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` - chains the destructive check first
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` - the single runtime surface
  - `.lazy-harness/scripts/lazy-init.ts`, `.lazy-harness/scripts/lazy-sync.ts` - jcode wiring step removed
- Removed:
  - `.jcode/**` (deleted); `jcode-skill-install` post-init action; `--skip-jcode` flag; 10 `check_jcode_*` self-tests
  - Phase 2 (2026-06-25): `.lazy-harness/scripts/jcode-wiring.ts` and `.lazy-harness/scripts/skill-create.ts` deleted; `lazy skill create` dispatcher removed from `.lazy-harness/bin/lazy`; `jcode-local` Scope enum renamed `local-only`
- Retained as deprecated history:
  - `.lazy-harness/spec/platform/jcode-skill-creation.md` (deprecated), `.lazy-harness/JCODE-INTEGRATION.md`, ADR 0006/0007/0029, and historical planning jcode mentions
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py` - `check_destructive_command_block` plus Pi package contract; jcode checks removed
- Cross-layer links:
  - SSOT `harness-enforcement-policy.md` updated to Pi/OMP-only

## Rule placement

- Rule: lazy-harness ships a single Pi/OMP runtime surface; jcode wiring is decommissioned and destructive-command blocking is runtime-agnostic.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`
- Why not AGENTS.md: this is a runtime architecture decision with source/tests and an implementation map; AGENTS.md carries only a compact pointer.
- Why not `.jcode`: the decision removes `.jcode` wiring entirely.
- Confirmation: user-confirmed

## Discovery capture

- DDD: none.
- SDD: `pi-agent-package.md` remains the runtime contract; `jcode-skill-creation.md` removed.
- BDD: none (no visible-flow change; agents already run under Pi/OMP).
- TDD: jcode self-tests removed; destructive-command block added.
- SSOT: `harness-enforcement-policy.md`, `runtime-and-shared-state.md`, `cli-tool-boundary.md` updated to Pi/OMP-only.
- Planning: `discovery-vs-loading-followups-20260624.md` records the removal follow-up.
