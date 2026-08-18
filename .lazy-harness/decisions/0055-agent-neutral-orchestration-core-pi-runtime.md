# ADR 0055 — Agent-Neutral Orchestration Core with Pi Subagents Runtime

Status: accepted architecture direction; runtime implementation not approved
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
  - 오케스트레이터 리드 뎁트
- Applies when:
  - delegating project retrieval, context sharding, or evidence extraction to subagents
  - deciding whether the parent or child owns complete discovery, evidence epochs, and read debt
  - designing a retrieval-child prompt, work packet, evidence packet, or model route
- Must:
  - keep orchestration semantics in the Lazy-Harness core and Pi Subagents as a thin execution runtime
  - make the top-level orchestrator own complete discovery, governing-record reads, semantic decisions, and final integration
  - give retrieval children bounded concrete nodes and require real record/source/test reads with provenance
  - make the parent read the child packet plus selected decision-critical canonical evidence
- Must not:
  - treat child task text, claims, or an unverified packet as parent `requiredRead` proof
  - load the whole project into every retrieval child by default or create a second policy/memory authority
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

The research objective is to reduce request-to-validation wall-clock time under a finite context window without weakening record recall, semantic judgement, or regression protection. A retrieval child that receives the whole project and repeats the parent's complete discovery, full grammar loading, and broad record reads defeats context sharding. The opposite shortcut—letting a child claim that it read evidence and automatically clearing the parent's debt—creates a false-proof boundary.

Current contracts establish two important baselines:

1. ADR 0049 requires complete lean discovery and targeted loading.
2. The Search/Read Debt SDD binds evidence to a root-scoped epoch and does not accept map cues as concrete required-read evidence.

Current Pi/OMP behavior also force-loads the full `.lazy-harness/AGENTS.md` grammar once per session. There is no verified delegated-evidence bridge that can transfer a child's successful reads into the parent guard. Therefore the target architecture and the currently deployed behavior must remain explicit and separate.

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

### 2. Read-debt ownership

Use **parent-global + child-scoped** debt ownership.

The top-level orchestrator owns, per fresh root-bound evidence epoch:

1. complete lean map discovery,
2. selection and direct reading of governing records,
3. selection of concrete feature/record/graph/source/test nodes for delegation,
4. semantic conflict resolution and option gates,
5. final plan, mutation decision, integration, and validation claim.

A retrieval child owns only the scoped loading debt delegated in its packet:

1. verify root, revision/fingerprint, and evidence epoch,
2. drill into the supplied concrete nodes,
3. read the necessary canonical record/source/test bodies,
4. return bounded claims with path/hash/range provenance,
5. return an explicit overflow or ambiguity status instead of silently expanding scope.

Complete discovery remains mandatory for the logical work unit. This ADR proposes that the orchestrator perform it once per evidence epoch; a read-only child may avoid repeating the complete overview only after a dedicated delegated-retrieval contract is implemented and protected. Until then, current runtime contracts remain unchanged.

### 3. Retrieval-child context and prompt

A child does not need prior knowledge of the entire project. It receives a bounded packet containing at least:

- root and revision/tree identity,
- parent evidence epoch,
- one objective and its dependencies,
- concrete map nodes selected by the parent,
- allowed record/source/test read scope,
- constraints and acceptance criteria,
- output budget and artifact destination,
- model route.

Use a **thin derived Evidence Scout prompt**, not a second `AGENTS.md` or policy engine. The profile is derived from canonical Lazy-Harness rules and contains only the invariants needed for the role:

- root-bound and freshness-checked,
- read-only,
- canonical-body reads rather than cue-only claims,
- no silent inference,
- no user decision, canonical promotion, mutation, or child subagent fan-out,
- bounded evidence output with unresolved states.

Current Pi/OMP package behavior still force-loads the full grammar into each activated session. This decision does not claim that prompt reduction is implemented. Phase 0 may test bounded task/output behavior using the existing runtime, but prompt-size savings require a separately approved role-profile loading change.

### 4. Parent proof after delegation

Use **packet + selective direct reads**.

The parent must read the bounded evidence packet. It then directly reads canonical evidence for:

- governing rules and contracts,
- conflicting or ambiguous claims,
- high-risk boundaries,
- facts that determine the final design or mutation,
- evidence sampled to validate scout fidelity.

The parent need not reread every child-read file. Conversely, a packet alone does not satisfy the parent's current `requiredRead` debt. Any future automatic handoff requires a verified supervisor event bound to root, revision, evidence epoch, successful tool result, concrete path/hash proof, and packet provenance.

### 5. Phase boundary

Phase 0 uses existing Pi Subagents only; it does not add a queue, daemon, new execution engine, competing memory store, or delegated-evidence permit. The parent continues to satisfy its own map/read debt directly.

A future implementation slice may add packet schemas, a role-profile adapter, and a verified evidence bridge only after explicit approval and focused regressions. Deferred canonicalization and Record Writer orchestration remain separate concerns even if they reuse packet/freshness primitives.

## Rejected alternatives

- **Every child performs full independent discovery.** Safe but duplicates map, prompt, and record-loading cost and weakens context sharding.
- **Give every child the full project context.** Recreates a large main context in each worker and increases context rot.
- **Full `AGENTS.md` plus a permanent scout overlay as the target.** Preserves current safety but leaves avoidable prompt duplication; retained only as the current runtime baseline.
- **Trust a verified packet without parent semantic reads.** Too weak for conflicts, high-risk decisions, and current guard semantics.
- **Build a new queue/daemon/agent engine first.** Adds control-plane complexity before the orchestration hypothesis is measured.

## Consequences

### Positive

- Global discovery and semantic authority stay with one accountable orchestrator.
- Child context is proportional to its evidence claim rather than project size.
- Pi remains replaceable as a runtime adapter.
- Parent rereads become risk- and decision-focused instead of duplicating all scout work.

### Negative / risks

- The parent still pays complete discovery and governing-record cost.
- Phase 0 cannot claim prompt-token savings while children still receive the full grammar.
- Selective rereads require a measurable sampling policy to detect scout omissions.
- A future evidence bridge has a strict trust boundary and can reintroduce false proof if implemented loosely.

## Implementation map

- Status: `none` — records-only architecture decision; no source/schema/runtime mutation is approved in this work unit.
- Current contract evidence:
  - `.lazy-harness/spec/platform/search-read-debt-contract.md` — root-scoped evidence epoch and direct map/read debt semantics.
  - `.lazy-harness/spec/platform/pi-agent-package.md` — current full-grammar Pi/OMP loading and adapter boundary.
  - `.lazy-harness/decisions/0049-discovery-vs-loading-complete-lean-discovery.md` — mandatory complete discovery plus targeted loading.
  - `.lazy-harness/decisions/0052-external-context-extension-non-adoption.md` — forbids a competing compression/memory/routing authority by default.
- Planned protection before runtime adoption:
  - wrong-root and stale-revision/epoch rejection,
  - task-text/path-mention and failed-read false-proof rejection,
  - concrete-node scoped reads and overflow states,
  - packet provenance plus parent selective-reread sampling,
  - single integrator/writer/final-validator ownership.
- Cross-layer links:
  - Planning: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`
  - SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`, `.lazy-harness/spec/platform/pi-agent-package.md`
  - TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md`
- Machine index:
  - no graph row added because no implementation file/symbol edge is yet approved or verified.

## Rule placement

- Rule: the top-level orchestrator owns global discovery and semantic authority; retrieval children perform bounded scoped reads through an agent-neutral contract executed first by Pi Subagents.
- Scope: framework-global.
- Primary record: `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md`.
- Why not AGENTS.md: this is an architecture trade-off and future runtime boundary, not yet an implemented all-agent grammar rule.
- Why not Pi/OMP local notes: the decision must remain runtime-neutral and shared by all future adapters.
- Confirmation: user-confirmed on 2026-07-24; runtime/source implementation remains separately approval-gated.

## Discovery capture

- DDD: none — orchestration labels are defined locally here; no independent business/domain invariant is promoted.
- SDD: candidate — packet, role-profile, and verified-evidence contracts are persisted in this ADR and pilot plan but await implementation approval.
- BDD: none — no product-visible flow changed; the future internal agent flow remains a pilot candidate.
- TDD: candidate — the required root/epoch/provenance/false-proof fixtures are persisted above and in the pilot plan; no runtime regression record changes yet.
- ADR: updated — this record captures the confirmed responsibility and trust-boundary decision.
- SSOT: none — no queue path, schema authority, permanent model default, or runtime owner configuration is approved.
- Planning: updated — `.lazy-harness/planning/agent-neutral-orchestration-pilot.md` captures the bounded experiment and unresolved implementation gates.
