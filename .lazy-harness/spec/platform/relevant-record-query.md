# SDD — Relevant Record Query

Status: accepted
Date: 2026-06-01
Layer: SDD
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related plan: `.lazy-harness/planning/record-query-context-loop-transition-plan.md`
Related spec: `.lazy-harness/spec/platform/record-digest-format.md`
Related schema: `.lazy-harness/schemas/relevant-record-index.schema.json`

## Purpose

Relevant Record Query is the framework-level mechanism that finds compact `.lazy-harness` record guidance for the current user message or planning context without binding policy to a concrete tool.

It answers:

```text
Given this user message and lightweight context,
which lazy-harness records should be in the agent's working context before answering?
```

## Non-goals

- Not a semantic-search algorithm baked into the framework.
- Not a full-document dump.
- Not a replacement for deliberate record reads when a record is selected.
- Not a tool-specific policy engine.
- Not a generated implementation/symbol index.

## Input contract

A query request should support:

```json
{
  "message": "user or coordinator message",
  "recentContext": ["optional short context strings"],
  "touchedFiles": ["optional/path.ts"],
  "preferredLayers": ["SSOT", "SDD"],
  "limit": 5,
  "tokenBudget": 600,
  "includeStatuses": ["active", "advisory", "needs-review"]
}
```

Fields:

| Field | Required | Notes |
|---|---:|---|
| `message` | yes | current user/coordinator request |
| `recentContext` | no | short strings only; no full transcript dumps |
| `touchedFiles` | no | can bias toward implementation-map related records |
| `preferredLayers` | no | canonical labels: DDD, SDD, BDD, TDD, ADR, SSOT, Planning |
| `limit` | no | default 5 |
| `tokenBudget` | no | default 600, normal ceiling 1000 |
| `includeStatuses` | no | default active/advisory/needs-review |

## Output contract

A query response should support both JSON and Markdown.

Minimal JSON shape:

```json
{
  "schemaVersion": "1.0",
  "generatedAt": "2026-06-01T00:00:00.000Z",
  "query": {
    "message": "...",
    "tokenBudget": 600
  },
  "digest": {
    "estimatedTokens": 240,
    "truncated": false,
    "entries": [
      {
        "recordPath": ".lazy-harness/ssot/project-identity.md",
        "title": "Project Identity",
        "layer": "SSOT",
        "status": "active",
        "scope": "host-project",
        "score": 0.87,
        "matchedCues": ["source of truth", "ownership"],
        "bullets": [
          "Consult this SSOT before deciding ownership or upstream boundaries.",
          "Confirmed corrections update this record or a more specific SSOT."
        ],
        "recordCompletion": "confirmed ownership/source-of-truth corrections update this SSOT"
      }
    ]
  }
}
```

Markdown rendering:

```md
Relevant lazy-harness rules
- `.lazy-harness/ssot/project-identity.md` — Project Identity
  - Consult this SSOT before deciding ownership or upstream boundaries.
  - Confirmed corrections update this record or a more specific SSOT.
```

## Matching model

The final implementation may use SearchProvider, generated index, grep fallback, or an external derived query backend, but it must preserve these framework constraints:

1. Root-bound: query only the current host `.lazy-harness` records.
2. Record-first: canonical Markdown records and graph are source of truth.
3. Digest-first: prefer `## Rule digest` sections when present.
4. Natural intent: match `Applies when` / titles / scopes / layers / record paths, not concrete tool names as primary keys.
5. Compact output: include paths and bullets, not full documents.
6. Status-aware: exclude `deprecated` and `reverted` by default.
7. Layer-aware: support DDD/SDD/BDD/TDD/ADR/SSOT/Planning filters.
8. Token-aware: truncate gracefully and include `truncated: true` when budget is exceeded.

## Ranking inputs

Recommended ranking signals:

| Signal | Purpose |
|---|---|
| digest `Applies when` matches | primary intent signal |
| digest title/path matches | strong direct cue |
| layer preferred by task | layer relevance |
| recent context/touched files | continuity signal |
| implementation-map cross-links | optional expansion |
| status | active > advisory > needs-review; deprecated/reverted excluded by default |
| recency | tie-breaker only |

Do not overfit to tool strings like `gh`, `bash`, `dev-cli`, or MCP tool names. If those appear, use them only to infer artifact/action context, not as policy ownership.

## Generated index contract

Relevant Record Query should have a generated cache separate from implementation-index:

- path: `.lazy-harness/generated/relevant-record-index.json`
- schema: `.lazy-harness/schemas/relevant-record-index.schema.json`
- canonical source: Markdown records + graph, not generated cache
- rebuild trigger: record files or graph change

The cache should store parsed digest metadata and lightweight fallback text, not full record bodies.

## SearchProvider relationship

`SearchProvider` remains the AI-first abstraction for candidate record search.

Phase 2 updates its direct fallback path model to the current canonical directories:

| Layer | Path |
|---|---|
| DDD | `.lazy-harness/domain/` |
| SDD | `.lazy-harness/spec/` |
| BDD | `.lazy-harness/behavior/` |
| TDD | `.lazy-harness/tests/` |
| ADR | `.lazy-harness/decisions/` |
| SSOT | `.lazy-harness/ssot/` |
| Planning | `.lazy-harness/planning/` |

Relevant Record Query may use SearchProvider for candidate narrowing, but it must add digest parsing, status filtering, token budgeting, and output rendering.

## Fallback behavior

When no `## Rule digest` exists:

1. Use path, title heading, status, first paragraph, and obvious rule words as a fallback candidate.
2. Keep fallback bullets conservative.
3. Prefer surfacing the path and recommending deliberate read rather than inventing a rule.
4. Mark the result as `digestSource: fallback`.

## Query examples

### Source-of-truth correction

Input:

```json
{ "message": "아니 medivance-pwa도 dogfood host야" }
```

Expected retrieval classes:

- project identity / dogfood host SSOT,
- project rule router,
- record write/update policy.

### API/component work

Input:

```json
{ "message": "이 컴포넌트 contract 바꾸자" }
```

Expected retrieval classes:

- relevant SDD records,
- implementation-map related records,
- record write/update policy for contract changes.

### Bug/regression work

Input:

```json
{ "message": "이 버그 고치고 회귀 안 나게 해줘" }
```

Expected retrieval classes:

- TDD/regression records,
- layer completeness gate,
- affected SDD/BDD/SSOT/DDD records if indexed.

### Release/deploy workflow

Input:

```json
{ "message": "릴리즈 준비해줘" }
```

Expected retrieval classes:

- release workflow records,
- validation/commit convention records,
- source-of-truth deployment policy records.

## Validation requirements

A future implementation must test:

1. current canonical layer directories are searched,
2. old `.lazy-harness/ddd|sdd|bdd|tdd` paths are not required,
3. digest status filtering excludes reverted/deprecated by default,
4. token budget truncates output under the requested ceiling,
5. queries for source-of-truth, contract, behavior, regression, release, runtime, and PR examples retrieve without tool-specific keys,
6. fallback entries do not invent bullets beyond record evidence.

## Implementation map

- Status: `planned`
- Primary files:
  - `.lazy-harness/spec/platform/relevant-record-query.md` — this SDD contract.
  - `.lazy-harness/schemas/relevant-record-index.schema.json` — generated cache schema.
  - `.lazy-harness/scripts/search-provider.ts` — direct fallback candidate search path model.
  - `.lazy-harness/spec/platform/record-digest-format.md` — digest source contract.
  - `.lazy-harness/spec/platform/record-write-update-policy.md` — record maintenance companion.
  - `.lazy-harness/planning/record-query-context-loop-transition-plan.md` — phase plan.
- Future files:
  - `.lazy-harness/scripts/relevant-record-query.ts`
  - `.lazy-harness/generated/relevant-record-index.json`
- Flow:
  1. Build/load relevant-record index from canonical records.
  2. Query by message/context/layer budget.
  3. Rank and render compact digest entries.
  4. Provide digest to pre-response context surface.
- Tests / protection:
  - Phase 2 self-test should protect SearchProvider canonical paths.
  - Future query CLI fixtures protect ranking/token output.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - SDD: `.lazy-harness/spec/platform/record-digest-format.md`
  - Planning: `.lazy-harness/planning/record-query-context-loop-transition-plan.md`

## Rule placement

- Rule: relevant record lookup must query canonical records by natural intent/context, render compact digest output, use a generated relevant-record index/cache, and avoid tool-specific project policy keys.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/relevant-record-query.md`
- Why not AGENTS.md: this is a platform contract for query/index behavior, not short operational grammar.
- Why not `.jcode`: query behavior is shared lazy-harness framework design, not local/private Jcode-only workflow.
- Confirmation: user-confirmed direction via ADR 0041 and transition plan.

## Discovery capture

- DDD: none.
- SDD: updated, this contract defines relevant-record query behavior.
- BDD: candidate, future behavior should surface compact rules before agent responses.
- TDD: future fixtures needed for query output, token budget, and no-tool-key retrieval.
- ADR: ADR 0041 selected organic hybrid guidance.
- SSOT: harness enforcement policy anchors mandatory record vs organic guidance split.
- Planning: record-query context loop transition plan Phase 2.
