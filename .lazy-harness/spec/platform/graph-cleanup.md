# SDD — Graph Cleanup CLI

Status: draft
Layer: SDD
Date: 2026-06-18
Related: `.lazy-harness/spec/platform/graph-hygiene.md`, `.lazy-harness/spec/platform/record-audit.md`

## Contract

`graph-cleanup` is a conservative companion to read-only `graph-hygiene`.

It exists because installed dogfood hosts can preserve old host/source graph rows that later block Phase 3 readiness with duplicate ids, missing ids, or stale `.lazy-harness/**` paths that exist in neither the host nor the canonical framework source.

## CLI

```bash
.lazy-harness/bin/lazy graph-cleanup --format=json
.lazy-harness/bin/lazy graph-cleanup --root /path/to/host --source /path/to/lazy-harness --format=json
.lazy-harness/bin/lazy graph-cleanup --apply --format=json
```

Options:

- `--root` / `--host`: host root. Defaults to `LAZY_HOST_ROOT` or current working directory.
- `--source`: canonical lazy-harness source checkout or its `.lazy-harness` directory.
- `--graph`: explicit graph JSONL path.
- `--format md|json`: output format.
- `--apply`: rewrite graph JSONL. Without this flag the command is dry-run only.

## Safety rules

1. Default mode is dry-run.
2. Apply mode must write a timestamped backup beside the graph before rewriting.
3. The command must preserve rows. It must not silently delete host graph knowledge.
4. Missing id rows get deterministic `kg_auto_<hash>` ids.
5. Duplicate id rows keep the first id and rename later duplicates to `<id>__dup_<line>_<hash>` with `duplicateOf` metadata.
6. Direct stale path references that exist in neither host nor canonical source are moved into `stalePaths` with field/path/reason metadata.
7. Source-only paths that exist in canonical source are not rewritten.
8. Invalid JSON rows are unsupported and make `ok=false`; the command does not guess repairs for invalid JSON.

## Non-goals

- Not replacement for `graph-hygiene`.
- Not candidate promotion.
- Not semantic graph merging.
- Not automatic host mutation by lifecycle hooks.

## Implementation map

- Primary files:
  - `.lazy-harness/spec/platform/graph-cleanup.md` — this contract.
  - `.lazy-harness/tests/graph-cleanup.md` — regression fixtures.
  - `.lazy-harness/scripts/graph-cleanup.py` — dry-run/apply planner.
  - `.lazy-harness/bin/lazy` — exposes `lazy graph-cleanup`.
  - `.lazy-harness/scripts/self-test.py` — temp-graph coverage.
- Key symbols:
  - `graph-cleanup.py#cleanup`
  - `graph-cleanup.py#repair_stale_paths`
  - `graph-cleanup.py#stale_paths_for_value`
  - `self-test.py#check_graph_cleanup_cli`
- Flow:
  1. Run graph-hygiene to identify issues.
  2. Run graph-cleanup dry-run to produce conservative operations.
  3. Inspect operations.
  4. If explicitly approved, run `--apply`; backup path is returned.
  5. Re-run graph-hygiene.
- Tests:
  - `python3 -m py_compile .lazy-harness/scripts/graph-cleanup.py`
  - temp graph dry-run/apply fixture in self-test
  - `lazy graph-cleanup` dispatcher fixture

## Discovery capture

- SDD: this record defines the new conservative cleanup CLI.
- TDD: `.lazy-harness/tests/graph-cleanup.md` protects dry-run/apply behavior.
- BDD: host readiness flow becomes inspect → dry-run → approved apply → graph-hygiene recheck.
- SSOT: graph storage remains `.lazy-harness/knowledge/graph.jsonl`; backups live beside the graph.
- ADR: none; follows existing graph-hygiene read-only boundary by using a separate explicit cleanup command.
- DDD: none.
