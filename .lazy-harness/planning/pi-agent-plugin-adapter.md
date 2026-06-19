# Pi Agent Plugin Adapter Plan

Status: implemented-initial
Created: 2026-06-09
Research bundle: `/home/lazydino/dev/pi-agent-research/lazy-harness-pi-plugin-research.md`

## Context

The user wants to use Pi Coding Agent and asked whether the current `.jcode`-specific lazy-harness wiring can become a Pi-native plugin/package.

Research cloned and inspected:

- `/home/lazydino/dev/pi-agent-research/pi-mono` — official Pi monorepo, canonical upstream for `@earendil-works/pi-coding-agent`.
- `/home/lazydino/dev/pi-agent-research/pi-autohooks` — Pi extension/hook examples and docs.
- `/home/lazydino/dev/pi-agent-research/Pi-YAML-Hooks` — YAML hook compatibility package targeting Pi `^0.74.0`.
- `/home/lazydino/dev/pi-agent-research/agent-pi` — real-world Pi package bundling extensions, skills, prompts, themes.
- Local installed Pi package: `/home/lazydino/.bun/install/global/node_modules/@earendil-works/pi-coding-agent`, version `0.74.0`.

## Decision

Create a Pi-native lazy-harness package rather than only copying `.jcode` files. The user selected option A on 2026-06-09: keep the first package inside this repository under `packages/lazy-harness-pi/` and install it into Pi by local path.

Implemented package shape:

```text
packages/lazy-harness-pi/
  package.json
  extensions/lazy-harness/index.ts
  skills/lazy-init/SKILL.md
  skills/lazy-doctor/SKILL.md
  skills/lazy-sync/SKILL.md
  skills/lazy-update/SKILL.md
  skills/lazy-test/SKILL.md
  prompts/lazy-harness.md
  README.md
```

The package should be installable by Pi through local path, git, or npm:

```bash
pi install /absolute/path/to/lazy-harness-pi
pi install -l /absolute/path/to/lazy-harness-pi
pi install git:github.com/lazy-dinosaur/lazy-harness-pi@<ref>
pi -e /absolute/path/to/lazy-harness-pi
```

## Mapping

| Jcode wiring | Pi package equivalent |
|---|---|
| `.jcode/AGENTS.md` and harness prompt | package prompt or extension `before_agent_start` append |
| `.jcode/skills/*/SKILL.md` | package `skills/*/SKILL.md` |
| `message.received` reminder | Pi `before_agent_start` event |
| `tool.execute.before` evidence guard | Pi `tool_call` event with `{ block: true, reason }` |
| tool event logs | Pi `tool_execution_*`, `tool_result`, `agent_end` events |
| `/jcode-init` | `lazy pi-init` plus optional Pi `/lazy-init` command |

## Required Pi APIs verified

Installed Pi `0.74.0` and upstream `0.79.0` both expose the necessary surfaces:

- package manifest under `package.json#pi`
- global/project extension directories
- package resources for `extensions`, `skills`, `prompts`, `themes`
- `before_agent_start` to modify system prompt or inject messages
- `tool_call` to block tool execution
- `resources_discover` to contribute dynamic skill/prompt paths
- `pi.registerCommand`, `pi.exec`, `ExtensionAPI`, `ExtensionContext`

## Implementation status

Initial implementation exists at `packages/lazy-harness-pi/`.

Validated/covered surfaces:

- Pi package manifest with `pi.extensions`, `pi.skills`, and `pi.prompts`.
- Native TypeScript extension mapping:
  - `before_agent_start` → `.lazy-harness/hooks/lifecycle/on-message-received.sh`
  - `tool_call` → `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh`
  - `tool_result` → recent evidence cache for lazy guard payloads
- Package skills copied from `.jcode/skills/*/SKILL.md`.
- Package prompt `prompts/lazy-harness.md`.
- Static self-test coverage via `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract`.

## Original implementation plan

1. Add `lazy pi-init` support beside `jcode-wiring.ts`, or create `pi-wiring.ts`.
2. Build a minimal package under a generated `.pi` or package root:
   - `package.json` with `keywords: ["pi-package"]`
   - `pi.extensions`, `pi.skills`, `pi.prompts`
3. Implement `extensions/lazy-harness/index.ts`:
   - locate `.lazy-harness/bin/lazy` from `ctx.cwd` by walking upward
   - on `before_agent_start`, inject concise `REMINDER. Harness-first...`
   - on `tool_call`, normalize Pi event payload to lazy lifecycle helper payload and call `check-read-debt-permit.py`
   - return `{ block: true, reason }` only for actual mutation evidence guard denials
   - expose `/lazy-map`, `/lazy-doctor`, `/lazy-test`, `/lazy-sync`, `/lazy-update`
4. Copy/adapt existing `.jcode/skills` into Pi skill directories.
5. Smoke test against local Pi `0.74.0` first:
   - `pi -e /path/to/package`
   - `pi install -l /path/to/package`
   - `pi list`
   - interactive mutation guard smoke
6. Then test with cloned upstream `0.79.0` from `pi-mono`.

## Compatibility notes

- Project-local `.pi` resources load only after project trust. If lazy-harness needs to affect trust, use global extension or CLI `-e` bootstrap.
- Pi tool names are `bash`, `read`, `edit`, `write`, `grep`, `find`, `ls`, not Jcode tool namespaces.
- Pi `tool_call` is a hard block surface, so keep recent lazy-harness relaxation: do not block read-only overview batch; only block mutation without root-bound evidence.
- Extensions run with full system permission. Package README must make trust boundary explicit.
- Native TypeScript extension is preferred. `Pi-YAML-Hooks` can be considered later as optional compatibility layer, not the primary implementation.

## Confirmed dual-support rollout (2026-06-19)

The user confirmed a dual-support rollout order:

1. **Phase 1: official Pi compatibility first.** Make `packages/lazy-harness-pi` accurately compatible with official Pi and validate the canonical Pi install/runtime path before relying on other forks.
2. **Phase 2: Oh My Pi / OMP compatibility second.** After Pi baseline is correct, verify the same lazy-harness package under OMP and add OMP-specific adapter fixes only if smoke tests prove they are needed.

Rationale:

- Official Pi remains the canonical baseline/fallback because ADR 0043, SDD, TDD, and current static self-test coverage are Pi-native.
- OMP is still a preferred daily-driver candidate because it has stronger built-in coding features, but it must not replace the Pi baseline until compatibility smoke passes.
- Dual support reduces risk: Pi proves core adapter correctness; OMP proves richer workflow compatibility.

Phase 1 implementation checklist:

- Confirm package manifest and resource loading under official Pi.
- Verify `before_agent_start` prompt/reminder injection.
- Verify `tool_call` mutation guard normalization, including shell aliases `cmd`, `command`, `shell`, and `terminal`.
- Verify `tool_result` evidence retention and recent-tool payload shape.
- Verify package commands `/lazy-map`, `/lazy-doctor`, `/lazy-test`, `/lazy-sync`, `/lazy-update`.
- Keep clean default behavior: no committed `.pi/settings.json`; install is explicit.

Phase 2 implementation checklist:

- Verify OMP can load legacy `pi.extensions` from `packages/lazy-harness-pi/package.json`.
- Verify OMP's `@earendil-works/pi-coding-agent` compatibility shim is enough for the current import.
- Verify OMP event payloads for `before_agent_start`, `tool_call`, and `tool_result` match what the bridge expects.
- Verify OMP command registration, `ctx.ui.notify`, and `pi.exec` behavior.
- Add OMP-specific manifest/docs/tests only after a failing smoke identifies a real incompatibility.

## Rule placement

- Rule: Pi/OMP support should be developed in two phases: official Pi compatibility first as canonical baseline/fallback, then OMP compatibility as daily-driver candidate.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/pi-agent-plugin-adapter.md`
- Why not AGENTS.md: this is a tooling rollout/evaluation sequence, not general agent prompt grammar.
- Why not `.jcode`: this is lazy-harness adapter strategy shared by hosts, not local/private Jcode preference.
- Confirmation: user-confirmed

## Implementation map

- Research bundle:
  - `/home/lazydino/dev/pi-agent-research/lazy-harness-pi-plugin-research.md` — consolidated external Pi package/plugin research.
- External source evidence:
  - `/home/lazydino/dev/pi-agent-research/pi-mono/packages/coding-agent/docs/extensions.md` — official extension docs.
  - `/home/lazydino/dev/pi-agent-research/pi-mono/packages/coding-agent/docs/packages.md` — official package docs.
  - `/home/lazydino/dev/pi-agent-research/pi-mono/packages/coding-agent/docs/skills.md` — official skill docs.
  - `/home/lazydino/dev/pi-agent-research/pi-mono/packages/coding-agent/docs/prompt-templates.md` — official prompt template docs.
  - `/home/lazydino/dev/pi-agent-research/pi-mono/packages/coding-agent/docs/development.md` — official development docs.
  - `/home/lazydino/dev/pi-agent-research/pi-mono/packages/coding-agent/src/core/extensions/types.ts` — extension event/API types.
  - `/home/lazydino/dev/pi-agent-research/pi-mono/packages/coding-agent/src/core/extensions/runner.ts` — event runner/block aggregation semantics.
  - `/home/lazydino/dev/pi-agent-research/agent-pi/package.json` — real package manifest example.
- Lazy-harness source to adapt later:
  - `.lazy-harness/scripts/jcode-wiring.ts` — current generated Jcode wiring source.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — current reminder hook semantics.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — mutation evidence guard to bridge from Pi `tool_call`.
  - `.jcode/skills/**/SKILL.md` — skill content to adapt to Pi package skills.
- Tests needed later:
  - package manifest parse test
  - Pi payload normalizer unit tests
  - local 0.74.0 extension smoke
  - lazy self-test coverage for `pi-wiring.ts`
  - official Pi Phase 1 runtime smoke covering startup, guard, evidence, and package commands
  - OMP Phase 2 runtime smoke covering legacy `pi.extensions`, import shim, events, commands, notify, and exec behavior

## Discovery capture

- DDD: none.
- SDD: candidate, Pi package/extension adapter contract needed.
- BDD: candidate, Pi session startup/tool-call behavior should mirror lazy-harness Jcode behavior.
- TDD: candidate, Pi package/extension smoke tests needed.
- ADR: candidate, if implementation is accepted, record a decision for native Pi package over YAML hooks.
- SSOT: candidate, Pi package install/update locations and trust model may need an SSOT.
- Planning: this record.
