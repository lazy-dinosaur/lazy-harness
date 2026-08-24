# ADR 0055 — Agent-Neutral Orchestration Core with Pi Subagents Runtime

Status: accepted architecture direction; compact admission v2 is implemented with a 6k soft target/12k hard cap and archived v1 validation; Luna High/live compact runs/main integration remain separately gated
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
  - make the top-level orchestrator own complete lean overview discovery, governing-record reads, coverage-basis facets, candidate-map approval/reopening, semantic decisions, and final integration
  - let the single read-only Reader profile operate only in explicit `candidate-map` or `claim-evidence` Work Packet mode; candidate-map proposes unverified evidence questions and claim-evidence loads one Parent-approved bundle
  - require bounded concrete nodes, canonical body reads with path/hash/range provenance, input-relative coverage conservation, freshness identity, explicit overflow, and fixed-point remap on newly discovered questions
  - make the Parent read the packet plus selected decision-critical canonical evidence; packets never transfer Parent read debt
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

Parent and ordinary Pi/OMP roles force-load the full `.lazy-harness/AGENTS.md` grammar once per session. The approved Reader-only slice adds one explicit package-owned `record-reader/v2` exception: a dedicated evidence-loading contract plus a hard canonical-record-only tool/lifecycle boundary. There is still no verified delegated-evidence bridge that can transfer child reads into the Parent guard.

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

A retrieval child owns only the scoped loading debt delegated in its explicit mode:

1. verify root, exact revision, Parent-attested canonical snapshot/overview identity, and evidence epoch;
2. drill only supplied concrete nodes—never run complete overview;
3. in `candidate-map`, conserve Parent-supplied objective facets/inventory entries into unverified evidence questions, unmapped items, or Parent-authored exclusions;
4. in `claim-evidence`, load one Parent-approved evidence bundle and return bounded claims with direct path/content-hash/range provenance;
5. return overflow, conflict, stale identity, dependency blockage, or `needs-remap` instead of silently expanding scope or claiming false completeness.

Complete discovery remains mandatory for the logical work unit and stays exclusively with the Parent. The single `record-reader/v2` role cannot run overview fallback. Candidate-map output is a non-authoritative routing proposal, never proof of claim completeness. The Parent approves or rewrites the proposed bundles before any claim-evidence dispatch.

### 3. Retrieval-child context and prompt

A child does not need prior knowledge of the entire project. It receives a bounded packet containing at least:

- packet/work-unit/parent ids plus explicit `candidate-map | claim-evidence` mode,
- root, exact revision, canonical working-set snapshot, complete-overview fingerprint, and Parent evidence epoch,
- one objective, Parent-authored coverage facets, and dependencies,
- concrete map nodes selected by the Parent,
- allowed canonical record scope and Parent-authored exclusions,
- constraints, hard read/tool/output budgets, and acceptance criteria,
- candidate-map approval or evidence-bundle identity where applicable,
- model route.

Use a **thin derived Evidence Scout prompt**, not a second `AGENTS.md` or policy engine. The profile is derived from canonical Lazy-Harness rules and contains only the invariants needed for the role:

- root-bound and freshness-checked,
- read-only,
- canonical-body reads rather than cue-only claims,
- no silent inference,
- no user decision, canonical promotion, mutation, or child subagent fan-out,
- bounded evidence output with unresolved states.

The earlier v1 and faithful full/no-write/no-approval/core profiles are retained only as experiment evidence, not package roles. The user-confirmed 2026-08-23 consolidation exposes one `record-reader/v2` Evidence Reader contract: Parent owns operating/development rules, complete overview, options, decisions, writing, and validation; Reader owns scoped canonical record loading and provenance; source verification remains a separate future role. This implements the ADR's thin-derived-scout direction instead of slicing or duplicating Parent AGENTS grammar.

The later user-confirmed review keeps one profile and adds two explicit packet modes rather than a second Scope Mapper role. `candidate-map` returns unverified evidence questions, coverage conservation, overlap/cycle proposals, and routing hints from Parent-supplied facets and concrete nodes. `claim-evidence` loads one approved evidence bundle. New questions, undeclared overlap, or dependency change force `needs-remap`; the Reader never recursively schedules work. Input-relative coverage plus fixed-point reopening reduces silent omission risk but does not claim absolute task-global completeness.

### 4. Parent proof after delegation

Use **packet + selective direct reads**.

Before candidate-map approval, the Parent directly reads governing rules/contracts and reconciles every supplied facet/inventory entry against assigned, unmapped, or explicitly excluded coverage. After claim-evidence packets return, it reads the bounded packets and directly reads canonical evidence for:

- governing rules and contracts,
- conflicting or ambiguous claims,
- high-risk boundaries,
- facts that determine the final design or mutation,
- a deterministic sample used to validate Reader fidelity.

Any `newEvidenceQuestions`, undeclared overlap, changed dependency, stale fingerprint, overflow, or failed sample reopens or invalidates the map. The Parent need not reread every child-read file. Conversely, no packet satisfies Parent `requiredRead` debt. Any future automatic handoff still requires a verified supervisor event bound to root, revision, canonical snapshot, evidence epoch, successful tool result, concrete path/hash proof, and packet provenance.

### 5. Phase boundary

Phase 0 uses existing Pi Subagents with one package-owned Record Reader profile; it does not add a queue, daemon, new execution engine, competing memory store, delegated-evidence permit, Source Verifier, or Record Writer. The Parent continues to satisfy its own map/read debt directly.

The guarded extension publishes explicit candidate-map/claim-evidence profile semantics: Parent-supplied coverage conservation, canonical snapshot identity, content-hash provenance, role ceilings, overlap/cycle proposals, and fixed-point remap outcomes. The extension hard-enforces only role marker, canonical tool scope, and Parent lifecycle/evidence isolation; it does not parse raw packet text or machine-validate semantic output. On 2026-08-23 the user separately approved one reversible self-host pilot, then corrected its unstarted model route after a transport-only precheck: run identical bounded candidate-map inputs sequentially on Luna medium and Luna high; select Medium only with no decision-relevant loss, High only when it uniquely passes, and stop on material disagreement. The selected route could unlock exactly two parallel claim-evidence Readers only after Parent inspection proved complete input-relative coverage, two disjoint dependency-safe bundles, and unchanged fingerprints. Automatic decomposition/scheduling, machine packet admission/counters, retries or follow-on waves, model defaults, verified evidence transfer, source verification, writing, and general runtime adoption remain separate gates.

Measured candidate result: both Luna arms conserved every supplied facet/inventory entry but independently returned one `single-reader` bundle, so the Parent enforced the approved fallback and launched no two-lane claim wave. Both also made one runtime-blocked compound root probe before recovering with the three exact allowed commands; the hard guard held.

The user then approved one bounded correction plus follow-up: clarify that root/revision verification requires three separate calls while preserving compound-command denial, protect it in static/fake-runtime tests, validate, and compare one identical Parent-normalized shared claim bundle on Luna medium versus high. This does not approve a tool expansion, machine packet admission, model default, automatic follow-on, merge, or promotion.

Measured claim result: both Luna arms attempted the prohibited `contact_supervisor` tool first and the records-only runtime blocked it. Both then obeyed the corrected three-call root probe and avoided overview, source, mutation, recursion, and external access, but both returned `incomplete`. The launcher soft-nudged finalization at 12 calls despite the packet's 14-call ceiling, leaving only one of three record hashes in each output. High directly loaded all three approved bodies and returned Q1–Q4; Medium loaded two bodies and returned Q1–Q2. That material difference cannot select High because neither route passed, and it cannot select Medium on efficiency. The blocked-attempt stop rule therefore leaves no selected model, retry, automatic follow-on, or promotion.

The user then approved exactly one corrected repeat. The Record Reader launch transport must disable Pi Subagents native supervisor/intercom coordination per child, retain the Lazy-Harness denial of leaked `contact_supervisor`, and set runtime soft/hard tool limits equal to the packet's 14-call budget. Prompt/reminder, SDD/TDD, static negative mutations, fake-runtime denial, isolated bridge-off configuration, focused validation, fresh Parent identity, and one identical sequential Luna medium/high rerun are in scope. Any prohibited tool surface/attempt, incomplete provenance, stale identity, or other prior stop condition ends the rerun without another retry; model defaults, automatic follow-on, merge, and promotion remain unapproved.

Corrected measured result: bridge-off and equal-budget transport passed; both Readers used the same 13 successful allowed calls and preserved the frozen dirty repository. Medium returned `needs-remap` after treating an already supplied not-read planning seed as a new dependency. Parent audit classified that as a conservative false-positive remap because ADR 0059 directly owns the rollback boundary and the approved three-record cap intentionally allowed one of four seeds under `notRead`. High returned a contractually valid bundle-local `complete` with Q1–Q4/F1–F6 direct provenance, all three hashes, required inventories, and no new question, dependency/overlap change, conflict, or overflow. There was no unresolved factual disagreement. Under the user-approved unique-pass rule, `openai-codex/gpt-5.6-luna:high` is selected only for separately approved future Record Reader runs; no persistent default or automatic follow-on is authorized.

The separately approved first real-work High shadow then tested integration-readiness candidate mapping. Runtime isolation and evidence coverage held, but packet semantics did not: High abbreviated and mistyped the frozen snapshot identity, exceeded the hard output budget while reporting no overflow/`proposal-ready`, and omitted packet-required `parentMustRead`. Because exact freshness, hard ceilings, and complete output shape are admission requirements, the Parent rejected the map and launched no claim-evidence stage. This is a **NO-GO for main integration**, while High remains only the previously selected experimental route.

The user then approved deterministic machine admission and one exact High shadow rerun. Pi Subagents supplies a strict dynamic `outputSchema` and its internal `structured_output` protocol tool; the package admission helper binds exact identity, requires common/mode fields, conserves Parent inputs, checks Parent reread provenance and hard output characters, and rejects inconsistent success states. This is a narrow packet-shape/declared-closure trust boundary, not semantic evidence validation, source verification, automatic scheduling, or merge authority.

Independent pre-rerun review `84f1e420-cc3b-4819-b6d5-89be5581ec9f` blocked the first implementation: packet contracts could exceed role ceilings, Parent coverage/exclusion and claim facet/question inputs were optional, the Parent CLI did not independently revalidate nested schema shape, claim remap questions lacked provenance structure, and a same-name `structured_output` tool was allowed without Pi Subagents runtime evidence. The first remediation rejects over-ceiling/missing-input contracts, binds Parent-authored exclusions and candidate/claim coverage, revalidates the closed generated schema, requires records-backed provenance, defines output size as compact-JSON Unicode code points, restores structured remap questions, gates the internal tool on absolute schema/capture runtime paths, and adds candidate/claim/adversarial/Unicode fixtures.

Follow-up reviewer `35e0b080-b680-49e7-b4e4-822d4c17ecd4` found no blocker but retained two High gaps before live execution: contracts still omitted mandatory common objective/node/layer/Parent-read/risk scope and claim map/bundle/seed/dependency/shared-owner identity, while provenance path/hash binding did not bind the cited ranges to `recordsRead.ranges`. It also found Parent exclusions were authorization-only rather than exact and that coverage arrays could exceed output schema cardinality. The second remediation makes those scope/bundle fields mandatory, echoes map/bundle identity as schema constants, preserves Parent exclusions exactly, binds approved seeds/dependencies/owners, rejects impossible cardinality, and requires every provenance range to have been directly recorded.

Closure reviewer `e39d07ca-c3e2-4936-aeb2-fabe17cf6cf9` found no blocker or High remaining and confirmed common scope, claim identity/basis, range provenance, and exact exclusions. Its sole Medium was a satisfiability edge: 64 candidate inputs exceeded the 32-row unmapped inventory, while a claim could approve 32 references but each claim could carry only 16. The final static correction caps candidate coverage at 32 total IDs and claim question/facet bases at 16 each, aligns schema inventories, and adds accepted-boundary plus one-over rejection fixtures. Focused checks, exact TypeBox compilation, and final standard/full regression then passed.

Measured exact logical rerun: Luna High run `db834bed-fb07-4563-ab98-01a65736083d` proved the real Pi Subagents dynamic-schema/capture path and obeyed all 14 allowed calls with no prohibited attempt or repository drift. It echoed exact identity, conserved F1–F7/I1–I8, supplied two records plus `parentMustRead`, and proposed one `single-reader` bundle. Parent admission nevertheless changed its self-reported `proposal-ready` to `invalid-packet`: compact JSON was 14,108 characters against 6,000, and three question provenance ranges were absent from the matching `recordsRead.ranges` inventories. The machine boundary therefore catches the prior false-success class, but the real-work Reader gate still fails. No claim stage, retry, main integration, default, or promotion follows.

The user separately clarified the intended rule-recall division: the Parent concentrates on harness grammar, behavior/guidance records, governing reads, and the final ordinary-guidance-versus-L5 interpretation; the existing Reader carries bounded canonical rule evidence and `parentMustRead` only. The selected path was one skipped-rule/L5-misclassification shadow through the unchanged two-mode contract, with no new role, full Parent grammar, policy authority, delegated debt, or `governingRuleCandidates` field.

Measured rule-recall shadow `a9c9bf32-7dd5-4a01-80c7-73acd90b2f33` qualitatively supported that division: it identified skipped retrieval as the failure class, separated organic guidance/search-read evidence from a new tool-specific L5, preserved Parent interpretation authority, returned ADR 0041 plus enforcement SSOT in `parentMustRead`, and represented the evidence with existing fields. Parent direct reads agreed, so this case demonstrates no semantic need for a rule-specific role/field. The packet was still `invalid-packet` at 8,310/6,000 characters with one range-inventory mismatch. The remaining demonstrated problem is compactness/range discipline, not authority allocation.

The user approved compact admission v2, then corrected the initial proposal that treated 6,000 as a fixed hard ceiling. New packets keep full identity/scope in a Parent envelope and emit one `contractDigest` plus normalized short-id evidence/coverage tables. Output uses a 6,000 soft target and 12,000 hard cap: exceeding target is a visible warning, while evidence that cannot accurately fit the hard cap returns status `overflow` with split detail instead of trimming. Archived v1 validation remains available. This is a wire/admission change only; Parent authority, Reader tools, read debt, and two-mode semantics do not move. No live compact run or main integration is approved.

Three fresh compact-v2 review passes drove closure. Initial reviewer `b30d9bc5-812a-45ec-aef6-32af9e577899` found remap, bundle/dependency, seed/node, canonical provenance, grammar/status, and TypeBox evidence gaps. Follow-up `a364ce42-12ab-4ef5-bbfc-1c40de8ce2e9` reported no High and narrowed three Medium ownership/budget edges. After approved-dependency binding, exactly-one bundle ownership, records>=2, 64-hash, and TypeBox Check fixtures, closure reviewer `acb68852-a98d-40ad-8ed7-cdff7644b2d6` reported no blocker, High, or Medium findings. Run/capture association remains explicitly Parent-audited rather than claimed by the digest receipt.

User-approved compact rule-recall canary `79dd9d1c-0ff8-4a62-b929-8e189e678d0c` was deterministically admitted `proposal-ready` at 3,143 characters with no warning, down 62.2% from the prior 8,310. It retained both questions, all eight inputs, direct evidence, risks, Parent rereads, verification, overlap, one bundle, and routing with no decision-relevant semantic loss. Runtime/repository boundaries held. The Reader did batch both reads before both hashes instead of immediate read→hash interleaving; hashes matched before output, so evidence remains valid but protocol ordering is a residual. This one candidate sample does not authorize claim loading, integration canary, main merge, default, or promotion.

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

- The Parent still pays complete discovery, governing-record, candidate-map approval, and selective verification cost.
- Candidate-map adds a serial stage and can increase total tokens/cost even when parallel evidence loading reduces wall-clock.
- Claim completeness remains probabilistic: conservation covers Parent-supplied facets and fixed-point discoveries, not unknowable omitted concepts.
- Dirty working trees require canonical snapshot and per-record content hashes; HEAD alone is insufficient.
- Overlapping or cyclic evidence closure can erase parallel benefit and must collapse to one bundle or fall back to one Reader/Parent.
- Selective rereads require a measurable sampling policy to detect Reader omissions.
- Profile clauses and transport schema alone do not prove valid LLM output. Three independent review passes required role-ceiling and satisfiable-cardinality admission, mandatory common/claim scope identity, full nested Parent-side revalidation, exact Parent exclusion and candidate/claim closure, records-backed path/hash/range provenance, structured remap evidence, runtime-owned internal-tool gating, and Unicode boundary fixtures before the approved exact High shadow may run. The closure review reported no blocker/High; its one Medium cardinality edge was corrected before final validation. Semantic evidence and source truth remain directly audited.
- A future evidence bridge has a strict trust boundary and can reintroduce false proof if implemented loosely.

## Implementation map

- Status: `experimental-reader-v2-compact-canary-admitted-main-gated` — compact v2 static validation and one bounded rule-recall canary pass at 3,143 characters with semantic fidelity retained. One hash-order deviation and single-sample/over-target-live gaps remain. Parent authority and records-only runtime hold; claim/main/default/scheduling/merge/promotion are unapproved.
- Current implementation evidence:
  - `packages/lazy-harness-pi/agents/record-reader.md` — one two-mode role with compact Parent envelope/digest, F/I/N/V/R/Q/B/D references, normalized evidence/coverage, accuracy-first soft/hard output policy, remap/overflow, and Parent reread semantics.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — unchanged records-only/lifecycle enforcement plus compact-v2/contractDigest/soft-hard reminder.
  - `packages/lazy-harness-pi/scripts/record-reader-admission.ts` — one v1/v2 CLI with compact digest/closed grammar, canonical provenance, exact coverage/node/seed/bundle/dependency/remap/status closure, soft warning, hard rejection, and deterministic receipts.
  - `packages/lazy-harness-pi/package.json` — package-owned Reader discovery and admission CLI script.
  - `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — v1 compatibility; compact digest/candidate/claim/scale/adversarial/status/ownership/40-64-hash and conditional installed-peer TypeBox Compile/Check fixtures; unchanged fake-runtime isolation.
- Current contract evidence:
  - `.lazy-harness/spec/platform/search-read-debt-contract.md` — root-scoped Parent evidence epoch and direct Parent map/read debt semantics.
  - `.lazy-harness/spec/platform/pi-agent-package.md` — role delivery, two-mode packet, and adapter boundary.
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md` — Parent discovery → candidate proposal → approved evidence loading → fixed-point reopen → Parent selective reread.
  - `.lazy-harness/decisions/0049-discovery-vs-loading-complete-lean-discovery.md` — complete Parent discovery plus targeted loading.
- Deferred protection before broader adoption:
  - automatic supervisor handoff and semantic evidence verification beyond deterministic packet admission,
  - admission thresholds, automatic dependency/overlap scheduling, retries/follow-on pilot waves, and any broader multi-Reader rollout,
  - Source Verifier and implementation-drift packet,
  - delegated read-debt recognition, Record Writer, model default, and production promotion.
- Cross-layer links:
  - BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
  - Planning: `.lazy-harness/planning/record-reader-thin-profile-experiment.md`
  - SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`, `.lazy-harness/spec/platform/pi-agent-package.md`
  - TDD: `.lazy-harness/tests/pi-agent-package.md`, `.lazy-harness/tests/pre-action-search-evidence-guard.md`
- Machine index:
  - base v2: `kg_record_reader_evidence_profile_impl_20260823`, `kg_record_reader_evidence_profile_test_20260823`
  - guarded modes: `kg_record_reader_two_mode_decision_20260823`, `kg_record_reader_two_mode_contract_impl_20260823`, `kg_record_reader_two_mode_contract_test_20260823`
  - first conditional pilot approval: `kg_record_reader_two_mode_pilot_approval_20260823`
  - Luna candidate A/B correction: `kg_record_reader_luna_candidate_ab_approval_20260823`
  - Luna candidate A/B measured stop: `kg_record_reader_luna_candidate_ab_result_20260823`
  - separate-probe + claim A/B approval: `kg_record_reader_claim_ab_approval_20260823`
  - measured stopped claim A/B: `kg_record_reader_claim_ab_result_20260823`
  - controlled rerun approval: `kg_record_reader_claim_rerun_approval_20260823`
  - transport correction: `kg_record_reader_transport_isolation_impl_20260823`, `kg_record_reader_transport_isolation_test_20260823`
  - corrected claim result + per-run route: `kg_record_reader_claim_rerun_result_20260823`, `kg_record_reader_luna_high_selection_20260823`
  - real-work High shadow NO-GO: `kg_record_reader_high_shadow_result_20260823`
  - machine admission, compact closure, and canary: `kg_record_reader_compact_contract_review_closure_20260824`, `kg_record_reader_compact_contract_validation_20260824`, `kg_record_reader_compact_rule_recall_canary_result_20260824`

## Rule placement

- Rule: the top-level orchestrator owns global discovery and semantic authority; retrieval children perform bounded scoped reads through an agent-neutral contract executed first by Pi Subagents.
- Scope: framework-global.
- Primary record: `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md`.
- Why not AGENTS.md: this is an architecture trade-off and opt-in role delivery boundary, not an all-agent grammar rule.
- Why not Pi/OMP local notes: the decision must remain runtime-neutral and shared by all future adapters.
- Confirmation: user approved compact v2 and exactly one rule-recall canary. The canary was admitted below target with no decision-relevant loss; one non-immediate hash-order deviation remains. No retry, claim, integration canary, automatic follow-on, default, promotion, Source Verifier, Writer, delegated debt, or main merge is approved.

## Discovery capture

- DDD: none — orchestration labels are defined locally here; no independent business/domain invariant is promoted.
- SDD: updated for compact v2 envelope/digest, normalized ids/tables, archived v1 validation, and separate output target/cap.
- BDD: compact rule-recall candidate behavior is now live-validated on one below-target sample; general and over-target accuracy remain unproven.
- TDD: updated with archived v1 plus compact digest/candidate/claim/reference/coverage/remap/scale and soft-hard fixtures.
- ADR: updated — this record owns the admission trust boundary and main gate.
- SSOT: none — no permanent queue, memory, model default, or project storage authority is introduced.
- Planning: owns measured duplication, compact implementation approval, accuracy-first budget correction, deferred graph migration, and future live-run gate.
