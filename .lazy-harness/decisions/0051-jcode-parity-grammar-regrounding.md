# ADR 0051 - Jcode-Parity Grammar Re-Grounding for OMP/Pi (load_harness_dir Replacement)

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
- Applies when:
  - deciding how OMP/Pi keep agents grounded in `.lazy-harness` records across a turn
  - changing the `before_agent_start` reminder, the `context` re-grounding body, or the capture gates
  - diagnosing why an agent read source/tests and acted without consulting the governing record, or ended a turn without capturing decisions
- Must:
  - replicate jcode's full-grammar drive organically via lifecycle hooks: `on-message-received` turn-start reminder AND `on-context.sh` mid-turn re-injection after file-touching tool results
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
2. `on-context.sh` (Pi/OMP `context` event, fed the turn's `recent_tool_calls`) **runs `lazy map` on the touched paths and injects the ACTUAL matching `.lazy-harness/<layer>` record refs + `lazy policy list` operating policies** — jcode "instructions relevant to files just read/edited — read and follow" parity: SURFACE the records, not merely a "go look" reminder — leading with the relevant-record search (§2.1/§2.5) and turn-end capture (§2.4) mandates plus the interactive grammar (§0/§2.3). `index.ts` passes `recent_tool_calls` to the hook and wires `FILE_OP_TOOLS`/`pendingRegroundByRoot`/`regroundBodyByRoot` — one inject per new file-op batch, reset per turn, fail-open.
3. Keep the keyword-gated capture STOP gates (`check-analysis-discovery-capture.sh` needs ≥3 layer acronyms + plan cue; `check-user-correction-capture.sh` needs a current-turn correction + ack) **conservative**, and drive capture through the re-grounding reminder instead — **Option C**.

### Rejected alternatives

- **Tighten read-debt** to require `.lazy-harness`/`lazy map` evidence (reject bare `src/`/`tests/` reads). Rejected: breaks AGENTS §2.5 missing-record host-code/docs reads and the 2026-06-04 `pre-action-search-evidence-guard` false-deny protection; and jcode itself never tightened read-debt — its reliability was the grammar, not the guard.
- **Loosen the capture STOP gates** so natural-language learnings trigger them. Rejected: re-introduces the 3x advisory loop that 62fc284/069d603 fixed.

## Consequences

- `before_agent_start` force-loads the FULL `.lazy-harness/AGENTS.md` grammar into the system prompt once per session (jcode `load_harness_dir` parity) AND the `context` event surfaces the records/policies relevant to the files just touched — so agents have the full grammar present and see the relevant records mid-turn, closing the "read code → act / end without capturing" drift.
- **Honest remaining gap — advisory, not a hard block.** Grammar force-load (`load_harness_dir`) and relevant-record re-injection now match jcode. What is NOT ported is jcode's `response.completed` hard-block (M11): OMP/Pi enforcement stays advisory + bounded continuation per ADR 0041 (the user-confirmed organic decision). records-first reliability comes from the grammar + re-injection, not from M11, so this gap does not affect records-first behavior; a true hard block requires revisiting ADR 0041.
- Hooks and the extension load at session start, so these fixes take effect only in a **fresh session**; a running session keeps the pre-fix behavior.
- Capture is driven by reminder, not by the STOP gates, so natural-language learnings still depend on the agent recording them.

## Implementation map

- Status: implemented
- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-context.sh` — mid-turn re-grounding body (search §2.1/§2.5 + capture §2.4 + interactive grammar)
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — turn-start harness-first reminder
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — `context` handler, `FILE_OP_TOOLS`, `pendingRegroundByRoot`/`regroundBodyByRoot`, jcode-shape `agent_end` payload, `ensureAskToolActive`
- Key symbols:
  - `context` handler + `pendingRegroundByRoot` (`index.ts`) — one re-inject per file-op batch, reset per turn
  - re-grounding body phrases `NOT record-grounding` / `Capture before you finish` — search + capture mandates
- Commits: `1ccfd05` (re-grounding wiring), `62fc284` (jcode-shape agent_end payload), `791d659` (native `ask` option gates), `069d603` (option-gate-discipline false positives), `3617769` (relevant-record search mandate), `deb9d53` (turn-end capture mandate), `3bb06d5` (SDD record + fixture)
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py` — pi-package context-injection assertion checks the body carries `re-grounding`, `NOT record-grounding`, `Capture before you finish`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/pi-agent-package.md`
  - ADR: `.lazy-harness/decisions/0050-pi-omp-only-runtime.md` (decommission that removed `load_harness_dir`), `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` (organic, not hard-gate)
- Machine index:
  - generated index key: `pending until implementation-index generator exists`

## Rule placement

- Rule: OMP/Pi replicate jcode's full-grammar drive organically via `on-message-received` + `on-context.sh` re-grounding (relevant-record search + turn-end capture); read-debt is not tightened and capture STOP gates stay conservative; the guarantee is organic, not hard.
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

## 2026-06-25 amendment — intent-keyed capability surfacing (gap-2 narrowing)

The "honest remaining gap" above noted the `context` re-grounding is **path-triggered**: it surfaces records for the files touched, so an **intent-keyed** convention (a capability with `appliesWhen: <intent>`, e.g. `creating_pull_request → <host>-pr-body-template`) was not surfaced when the agent had not touched a related file — the observed failure where an OMP/Pi agent opened a PR by searching `.github/` templates and improvising instead of resolving the host PR-body capability.

Narrowed (still organic, not a hard guarantee): `on-context.sh` now also injects a compact **`lazy capability list`** catalog (`id (level): appliesWhen` per capability, capped) alongside `lazy policy list`, with the instruction to resolve the matching intent first (`lazy capability resolve --intent <intent>`). Deterministic catalog only — no user-text intent classification (cli-tool-boundary), no hard gate (ADR 0041), host-agnostic (lists whatever capabilities the host registry holds). Records-first reliability still depends on the agent acting on the surfaced catalog; this raises the salience of intent conventions, it does not force them.

- Code: `.lazy-harness/hooks/lifecycle/on-context.sh` (capability catalog block).
- SDD: `.lazy-harness/spec/platform/pi-agent-package.md` (Must bullet + impl map).
- TDD: `check_on_context_surfaces_capability_catalog` (`.lazy-harness/scripts/self-test.py`, FRAMEWORK_ONLY).
