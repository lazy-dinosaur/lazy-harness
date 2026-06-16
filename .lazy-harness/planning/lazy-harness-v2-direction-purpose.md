# Lazy-Harness V2 Direction and Purpose

Status: draft
Date: 2026-06-16
Layer: Planning
Related DDD: `.lazy-harness/domain/searchable-record-memory.md`
Related SSOT: `.lazy-harness/ssot/project-navigation.md`, `.lazy-harness/ssot/rule-sources.md`
Related Project Map: `.lazy-harness/project/feature-navigation.xml`

## Purpose

Lazy-Harness V2 should help an agent keep durable understanding of a project as the project evolves.

The core product is not a CLI, folder taxonomy, hook, or graph search engine. The core product is an expanding **project map / project atlas**: a structured memory of facts, expectations, contracts, decisions, validation evidence, ownership, and source links.

## Direction

1. **Project understanding first**
   - Records should make the project easier to understand across sessions.
   - New knowledge should sharpen the project map instead of creating scattered notes.

2. **Agent-neutral core, Pi-first adapter**
   - V2 should reduce hard dependency on Jcode-specific wiring.
   - Jcode can remain an adapter, but the core should be usable by Pi agent and future agents.

3. **Records as knowledge nodes**
   - A record can have one primary home and multiple facets.
   - DDD, BDD, SDD, TDD, ADR, and SSOT do not need to be physically merged.
   - They can be facets/tags that describe what kind of knowledge a node contains.

4. **Canonical reading over generated authority**
   - Indexes, maps, and search helpers are navigation aids only.
   - Understanding comes from reading canonical records/source/tests and updating records after confirmation.

5. **Simpler user-facing mental model**
   - Instead of asking agents to constantly decide between many folders first, V2 should present a simpler map:
     - facts
     - expectations
     - contracts
     - decisions
     - validation
     - ownership / SSOT
     - source links
   - Existing V1 folders can remain as compatibility or implementation detail while the V2 taxonomy matures.

6. **Dynamic project/team policy optimization**
   - V2 should deserve the word "framework" by letting each project/team evolve its own working rules.
   - Examples include testing style, commit style, review style, system-design boundaries, release flow, validation commands, and collaboration conventions.
   - These rules are not one universal lazy-harness policy. They should be discovered, confirmed, versioned, audited, and promoted/demoted per project as real evidence accumulates.
   - The framework supplies the machinery: records, policy/capability registry, adapters, evidence capture, audit, sync, validation, and rollback paths.
   - A project decides whether a rule/capability is only discoverable, recommended, default, warning-level, or blocking.

## Non-goals for this direction note

- This is not implementation approval.
- This does not move existing records.
- This does not delete rulebook, DDD/BDD/SDD/TDD folders, or Jcode integration.
- This does not define the final V2 schema.

## Initial working thesis

Lazy-Harness V1 proved that record-first memory, validation, and source links are useful, but the system became too much about prompts, gates, and tool surfaces.

V2 should be simpler:

> Maintain a living project map so agents can recover project understanding, make better changes, and leave the map clearer than they found it.

And V2 should be more framework-like:

> Provide the machinery for project/team-specific rules to emerge, change, and become optimized for the project instead of hardcoding one universal workflow.

## Rule placement

- Rule: Lazy-Harness V2 direction should center on an expanding project map/atlas, agent-neutral durable understanding, and dynamic project/team policy optimization, with Pi as a primary adapter direction.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/lazy-harness-v2-direction-purpose.md`
- Why not AGENTS.md: this is architectural direction, not an immediate prompt rule.
- Why not `.jcode`: the direction explicitly reduces Jcode-specific coupling and applies to the shared framework.
- Confirmation: user-confirmed as direction/purpose discussion, not implementation approval.

## Discovery capture

- DDD: candidate only; uses existing Searchable Record Memory terms.
- BDD: candidate only; implies agent behavior should maintain project understanding.
- SDD: none yet; schema/contract is not designed here.
- TDD: none yet; validation strategy is not designed here.
- ADR: none yet; trade-off decision still needs a future ADR if adopted.
- SSOT: candidate only; future taxonomy/ownership records may be needed.
- Planning: updated by this draft direction record.
