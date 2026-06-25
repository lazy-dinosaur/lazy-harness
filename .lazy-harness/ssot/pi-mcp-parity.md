# Pi MCP Parity

Status: superseded
Superseded on: 2026-06-24
Superseded by: .lazy-harness/decisions/0050-pi-omp-only-runtime.md
Layer: SSOT

## Rule digest

- Status: deprecated
- Layer: SSOT
- Scope: framework-global
- Applies when:
  - syncing or validating Pi Coding Agent MCP servers to match this host's Jcode harness set
  - converting Jcode MCP server config into Pi adapter `mcpServers` format
- Must:
  - keep Pi's MCP set in parity with `~/.jcode/mcp.json` (`servers`) in `~/.pi/agent/mcp.json` (`mcpServers`)
  - preserve existing Pi imports (e.g. `claude-code`) and back up the prior Pi config before writing
  - drop Jcode-only `shared`/`transport` flags and convert Figma OAuth to Pi adapter format
  - keep proxy/lazy mode (no `directTools` by default) to avoid context bloat
- Must not:
  - copy secret values into `.lazy-harness` records; keep secrets only in user-local config files
- Record completion:
  - server-set or conversion-rule changes update this SSOT with refreshed parity validation counts

## Purpose

> Superseded by ADR 0050 (Pi/OMP-only): jcode is removed; the ~/.jcode/mcp.json MCP parity source no longer exists. Preserved as history.

Pi Coding Agent should have the same MCP server set as the Jcode harness on this host.

## Source and target

- Source config: `~/.jcode/mcp.json`
  - Jcode uses `servers` as the top-level server map.
- Pi target config: `~/.pi/agent/mcp.json`
  - `pi-mcp-adapter` reads `mcpServers` as the top-level server map.
  - Existing imports are preserved, including `claude-code`.

## Server parity as of 2026-06-09

The following Jcode MCP servers were converted into Pi `mcpServers`:

- `context7`
- `electron-test`
- `exa`
- `figma`
- `filesystem`
- `github`
- `grep_app`
- `playwright`
- `supabase-lazydino`
- `supabase-medivance`
- `tosspayments-integration-guide`
- `websearch`

Parity validation:

```text
jcodeCount=12
piCount=12
missingFromPi=[]
extraInPi=[]
```

Pi adapter loader validation:

```text
loadedServerCount=12
hasPiOwnedServers=true
imports=[claude-code]
```

## Conversion rules

- Copy stdio servers as `command`, `args`, `env`.
- Drop Jcode-only `shared` flags.
- Drop Jcode-only `transport` flags.
- Convert Jcode Figma OAuth object to Pi adapter format:
  - `auth: "oauth"`
  - `oauth.scope: "mcp:connect"`
- Do not enable `directTools` by default. The adapter's proxy/lazy mode is kept to avoid context bloat.
- Preserve secret values only in user-local config files. Never copy them into `.lazy-harness` records.

## Backup

Before writing, the previous Pi MCP config was backed up as:

```text
~/.pi/agent/mcp.json.bak-20260609T124824Z
```

## Validation commands

```bash
python3 - <<'PY'
import json, pathlib
src=json.loads((pathlib.Path.home()/'.jcode/mcp.json').read_text()).get('servers',{})
dst=json.loads((pathlib.Path.home()/'.pi/agent/mcp.json').read_text()).get('mcpServers',{})
print({'jcodeCount':len(src),'piCount':len(dst),'missingFromPi':sorted(set(src)-set(dst)),'extraInPi':sorted(set(dst)-set(src))})
PY

cd /home/lazydino/dev/lazy-harness
bun - <<'TS'
import { loadMcpConfig } from '/home/lazydino/.pi/agent/npm/node_modules/pi-mcp-adapter/config.ts';
const config = loadMcpConfig(undefined, process.cwd());
console.log(Object.keys(config.mcpServers).sort());
TS
```

## Implementation map

- `~/.jcode/mcp.json` — source Jcode MCP server config.
- `~/.pi/agent/mcp.json` — Pi MCP adapter global override containing converted `mcpServers`.
- `~/.pi/agent/npm/node_modules/pi-mcp-adapter/config.ts` — Pi adapter config loader, merge precedence, import expansion.
- `~/.pi/agent/npm/node_modules/pi-mcp-adapter/types.ts` — Pi adapter `ServerEntry` fields.
- `.lazy-harness/ssot/pi-mcp-parity.md` — non-secret record of parity source, target, server names, conversion rules, and validation.
