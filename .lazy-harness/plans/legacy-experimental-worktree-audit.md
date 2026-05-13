# Legacy Experimental Worktree Audit Queue

Date: 2026-05-13
Status: queued
Scope: `/home/lazydino/dev/medivance.experimental-lazy-harness` on branch `experimental/lazy-harness`

## Why this exists

The canonical lazy-harness source of truth is now `/home/lazydino/dev/lazy-harness` (`main`) and the dogfooding host is `/home/lazydino/dev/medivance`.
The experimental Medivance worktree is legacy extraction scaffolding, but it may still contain useful fixes or drift signals.
Do not delete or overwrite it without explicit user confirmation.

## Current observed legacy state

User-provided summary says:

- `.lazy-harness/` framework v1.4
- ADR 0001~0026
- 5c complete
- 5d Interview Loop complete
- 5e host-project pilot complete
- `bun run lazy:doctor` passed
- `bun run lazy:test` failing from fixture count drift: BDD expected 3, actual 2
- doctor warning: one Unicode replacement character in `decisions.jsonl`

Fresh existence check from canonical repo session:

```text
/home/lazydino/dev/medivance.experimental-lazy-harness exists
branch: experimental/lazy-harness
modified:
  .lazy-harness/logs/actions.jsonl
  .lazy-harness/logs/validations.jsonl
  .lazy-harness/regression/candidates.jsonl
```

## Queue items

### 1. Fixture baseline drift audit

Goal: decide whether the legacy BDD fixture drift contains a useful regression case or is already obsolete in the canonical repo.

Steps:

1. Run legacy `.lazy-harness/bin/lazy test` or equivalent in the experimental worktree.
2. Capture exact failing fixture path and expected/actual values.
3. Compare against canonical `/home/lazydino/dev/lazy-harness` trigger fixture expectations.
4. If canonical source already fixes it, mark obsolete.
5. If canonical source lacks protection, port the minimal fixture/test correction into canonical repo only.

### 2. Unicode replacement warning audit

Goal: determine whether the `decisions.jsonl` replacement character warning exists only in legacy or should be cleaned in canonical records.

Steps:

1. Locate `�` in legacy `.lazy-harness/logs/decisions.jsonl`.
2. Compare canonical `.lazy-harness/logs/decisions.jsonl` and doctor D08 result.
3. If canonical contains the bad character, fix with evidence preserving original meaning.
4. If legacy-only, record as obsolete legacy drift.

### 3. Recoverable work audit

Goal: ensure no useful framework code/docs from `experimental/lazy-harness` are missing from canonical source.

Steps:

1. Compare framework-owned paths only:
   - `.lazy-harness/scripts/`
   - `.lazy-harness/hooks/`
   - `.lazy-harness/schemas/`
   - `.lazy-harness/triggers/`
   - `.lazy-harness/manifests/`
   - `.lazy-harness/AGENTS.md`
   - `.lazy-harness/README.md`
   - `.lazy-harness/JCODE-INTEGRATION.md`
2. Ignore host institutional memory unless explicitly requested.
3. Produce a short table: `obsolete | already ported | candidate to port | unsafe/private`.
4. Port only candidate framework changes into `/home/lazydino/dev/lazy-harness`.

## Constraints

- Do not treat the experimental worktree as source of truth.
- Do not delete the worktree without explicit confirmation.
- Do not modify `/home/lazydino/dev/medivance/.lazy-harness` directly except via sync/update.
- Any recovered framework change must land in canonical source repo first, then sync to hosts.
