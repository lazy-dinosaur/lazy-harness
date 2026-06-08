# SDD — Graph Explain

Status: accepted-design-not-implemented
Date: 2026-06-08
Layer: SDD
Related SDD: `.lazy-harness/spec/platform/graph-query.md`
Related SDD: `.lazy-harness/spec/platform/graph-path.md`
Related TDD: `.lazy-harness/tests/graph-explain.md`
Related Planning: `.lazy-harness/planning/graph-explain-implementation-plan.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related ADR: `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md`
Related Planning: `.lazy-harness/planning/retrieval-architecture-holistic-review.md`
Related Planning: `.lazy-harness/planning/graph-index-migration-considerations.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- User-confirmed option: A, Cited structural explanation
- Applies when:
  - designing, implementing, or validating a future `lazy graph explain` command
  - using graph query/path outputs to produce human-readable structural explanations
  - evaluating whether Graphify-style `explain` can be added without making CLI output semantic authority
- Must:
  - keep `lazy graph explain` additive, read-only, cue-only, deterministic, TypeScript/Bun based, and non-canonical
  - return cited structural explanation only: matched fields, graph rows, records, paths, edges, and provenance that explain why candidates appeared
  - require every explanatory statement to cite one or more record paths, source/test paths, graph row ids, generated-index ids, or edge provenance strings
  - preserve LLM/searcher as semantic authority; the command may explain structure but must not decide meaning, sufficiency, risk, gate, or next action
  - reuse existing graph query/path inputs and output contracts where possible
  - cap output by `--limit`, `--max-statements`, and optional path-depth controls
  - include explicit notes that output does not satisfy read evidence
  - keep `lazy graph explain` unsupported until SDD/TDD/plan validation is complete and implementation is separately committed
- Must not:
  - emit `requiredRead`, `optionalRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, or `candidateMeanings`
  - summarize or interpret user intent
  - claim causality, completeness, correctness, semantic sufficiency, or required follow-up work
  - replace `lazy map`, `graph query`, `graph path`, `retrieval-audit`, or record/source/test reads
  - relax overview/read-debt/lifecycle/prompt/option-gate policy
  - add MCP, daemon, watch mode, prompt/reminder injection, or Graphify vendoring in this slice
- Record completion:
  - implementation changes must update this SDD, `.lazy-harness/tests/graph-explain.md`, `.lazy-harness/planning/graph-explain-implementation-plan.md`, `graph-query.ts`, self-test, manifest, graph rows, and downstream evidence together.

## CLI contract, planned

Command:

```bash
.lazy-harness/bin/lazy graph explain '<term-or-file>' [--format=json|md] [--limit=N] [--max-statements=N] [--include-paths]
```

Planned flags:

- `--format=json|md` — default `md`.
- `--limit=N` — caps underlying query/path candidates; default `8`.
- `--max-statements=N` — caps cited structural explanation statements; default `8`, max `20`.
- `--include-paths` — optionally include bounded path evidence between top candidates, still cue-only.
- `--fresh` — allowed only if it preserves read-only/non-mutating behavior for canonical records and generated caches.

Current boundary:

- `lazy graph explain` remains unsupported until a later implementation commit.
- The current command must continue to fail with an explicit unsupported prototype-slice message.

## Output shape, planned

JSON output must include:

- `mode: graph-query.explain`
- `query`
- `resultState: explained | partial | gap`
- `explanationKind: structural`
- `coverage.gaps`: structural gaps only, e.g. `no-query-candidates`, `no-citations`, `no-path-evidence`
- `statements`: bounded list of cited structural statements
  - `statement`: a short structural sentence, not a semantic judgement
  - `support`: array of structural support items
    - `kind`: `matched-field | graph-edge | graph-row | record | source | test | path`
    - `path` or `id`
    - `relation` when applicable
    - `provenance`
  - `citations`: array of citation ids/paths repeated from support
- `queryPacket`: compact selected fields from `GraphQueryResult`
- `pathPackets`: optional compact selected fields from `GraphPathResult`
- `fallback`: overview/map/retrieval-audit/grep commands
- `notes`: cue-only / generated-non-canonical / read-real-evidence reminders

Forbidden output fields anywhere:

```text
requiredRead optionalRead confidence intent risk gate nextAction candidateMeanings
```

## Semantics

`lazy graph explain` should answer only:

> “What indexed/cited structure caused these graph query/path candidates to appear?”

It must not answer:

- what the user means,
- what the agent must read,
- whether evidence is sufficient,
- whether a relation is causal,
- whether a change is safe,
- or what the next action should be.

It explicitly does **not satisfy read evidence**. Agents must still read real records/source/tests before relying on any statement.

## Structural statement rules

Allowed statement examples:

- `Record X appears because query token Y matched field Z.`
- `Candidate X is connected to candidate Y through edge relation R from provenance P.`
- `Path output used candidate_context fallback because endpoint path P appeared in the other query packet.`
- `No path evidence was found within max depth N; fallback commands are provided.`

Forbidden statement examples:

- `This is the correct record to read.`
- `The user likely means X.`
- `Confidence is high.`
- `You should do Y next.`
- `This proves X caused Y.`

## Implementation strategy, planned

1. Parse `graph explain <query>` only after this SDD/TDD/plan is accepted.
2. Build a `GraphQueryResult` with existing `buildGraphQuery`.
3. Convert seeds, matched fields, candidate lists, citations, and graph edges into bounded structural statements.
4. If `--include-paths` is set, optionally call `buildGraphPath` between selected endpoint candidates, but only as cited support.
5. Render JSON and Markdown from the same structural packet.
6. Keep all statements compact and citation-backed.
7. Preserve current unsupported behavior until implementation is complete.

## Implementation map

- Status: planned
- Primary files:
  - `.lazy-harness/spec/platform/graph-explain.md` — this SDD.
  - `.lazy-harness/tests/graph-explain.md` — regression contract for future implementation.
  - `.lazy-harness/planning/graph-explain-implementation-plan.md` — phased implementation plan.
  - `.lazy-harness/scripts/graph-query.ts` — planned implementation location for parser, builder, and renderer.
  - `.lazy-harness/scripts/self-test.py` — planned regression protection.
  - `.lazy-harness/bin/lazy` — planned help/dispatcher update if implementation starts.
- Planned symbols:
  - `GraphExplainResult`
  - `GraphExplainStatement`
  - `buildGraphExplain`
  - `renderExplainMarkdown`
  - `check_graph_explain_cli`
- Current protection:
  - `check_graph_query_cli` and `check_graph_path_cli` keep `lazy graph explain` unsupported until implementation.
- Planned graph id:
  - `kg_graph_explain_structural_design_20260608`

## Layer completeness impact

- DDD: no new domain entity; existing Searchable Record Memory still controls cue-only retrieval interpretation.
- BDD: LLM-owned record retrieval behavior remains unchanged; explain output is cue-only.
- SDD: this record defines the planned explain contract.
- TDD: `.lazy-harness/tests/graph-explain.md` defines implementation fixtures before code changes.
- ADR: no new ADR required for this design-only slice because it does not relax policy or add runtime/dependency architecture. A new ADR is required before adding semantic authority, MCP, daemon, watch mode, Graphify vendoring, or lifecycle policy changes.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains controlling.
- Planning: `.lazy-harness/planning/graph-explain-implementation-plan.md` tracks phased implementation.

## Rule placement

- Rule: `lazy graph explain` must be a cited structural explanation helper only, not a semantic authority.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/graph-explain.md`
- Why not AGENTS.md: command contract, output shape, and implementation map belong in SDD/TDD/source, not always-loaded prompt grammar.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed option A
