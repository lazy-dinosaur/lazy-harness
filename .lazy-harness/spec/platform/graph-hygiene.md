# SDD — Graph Hygiene CLI

Status: accepted
Date: 2026-05-21
Layer: SDD
Related: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`, `.lazy-harness/ssot/implementation-map-storage.md`, `.lazy-harness/spec/platform/record-audit.md`

## Contract

`graph-hygiene` is a read-only lint command for `.lazy-harness/knowledge/graph.jsonl`.

It exists because downstream host dogfooding showed that the graph grows usefully, but path hygiene issues can make future agents follow stale or non-host paths.

The command reports issues and may optionally exit non-zero with `--fail-on-issues`, but it must not repair, delete, rewrite, or supersede graph rows.

## CLI

```bash
  bun .lazy-harness/scripts/graph-hygiene.ts --format=json --root <host> --source <lazy-harness-source>
.lazy-harness/bin/lazy graph-hygiene --format=md
.lazy-harness/bin/lazy graph-hygiene --fail-on-issues
```

Options:

- `--root` / `--host`: host root. Defaults to `LAZY_HOST_ROOT` or current working directory.
- `--source`: canonical lazy-harness source checkout or its `.lazy-harness` directory. When present, paths absent from the host but present in source are counted as `sourceOnlyPaths` instead of actionable `missingPaths`.
- `--graph`: explicit graph JSONL path.
- `--format md|json`: output format.
- `--fail-on-issues`: exit `2` when any issue is found. Default is report-only.

## Checks

The command detects:

- invalid JSONL rows
- rows missing a string `id`
- duplicate `id` values
- comma-joined path strings in `path`, `file`, `sourcePath`, `targetPath`, evidence paths, or graph link targets
- host-relative paths that do not exist in either host or source
- source-only paths that exist in framework source but are not installed into the host

## Non-goals

- Not graph repair. Use explicit `.lazy-harness/bin/lazy graph-cleanup` for dry-run/apply cleanup planning.
- Not candidate promotion.
- Not source-vs-host ownership repair. It only classifies source-only paths to avoid false actionable host-missing warnings.
- Not a replacement for `record-audit`; `record-audit` gives a dashboard, `graph-hygiene` gives issue details.

## Implementation map

- `.lazy-harness/scripts/graph-hygiene.ts`
  - Implements the read-only graph lint CLI and JSON/Markdown output.
  - Classifies source-only framework paths separately from actionable host missing paths when `--source` or a default source checkout is available.
- `.lazy-harness/bin/lazy`
  - Exposes `lazy graph-hygiene`.
- `.lazy-harness/scripts/self-test.py`
  - `check_graph_hygiene_cli` covers invalid JSON, duplicate/missing IDs, comma-joined paths, missing paths, source-only paths, dispatcher pass-through, and `--fail-on-issues` exit code.
- `.lazy-harness/spec/platform/record-audit.md`
  - Related dashboard that summarizes graph hygiene counts.
- `.lazy-harness/knowledge/graph.jsonl`
  - Stores confirmed implementation/test edges for this CLI.
- `.lazy-harness/spec/platform/graph-cleanup.md`
  - Companion SDD for conservative cleanup planning when graph-hygiene exposes duplicate-id, missing-id, or stale path blockers.

## Discovery capture

- DDD: none.
- SDD: this accepted contract defines graph hygiene lint behavior.
- BDD: none.
- TDD: protected by self-test fixture.
- ADR: none; follows ADR 0028 graph invariants and ADR 0030 implementation map storage.
- SSOT: reinforces `.lazy-harness/ssot/implementation-map-storage.md` path ownership.
- Planning: promoted from downstream dogfood record-audit graph hygiene candidate.
