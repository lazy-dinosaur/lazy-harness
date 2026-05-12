# Post-MVP Gap Map

Date: 2026-05-12
Branch: `experimental/lazy-harness`
Baseline commit: `43622e8b`
Status: framework MVP proof complete, real host-project pilot pending

## 1. What is complete now

| Area | Status | Evidence |
|---|---|---|
| 5c Code-trigger adapters | Complete | DDD/SDD/BDD/SSOT detectors, cross-layer map, lint drift, structured ask, E2E fixtures |
| Post-5c detector extraction | Complete | `code-change.ts` is orchestration-only, detectors live under `triggers/detectors/` |
| Framework-owned validation | Complete | `bun run lazy:test`, `bun run lazy:doctor`, pre-push guard |
| 5d Interview loop | Complete | collect, answer, TDD gate, aftershock, lifecycle hooks, walkthrough depth >= 2 |
| 5e MVP proof artifact | Complete | `retrospective/e2e/5e-mvp-proof.md` |
| Affected regression test runner | Complete | response.completed helper runs matching Vitest tests or opens structured interview gate |

## 2. MVP boundary decision

Framework MVP means the harness can prove the full loop on controlled, fixture-backed feature artifacts:

```text
trigger detection
→ structured question
→ durable answer/decision
→ TDD or affected-test gate
→ aftershock re-analysis
→ lifecycle hook surfacing
→ reproducible self-test/doctor/pre-push
```

This is now complete.

Phase 5 is not production-complete because `5e-1` still requires one real host-project feature to be shipped through the harness. After that pilot, framework work moves to a standalone `lazy-harness` repository.

## 3. Remaining gaps before Phase 5 close

| Gap | Severity | Why it matters | Next action |
|---|---|---|---|
| Real host-project feature pilot not shipped | Critical | Fixture proof is not the same as product release flow | Pick small feature, choose pattern, run harness end-to-end on feature branch |
| Traceability is fixture-backed only | High | 5e-3 needs real figma/SDD/BDD/test/code/regression links | Create real feature traceability file during pilot |
| Decision consume path is still semi-manual | High | A/B/C/D answers are persisted, but not all effects mutate target docs automatically | Add effect executor coverage per layer, starting with TDD/affected-test decisions |
| Affected test runner is Vitest-first | Medium | Good for current repo, but custom commands and Playwright need explicit routing | Add decision-driven custom test command support |
| Aftershock v0 is heuristic | Medium | It proves recursion, not full artifact-diff dependency analysis | Add artifact-diff based effect mapping after pilot data |
| Hook lifecycle docs need final alignment with jcode core | Medium | Users must understand when lifecycle outputs re-enter the LLM | Finalize hook lifecycle documentation with concrete payload/continuation examples |
| Standalone extraction not performed yet | Critical after pilot | lazy-harness must not keep living as host-project internals | Execute `.lazy-harness/plans/extract-to-lazy-harness-repo.md` |
| Project Init Interview not implemented yet | High | new projects need stack/test/architecture/design decisions captured before coding | Implement `.lazy-harness/plans/project-init-interview-spec.md` after extraction |

## 4. Recommended next execution sequence

1. Pick the real host-project pilot feature.
2. Record 5e pattern decision, likely `inside-out` for a small code-first feature.
3. Create pilot intent/spec/behavior/traceability seed files.
4. Make one small code change on a feature branch and let lifecycle hooks surface required questions/tests.
5. Answer questions through `interview-loop.ts --mode answer --apply`.
6. Run affected tests and full gates.
7. Record retrospective and close 5e criteria that are genuinely satisfied.

## 5. Validation baseline

Last verified before this document:

```bash
git diff --check
bun run typecheck:node
bun run lazy:test
bun run lazy:doctor
.lazy-harness/hooks/pre-push.sh origin dummy
git push origin experimental/lazy-harness
```

All passed. Push reached `origin/experimental/lazy-harness` at `43622e8b`.
