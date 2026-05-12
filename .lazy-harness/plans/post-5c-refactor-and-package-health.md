# Post-5c Refactor + Package Health Plan

Date: 2026-05-12
Branch: `experimental/lazy-harness`
Baseline commit: `e29eb9ce Test(lazy-harness): pin 5c e2e cascade`

## Verified baseline

```bash
bun run lazy:test
bun run lazy:doctor
.lazy-harness/hooks/pre-push.sh origin dummy
```

Current pinned outputs:

- Trigger fixture counts: `{'ddd': 6, 'sdd': 2, 'bdd': 3, 'ssot': 7}`
- 5c-8 E2E counts: `{'ddd': 1, 'sdd': 1, 'bdd': 1, 'ssot': 2}`
- 5c-8 cross-layer summary: `sdd->ddd:gap=1`, `bdd->ddd:gap=1`, `bdd->sdd:gap=1`
- Structured ask validation: `ok=true`
- Doctor full profile: D01~D06 green

## Current size

```text
1928 .lazy-harness/triggers/code-change.ts
 210 .lazy-harness/triggers/lint-output.ts
 256 .lazy-harness/scripts/doctor.py
 313 .lazy-harness/scripts/self-test.py
```

`code-change.ts` is now the main maintainability risk. It contains DDD, SDD, BDD, SSOT, cross-layer, structured ask validation, CLI parsing, and filesystem/git helpers in one file.

## Refactor goal

Split behavior without changing output.

Target layout:

```text
.lazy-harness/triggers/
  code-change.ts              # CLI + orchestration only
  types.ts                    # shared public types
  registries.ts               # known terms, XML registry readers
  common.ts                   # path/git/source helpers, unique/splitIdentifierWords
  structured-ask.ts           # validateStructuredAsk(s)
  cross-layer.ts              # buildCrossLayerMap
  detectors/
    ddd.ts
    sdd.ts
    bdd.ts
    ssot.ts
```

## Refactor order

1. Extract pure/common helpers first.
   - `unique`, `normalizePath`, `isTypescriptFile`, `splitIdentifierWords`, registry readers.
   - Validation: `bun run lazy:test` unchanged.
2. Extract `structured-ask.ts` and `cross-layer.ts`.
   - Lowest coupling and already pinned by 5c-7/5c-5 tests.
3. Extract detector modules one at a time.
   - DDD first, then SDD, BDD, SSOT.
   - After each extraction run `bun run lazy:test`.
4. Keep `code-change.ts` as stable public CLI.
   - No CLI flag change.
   - No JSON shape change.

## Non-goals

- Do not introduce `.jcode` as primary doctor.
- Do not change detector heuristics during extraction.
- Do not broaden fixture baselines unless a deliberate behavior change is required and documented.

## Package/dependency health

Current `bun run typecheck:node` result:

```text
error TS2688: Cannot find type definition file for 'electron-vite/node'.
  The file is in the program because:
    Entry point of type library 'electron-vite/node' specified in compilerOptions
tsconfig.node.json(2,13): error TS6053: File '@electron-toolkit/tsconfig/tsconfig.node.json' not found.
```

Classification by 5c-6: environment/package health, not lazy-harness code drift.

Likely root cause:

- package install state is incomplete for `electron-vite` / `@electron-toolkit/tsconfig`, or workspace dependency resolution is stale.

Recommended remediation sequence:

1. Check dependency presence without mutating state:
   ```bash
   bun pm ls electron-vite @electron-toolkit/tsconfig
   test -e node_modules/electron-vite
   test -e node_modules/@electron-toolkit/tsconfig
   ```
2. If missing, run install/bootstrap in the main project context:
   ```bash
   bun install
   ```
3. Re-run:
   ```bash
   bun run typecheck:node
   ```
4. If still failing, add a doctor D07 package-health check that reports missing package/config as `environment` and keeps it separate from framework regression.

## Success criteria for next work

- Refactor preserves `lazy:test` output exactly.
- `git diff --check` clean after each extraction.
- `pre-push.sh origin dummy` leaves working tree clean.
- Package health is either fixed or explicitly reported by doctor D07 as environment issue.
