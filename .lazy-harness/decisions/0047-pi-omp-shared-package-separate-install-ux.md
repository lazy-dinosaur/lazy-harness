# ADR 0047 — Pi and OMP share package core but use separate install UX

Status: accepted
Date: 2026-06-19

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Applies when:
  - installing or packaging lazy-harness for Pi and/or OMP runtimes
  - deciding install UX for Pi-only, OMP-only, or both
- Must:
  - keep one shared source package (`packages/lazy-harness-pi/`) with both `pi` and `omp` manifest sections
  - expose separate wrapper UX (`lazy pi install`, `lazy omp install`); default Pi install to global bootstrap
  - no-op the globally loaded extension when cwd does not resolve to a `.lazy-harness/bin/lazy` host root
- Must not:
  - depend on legacy `pi` manifest fallback for normal OMP operation
- Record completion:
  - changes to package manifest, install UX, or project activation update this ADR and `.lazy-harness/spec/platform/pi-agent-package.md`
- Related records:
  - `.lazy-harness/spec/platform/pi-agent-package.md`
  - `.lazy-harness/tests/pi-agent-package.md`
  - `.lazy-harness/planning/pi-omp-global-bootstrap-project-activation-plan.md`

## Context

The lazy-harness package originally targeted official Pi first. OMP can load Pi-style package manifests through fallback behavior, but OMP is a distinct fork/runtime with its own plugin install semantics. The user clarified that some users may install Pi only, OMP only, or both, so one implicit shared install path is not enough.

Official OMP source evidence shows package manifest resolution prefers `package.json#omp` and only then falls back to `package.json#pi`. OMP persistent local path install is exposed through `omp plugin install <path>` / `omp plugin uninstall <package>`, while one-run extension loading uses `omp -e <path>`. Official Pi uses `pi install`, `pi remove`, `pi list`, and `pi -e` with local/global settings semantics.

## Decision

Keep the first implementation as a shared source package under:

```text
packages/lazy-harness-pi/
```

but expose separate wrapper UX:

```bash
.lazy-harness/bin/lazy pi install --local
.lazy-harness/bin/lazy pi install --global
.lazy-harness/bin/lazy omp install
```

The shared package manifest must include both `pi` and `omp` resource sections. OMP should not depend on legacy `pi` fallback for normal operation.

## 2026-06-22 amendment — global bootstrap with project activation

User-confirmed next direction: package installation should behave as a runtime bootstrap, while actual lazy-harness behavior remains project-activated.

- Default install UX should move toward global/user-level bootstrap: `lazy pi install` installs the Pi package globally by default, and `lazy omp install` keeps OMP's plugin-registry install semantics.
- Project opt-in is represented by initialized project artifacts such as `.lazy-harness/bin/lazy` plus project-local prompt/config files.
- Non-harness projects must remain safe: the globally loaded extension no-ops when `ctx.cwd` does not resolve to a `.lazy-harness/bin/lazy` root.
- Long/static project instructions belong in project-local `.pi/APPEND_SYSTEM.md` and `.omp/APPEND_SYSTEM.md`; `before_agent_start` remains for short dynamic reminders and guard state only.
- Implementation plan: `.lazy-harness/planning/pi-omp-global-bootstrap-project-activation-plan.md`.

## Rationale

- Separate wrapper UX matches real user install modes: Pi-only, OMP-only, or both.
- Keeping one shared package avoids premature `packages/lazy-harness-omp` extraction while most extension code is still common.
- Explicit `package.json#omp` removes ambiguity and follows OMP's own manifest precedence.
- OMP package split remains available later if runtime smoke shows larger adapter divergence than wrapper/manifest differences.

## Consequences

- `.lazy-harness/scripts/pi-package.ts` becomes runtime-aware and dispatches Pi and OMP command arrays from the same source wrapper; Pi install defaults to global bootstrap while destructive remove keeps explicit scope.
- `.lazy-harness/bin/lazy` owns distinct `pi`, `omp`, and `agent activate` subcommands.
- Regression coverage must protect default Pi global install, explicit Pi local install, OMP wrapper dry-runs, non-harness no-op behavior, activation prompt files, and the explicit OMP manifest.
- Documentation must warn that OMP local path installs persist through OMP plugin registry semantics; use `lazy omp smoke` for non-persistent one-run loading.

## Implementation map

- `packages/lazy-harness-pi/package.json` — shared package manifest with `pi` and `omp` resource sections.
- `.lazy-harness/scripts/pi-package.ts` — runtime-aware wrapper for `lazy pi` and `lazy omp`; maps Pi to `pi install/remove/list/-e` and OMP to `omp plugin install/uninstall/list` plus `omp -e`.
- `.lazy-harness/bin/lazy` — dispatches separate `pi` and `omp` subcommands with `LAZY_AGENT_RUNTIME`, `LAZY_PI_TARGET_REPO`, and `LAZY_OMP_TARGET_REPO`.
- `.lazy-harness/scripts/agent-activate.ts` — writes project-local `.pi/APPEND_SYSTEM.md` / `.omp/APPEND_SYSTEM.md` activation prompt pointers and excludes `.pi/` / `.omp/` from team commits.
- `packages/lazy-harness-pi/README.md` — documents separate Pi and OMP install, smoke, doctor, remove commands and trust boundary.
- `.lazy-harness/spec/platform/pi-agent-package.md` — SDD contract for shared package plus separate wrapper UX.
- `.lazy-harness/tests/pi-agent-package.md` — regression contract for explicit `omp` manifest and OMP wrapper dry-runs.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — automated guard for Pi/OMP package manifest and wrapper command arrays.
