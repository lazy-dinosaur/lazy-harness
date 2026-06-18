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
- purpose-scoped find evidence for `rulebook`/`test` can satisfy generic search-debt as search evidence.
- purpose-scoped find evidence for `architecture`/`full` must not satisfy search-debt by itself.
- response audit stays silent when correlated search-debt has safe purpose-scoped find evidence.
- required-read debt still requires concrete read evidence; purpose-scoped find is not read evidence.
- core `lazy find` assertions use a temporary fixture host, not whatever framework records happen to be synced into the current host.
- downstream dogfood worktree/dev-instance fixture proves `rulebook`, `test`, `fact`, and `capability` purposes search different first surfaces.

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
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py`
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py`
  - `.lazy-harness/scripts/self-test.py`
  - temporary core fixture in `check_purpose_scoped_retrieval_cli`
  - temporary downstream dogfood fixture in `check_purpose_scoped_retrieval_cli`
- Test symbol:
  - `check_purpose_scoped_retrieval_cli`
- Validation:
  - `.lazy-harness/bin/lazy test`

## Core fixture host safety

Self-test creates a temporary core fixture for the generic `lazy find` assertions:

- `.lazy-harness/rules/project-policy-storage.md` — proves `rulebook` purpose returns rules without broad records.
- `.lazy-harness/tests/purpose-scoped-retrieval.md` — proves `test` purpose returns TDD records.
- `.lazy-harness/decisions/purpose-scoped-retrieval.md` — negative fixture proving `test` purpose does not default to ADR/fact sweeps.
- `.lazy-harness/spec/platform/capability-resolution.md` — proves `fact` purpose returns fact/contract records.
- `.lazy-harness/ssot/capabilities.json` — proves `retrieval_test` capability resolution works.

This fixture is required because host memory is host-owned. A downstream host may not contain framework TDD records such as `.lazy-harness/tests/purpose-scoped-retrieval.md`, and self-test must still validate framework CLI behavior there.

## Phase 4 downstream dogfood fixture

Self-test creates a temporary downstream-like host with:

- `.lazy-harness/rules/dev-worktree.md` — operating rule for `bun run wt new` / `bun run dev:instance` wrappers.
- `.lazy-harness/ssot/capabilities.json` — `dev-worktree-standard-command` with `preferredActions` and `discouragedActions`.
- `.lazy-harness/spec/infra/dev-worktree-instances.md` — fact/contract record.
- `.lazy-harness/tests/dev-worktree-instances.md` — TDD/regression record.
- `tests/dev-worktree.spec.ts` — source test cue.

Required assertions:

- `lazy find --purpose rulebook 'git worktree add'` returns the rulebook/capability surfaces and no broad fact records.
- `lazy find --purpose test 'worktree dev instance'` returns TDD/source-test surfaces and no SDD fact record by default.
- `lazy find --purpose fact 'dev worktree instances'` returns the SDD fact record.
- `lazy find --purpose capability 'git worktree add'` returns `dev-worktree-standard-command`.
