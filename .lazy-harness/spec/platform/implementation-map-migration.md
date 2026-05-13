# Implementation Map Migration Guide

Status: accepted
Layer: SDD
Related standard: `.lazy-harness/spec/platform/implementation-map-standard.md`
Related ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
Related SSOT: `.lazy-harness/ssot/implementation-map-storage.md`

## 1. Goal

Migrate existing host records to ADR 0030 without overwriting host institutional memory.

The migration is incremental. Existing DDD/SDD/BDD/TDD/ADR/SSOT Markdown files remain valid, but records that describe implemented behavior should gain an `Implementation map` section and, when verified, corresponding `knowledge/graph.jsonl` implementation facts.

## 2. Non-destructive migration rule

Do not bulk rewrite host records blindly.

Migration must be one of:

1. **Touch-on-change**: when a record is naturally updated during work, add or refresh `Implementation map`.
2. **Focused audit**: when a feature/domain is actively being investigated, migrate only directly related records.
3. **Explicit migration pass**: user asks to migrate all or a selected layer, then run an audit and apply reviewed edits.

## 3. Audit checklist

For each host record under:

```text
.lazy-harness/domain/**/*.md
.lazy-harness/spec/**/*.md
.lazy-harness/behavior/**/*.md
.lazy-harness/tests/**/*.md
.lazy-harness/decisions/**/*.md
.lazy-harness/ssot/**/*.md
```

Classify:

| Case | Action |
|---|---|
| Record has no implementation relevance | Add nothing, optionally mark `Implementation map` as `Status: none` only if useful |
| Record references code/files/functions but lacks `Implementation map` | Add `Implementation map` with `Status: needs-review` or `verified` |
| Record has implementation info in prose | Normalize into `Implementation map` and preserve important context |
| Record implementation contradicts source | Mark `Status: needs-review`; create graph conflict candidate instead of overwriting |
| Source cannot be verified quickly | Mark `Status: planned` or `needs-review`; do not invent symbols |

## 4. Migration steps

### Step 1 — find candidate records

```bash
find .lazy-harness/domain .lazy-harness/spec .lazy-harness/behavior .lazy-harness/tests .lazy-harness/decisions .lazy-harness/ssot \
  -type f -name '*.md' \
  ! -path '*/README.md' \
  -print
```

### Step 2 — prioritize records likely to need maps

Search for implementation hints:

```bash
grep -RIlE 'src/|app/|components/|lib/|server/|api/|function|class|component|test|spec|schema|prisma|supabase|route|handler' \
  .lazy-harness/domain .lazy-harness/spec .lazy-harness/behavior .lazy-harness/tests .lazy-harness/decisions .lazy-harness/ssot
```

### Step 3 — inspect source with verified methods

Acceptable evidence:

- direct file read
- LSP symbols/outline
- AST parser output
- test runner output
- explicit user confirmation

Do not use loose regex-only function lists as canonical truth.

### Step 4 — add Markdown section

Use this minimal migration block:

```md
## Implementation map

- Status: `needs-review`
- Primary files:
  - `path/to/file` — role
- Key symbols:
  - `SymbolName` (`path/to/file`) — role
- Flow:
  1. Entry/trigger
  2. Core implementation
  3. Output/side effect
- Tests / protection:
  - `path/to/test` — protection
- Cross-layer links:
  - SDD: `...`
  - TDD: `...`
- Machine index:
  - graph ids: `pending`
  - generated index key: `pending`
```

Set `Status: verified` only when file/symbol evidence has been checked.

### Step 5 — add graph facts when verified

Append confirmed graph records only after user confirmation or a validated safe rule.

Example JSONL records:

```jsonl
{"id":"kg_record_example_implemented_by_file","createdAt":"2026-05-13T00:00:00.000Z","updatedAt":"2026-05-13T00:00:00.000Z","layer":"sdd","kind":"implementation","subject":"record:sdd.example","predicate":"implemented_by","object":"src/example.ts","status":"confirmed","confidence":"code-evidence","evidence":[{"type":"code","path":"src/example.ts","lines":[1,80]}],"links":[{"rel":"indexed_by","target":"generated.implementation-index.records.sdd.example"}],"provenance":{"source":"migration"}}
{"id":"kg_file_example_defines_symbol","createdAt":"2026-05-13T00:00:00.000Z","updatedAt":"2026-05-13T00:00:00.000Z","layer":"sdd","kind":"symbol","subject":"src/example.ts","predicate":"defines_symbol","object":{"name":"example","kind":"function","range":{"startLine":10,"endLine":40}},"status":"confirmed","confidence":"code-evidence","evidence":[{"type":"code","path":"src/example.ts","lines":[10,40]}],"links":[],"provenance":{"source":"migration"}}
```

### Step 6 — regenerate generated index when tooling exists

If there is no indexer yet, leave `generated/implementation-index.json` absent or stale. Do not hand-author generated cache as canonical truth.

## 5. Host sync behavior

`lazy-sync` distributes the standard/spec/schema, but must not overwrite host-specific record contents.

Expected rollout:

1. Source framework updates AGENTS/spec/SSOT/schema docs.
2. Host runs `lazy-sync --from ~/dev/lazy-harness --target <host> --force`.
3. Host records remain intact.
4. Future edits/migration passes add `Implementation map` sections incrementally.

## 6. Automation levels

Automation is allowed, but it must be staged by risk.

| Level | Command / behavior | Writes files? | Safe default? |
|---|---|---:|---:|
| Audit | `lazy impl-map --format=markdown` | No | Yes |
| Machine report | `lazy impl-map --format=json` | No | Yes |
| Jcode prompt | `lazy impl-map --format=jcode-prompt` | No | Yes |
| Jcode-assisted migration | Start Jcode with the generated prompt and let it inspect source + edit records | Yes | Requires user/session intent |
| Fully automatic apply | Script edits records and graph without review | Yes | No |

Recommended workflow:

```bash
.lazy-harness/bin/lazy impl-map --format=markdown
.lazy-harness/bin/lazy impl-map --format=jcode-prompt > /tmp/implementation-map-migration.prompt.txt
```

Then run Jcode with that prompt in the host root. The agent must still follow ADR 0030:

- inspect source before naming symbols,
- avoid loose regex-only symbol truth,
- add graph facts only when evidence is clear,
- preserve existing host records,
- ask if the layer/meaning is ambiguous.

## 7. Migration done criteria

A migrated area is done when:

- relevant records have `Implementation map` sections,
- file/symbol names are verified,
- graph facts exist for verified implementation relationships or are explicitly marked pending,
- stale/generated index status is clear,
- tests/protection are linked where they exist.
