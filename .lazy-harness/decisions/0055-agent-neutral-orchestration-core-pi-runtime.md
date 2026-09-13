# ADR 0055 — Agent-Neutral Orchestration Core with Pi Subagents Runtime

Status: accepted architecture direction; live R2 delivery/join safety passed but functional canary incomplete; user-selected per-read-cap/source-guard correction focused-green; full revalidation and main integration pending
Date: 2026-07-24
Layer: ADR

## Rule digest

- Status: advisory
- Layer: ADR
- Scope: framework-global
- Aliases:
  - agent-neutral orchestration
  - Lazy core + Pi runtime
  - top-level orchestrator debt
  - scoped retrieval child
  - delegated evidence packet
  - Harness Reader
  - Reader join barrier
  - Parent code lane
- Applies when:
  - delegating project retrieval, context sharding, or evidence extraction to subagents
  - deciding whether the dedicated Reader or Parent owns harness-record retrieval
  - designing the parallel Reader-record lane, Parent-code lane, and their join boundary
  - choosing how to continue approved target-root work when direct session switching is unavailable
- Must:
  - keep orchestration semantics in the Lazy-Harness core and Pi Subagents as a thin execution runtime
  - make one dedicated Reader own complete `.lazy-harness` retrieval across DDD/SDD/BDD/TDD/ADR/SSOT/Planning for the current task
  - let the Parent concurrently inspect source/tests or immediately needed behavior while the Reader searches and reads canonical records
  - require the Parent to await and consume the Reader response before planning, mutation, or host-specific completion claims
  - make the Parent launch an available target-root CLI itself before asking the user to perform a recoverable context transition
- Must not:
  - require the Parent to repeat Reader-covered record reads merely to satisfy search/read debt
  - make the Parent preselect concrete record nodes for the Reader or turn ordinary Reader completion into admission/provenance/audit proof machinery
  - use the Reader as the source-code investigator, semantic decision maker, writer, or validator
  - offload an approved target-worktree transition to the user when an agent-owned root-bound CLI is available
- Record completion:
  - approved runtime changes update the relevant SDD/TDD records; pilot results update the linked Planning record
- Related records:
  - `.lazy-harness/decisions/0049-discovery-vs-loading-complete-lean-discovery.md`
  - `.lazy-harness/decisions/0051-jcode-parity-grammar-regrounding.md`
  - `.lazy-harness/decisions/0052-external-context-extension-non-adoption.md`
  - `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - `.lazy-harness/spec/platform/pi-agent-package.md`
  - `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`

## Context

### Quality-preservation clarification — 2026-08-25

The user clarified that the optimization target is **not higher accuracy than the direct Parent baseline**. The target is to preserve the same semantic quality, correctness, and trust level while improving request-to-validation wall-clock, Parent-context pressure, token use, or cost through bounded orchestration.

Quality is therefore a non-regression gate: a delegated treatment qualifies for performance comparison only after it matches the same baseline/oracle/fidelity bar. Failure to prove equivalence blocks that candidate's promotion, but does not imply that the existing map-first retrieval baseline needs higher accuracy or a replacement evidence architecture.

Current contracts establish two important baselines:

1. ADR 0049 requires complete lean discovery and targeted loading.
2. The Search/Read Debt SDD binds evidence to a root-scoped epoch and does not accept map cues as concrete required-read evidence.

Current Pi/OMP behavior also force-loads the full `.lazy-harness/AGENTS.md` grammar once per session. There is no verified delegated-evidence bridge that can transfer a child's successful reads into the parent guard. Therefore the target architecture and the currently deployed behavior must remain explicit and separate.

### Correction capture — Reader owns harness retrieval

On 2026-08-26 the user corrected the orchestration model: the dedicated Reader searches the full stored harness memory, selects and reads the relevant canonical DDD/SDD/BDD/TDD/ADR/SSOT/Planning records, and returns the applicable policies, facts, conflicts, and missing information. The Parent does not first choose record nodes for the Reader and does not reread those same records to clear a debt journal.

The Parent uses that time for a parallel lane: inspect source/tests, or directly inspect an immediately needed behavior record. Before planning, mutation, or a host-specific completion claim, it joins the completed Reader response. Reader failure, ambiguity, or incomplete coverage triggers Parent follow-up or an option gate; ordinary successful completion does not trigger duplicate proof or rereads.

This correction supersedes the earlier parent-global/child-scoped read-debt design and the v1–v3 proof-remediation direction. Runtime implementation remains separately approval-gated; current debt hooks are transitional deployed behavior, not the accepted target architecture.

## Correction capture — agent-owned target transition

On 2026-08-26 the user corrected the Parent for stopping after `lazy_move_project` reported that `ctx.switchSession` was unavailable and asking the user to run `/lazy-move`. The approved target path and `interactive_shell` Pi CLI were already available, so this was an orchestration error, not a missing user prerequisite.

Decision refinement: attempt the direct switch first; when that runtime cannot switch, launch one agent-owned coding CLI in the approved target cwd and require target-root grounding. Ask for manual user transition only when the target is unapproved/unverified, the CLI facility is unavailable or fails, or another writer makes launch unsafe. This does not authorize cross-root reads by the current Parent or relax single-writer, approval, validation, or integration boundaries.

The typed policy/capability ids are `agent-owned-target-context-transition`; the user-visible scenarios live in `.lazy-harness/behavior/agent-owned-target-context-transition.md`.

## Decision

### 1. Responsibility boundary

Lazy-Harness owns the agent-neutral orchestration meaning:

- dependency DAG and work decomposition,
- `WorkPacket` and `EvidencePacket` semantics,
- root/HEAD/evidence-epoch freshness,
- read/write scope and artifact ownership,
- one integrator, one canonical writer per target, and one final validation owner,
- overflow states, quality gates, and measurement,
- canonicalization policy and record continuity.

Pi Subagents is the first execution adapter. It owns:

- fresh child sessions,
- model selection,
- parallel/chain scheduling,
- worktree and artifact mechanics,
- supervision, interruption, and result delivery.

The Lazy-Harness core must not depend directly on Pi APIs. A thin adapter may translate a Lazy work packet into Pi `subagent({ tasks | chain, ... })` calls and translate the result back into an evidence packet.

### 2. Harness-record retrieval ownership and join

Use **Reader-owned harness retrieval + Parent-owned parallel code investigation + one join barrier**.

The dedicated Reader owns, per work unit:

1. one complete `lazy map --overview` inventory of stored harness memory,
2. task-relevant drill-down and semantic selection across DDD/SDD/BDD/TDD/ADR/SSOT/Planning,
3. real canonical record-body reads, including cross-layer links needed to avoid policy/fact omissions,
4. a bounded response containing applicable policies, facts, conflicts, missing information, and cited record paths,
5. explicit `complete`, `incomplete`, or `conflict` status.

The Parent concurrently owns:

1. source/test investigation and implementation reality,
2. an optional direct read of immediately needed behavior guidance,
3. waiting for and consuming the Reader response before plan/mutation/completion,
4. semantic decisions, option gates, mutation, integration, and validation.

A successful Reader response is the synchronization event for harness-record retrieval. The Parent does not repeat Reader-covered record reads merely to satisfy a search/read-debt journal. It directly reads a record only when the Reader reports conflict/incompleteness, when the exact record itself will be edited, or when a newly discovered contradiction requires resolution.

### 3. Reader context and prompt

The Reader receives the root, current revision identity, and the current task—not Parent-selected record nodes. It performs harness-wide map-first discovery and relevant canonical loading itself. Its allowed knowledge lane is the stored harness memory and its cross-layer links; source-code investigation remains the Parent's parallel lane.

Use a thin derived Harness Reader prompt, not a second policy engine. It requires:

- root-bound read-only operation,
- complete harness inventory followed by task-relevant canonical record reads,
- DDD/SDD/BDD/TDD/ADR/SSOT/Planning coverage consideration,
- no silent inference, mutation, user decision, source-code implementation review, or subagent fan-out,
- concise policy/fact/conflict/missing output with record-path citations.

### 4. Parent join after delegation

The Parent launches the Reader at the beginning of the work unit and continues useful code/test or immediate-behavior investigation while it runs. Before any plan, mutation, or host-specific completion claim, the Parent waits for the Reader result and incorporates it into the same work-unit context.

Ordinary successful Reader completion requires no candidate-output admission, exact tool-sequence proof, independent semantic audit, agreement receipt, or duplicate Parent record reads. If the Reader returns `incomplete`/`conflict`, fails, or omits an obviously relevant layer, the Parent performs the bounded follow-up read or option gate before action.
### 5. Phase boundary

The current deployed Pi/OMP hooks still implement direct Parent search/read-debt guarding. They remain transitional until a separately approved implementation replaces that flow with Reader launch/join semantics and a simple failure fallback.

A future implementation slice may add the Reader role plus orchestration join, retire the default debt journal/duplicate-read requirement for Reader-managed work units, and add focused regressions. It must not revive the v1–v3 proof/admission/audit apparatus.

## Rejected alternatives

- **Every child performs full independent discovery.** Safe but duplicates map, prompt, and record-loading cost and weakens context sharding.
- **Give every child the full project context.** Recreates a large main context in each worker and increases context rot.
- **Full `AGENTS.md` plus a permanent scout overlay as the target.** Preserves current safety but leaves avoidable prompt duplication; retained only as the current runtime baseline.
- **Require Parent rereads after a successful Reader response.** Duplicates the harness-record lane and defeats the purpose of concurrent retrieval; retained only as a failure/conflict fallback.
- **Build a new queue/daemon/agent engine first.** Adds control-plane complexity before the orchestration hypothesis is measured.

## Consequences

### Positive

- Global discovery and semantic authority stay with one accountable orchestrator.
- Child context is proportional to its evidence claim rather than project size.
- Pi remains replaceable as a runtime adapter.
- Parent rereads become risk- and decision-focused instead of duplicating all scout work.

### Negative / risks

- Reader latency becomes a join dependency before planning or mutation.
- Reader omissions must be visible through `incomplete`/`conflict` rather than hidden behind proof machinery.
- The current direct Parent debt hooks conflict with the accepted target until an approved implementation retires or narrows them.

## 2026-09-04 correction — topology failure does not reverse Reader ownership

The user reaffirmed that subagent-based harness reading is the selected architecture. The completed broad-audit topology run used a manually prompted builtin `delegate` while the current main package had no `agents/` resource and no Reader registration in `packages/lazy-harness-pi/package.json`. It therefore exposed missing Reader integration, result/output contracts, and budget handling; it did not authorize a return to Parent-owned record retrieval.

The target remains: one dedicated Reader searches and reads canonical harness memory, the Sol Medium Parent works the source/test lane, content-bearing Reader delivery closes the join, and the Parent owns the complete final answer. Direct Parent record retrieval is only the transitional failure fallback until that separately approved runtime slice exists.

A child process `complete` acknowledgement alone is not the Reader join. The Reader packet itself must reach the Parent with `complete|incomplete|conflict`; after Parent synthesis, a post-response advisory must not replace the caller-visible primary answer with an advisory-only message.

## Implementation map

- Status: `reader-runtime-static-slice-reviewed-ok-and-standard-green-in-isolated-worktree; new-live-smoke-and-main-integration-pending` — Reader-owned retrieval, Parent lane, explicit content join, debt fallback, and print-output preservation are implemented on `work/reader-runtime-v1`; main remains unchanged.
- Current implementation and contract evidence:
  - `.lazy-harness/spec/platform/search-read-debt-contract.md` — root-scoped evidence epoch and direct map/read debt semantics.
  - `.lazy-harness/spec/platform/pi-agent-package.md` — package resource, launch/join, budget/failure, and output-mode adapter contract.
  - `packages/lazy-harness-pi/agents/record-reader.md` — dedicated canonical-record-only Reader role.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — `ReaderRunState`, explicit `lazy_reader_join`, record fingerprint reuse, steer invalidation, and print-mode stderr advisory separation.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` / `check-search-performed.sh` — successful Reader join evidence, safe Parent source inspection, and direct fallback.
  - `.lazy-harness/evidence/dedicated-reader-runtime-v1-20260906.md` — static implementation validation/review capsule.
  - `.lazy-harness/evidence/dedicated-reader-live-canary-r2-20260906.md` — live transport/join/output pass plus terminal budget/source-lane gaps and selected correction.
  - `.lazy-harness/decisions/0049-discovery-vs-loading-complete-lean-discovery.md` — mandatory complete discovery plus targeted loading.
  - `.lazy-harness/decisions/0052-external-context-extension-non-adoption.md` — forbids a competing compression/memory/routing authority by default.
- Configured Parent-transition guidance:
  - `.lazy-harness/behavior/agent-owned-target-context-transition.md` — direct-switch and CLI-fallback scenarios.
  - `.lazy-harness/ssot/policies.json#agent-owned-target-context-transition` — default behavior semantics.
  - `.lazy-harness/ssot/capabilities.json#agent-owned-target-context-transition` — preferred/discouraged actions.
  - `.lazy-harness/tests/project-operating-rulebook.md` — resolver regression expectations.
  - implemented Reader inventory/search across canonical harness layers,
  - implemented Parent source/test or immediate-behavior parallel lane guidance,
  - implemented join-before-plan/mutation/completion barrier,
  - implemented no-duplicate-debt behavior after successful Reader completion,
  - implemented failure/conflict/budget/stale fallback plus single Parent decision/writer/final-validator ownership.
- Cross-layer links:
  - Planning: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`
  - SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`, `.lazy-harness/spec/platform/pi-agent-package.md`
  - TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md`
- Machine index:
  - graph id: `kg_agent_owned_target_context_transition_20260826`; new Reader implementation graph rows are added in the isolated worktree.

## Rule placement

- Rule: the dedicated Reader owns harness-record discovery/loading; the Parent concurrently owns source/test or immediate-behavior investigation and joins the Reader response before decisions or action.
- Scope: framework-global.
- Primary record: `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md`.
- Why not AGENTS.md alone: this ADR owns the architecture trade-off; `.lazy-harness/AGENTS.md` now carries only the compact operational Reader/join/fallback grammar.
- Why not Pi/OMP local notes: the decision must remain runtime-neutral and shared by all future adapters.
- Confirmation: user-confirmed on 2026-07-24; runtime/source implementation remains separately approval-gated.
- Confirmation: user-confirmed on 2026-07-24; Reader runtime/source implementation remains separately approval-gated.
- Quality-preservation objective: user-confirmed on 2026-08-25 — the direct Parent workflow is the quality baseline; delegation must preserve it, not improve it, before performance/context/cost gains can count.
- Reader ownership correction: user-confirmed on 2026-08-26 — Reader searches and reads stored harness policy/fact records while Parent investigates code/behavior in parallel; successful Reader completion replaces duplicate Parent read-debt work.
- Target-transition correction: user-confirmed on 2026-08-26 — an available agent-owned target-root CLI precedes manual user handoff when direct switching is unavailable.
- Reader architecture reaffirmation: user-confirmed on 2026-09-04 — a failed generic-delegate/print-mode experiment must drive the missing Reader integration and result/output contracts; it must not silently change the accepted target back to Parent-owned record reading.
- Isolated implementation approval: user selected the full coherent Reader slice in a new worktree; live model smoke, main integration, commit, push, and release remain separate gates.
## Discovery capture

- DDD: updated — `.lazy-harness/domain/searchable-record-memory.md` defines Harness Reader, Parent code lane, and Reader join.
- SDD: updated — `.lazy-harness/spec/platform/search-read-debt-contract.md` records the accepted Reader-join supersession direction while current hooks remain transitional.
- BDD: updated — `.lazy-harness/behavior/llm-owned-record-retrieval.md` owns the parallel Reader/Parent/join behavior.
- TDD: updated — `.lazy-harness/tests/pre-action-search-evidence-guard.md` records planned Reader-join replacement regressions without claiming implementation.
- ADR: updated — this record supersedes parent-global/child-scoped debt ownership and v1–v3 proof-remediation architecture.
- SSOT: updated — `.lazy-harness/ssot/harness-enforcement-policy.md` makes Reader completion the target recall mechanism and direct debt hooks transitional.
- Planning: updated — `.lazy-harness/planning/agent-neutral-orchestration-pilot.md` closes v3 proof remediation and captures the simple Reader-join implementation backlog.

## Discovery capture — Reader architecture reaffirmation

- DDD: none; existing Harness Reader vocabulary remains sufficient.
- SDD: updated in search-read-debt and Pi package contracts for content-bearing join, package registration, and primary-answer preservation.
- BDD: updated with Reader result delivery and caller-visible output scenarios.
- TDD: updated with planned join/delivery/print-mode regressions without passing claims.
- ADR: updated here because the user corrected the interpretation of the failed topology run and reaffirmed the selected architecture.
- SSOT: none; current transitional enforcement and settings remain unchanged.
- Planning: updated to replace the mistaken permanent direct-Parent interpretation with a temporary fallback boundary.

## Discovery capture — isolated Reader runtime implementation

- DDD: implementation status only; established terms remain authoritative.
- SDD: updated for implemented Reader package, join/debt bridge, budgets, and output modes.
- BDD: updated because the selected parallel Reader/Parent behavior now has isolated implementation.
- TDD: updated with focused green Reader and print-mode fixtures; live model coverage remains pending.
- ADR: implementation status updated here without changing the accepted architecture.
- SSOT: direct debt is now an implemented fallback in the branch; main remains transitional.
- Planning: isolated slice is focused-green; independent review and main integration are still gated.
