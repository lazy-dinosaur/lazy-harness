# Antigravity MCP to Pi Bridge

Status: active
Layer: SDD

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - importing Antigravity MCP server definitions into Pi MCP adapter config
- Must:
  - read only `mcpServers` and convert server keys/stdio fields into Pi `~/.pi/agent/mcp.json`
  - support a dry-run before apply
- Must not:
  - read or copy Antigravity OAuth token stores
  - write secret-looking keys/values into `.lazy-harness` records or command summaries (redact)
- Record completion:
  - conversion or security-boundary changes update this SDD and the Pi package regression test
- Related records:
  - `.lazy-harness/tests/antigravity-mcp-pi-bridge.md`

## Purpose

Import Antigravity MCP server definitions into Pi MCP adapter config without copying Antigravity OAuth token stores.

## Source and target

Antigravity sources:

- `~/.gemini/config/mcp_config.json`
- `~/.gemini/antigravity/mcp_config.json`
- Optional workspace configs:
  - `<workspace>/.agents/mcp_config.json`
  - `<workspace>/_agents/mcp_config.json`

Pi target:

- `~/.pi/agent/mcp.json`

## Command

Dry-run:

```bash
bun packages/lazy-harness-pi/scripts/import-antigravity-mcp.ts --dry-run
```

Apply:

```bash
bun packages/lazy-harness-pi/scripts/import-antigravity-mcp.ts --apply
```

From Pi:

```text
/lazy-import-antigravity-mcp --dry-run
/lazy-import-antigravity-mcp --apply
```

## Conversion contract

- Parse JSON or JSONC-like Antigravity MCP config.
- Read `mcpServers` only.
- Convert remote server keys:
  - `serverUrl` -> Pi `url`
  - `httpUrl` -> Pi `url`
  - `url` -> Pi `url`
- Preserve stdio fields:
  - `command`, `args`, `env`, `cwd`
- Preserve remote header fields:
  - `headers`
- Convert disabled tool list:
  - `disabledTools` -> Pi `excludeTools`
- Skip disabled servers by default.
- Avoid overwriting existing Pi servers by default; use `--overwrite` or `--prefix` for conflicts.
- Convert OAuth client config:
  - Antigravity `oauth.clientId`, `clientSecret`, `scope`, `redirectUri`, `clientName`, `clientUri`, `grantType` -> Pi `auth: "oauth"`, `oauth` object.
- Convert Google ADC auth:
  - Antigravity `authProviderType: "google_credentials"` -> Pi `auth: "bearer"`, `bearerTokenEnv`.
  - The command prints an export helper such as:
    ```bash
    export ANTIGRAVITY_MCP_EXAMPLE_ACCESS_TOKEN="$(gcloud auth application-default print-access-token)"
    ```

## Security boundary

The importer must not read or copy Antigravity OAuth token stores, especially:

```text
~/.gemini/antigravity/mcp_oauth_tokens.json
```

Secrets may remain in user-local config files when a user explicitly applies a merge, but `.lazy-harness` records and command summaries must redact secret-looking keys/values.

## Implementation map

- `packages/lazy-harness-pi/scripts/import-antigravity-mcp.ts` — importer/bridge implementation.
- `packages/lazy-harness-pi/fixtures/antigravity-mcp-config.jsonc` — regression fixture with stdio, OAuth, Google ADC, and disabled server examples.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — exposes `/lazy-import-antigravity-mcp` Pi command.
- `packages/lazy-harness-pi/README.md` — user-facing usage and Google ADC bridge notes.
- `.lazy-harness/tests/antigravity-mcp-pi-bridge.md` — regression contract.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — static and fixture conversion coverage.
