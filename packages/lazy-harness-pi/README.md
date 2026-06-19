# Lazy-Harness Pi Package

Pi Coding Agent package for lazy-harness prompt/runtime lifecycle integration.

The package is not installed by default after a clean reset. Install it only when you want Pi to load lazy-harness behavior.

## Recommended wrapper commands

Use the lazy-harness wrapper first. It keeps the package path consistent and makes install/remove scope explicit.

Project-local install for the current host:

```bash
.lazy-harness/bin/lazy pi install --local
```

Project-local install into another repo from that repo:

```bash
cd /path/to/other/repo
/home/lazydino/dev/lazy-harness/.lazy-harness/bin/lazy pi install --local
```

The install target is the current repo, but the source package path remains `/home/lazydino/dev/lazy-harness/packages/lazy-harness-pi`.

Global install for all Pi projects:

```bash
.lazy-harness/bin/lazy pi install --global
```

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

Isolation behavior:

- `--local` writes the target repo's `.pi/settings.json`; the wrapper also ensures `.pi/` is listed in that repo's `.git/info/exclude` to avoid teammate contamination.
- `--global` writes user-global Pi settings so every Pi project can load the package. Runtime hooks still resolve the active repo via Pi `ctx.cwd` and run that repo's `.lazy-harness` hooks only.
- Recent tool-call evidence is scoped by lazy root, so a Pi process that touches multiple repos does not mix `recent_tool_calls` between roots.
- Use `--target-repo /path/to/repo` for explicit install/list/smoke diagnostics without relying on the caller cwd.

Publishing this package to npm or moving it to a standalone repo is intentionally deferred until official Pi and OMP runtime smoke are stable.

## Install locally into a project

Raw Pi commands are still supported when debugging Pi itself.

Global install for all projects:

```bash
pi install /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --no-approve
```

Project-local install for this repo only:

```bash
pi install -l /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --approve
```

## One-run smoke

```bash
pi -e /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --help
```

## What it wires

- `before_agent_start` injects the lazy-harness record-first reminder by reusing `.lazy-harness/hooks/lifecycle/on-message-received.sh` when available.
- `tool_call` bridges Pi tool payloads into `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` and blocks only when the generic search/read evidence guard denies.
- `tool_call` normalizes Pi shell aliases `cmd`, `command`, `shell`, and `terminal` to lazy `bash` before invoking the guard.
- `tool_result` records recent read/search/tool evidence for the next guard invocation.
- Commands: `/lazy-map`, `/lazy-doctor`, `/lazy-test`, `/lazy-sync`, `/lazy-update`, `/lazy-import-antigravity-mcp`.

## Antigravity MCP import

Dry-run Antigravity MCP config conversion:

```bash
bun /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi/scripts/import-antigravity-mcp.ts --dry-run
```

Apply conversion into Pi MCP adapter config:

```bash
bun /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi/scripts/import-antigravity-mcp.ts --apply
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

Pi extensions run with project extension permissions. Install only in projects where you trust the checked-out lazy-harness source and the host `.lazy-harness` directory.
