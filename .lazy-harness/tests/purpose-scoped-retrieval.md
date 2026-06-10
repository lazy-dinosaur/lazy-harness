# Purpose-Scoped Retrieval Regression

Status: accepted
Layer: TDD
Related ADR: `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`

## Regression

Purpose-scoped retrieval must not collapse back into universal record sweeps. Test/rulebook/capability purposes should search their own surfaces first while fact/architecture purposes keep broad evidence available.

## Required protection

Self-test must prove:

- `lazy find --purpose rulebook <query>` returns rulebook/capability surfaces and does not default to broad record candidates.
- `lazy find --purpose test <query>` returns TDD/source-test candidates first.
- `lazy find --purpose fact <query>` returns record candidates.
- `lazy find --purpose architecture <query>` includes broad search spaces.
- `lazy find` requires explicit `--purpose`.
- source does not reintroduce `lazy route` or raw prompt classifier semantics.
- `lazy map 'purpose scoped retrieval'` finds the dedicated record package.

## Layer completeness gate

- DDD: `.lazy-harness/domain/purpose-scoped-retrieval.md` defines fact/rulebook/test retrieval vocabulary.
- BDD: `.lazy-harness/behavior/purpose-scoped-retrieval.md` defines agent behavior scenarios.
- SDD: `.lazy-harness/spec/platform/purpose-scoped-retrieval.md` defines CLI contract.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains the no-semantic-classifier boundary.
- ADR: `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md` accepts `lazy find` over `lazy route`.

## Implementation map

- Source:
  - `.lazy-harness/scripts/purpose-find.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/self-test.py`
- Test symbol:
  - `check_purpose_scoped_retrieval_cli`
- Validation:
  - `.lazy-harness/bin/lazy test`
