# Lazy-Harness V2 Evolution Context

Status: draft
Date: 2026-06-16
Layer: Planning
Related direction: `.lazy-harness/planning/lazy-harness-v2-direction-purpose.md`
Related ADR: `.lazy-harness/decisions/0001-core-philosophy.md`, `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`, `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`, `.lazy-harness/decisions/0043-pi-native-package-in-source-repo.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## Purpose

This note captures the broad evolution that led to the V2 direction. It is not a final schema, migration plan, or implementation approval.

The point is to preserve what was learned while building lazy-harness so V2 is not designed from a shallow slogan.

## Original goal

Lazy-Harness started from Principle 0:

> Humans and AI are both incomplete, so the framework should let them complement each other.

The initial target was not “more automation.” The target was a working loop where:

- humans catch what AI misses,
- AI records what humans should not have to remember,
- project knowledge accumulates instead of being lost between sessions,
- and validation catches drift before broken assumptions become permanent.

## What V1 built

V1 accumulated several useful capabilities:

1. **Record-first memory**
   - DDD/SDD/BDD/TDD/ADR/SSOT records became durable project memory.
   - The framework learned to prefer records/source/tests over chat memory or generated caches.

2. **Lifecycle feedback loops**
   - response/completion hooks and self-tests caught missing records, stale plans, and incomplete validations.
   - Later amendments reduced over-blocking during development and moved stronger checks to commit/push validation.

3. **Implementation maps**
   - Markdown records gained Implementation map sections.
   - Confirmed file/symbol/edge facts also go into `.lazy-harness/knowledge/graph.jsonl`.
   - Generated indexes are derived navigation caches, not canonical truth.

4. **Project/source navigation**
   - `feature-navigation.xml`, record-index, record-map, and purpose-scoped retrieval improved rediscovery.
   - The useful part is navigation and candidate surfacing, not semantic authority.

5. **Rule and capability experiments**
   - Project operating rulebook and capability registry tried to separate “what is true here?” from “how should agents act here?”
   - The concept is useful, but current rulebook surface may be too heavy if it does not actually improve agent behavior.

6. **Pi direction**
   - Pi-native package work showed the framework should not remain Jcode-bound.
   - Jcode can be an adapter, but the core should be agent-neutral and Pi-first capable.

## What V1 taught us not to do

1. **Do not turn CLI into semantic authority**
   - `lazy route` and route telemetry were superseded because static tools classified user intent/risk/gate from raw text.
   - Graph query/path/explain also became risky because it encouraged agents to trust cue output instead of reading records.

2. **Do not optimize for search at the cost of understanding**
   - Graph CLI produced attractive token/coverage metrics, but harmed record-first discipline.
   - It was rolled back so retrieval returns to `lazy map`, `lazy find`, `retrieval-audit`, grep/source/test reads, and canonical records.

3. **Do not make layer placement the user-facing product**
   - DDD/SDD/BDD/TDD/ADR/SSOT are useful lenses.
   - But forcing agents to experience the framework primarily as folder-choice friction can distract from the real goal: maintaining project understanding.

4. **Do not store project policy in local agent wiring**
   - `.jcode/**` is local/private wiring.
   - Shared project rules, facts, decisions, and ownership must converge into `.lazy-harness/**` records.

## V2 interpretation

V2 should treat V1 as a proof that durable record memory works, but the presentation needs to become simpler and more project-map-oriented.

The V2 product should be:

> A living project map / project atlas that lets agents recover context, make safer changes, and leave the project easier to understand than before.

This means records are best understood as **knowledge nodes**:

- each node can have a primary home,
- each node can carry multiple facets such as DDD, BDD, SDD, TDD, ADR, SSOT,
- each node should connect to source files, tests, ownership, decisions, and validation evidence,
- and generated tools should help navigate the map without becoming semantic judges.

## Current working direction

Keep the useful V1 primitives:

- record-first memory,
- source/test evidence,
- implementation maps,
- graph JSONL as confirmed edge storage,
- generated indexes as rebuildable caches,
- self-test and validation discipline,
- explicit option gates for ambiguity,
- project-local `.lazy-harness` as canonical host memory.

Simplify or reconsider the V1 friction points:

- excessive prompt/gate burden,
- rulebook as a separate heavy surface,
- folder-first layer placement UX,
- Jcode-specific assumptions,
- any CLI/helper that tries to become a semantic judge.

## Rule placement

- Rule: V2 planning must account for the full V1 evolution: record memory, lifecycle validation, implementation maps, navigation aids, rulebook/capability experiments, Pi migration, and graph rollback lessons.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/lazy-harness-v2-evolution-context.md`
- Why not AGENTS.md: this is planning context and architectural memory, not an immediate agent grammar rule.
- Why not `.jcode`: this is shared framework direction and explicitly includes reducing Jcode coupling.
- Confirmation: user-confirmed goal that the framework should understand everything built and learned so far.

## Discovery capture

- DDD: candidate only; reinforces searchable record memory and project-map vocabulary.
- BDD: candidate only; reinforces behavior that agents should preserve understanding across sessions.
- SDD: none yet; no schema/contract change in this note.
- TDD: none yet; no validation change in this note.
- ADR: candidate only; future V2 ADR should cite this context if adopted.
- SSOT: candidate only; future taxonomy/ownership records may cite this context.
- Planning: updated by this draft evolution record.
