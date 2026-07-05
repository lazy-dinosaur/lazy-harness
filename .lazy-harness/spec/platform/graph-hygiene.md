# SDD — Graph Hygiene CLI

Status: accepted
Date: 2026-05-21
Layer: SDD
Related: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`, `.lazy-harness/ssot/implementation-map-storage.md`, `.lazy-harness/spec/platform/record-audit.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 그래프 위생
  - graph hygiene
  - graph lint
  - 그래프 검사
- Applies when:
  - linting `knowledge/graph.jsonl` for id/path hygiene, or before relying on graph paths for navigation
- Must:
  - stay read-only and report issues (invalid rows, missing/duplicate id, comma-joined paths, missing/source-only paths)
  - apply the supersession-aware duplicate-id policy (2026-07-05): group rows by `id`; a group with ≤1 active (non-`superseded`) row plus `status:superseded` history is a legitimate trail counted as `supersededTrails` (NOT an error); only 2+ ACTIVE rows sharing an `id` raise `duplicate-id`
  - apply the retired-id-group skip (2026-07-05, user-confirmed Option A from a downstream-host detector-conflict decision): an id-group containing any `status:superseded` row is retired settled history — skip its rows for missing-path/comma-joined warnings AND for legacy/removed-framework migration proposals (a row that is itself `superseded` is also skipped). ACTIVE rows are still flagged. This is read-only and leaves host graphs untouched: hosts get clean counts via `lazy update` to the framework detector, NOT by bulk-appending supersede rows to their own graph
  - support `--fail-on-issues` (exit 2) and classify source-only vs actionable host-missing paths
  - support `--migration-plan` (2026-07-05, user-approved): read-only detection only — SURFACE candidates (legacy-shape rows, references to ADR-0050-removed framework files) and report record-BODY jcode mentions (DETECTION-ONLY, fixed via `lazy-record-quality`). Proposals are LLM-VERDICT candidates, not directives: the subject/predicate/object mapping is a HINT to verify, and the per-row verdict (KEEP / CONVERT-if-fact-holds / SUPERSEDE-by-real-reason — never by age/shape) is decided by the `lazy-graph-migrate` guided skill against source, batch + user approval, append+supersede. Proposals never count toward `--fail-on-issues`
- Must not:
  - repair, delete, rewrite, supersede, or promote graph rows
- Record completion:
  - check or output changes update this SDD and the graph-hygiene self-test
- Related records:
  - `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
  - `.lazy-harness/ssot/implementation-map-storage.md`
  - `.lazy-harness/spec/platform/record-audit.md`
  - `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`

## Contract

`graph-hygiene` is a read-only lint command for `.lazy-harness/knowledge/graph.jsonl`.

It exists because downstream host dogfooding showed that the graph grows usefully, but path hygiene issues can make future agents follow stale or non-host paths.

The command reports issues and may optionally exit non-zero with `--fail-on-issues`, but it must not repair, delete, rewrite, or supersede graph rows.

## CLI

```bash
  bun .lazy-harness/scripts/graph-hygiene.ts --format=json --root <host> --source <lazy-harness-source>
.lazy-harness/bin/lazy graph-hygiene --format=md
.lazy-harness/bin/lazy graph-hygiene --fail-on-issues
.lazy-harness/bin/lazy graph-hygiene --migration-plan --format=md
```

Options:

- `--root` / `--host`: host root. Defaults to `LAZY_HOST_ROOT` or current working directory.
- `--source`: canonical lazy-harness source checkout or its `.lazy-harness` directory. When present, paths absent from the host but present in source are counted as `sourceOnlyPaths` instead of actionable `missingPaths`.
- `--graph`: explicit graph JSONL path.
- `--format md|json`: output format.
- `--fail-on-issues`: exit `2` when any issue is found. Default is report-only.
- `--migration-plan`: append a read-only `migrationPlan` section (JSON) / `## Migration plan` section (md) proposing legacy-schema-row normalization, removed-framework-ref supersede notes, and `recordJcodeMentions` (detection-only count of record BODIES mentioning jcode, for `lazy-record-quality` human judgment). Still read-only: the CLI never repairs/rewrites/supersedes rows or edits record bodies; the REMOVED_FRAMEWORK_FILES list mirrors `lazy-sync.ts` KNOWN_REMOVED_MANAGED_FILES (co-change both together). Summary also carries `supersededTrails` (legitimate 1-active+superseded id groups).

## Checks

The command detects:

- invalid JSONL rows
- rows missing a string `id`
- duplicate `id` values
- comma-joined path strings in `path`, `file`, `sourcePath`, `targetPath`, evidence paths, or graph link targets
- host-relative paths that do not exist in either host or source
- source-only paths that exist in framework source but are not installed into the host

## Non-goals

- Not graph repair.
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

## Discovery capture

- DDD: none.
- SDD: this accepted contract defines graph hygiene lint behavior.
- BDD: none.
- TDD: protected by self-test fixture.
- ADR: none; follows ADR 0028 graph invariants and ADR 0030 implementation map storage.
- SSOT: reinforces `.lazy-harness/ssot/implementation-map-storage.md` path ownership.
- Planning: promoted from downstream dogfood record-audit graph hygiene candidate.
