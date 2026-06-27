# Planning — OMP plugin live-link fix (2026-06-27)

Status: implemented

## Rule digest

- Status: active
- Layer: Planning
- Scope: framework-global
- Applies when:
  - debugging why a downstream OMP/Pi host does not follow current `.lazy-harness` grammar (record-first, capture, re-grounding)
  - deciding how the Pi/OMP runtime plugin is updated across hosts
- Must:
  - install the OMP plugin with `omp plugin link <source-path>` (live dev-link), never `omp plugin install` (stale snapshot)
  - treat the runtime plugin as a SEPARATE update channel from `lazy sync` (which only updates `.lazy-harness/` Category A, not the installed plugin)
- Must not:
  - assume `lazy sync` propagates extension/grammar-drive changes to the runtime
- Related records:
  - `.lazy-harness/spec/platform/pi-agent-package.md`
  - `.lazy-harness/decisions/0051-jcode-parity-grammar-regrounding.md`
  - `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`

## Problem (dogfood)

A medivance-homepage OMP session answered a signup-flow question by reading `SignupStatusPages.server.tsx` directly, with no record-first search and no read/search-debt surfacing — the exact "read code → act without consulting the governing record" drift ADR 0051 targets.

## Root cause

Two-layer:

1. **Grammar drive** (ADR 0051): record-first under OMP/Pi depends on the extension force-loading the full `AGENTS.md` grammar at `before_agent_start` plus `on-context` mid-turn re-injection. jcode got this free via `load_harness_dir=true`; OMP/Pi replicate it organically in the installed extension.
2. **Delivery channel (the actual defect):** the OMP plugin was installed via `omp plugin install` = an **npm-style snapshot copied into `~/.omp/plugins/node_modules/@lazy-dinosaur/lazy-harness-pi`**, pinned at a pre-ADR-0051 build (no `pendingRegroundByRoot`/`regroundBodyByRoot`/`FILE_OP_TOOLS` markers). Pi, by contrast, was live-linked through `~/.pi/agent/settings.json` `packages: [source-path]` and already ran current code. `lazy sync` updates `.lazy-harness/` only, so the stale plugin never refreshed.

Also: package version stayed `0.1.0` across extension changes, so a version-based update would not have detected drift.

## Decision

Switch OMP to **live dev-link parity with Pi**:

- `omp plugin link <source-path>` creates a symlink (`~/.omp/plugins/node_modules/@lazy-dinosaur/lazy-harness-pi -> packages/lazy-harness-pi`), so the plugin tracks the source checkout live. Source change = instant propagation to all OMP hosts (the plugin install is user-global), no reinstall, no version bump.
- `lazy omp install` now maps to `omp plugin link` (was `omp plugin install`).

Live-link's only coupling — all OMP sessions track the source working tree's current state (incl. dirty edits/branch) — is the same coupling Pi already has; it is parity, not new risk.

## Resolution

- Relinked the global OMP plugin: `omp plugin uninstall` + `omp plugin link /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi`. Verified symlink → source and 11 ADR-0051 markers reachable.
- `.lazy-harness/scripts/pi-package.ts` — `commandForInstallLike` omp branch + help text now use `omp plugin link`.
- `.lazy-harness/spec/platform/pi-agent-package.md` — install contract documents live-link + snapshot pitfall.
- `packages/lazy-harness-pi/README.md` — install docs updated.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — assertions expect `omp plugin link`.

Takes effect on the next fresh OMP/Pi session (running sessions loaded the old plugin at start; restart required).

## Honest remaining gap

Even live-linked, record-first stays advisory (ADR 0041): the grammar force-load + re-injection nudge, they do not hard-block. A hard guarantee would require revisiting ADR 0041 (L5 hard-stop promotion), which the user previously rejected.

## Rule placement

- Rule: OMP plugin install = `omp plugin link` (live dev-link), parity with Pi; runtime plugin is a separate update channel from `lazy sync`.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/pi-agent-package.md`
- Confirmation: user-confirmed (chose live-link over snapshot + version-bump)

## Discovery capture

- DDD: none.
- SDD: `pi-agent-package.md` install contract updated to live-link.
- BDD: none (agent grounding behavior, not user UI).
- TDD: `check_pi_package_layout_and_contract` asserts `omp plugin link`.
- ADR: ADR 0051 (grammar drive) + ADR 0050 (Pi/OMP-only runtime) remain governing; no new ADR — this is a delivery-channel fix within the existing decision.
- SSOT: none.
- Planning: this record.

## Decision log (2026-06-27)

- M11-style hard completion gate (response.completed `blocking=true`) restoration was offered. User chose to **stay advisory** (keep ADR 0041) and **verify record-first in a fresh OMP session first** before considering any hard-gate restoration.
- Rationale: live-link restores the exact mechanism jcode used for record-first (always-loaded grammar + on-context re-injection — both advisory nudges, never a per-action hard block). jcode's only hard component was the M11 turn-end completion gate, which was deliberately dropped in ADR 0041 (user rejected hard gates as too slow). So advisory-first parity is the expected baseline; escalate to M11/L4 only if a fresh-session test still shows record-first misses.
