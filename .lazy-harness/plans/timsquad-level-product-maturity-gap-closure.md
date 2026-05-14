# Plan — timsquad-level product maturity gap closure

Date: 2026-05-14
Status: active plan
Related audit: `.lazy-harness/retrospective/audits/2026-05-12-lazy-vs-timsquad-comparison.md`
Related scorecard: `.lazy-harness/retrospective/metrics/completeness-scorecard.xml`

## 1. Context

User asked to compare lazy-harness maturity against `https://github.com/sonature-lab/timsquad`, which is the external product-maturity reference target.

Current conclusion:

- Lazy-harness is stronger in conceptual depth, record-first convergence, implementation mapping, user-correction persistence, and lifecycle safety.
- TimSquad is stronger in productization, public installation, CLI/skill UX, packaging, templates, public docs, rollback/update UX, daemon polish, and external adoption readiness.
- The correct strategy is not to clone TimSquad templates, but to close productization gaps while preserving lazy-harness' differentiator: AI error recovery through record-first lifecycle governance.

## 2. Latest quantitative snapshot

Measured 2026-05-14 from local lazy-harness and public TimSquad GitHub tree.

| Metric | TimSquad v3.8 | lazy-harness | Note |
|---|---:|---:|---|
| Public package | npm package `timsquad` | install script + source repo, no npm package | TimSquad ahead |
| Total files | 479 | 247 tracked `.lazy-harness` files | TimSquad ahead |
| TypeScript files | 77 | ~40 | TimSquad ahead |
| Template files | 330 | intentionally low, manifest/seed driven | Strategic difference |
| Test files | 23 | 8 tracked test/record files, plus 21 self-test checks | Different shapes |
| Skill dirs | ~39 | public/tracked skills not yet productized | TimSquad ahead |
| Agent templates | ~10 | Jcode profile routing private/local | TimSquad ahead |
| Docs files | 55 | ADR/records rich, public docs less polished | TimSquad ahead in UX |
| ADRs | not central | 32 ADRs | lazy-harness ahead |
| Framework validation | vitest/lint/build | self-test + doctor + host sync dogfooding | lazy-harness strong internally |

## 3. Current maturity estimate

| Dimension | Score | Rationale |
|---|---:|---|
| Conceptual completeness | 9.1 / 10 | ADR 0030~0032 closed implementation maps, root-bound convergence, user-correction ownership convergence. |
| Internal implementation completeness | 5.8 / 10 | lazy-init/sync/update/test/doctor, self-test, smoke doctor, dogfooding hosts all working. |
| Product maturity | 3.2 / 10 | no npm package, weak public CLI docs, rollback incomplete, skill ecosystem not productized. |
| Ecosystem maturity | 3.0 / 10 | private Jcode skills exist but public installable skills/agents are not yet at TimSquad level. |
| Safety/lifecycle maturity | 8.3 / 10 | record-first, default unknown, missing-record convergence, user correction SSOT, implementation maps, lifecycle tests. |

## 4. What TimSquad does better

1. Global install and public package UX.
2. Clear `tsq init`, `tsq update`, `tsq daemon` user story.
3. Rollback-capable update flow.
4. Large skill ecosystem.
5. Agent templates installed for Claude Code.
6. Project type/level/domain/stack driven init.
7. Polished public docs in English/Korean.
8. Daemon-backed metrics and meta-index UX.
9. Public changelog/release cadence.
10. External user mental model is simpler.

## 5. What lazy-harness does better

1. Default unknown epistemic baseline.
2. Root-bound record search, no sibling repo contamination.
3. Missing records converge into `.lazy-harness` instead of scattered docs.
4. User corrections about host role/source-of-truth/ownership become confirmed SSOT overrides.
5. DDD/SDD/BDD/TDD/ADR/SSOT are equal first-class layers.
6. Implementation map 3-layer storage: human MD, JSONL graph, generated index cache.
7. Framework self-test and doctor validate its own operating grammar.
8. Dogfooding sync across `dev/medivance` and `dev/medivance-pwa` is proven.
9. Stronger recovery/safety posture for AI mistakes.

## 6. Priority roadmap to reach TimSquad-level visible completeness

### P1 — Product shell

Goal: a fresh project can install, inspect, update, validate, and rollback without knowing internal paths.

- `lazy inspect`
- `lazy status`
- `lazy init --interview`
- `lazy update --rollback`
- `lazy sync --rollback` or snapshot-backed rollback
- public `docs/cli.md` and `docs/cli.ko.md`
- GitHub Actions: self-test, doctor, temp-host init smoke, sync smoke

### P2 — Project Init Interview

Goal: turn root-bound convergence into first-run project profile setup.

Seed or update:

- `.lazy-harness/ssot/project-identity.md`
- `.lazy-harness/ssot/*ownership*.md`
- `.lazy-harness/tests/test-strategy.xml`
- stack/config summary
- allowed/forbidden mutation boundaries
- upstream/downstream host relationships

### P3 — Public skill and agent ecosystem

Goal: make the private Jcode behavior installable and discoverable.

Candidate skills:

- `/lazy-start`
- `/lazy-status`
- `/lazy-record`
- `/lazy-ownership`
- `/lazy-test-strategy`
- `/lazy-audit`
- `/lazy-retro`
- `/lazy-report`

Optional cross-environment templates:

- Jcode `.jcode/` wiring remains primary for Lazydino.
- Claude Code `.claude/agents` and `.claude/skills` can be optional output later.

### P4 — Public docs and proof

Goal: explain the framework without internal session context.

- Rewrite root README as user-facing product README.
- Move internal status into `docs/internal/` or `.lazy-harness/handoff/` only.
- Add case studies:
  - medivance dogfooding sync
  - medivance-pwa DB ownership correction
  - test-strategy convergence and Vitest-not-forced clarification
- Add release notes/changelog.

### P5 — Daemon / metrics / graph index

Goal: make graph/retrospective useful beyond static files.

- `lazy daemon status`
- validation history summary
- stale record warnings
- implementation-index generator
- graph query UX

## 7. Immediate next actions

Recommended execution order:

1. Implement `lazy inspect` + `lazy status` before adding more theory.
2. Implement Project Init Interview minimal path that writes project identity, ownership, and test strategy records.
3. Add rollback snapshots to update/sync.
4. Write public CLI docs.
5. Add temp-host CI smoke.
6. Then productize skills.

## 8. Screenshot observation: SDD/TDD behavior gap

User showed another session where the agent said SDD was not automatic and TDD was added, then admitted SDD was missed for `ChatWindow` / `WindowControls` contract.

Interpretation:

- The conclusion that SDD should be updated is correct when interface/contract/component boundaries are touched.
- The phrase "자동이 아니라 내가 판단해서 누적" is partially wrong for lazy-harness intent. It is not arbitrary agent judgment. Layer trigger mapping is a framework rule: API / contract / component changes trigger SDD search/update.
- TDD is for bug reproduction/regression/protection, not a replacement for SDD.
- A change can require both SDD and TDD:
  - SDD: contract/interface such as `ChatWindow`, `WindowControls`, `onClose`, scroll behavior, IPC/window mode.
  - TDD: regression protection such as "new window should start minimized" or "X click closes the room".
- This suggests a future guard gap: layer-impact should more aggressively flag SDD when UI component props, IPC contracts, or window-control contracts change.

## 9. Implementation map

- Status: `planned`
- Primary files:
  - `.lazy-harness/plans/timsquad-level-product-maturity-gap-closure.md` — this plan.
  - `.lazy-harness/retrospective/audits/2026-05-12-lazy-vs-timsquad-comparison.md` — previous comparison baseline.
  - `.lazy-harness/retrospective/metrics/completeness-scorecard.xml` — older scorecard to update later.
  - `.lazy-harness/plans/project-init-interview-spec.md` — P2 details.
  - `.lazy-harness/plans/post-mvp-gap-map.md` — existing post-MVP gap sequence.
- Key symbols / config:
  - `lazy inspect` — planned CLI command.
  - `lazy status` — planned CLI command.
  - `Project Init Interview` — planned onboarding flow.
- Flow:
  1. Preserve lazy-harness conceptual advantage.
  2. Close product-shell and onboarding gaps.
  3. Productize skills and docs.
  4. Add public proof and CI.
- Tests / protection:
  - Future: `python3 .lazy-harness/scripts/self-test.py`
  - Future: `python3 .lazy-harness/scripts/doctor.py --profile smoke`
  - Future: temp-host init/sync smoke in CI.
- Ownership boundaries:
  - Owner/upstream: `/home/lazydino/dev/lazy-harness`.
  - This plan may change framework roadmap/docs/scripts.
  - This plan must not mutate host project app code directly.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
  - ADR: `.lazy-harness/decisions/0031-root-bound-record-convergence.md`
  - ADR: `.lazy-harness/decisions/0032-user-correction-ownership-ssot-convergence.md`
  - TDD: `.lazy-harness/tests/test-strategy.xml`
- Machine index:
  - graph ids: `pending`
  - generated index key: `pending until implementation-index generator exists`
