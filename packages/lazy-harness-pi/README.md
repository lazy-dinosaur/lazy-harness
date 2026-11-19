# Lazy-Harness Pi / OMP Package

Pi Coding Agent and Oh My Pi / OMP package for lazy-harness prompt/runtime lifecycle integration.

The package is not installed by default after a clean reset. Install it only when you want Pi or OMP to load lazy-harness behavior.

## Cross-platform prerequisites

- Lazy-harness base install: `git`, `bun`, `python3`, and a git repository target. The public installer prints macOS/Linux install hints if any required command is missing.
- Official Pi commands require `pi` on `PATH`.
- Oh My Pi / OMP commands require `omp` on `PATH`.
- Antigravity Google ADC MCP bridge commands require `gcloud` only when importing `authProviderType: "google_credentials"` servers.
- The wrapper commands do not install system dependencies automatically; install them with the OS package manager first, then run `lazy pi doctor` or `lazy omp doctor`.

## macOS monitoring checklist

Monitoring is optional and default-off. The [monitoring SDD](../../.lazy-harness/spec/platform/monitoring-thin-consumer.md)
is the canonical configuration, admission, budget, status and logging contract; this checklist is setup guidance.

1. Install Xcode Command Line Tools (`xcode-select --install`), Git, Python 3, Bun and **Pi 1.5.x**.
   Confirm `git --version`, `python3 --version`, `bun --version`, `pi --version` in the shell Pi uses.
2. Clone the source with submodules and install both dependency trees:
   ```bash
   git clone --recurse-submodules https://github.com/lazy-dinosaur/lazy-harness.git
   cd lazy-harness
   # Repair an existing/ordinary clone instead:
   git submodule update --init --recursive vendor/lazy-harness-monitoring
   bun install --frozen-lockfile
   (cd vendor/lazy-harness-monitoring && bun install --frozen-lockfile)
   .lazy-harness/bin/lazy pi install
   ```
   The wrapper repeats the idempotent preparation before global/local registration. Re-register on
   the Mac even if settings were copied: Pi stores **absolute package paths** from the old machine.
   Activate/initialize the intended host project separately; keep the source checkout installed.
3. In Pi, `/login openrouter` stores the credential. Monitoring refuses environment-key fallback;
   never put credentials in project files or the configuration below.
4. After approving observe and its budget, run in the **host project**, never an upstream/shared checkout:
   ```bash
   lazy monitoring enable --dry-run  # preview; no writes or model calls
   lazy monitoring enable
   lazy monitoring config           # effective config + real parser/catalog validation
   # Custom catalog/budget (paths are host-root-relative):
   lazy monitoring enable --no-default-docs --doc .lazy-harness/ssot/project-identity.md --calls 2 --usd 0.02 --force
   ```
   Defaults: two monitoring ownership/ADR records when present (missing records are skipped with a notice),
   observe, 100 lifetime calls, concurrency 1, queue 2, 1,000,000 reserved tokens, USD 0.05 reserved.
   Limits are conservative reservations, not promised spend. Enable itself makes **zero model calls**;
   subsequent Pi observation after reload may use the approved budget. Existing config refuses overwrite
   with a diff unless `--force`; `--dry-run` writes nothing. Hard caps: 16 records, 8 KiB each, **12 KiB total**.
   Read format detects `pi-hashline-edit-pro` in the user's Pi settings packages; otherwise `pi-read-text-v1`.
   Override with `--read-format unknown|pi-read-text-v1|pi-hashline-edit-pro-v1` if necessary.
   In Pi, `/monitoring enable` uses the same defaults/validation (use CLI flags for customization).
   No command auto-reloads; apply the file change with `/reload`. The login hint is conditional and
   does not inspect auth.json or secret values.
   Manual-file fallback: author `.lazy-harness/monitoring-attach.json` using the [SDD configuration contract](../../.lazy-harness/spec/platform/monitoring-thin-consumer.md#configuration-manual-file-fallback).
### Global monitoring allowlist (macOS/Linux)

Instead of creating per-project files with `lazy monitoring enable`, explicitly allowlist projects:

```bash
lazy monitoring enable --global --project /absolute/path/to/project --dry-run
lazy monitoring enable --global --project /absolute/path/to/project
# --project without a value uses the current host root:
lazy monitoring enable --global --project
lazy monitoring config
# In each open Pi project: /reload, then /monitoring status
lazy monitoring disable --global --project /absolute/path/to/project
# Remove the entire global file (shows it first):
lazy monitoring disable --global
```

**Consent:** conversation excerpts of allowlisted projects are sent to **OpenRouter Jev** during
judgement after reload. Enable/config/status themselves make no model calls. Budgets are **per
session**, not a global account cap: totals scale with open sessions. First global enable prints this notice.

Global config is `$XDG_CONFIG_HOME/lazy-harness/monitoring.json`, falling back to
`~/.config/lazy-harness/monitoring.json` (file 0600, directory 0700). Bare CLI `enable --global`
creates/updates defaults only; it does not enroll any project. Adding/removing allowlist entries preserves
other projects and defaults; replacing defaults requires `--force` after reviewing the diff.
`--all --i-understand` explicitly enables all projects; `all` is false by default. A project cannot be
excluded while `all:true`; remove the global file first. Global mode never writes project files.

At startup, a project `.lazy-harness/monitoring-attach.json` **wins entirely**, even if off or invalid.
Otherwise, only realpath-matching allowlisted roots (or explicit `all:true`) use global defaults.
The automatic catalog considers direct `.lazy-harness/ssot/*.md` and `decisions/*.md`, preferring
`## Rule digest`, then smaller files, then path. It admits no symlinks, at most 16 documents,
8 KiB each and 12 KiB total; no eligible documents means off with `no_catalog_documents` and no calls.
Use a project file for a custom catalog. Config shows source, membership, selected paths/bytes and validation;
Pi status adds `configSource` (`project | global | off`) and `configReason`.

In Pi, `/monitoring enable --global` and `/monitoring disable --global` add/remove **only the current
project** and remind you to `/reload`; they never reload automatically. Per-project `/monitoring enable`
and `/monitoring disable` remain available. Removing a project override can reveal an existing global opt-in.

5. `/reload`, then `/monitoring status` (no model call). Inspect `attached`, `paused`, `rebuilding`, `ready`, `stage`, `reason`,
   catalog ids/versions/bytes, `budget` used/remaining, classifier state, `window` state/bytes/
   lastReason/renewals, counters, `lastOutcomes` and log path/written/dropped/errors.
   Default metadata-only logs are outside Git:
   `$XDG_STATE_HOME/lazy-harness/monitoring/observe/<hash>/<date>.jsonl`, or
   `~/.local/state/lazy-harness/monitoring/observe/<hash>/<date>.jsonl` when unset.
   `observeLog: false` disables logging; see the SDD for retention, permissions and custom path safety.
6. **Report results:** in Pi run `/monitoring status --save`, then from this host project:
   ```bash
   lazy monitoring report --issue --dry-run   # preview only; no gh calls
   lazy monitoring report --issue             # print report + target, then submit
   # Or save locally (outside every Git worktree):
   lazy monitoring report --lines 20 --out "$HOME/monitoring-report.md"
   ```
   Saving status is explicit; plain status is unchanged. `status-latest.json` is private (0600,
   directory 0700) in the external observe state directory, even when observe logging is disabled.
   Saved status is a snapshot, not live telemetry; the report notes its age. Missing status is OK.
   Collection makes zero model calls; only `--issue` contacts GitHub via `gh`. Default repository:
   `lazy-dinosaur/lazy-harness` (override `--repo OWNER/NAME`). Review metadata before sharing.
   Never paste `auth.json`, keys, environment dumps or conversation text. Credential-like patterns
   refuse the outbound report. Use a non-symlinked external path; Git worktree paths are refused.
   On macOS prefer `$HOME` output paths over the `/tmp` symlink.
7. Turn off: `lazy monitoring disable` or `/monitoring disable` in Pi, then `/reload`.
   Off retains the vendor-free control/status command but registers no monitoring hooks and touches no vendor modules.

Troubleshooting (never put raw provider errors or credentials in a bug report):

- Empty `vendor` / `monitoring_module_unavailable`: run the recursive submodule command and both
  frozen installs, rerun `lazy pi install`, then `/reload`. One startup notice is expected, not a hook denial.
- `frame_unavailable`: inspect session snapshot availability; tail mode handles long sessions but
  genuinely unavailable frames close admission. Reload after resolving the source issue.
- `selection_material_unavailable:material_limit`: reduce catalog/message material; the window is
  byte-bounded. Do not increase the catalog beyond the SDD caps.
- `classifier_uncertain:<class>`: inspect bounded `budget.used.lastFailure` (auth/timeout/etc.).
  Fix the underlying condition then reload; uncertain outcomes deliberately stop the classifier, no retry.
- Window renewals are normal during long streaming sessions; they do **not** reset lifetime budgets.
- `queued_input_followUp:*` / `queued_input_steer:*`: phase 1 records queued inputs as skipped,
  not specially judged at delivery. `/monitoring status` sweeps overdue outcomes; see SDD.

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
- Pi 1.1+: `/lazy-move "/path/to/project" [--prompt text]` continues the saved conversation in a new session using the target project’s tools and rules. The original session stays available. Use `lazy_move_project` through the agent for the same handoff after the current turn; a queued request does not mean the session has already switched.

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
