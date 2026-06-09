# Graph Path Implementation Plan

Status: implemented-slice-1
Date: 2026-06-08
Layer: Planning
Related SDD: `.lazy-harness/spec/platform/graph-path.md`
Related TDD: `.lazy-harness/tests/graph-path.md`
Related SDD: `.lazy-harness/spec/platform/graph-query.md`
Related Planning: `.lazy-harness/planning/graph-query-prototype-implementation-plan.md`
Related Planning: `.lazy-harness/planning/graph-index-migration-considerations.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## Rule digest

- Status: completed
- Layer: Planning
- Scope: framework-global
- Applies when:
  - implementing the first `lazy graph path` slice after graph-query slice 1
  - planning exact source/test/documentation updates for bounded path navigation
- Must:
  - keep the implementation additive, read-only, cue-only, deterministic, TS/Bun based
  - write/update SDD and TDD before source changes
  - reuse existing graph-query candidate construction where possible
  - leave graph explain behavior to its separate SDD/TDD/plan slice
  - validate with focused graph-path commands and full framework self-test
  - sync downstream hosts after committing framework changes
- Must not:
  - change lifecycle policy, overview hard block, prompt reminders, option gate rules, or read-debt semantics
  - implement Graphify MCP/daemon/watch/export/wiki behavior
  - vendor Graphify/Python or introduce another runtime
  - add semantic authority fields or next-action recommendations
- Record completion:
  - completion updates SDD/TDD implementation maps, graph rows, manifest entries, and sync evidence.

## Direction lock

This slice implements only:

> `lazy graph path <from> <to>` as a read-only bounded path navigation helper over existing graph-query outputs.

Explicitly out of scope:

- graph explain changes outside its separate SDD/TDD/plan slice
- MCP/daemon/watch
- graph artifact export/wiki/report
- prompt packet injection
- lifecycle hard-block relaxation
- static intent/risk/read classifiers

## Implementation steps

### Phase 0 — Contract first

- Create `.lazy-harness/spec/platform/graph-path.md`.
- Create `.lazy-harness/tests/graph-path.md`.
- Link both records to graph-query SDD, CLI boundary SSOT, and this plan.

### Phase 1 — Source implementation

Patch `.lazy-harness/scripts/graph-query.ts`:

1. Extend args to parse command-specific path flags:
   - command: `query | path`
   - `--max-depth`
   - `--max-paths`
2. Keep graph explain changes out of the graph path patch.
3. Add `GraphPathResult` type with no forbidden semantic fields.
4. Export/refactor internal graph query builder enough for path reuse inside the same file.
5. Implement `buildGraphPath(root, from, to, limit, maxDepth, maxPaths, fresh)`:
   - call `buildGraphQuery` for `from` and `to`
   - merge nodes/edges from both results
   - choose endpoint candidates by exact path match first, then endpoint candidate order
   - run deterministic undirected BFS over compact node ids
   - return `linked`, `partial`, or `gap`
6. Add Markdown renderer.
7. Ensure JSON/Markdown output remains compact and warning-heavy.

Patch `.lazy-harness/bin/lazy` help to advertise path command.

### Phase 2 — Regression tests

Patch `.lazy-harness/scripts/self-test.py`:

- Add `check_graph_path_cli()` near `check_graph_query_cli()`.
- Verify SDD/TDD existence and key phrases.
- Verify help text includes graph path.
- Verify linked fixture and gap fixture.
- Verify no forbidden fields recursively.
- Verify read-only behavior for graph JSONL and record-index cache.
- Verify graph path behavior remains unchanged by any separate graph-explain slice.
- Add the function to the framework check list.

### Phase 3 — Knowledge graph and sync metadata

- Append confirmed graph rows for SDD/TDD/source/test implementation edges.
- Update `.lazy-harness/manifests/init-categories.json` if new records need Category A sync inclusion.
- Update graph-query SDD/TDD wording so path is no longer listed as slice-1 unsupported; graph explain wording is owned by the separate graph-explain records.

### Phase 4 — Validation

Focused:

```bash
.lazy-harness/bin/lazy graph path 'workflow compression not safety reduction' '.lazy-harness/ssot/cli-tool-boundary.md' --format=json --limit=8 --max-depth=4
.lazy-harness/bin/lazy graph path 'zzzz-missing-from' 'zzzz-missing-to' --format=json --limit=8
python3 -m py_compile .lazy-harness/scripts/self-test.py
```

Full:

```bash
python3 .lazy-harness/scripts/self-test.py --scope framework
```

### Phase 5 — Commit and downstream sync

- Commit framework changes in this repo.
- Run lazy-sync verification / downstream sync to active hosts.
- Commit/summarize downstream sync if applicable.

Status: source implementation, focused graph-query/path checks, full framework self-test, commit hook lazy test, and 15/15 downstream host sync/smoke validation passed. Evidence: `.lazy-harness/evidence/2026-06-08-graph-path-downstream-sync.md`.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Path output is over-read as semantic proof | Notes, SDD/TDD, forbidden fields, self-test guard |
| BFS output grows too large | `--limit`, `--max-depth`, `--max-paths`, compact ids |
| Existing graph-query compactness regresses | keep existing self-test compactness checks passing |
| Path-backed or semantic explain overreaches through graph path | graph-explain tests keep path-backed support structural/cue-only and forbid semantic authority fields |
| Path cannot find useful connection | return endpoint candidates and fallback, not conclusions |

## Implementation map

- Status: implemented-slice-1
- Primary files:
  - `.lazy-harness/planning/graph-path-implementation-plan.md` — this plan.
  - `.lazy-harness/spec/platform/graph-path.md` — SDD contract.
  - `.lazy-harness/tests/graph-path.md` — TDD contract.
  - `.lazy-harness/scripts/graph-query.ts` — implements parser, `GraphPathResult`, bounded BFS path search, JSON output, and Markdown rendering.
  - `.lazy-harness/bin/lazy` — advertises graph path.
  - `.lazy-harness/scripts/self-test.py` — protects graph path linked/gap/read-only/no-semantic-field fixtures and keeps graph-explain Phase 1 tests separate.
  - `.lazy-harness/knowledge/graph.jsonl` — implementation map edges for graph path SDD/TDD/source/test.
- Symbols:
  - `GraphPathResult`
  - `parseArgs`
  - `buildGraphPath`
  - `findBoundedPaths`
  - `renderPathMarkdown`
  - `check_graph_path_cli`
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
- Machine index:
  - graph id: `kg_graph_path_cli_20260608`

## Discovery capture

- Captured Graphify-style path as an additive next slice in SDD/TDD/Planning instead of chat-only backlog.
- No ADR opened because this is a CLI helper implementation, not a lifecycle/policy authority change.
- Current graph-explain path-backed support is owned by the separate graph-explain SDD/TDD/plan; semantic summarization still requires an option gate/ADR.
