# External Context-Compression/Memory Extension Policy

Status: accepted
Layer: SSOT
Date: 2026-06-30
Related ADR: `.lazy-harness/decisions/0052-external-context-extension-non-adoption.md`
Related SSOT: `.lazy-harness/ssot/project-identity.md`, `.lazy-harness/ssot/rule-sources.md`
Related ADR: `.lazy-harness/decisions/0049-discovery-vs-loading-complete-lean-discovery.md`, `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`

## Rule digest

- Status: active
- Layer: SSOT
- Scope: host-project
- Applies when:
  - user asks whether to add an external Pi/OMP context-compression, context-rerouting, or session-memory extension to this repo's workflow
  - evaluating packages such as `@hypabolic/pi-hypa`, `context-mode`, `pi-lean-ctx`, or similar context-window-savings extensions
  - deciding whether a tool that intercepts/compresses/reroutes `bash`/`read`/`grep`/`find`/`ls` or injects a routing `AGENTS.md` belongs in this source repo
- Must:
  - treat such extensions as non-adopted by default in this lazy-harness source repo
  - require explicit user confirmation (and a downstream dogfood-host trial) before any adoption here
  - keep `.lazy-harness/AGENTS.md` as the single routing grammar and `.lazy-harness` records as the single memory store in this repo
- Must not:
  - install/enable a competing context-compression/memory/routing extension here without user confirmation
  - let an external extension silently rewrite, compress, reroute, or block the `bash`/`read` outputs the harness-first evidence gate depends on
- Record completion:
  - adoption/non-adoption or installed-package-baseline changes update this SSOT plus `.lazy-harness/decisions/0052-external-context-extension-non-adoption.md`
- Related records:
  - `.lazy-harness/decisions/0052-external-context-extension-non-adoption.md`
  - `.lazy-harness/ssot/project-identity.md`
  - `.lazy-harness/decisions/0049-discovery-vs-loading-complete-lean-discovery.md`

## User-confirmed statement

On 2026-06-30 the user confirmed (option A) that this lazy-harness source repo owns its own context economy and record-first memory, and that external Pi/OMP context-compression, context-rerouting, or competing session-memory extensions are **non-adopted by default** here.

Such extensions are not banned globally — they may be valuable on downstream product hosts — but in this framework source repo they are off by default because they conflict with the harness-first evidence gate, the `.lazy-harness/AGENTS.md` grammar, and the record-first memory identity.

## Why (summary; full rationale in ADR 0052)

1. **Evidence gate**: the harness requires complete `lazy map` output and verbatim record/source/test reads; extensions that rewrite/compress/reroute `bash`/`read` can invalidate that evidence.
2. **Grammar**: `.lazy-harness/AGENTS.md` is the single behavior grammar; an injected routing `AGENTS.md` (e.g. `context-mode`) competes with it.
3. **Memory/identity**: a bundled FTS5/session-memory store competes with lazy-harness's own record-first institutional memory and lifecycle hooks.

## Installed-package baseline (2026-06-30)

Pi packages installed (`/home/lazydino/.pi/agent/npm/package.json`):

- `pi-claude-auth`, `pi-figma-remote-auth`, `pi-hashline-edit-pro`, `pi-lens`, `pi-mcp-adapter`, `pi-subagents`

Project `.pi/settings.json` additionally loads the local package `../packages/lazy-harness-pi`.

Not installed (and non-adopted by default per this policy): `@hypabolic/pi-hypa`, `context-mode`, `pi-lean-ctx`.

## Adoption path (if ever pursued)

1. Trial on a downstream product host (e.g. `medivance`) and observe effect/conflict via the dogfood loop.
2. Bring findings back here; get explicit user confirmation.
3. Record an "adopt" decision (ADR + update this SSOT) and add a TDD regression protecting harness-first evidence integrity (`lazy map`/record reads must not be silently rewritten/compressed/blocked).
