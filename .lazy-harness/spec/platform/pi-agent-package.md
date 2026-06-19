# Pi Agent Package Contract

Status: active
Layer: SDD

## Purpose

Provide a Pi Coding Agent package that installs lazy-harness behavior into Pi without a separate repository.

## Package root

```text
packages/lazy-harness-pi/
```

This package is framework-source owned. It is installed into Pi by local path and locates the active host root at runtime.

## Manifest contract

`packages/lazy-harness-pi/package.json` must include:

```json
{
  "name": "@lazy-dinosaur/lazy-harness-pi",
  "keywords": ["pi-package"],
  "pi": {
    "extensions": ["./extensions"],
    "skills": ["./skills"],
    "prompts": ["./prompts"]
  }
}
```

## Extension contract

`packages/lazy-harness-pi/extensions/lazy-harness/index.ts` must:

1. export a default Pi extension function,
2. walk upward from `ctx.cwd` to find `.lazy-harness/bin/lazy`,
3. handle `before_agent_start` by invoking `.lazy-harness/hooks/lifecycle/on-message-received.sh` through stdin JSON and appending the returned reminder body to the system prompt,
4. handle `tool_call` by normalizing Pi tool payload into lazy lifecycle JSON and invoking `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh`,
5. return `{ block: true, reason }` only when the lazy hook emits a deny reason,
6. handle `tool_result` by retaining recent tool evidence for later guard invocations,
7. register convenience commands: `/lazy-map`, `/lazy-doctor`, `/lazy-test`, `/lazy-sync`, `/lazy-update`.

Pi shell aliases `cmd`, `command`, `shell`, and `terminal` must normalize to lazy `bash` before the guard runs. Otherwise shell actions can bypass read-debt enforcement because the canonical helper classifies `bash` as an action tool.

## Install contract

Clean default:

The source checkout must not require active Pi installation settings. After a factory reset, `~/.pi/agent/` and project-local `.pi/settings.json` may be absent. The package remains installable from source, but it is not installed by default.

Recommended wrapper commands:

```bash
.lazy-harness/bin/lazy pi install --local
.lazy-harness/bin/lazy pi install --global
.lazy-harness/bin/lazy pi list
.lazy-harness/bin/lazy pi smoke
.lazy-harness/bin/lazy pi doctor
.lazy-harness/bin/lazy pi remove --local
.lazy-harness/bin/lazy pi remove --global
```

The wrapper keeps the package path consistent, requires explicit `--local` or `--global` for persistent install/remove, supports `--dry-run` for install/remove/smoke, and intentionally defers npm/standalone publishing until official Pi and OMP runtime smoke are stable.

Global install for all Pi projects:

```bash
pi install /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --no-approve
```

This creates/writes user-global Pi settings:

```json
{
  "packages": ["../../dev/lazy-harness/packages/lazy-harness-pi"]
}
```

Global install is required when Pi is used from multiple existing projects. Project-local install only affects the current repository.

Project-local install:

```bash
pi install -l /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --approve
```

This creates/writes source-repo project-local Pi settings:

```json
{
  "packages": ["../packages/lazy-harness-pi"]
}
```

Project-local `.pi/settings.json` is generated only when intentionally attaching this checkout. It must not be committed as the default clean state.

One-run smoke:

```bash
pi -e /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --help
```

## Boundaries

- The extension is a bridge, not a duplicate policy engine.
- The canonical prompt/runtime behavior remains in `.lazy-harness/hooks/lifecycle/**` and `.lazy-harness` records.
- Pi `tool_call` is a hard-block surface; the extension must preserve the recent relaxed policy by blocking only actual mutation/evidence guard denials.
- Read-only overview batch/parallel behavior must not be blocked by this package.
- Pi shell aliases `cmd`, `command`, `shell`, and `terminal` must not bypass the guard.
- Because Pi extensions run with project extension permissions, package README must document the trust boundary.

## Implementation map

- `packages/lazy-harness-pi/package.json` — Pi package manifest.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — event bridge implementation.
- `packages/lazy-harness-pi/skills/*/SKILL.md` — skills exposed to Pi.
- `packages/lazy-harness-pi/prompts/lazy-harness.md` — prompt template.
- `packages/lazy-harness-pi/README.md` — install/smoke/trust docs.
- `.lazy-harness/scripts/pi-package.ts` — `lazy pi` install/list/remove/smoke/doctor wrapper around official Pi commands.
- `.lazy-harness/bin/lazy` — dispatches `lazy pi ...` to `pi-package.ts`.
- `.pi/settings.json` — optional source-repo Pi local package attachment created by `pi install -l`; not committed by default.
- `~/.pi/agent/settings.json` — optional user-global package attachment created by `pi install` so all existing Pi projects load the extension.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — static contract validation.
- `.lazy-harness/decisions/0043-pi-native-package-in-source-repo.md` — repo placement decision.

## Rule placement

- Rule: Pi install UX should use `lazy pi` wrapper commands first; npm/standalone publishing remains deferred until official Pi and OMP runtime smoke are stable.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/pi-agent-package.md`
- Why not AGENTS.md: this is a Pi package installer contract, not general prompt grammar.
- Why not `.jcode`: this is shared lazy-harness Pi adapter behavior, not private Jcode preference.
- Confirmation: user-confirmed
