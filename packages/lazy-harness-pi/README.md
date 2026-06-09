# Lazy-Harness Pi Package

Pi Coding Agent package for lazy-harness prompt/runtime lifecycle integration.

## Install locally into a project

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
