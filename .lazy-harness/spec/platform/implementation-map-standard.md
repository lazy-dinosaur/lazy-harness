# Implementation Map Standard

Status: accepted
Layer: SDD
Related ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
Related SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
Related graph spec: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - writing or updating a record that refers to implemented behavior, or deciding where implementation facts live
- Must:
  - add an `## Implementation map` (files, key symbols, flow, tests, ownership, cross-layer links) when implementation exists or is verifiable
  - store confirmed file/symbol/edge facts in `knowledge/graph.jsonl`; keep the generated index derived-only
  - heed advisory `lazy impl-map` status drift (planned-but-files-present, verified-but-files-missing) when reviewing map `Status`
- Must not:
  - treat the generated implementation-index as canonical, or mark `verified` without confirmable source
- Record completion:
  - standard changes update this SDD, ADR 0030, and the implementation-map storage SSOT
- Related records:
  - `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
  - `.lazy-harness/ssot/implementation-map-storage.md`
  - `.lazy-harness/spec/platform/progressive-knowledge-graph.md`

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

## 8. Implementation status drift (advisory)

`lazy impl-map` (`.lazy-harness/scripts/implementation-map-audit.ts`) also reports **advisory** status-drift candidates so a record's `## Implementation map` `Status:` does not silently diverge from reality. It is read-only and never a blocking gate (ADR 0016/0041/0048).

It parses each record's `## Implementation map` block and reports:

- `planned-status-files-present` — `Status: planned` or `none`, yet a referenced code file under `Primary files:`/`Future files:` exists (review for promotion).
- `verified-status-files-missing` — `Status: verified`, yet a referenced `Primary files:`/`Future files:` path is gone (review for demotion/fix).

To stay low-noise, detection:

1. reads only the `Primary files:` / `Future files:` subsections (Tests/validation/cross-layer noise excluded);
2. counts only clean path tokens (a slash + file extension; whitespace, `$env`, globs, `#anchors`, and `path/to/` placeholders are ignored — so command strings like `python3 …/self-test.py` never count);
3. resolves a ref against the host root with a `.lazy-harness/`-relative fallback (so shorthand like `knowledge/graph.jsonl` resolves);
4. skips records whose `## Rule digest` `Status` is `deprecated` or `reverted`.

File existence is a heuristic, not proof of completion, so the report is a review list, not a verdict. Promote/demote `Status` only after confirming source.

### Automatic surface (response.completed)

A turn-scoped advisory also runs at `response.completed` via `.lazy-harness/hooks/lifecycle/helpers/check-impl-map-status-drift.py`. When a turn writes to a `.lazy-harness/**/*.md` record or touches/removes a referenced source file, it reuses the same detector and surfaces drift **only for records this turn touched** (record path or a drifted file path appears in the turn's tool-call evidence), so unrelated accumulated drift is not re-nagged every turn. It is organic/advisory (ADR 0041/0048, guidance-ladder L3): one advisory per turn, fail-open (exit 0), no new hard gate, no user-text classification. Full-corpus review stays manual via `lazy impl-map`.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/implementation-map-standard.md` — this contract (map format, `Status` enum, advisory drift).
  - `.lazy-harness/scripts/implementation-map-audit.ts` — `lazy impl-map` audit + advisory status-drift detection.
  - `.lazy-harness/bin/lazy` — dispatches `lazy impl-map`.
  - `.lazy-harness/hooks/lifecycle/helpers/check-impl-map-status-drift.py` — response.completed turn-scoped drift advisory (reuses the audit detector).
- Key symbols:
  - `auditRecord` (`.lazy-harness/scripts/implementation-map-audit.ts`) — per-record migration status + drift computation.
  - `extractPrimaryFutureRefs` / `isCleanPath` / `refExists` (`.lazy-harness/scripts/implementation-map-audit.ts`) — low-noise ref extraction and `.lazy-harness/`-fallback resolution.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_impl_map_status_drift` — synthetic-fixture detection test; never gates on real-corpus drift.
  - `.lazy-harness/scripts/self-test.py#check_impl_map_status_drift_helper` — helper advisory fixture (silent / relevant-emit / fail-open).
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
  - SDD: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
- Machine index:
  - graph ids: `kg_impl_map_status_drift_cli_20260626`, `kg_impl_map_status_drift_self_test_20260626`, `kg_impl_map_status_drift_helper_20260626`
