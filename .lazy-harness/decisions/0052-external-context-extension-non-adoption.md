# ADR 0052 — External Context-Compression/Memory Pi Extensions: Non-Adoption by Default in the Lazy-Harness Source Repo

Status: accepted
Date: 2026-06-30
Layer: ADR
Related SSOT: `.lazy-harness/ssot/external-context-extension-policy.md`, `.lazy-harness/ssot/project-identity.md`, `.lazy-harness/ssot/rule-sources.md`
Related ADR: `.lazy-harness/decisions/0049-discovery-vs-loading-complete-lean-discovery.md`, `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`, `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`
Related Planning: `.lazy-harness/planning/external-agent-harness-reference.md`
Related candidate: `.lazy-harness/knowledge/candidates.jsonl#candidate-external-pi-context-compression-packages-eval-20260630`

## Rule digest

- Status: active
- Layer: ADR
- Scope: host-project
- Applies when:
  - considering installing an external Pi/OMP package that intercepts, compresses, or reroutes `bash`/`read`/`grep`/`find`/`ls` or `tool_call`/`tool_result`, injects its own routing `AGENTS.md`, or runs a competing session memory/knowledge store
  - evaluating context-window-savings extensions such as `@hypabolic/pi-hypa`, `context-mode`, or `pi-lean-ctx`
- Must:
  - treat such extensions as non-adopted by default in this lazy-harness source repo
  - require an explicit user-confirmed decision plus a downstream dogfood-host trial before any adoption here
  - if ever adopted in this repo, add a TDD regression protecting harness-first evidence integrity (`lazy map` and record reads must not be silently rewritten/compressed/blocked)
- Must not:
  - install or enable a competing context-compression/memory/routing extension in this repo without user confirmation
  - let an external extension reroute or compress the `bash`/`read` outputs the harness-first evidence gate depends on, or inject a second routing `AGENTS.md` grammar that competes with `.lazy-harness/AGENTS.md`
- Record completion:
  - adoption or non-adoption changes update this ADR plus `.lazy-harness/ssot/external-context-extension-policy.md`
- Related records:
  - `.lazy-harness/ssot/external-context-extension-policy.md`
  - `.lazy-harness/ssot/project-identity.md`
  - `.lazy-harness/decisions/0049-discovery-vs-loading-complete-lean-discovery.md`

## Context

On 2026-06-30 the user evaluated external Pi packages that advertise large context-window savings for adoption in this repo's workflow:

- **`@hypabolic/pi-hypa`** (FSL-1.1): a Pi extension that intercepts Pi's `bash` tool via `hypa rewrite --json` and compresses shell output with deterministic local reducers (`.NET` binary + local SQLite, `hypa_*` CLI-backed tools, `/hypa` diagnostics).
- **`context-mode`** (Elastic-2.0, v1.0.169): a more invasive extension+skill that registers `tool_call`/`tool_result`/`session_start`/`before_agent_start`/`session_before_compact`/`session_compact`/`session_shutdown` hooks, **injects its own routing `AGENTS.md` plus tool-routing enforcement that can block tools**, reroutes `read`/`grep`/`find`/`ls`/`bash`, and runs an FTS5 knowledge base with session snapshot/resume memory injection (claims ~98% context savings, 6 MCP sandbox tools, `/ctx-stats` `/ctx-doctor`).
- **`pi-lean-ctx`** (sibling discovered in the same catalog): routes `bash`/`read`/`grep`/`find`/`ls` through `lean-ctx` with a persistent session cache.

These tools are legitimately useful for reducing noisy tool output. But this checkout is the standalone **lazy-harness framework source-of-truth repo** (`.lazy-harness/ssot/project-identity.md`), whose identity is record-first institutional memory plus a harness-first evidence gate. Three structural conflicts arise specifically here:

1. **Harness-first evidence gate conflict.** The search-debt gate requires the agent to read the *complete* `lazy map` discovery output (ADR 0049) and the *real* record/source/test text via `read`. Extensions that rewrite, compress, or reroute `bash`/`read` output can silently break that evidence (lost record cues, wrong drill-down, invalidated read proof). `context-mode` and `pi-lean-ctx` reroute `read` itself; `pi-hypa` rewrites `bash`.
2. **`AGENTS.md` grammar conflict.** `.lazy-harness/AGENTS.md` is the single source of truth for agent behavior in this repo (§0). `context-mode` injects its own routing `AGENTS.md` and enforcement, creating two competing grammars.
3. **Competing memory/identity conflict (most fundamental).** `context-mode`'s FTS5 knowledge base + session memory injection directly competes with lazy-harness's reason for being (record-first memory, knowledge graph) and stacks a second lifecycle-hook layer (ADR 0016) and a second memory store on top of the framework's own context economy (ADR 0049 complete-lean-discovery + JIT targeted loading).

The measurable upside (compressing long build/test/git logs) is larger on real downstream product hosts than in this framework source repo, where the dominant tool traffic is `lazy map`/record reads that must stay verbatim.

## Decision

Adopt a **non-adoption-by-default** stance for external Pi/OMP context-compression, context-rerouting, or competing-session-memory extensions in this lazy-harness source repo.

- Do not install or enable such an extension here without an explicit user-confirmed decision.
- If adoption is pursued, first trial it on a downstream product host (e.g. `medivance`) and observe via the dogfood loop; promote to an explicit "adopt" decision here only after user confirmation.
- If ever adopted in this repo, add a TDD regression that protects harness-first evidence integrity: `lazy map` discovery output and `.lazy-harness` record reads must not be silently rewritten, compressed, or blocked by the extension.

This decision is the architectural "why"; the operational stance and the current installed-package baseline live in `.lazy-harness/ssot/external-context-extension-policy.md`.

## Consequences

### Positive

- Protects the harness-first evidence gate and the verbatim-read contract from silent interception.
- Keeps a single `AGENTS.md` grammar and a single record-first memory store in the source repo.
- Preserves the framework's own context economy (ADR 0049) as the canonical approach.

### Negative

- This repo forgoes the advertised context-window savings of these extensions.
- Long shell logs here are not auto-compressed; the agent relies on JIT targeted loading instead.

### Mitigation

- Downstream product hosts remain free to evaluate/adopt these tools via the dogfood loop, where the savings are larger and the record-first identity is consumed rather than authored.
- A future "adopt" decision can be made per-host with its own ADR/SSOT and the required evidence-integrity regression.

## Implementation map

- Status: `records-only` (policy decision; no source code change in this turn)
- Primary records:
  - `.lazy-harness/decisions/0052-external-context-extension-non-adoption.md` — this ADR (why / trade-off).
  - `.lazy-harness/ssot/external-context-extension-policy.md` — operational stance + installed-package baseline.
  - `.lazy-harness/knowledge/candidates.jsonl#candidate-external-pi-context-compression-packages-eval-20260630` — originating evaluation discovery (promoted by this ADR).
- Evidence baseline:
  - Installed Pi packages (`/home/lazydino/.pi/agent/npm/package.json`): `pi-claude-auth`, `pi-figma-remote-auth`, `pi-hashline-edit-pro`, `pi-lens`, `pi-mcp-adapter`, `pi-subagents`; project `.pi/settings.json` loads `../packages/lazy-harness-pi`. Neither `@hypabolic/pi-hypa`, `context-mode`, nor `pi-lean-ctx` is installed.
- Protective test (deferred until/unless adoption): harness-first evidence-integrity regression per the Decision.
