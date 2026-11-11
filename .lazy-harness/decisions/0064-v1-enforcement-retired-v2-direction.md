# ADR 0064 — v1 enforcement retired; lazy-harness proceeds as v2

Status: accepted (user-confirmed 2026-11-10)
Layer: ADR
Date: 2026-11-10
Related ADR: `.lazy-harness/decisions/0063-module-composition-contract.md`, `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md` (verification policy this narrows), `.lazy-harness/decisions/0061-monitoring-core-fabric-optional.md`
Related planning: `.lazy-harness/planning/hook-to-monitoring-transition.md`
Related grammar: `.lazy-harness/AGENTS.md` §4

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Aliases:
  - v1 retirement
  - v1 강제 은퇴
  - hooks advisory
  - v2 전환
- Applies when:
  - adding, changing or reviewing a lifecycle hook, tool guard or response-completed helper
  - deciding whether validation (lazy check / lazy test) runs automatically
  - retiring a v1 CLI/record tool because a module takes over its job
- Must:
  - keep lifecycle hooks non-blocking: read-debt, search-debt, overview order, rule placement, option gate and test gates are notices or runtime records only
  - keep blocking only for destructive commands, project command boundary and Reader child boundaries
  - never run tests from hooks; recommend `lazy check` and `lazy test` (or `lazy validate --plan standard`) before merge or commit
  - retire a v1 CLI/record tool only after the monitoring or knowledge module measurably does its job
- Must not:
  - reintroduce a hook that blocks actions or drives follow-up turns for evidence/placement/test reasons
  - treat the retired v1 enforcement self-tests as protection to restore
- Record completion:
  - update this ADR when another v1 surface is retired or a hook regains blocking power

## Context

The v1 harness enforced its behaviour rules with blocking lifecycle hooks: tool calls were denied without map/read evidence (read-debt, search-debt), response-completed helpers injected STOP follow-up turns (rule placement, option gate, 5d-3 test gates) and ran affected tests automatically, and capture notices were added to every turn. In daily use these gates repeatedly stopped real work (blocked shells on automated turns, repeated re-grounding, STOP loops). Meanwhile v2 moved judgement to the monitoring module and record storage to the knowledge module (ADR 0063).

## Decision

The user officially abandons v1 and builds v2 (“공식적으로 v1 을 버리고 v2 를 제작하면서 나아갈생각”, “read debth 도 변경하고 훅도 다 빼버리자 진행해”).

| Scope | Now |
| --- | --- |
| Retired now: v1 enforcement | Pre-tool read-debt/search-debt/overview-order denials removed; 5d-3 affected-test and TDD cross-verify helpers removed from response.completed (both engines); response-completed advisories are UI/stderr notices, never follow-up turns; capture assessment is a runtime entry, not a conversation message; AGENTS.md §4 recommends validation instead of requiring it |
| Kept | Destructive-command and project-command-boundary blocking; Reader child budget/join boundaries; turn-start read-debt guidance; the helper scripts and CLI tools themselves |
| Retire later | v1 CLI and record tools (map, lint, capture) once monitoring and knowledge modules measurably replace them (staged plan in `.lazy-harness/planning/hook-to-monitoring-transition.md`) |
| Unchanged until migration | Existing `.lazy-harness/` Markdown records stay canonical until moved to the knowledge module DB |

The v1 self-tests that asserted blocking or follow-up delivery were retired or inverted to assert the non-blocking behaviour; the hook-based affected-repository routing regression and two read-debt permit/Reader-status fixture checks are no longer registered.

## Consequences

- Work no longer stops on missing evidence; agents can still miss records until monitoring injection is in place (accepted trade-off, measured in stage 3 of the transition plan).
- Validation quality depends on running the recommended commands before merge.
- Hosts receive the change through `lazy sync` after merge.

## Alternatives

- Keep blocking until monitoring is ready: rejected by the user; the gates cost more than they protected.
- Rewrite every v1 enforcement test for v2: rejected; the behaviour they protect is retired.

## Implementation map

- Status: `implemented` (branch `work/hooks-advisory`)
- Primary files: `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh`, `.lazy-harness/hooks/lifecycle/on-response-completed.sh`, `.lazy-harness/scripts/lifecycle-check.py`, `.lazy-harness/scripts/lifecycle-parity-runner.py`, `packages/lazy-harness-pi/extensions/lazy-harness/index.ts`, `.lazy-harness/AGENTS.md`
- Tests / protection: `tests/lazy-harness/pi-capture-evidence.test.ts` (non-blocking, no follow-up, destructive command still refused), `.lazy-harness/scripts/self-test.py` inverted checks (search-debt no deny, retired TDD/affected gates silent, no follow-up delivery)
