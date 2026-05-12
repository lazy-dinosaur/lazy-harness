# Extract to Standalone `lazy-harness` Repository

Date: 2026-05-12
Status: mandatory next-stage boundary
Current branch: `experimental/lazy-harness`

## Non-forgettable rule

This repository is only the **host-project incubation worktree** for validating lazy-harness.

After framework MVP proof and one host-project pilot validation, ongoing framework work must move to a standalone repository named:

```text
lazy-harness
```

Do not keep growing framework internals indefinitely inside the host project repository.

## Why extract

- `.lazy-harness/` is a framework, not product code.
- Host-project branches must not carry framework internals.
- ADR 0021 already established the experimental branch boundary.
- The next maturity step is repository boundary, not more host-repo patching.

## Extraction trigger

Extraction becomes the default next action once these are true:

1. Framework MVP proof is complete.
2. `lazy:test`, `lazy:doctor`, and pre-push pass.
3. A small host-project pilot has exercised the lifecycle enough to confirm the flow.
4. Post-MVP gap map is updated with any pilot findings.

## Target repo contents

Move or recreate as first-class repo assets:

```text
.lazy-harness/framework/
.lazy-harness/decisions/
.lazy-harness/hooks/
.lazy-harness/scripts/
.lazy-harness/schemas/
.lazy-harness/triggers/
.lazy-harness/plans/
.lazy-harness/handoff/
.lazy-harness/retrospective/
package.json scripts: lazy:test, lazy:doctor, lazy:test:affected
README.md
```

Then normalize paths so the standalone repo does not require the host project layout.

## Host-project integration after extract

The host project should only keep a thin integration surface, for example:

```text
.lazy-harness.config.*
.husky/pre-commit
.husky/post-commit
.husky/pre-push
```

Those wrappers should call the standalone lazy-harness package/repo instead of owning framework internals.

## Extraction checklist

1. Create new repository `lazy-harness`.
2. Copy framework-owned files from this experimental branch.
3. Remove host-project-specific names from docs and fixtures unless intentionally labeled as examples.
4. Make `lazy:test` pass in the new repo without host-project assumptions.
5. Add fixture host project under `fixtures/host-project/` if needed.
6. Document installation/back-link from a host project.
7. Keep ADR 0021 history, then add a new ADR for standalone repo boundary.
8. In the host project, replace tracked framework internals with wrapper/integration only.

## Forbidden after extract

- Do not use a product repository as the long-term SSOT for framework internals.
- Do not commit `.lazy-harness/` internals to normal product branches.
- Do not make Jcode own framework logic. Jcode remains a harness/tool wrapper.
