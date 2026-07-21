# SDD — Code Organization Profile

Status: active-pilot
Date: 2026-07-20
Layer: SDD
Related ADR: `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
Related policy contract: `.lazy-harness/spec/platform/policy-machinery-v2.md`
Related runtime contract: `.lazy-harness/spec/platform/pi-agent-package.md`
Related TDD: `.lazy-harness/tests/code-organization-profile.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Confidence: medium
- Aliases:
  - code organization profile
  - source organization profile
  - code shape review
  - 코드 정돈 프로필
  - 코드 구성 원칙
- Surface terms:
  - local chronological coherence
  - narrowing ownership path
  - delayed extraction
  - lifecycle vocabulary
  - changed-surface review
- Applies when:
  - creating, modifying, extracting, or reviewing source code
  - deciding whether a long flow should stay local or become a shared authority
  - reviewing duplicated executable flows or unclear lifecycle ownership
- Must:
  - preserve domain-shape continuity and local chronological coherence
  - keep ownership paths narrowing toward one accountable implementation
  - extract only when repetition or reuse would otherwise create multiple authorities
  - review only new or changed source during the observe stage
  - resolve matching host-project source-work policies/capabilities before applying the framework baseline
- Must not:
  - infer system architecture, prescribe folders, or split files by line count
  - mirror Goedamjip or bulk-rewrite untouched source
- Record completion:
  - profile semantics or rollout changes update this SDD and its TDD/policy/runtime links
- Related records:
  - `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
  - `.lazy-harness/spec/platform/guidance-ladder.md`
  - `.lazy-harness/spec/platform/pi-agent-package.md`
  - `.lazy-harness/tests/code-organization-profile.md`

## Purpose

The Code Organization Profile gives agents a reusable way to review how code is arranged locally without turning one reference repository, folder taxonomy, or named architecture into a universal standard.

Goedamjip was inspected as a read-only Golden Reference. Its source supplied evidence for useful local organization principles, but its current tree, legacy choices, framework, business model, and folder names are not copied as rules.

Profile v1 is the framework baseline, not the only project rule. A host may add narrower `host-project` source-organization policies and capabilities in its canonical registries. On a source-file context event, Lazy-Harness resolves exact source-work intents through those host registries and surfaces the matching source records, summaries, and actions alongside this baseline.

## Separate track from system architecture

System architecture and code organization are related but have different authority:

| Track | Owns | Does not own |
|---|---|---|
| Three-layer architecture guidance | host topology, scoped bindings, boundaries, contracts, state/effect ownership, Host Architecture Map truth | within-file ordering or a universal source layout |
| Code Organization Profile | local discoverability, source flow, naming continuity, extraction timing, and changed-source review | host topology, business/domain design, profile confirmation, folders, deployment, or enforcement |

A local organization observation never confirms a Layer 2 binding, writes a Host Architecture Map, or selects FSD, Clean, Hexagonal, DDD, modular-monolith, or any other named architecture. If a review exposes a real system-boundary question, it becomes a separate architecture candidate and option gate.

## Profile v1 principles

### COP-01 — Domain-shape continuity

Keep important domain names and data shapes recognizable through input, state, decision, rendering, and effect paths. Introduce a transformed representation only when it owns a real boundary or invariant.

This does not require one object shape everywhere. Boundary validation, persistence, generated contracts, and independently evolving APIs may need explicit representations.

### COP-02 — Local chronological coherence

When a module owns a lifecycle or executable flow, arrange its local implementation so a reader can follow the meaningful sequence: establish inputs and state, derive decisions, perform effects, handle completion/failure, then clean up.

Do not reorder public APIs, declarations, or cohesive sections mechanically. Chronology is a readability aid, not a universal AST order.

### COP-03 — Narrowing ownership path

Composition should narrow toward one accountable owner. Entry and composition surfaces connect the workflow; a feature/controller owns the interaction or lifecycle; reusable helpers own stable mechanics.

This principle does not prescribe page/feature/shared folders. The host decides paths and system boundaries separately.

### COP-04 — Explicit lifecycle vocabulary and owner

Use consistent lifecycle words for materially different phases, such as setup, start, pause, resume, complete, fail, cancel, and cleanup. Timers, listeners, media/animation handles, requests, and subscriptions should have one discoverable owner and cleanup path.

This is the local expression of lifecycle clarity. Cross-process or cross-service guarantees remain architecture/contract concerns.

### COP-05 — Delayed extraction, single authority

Keep a coherent flow local while it has one owner and one change reason. Extract a shared authority when one of these becomes true:

- near-identical executable flows are maintained in multiple places;
- independently reused mechanics have a stable contract;
- duplicated state/effect/lifecycle logic can drift;
- local density hides the accountable owner or cleanup path.

A long file alone is not evidence for extraction. Conversely, line-count reduction is not success if it fragments one chronological flow across shallow wrappers.

## Review protocol

A Code Organization Profile review reports observations, not architecture truth:

1. name the changed source surface;
2. cite the relevant `COP-*` principle and concrete source evidence;
3. distinguish semantic judgement from mechanically observable evidence;
4. recommend keep-local, rename/reorder, extract-one-authority, or explicitly-diverge;
5. state uncertainty and stop before a new architecture or business-design decision.

The default success result may be `no organization change needed`. Resolved host guidance may narrow or extend the review for that project, but it cannot silently infer system architecture or promote enforcement beyond its declared policy level.

## Semantic and mechanical responsibility

### LLM-owned judgement

The LLM/reviewer decides:

- whether source order preserves the meaningful lifecycle;
- whether names preserve domain shape;
- where the accountable owner is;
- whether repetition represents one shared authority or intentional divergence;
- whether extraction improves or damages local coherence.

No shell hook or raw-text classifier may decide these meanings.

### Mechanically observable candidates

Tools may surface evidence such as:

- high-similarity executable blocks;
- repeated lifecycle registrations or cleanup signatures;
- duplicate exported mechanics;
- structural complexity around one changed flow.

Profile v1 defines no universal line-count, similarity, complexity, or file-count threshold. Existing AST/lint/duplication diagnostics may supply observe-stage evidence, but they do not decide the recommendation.

## Rollout

### Phase O — observe (active)

- applies only to newly created or modified source files;
- surfaces the framework baseline and matching host-project source guidance through typed `recommend` policy/capability resolution plus the Pi/OMP source-touch context reminder;
- adds no AST/lint rule, warning, block, scaffold, or bulk rewrite;
- keeps untouched legacy source outside the active review surface.

### Phase W — warn (not approved)

A mechanical warning requires measured observe-stage examples, explicit false-positive analysis, user confirmation, a bypass, and focused fixtures. Each rule is promoted independently.

### Phase B — block (not approved)

Blocking is exceptional and requires the Guidance Ladder L5 promotion contract. This profile alone cannot authorize a hard stop.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/code-organization-profile.md` — canonical Profile v1 semantics and rollout boundary.
  - `.lazy-harness/AGENTS.md` — compact changed-source review pointer.
  - `.lazy-harness/hooks/lifecycle/on-context.sh` — derives exact source-work intents from file-tool labels and requests host-resolved guidance.
  - `.lazy-harness/hooks/lifecycle/helpers/operating_rule_catalog.py` — renders canonical policy/capability resolver matches without user-text classification.
  - `.lazy-harness/ssot/policies.json` — typed `recommend` policy.
  - `.lazy-harness/ssot/capabilities.json` — review checklist capability binding.
  - `.lazy-harness/generated/policy-rulebook.md` — non-canonical generated explanation.
- Key symbols:
  - `check_code_organization_profile` (`.lazy-harness/scripts/self-test.py`) — protects records, advisory policy/capability, manifest distribution, and source-touch reminder behavior.
  - `check_on_context_surfaces_operating_rule_catalog` (`.lazy-harness/scripts/self-test.py`) — protects the generic mid-turn context surface.
- Flow:
  1. A source file is created, read, or modified.
  2. Pi/OMP context re-grounding derives only mechanical source-work intents from the file-tool label.
  3. Canonical `lazy capability resolve` and `lazy policy resolve` calls return framework and host-project matches.
  4. The reminder surfaces matching source records, summaries, and actions; the LLM reads them and reviews only the changed source.
  5. Typed policy levels remain authoritative, and any future warning or block requires separate evidence and approval.
- Tests / protection:
  - `.lazy-harness/tests/code-organization-profile.md`
  - `.lazy-harness/scripts/self-test.py#check_code_organization_profile`
  - minimal temp-host fixture proving a host-only source policy/capability appears in source context and not record-only context
- Ownership boundaries:
  - Framework owns the reusable profile and advisory transport.
  - Each host owns its architecture, domain rules, folder mappings, exceptions, and additional source-organization policies/capabilities; framework sync preserves host registry entries.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`, `.lazy-harness/decisions/0048-operating-rule-storage-apply-repair.md`
  - SDD: `.lazy-harness/spec/platform/pi-agent-package.md`
  - TDD: `.lazy-harness/tests/code-organization-profile.md`
  - SSOT: `.lazy-harness/ssot/policies.json`, `.lazy-harness/ssot/capabilities.json`
- Machine index:
  - graph ids: `kg_code_organization_profile_runtime_20260720`, `kg_code_organization_profile_policy_20260720`, `kg_code_organization_profile_test_20260720`
  - generated index key: pending regeneration

## Layer completeness impact

- DDD: no independent delta; this profile does not define business vocabulary or invariants.
- BDD: no independent product-visible flow; agent review behavior is owned by this platform SDD/runtime contract.
- SSOT: independent typed policy/capability registry entries are added without a new prose SSOT.
- ADR: ADR 0054 is amended to separate local source organization from Host Architecture Map truth.
- TDD: `.lazy-harness/tests/code-organization-profile.md` owns regression protection.

## Rule placement

- Rule: review changed source with Profile v1 while keeping local organization separate from system architecture and enforcement.
- Scope: framework-global.
- Primary record: `.lazy-harness/spec/platform/code-organization-profile.md`.
- Why not AGENTS.md alone: AGENTS carries only the compact pointer; this SDD owns the full semantics and rollout.
- Why not architecture profiles: local source arrangement cannot confirm host topology or a Layer 2 binding.
- Confirmation: user selected the Code Organization Profile track on 2026-07-20, then explicitly selected the host adaptation bridge so project-specific source rules affect actual agent guidance rather than remaining stored metadata.

## Discovery capture

- DDD: no independent delta.
- SDD: this record is the primary contract for Profile v1 and host-resolved observe-stage source guidance.
- BDD: no independent product behavior delta.
- TDD: new regression record and focused self-test protection.
- ADR: ADR 0054 receives the two-track boundary amendment.
- SSOT: typed policy/capability entries are the canonical operating-policy bindings.
- Planning: no separate plan record; warn/block and mechanical-rule promotion remain explicit future gates here.
