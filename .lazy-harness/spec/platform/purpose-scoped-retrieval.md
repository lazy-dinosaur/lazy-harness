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
  - include a cue-only evidence capsule that can satisfy search-debt only for non-broad purposes
  - avoid raw prompt classifiers and `lazy route` semantics
  - separate fact, rulebook, test, capability, source, architecture, and full retrieval spaces
- Must not:
  - decide risk, required reads, gates, or next actions
  - mark candidates as proof that files were read
  - let `architecture` or `full` purpose output satisfy search-debt by itself
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

- Status: `phase-4-dogfood-fixture-implemented`
- Source files:
  - `.lazy-harness/scripts/purpose-find.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/ssot/capabilities.json`
  - `.lazy-harness/project/feature-navigation.xml`
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py`
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py`
- Key symbols:
  - `parseArgs`
  - `normalizePurpose`
  - `buildResult`
  - `fileCandidates`
  - `capabilityCandidates`
  - `graphCandidates`
- Tests:
  - `.lazy-harness/scripts/self-test.py#check_purpose_scoped_retrieval_cli`
  - `.lazy-harness/scripts/self-test.py#check_read_debt_permit_generic_external_action`
  - `.lazy-harness/scripts/self-test.py#check_response_rule_audit_from_surfaced_digest`
  - core temporary fixture in `.lazy-harness/scripts/self-test.py#check_purpose_scoped_retrieval_cli` for host-safe generic purpose assertions
  - downstream worktree/dev-instance fixture in `.lazy-harness/scripts/self-test.py#check_purpose_scoped_retrieval_cli`

## Phase 3 evidence integration

`lazy find` JSON output includes an `evidence` object:

```json
{
  "event": "purpose-scoped-retrieval.evidence",
  "purpose": "test",
  "searchEvidence": true,
  "readEvidence": false,
  "qualifiesSearchDebt": true,
  "caveat": "cue-only search evidence; not proof that candidate files were read"
}
```

Lifecycle helpers may count this as **search evidence only** when the explicit purpose is one of:

- `fact` / `record` / `information`,
- `rulebook` / `rules` / `operating-rule`,
- `test` / `tests` / `validation`,
- `capability` / `capabilities`,
- `source` / `implementation`.

They must not count `architecture`, `design`, or `full` purpose output as satisfying search-debt by itself. Required-read debt still requires actual read/search evidence for concrete paths; purpose-scoped find evidence is not read evidence.

## Phase 4 downstream dogfood fixture

Before the downstream dogfood fixture, `check_purpose_scoped_retrieval_cli` creates a minimal core fixture host for generic assertions. This avoids depending on host-owned record memory, because synced hosts do not have to contain framework TDD records such as `.lazy-harness/tests/purpose-scoped-retrieval.md`.

The implementation is protected by a temporary downstream-like host fixture in `check_purpose_scoped_retrieval_cli`. The fixture models a host with a worktree/dev-instance operating rule, a capability binding, an SDD fact record, a TDD record, and a source test file.

Purpose behavior under this fixture:

- `rulebook` returns `.lazy-harness/rules/dev-worktree.md` and `dev-worktree-standard-command`, without broad fact records.
- `test` returns `.lazy-harness/tests/dev-worktree-instances.md` and `tests/dev-worktree.spec.ts`, without defaulting to `.lazy-harness/spec/infra/dev-worktree-instances.md`.
- `fact` returns `.lazy-harness/spec/infra/dev-worktree-instances.md`.
- `capability` returns `dev-worktree-standard-command` for discouraged raw `git worktree add`.

This fixture exists because downstream dogfood originally showed that worktree/dev-instance policy could be present but not applied by retrieval/action guidance.
