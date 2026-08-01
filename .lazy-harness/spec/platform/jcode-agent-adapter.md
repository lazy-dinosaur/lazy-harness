# SDD — Jcode Agent Adapter

Status: active-phase1
Date: 2026-08-01
Layer: SDD
Related ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
Related TDD: `.lazy-harness/tests/jcode-agent-adapter.md`
Related planning: `.lazy-harness/planning/jcode-runtime-adapter-pilot.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - Jcode adapter
  - lazy jcode
  - Jcode hook bridge
  - Jcode 기본 적용
- Surface terms:
  - before_model
  - pre_tool
  - post_tool
  - turn_start
  - turn_end
  - JCODE_HOOK_PAYLOAD
- Applies when:
  - installing, removing, smoke-testing, or debugging lazy-harness under Jcode
  - changing Jcode lifecycle payload translation or root-scoped evidence
- Must:
  - use official Jcode hooks and canonical lazy-harness lifecycle scripts
  - no-op outside an exact user-trusted lazy-harness root
  - keep installation idempotent, backed up, TOML-safe, and reversible
  - keep Jcode runtime evidence isolated by canonical runtime root and session
  - persist no raw command, query, URL, credential, or tool-result text
  - treat `before_model` as a bounded request-scoped context transport, separate from detached observers and the `pre_tool` gate
- Must not:
  - restore generated project policy under `.jcode`
  - claim observer hooks can block or inject model context
- Record completion:
  - adapter, installer, or hook-contract changes update this SDD and its TDD
- Related records:
  - `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
  - `.lazy-harness/spec/platform/pi-agent-package.md`
  - `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - `.lazy-harness/ssot/runtime-and-shared-state.md`

## Purpose

Provide a thin, reversible Jcode adapter that reuses lazy-harness canonical lifecycle hooks without duplicating policy or reviving the removed directory bridge.

## Supported Jcode baseline

The pilot baseline is Jcode `v0.64.114-dev` / base release `0.64.2`, commit `0ffe9f484`.

Supported official surfaces:

| Jcode surface | Semantics | Adapter use |
|---|---|---|
| project `AGENTS.md` | static project instructions in system prompt | canonical root grammar entrypoint |
| `before_model` | synchronous bounded JSON context decision immediately before a provider request | initial static harness reminder or post-tool relevant-record re-grounding |
| `turn_start` | detached observer before model generation | arm root/session turn state |
| `pre_tool` | synchronous gate; stdin tool JSON; exit 2 blocks | canonical destructive/read-debt guard |
| `post_tool` | detached observer after tool completion | append bounded success/failure evidence |
| `turn_end` | detached observer with status and assistant text | run advisory lifecycle audit and diagnostics |
| `session_start/end` | detached observers | bounded state setup/cleanup |

Observer output is ignored by Jcode. Therefore `turn_start`, `post_tool`, and `turn_end` must never be documented as prompt injection or hard blocking.

## CLI contract

```text
lazy jcode install [--dry-run] [--format=md|json] [--config=PATH] [--target=DIR]
lazy jcode remove  [--dry-run] [--format=md|json] [--config=PATH]
lazy jcode doctor  [--format=md|json] [--config=PATH] [--target=DIR]
lazy jcode smoke   [--dry-run] [--format=md|json]
lazy jcode trust   [--target=DIR] [--dry-run] [--format=md|json]
lazy jcode untrust [--target=DIR] [--dry-run] [--format=md|json]
lazy jcode trusted-roots [--format=md|json]
lazy jcode hook <before-model|turn-start|pre-tool|post-tool|turn-end|session-start|session-end>
```

- Default config: absolute `$JCODE_HOME/config.toml` when `JCODE_HOME` is absolute, otherwise `~/.jcode/config.toml`; relative `JCODE_HOME` is never resolved from a repository cwd. Package mutations reject relative `JCODE_HOME`.
- `install` creates a timestamped sibling backup before config mutation and trusts the selected current lazy root.
- Managed hooks call the trusted adapter source through a shell-quoted absolute path.
- Trust registry: `$JCODE_HOME/lazy-harness-trusted-roots.json` or `~/.jcode/lazy-harness-trusted-roots.json`, mode `0600`, exact canonical real paths only.
- Existing unrelated TOML keys, comments, quoted keys, line endings, and trailing whitespace/newlines are byte-preserved outside exact managed additions/removals.
- A conflicting existing managed hook key stops before mutation unless it already matches the desired command. The pilot does not compose arbitrary user hook commands.
- `remove` removes only exact managed values and removes an adapter-created empty `[hooks]` table; it never removes an unrelated hook or trust entry.
- `trust`/`untrust` are explicit, reversible registry operations; a repository marker alone never grants execution.
- Outside an exact trusted root, hook commands exit `0` silently.

## Runtime bridge contract

### Root resolution

Resolve candidates only from official Jcode evidence, in this order:

1. `JCODE_HOOK_CWD`,
2. `cwd` inside `JCODE_HOOK_PAYLOAD`.

Walk upward until `.lazy-harness/bin/lazy` exists, canonicalize the real path, then require an exact trust-registry match. Do not fall back to adapter process cwd, sibling checkouts, remembered roots, or marker-only trust.

### Turn start

- Create a root/session-scoped runtime state envelope.
- Arm the canonical search/read-debt journal with a static transport marker; do not classify user text.
- Do not print the reminder body because Jcode observer stdout is discarded and root `AGENTS.md` is already static prompt context.

### Before model

- Run synchronously before every actual provider request, including the initial request and requests following successful tools.
- Jcode supplies bounded structural request metadata and never requires raw provider output or unbounded conversation history.
- Before the first tool result, invoke `.lazy-harness/hooks/lifecycle/on-message-received.sh` as a static transport and pass through only strict `{"action":"allow","inject":{"body":"...","format":"system_reminder"}}` JSON.
- After successful correlated tool evidence exists, invoke `.lazy-harness/hooks/lifecycle/on-context.sh` with the bounded root/session `recent_tool_calls` envelope.
- Cap the normalized reminder body at 24,000 characters; empty, malformed, oversized, timed-out, failed, or untrusted results fail open with no stdout.
- The injected body is request-scoped dynamic system context. It is not canonical memory and must not alter Jcode's static prompt-cache portion.

### Pre-tool

- Read the full Jcode tool input JSON from stdin.
- Project `{ event, session_id, working_dir, tool: { name, args }, recent_tool_calls }`.
- Invoke `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh`.
- If the canonical hook emits a deny reason, write a concise reason to stderr and exit `2`.
- Otherwise exit `0`.
- Adapter/config/runtime failures fail open except for a confirmed canonical deny.

### Post-tool

- Record a bounded structural evidence row keyed by root/session.
- Use Jcode fields `TOOL_NAME`, `STATUS`, `DURATION_MS`, `OUTPUT_BYTES`, and `ERROR` only.
- Because Jcode does not expose original input in `post_tool`, correlate only one unambiguous same-session/tool pending entry inside a bounded time window.
- Evidence counts as successful read evidence only when status is `ok`; ambiguous, stale, or failed entries are removed without becoming proof.
- State uses the canonical root/session runtime path, atomically published owner-bearing locks, bounded stale recovery with owner revalidation, mode `0600`, and atomic state rename.

### Turn end

- Project `assistant_response` from `JCODE_HOOK_LAST_ASSISTANT_TEXT` and attach bounded recent tool calls from adapter state.
- Invoke the canonical response-completed hook for advisory diagnostics.
- Do not claim or attempt Pi-style bounded follow-up continuation in the pilot.
- Clear per-turn evidence after the audit snapshot is produced.

## Prompt and option-gate boundary

- Root `AGENTS.md` is the canonical Jcode prompt entrypoint.
- `.jcode/prompt-overlay.md` is optional transport and must not contain canonical project policy.
- The approved Phase 1 baseline adds a generic `before_model` transport. Context reinjection remains a reported gap until the Jcode core implementation, adapter fixture, and trusted/untrusted live matrix pass.
- Jcode has no verified native selectable `ask` tool in this baseline; agents must still stop for options, but UI parity is not claimed.

## Security and state

- Never log raw user messages, assistant prose beyond Jcode's bounded turn-end field, tool results, secrets, or full tool inputs in persistent adapter state.
- Persist only canonical root-contained filesystem paths needed by guards plus tool name, status, timestamps, and hashes; reject URL-shaped, control-character, or out-of-root `path` values and never persist command/query/URL text.
- Resolve state under canonical `$LAZY_RUNTIME_ROOT` when explicitly provided; otherwise use the worktree git-dir/session runtime root, matching `runtime_paths.py`, and pass the same runtime environment to canonical hooks.
- Long-lived Jcode server processes must not share evidence between roots or sessions.

## Implementation map

- Status: Phase 1 Jcode core committed at `38036ca63`; lazy-harness adapter fixture passed; source-build live matrix pending
- Primary files:
  - `/home/lazydino/dev/jcode/crates/jcode-base/src/hooks.rs` — strict bounded `before_model` execution, parsing, recursion suppression, request-kind classification, and dynamic-only application.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/agent/prompting.rs` — shared app-core provider request prompt boundary.
  - `/home/lazydino/dev/jcode/crates/jcode-tui/src/tui/app/turn_hooks.rs` — local TUI test-harness request boundary.
  - `.lazy-harness/scripts/jcode-adapter.ts` — trusted-root gating, hook normalization, canonical runtime state, owned locks, and canonical hook invocation.
  - `.lazy-harness/scripts/jcode-trust.ts` — mode-0600 exact canonical-root trust registry.
  - `.lazy-harness/scripts/jcode-package.ts` — TOML validation/merge/remove, trust commands, doctor, smoke, and formatting.
  - `.lazy-harness/bin/lazy` — Jcode CLI dispatch.
  - `.lazy-harness/scripts/self-test.py` — adversarial config/trust/runtime fake-hook coverage.
- Flow:
  1. Explicit install TOML-validates and writes managed global hooks with backup, then trusts the selected root.
  2. Jcode dispatches official events to `lazy jcode hook`.
  3. The adapter canonicalizes the live root and bridges shared lifecycle hooks only for an exact registry match.
  4. Marker-only/non-lazy projects return silently; doctor reports hooks, trust, TOML validity, and capability gaps.
- Key symbols:
  - `activeRoot` / `statePath` / `withState` — exact trust gate, canonical state path, stale-lock recovery, and ownership-safe cleanup.
  - `turnStart` / `preTool` / `postTool` / `turnEnd` — translate official lifecycle events without persisting raw command/query/URL text.
  - `loadTrustRegistry` / `updateTrustedRoot` / `writeTrustRegistry` — canonical root trust.
  - `installText` / `removeText` / `trustCommand` / `classifyHooks` — preserve valid TOML and stop on conflicts.
- Tests / protection:
  - `.lazy-harness/tests/jcode-agent-adapter.md`
  - `.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter`
- Ownership boundaries:
  - Lazy-Harness owns translation, root isolation, and canonical hook calls.
  - Jcode owns official event timing, observer detachment, gate timeout, and prompt loading.
  - User-owned unrelated Jcode configuration must be preserved.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
  - TDD: `.lazy-harness/tests/jcode-agent-adapter.md`
  - SSOT: `.lazy-harness/ssot/runtime-and-shared-state.md`, `.lazy-harness/ssot/harness-enforcement-policy.md`
- Machine index:
  - graph ids: `kg_jcode_agent_adapter_runtime_20260801`, `kg_jcode_agent_adapter_install_20260801`, `kg_jcode_agent_adapter_test_20260801`, `kg_jcode_agent_adapter_trust_20260801`
  - generated index key: pending regeneration

## Rule placement

- Rule: Jcode support uses official hooks through a root-detecting, reversible thin adapter.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/jcode-agent-adapter.md`
- Why not AGENTS.md: this record owns runtime payload/config contracts, not general agent grammar.
- Why not `.jcode`: Jcode config transports the hook; it does not own the contract.
- Confirmation: user-confirmed 2026-08-01

## Discovery capture

- DDD: no independent delta.
- SDD: this record owns the new runtime adapter contract.
- BDD: no independent product-visible flow.
- TDD: independent regression contract in `.lazy-harness/tests/jcode-agent-adapter.md`.
- ADR: architecture decision in `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`.
- SSOT: independent delivery-boundary delta recorded in `.lazy-harness/ssot/harness-enforcement-policy.md`; runtime path ownership remains unchanged.
- Planning: staged pilot in `.lazy-harness/planning/jcode-runtime-adapter-pilot.md`.
