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
- Provide `lazy pi` wrapper commands for install/list/remove/smoke/doctor before relying on raw `pi install` commands.
- Verify `before_agent_start` prompt/reminder injection.
- Verify `tool_call` mutation guard normalization, including shell aliases `cmd`, `command`, `shell`, and `terminal`.
- Verify `tool_result` evidence retention and recent-tool payload shape.
- Verify source package path and target repo are separated for local install into other repos.
- Verify global install runtime state is root/session scoped so evidence from repo A does not leak into repo B.
- Verify package commands `/lazy-map`, `/lazy-doctor`, `/lazy-test`, `/lazy-sync`, `/lazy-update`.
- Keep clean default behavior: no committed `.pi/settings.json`; install is explicit.

Phase 2 implementation checklist:

- Verify OMP can load legacy `pi.extensions` from `packages/lazy-harness-pi/package.json`.
- Verify OMP's `@earendil-works/pi-coding-agent` compatibility shim is enough for the current import.
- Verify OMP event payloads for `before_agent_start`, `tool_call`, and `tool_result` match what the bridge expects.
- Verify OMP command registration, `ctx.ui.notify`, and `pi.exec` behavior.
- Add OMP-specific manifest/docs/tests only after a failing smoke identifies a real incompatibility.

## Confirmed installer wrapper staging (2026-06-19)

The user confirmed Option A for Pi install UX:

- Implement `lazy pi install/list/remove/smoke/doctor` first.
- Keep `packages/lazy-harness-pi` source-local for now.
- Defer npm package publication or standalone repo extraction until official Pi Phase 1 and OMP Phase 2 runtime smoke are stable.

Wrapper contract:

- `lazy pi install --local|--global [--dry-run]` maps to official `pi install` with the source package path.
- `lazy pi remove --local|--global [--dry-run]` maps to official `pi remove` with the source package path.
- `lazy pi list [--local|--global]` runs official `pi list` without mutating settings.
- `lazy pi smoke [--dry-run]` runs one-run load smoke via `pi -e <package> --help`; it never persists settings.
- `lazy pi doctor [--no-smoke] [--strict]` checks package layout, `pi --version`, `pi list`, and optional one-run smoke without mutating settings.
- Persistent install/remove require explicit `--local` or `--global`.

Isolation hardening added after user review:

- `lazy` captures a fresh invocation cwd and passes it as `LAZY_PI_TARGET_REPO` before changing to its own host root, so full-path wrapper calls from other repos or nested pre-commit lazy runs install into the caller repo. Direct `pi-package.ts` ignores stale parent `LAZY_INVOCATION_CWD` unless an explicit `--target-repo`/`LAZY_PI_TARGET_REPO` is supplied.
- `pi-package.ts` separates source root (`packages/lazy-harness-pi`) from target repo (`--target-repo`, `LAZY_PI_TARGET_REPO`, `LAZY_INVOCATION_CWD`, or cwd).
- Local install ensures the target repo's `.git/info/exclude` includes `.pi/` before writing project-local Pi settings.
- The Pi extension scopes recent tool evidence and active packet IDs by detected lazy root.

## Official Pi Phase 1 smoke closeout (2026-06-19)

Status: user-confirmed-pass
Confirmation: user reported that the previously listed official Pi wrapper/runtime checks all succeeded.

Closed Phase 1 scope:

- `lazy pi` wrapper diagnostics/install surface validated for the official Pi baseline.
- Official Pi package load/runtime path validated enough to move to Phase 2.
- Startup reminder injection, tool-call mutation guard normalization, tool-result evidence retention, source/target repo separation, root/session-scoped state, and package command surface are treated as Phase 1 pass by user confirmation.

Next active scope:

- Begin **Phase 2: Oh My Pi / OMP compatibility**.
- Verify OMP can load the existing `packages/lazy-harness-pi` package before adding OMP-specific code.
- Add OMP-specific manifest/docs/tests only if smoke tests prove a real incompatibility.
- Keep npm publication / standalone repo extraction deferred until OMP Phase 2 runtime smoke is stable.

Discovery capture:

- Planning: official Pi Phase 1 is closed by user-reported smoke success; OMP Phase 2 is the next active adapter work.
- SDD/TDD: no new contract or regression added in this closeout; future OMP failures should create/update adapter contract and smoke regression records.
- SSOT/ADR/DDD/BDD: no change.

## Rule placement

- Rule: Pi install UX should be stabilized through `lazy pi` wrapper commands first; npm/standalone publish remains deferred until official Pi and OMP runtime smoke are stable.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/pi-agent-plugin-adapter.md`
- Why not AGENTS.md: this is installer/distribution rollout planning, not prompt grammar.
- Why not `.jcode`: this is lazy-harness Pi package distribution strategy, not local/private Jcode preference.
- Confirmation: user-confirmed

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
  - `.lazy-harness/scripts/pi-package.ts` — `lazy pi` wrapper implementation for official Pi install/list/remove/smoke/doctor.
  - `.lazy-harness/bin/lazy` — dispatch surface for `lazy pi`; passes fresh `LAZY_PI_TARGET_REPO` for cross-repo and nested pre-commit local install.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — root-scoped Pi event bridge runtime state.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — current reminder hook semantics.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — mutation evidence guard to bridge from Pi `tool_call`.
  - `.jcode/skills/**/SKILL.md` — skill content to adapt to Pi package skills.
- Tests needed later:
  - package manifest parse test
  - Pi payload normalizer unit tests
  - local 0.74.0 extension smoke
  - lazy self-test coverage for `pi-wiring.ts`
  - lazy self-test coverage for `pi-package.ts` wrapper dry-runs and doctor no-smoke
  - lazy self-test coverage for source/target repo separation, `.pi/` git exclude, and root-scoped recent-tool evidence isolation
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

## OMP Phase 2 initial compatibility smoke (2026-06-19)

Status: implemented-initial

Read-only/runtime evidence:

- Installed official Pi binary: `pi 0.79.7` at `~/.bun/bin/pi`.
- Installed OMP binary: `omp/16.0.11` at `~/.bun/bin/omp`.
- `omp -e <packages/lazy-harness-pi> --help` accepts the package path without rejecting the legacy `pi.extensions` package layout.
- `omp -e <packages/lazy-harness-pi/extensions/lazy-harness/index.ts> --help` accepts the direct extension file path.
- OMP installed types show `before_agent_start` receives `systemPrompt: string[]` and returns `systemPrompt?: string[]`, while official Pi baseline remains compatible with string prompt handling.

Compatibility fix:

- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` now preserves both official Pi string `systemPrompt` values and OMP string-array prompt blocks.
- When OMP sends `systemPrompt: string[]`, the lazy reminder is appended as a new block instead of coercing the prompt array into a comma-joined string.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` now includes a fake OMP `before_agent_start` string-array smoke in addition to the official Pi string smoke.

Remaining OMP Phase 2 risk:

- The current non-mutating smoke covers package/extension path acceptance and event shape compatibility through local source/type evidence plus fake runtime tests.
- A full interactive/non-interactive OMP model run can still be performed later if needed, but should be treated as an environment/cost-bearing runtime smoke rather than a prerequisite for this code fix.

Discovery capture:

- SDD: `.lazy-harness/spec/platform/pi-agent-package.md` updated with OMP string-array system prompt compatibility contract.
- TDD: `.lazy-harness/tests/pi-agent-package.md` updated with `omp_before_agent_start_system_prompt_array` regression.
- Planning: this OMP Phase 2 initial smoke section records the runtime evidence and remaining risk.
- DDD/BDD/ADR/SSOT: no new domain, behavior, decision, or source-of-truth change beyond the SDD/TDD contract.

## Rule placement

- Rule: OMP Phase 2 compatibility should add OMP-specific adapter fixes only after runtime/source evidence proves a real mismatch; the current proven mismatch is string-array `systemPrompt` preservation during `before_agent_start`.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/pi-agent-plugin-adapter.md`
- Why not AGENTS.md: this is rollout and runtime-smoke planning, not prompt grammar.
- Why not `.jcode`: this is shared Pi/OMP adapter work, not local/private Jcode preference.
- Confirmation: inferred-from-runtime-evidence

## OMP doc-read / same-experience hook surface investigation (2026-06-19)

Status: candidate-next

User observation:

- Pi appears to inject and honor the lazy-harness reminder correctly.
- OMP can load the extension, but user-observed behavior suggests it may still answer without doing the desired lazy-harness document/read step.

Read-only OMP runtime evidence from installed `@oh-my-pi/pi-coding-agent` 16.1.1:

- CLI supports `--hook=<value>` and `-e, --extension=<value>`.
- OMP extension events include `before_agent_start`, `context`, `before_provider_request`, `after_provider_response`, `tool_call`, `tool_result`, `turn_start`, `turn_end`, `message_start/update/end`, `agent_start/end`, and `session_stop`.
- `before_agent_start` extension result can inject a custom message and can replace/append system prompt blocks. Current lazy-harness extension uses system prompt injection only.
- `context` event fires before each LLM call and can return modified model messages. This is a strong candidate for ensuring read-debt context is actually in the provider payload.
- OMP hook subsystem exists separately from extensions. Hook modules are discovered via the `hooks` capability and can subscribe to `before_agent_start`, `context`, `tool_call`, `tool_result`, `turn_start`, `turn_end`, and more.
- Hook `before_agent_start` can inject a persisted, visible custom message into the session.
- `session_stop` event result supports `{ continue: true, additionalContext }` or `{ decision: "block", reason }`, which OMP converts into a hidden next-turn continuation. This is the closest equivalent to Jcode `response.completed` hard-stop/continuation behavior.
- Tool hard block remains available through `tool_call` returning `{ block: true, reason }`.

Implication:

- The red OMP command block in the UI is not by itself proof of failure. It appears to be a command/hook output block. Failure should be determined from exit code/error, not block color.
- The existing extension reminder is not enough to guarantee identical experience if the model ignores it.
- The likely next implementation should add an OMP-specific enforcement layer using `context` and/or `before_agent_start` custom message injection, plus optional `session_stop` continuation for post-response rule debt.

Recommended implementation order:

1. Add OMP-compatible read-debt context injection to the lazy-harness package using `context` or `before_agent_start` custom messages, so the provider sees concrete lazy-harness evidence rather than only a reminder.
2. Preserve the current `tool_call` mutation/evidence hard block.
3. Add `session_stop` continuation only if OMP needs post-response parity with Jcode's response-completed gate.
4. Add fake runtime/self-test coverage for OMP `context` and `session_stop` handlers before relying on direct interactive OMP behavior.

Discovery capture:

- SDD: candidate, Pi/OMP adapter contract should expand beyond reminder-only injection to OMP read-debt context injection.
- BDD: candidate, OMP user-visible behavior should match Pi/Jcode: host-specific answers must be preceded by lazy-harness evidence read/context.
- TDD: candidate, add fake OMP runtime tests for `context` message injection and optionally `session_stop` continuation.
- Planning: this section.
- DDD/ADR/SSOT: none yet.

## Rule placement

- Rule: OMP parity should use OMP-native hooks/events to provide the same lazy-harness read-debt experience as Pi/Jcode; reminder-only injection is insufficient if the model can ignore it.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/pi-agent-plugin-adapter.md`
- Why not AGENTS.md: this is OMP adapter implementation planning, not general prompt grammar.
- Why not `.jcode`: this is shared Pi/OMP package behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed goal, implementation pending

## OMP official source-of-truth reset (2026-06-19)

Status: user-confirmed direction

User correction:

- OMP is a fork of Pi, but OMP must not be treated as a transparent Pi package/runtime clone.
- Pi already worked with the earlier package behavior; the later `0e78c0c` same-experience/context-visible-message change was not required for Pi and caused visible-message side effects.
- OMP compatibility must be re-derived from OMP official docs and OMP official repository/source, with official Pi used only as a comparison baseline.

Current repository state after correction:

- Reset to `origin/feature/map-first-record-navigation` / `b7b0f3b`.
- Removed unpushed `0e78c0c Inject OMP read-debt context in Pi adapter` and dirty OMP manifest/doc/test changes.
- Kept prior validated commits up to `b7b0f3b`, including OMP hook-surface investigation and OMP string-array systemPrompt compatibility.

Next investigation contract:

1. Clone or inspect official OMP repo/docs from package metadata (`https://github.com/can1357/oh-my-pi`, package directory `packages/coding-agent`) before changing the lazy-harness adapter.
2. Clone or inspect official Pi repo/docs from package metadata (`https://github.com/earendil-works/pi`, package directory `packages/coding-agent`) only as a comparison baseline.
3. Identify OMP package loading, extension discovery, hook/event payloads, and install semantics from official OMP evidence rather than from Pi assumptions.
4. Only after that evidence exists, make the minimum OMP-specific adapter/setup change.
5. Preserve Pi's current working behavior unless a Pi-specific regression is proven.

Discovery capture:

- SDD: candidate, Pi/OMP adapter contract needs an OMP official-source-first source-of-truth clause.
- TDD: candidate, add regression that Pi does not receive visible OMP-only read-debt custom messages unless a Pi runtime explicitly supports/needs them.
- Planning: this section.
- DDD/BDD/ADR/SSOT: none yet.

## Rule placement

- Rule: OMP compatibility work must be based on OMP official docs/repository/source first, with official Pi used only as a comparison baseline; do not infer OMP package loading or hook behavior from Pi fallback behavior.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/pi-agent-plugin-adapter.md`
- Why not AGENTS.md: this is adapter investigation workflow, not global prompt grammar.
- Why not `.jcode`: this is shared Pi/OMP package behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed
