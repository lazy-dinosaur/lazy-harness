# Map-First Retrieval Regression

Status: accepted
Layer: TDD
Related ADR: `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - 맵 회귀 테스트
  - map regression
  - 검색 보호
- Applies when:
  - changing retrieval helpers, map traversal, or search/read-debt evidence rules
  - validating that agents follow the project map instead of delegating semantic search to a CLI
- Must:
  - keep `lazy map` map-traversal only: reject `--query`, raw user text, and long natural-language strings
  - require concrete record/source/test reads; map overview is search evidence only, not required-read
  - teach map-first retrieval in message.received and forbid keyword grep/rg/find fallback
- Must not:
  - advertise or accept `lazy find`/`purpose-find.ts`, or treat grep/rg/find/agentgrep as search evidence
- Record completion:
  - changes to map-first retrieval update this TDD plus ADR 0045 and the purpose-scoped-retrieval SDD/DDD/BDD
- Related records:
  - `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`
  - `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`
  - `.lazy-harness/domain/purpose-scoped-retrieval.md`
  - `.lazy-harness/behavior/purpose-scoped-retrieval.md`
  - `.lazy-harness/ssot/cli-tool-boundary.md`

## Regression

Retrieval helpers must not become semantic search engines. Agents should follow the project map, pick concrete nodes, and read actual record/source/test evidence. `lazy find` and query-like `lazy map` usage caused agents to delegate search to CLI output.

## Required protection

Self-test must prove:

- `lazy find` is not advertised by `lazy help`.
- `lazy find --purpose ...` fails.
- `purpose-find.ts` is absent.
- `lazy map --query ...` fails.
- `lazy map 'long natural-language string'` fails with a map-node error.
- `lazy map <feature-id>` succeeds for a concrete feature id copied from overview.
- `lazy map --overview` teaches concrete map traversal, not free-form query search.
- message.received prompt teaches map-first retrieval, forbids raw user text / invented `--query` for `lazy map`, and forbids keyword grep/rg/find fallback.
- search/read debt helpers no longer treat `lazy find`, grep, rg, find, agentgrep, or generic query tools as search evidence.
- required-read debt still requires concrete read evidence; map overview is search evidence only.
- exact record-path drill returns one focused record (`counts.records == 1`, `features == 0`) with a `Focused` note; compact fuzzy `relatedRecords` never contain the focused record itself, stay one-liners (`recordPath/title/status/aliases` only, aliases ≤ 2), and every neighbor exists in the real record index (no fabrication). The no-self and compactness guards live inside the `for entry in related:` loop of `check_purpose_scoped_retrieval_cli` — they must remain loop children, never re-indented under the Rule-digest block (2026-09-17 incident: PR8 dead-coded them via indent shift and was only caught by deployment audit; restored by PR9).
- focused drill exposes the record `Rule digest` (appliesWhen ≤ 2, must ≤ 3, mustNot ≤ 1) sourced verbatim from the record body's `## Rule digest` section (digest-first loading).
- keyword drill keeps multi-record fuzzy results; in markdown only the top two records render full detail and tail records render compact one-liners.

## Layer completeness gate

- DDD: `.lazy-harness/domain/purpose-scoped-retrieval.md` defines map-first vocabulary.
- BDD: `.lazy-harness/behavior/purpose-scoped-retrieval.md` defines agent behavior scenarios.
- SDD: `.lazy-harness/spec/platform/purpose-scoped-retrieval.md` defines CLI contract.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains the no-semantic-classifier boundary.
- ADR: `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md` supersedes purpose find with map-first retrieval.

## Implementation map

- Source:
  - `.lazy-harness/scripts/record-map.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh`
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py`
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py`
  - `.lazy-harness/scripts/self-test.py`
- Test symbol:
  - `check_purpose_scoped_retrieval_cli` — retained name; now validates map-first retrieval and removed find.
- Validation:
  - `.lazy-harness/bin/lazy test`
