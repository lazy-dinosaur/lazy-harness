# generated

Derived artifacts for AI/tool retrieval. Read-only outputs.

## Files

| File | Purpose | Canonical? |
|---|---|---|
| `reference-index.json` | Derived reference resolver index/cache. | No |
| `implementation-index.json` | Derived implementation map index for AI/LSP/AST/outline retrieval. | No |
| `record-index.json` | Derived record/source hint cache combining record digests, aliases/surface terms, implementation hints, graph hints, and Project Profile feature navigation. | No |

## Trigger to fill

- XML/source records updated → regenerate derived reference artifacts.
- LSP/AST/outline/source scan available → regenerate `implementation-index.json`.
- Rule digests, Project Profile `feature-navigation.xml`, implementation maps, or graph records updated → regenerate `record-index.json`.

## Implementation index policy

`implementation-index.json` is a cache, not source of truth.

Canonical implementation knowledge lives in:

1. Markdown `Implementation map` sections in DDD/SDD/BDD/TDD/ADR/SSOT records.
2. Confirmed implementation graph records in `.lazy-harness/knowledge/graph.jsonl`.

If the generated index disagrees with Markdown or graph records, inspect source and then update/supersede canonical records or regenerate the index.


## Record index policy

`record-index.json` is a deterministic cache for record/source retrieval, not source of truth.

Canonical record/source retrieval knowledge lives in:

1. Markdown `## Rule digest` sections and `Implementation map` sections.
2. `.lazy-harness/project/feature-navigation.xml` in each host.
3. Confirmed graph rows in `.lazy-harness/knowledge/graph.jsonl`.
4. Source files and tests referenced by canonical records.

Regenerate with:

```bash
.lazy-harness/bin/lazy record-index --write --format=md
```

The generated file may be absent. Runtime query must fall back to source scanning when the cache is missing or stale. The source repository ignores `.lazy-harness/generated/record-index.json` by default to keep commits focused on canonical records and generator code.

## Status

- Empty/missing generated files are valid (Principle #10 Empty-Container Tolerance).
- Will be filled when triggers/indexers fire (Principle #6 Trigger-Based Growth).
- Auto-audited on update (Principle #1.2 Drafting and Auditing).
