# TDD — Graph Cleanup CLI

Status: draft
Layer: TDD
Date: 2026-06-18

## Regression target

`lazy graph-cleanup` must provide a conservative, inspectable way to clean graph hygiene blockers without making `graph-hygiene` mutating and without silently deleting host graph knowledge.

## Protected fixtures

| Case | Trigger | Expected |
|---|---|---|
| `cleanup_dry_run` | temp graph with missing id, duplicate id, stale path, source-only path | Reports operations but does not mutate file. |
| `cleanup_apply_backup` | same temp graph with `--apply` | Writes a backup beside the graph, preserves row count, adds deterministic id, renames duplicate id, and moves stale path to `stalePaths`. |
| `cleanup_source_only_preserved` | path missing in host but present in canonical source | No stale-path operation for that path; graph-hygiene later reports it as source-only rather than missing. |
| `cleanup_graph_hygiene_after_apply` | run graph-hygiene after apply | Missing id, duplicate id, and missing path issues introduced by the fixture are gone. |
| `cleanup_invalid_json_unsupported` | invalid JSON row | Returns `ok=false`, lists unsupported invalid row, does not guess a repair. |
| `cleanup_dispatcher` | `.lazy-harness/bin/lazy graph-cleanup --format=json` | Dispatcher calls the cleanup helper for the current host root. |

## Acceptance assertions

1. Default mode is dry-run.
2. Apply mode requires explicit `--apply` and creates a backup.
3. No rows are deleted in the protected fixture.
4. Missing ids become deterministic `kg_auto_*` ids.
5. Later duplicate ids are renamed and get `duplicateOf` metadata.
6. Stale paths are moved into `stalePaths` and removed from active graph path fields.
7. Source-only paths are not rewritten.
8. `graph-hygiene` remains read-only and separate.

## Implementation map

- Primary files:
  - `.lazy-harness/tests/graph-cleanup.md` — this TDD.
  - `.lazy-harness/spec/platform/graph-cleanup.md` — SDD contract.
  - `.lazy-harness/scripts/graph-cleanup.py` — implementation.
  - `.lazy-harness/bin/lazy` — dispatcher.
  - `.lazy-harness/scripts/self-test.py` — temp-graph fixture coverage.
- Key symbols:
  - `graph-cleanup.py#cleanup`
  - `graph-cleanup.py#repair_stale_paths`
  - `self-test.py#check_graph_cleanup_cli`
- Validation commands:
  - `python3 -m py_compile .lazy-harness/scripts/graph-cleanup.py`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`

## Layer completeness

- SDD: `.lazy-harness/spec/platform/graph-cleanup.md`.
- BDD: readiness flow now has an explicit dry-run/apply cleanup step.
- SSOT: graph storage remains `.lazy-harness/knowledge/graph.jsonl`.
- ADR: no new ADR; follows existing graph-hygiene read-only boundary.
- DDD: no domain/business impact.
