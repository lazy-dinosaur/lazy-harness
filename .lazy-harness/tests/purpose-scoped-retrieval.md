# Map-First Retrieval Regression

Status: accepted
Layer: TDD
Related ADR: `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`

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
