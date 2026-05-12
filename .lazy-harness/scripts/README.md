# scripts

Framework-owned verification scripts (ADR 0022).

Jcode may wrap these commands, but operational validation lives here.

## Commands

```bash
bun run lazy:test
bun run lazy:doctor
python3 .lazy-harness/scripts/doctor.py --profile smoke
python3 .lazy-harness/scripts/doctor.py --profile full
```

## Files

- `self-test.py` — primary reproducible gate used by `bun run lazy:test` and pre-push.
  - doctor smoke
  - C17 negative fixture
  - XML/JSONL parse
  - DDD/SDD/BDD/SSOT trigger fixture counts
  - cross-layer map exact summary/gaps
  - structured ask validation report
- `doctor.py` — framework-owned doctor.
  - D01 XML parse
  - D02 JSONL parse
  - D03 ADR sequence + doc count
  - D04 README/handoff/phase freshness
  - D05 branch/hook policy
  - D06 C17 external dependency invariant (full profile)
- `contract-diff.ts` — existing contract diff helper.
- `../triggers/lint-output.ts` — 5c-6 tsc/eslint output classifier, exposed as `bun run lazy:lint-drift`.

## Status

- Empty containers remain valid (Principle #10).
- New checks should land in this directory first, then wrappers may call them.
