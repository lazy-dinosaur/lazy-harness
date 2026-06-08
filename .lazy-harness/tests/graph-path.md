# TDD — Graph Path

Status: accepted
Date: 2026-06-08
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/graph-path.md`
Related SDD: `.lazy-harness/spec/platform/graph-query.md`
Related Planning: `.lazy-harness/planning/graph-path-implementation-plan.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - implementing or changing `lazy graph path`
  - changing graph query/path dispatch, bounded BFS, path output, or path Markdown rendering
  - deciding whether graph path remains cue-only and non-authoritative
- Must:
  - protect JSON and Markdown output shapes
  - protect linked, partial, and gap states
  - protect bounded BFS path output between two known graph-query cues
  - protect no semantic-authority fields recursively
  - protect read-only behavior: no canonical record, graph, generated cache, runtime journal, or user memory mutation
  - protect `lazy graph explain` remains unsupported until a separate slice
- Must not:
  - allow required-read, optional-read, confidence, intent, risk, gate, next-action, or candidate-meaning fields
  - treat path output as proof of evidence read or proof of causality
  - require path to replace query/map/retrieval-audit
- Record completion:
  - implementation changes update this TDD, SDD, source, dispatcher/help, self-test, graph rows, manifest sync entries, and evidence.

## Fixture matrix

| Fixture id | Scenario | Expected |
|---|---|---|
| `graph_path_linked_query_to_record` | `lazy graph path 'workflow compression not safety reduction' '.lazy-harness/ssot/cli-tool-boundary.md' --format=json --limit=8` | `resultState=linked`, at least one bounded path, endpoints include from/to candidates, no forbidden semantic fields |
| `graph_path_gap` | from/to cues do not match any structural candidates | `resultState=gap`, `no-from-candidates` or `no-to-candidates`, fallback commands present |
| `graph_path_partial` | endpoints exist but no bounded path under max depth | `resultState=partial`, `no-paths`, endpoint candidates present |
| `graph_path_read_only` | running path in source/temp host | graph JSONL and generated record-index cache are unchanged |
| `graph_path_markdown_warning` | markdown output | includes cue-only / measurement boundary warning and does not claim required reads |
| `graph_explain_still_unsupported` | `lazy graph explain` | still fails with explicit unsupported message |

Forbidden keys anywhere in output:

```text
requiredRead optionalRead confidence intent risk gate nextAction candidateMeanings
```

## Acceptance assertions

Self-test must verify:

1. `.lazy-harness/spec/platform/graph-path.md` exists.
2. `.lazy-harness/tests/graph-path.md` exists.
3. `lazy help` advertises `graph path <from> <to>`.
4. `lazy graph path 'workflow compression not safety reduction' '.lazy-harness/ssot/cli-tool-boundary.md' --format=json --limit=8 --max-depth=4` returns valid JSON.
5. Linked path output has `mode=graph-query.path`, `resultState=linked`, `paths.length > 0`, path nodes/edges, endpoints, citations, fallback, and notes.
6. Recursive forbidden-key check passes.
7. Graph path does not mutate `.lazy-harness/knowledge/graph.jsonl` or `.lazy-harness/generated/record-index.json`.
8. Markdown output contains `cue-only` and `does not satisfy read evidence`.
9. `lazy graph explain` remains unsupported.
10. Existing `lazy graph query` compactness and coverage tests still pass.

## Validation commands

Focused validation:

```bash
.lazy-harness/bin/lazy graph path 'workflow compression not safety reduction' '.lazy-harness/ssot/cli-tool-boundary.md' --format=json --limit=8 --max-depth=4
.lazy-harness/bin/lazy graph path 'zzzz-missing-from' 'zzzz-missing-to' --format=json --limit=8
.lazy-harness/bin/lazy graph path 'workflow compression not safety reduction' '.lazy-harness/ssot/cli-tool-boundary.md' --format=md --limit=8
python3 -m py_compile .lazy-harness/scripts/self-test.py
```

Full validation:

```bash
python3 .lazy-harness/scripts/self-test.py --scope framework
```

## Interpretation guard

A graph path is a navigation cue only. It is not:

- required-read proof,
- confidence,
- policy approval,
- causality proof,
- or next-action guidance.

## Implementation map

- Status: implemented
- Primary files:
  - `.lazy-harness/tests/graph-path.md` — this TDD record.
  - `.lazy-harness/spec/platform/graph-path.md` — path output contract.
  - `.lazy-harness/planning/graph-path-implementation-plan.md` — implementation plan.
  - `.lazy-harness/scripts/graph-query.ts` — implements graph path parser, bounded BFS, output shape, and Markdown warnings.
  - `.lazy-harness/bin/lazy` — advertises graph path.
  - `.lazy-harness/scripts/self-test.py` — `check_graph_path_cli` regression fixture.
- Key symbols:
  - `check_graph_path_cli`
  - `buildGraphPath`
  - `findBoundedPaths`
  - `renderPathMarkdown`
  - `parseArgs`
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
- Machine index:
  - graph id: `kg_graph_path_cli_20260608`

## Layer completeness impact

- DDD: no new terms; existing searchable record memory applies.
- BDD: LLM-owned retrieval boundary applies.
- SDD: `.lazy-harness/spec/platform/graph-path.md` defines contract.
- TDD: this record and self-test protect behavior.
- ADR: none for this implementation slice; ADR needed before policy change.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains controlling.
- Planning: `.lazy-harness/planning/graph-path-implementation-plan.md` tracks execution.

## Rule placement

- Rule: Graph path tests must prove path output is bounded, read-only, cue-only, and no semantic authority.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/graph-path.md`
- Why not AGENTS.md: regression fixture detail belongs in TDD/source, not prompt grammar.
- Why not `.jcode`: shared lazy-harness regression behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed option A
