# ADR 0045 — Map-First Retrieval Supersedes Purpose Find

Status: accepted
Date: 2026-06-22
Layer: ADR
Related DDD: `.lazy-harness/domain/purpose-scoped-retrieval.md`
Related BDD: `.lazy-harness/behavior/purpose-scoped-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`
Related TDD: `.lazy-harness/tests/purpose-scoped-retrieval.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Applies when:
  - retrieving project understanding or locating records, source, or tests in a host
  - choosing how to discover implementation evidence before answering or planning
- Must:
  - use map-first traversal: `lazy map --overview`, pick concrete nodes, expand, then read records/source/tests
  - keep the LLM/searcher as semantic authority; treat generated map/index/graph output as cue-only
  - on incomplete/ambiguous map, ask a 3-5 option gate or state the missing prerequisite
- Must not:
  - run `lazy find --purpose`, pass raw natural-language strings to `lazy map`, or fall back to keyword grep/rg/find
- Record completion:
  - changes to retrieval flow or map semantics update this ADR plus the purpose-scoped-retrieval DDD/BDD/SDD/TDD records
- Related records:
  - `.lazy-harness/domain/purpose-scoped-retrieval.md`
  - `.lazy-harness/behavior/purpose-scoped-retrieval.md`
  - `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`
  - `.lazy-harness/tests/purpose-scoped-retrieval.md`
  - `.lazy-harness/ssot/cli-tool-boundary.md`

## Context

Lazy-harness stores project understanding as project/topic anchors with DDD facts, BDD expectations, SDD contracts, TDD validation, ADR decisions, SSOT ownership, and source/test links. The retrieval helper must let the LLM follow that map and decide what to read.

`lazy find --purpose ...` violated that product shape in practice. Dogfood showed agents delegated semantic search to the CLI, overused `--purpose fact`, passed raw natural-language strings, and even invented `lazy map --query` syntax. Cross-project validation on 2026-06-22 showed source recall was weak enough that `lazy find` could not be trusted as an implementation locator.

## Decision

Remove `lazy find` from the active CLI and default retrieval workflow.

Canonical flow:

1. `lazy map --overview` prints the project map/inventory.
2. The LLM/searcher chooses concrete feature ids, record paths, graph ids, source paths, or test paths.
3. `lazy map <node>` expands a chosen node.
4. The agent reads canonical records, Implementation maps, graph links, source, and tests.
5. If the map/index is incomplete or ambiguous, the agent asks a 3-5 option gate or states the missing prerequisite instead of running keyword grep/rg/find fallback.

`lazy map` is a map traversal helper, not a free-form search box. It must reject raw user text, long natural-language strings, invented `--query` arguments, and keyword-search fallback semantics.

## Consequences

- The LLM/searcher remains semantic authority.
- Generated map/index/graph outputs stay cue-only.
- Rule/action lookup still uses `lazy rules resolve` and `lazy capability resolve`.
- Removed `lazy find` evidence no longer satisfies search-debt.
- Prompt guidance must teach map-first traversal, not purpose-scoped CLI search.

## Implementation map

- Status: `map-first-retrieval-implemented`
- Primary records:
  - `.lazy-harness/domain/purpose-scoped-retrieval.md`
  - `.lazy-harness/behavior/purpose-scoped-retrieval.md`
  - `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`
  - `.lazy-harness/tests/purpose-scoped-retrieval.md`
- Primary source:
  - `.lazy-harness/scripts/record-map.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh`
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py`
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py`
  - `.lazy-harness/ssot/capabilities.json`
  - `.lazy-harness/project/feature-navigation.xml`
  - `.lazy-harness/scripts/self-test.py`
- Validation:
  - `.lazy-harness/bin/lazy map --overview --format=md --limit=20`
  - `.lazy-harness/bin/lazy map <feature-id|record-path|graph-id|source-path> --format=json`
  - `.lazy-harness/bin/lazy map 'long natural language string' --format=json` must fail
  - `.lazy-harness/bin/lazy find --purpose fact foo` must fail
  - `.lazy-harness/bin/lazy test`

## Rule placement

- Rule: Retrieval is map-first and LLM-owned; CLIs may expose project-map/index nodes but must not own semantic search.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`
- Why not AGENTS.md: this is a retrieval architecture/runtime decision with source/tests and implementation maps; prompt grammar only points to the record behavior.
- Why not `.jcode`: this changes shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed
