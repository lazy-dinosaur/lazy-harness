# generated

Derived artifacts for AI/tool retrieval. Read-only outputs.

## Files

| File | Purpose | Canonical? |
|---|---|---|
| `reference-index.json` | Derived reference resolver index/cache. | No |
| `implementation-index.json` | Derived implementation map index for AI/LSP/AST/outline retrieval. | No |

## Trigger to fill

- XML/source records updated → regenerate derived reference artifacts.
- LSP/AST/outline/source scan available → regenerate `implementation-index.json`.

## Implementation index policy

`implementation-index.json` is a cache, not source of truth.

Canonical implementation knowledge lives in:

1. Markdown `Implementation map` sections in DDD/SDD/BDD/TDD/ADR/SSOT records.
2. Confirmed implementation graph records in `.lazy-harness/knowledge/graph.jsonl`.

If the generated index disagrees with Markdown or graph records, inspect source and then update/supersede canonical records or regenerate the index.

## Status

- Empty/missing generated files are valid (Principle #10 Empty-Container Tolerance).
- Will be filled when triggers/indexers fire (Principle #6 Trigger-Based Growth).
- Auto-audited on update (Principle #1.2 Drafting and Auditing).
