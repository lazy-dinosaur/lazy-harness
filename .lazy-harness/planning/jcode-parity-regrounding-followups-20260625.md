# Planning — Jcode-Parity Re-Grounding Follow-ups

Status: open
Created: 2026-06-25
Layer: Planning
Related ADR: `.lazy-harness/decisions/0051-jcode-parity-grammar-regrounding.md`
Related SDD: `.lazy-harness/spec/platform/pi-agent-package.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: framework-global
- Applies when:
  - verifying or extending the OMP/Pi jcode-parity re-grounding work (ADR 0051)
  - deciding whether to re-introduce a hard response-completion gate
- Must:
  - treat the two open items below as the remaining work before declaring full jcode parity
- Must not:
  - claim live end-to-end parity until the fresh-session verification passes

## Context

ADR 0051 restored jcode's two grounding mechanisms in the OMP/Pi extension and
shipped + synced them (commits `1ccfd05`/`62fc284`/`791d659`/`069d603`/`3617769`/
`deb9d53`/`3bb06d5`/`ce34f98`/`32c8986`):

- (1a) `before_agent_start` force-loads the full `.lazy-harness/AGENTS.md` grammar into the system prompt once per session (jcode `load_harness_dir` parity) — verified by direct extension call (Turn 1 injects 13,665 chars; Turn 2 dedups).
- (b) `context` event surfaces the actual `lazy map` records + `lazy policy list` policies relevant to the files just touched — verified on the medivance worktree (PendingReservationsWidget → dashboard-pending BDD + 0017 ADR + 5 policies).
- review/gap-analysis turn-start driver in `on-message-received`.

## Open follow-ups (backlog)

1. **Live multi-turn OMP verification (host action).** All verification so far is
   simulation / direct extension call / `lazy test` 79/79 — NOT a live multi-turn
   OMP session. Re-run the worktree scenario ("attach instance 5 to test DB" type)
   in a FRESH OMP session (extension/hooks load at session start) and confirm:
   records-first (reads governing record before action), correct dev-cli usage,
   turn-end capture, selectable option gates, no advisory loop.

2. **dev-DB hard-stop decision — RESOLVED (user-confirmed 2026-06-25).** Git
   archaeology confirmed jcode NEVER had a dev-instance/DB hard-stop hook
   (`electron-vite`/`dev-cli`/`bun db` were never blocked in medivance or
   lazy-harness history). jcode's reliability for the dev-DB boundary came purely
   from `load_harness_dir` force-loading the grammar, which made the agent read
   the `named-dev-instance-workflow` + `db-environment-safety` records (organic),
   NOT from a hard-stop. The only hard blocks in either era are destructive-shell
   (`safe-guard.sh` → `check-destructive-command.py`) + commit-time `lazy test`.
   The 2026-06-01 hard-enforcement experiment (search/read-debt BLOCKING gates,
   commit `9411cbd`) was reverted the same day (ADR 0041). **Decision: no new
   dev-DB hard-stop.** grammar force-load (32c8986) is the true jcode-parity
   mechanism; verify it in a fresh session (item 1) first. A narrow L5 hard-stop
   remains an ADR 0041-sanctioned OPTION only if grammar-parity proves
   insufficient live — it would be NEW (beyond jcode), not a restoration.

## Discovery capture

- DDD: none (no domain term/business-rule change).
- SDD: updated — `pi-agent-package.md` (force-load + relevant-record surfacing + review driver).
- BDD: none (agent-grounding behavior, no user-visible flow record).
- TDD: updated — `pi-agent-package` context-injection self-test assertion (search/capture phrases).
- ADR: updated — `0051-jcode-parity-grammar-regrounding.md`.
- SSOT: none changed (`cli-tool-boundary`/`harness-enforcement-policy` remain authoritative; no tool-specific policy added).
- Planning: this record captures the two open follow-ups (live verification + M11 decision).
