# SDD — Graph Explain

Status: accepted-phase4-ranking-hardened
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

- Status: accepted-phase4-ranking-hardened
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
  - support JSON structural packets, Markdown rendering, and optional path-backed statement support through bounded graph path packets
- Must not:
  - emit `requiredRead`, `optionalRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, or `candidateMeanings`
  - summarize or interpret user intent
  - claim causality, completeness, correctness, semantic sufficiency, or required follow-up work
  - replace `lazy map`, `graph query`, `graph path`, `retrieval-audit`, or record/source/test reads
  - relax overview/read-debt/lifecycle/prompt/option-gate policy
  - add MCP, daemon, watch mode, prompt/reminder injection, or Graphify vendoring in this slice
- Record completion:
  - implementation changes must update this SDD, `.lazy-harness/tests/graph-explain.md`, `.lazy-harness/planning/graph-explain-implementation-plan.md`, `graph-query.ts`, self-test, manifest, graph rows, and downstream evidence together.

## CLI contract, Phase 3 current

Command:

```bash
.lazy-harness/bin/lazy graph explain '<term-or-file>' [--format=json|md] [--limit=N] [--max-statements=N] [--include-paths]
```

Current flags:

- `--format=json` — machine-readable structural packet. If omitted, `graph explain` defaults to JSON.
- `--format=md` — Phase 2 human-readable Markdown rendering of the same structural packet.
- `--limit=N` — caps underlying query/path candidates; default `8`.
- `--max-statements=N` — caps cited structural explanation statements; default `8`, max `20`.
- `--include-paths` — attaches bounded `GraphPathResult` packets for selected structural candidates when indexed paths exist; reports `no-path-evidence` only when no bounded path evidence is found.
- `--fresh` — allowed only if it preserves read-only/non-mutating behavior for canonical records and generated caches.

Current boundary:

- `lazy graph explain` is supported for JSON structural packets, Markdown rendering, and optional path-backed statements.
- Markdown rendering is a view over the same structural packet.
- Path-backed statements are structural navigation cues only; they do not prove evidence was read, causality, correctness, risk, gate state, or next action.
- Path-backed statements must use edge-backed paths only. Zero-edge/self paths may appear inside a bounded `pathPackets` payload, but they must not become `support.kind=path`, must not invent a `bounded_path` relation, and must not clear `no-path-evidence` by themselves.

## Ranking hardening, Phase 4

- `lazy graph explain` may use internal-only deterministic scoring to rank candidate statements.
- Internal scoring may consider path/title/slug token coverage, candidate array order, and a small query-token-gated cross-layer bridge set for retrieval/workflow and CLI-boundary records.
- Scores, confidence, importance, required-read, optional-read, risk, gate, intent, next action, or candidate meaning must not appear in JSON or Markdown output.
- Candidate statements are ranked independently from seed/citation/edge generation order, but every emitted statement must remain support-backed and citation-backed.
- The permanent gold-labeled benchmark command is:

```bash
.lazy-harness/bin/lazy graph-explain-accuracy-benchmark [--format=json|md] [--precision-k=N] [--fail-on-thresholds]
```

- The benchmark is measurement-only and cue-only; it does not become semantic authority or required-read policy.
- `--fail-on-thresholds` is a framework source-checkout gate because the gold labels are selected against the source repo's framework records/evidence. Downstream product hosts may run the command for schema/policy smoke, but must not treat source gold-threshold failure as a downstream deployment failure.

## Dynamic write/read workflow boundary

User-confirmed direction (2026-06-09): lazy-harness agents are expected to continuously search, read, write records/source, run validation, and search/read again. In that loop, generated graph/query/explain output is useful as a fast ranked cue surface, but it is not the source of truth.

Contract:

- `graph query`, `graph path`, and `graph explain` may accelerate navigation through ranked/cited generated graph context.
- They must remain stale-cache-safe: a generated graph result can be behind recently edited records/source/tests until indexes are rebuilt.
- After any mutation, agents must read the changed canonical records/source/tests and run focused validation rather than trusting generated graph state.
- Future Graphify-style watch, MCP, daemon, or generated graph export work must preserve this cue-only/non-canonical boundary.
- The preferred architecture for dynamic LLM write/read loops is hybrid: Graphify-style cue graph plus canonical record/source/test reads plus validation gates.

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
- `pathPackets`: empty unless `--include-paths`; with `--include-paths`, contains bounded `GraphPathResult` packets selected from graph-query candidates
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

## Implementation strategy, Phase 3 current

1. Parse `graph explain <query>` as a supported JSON/Markdown command.
2. Build a `GraphQueryResult` with existing `buildGraphQuery`.
3. Convert seeds, matched fields, citations, and graph edges into bounded structural statements.
4. Implement `--include-paths` by selecting bounded graph-query candidate targets and calling `buildGraphPath` as cited structural support.
5. Render `--format=md` via `renderExplainMarkdown` from the same JSON packet, including a `## Path packets` section.
6. Convert only edge-backed paths into path support statements; do not promote zero-edge/self paths as evidence.
7. Keep `candidate_context` wording limited to endpoint presence in the other graph-query packet and explicit non-semantic boundary language.
8. Keep all JSON and Markdown statements compact, citation-backed, support-backed, and non-semantic.

## Implementation map

- Status: implemented-phase3-path-backed
- Primary files:
  - `.lazy-harness/spec/platform/graph-explain.md` — this SDD.
  - `.lazy-harness/tests/graph-explain.md` — JSON/Markdown regression contract.
  - `.lazy-harness/planning/graph-explain-implementation-plan.md` — phased implementation plan.
  - `.lazy-harness/scripts/graph-query.ts` — implements parser, `buildGraphExplain`, JSON output, `renderExplainMarkdown`, `explainPathTargets`, `buildExplainPathPackets`, and `pathPacketSupport`.
  - `.lazy-harness/scripts/self-test.py` — implements `check_graph_explain_cli` regression protection for JSON, Markdown, `--include-paths` path packets, zero-edge/self path non-evidence, and `candidate_context` boundary wording.
  - `.lazy-harness/bin/lazy` — advertises graph explain JSON/Markdown.
  - `.lazy-harness/evidence/2026-06-08-graph-explain-phase1-downstream-sync.md` — downstream sync/smoke validation capsule for source commit `dfd11ffe676500ad928c61789034835a81097ef1`.
  - `.lazy-harness/evidence/2026-06-09-graph-explain-phase2-markdown-downstream-sync.md` — downstream sync/smoke validation capsule for Phase 2 Markdown source commit `4208c85758fac89ff22b5edcddefad358d547d2a`.
  - `.lazy-harness/evidence/2026-06-09-graph-explain-phase3-path-downstream-sync.md` — downstream sync/smoke validation capsule for Phase 3 path-backed source commit `e8a0ca872b8e531fb0ca7e4ac2250cf613ce9941`.
- Current symbols:
  - `GraphExplainResult`
  - `GraphExplainStatement`
  - `GraphExplainSupport`
  - `buildGraphExplain`
  - `renderExplainMarkdown`
  - `explainPathTargets`
  - `buildExplainPathPackets`
  - `pathPacketSupport`
  - `check_graph_explain_cli`
- Current protection:
  - `check_graph_explain_cli` verifies JSON shape, Markdown caveats/support/citations, support/citations on every statement, recursive forbidden-field absence, read-only behavior, `--include-paths` path packet/support behavior, zero-edge/self path non-evidence, and `candidate_context` boundary wording.
  - `check_graph_query_cli` and `check_graph_path_cli` remain graph query/path regression protection.
- Graph ids:
  - `kg_graph_explain_structural_design_20260608`
  - `kg_graph_explain_phase1_cli_20260608`
  - `kg_graph_explain_phase1_self_test_20260608`
  - `kg_graph_explain_phase2_markdown_cli_20260609`
  - `kg_graph_explain_phase2_markdown_self_test_20260609`
  - `kg_graph_explain_phase3_path_cli_20260609`
  - `kg_graph_explain_phase3_path_self_test_20260609`
  - `kg_graph_explain_phase3_path_downstream_sync_20260609`
  - `kg_graph_explain_phase2_downstream_sync_20260609`
  - `kg_graph_explain_phase1_downstream_sync_20260608`

## Layer completeness impact

- DDD: no new domain entity; existing Searchable Record Memory still controls cue-only retrieval interpretation.
- BDD: LLM-owned record retrieval behavior remains unchanged; explain output is cue-only.
- SDD: this record defines the JSON/Markdown/path-backed explain contract.
- TDD: `.lazy-harness/tests/graph-explain.md` defines JSON/Markdown/path-backed fixtures.
- ADR: no new ADR required for Phase 3 because it does not relax policy or add runtime/dependency architecture. A new ADR is required before adding semantic authority, MCP, daemon, watch mode, Graphify vendoring, or lifecycle policy changes.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains controlling.
- Planning: `.lazy-harness/planning/graph-explain-implementation-plan.md` tracks phased implementation.

## Rule placement

- Rule: `lazy graph explain` must be a cited structural explanation helper only, not a semantic authority.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/graph-explain.md`
- Why not AGENTS.md: command contract, output shape, and implementation map belong in SDD/TDD/source, not always-loaded prompt grammar.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed option A
