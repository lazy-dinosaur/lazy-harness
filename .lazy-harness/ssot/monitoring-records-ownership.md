# SSOT — Monitoring Records Ownership

Status: accepted
Date: 2026-11-09
Layer: SSOT
Confirmation: user-confirmed (2026-11-09)

## Rule digest

- Status: active
- Layer: SSOT
- Scope: host-project
- Confidence: high
- Aliases:
  - monitoring records ownership
  - 모니터링 기록 정본
  - monitoring records landing
- Applies when:
  - changing monitoring decision, design, measurement or evidence records
  - deciding monitoring repository ownership, migration order or host composition
- Must:
  - keep monitoring decision/design/measurement records canonical on lazy-harness main; change them only through PRs
  - keep module code, tests and fixtures in lazy-dinosaur/lazy-harness-monitoring; retain evidence in lazy-harness
  - treat work/monitoring-engine-v2 as frozen history and never commit experiment result data
  - keep monitoring pinned-submodule-only and unattached in lazy-harness; composition remains parked
  - wait until the lazy-harness module connection contract is committed on main before adding monitoring's root declaration file, merging monitoring's connection-contract PR (#14) or opening the submodule-inclusion PR; then adapt monitoring to it in its own repository; module sessions do not delegate this work to the contract session
- Must not:
  - infer the same ownership rule for the knowledge module without a separate decision
- Record completion:
  - confirmed monitoring ownership, canonical location or composition changes update this SSOT through a PR
- Related records:
  - `.lazy-harness/decisions/0061-monitoring-core-fabric-optional.md`
  - `.lazy-harness/decisions/0062-monitoring-core-own-repository.md`
  - `.lazy-harness/planning/monitoring-core-live-integration-plan.md`

## Ownership and migration sequence

Monitoring decision, design and measurement records are canonical on **lazy-harness main** and change only via PRs. This records-only landing brings historical records to main through a PR; it does not activate monitoring or migrate implementation.

`work/monitoring-engine-v2` is a frozen historical branch. The 14 copied records document its pre-migration layout at `221553d`; their original content is preserved with one pre-migration note after each H1. Historical code/script/test/fixture paths are not claims that those implementations exist on main.

Module code, tests and fixtures live in **`lazy-dinosaur/lazy-harness-monitoring`**, independently of this repository. Monitoring core remains Fabric-independent and integration optional (ADR 0061). Evidence stays in lazy-harness under `.lazy-harness/evidence/monitoring-core/` (ADR 0062). Experiment result data is never committed; retained decision/measurement narratives and the synthetic author-review evidence table are not permission to commit raw experiment results.

As of the user decision on **2026-11-09**, lazy-harness includes monitoring only as a pinned submodule and **does not attach it**. Composition is parked; this ownership record grants no activation or attachment approval.

The knowledge module may adopt the same rule later, but only through a **separate decision**. After this records-only PR merges, LH-5 adds ADR 0063; this PR retains the ADR count of 62 and does not add ADR 0063.

## 2026-11-09 correction — contract first

User correction relayed by the contract session: modules started attaching before the lazy-harness connection contract existed. The contract is defined and documented on lazy-harness main by its own session; each module repository adapts after the contract commit is announced, without delegating that work to the contract session. Monitoring therefore holds its declaration file, PR #14 merge and submodule-inclusion PR. The declaration file `lazy-harness-module/v1` is still a draft with required/optional fields unconfirmed; those fields are owned by the contract SDD and are not restated here.

## Implementation map

- Status: verified (records-only ownership and sequence; no code or runtime attachment changed).
- Primary record: `.lazy-harness/ssot/monitoring-records-ownership.md` — canonical repository ownership, frozen-history boundary and parked composition.
- `.lazy-harness/decisions/0061-monitoring-core-fabric-optional.md` — Fabric-independent core and optional integration decision.
- `.lazy-harness/decisions/0062-monitoring-core-own-repository.md` — separate implementation repository and retained lazy-harness evidence ownership.
- `.lazy-harness/planning/monitoring-core-live-integration-plan.md` — historical design, qualification and migration planning context.
- `.lazy-harness/evidence/monitoring-core/input-v2-review.md` — verbatim synthetic author-review evidence table; not measured model accuracy or experiment result data.
- Allowed boundary: records-only PRs in lazy-harness; implementation work belongs to lazy-dinosaur/lazy-harness-monitoring.
- Forbidden boundary: implementation/test/fixture migration or runtime composition in this records-only landing; edits to frozen historical records on work/monitoring-engine-v2.
- Flow: historical records plus pre-migration note → records-only PR → canonical records on main → separate LH-5 ADR 0063 work.
- Protection: doctor full framework profile, record-lint, lazy check and standard validation; byte comparisons preserve the 14 original record bodies and the imported evidence.
- Exception procedure: obtain a separate user-confirmed decision and PR before changing ownership, composition or knowledge-module policy.

## Rule placement

- Rule: monitoring records land on lazy-harness main (records only, pre-migration note, canonical moves to main via PR; ownership in ssot/monitoring-records-ownership.md); lazy-harness only includes the pinned submodule, composition parked
- Scope: host-project
- Primary record: `.lazy-harness/ssot/monitoring-records-ownership.md`
- Why not AGENTS.md: repository ownership/sequence, not agent behaviour
- Why not local notes: shared repository ownership
- Confirmation: user-confirmed (2026-11-09)
