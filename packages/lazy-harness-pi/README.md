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

- Parent and ordinary Pi/OMP roles receive the full Lazy-Harness interactive grammar once per runtime session.
- The package exposes one opt-in `lazy-harness.record-reader` evidence-loader profile with two explicit Work Packet modes. `candidate-map` returns a non-authoritative coverage/evidence-question proposal from Parent-supplied facets and concrete nodes; `claim-evidence` loads one Parent-approved evidence bundle. The Parent retains full Lazy-Harness operating grammar, complete overview discovery, governing-record reads, map approval/reopening, semantic authority, mutation, and validation. The Reader has no Parent AGENTS grammar, source access, mutation, output artifact, subagent recursion, or Parent response-completion lifecycle.
- `before_agent_start` injects the lazy-harness record-first reminder by reusing `.lazy-harness/hooks/lifecycle/on-message-received.sh` when available, and displays `lazy-harness read-debt` with `status=armed`, `status=not-armed(synthetic-turn)`, `status=not-armed(hook-empty)`, `status=not-armed(hook-timeout)`, or `status=not-armed(hook-error)`, plus `phase=armed|debug` and concise `hook=<detail>` for failures. Synthetic/steering starts are debug-only: they do not create read-debt journal rows, but they still get a visible status marker and minimal steering reminder to avoid host-specific claims or mutations from memory.
- A non-extension mid-turn steer re-arms generic evidence in memory: prior recent-tool evidence is cleared, late results from pre-steer tool calls are ignored, and action remains blocked until a fresh post-steer map/read call completes. The adapter does not classify steer text or maintain command-specific rules.
- `tool_call` bridges Pi tool payloads into `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` and blocks only when the generic search/read evidence guard denies.
- `tool_call` normalizes Pi shell aliases `cmd`, `command`, `shell`, and `terminal` to lazy `bash` before invoking the guard; not-armed action blocks include the read-debt status/detail.
- Commands: `/lazy-map`, `/lazy-doctor`, `/lazy-test`, `/lazy-sync`, `/lazy-update`, `/lazy-import-antigravity-mcp`.

Run the opt-in records-only child through Pi Subagents only after the Parent has completed the lean overview, directly read governing records, and frozen packet identity.

The launch transport must disable native supervisor/intercom coordination for this role—for scripted Pi Subagents runs, pass `intercomBridge: { mode: "off" }`—so `contact_supervisor` is not injected. Runtime tool-call soft/hard limits both equal packet `budget.toolCalls` and reserve the final call for `structured_output`. Output size is separate: compact v2 uses a 6,000-code-point soft target and 12,000 hard cap. Above target is a receipt warning; accurate closure that cannot fit the hard cap returns `overflow` with bounded split detail rather than trimming.

Every new Reader run uses `record-reader-admission/v2`. The Parent envelope keeps full identity, objective, catalogs, scope, and budgets; the model payload echoes one schema-constant `contractDigest`. Compact ids/tables remove duplication without deleting evidence. The helper validates envelope-byte digest and payload references; Parent separately audits Pi run metadata, schema/capture artifact location, transcript probes, and pre/post fingerprints—the receipt alone is not run attestation. Archived v1 remains validation-only. Machine admission never decides semantic truth, source correctness, merge, or promotion.

```bash
bun "$LAZY_HARNESS_PI_PACKAGE/scripts/record-reader-admission.ts" digest --contract /path/to/compact-contract.json
bun "$LAZY_HARNESS_PI_PACKAGE/scripts/record-reader-admission.ts" schema --contract /path/to/contract.json
bun "$LAZY_HARNESS_PI_PACKAGE/scripts/record-reader-admission.ts" validate --contract /path/to/contract.json --output /path/to/structured-output.json
```

```text
/run lazy-harness.record-reader "packetVersion: record-reader/v2; admissionSchemaVersion: record-reader-admission/v2; contractDigest: <sha256>; mode: candidate-map; full Parent envelope identity; F/I/N/V catalogs; allowedLayers; governingRecordsReadByParent; risk/exclusions; budget.targetOutputCharacters: 6000; budget.hardOutputCharacters: 12000; budget.toolCalls: 14."
```

`candidate-map` remains non-authoritative. Compact questions reference `R*` records and range indexes; one `coverage` map conserves every Parent `F*`/`I*`; node tracking uses `N*`; implementation candidates use `V*`; bundles/dependencies use `B*`/`D*`. Claim mode requires `needs-remap` for new-question/overlap/dependency changes, `conflict` for blocking conflicts, `blocked-by-dependency` for `blockedDependencies`, and matching `overflow` status/detail. Parent expands refs, approves/rewrites bundles, and directly rereads decision-critical records. Neither mode clears Parent read debt.

This package defines one guarded Reader role with archived v1 validation and compact v2 generation for new packets. Static/adversarial fixtures protect the profile; compact admission protects the full-envelope digest, normalized references, exact coverage, 6,000 soft target/12,000 hard cap, and closure consistency. The extension's records-only tools and Parent lifecycle isolation are unchanged. Automatic decomposition, live compact reruns, Source Verifier, Writer, delegated evidence, model defaults, main integration, and production promotion remain separately approval-gated.

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
