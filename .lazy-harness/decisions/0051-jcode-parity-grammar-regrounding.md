# ADR 0051 - Pi/OMP Grammar Re-Grounding (Historical Jcode-Parity Origin)

Status: accepted
Date: 2026-06-25
Layer: ADR
Related SDD: `.lazy-harness/spec/platform/pi-agent-package.md`, `.lazy-harness/spec/platform/search-read-debt-contract.md`, `.lazy-harness/spec/platform/option-gate-discipline.md`
Related SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`, `.lazy-harness/ssot/cli-tool-boundary.md`
Related TDD: `.lazy-harness/tests/pi-agent-package.md`, `.lazy-harness/tests/pre-action-search-evidence-guard.md`
Related ADR: `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`, `.lazy-harness/decisions/0007-agents-md-injection.md`, `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`, `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`, `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Aliases:
  - Pi OMP grammar grounding
  - grammar 재접지
  - load_harness_dir 대체
- Applies when:
  - deciding how OMP/Pi keep agents grounded in `.lazy-harness` records across a turn
  - changing the `before_agent_start` reminder, the `context` re-grounding body, or the capture gates
  - diagnosing why an agent read source/tests and acted without consulting the governing record, or ended a turn without capturing decisions
- Must:
  - keep the proven full-grammar drive organically via `on-message-received` at turn start and one bounded `on-context.sh` reminder after the first successful file-operation batch of each normal turn; later same-turn file operations must not restart re-grounding
  - keep the `on-context.sh` body forcing relevant-record search (reading code/tests is NOT record-grounding; `lazy map` + governing `.lazy-harness/<layer>` record before action, §2.1/§2.5) and turn-end capture (decisions/user-corrections/repeated-mistake-fixes/host-learnings → record, §2.4)
  - keep the keyword-gated capture STOP gates conservative and drive capture through re-grounding (Option C)
  - state honestly that this is organic (advisory reminder), not a hard guarantee
- Must not:
  - tighten the generic read-debt guard to require `.lazy-harness`/`lazy map` evidence (breaks §2.5 missing-record host-code reads and the pre-action-search-evidence-guard false-deny protection; jcode never tightened read-debt)
  - loosen `check-analysis-discovery-capture.sh` / `check-user-correction-capture.sh` triggers to fire on natural-language learnings (re-introduces the 3x advisory loop)
  - claim hard parity with jcode's config-forced grammar load
- Record completion:
  - changes to the re-grounding bodies, capture-gate sensitivity, or the context handler update this ADR plus `pi-agent-package.md` SDD/TDD
- Related records:
  - `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - `.lazy-harness/spec/platform/pi-agent-package.md`

## Context

Jcode (ADR 0007, superseded by ADR 0050) loaded the harness grammar through generated `.jcode/config.toml` with `load_harness_dir = true` and `load_jcode_agents = true`: the jcode runtime **force-loaded the full `.lazy-harness/AGENTS.md` grammar into every session's system prompt**, and natively re-injected "the AGENTS/.jcode instructions relevant to files just read/searched/edited this turn — read and follow them" after each file operation. The agent therefore always had §2.1 (mandatory record search), §2.4 (capture), and §2.5 (default-unknown) in front of it, and re-saw the relevant-record mandate every time it touched files.

ADR 0050 decommissioned jcode. OMP/Pi load `.lazy-harness/AGENTS.md` as a context file plus a compact `on-message-received` reminder plus an activation pointer, **once at session start**. There is no `load_harness_dir` equivalent that force-injects the full grammar every session, and no native mid-turn re-injection. Consequence (observed in dogfood): on a long turn the agent reads source/tests directly and acts — e.g. runs a raw `electron-vite dev` (main DB) instead of consulting `named-dev-instance-workflow.md`/`db-environment-safety.md` and using the `--test --instance` wrapper — and ends turns without capturing decisions/corrections into records.

The generic read-debt guard (`check-read-debt-permit.py`) was never the relevant-record enforcer: it is satisfied by any root-bound read (incl. `src/`/`tests/`) within a 2h TTL, and at the known-good baseline (504a9437) it was even more lenient (grep/glob/lsp counted). Jcode's reliability came from the always-present, continuously re-injected grammar — not the guard.

## Decision

Replicate jcode's grammar drive **organically through the lifecycle hooks**, with no read-debt tightening and no runtime change:

1. `on-message-received` (`before_agent_start`) — the extension **force-loads the FULL `.lazy-harness/AGENTS.md` grammar (§0–§2.5) into the system prompt once per session (jcode `load_harness_dir` parity, deduped by the `Lazy-Harness AI` title marker, fail-open)** — and the hook carries the turn-start harness-first search/read-debt reminder, map-first protocol, interactive grammar, and a **review/gap-analysis driver**: on a "what is missing/undecided/incomplete"/audit request, enumerate `lazy policy list` + `lazy capability list` and map the governing records BEFORE reading code (AGENTS §1/§2.1).
2. `on-context.sh` (Pi/OMP `context` event, fed the turn's `recent_tool_calls`) runs `lazy map` on touched paths and injects actual matching records plus operating guidance. `index.ts` collapses all successful file operations before the first callback into one batch and injects at most once per normal turn; a cached body suppresses later same-turn retriggers. Fresh `before_agent_start` and explicit steer epochs reset the boundary. Missing/failed/empty context hooks fail open for that callback but retain pending state for a later context retry. Catalog enumeration is discovery-only and already-resolved source guidance must not trigger another resolver chain.
3. Keep the keyword-gated capture STOP gates (`check-analysis-discovery-capture.sh` needs ≥3 layer acronyms + plan cue; `check-user-correction-capture.sh` needs a current-turn correction + ack) **conservative**, and drive capture through the re-grounding reminder instead — **Option C**.

### Rejected alternatives

- **Tighten read-debt** to require `.lazy-harness`/`lazy map` evidence (reject bare `src/`/`tests/` reads). Rejected: breaks AGENTS §2.5 missing-record host-code/docs reads and the 2026-06-04 `pre-action-search-evidence-guard` false-deny protection; and jcode itself never tightened read-debt — its reliability was the grammar, not the guard.
- **Loosen the capture STOP gates** so natural-language learnings trigger them. Rejected: re-introduces the 3x advisory loop that 62fc284/069d603 fixed.

## Consequences

- `before_agent_start` force-loads the FULL `.lazy-harness/AGENTS.md` grammar into the system prompt once per session (jcode `load_harness_dir` parity) AND the `context` event surfaces the records/policies relevant to the files just touched — so agents have the full grammar present and see the relevant records mid-turn, closing the "read code → act / end without capturing" drift.
- **Honest remaining gap — advisory, not a hard block.** Grammar force-load (`load_harness_dir`) and relevant-record re-injection now match jcode. What is NOT ported is jcode's `response.completed` hard-block (M11): OMP/Pi enforcement stays advisory + bounded continuation per ADR 0041 (the user-confirmed organic decision). records-first reliability comes from the grammar + re-injection, not from M11, so this gap does not affect records-first behavior; a true hard block requires revisiting ADR 0041.
- Hooks and the extension load at session start, so these fixes take effect only in a **fresh session**; a running session keeps the pre-fix behavior.
- Capture is driven by reminder, not by the STOP gates, so natural-language learnings still depend on the agent recording them.


## 2026-06-28 amendment — proactive map-first in mid-turn re-grounding

- Trigger: dogfood — on a later-turn audit the agent read a known spec then dove into code without running `lazy map --overview` first. Root cause: the proactive map-first protocol AND the review/audit driver ("map governing records FIRST, then read code") lived only in the turn-start `on-message-received` reminder, which is **once-per-session** (`before_agent_start` dedup). The `context` mid-turn body was **reactive** (records for files already touched) and never re-asserted proactive map-first — so on later turns the record-first push faded and agents leaned code-first.
- Change: `on-context.sh` MANDATE keeps the proactive **"Map-first BEFORE reading/editing more"** bullet, but ADR 0048's 2026-08-18 correction bounds delivery to one successful reminder per normal turn rather than every file operation. This preserves record-first visibility without fragmenting a coherent edit loop.
- Protection: `check_on_context_surfaces_operating_rule_catalog` asserts the `Map-first BEFORE reading/editing more` phrase in the on-context body.
- Still organic/advisory (ADR 0041), not a hard block; takes effect in a fresh session.

## 2026-07-03 amendment — M11 hard-block was already advisory in the LAST jcode state (gap framing corrected)

- Trigger: user asked whether Pi now matches the last jcode-only state; git archaeology re-verified the actual M11 endgame.
- Finding (git-verified):
  - ADR 0016 (2026-05-11) designed `response.completed` as a PRIMARY blocking gate (`blocking = true`), but the generated jcode wiring (`25573b0`, 2026-05-14, first `jcode-wiring.ts`) registered it `blocking = false` from its very first version and NEVER emitted `blocking = true`.
  - The 2026-06-01 hard-gate restoration experiment (`50477fa`, reverted same day by `9411cbd`/ADR 0041) also kept `response.completed` `blocking = false`.
  - The last jcode state before the Pi cutover (`05c1c57^`, 2026-06-24) registered: `check-bash.sh blocking=true`, `response.completed blocking=false (5000ms)`, `message.received blocking=true (800ms, fail-open)`, `log-tool.sh blocking=false`.
  - `.lazy-harness/ssot/harness-enforcement-policy.md` already recorded this: "current generated Jcode wiring uses `blocking = false`, weakening the original completion-audit contract".
- Correction: the "Honest remaining gap" consequence above compares against the ORIGINAL ADR 0016 design, not the final jcode state. Measured against the LAST jcode state, the Pi `agent_end` advisory + bounded `followUp` continuation path is at parity or stronger — do not treat the M11 hard-block as a missing jcode feature; re-introducing it would be NEW enforcement (ADR 0041 L5 promotion), not a restoration.
- Related context (same audit): the graph CLI rollback (`504a943`, the known-good baseline referenced above) and the birth of `packages/lazy-harness-pi` both happened in the 2026-06-08..15 window; the literal pre-graph commit (`da6417b`) predates the Pi adapter entirely, which is why the rollback was surgical rather than a branch reset (`.lazy-harness/planning/graph-cli-rollback-plan.md`).
- Remaining gate for a "fully identical to jcode" claim: only the live fresh-session multi-turn verification (`.lazy-harness/planning/jcode-parity-regrounding-followups-20260625.md` item 1). **CLOSED 2026-07-03**: live fresh Pi session passed all six checklist items — evidence: `.lazy-harness/evidence/2026-07-03-pi-jcode-parity-live-fresh-session-verification.md`.

## 2026-07-03 amendment 2 — mid-turn steer re-grounding (delivery-semantics parity)

- Trigger: dogfood — the user observed that when a new instruction is sent mid-turn via Pi's default Enter (*steering*), the agent absorbs it without record search. jcode delivered user messages only BETWEEN turns (follow-up semantics), so this path did not exist under jcode.
- Root cause (code + Pi docs verified): a steered message is delivered inside the running agent loop and does NOT re-fire `before_agent_start` — no fresh read-debt arming and no turn-start §2.1 reminder for the new instruction; the previous topic's armed read-debt packet keeps the action guard satisfied, so the new topic proceeds ungrounded. Pi `input` events expose `streamingBehavior: "steer"` for exactly this case; Alt+Enter (`followUp`) already matches jcode delivery.
- Change: the extension `input` handler transforms steered user text (non-extension source, non-empty) by appending a compact steer re-ground `<system-reminder>` (map-first for the NEW topic; prior-turn evidence/approvals may be stale per ADR 0038) and sets `pendingRegroundByRoot` (clearing the cached body) so the next `context` call re-injects the harness re-grounding.
- Boundary kept: organic/advisory (ADR 0041) — no blocking, no user-text classification (the reminder is static transport; the LLM judges topic novelty), fail-open for empty/extension inputs.
- Protection: `check_pi_package_layout_and_contract` asserts `steer re-ground` / `streamingBehavior` in the extension source.
- Takes effect in a fresh session (extension loads at session start).

## 2026-08-18 amendment — cadence bounded after Medivance dogfood

- Medivance exposed that literal post-file-op parity was counterproductive in Pi: every micro-edit/search triggered another full reminder and restarted record/capability discovery.
- ADR 0048 now owns the correction: at most one successful `context` reminder per normal turn, with pre-context file operations collapsed; fresh turns and explicit steers reset the boundary.
- Fail-open remains, but failed/empty context hooks keep pending state so a later context callback can retry. Pending clears only after a valid body exists.
- Exact source guidance rendered by the helper is already resolved. The generic catalog is discovery-only and must not cause broad manual resolver chains.
- Protection lives in `check_pi_package_layout_and_contract` and `.lazy-harness/tests/pi-agent-package.md`.

## 2026-08-19 amendment — parity yields to bounded work-unit grounding

- Trigger: live Pi dogfood showed that once-per-turn parity was still too expensive: ordinary follow-ups and reads repeatedly injected map/record/catalog instructions and caused the model to reread unchanged evidence.
- Decision: preserve the full grammar once per runtime session, but replace per-turn/file-read re-grounding with work-unit evidence reuse. Pi/OMP cache one successful overview plus directly read governing-record hashes; normal messages reuse valid hashes without another system-prompt body.
- Context: reads/searches never trigger `on-context.sh`. The first successful mutation may trigger one five-line pointer-only reminder. The hook performs no map, catalog, record-list, or resolver subprocess.
- Steering: an explicit non-extension steer clears work-unit fingerprints and writes one fresh grounding packet inline; it does not schedule a second context reminder.
- Rationale: jcode delivery parity is subordinate to ADR 0041’s organic/fast requirement. Replaying full grammar/catalog state is not correctness evidence and became a measured token-cost regression.
- Protection: prompt-budget <=300, Pi reuse/record-drift/steer fixtures, and mutation-only context retry.

## Implementation map

- Status: implemented
- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-context.sh` — five-line pointer-only mutation-boundary reminder.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — pointer-only first-grounding packet.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — `workUnitEvidenceByRoot`, governing-record hashes, `REGROUND_MUTATION_TOOLS`, explicit-steer reset, canonical lifecycle `agent_end`, trace, and native ask support.
- Key symbols:
  - `observeWorkUnitEvidence` / `workUnitEvidenceValid` — recognize overview + direct governing-record reads and verify hashes before later-turn reuse.
  - `context` handler + `pendingRegroundByRoot`/`regroundBodyByRoot` — mutation-only pointer injection with retry, not per-read re-grounding.
  - `agentEndTracePath` / `writeAgentEndTrace` — opt-in runtime-root diagnostics that preserve payload and continuation semantics
- Commits: `1ccfd05` (re-grounding wiring), `62fc284` (jcode-shape agent_end payload), `791d659` (native `ask` option gates), `069d603` (option-gate-discipline false positives), `3617769` (relevant-record search mandate), `deb9d53` (turn-end capture mandate), `3bb06d5` (SDD record + fixture)
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py` — pi-package assertions protect re-grounding plus canonical lifecycle `agent_end` projection and content-free trace behavior
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/pi-agent-package.md`
  - ADR: `.lazy-harness/decisions/0050-pi-omp-only-runtime.md` (decommission that removed `load_harness_dir`), `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` (organic, not hard-gate)
- Machine index:
  - graph ids: `kg_pi_agent_end_structural_trace_impl_20260714`,
    `kg_pi_agent_end_structural_trace_test_20260714`,
    `kg_pi_context_once_per_turn_20260818`
  - generated index key: `pending until implementation-index generator exists`

## Rule placement

- Rule: OMP/Pi keep the full grammar live through turn-start grounding plus at most one successful mid-turn context reminder per normal turn. File operations before the first callback collapse; later same-turn operations do not re-trigger; failed hooks may retry; explicit steer starts a fresh evidence boundary. Read-debt is not tightened and capture STOP gates stay conservative.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0051-jcode-parity-grammar-regrounding.md`
- Why not AGENTS.md: runtime/extension behavior decision with source/tests and an implementation map; AGENTS.md carries only the compact grammar.
- Why not local notes: framework source synced to all hosts, not Pi/OMP local/private.
- Confirmation: user-confirmed

## Discovery capture

- DDD: none (no domain term change).
- SDD: `pi-agent-package.md` updated (on-context search+capture mandate in Must bullet + impl map).
- BDD: none (no visible-flow record; the behavior is agent grounding, not user UI).
- TDD: `pi-agent-package.md` context-injection self-test assertion extended for the search+capture mandate phrases.
- SSOT: none changed; `cli-tool-boundary.md`/`harness-enforcement-policy.md` remain authoritative (no tool-specific policy added).
- Planning: none (decision recorded here; live fresh-session verification pending).

## Discovery capture — Pi agent-end trace

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: updated in `pi-agent-package.md`; this ADR's implementation map only gained the verified diagnostic symbols.
- BDD: none because normal agent behavior is unchanged.
- TDD: updated in `pi-agent-package.md` and `self-test.py`.
- ADR: none semantic because the opt-in trace does not change the accepted runtime decision.
- SSOT: updated in `runtime-and-shared-state.md` for the runtime-only path.
- Planning: updated in the analysis-discovery capture backlog; fresh source-linked trace passed and current remediation was user-closed without changing runtime semantics.

## Discovery capture — 2026-08-18 cadence correction

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: updated in `.lazy-harness/spec/platform/pi-agent-package.md`.
- BDD: none because no independent product flow changed.
- TDD: updated in `.lazy-harness/tests/pi-agent-package.md` and the Pi fake runtime.
- ADR: updated here and in ADR 0048 because the former per-file-op parity cadence was narrowed after dogfood evidence.
- SSOT: none because no policy/capability ownership or schema changed.
- Planning: updated in `.lazy-harness/planning/workflow-churn-reduction-plan.md`.
