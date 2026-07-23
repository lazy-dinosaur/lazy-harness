# scripts

Framework-owned verification scripts (ADR 0022).

Jcode may wrap these commands, but operational validation lives here.

## Commands

```bash
.lazy-harness/bin/lazy check
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
- `lazy-sync.ts` — update Category A framework body on an already-initialized host while preserving host memory; `--skip-knowledge-seeds` leaves host `knowledge/*.jsonl` untouched for a reviewed rollout.
- `lazy-update.ts` — public-safe updater. Refreshes the persistent source checkout, then delegates to `lazy-sync.ts`.
- `contract-diff.ts` — existing contract diff helper.
- `lazy-check.py` — fast changed-file static validation tier used by `.lazy-harness/bin/lazy check`; not a replacement for `self-test.py` / `lazy test`.
- `../triggers/lint-output.ts` — 5c-6 tsc/eslint output classifier, exposed as `bun run lazy:lint-drift`.

## Status

- Empty containers remain valid (Principle #10).
- New checks should land in this directory first, then wrappers may call them.
