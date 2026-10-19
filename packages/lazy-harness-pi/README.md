# Lazy-Harness Pi / OMP Package

Pi Coding Agent and Oh My Pi / OMP package for lazy-harness prompt/runtime lifecycle integration.

The package is not installed by default after a clean reset. Install it only when you want Pi or OMP to load lazy-harness behavior.

## Cross-platform prerequisites

- Lazy-harness base install: `git`, `bun`, `python3`, and a git repository target. The public installer prints macOS/Linux install hints if any required command is missing.
- Official Pi commands require `pi` on `PATH`.
- Oh My Pi / OMP commands require `omp` on `PATH`.
- Antigravity Google ADC MCP bridge commands require `gcloud` only when importing `authProviderType: "google_credentials"` servers.
- The wrapper commands do not install system dependencies automatically; install them with the OS package manager first, then run `lazy pi doctor` or `lazy omp doctor`.

## Recommended wrapper commands

Use the lazy-harness wrapper first. It keeps the package path consistent, separates Pi from OMP install UX, and avoids relying on OMP's legacy `pi` manifest fallback.

### Official Pi

Global bootstrap for all Pi projects:

```bash
.lazy-harness/bin/lazy pi install
```

Explicit spelling is also accepted:

```bash
.lazy-harness/bin/lazy pi install --global
```

Project-local install for this repo only remains available for advanced/debug cases:

```bash
.lazy-harness/bin/lazy pi install --local
```

Project-local attachment into another repo from that repo:

```bash
cd /path/to/other/repo
/path/to/lazy-harness/.lazy-harness/bin/lazy pi install --local
```

The install target for `--local` is the current repo, but the source package path remains `/path/to/lazy-harness/packages/lazy-harness-pi`. Replace `/path/to/lazy-harness` with the checkout path on the current computer, for example `$HOME/dev/lazy-harness`.

Project activation is separate from package installation:

```bash
.lazy-harness/bin/lazy agent activate --target /path/to/project
```

`lazy init` prints the same activation command after bootstrapping a host. Activation creates project-local `.pi/APPEND_SYSTEM.md` and `.omp/APPEND_SYSTEM.md` pointer prompts, merges `.pi/settings.json` so Pi loads project-owned `../.claude/skills`, `../.codex/skills`, and `../.agents/skills` with `enableSkillCommands: true`, and the global package no-ops outside projects where `.lazy-harness/bin/lazy` is present.

Do not attach a second project copy while a different global copy is active: duplicate tool registrations can fail startup. Reconcile explicit project pins/attachments in the same approved rebind batch while preserving project skills settings; installation is not permission to mutate other hosts.

### Experimental OMP Reader and offline accounting

OMP uses the thin `omp/index.ts` entrypoint, shared instance-owned guard/ledger/join core and explicit output-mode fallback. Pi keeps its Fabric Reader/policy and existing entrypoint; no legacy Subagents manifest is restored. Project Reader activation is create-only and preview-only by default:

```bash
bun packages/lazy-harness-pi/scripts/activate-omp-reader.ts --target /path/to/host --model provider/model
```

Add `--apply` only for the approved initialized target, then restart OMP. Differing definitions/symlinks are refused, not overwritten. Native task lifecycle is identity, not content; visible successful untruncated yielded packets plus shared terminal ledger/range/hash checks are required for join. Legacy read limits ignored by OMP are rejected; finite raw ranges and returned coverage are enforced.

`bun packages/lazy-harness-pi/scripts/collect-runtime-usage.ts /path/to/private/manifest.json` reads an explicit Parent/Reader session inventory, validates safe unique usage entries and preserves reported cache categories/totalTokens. Real sessions/reports remain private; synthetic zero usage is not efficiency or billing evidence. Details and manifest shape: `.lazy-harness/tests/runtime-session-usage.md` and `.lazy-harness/spec/platform/pi-agent-package.md`.

Default offline fixtures test registration, exact activation, transport/epoch/isolation negatives and collection. Installed-native OMP tests are explicit `LAZY_OMP_NATIVE_TEST=1` opt-in and are not counted as passing when skipped. OMP remains Experimental. Development SDK is pinned to Pi 0.85.1; managed Pi 1.3 is not a source compatibility pass, and user/custom event plus SDK-fixture migration remains separate work. No global upgrade, paid comparison or full-runtime parity is implied.

List current Pi package settings:

```bash
.lazy-harness/bin/lazy pi list
.lazy-harness/bin/lazy pi list --global
```

One-run load smoke without persisting settings:

```bash
.lazy-harness/bin/lazy pi smoke
```

Diagnostics without mutating Pi settings:

```bash
.lazy-harness/bin/lazy pi doctor
```

Remove the package:

```bash
.lazy-harness/bin/lazy pi remove --local
.lazy-harness/bin/lazy pi remove --global
```

For preview-only safety, add `--dry-run` to `install`, `remove`, or `smoke`.

### Oh My Pi / OMP

Persistent OMP plugin link:

```bash
.lazy-harness/bin/lazy omp install
```

List current OMP plugins:

```bash
.lazy-harness/bin/lazy omp list
```

One-run OMP load smoke without persisting plugin settings:

```bash
.lazy-harness/bin/lazy omp smoke
```

Diagnostics without mutating OMP plugin settings:

```bash
.lazy-harness/bin/lazy omp doctor
```

Remove the OMP plugin link:

```bash
.lazy-harness/bin/lazy omp remove
```

For preview-only safety, add `--dry-run` to `install`, `remove`, or `smoke`.

OMP local path installs use official OMP plugin link semantics and persist in OMP's plugin registry. Use `lazy omp smoke` when you only want a one-run, non-persistent package load.

Isolation behavior:

- `lazy pi install` writes user-global Pi settings so every Pi project can load the package bootstrap; runtime hooks still resolve the active repo via Pi `ctx.cwd` and run that repo's `.lazy-harness` hooks only.
- `lazy pi install --local` writes the target repo's `.pi/settings.json`; the wrapper also ensures `.pi/` is listed in that repo's `.git/info/exclude` to avoid teammate contamination.
- `lazy agent activate` writes project-local `.pi/APPEND_SYSTEM.md` and `.omp/APPEND_SYSTEM.md` pointer prompts, merges `.pi/settings.json` with project-relative Claude/Codex/Agents skill paths (`../.claude/skills`, `../.codex/skills`, `../.agents/skills`) and `enableSkillCommands: true`, and ensures `.pi/` / `.omp/` are listed in that repo's `.git/info/exclude`.
- OMP persistent installs run through `omp plugin link <path>` (live dev-link that tracks the source checkout — source change = instant update, no stale snapshot) and are independent of Pi `.pi/settings.json`.
- Recent tool-call evidence is scoped by lazy root, so a Pi process that touches multiple repos does not mix `recent_tool_calls` between roots.
- Use `--target-repo /path/to/repo` for explicit install/list/smoke diagnostics without relying on the caller cwd.

Publishing this package to npm or moving it to a standalone repo is intentionally deferred until official Pi and OMP runtime smoke are stable.

## Install locally into a project

Raw Pi and OMP commands are still supported when debugging the agent runtime itself.

Define the source package path once before using raw Pi/OMP commands:

```bash
LAZY_HARNESS_PI_PACKAGE=/path/to/lazy-harness/packages/lazy-harness-pi
```

Global install for all projects:

```bash
pi install "$LAZY_HARNESS_PI_PACKAGE" --no-approve
```

Project-local install for this repo only:

```bash
pi install -l "$LAZY_HARNESS_PI_PACKAGE" --approve
```

OMP persistent plugin link:

```bash
omp plugin link "$LAZY_HARNESS_PI_PACKAGE"
```


OMP remove:

```bash
omp plugin uninstall @lazy-dinosaur/lazy-harness-pi
```

## One-run smoke

```bash
pi -e "$LAZY_HARNESS_PI_PACKAGE" --help
```

OMP:

```bash
omp -e "$LAZY_HARNESS_PI_PACKAGE" --help
```

## What it wires

- The package exposes `lazy_reader_request` to prepare a dedicated `lazy-harness.record-reader` on **Pi Fabric**. No pi-subagents installation or registration is required. OMP runtime changes are outside this Pi transport commit; the shared Reader body remains in `agents/record-reader.md`.
- For a Reader-managed Pi work unit, send the exact `root:`, `revision:`, `model: openai/gpt-6-luna:low`, `evidenceEpoch:`, `maxReadCalls:`, `maxRequestedLines:`, derived `maxLinesPerRead`, and `task:` envelope to that tool. The task model must equal launch model. Pass `prepared.details.request` unchanged to `agents.spawn` inside `fabric_exec`, return the handle, and continue the Parent source/test lane with native/simple read-only tools. Return the full `agents.wait({id: handle.id})` result and consume actual packet content before `lazy_reader_join`. Normally omit run ID, counters and paths; runtime-owned read counts, max observed limit, failed-call count and all successful fingerprints are checked. A process-complete acknowledgement alone is not a join. Old Agent Contract v1/acceptance/output/artifacts/toolBudget flags are not Fabric options. Fabric's native process artifacts remain runtime-owned; its sessionless child mirrors the actual hook-owned ledger to runtime scratch keyed by the host-issued run id. Model-reported counters cannot replace it.
- Reader parity is mapped from the full existing role definition, not just its Markdown body: system-prompt replacement; no inherited Parent project context/skills; fresh seed; declared guard-module identity; read-only tool ceiling; soft 12 assistant turns plus 2 grace turns. The hook-owned ledger carries the contract/turn state and the Parent rejects missing/changed policy stamps or a hard-limit violation. Start the Reader with spawn, do Parent source/test work in parallel, and wait only at the join boundary. Unsupported frontmatter changes fail preparation instead of being silently ignored.
- A matching `complete` join satisfies the transitional search/read-debt bridge without duplicate Parent record reads. Missing/incomplete/conflict/stale/budget-exceeded Reader results use bounded direct Parent fallback.
- In non-interactive Pi text/print mode, the substantive Parent response remains primary stdout; any post-response advisory is emitted to stderr and does not queue a second assistant turn that could replace it.
- `before_agent_start` injects the lazy-harness record-first reminder by reusing `.lazy-harness/hooks/lifecycle/on-message-received.sh` when available, and displays `lazy-harness read-debt` with `status=armed`, `status=not-armed(synthetic-turn)`, `status=not-armed(hook-empty)`, `status=not-armed(hook-timeout)`, or `status=not-armed(hook-error)`, plus `phase=armed|debug` and concise `hook=<detail>` for failures. Synthetic/steering starts are debug-only: they do not create read-debt journal rows, but they still get a visible status marker and minimal steering reminder to avoid host-specific claims or mutations from memory.
- A non-extension mid-turn steer re-arms generic evidence in memory: prior recent-tool evidence is cleared, late results from pre-steer tool calls are ignored, and action remains blocked until a fresh post-steer map/read call completes. The adapter does not classify steer text or maintain command-specific rules.
- `tool_call` bridges Pi tool payloads into `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` and blocks only when the generic search/read evidence guard denies.
- `tool_call` normalizes Pi shell aliases `cmd`, `command`, `shell`, and `terminal` to lazy `bash` before invoking the guard; not-armed action blocks include the read-debt status/detail.
- Commands: `/lazy-map`, `/lazy-doctor`, `/lazy-test`, `/lazy-sync`, `/lazy-update`, `/lazy-import-antigravity-mcp`.

## Antigravity MCP import

Dry-run Antigravity MCP config conversion:

```bash
bun "$LAZY_HARNESS_PI_PACKAGE/scripts/import-antigravity-mcp.ts" --dry-run
```

Apply conversion into Pi MCP adapter config:

```bash
bun "$LAZY_HARNESS_PI_PACKAGE/scripts/import-antigravity-mcp.ts" --apply
```

Or from Pi:

```text
/lazy-import-antigravity-mcp --dry-run
/lazy-import-antigravity-mcp --apply
```

The importer reads Antigravity MCP configs such as `~/.gemini/config/mcp_config.json` and `~/.gemini/antigravity/mcp_config.json`, converts `serverUrl` to Pi `url`, converts `disabledTools` to `excludeTools`, and converts `authProviderType: "google_credentials"` into a Pi `bearerTokenEnv` bridge. It does not copy Antigravity OAuth token stores. For Google ADC-backed servers, export the generated bridge command before running Pi, for example:

```bash
export ANTIGRAVITY_MCP_EXAMPLE_ACCESS_TOKEN="$(gcloud auth application-default print-access-token)"
```

## Trust boundary

Pi/OMP extensions run with project extension permissions. Install only in projects where you trust the checked-out lazy-harness source and the host `.lazy-harness` directory.
