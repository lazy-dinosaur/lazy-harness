# Purpose-Scoped Retrieval

Status: accepted
Layer: SDD
Date: 2026-06-10
Related ADR: `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`
Related DDD: `.lazy-harness/domain/purpose-scoped-retrieval.md`
Related BDD: `.lazy-harness/behavior/purpose-scoped-retrieval.md`
Related TDD: `.lazy-harness/tests/purpose-scoped-retrieval.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - adding or changing `lazy find`
  - changing purpose retrieval taxonomy
  - changing search/read debt evidence semantics later
- Must:
  - require explicit `--purpose`
  - keep output cue-only
  - avoid raw prompt classifiers and `lazy route` semantics
  - separate fact, rulebook, test, capability, source, architecture, and full retrieval spaces
- Must not:
  - decide risk, required reads, gates, or next actions
  - mark candidates as proof that files were read
  - classify raw user text from lifecycle hooks
- Record completion:
  - CLI changes update ADR/DDD/BDD/TDD/SSOT and self-test fixtures.

## CLI contract

```bash
lazy find --purpose <fact|record|rulebook|test|capability|source|architecture|full> <query> [--format=json|md] [--limit=N]
```

Aliases:

- `record` and `information` normalize to `fact`.
- `rules`, `operating-rule`, and `operating-rules` normalize to `rulebook`.
- `tests` and `validation` normalize to `test`.
- `implementation` normalizes to `source`.
- `design` normalizes to `architecture`.

## Output contract

JSON output must include:

- `mode: "purpose-scoped-find"`
- `purpose`
- `query`
- `searchSpaces`
- `commands`
- `candidates.records`
- `candidates.rules`
- `candidates.capabilities`
- `candidates.sourceFiles`
- `candidates.testFiles`
- `candidates.graphRows`
- `escalation`
- `notes`

Markdown output must communicate the same cue-only sections.

## Purpose spaces

| Purpose | First search spaces |
|---|---|
| `fact` | records, graph, implementation-map/source cues |
| `rulebook` | `.lazy-harness/rules/**`, capabilities |
| `test` | `.lazy-harness/tests/**`, source test files, validation capabilities |
| `capability` | `.lazy-harness/ssot/capabilities.json`, linked rulebook records |
| `source` | source/test files and graph/source cues |
| `architecture` | overview, records, rules, capabilities, source, tests, graph |
| `full` | explicit broad mode across all supported spaces |

## Implementation map

- Status: `phase-0-2-implemented`
- Source files:
  - `.lazy-harness/scripts/purpose-find.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/ssot/capabilities.json`
  - `.lazy-harness/project/feature-navigation.xml`
- Key symbols:
  - `parseArgs`
  - `normalizePurpose`
  - `buildResult`
  - `fileCandidates`
  - `capabilityCandidates`
  - `graphCandidates`
- Tests:
  - `.lazy-harness/scripts/self-test.py#check_purpose_scoped_retrieval_cli`
