# Post-MVP Gap Map

Date: 2026-05-12
Branch: `experimental/lazy-harness`
Baseline commit: `43622e8b`; updated through host-project pilot remediation
Status: framework MVP proof complete, host-project pilot complete, extraction pending

## 1. What is complete now

| Area | Status | Evidence |
|---|---|---|
| 5c Code-trigger adapters | Complete | DDD/SDD/BDD/SSOT detectors, cross-layer map, lint drift, structured ask, E2E fixtures |
| Post-5c detector extraction | Complete | `code-change.ts` is orchestration-only, detectors live under `triggers/detectors/` |
| Framework-owned validation | Complete | `bun run lazy:test`, `bun run lazy:doctor`, pre-push guard |
| 5d Interview loop | Complete | collect, answer, TDD gate, aftershock, lifecycle hooks, walkthrough depth >= 2 |
| 5e MVP proof artifact | Complete | `retrospective/e2e/5e-mvp-proof.md` |
| Affected regression test runner | Complete | response.completed helper runs matching project-routed tests or opens structured interview gate |

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

The first host-project pilot is complete and documented in `retrospective/e2e/5e-host-project-pilot.md`. It proved the harness loop on a real feature branch and found the affected-test command-routing gap. After remediation, the next learning step is not immediate extraction. The framework should first apply Project Profile concepts to the real Medivance host project, then repeat real feature pilots until the profile/interview/report needs stabilize.

## 3. Remaining gaps before Phase 5 close

| Gap | Severity | Why it matters | Next action |
|---|---|---|---|
| Real host-project feature pilot | Closed for first pilot | Feature branch commit `ba162ab1` proves first end-to-end host pilot | Keep merge/release outside framework branch; use learning for extraction |
| Formal traceability file for host pilots | Medium | Pilot has branch/test/commit evidence but not generated formal traceability XML | Generate during Project Init Interview / future pilot profile |
| Decision consume path is still semi-manual | High | A/B/C/D answers are persisted, but not all effects mutate target docs automatically | Add effect executor coverage per layer, starting with TDD/affected-test decisions |
| Affected test command routing v1 | Closed for unit/component | Runner now uses test-strategy or package script, not hardcoded Vitest | Extend to Playwright/e2e/workspaces after extraction |
| Aftershock v0 is heuristic | Medium | It proves recursion, not full artifact-diff dependency analysis | Add artifact-diff based effect mapping after pilot data |
| Hook lifecycle docs need final alignment with jcode core | Medium | Users must understand when lifecycle outputs re-enter the LLM | Finalize hook lifecycle documentation with concrete payload/continuation examples |
| Project Profile skill not implemented yet | High | before each real host feature, agents need a project-local profile for folder structure, architecture, design system, testing, and recording rules | Implement a lightweight skill-first Project Profile flow from `.lazy-harness/plans/project-init-interview-spec.md`; CLI can come later |
| Standalone extraction not performed yet | Critical later | lazy-harness must eventually stop living as host-project internals, but premature extraction would freeze unproven assumptions | Extract only after Project Profile skill + several real host pilots stabilize |
| Portable host-project report not implemented yet | Medium | host projects need a copy/pasteable report so framework repo can learn from real usage without relying on chat history | Implement `.lazy-harness/plans/report-and-knowledge-roadmap.md` after Project Profile skill proves what report fields matter; defer DB/RAG until report JSON proves useful |

## 4. Recommended next execution sequence

1. Keep host pilot branches separate from framework branch.
2. Add a lightweight Project Profile skill/manifest entry that applies the Project Init Interview concept without waiting for a full CLI.
3. Use the skill on Medivance to create or update project profile artifacts: purpose, folder structure, frontend/backend architecture, design system, test strategy, and agent rules.
4. Run several real host-project feature pilots against that profile.
5. Promote repeated questions/gaps from those pilots into the future Project Init Interview CLI.
6. Implement portable `lazy:report` Markdown + JSON export once the real report fields are clear.
7. Prepare standalone `lazy-harness` repository extraction after the profile/report loop stabilizes.
8. Expand affected-test routing to Playwright/e2e/workspaces.
9. Add artifact-diff aftershock mapping after pilot data.
10. Consider DB/RAG ingestion only after report JSON proves useful.

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
