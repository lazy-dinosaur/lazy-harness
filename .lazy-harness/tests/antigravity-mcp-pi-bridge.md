# Antigravity MCP to Pi Bridge Regression

Status: active
Layer: TDD

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - importing or converting an Antigravity MCP config into a Pi MCP adapter config
  - working on the Pi package importer, server field mapping, or OAuth handling
- Must:
  - convert Antigravity MCP servers to Pi adapter configs, preserving stdio, url, auth, and excludeTools
  - bridge `google_credentials` to bearer auth with `bearerTokenEnv` and skip disabled servers by default
- Must not:
  - read or copy the Antigravity `mcp_oauth_tokens.json` token store
  - overwrite an existing same-named Pi server without `--overwrite` or `--prefix`
- Record completion:
  - changes to importer behavior or fixtures update this TDD plus the SDD contract
- Related records:
  - `.lazy-harness/spec/platform/antigravity-mcp-pi-bridge.md`

## Regression target

The Pi package importer must safely convert Antigravity MCP configs to Pi MCP adapter configs without copying Antigravity OAuth token stores.

## Protected cases

| Case | Input | Expected |
|---|---|---|
| `jsonc_parse` | Antigravity config fixture with comments/trailing commas | Importer parses successfully |
| `stdio_copy` | `command`, `args`, `env` server | Pi server preserves stdio fields |
| `remote_url` | `serverUrl` server | Pi server uses `url` |
| `oauth_copy` | Antigravity `oauth` object | Pi server has `auth: "oauth"` and copied client config |
| `disabled_tools` | Antigravity `disabledTools` | Pi server has `excludeTools` |
| `google_credentials_bridge` | `authProviderType: "google_credentials"` | Pi server has `auth: "bearer"` and `bearerTokenEnv`; report includes export helper |
| `skip_disabled` | `disabled: true` | Server is skipped by default |
| `no_token_store_copy` | Antigravity token store path exists conceptually | Importer never reads/copies `mcp_oauth_tokens.json` |
| `safe_conflict` | Existing Pi server with same name | Importer skips unless `--overwrite` or `--prefix` is used |

## Automated coverage

Implemented in:

```text
.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract
```

The self-test runs:

```bash
bun packages/lazy-harness-pi/scripts/import-antigravity-mcp.ts \
  --source packages/lazy-harness-pi/fixtures/antigravity-mcp-config.jsonc \
  --target <temp>/pi-mcp.json \
  --prefix ag- \
  --apply
```

and verifies:

- imported servers are `ag-local-db`, `ag-remote-oauth`, `ag-gcp-adc`
- disabled fixture server is skipped
- `serverUrl` becomes `url`
- `disabledTools` becomes `excludeTools`
- `google_credentials` becomes `bearerTokenEnv`

## Implementation map

- `packages/lazy-harness-pi/scripts/import-antigravity-mcp.ts` — converter implementation.
- `packages/lazy-harness-pi/fixtures/antigravity-mcp-config.jsonc` — source fixture.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — regression runner.
- `.lazy-harness/spec/platform/antigravity-mcp-pi-bridge.md` — SDD contract.
