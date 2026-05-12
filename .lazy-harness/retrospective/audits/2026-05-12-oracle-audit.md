# Oracle Audit — 2026-05-12

- Scope: `/home/lazydino/dev/medivance.experimental-lazy-harness`
- Branch: `experimental/lazy-harness`
- Mode: read-only exhaustive repo audit by Oracle subagent
- Result captured: 2026-05-12 UTC

## Executive conclusion

`DDD`, `SDD`, and `BDD` trigger PoCs are real and runnable, but the framework operation layer was not yet fully trustworthy. The audit identified false-green risks around missing doctor/skills, XML parse failures, stale ADR/docs, and branch policy hook conflicts.

## Verified working state

- `bun .lazy-harness/triggers/code-change.ts --scope .lazy-harness/triggers/fixtures --layer all --format json` runs successfully.
- Fixture baseline before 5c-4:
  - scanned files: 6
  - candidates: 5
  - by layer: DDD 3, SDD 1, BDD 1
- JSONL logs were parseable at audit time.
- `code-change.ts` existed at 1502 lines and contained DDD + SDD + acronym + BDD detector logic.

## Critical findings

### 1. Doctor false-green / missing skill body

Handoff referenced:

```bash
.jcode/skills/harness-doctor/scripts/doctor.sh
```

But the current worktree had no `.jcode/` directory, so doctor C1-C16 claims were not reproducible.

### 2. XML parsing failures

Two XML files failed parser validation:

- `.lazy-harness/planning/phase-5-plan.xml`: unescaped `.husky/<3 hooks>`
- `.lazy-harness/retrospective/metrics/completeness-scorecard.xml`: `</url>` closing tag mismatch for `<tsqUrl>`

### 3. ADR 0021 stale reference

Multiple files referenced ADR 0021, but `.lazy-harness/decisions/0021-experimental-branch-and-extract-strategy.md` was missing.

### 4. Hook branch policy conflict

`pre-commit-guard.sh` and `pre-push.sh` were not branch-aware:

- `pre-commit-guard.sh` could block normal `.lazy-harness/` commits even on `experimental/lazy-harness`.
- `pre-push.sh` used `origin/HEAD..HEAD`, which could treat the whole experimental branch as a private-file leak.

### 5. README / planning / handoff drift

Examples:

- README still said `17 ADR` and marked 5c-3 as next.
- Handoff pointed to old HEAD and unreproducible doctor command.
- Phase plan still referenced `commit-change.ts` for BDD even though implementation lives in `code-change.ts`.

## Recommended action order

1. Fix XML parse errors and add XML self-test.
2. Create ADR 0021 file.
3. Make hooks branch-aware.
4. Update README / handoff / phase plan stale claims.
5. Add lazy-harness self-test script.
6. Define SSOT registry before implementing 5c-4 detector.
7. Implement `--layer ssot` and SSOT fixtures.

## Status after remediation in this session

This audit file was created because the handoff already referenced this path but the file did not exist. The P0 findings are being remediated in the same session that created this file.
