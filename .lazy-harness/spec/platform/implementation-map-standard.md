# Implementation Map Standard

Status: accepted
Layer: SDD
Related ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
Related SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
Related graph spec: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`

## 1. Purpose

Every reusable lazy-harness record should make the implementation discoverable for both humans and AI tools.

A record is not complete if it only explains intent. When implementation exists or can be verified, it should also point to:

- files that implement the knowledge
- symbols/functions/classes/components that matter
- tests or fixtures that protect it
- cross-layer records that explain, specify, validate, or decide it
- generated search/index artifacts that can be rebuilt by tooling
- ownership boundaries that say which host/service/file owns a behavior and what must not be changed here

## 2. Three-layer storage model

| Layer | Path | Role | Canonical? |
|---|---|---|---|
| Human report | `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/**/*.md` | Readable explanation plus short `Implementation map` section | Yes, for explanation |
| Machine graph | `.lazy-harness/knowledge/graph.jsonl` | Confirmed file/symbol/edge facts usable by AI search and future LSP-backed retrieval | Yes, for confirmed graph facts |
| Generated index | `.lazy-harness/generated/implementation-index.json` | Rebuildable cache from LSP/AST/outline/search results | No, derived only |

## 3. Required Markdown section

When a DDD/SDD/BDD/TDD/ADR/SSOT record refers to implemented behavior, add this section unless there is no implementation yet.

```md
## Implementation map

- Status: `none | planned | verified | stale | needs-review`
- Primary files:
  - `path/to/file.ts` — role in this record
- Key symbols:
  - `symbolName` (`path/to/file.ts`) — why it matters
- Flow:
  1. Entry point or trigger
  2. Core implementation path
  3. Output, side effect, or persisted state
- Tests / protection:
  - `path/to/test.ts` — what it guards
- Ownership boundaries:
  - Owner/upstream: `host/service/path`
  - This host may change: `compatibility/API/query/UI glue`
  - This host must not change without explicit confirmation: `shared DB schema/data migrations/upstream contracts`
- Cross-layer links:
  - DDD: `...`
  - SDD: `...`
  - BDD: `...`
  - TDD: `...`
  - ADR: `...`
  - SSOT: `...`
- Machine index:
  - graph ids: `kg_...`
  - generated index key: `implementationIndex.records["..."]`
```

Rules:

1. Keep the Markdown section short enough to read during normal work.
2. Put detailed node/edge facts in `knowledge/graph.jsonl`, not duplicated prose.
3. Treat generated index data as a cache. If Markdown/graph and generated index disagree, inspect source and update the graph or mark the index stale.
4. Do not invent symbols. Use file reads, LSP/outline, TypeScript AST, or equivalent verified source inspection.
5. For user-confirmed project role or ownership facts, map the boundary explicitly even when there is no single implementing function.

## 4. Graph predicates and links

Implementation graph records may use these predicates:

| Predicate | Subject | Object |
|---|---|---|
| `implemented_by` | record/domain/contract/scenario/test/decision/ssot id | file path or symbol id |
| `defines_symbol` | file path | symbol descriptor |
| `calls` | symbol id | symbol id |
| `protected_by` | record or symbol id | test path or test symbol id |
| `configured_by` | implementation or behavior id | config/env/schema path |
| `generates` | source path or tool id | generated path |
| `indexed_by` | record id | generated index key |

Implementation graph records should use `kind` values such as `implementation`, `file`, `symbol`, or `generated-index`.

Recommended link rel values:

- `implemented_by`
- `defines_symbol`
- `calls`
- `protected_by`
- `configured_by`
- `generates`
- `indexed_by`
- plus existing cross-layer rels such as `specified_by`, `validated_by`, `decided_by`, and `source_of_truth_for`

## 5. Generated index contract

`generated/implementation-index.json` is optimized for AI/LSP retrieval and may be rebuilt.

Minimum shape:

```json
{
  "schemaVersion": "1.0",
  "generatedAt": "2026-05-13T00:00:00.000Z",
  "source": {
    "root": ".",
    "commit": "optional-git-sha",
    "method": "lsp|ast|outline|manual|mixed"
  },
  "records": {
    "record-id-or-path": {
      "recordPath": ".lazy-harness/domain/example.md",
      "layer": "ddd",
      "files": [
        {
          "path": "src/example.ts",
          "role": "primary implementation",
          "symbols": [
            {
              "name": "example",
              "kind": "function",
              "range": { "startLine": 10, "endLine": 40 },
              "signature": "example(input: Input): Output"
            }
          ]
        }
      ],
      "tests": ["src/example.test.ts"],
      "graphIds": ["kg_example_implemented_by_src_example"]
    }
  }
}
```

## 6. Update behavior

When implementation changes:

1. Search/read relevant records first.
2. Update the human `Implementation map` section if file/symbol/flow meaning changed.
3. Append or supersede graph records in `knowledge/graph.jsonl` after confirmation or validated safe rule.
4. Regenerate `generated/implementation-index.json` when tooling exists. Until then, mark generated index as missing/stale instead of inventing data.
5. If the layer for a fact is ambiguous, ask the user using the standard option gate before writing canonical records.

## 7. TDD / regression layer completeness

When adding or updating TDD/regression records, do not stop at the protection case. Apply `.lazy-harness/spec/platform/layer-completeness-gate.md`:

1. check whether SDD, BDD, SSOT, or DDD records are impacted,
2. update impacted primary records and cross-link them,
3. or add a local `Layer completeness` judgement that explicitly mentions SDD, BDD, SSOT, and DDD.

The `Implementation map` should then link to the affected cross-layer records and protection tests.
