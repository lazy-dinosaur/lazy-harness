# SDD — Graph Explain

Status: accepted-phase2-markdown
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
Related evidence: `.lazy-harness/evidence/2026-06-08-graph-explain-phase1-downstream-sync.md`
Related evidence: `.lazy-harness/evidence/2026-06-09-graph-explain-phase2-markdown-downstream-sync.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- User-confirmed option: A, Cited structural explanation
- Applies when:
  - designing, implementing, or validating `lazy graph explain`
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
  - support JSON structural packets and Phase 2 Markdown rendering while keeping path-backed statements as a future slice
- Must not:
  - emit `requiredRead`, `optionalRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, or `candidateMeanings`
  - summarize or interpret user intent
  - claim causality, completeness, correctness, semantic sufficiency, or required follow-up work
  - replace `lazy map`, `graph query`, `graph path`, `retrieval-audit`, or record/source/test reads
  - relax overview/read-debt/lifecycle/prompt/option-gate policy
  - add MCP, daemon, watch mode, prompt/reminder injection, or Graphify vendoring in this slice
- Record completion:
  - implementation changes must update this SDD, `.lazy-harness/tests/graph-explain.md`, `.lazy-harness/planning/graph-explain-implementation-plan.md`, `graph-query.ts`, self-test, manifest, graph rows, and downstream evidence together.

## CLI contract, Phase 2 current

Command:

```bash
.lazy-harness/bin/lazy graph explain '<term-or-file>' [--format=json|md] [--limit=N] [--max-statements=N] [--include-paths]
```

Current flags:

- `--format=json` — machine-readable structural packet. If omitted, `graph explain` defaults to JSON.
- `--format=md` — Phase 2 human-readable Markdown rendering of the same structural packet.
- `--limit=N` — caps underlying query/path candidates; default `8`.
- `--max-statements=N` — caps cited structural explanation statements; default `8`, max `20`.
- `--include-paths` — accepted in Phase 1 as a boundary flag; output reports `no-path-evidence` and leaves `pathPackets` empty until Phase 3.
- `--fresh` — allowed only if it preserves read-only/non-mutating behavior for canonical records and generated caches.

Current boundary:

- `lazy graph explain` is supported for JSON structural packets and Phase 2 Markdown rendering.
- Markdown rendering is supported as a Phase 2 view over the same structural packet.
- Path-backed statements remain a Phase 3 boundary; `--include-paths` emits `no-path-evidence` with empty `pathPackets`.

## Output shape, Phase 1 JSON

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
- `pathPackets`: empty array in Phase 1; future compact selected fields from `GraphPathResult` are Phase 3
- `fallback`: overview/map/retrieval-audit/grep commands
- `notes`: cue-only / generated-non-canonical / read-real-evidence reminders

Forbidden output fields anywhere:

```text
requiredRead optionalRead confidence intent risk gate nextAction candidateMeanings
```

## Output shape, Phase 2 Markdown

Markdown output must include:

- top cue-only/read-evidence caveats,
- mode/query/resultState/explanationKind metadata,
- a `## Statements` section where each statement bullet includes both `support:` and `citations:`,
- support sub-bullets with kind/provenance labels,
- fallback commands,
- bottom notes repeating that the Markdown does not satisfy read evidence and that LLM/searcher remains semantic authority.

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

## Implementation strategy, Phase 2 current

1. Parse `graph explain <query>` as a supported JSON/Markdown command.
2. Build a `GraphQueryResult` with existing `buildGraphQuery`.
3. Convert seeds, matched fields, citations, and graph edges into bounded structural statements.
4. Keep `--include-paths` as a boundary flag that reports `no-path-evidence` with empty `pathPackets` until Phase 3.
5. Render `--format=md` via `renderExplainMarkdown` from the same JSON packet.
6. Keep all JSON and Markdown statements compact, citation-backed, and support-backed.

## Implementation map

- Status: implemented-phase2-markdown
- Primary files:
  - `.lazy-harness/spec/platform/graph-explain.md` — this SDD.
  - `.lazy-harness/tests/graph-explain.md` — JSON/Markdown regression contract.
  - `.lazy-harness/planning/graph-explain-implementation-plan.md` — phased implementation plan.
  - `.lazy-harness/scripts/graph-query.ts` — implements parser, Phase 1/2 types, `buildGraphExplain`, JSON output, and `renderExplainMarkdown`.
  - `.lazy-harness/scripts/self-test.py` — implements `check_graph_explain_cli` regression protection for JSON and Markdown.
  - `.lazy-harness/bin/lazy` — advertises graph explain JSON/Markdown.
  - `.lazy-harness/evidence/2026-06-08-graph-explain-phase1-downstream-sync.md` — downstream sync/smoke validation capsule for source commit `dfd11ffe676500ad928c61789034835a81097ef1`.
  - `.lazy-harness/evidence/2026-06-09-graph-explain-phase2-markdown-downstream-sync.md` — downstream sync/smoke validation capsule for Phase 2 Markdown source commit `4208c85758fac89ff22b5edcddefad358d547d2a`.
- Current symbols:
  - `GraphExplainResult`
  - `GraphExplainStatement`
  - `GraphExplainSupport`
  - `buildGraphExplain`
  - `renderExplainMarkdown`
  - `check_graph_explain_cli`
- Current protection:
  - `check_graph_explain_cli` verifies JSON shape, Markdown caveats/support/citations, support/citations on every statement, recursive forbidden-field absence, read-only behavior, and include-paths boundary.
  - `check_graph_query_cli` and `check_graph_path_cli` remain graph query/path regression protection.
- Graph ids:
  - `kg_graph_explain_structural_design_20260608`
  - `kg_graph_explain_phase1_cli_20260608`
  - `kg_graph_explain_phase1_self_test_20260608`
  - `kg_graph_explain_phase2_markdown_cli_20260609`
  - `kg_graph_explain_phase2_markdown_self_test_20260609`
  - `kg_graph_explain_phase2_downstream_sync_20260609`
  - `kg_graph_explain_phase1_downstream_sync_20260608`

## Layer completeness impact

- DDD: no new domain entity; existing Searchable Record Memory still controls cue-only retrieval interpretation.
- BDD: LLM-owned record retrieval behavior remains unchanged; explain output is cue-only.
- SDD: this record defines the JSON/Markdown explain contract.
- TDD: `.lazy-harness/tests/graph-explain.md` defines JSON/Markdown and future path-backed fixtures.
- ADR: no new ADR required for Phase 2 because it does not relax policy or add runtime/dependency architecture. A new ADR is required before adding semantic authority, MCP, daemon, watch mode, Graphify vendoring, or lifecycle policy changes.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains controlling.
- Planning: `.lazy-harness/planning/graph-explain-implementation-plan.md` tracks phased implementation.

## Rule placement

- Rule: `lazy graph explain` must be a cited structural explanation helper only, not a semantic authority.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/graph-explain.md`
- Why not AGENTS.md: command contract, output shape, and implementation map belong in SDD/TDD/source, not always-loaded prompt grammar.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed option A
