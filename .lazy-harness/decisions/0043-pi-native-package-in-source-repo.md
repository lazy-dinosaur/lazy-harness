# ADR 0043 — Pi native package lives in lazy-harness source repo

Status: accepted
Date: 2026-06-09

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Aliases:
  - Pi 패키지
  - pi package
  - 패키지 위치
  - lazy-harness-pi
- Applies when:
  - building, installing, or locating the Pi-native lazy-harness integration package
  - deciding where the Pi adapter package lives relative to the source repo
- Must:
  - keep the first Pi package in-repo at `packages/lazy-harness-pi/`, installed by local package path
  - have the extension locate the host root by walking up to `.lazy-harness/bin/lazy`
  - document the trust boundary because Pi extensions run with project extension permissions
- Must not:
  - publish to npm or split a standalone repo before the adapter stabilizes and runtime smoke passes
- Record completion:
  - changes to package location, install UX, or trust boundary update this ADR and `.lazy-harness/spec/platform/pi-agent-package.md`
- Related records:
  - `.lazy-harness/spec/platform/pi-agent-package.md`
  - `.lazy-harness/tests/pi-agent-package.md`
  - `.lazy-harness/planning/pi-agent-plugin-adapter.md`

## Context

The user wants to use Pi Coding Agent and confirmed option A: build a Pi-native lazy-harness package inside the current lazy-harness repository, then install it into Pi by local package path.

Research showed Pi supports package resources through `package.json#pi` and event hooks through TypeScript extensions. The package can bundle extensions, skills, and prompts without a separate repository.

## Decision

Keep the first Pi integration package in this repository under:

```text
packages/lazy-harness-pi/
```

Install locally with:

```bash
pi install -l /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --approve
```

The extension must locate the active host root from Pi's current working directory by walking upward to `.lazy-harness/bin/lazy`. Therefore the package can live in the source repo while operating against any initialized host that Pi is run from.

## Rationale

- A separate repo is premature while API and behavior are still being validated.
- Keeping the package in source keeps lazy lifecycle hook semantics, skills, prompts, and tests close to their canonical implementation.
- Pi supports local package paths, so no npm/git publication is needed for the first usable version.
- Later extraction to a standalone repo or npm package remains possible once the adapter is stable.
- A `lazy pi` wrapper is preferred for source-local install UX while the adapter stabilizes; npm publication remains deferred until official Pi and OMP runtime smoke pass.

## Consequences

- `packages/lazy-harness-pi` is framework-source only for now and self-test coverage is `FRAMEWORK_ONLY`.
- Downstream projects can install the source package by absolute path while the extension still operates on their local `.lazy-harness` checkout.
- The package README must document the trust boundary because Pi extensions run with project extension permissions.

## Implementation map

- Package manifest:
  - `packages/lazy-harness-pi/package.json` — Pi package declaration with `pi.extensions`, `pi.skills`, and `pi.prompts`.
- Extension:
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — maps Pi `before_agent_start`, `tool_call`, and `tool_result` events to lazy-harness lifecycle behavior.
- Package resources:
  - `packages/lazy-harness-pi/skills/*/SKILL.md` — Pi package skill wrappers copied from current Jcode skills.
  - `packages/lazy-harness-pi/prompts/lazy-harness.md` — Pi prompt reminder.
  - `packages/lazy-harness-pi/README.md` — install, smoke, trust boundary, and command documentation.
- Tests:
  - `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — static manifest/resource/bridge contract coverage.
- Installer wrapper:
  - `.lazy-harness/scripts/pi-package.ts` — safe source-local `lazy pi` wrapper for install/list/remove/smoke/doctor.
  - `.lazy-harness/bin/lazy` — dispatches `lazy pi ...`.
- Related records:
  - `.lazy-harness/spec/platform/pi-agent-package.md`
  - `.lazy-harness/tests/pi-agent-package.md`
  - `.lazy-harness/planning/pi-agent-plugin-adapter.md`
