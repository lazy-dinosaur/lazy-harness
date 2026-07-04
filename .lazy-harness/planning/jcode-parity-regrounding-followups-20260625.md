# Planning — Jcode-Parity Re-Grounding Follow-ups

Status: closed (2026-07-03 — live verification passed; steer re-ground follow-up shipped)
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
  - treat the items below as the completed verification trail for the full jcode-parity claim
- Must not:
  - re-open the full-parity question without new live counter-evidence

## Context

ADR 0051 restored jcode's two grounding mechanisms in the OMP/Pi extension and
shipped + synced them (commits `1ccfd05`/`62fc284`/`791d659`/`069d603`/`3617769`/
`deb9d53`/`3bb06d5`/`ce34f98`/`32c8986`):

- (1a) `before_agent_start` force-loads the full `.lazy-harness/AGENTS.md` grammar into the system prompt once per session (jcode `load_harness_dir` parity) — verified by direct extension call (Turn 1 injects 13,665 chars; Turn 2 dedups).
- (b) `context` event surfaces the actual `lazy map` records + `lazy policy list` policies relevant to the files just touched — verified on the medivance worktree (PendingReservationsWidget → dashboard-pending BDD + 0017 ADR + 5 policies).
- review/gap-analysis turn-start driver in `on-message-received`.

## Open follow-ups (backlog)

1. **Live multi-turn OMP/Pi verification — PASSED (2026-07-03).** Fresh Pi session on this
   host passed all six checks; evidence capsule:
   `.lazy-harness/evidence/2026-07-03-pi-jcode-parity-live-fresh-session-verification.md`.
   The "fully identical to the last jcode state" claim is now permitted.
   Original scenario (kept for re-runs): All verification before this was
   simulation / direct extension call / `lazy test` 79/79 — NOT a live multi-turn
   session. User-selected 2026-07-03: run the verification on THIS host (lazy-harness
   source repo) in a FRESH Pi session (extension/hooks load at session start).
   Scenario — give the fresh session a host-dependent multi-step task (e.g. "audit
   record-lint behavior and fix one host-owned digest issue") and confirm, in order:
   - turn 1 system prompt carries the FULL AGENTS.md grammar (§0–§2.5) once, plus the
     read-debt marker `status=armed`;
   - the agent runs `lazy map --overview` + drills into governing records BEFORE reading
     code (records-first), and mid-turn file-ops trigger the `context` re-grounding body
     with ACTUAL record refs (not a generic reminder);
   - an ambiguous decision point renders a native selectable `ask` option gate (not plain
     A/B/C text);
   - turn-end: new decisions/corrections are captured into `.lazy-harness/<layer>` records
     in the same turn;
   - any advisory continuation resolves within the bounded cap (no loop; max 2 same-body,
     1 chained).
   Evidence: record an evidence capsule per `lazy-evidence-capsule`; on pass, update this
   record and ADR 0051; only then may "fully identical to the last jcode state" be claimed.

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

3. **M11 gap framing corrected (2026-07-03, user-confirmed).** Git archaeology showed the
   generated jcode wiring registered `response.completed` `blocking = false` from its first
   version (`25573b0`, 2026-05-14) through the final pre-cutover state (`05c1c57^`);
   ADR 0016's `blocking = true` design was never emitted by the generator. Therefore the
   Pi `agent_end` advisory + bounded `followUp` path is parity-or-stronger versus the LAST
   jcode state, and the "M11 hard-block gap" applies only versus the original ADR 0016
   design. See the 2026-07-03 amendment in
   `.lazy-harness/decisions/0051-jcode-parity-grammar-regrounding.md`. Item 1 (live
   fresh-session verification) passed on 2026-07-03 — the full-parity claim is closed.

4. **Mid-turn steer delivery gap — FIXED (2026-07-03, user-confirmed Option A).** Dogfood
   showed Pi's default Enter (*steering*) delivers new instructions mid-turn, skipping
   `before_agent_start` (no fresh read-debt arming, no §2.1 reminder) — a path jcode never
   had (jcode delivered user messages only between turns; Pi Alt+Enter/followUp matches
   that). Fix: extension `input` handler transforms `streamingBehavior === "steer"` text
   with a steer re-ground reminder and forces the next `context` re-injection. See
   ADR 0051 2026-07-03 amendment 2; protected by `check_pi_package_layout_and_contract`
   (`steer re-ground` / `streamingBehavior` phrases).

## Discovery capture

- DDD: none (no domain term/business-rule change).
- SDD: updated — `pi-agent-package.md` (force-load + relevant-record surfacing + review driver).
- BDD: none (agent-grounding behavior, no user-visible flow record).
- TDD: updated — `pi-agent-package` context-injection self-test assertion (search/capture phrases).
- ADR: updated — `0051-jcode-parity-grammar-regrounding.md`.
- SSOT: none changed (`cli-tool-boundary`/`harness-enforcement-policy` remain authoritative; no tool-specific policy added).
- Planning: this record captures the verification trail; all items closed as of 2026-07-03 (live verification + M11 decision + steer re-ground fix).
