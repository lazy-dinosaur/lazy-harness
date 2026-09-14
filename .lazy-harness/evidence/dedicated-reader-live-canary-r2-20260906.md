# Evidence — Dedicated Reader live canary R2

Status: **TERMINAL-INCOMPLETE — no retry**

## Identity

- Implementation worktree: `/tmp/lazy-harness-reader-runtime-v1`, branch `work/reader-runtime-v1`.
- Canary root: `/tmp/lh-reader-runtime-live-canary-r2-20260906`.
- Synthetic source HEAD/tree: `8ac8988ab2e79c3ca7f7150ae0a84989930e7195` / `1265e9c2465b8dde1a9678e24df8ad23c0489591`.
- Parent: one exact `openai-codex/gpt-5.6-sol:medium` session.
- Reader: one package-discovered `lazy-harness.record-reader`, exact `openai-codex/gpt-5.6-luna:low`, one successful model attempt.
- Contract SHA-256: `a862ad2fb3751fa1e2d2fda71ff6432b597d3d692515e673b710adf6cad7480c`.
- Preflight SHA-256: `16bb781569278e58f309e734053391098227b7031b6ee526bd8dd699f566f3cb`.
- Artifact manifest SHA-256: `1887f55e6f597dd7ea27e85bac1ada571e82dff82e374685a8f7fc8b0f36ca3f` (`25` files).

R1 at `/tmp/lh-reader-runtime-live-canary-r1-20260906` was superseded before any model launch when source review found missing Reader-child lifecycle isolation. R2 consumed the one approved live allowance.

## Passed boundaries

- Package discovery surfaced exactly one `lazy-harness.record-reader` role.
- Launch used explicit Luna Low, Agent Contract v1, `acceptance:false`, `output:false`, `artifacts:false`, fresh context, exact cwd, and exact root/revision/model/evidence-epoch/lowered-budget/task fields.
- Reader child had no Parent `lazy-harness` lifecycle custom message; role-marker isolation worked.
- Reader first call was the exact complete overview and it selected/drilled its own nodes.
- One `3,077`-byte Reader result reached Parent before `lazy_reader_join`.
- Parent made zero canonical record-body reads.
- Parent joined the packet as `incomplete`; it was not promoted to complete, and Parent obeyed the canary's no-fallback stop.
- Pi print mode preserved the Parent terminal response on stdout; the capture advisory appeared on stderr with no response-replacing assistant turn.
- Source remained tracked/staged clean; no mutation, retry, fallback model, validation, commit, push, release, or graph migration occurred.

## Terminal gaps

### Reader cumulative line budget

Five successful reads requested `350 + 280 + 280 + 220 + 220 = 1,350` lines against `maxRequestedLines=1,200`. Reader accurately reported `failedToolCalls=0` and `LAZY_HARNESS_READER_RESULT: incomplete`. No semantic or efficiency result is admitted.

### Parent parallel source lane

The Parent attempted source work while Reader ran, but both calls were blocked:

1. a read-only source `rg` was false-classified as an action by the Python debt helper because its `READ_ONLY_SHELL_RE` lagged the TypeScript recognizer;
2. the Parent's follow-up compound `printf`/`find` call was classified as an action and correctly blocked by the pending join.

No Parent source evidence was delivered. Child-result delivery itself succeeded.

### Runner measurement

`run/status.json` recursively counted the nested Reader session file as a second Parent session. Actual topology was one Parent and one Reader. The original status remains immutable; analysis records the correction.

## Diagnostic metrics

- wall: `63.982s`;
- Parent: 7 turns, 6 tools, 95,597 provider tokens, `$0.22229900`;
- Reader: 4 turns, 7 tools, 66,303 provider tokens, `$0.00878884`, `29.370s`;
- combined: 11 turns, 13 tools, 161,900 provider tokens, `$0.23108784`.

These metrics are not promoted because the packet was incomplete and the Parent source lane failed.

## User-confirmed correction

The user selected **Per-read cap + guard alignment** without authorizing a new model run:

- derive and bind `maxLinesPerRead = floor(maxRequestedLines / maxReadCalls)` through task, launch state, Reader contract, and join; R2's limits yield `200`, so six allowed reads cannot exceed 1,200 lines;
- align Python read-only shell recognition with TypeScript for safe source `grep`/`rg`/`find` while Reader is pending;
- protect both with focused/full static regressions;
- ask again before any new live canary.

## Discovery capture

- DDD: no new vocabulary.
- SDD: candidate/confirmed defect in per-read budget binding and cross-language read-only shell parity.
- BDD: Reader/Parent parallel behavior remains selected; live source-lane execution is incomplete.
- TDD: add per-read cap equality/violation and pending Reader read-only source-shell scenarios.
- ADR: no ownership change.
- SSOT: no settings or ownership change.
- Planning: R2 terminal outcome and user-selected static correction recorded; no rerun authorized.

## Static correction implementation and adversarial review

The selected correction is implemented in the isolated worktree without another model canary:

- task/role/launch/join bind `maxLinesPerRead=floor(total/count)` and `maxObservedReadLimit`;
- complete ledgers require positive calls/lines/observed limit, `recordPaths <= readCalls`, observed <= requested, requested <= calls × cap, and zero failed calls;
- Reader child keeps Parent lifecycle isolation but has a dedicated tool boundary allowing canonical record read/grep and exact overview/drill/pwd/revision commands only;
- non-complete or errored-complete joins discard every pre-join call before fallback evidence is evaluated;
- Parent source work may use native read/grep/find or simple shell grep/rg with head/tail/wc filters; adversarial chained, redirected, substituted, write-option, unsafe-filter, quoted/escaped `rg --pre`, and nested namespaced shell forms remain blocked.

Successive independent reviews surfaced and drove fixes for each adversarial boundary. One resumed reviewer failed before review (`Cannot read properties of undefined (reading 'create')`) and is preserved as infrastructure failure. Focused package, generic read-debt, and 19-scenario hook checks pass. Final independent blocker review `7bd36fb6` returned `No issues found` / isolated `OK`; standard validation passed (`76.201s`, full self-test `75.869s`). R2 itself remains terminal-incomplete and is never relabeled.
