# SDD — Jcode Agent Adapter

Status: deprecated-history
Superseded by: `.lazy-harness/decisions/0059-pi-primary-jcode-decommission.md`
Date: 2026-08-01
Layer: SDD
Related ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
Related TDD: `.lazy-harness/tests/jcode-agent-adapter.md`
Related planning: `.lazy-harness/planning/jcode-runtime-adapter-pilot.md`

## Rule digest

- Status: deprecated
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
  - turn_followup
  - ask
  - interaction_request
  - needs_input
  - pre_tool
  - post_tool
  - turn_start
  - turn_end
  - JCODE_HOOK_PAYLOAD
  - /cwd
  - /cd
  - session cwd
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
  - use Jcode's typed native interaction broker for supported option gates and structured `needs_input` for unsupported runtimes
  - treat `turn_followup` as a separately bounded synchronous controller with at most one synthetic continuation per originating real-user turn
  - manage trusted-root project AGENTS suppression through a private reversible local transport flag
  - inject the canonical trusted root `.lazy-harness/AGENTS.md` on every `before_model` request
  - prefer the current request payload cwd over a stale inherited hook cwd during a same-session cwd transition
  - replace old-root pending/recent evidence before target-root context or actions are evaluated
  - make Jcode core cwd persistence transactional: a failed save restores all live cwd-derived state and exposes no successful cwd side effect
  - preserve the current live session cwd across remote reconnect/subscription instead of replaying the launcher cwd
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

The current source baseline includes Jcode lifecycle commits `38036ca63`, `eaa12fc30`, `6597ac650`, and `dcc8ed100`.

Supported official surfaces:

| Jcode surface | Semantics | Adapter use |
|---|---|---|
| project `AGENTS.md` | static project instructions in system prompt | canonical root grammar entrypoint |
| `before_model` | synchronous bounded JSON context decision immediately before a provider request | initial static harness reminder or post-tool relevant-record re-grounding |
| `turn_followup` | synchronous strict JSON decision after a fully committed turn | one bounded system-generated response-completed audit continuation |
| `turn_start` | detached observer before model generation | arm root/session turn state |
| `pre_tool` | synchronous gate; stdin tool JSON; exit 2 blocks | canonical destructive/read-debt guard |
| `post_tool` | detached observer after tool completion | append bounded success/failure evidence |
| `turn_end` | detached observer with status and assistant text | run advisory lifecycle audit and diagnostics |
| `session_start/end` | detached observers | bounded state setup/cleanup |

Observer output is ignored by Jcode. Therefore `turn_start`, `post_tool`, and `turn_end` must never be documented as prompt injection or hard blocking.

## CLI contract

```text
lazy jcode install [--dry-run] [--format=md|json] [--config=PATH] [--target=DIR] [--adapter-lazy=PATH]
lazy jcode remove  [--target=DIR] [--dry-run] [--format=md|json] [--config=PATH]
lazy jcode doctor  [--format=md|json] [--config=PATH] [--target=DIR] [--adapter-lazy=PATH]
lazy jcode smoke   [--dry-run] [--format=md|json]
lazy jcode trust   [--target=DIR] [--dry-run] [--format=md|json]
lazy jcode untrust [--target=DIR] [--dry-run] [--format=md|json]
lazy jcode trusted-roots [--format=md|json]
lazy jcode launcher-status [--launcher=PATH] [--format=md|json]
lazy jcode promote-launcher [--launcher=PATH] [--dry-run] [--format=md|json]
lazy jcode rollback-launcher [--launcher=PATH] [--dry-run] [--format=md|json]
lazy jcode hook <before-model|turn-followup|turn-start|pre-tool|post-tool|turn-end|session-start|session-end>
```

- Default config: absolute `$JCODE_HOME/config.toml` when `JCODE_HOME` is absolute, otherwise `~/.jcode/config.toml`; relative `JCODE_HOME` is never resolved from a repository cwd. Package mutations reject relative `JCODE_HOME`.
- `install` creates a timestamped sibling backup before config mutation and trusts the selected current lazy root.
- Managed hooks call the trusted adapter source through a shell-quoted absolute path.
- Trust registry: `$JCODE_HOME/lazy-harness-trusted-roots.json` or `~/.jcode/lazy-harness-trusted-roots.json`, mode `0600`, exact canonical real paths only.
- Existing unrelated TOML keys, comments, quoted keys, line endings, and trailing whitespace/newlines are byte-preserved outside exact managed additions/removals.
- A conflicting existing managed hook key stops before mutation unless it already matches the desired command. The pilot does not compose arbitrary user hook commands.
- `remove` removes only exact managed values and removes an adapter-created empty `[hooks]` table; it never removes an unrelated hook or trust entry.
- `trust`/`untrust` are explicit, reversible registry operations; a repository marker alone never grants execution.
- `install`/`trust` idempotently manage only `[prompt] ignore_project_agents = true` in `<trusted-root>/.jcode/config.local.toml`; `remove --target`/`untrust` remove only a marker-owned key/table/file.
- Existing user-owned local TOML is preserved. A user-owned `ignore_project_agents = false` is a conflict, while an already-true unmarked value remains user-owned and is never removed.
- The local config is kept private through an existing Git ignore or one exact managed `.git/info/exclude` entry. Backups are written under private Git metadata, not into the worktree.
- Outside an exact trusted root, hook commands exit `0` silently.

## Unified project activation contract

- `lazy agent activate --target <root>` is the explicit unified Pi/OMP/Jcode activation and repair surface. For Jcode it reuses the existing install/trust/local-config transaction, installs or repairs global hooks, and passes one stable adapter entrypoint resolved from the host sync marker's canonical `sourceRoot` with a current-framework fallback.
- `lazy init --target <root>` may invoke unified activation after successful framework installation because the user explicitly selected that target. Dry-run must describe the activation without mutating global config, trust, Git exclusions, or project files.
- `lazy sync --target <root>` must inspect exact-root trust before invoking Jcode repair. It may repair or diagnose an already trusted root, but an untrusted root remains untrusted and receives an explicit `lazy agent activate --target <root>` instruction.
- Unified activation is idempotent and reports Pi, OMP, Jcode global-hook, exact-root trust, local transport, and doctor readiness outcomes in one Markdown/JSON result without emitting planned file contents.
- A partial failure must restore all activation state changed by that invocation while preserving pre-existing Pi/OMP files, unrelated Jcode TOML, user-owned local config, and prior trust.
- Projects reuse one machine-global lazy-patched Jcode candidate. Project activation must not copy/build Jcode per root or silently promote the candidate over official stable/current or the normal launcher.
- Machine launcher option A is confirmed: after candidate provenance and pointer validation, atomically repoint only `~/.local/bin/jcode` to `~/.jcode/builds/lazy-patched/jcode`; preserve its exact prior target and leave official stable/current unchanged.
- `launcher-status` validates the completed candidate, binary digest, and embedded version against strict provenance. `promote-launcher` persists mode-0600 rollback state before atomic symlink replacement; `rollback-launcher` restores the exact prior symlink or missing state and refuses unrelated launcher drift.

## Runtime bridge contract

### Root resolution

Resolve candidates only from official Jcode evidence:

1. When `JCODE_HOOK_PAYLOAD.cwd` is present and non-empty, it is the current request authority and is the only root candidate.
2. Fall back to `JCODE_HOOK_CWD` only when the payload omits cwd.

This ordering is required because an inherited hook environment can briefly retain the previous root after native same-session `/cwd`. Walk upward until `.lazy-harness/bin/lazy` exists, canonicalize the real path, then require an exact trust-registry match. Do not fall back to adapter process cwd, sibling checkouts, remembered roots, or marker-only trust.

### Same-session cwd transition

- Jcode core owns `/pwd`, `/cwd [path]`, `/cd <path>`, existing-directory canonicalization, mutation and persistence of the current session `working_dir`, remote `SetCwd`/`SessionCwd`, client propagation, and the LLM cwd tool.
- The transition preserves the current session id and conversation messages. It must not create a new session or worktree.
- On the next provider request, Jcode rebuilds project instructions, skills, and headers from the updated working directory, including after visible conversation has begun.
- The adapter consumes the request payload cwd, selects the target exact-trusted lazy root, and treats any persisted state envelope whose `root` differs as invalid.
- The first target-root `before_model` atomically persists a fresh target-root envelope with empty `pending` and `recent` rows before emitting target grammar. Old-root evidence cannot satisfy a target-root gate.
- Jcode core must snapshot every live field changed by `Agent::set_working_dir`. If `session.save()` fails, it restores that snapshot before returning the error. Remote `SetCwd`, local slash commands, and the LLM cwd tool must not publish successful events or metadata for a rolled-back transition.
- Remote clients must update their reconnect/subscription cwd source when `SessionCwd` succeeds. Reconnecting after A → `/cwd` B must advertise B and must not overwrite the persisted/live session back to A.
- Implemented by Jcode commits `2f44249d1` (transactional rollback and error-only failure propagation) and `d58409274` (exact established-session reconnect uses live cwd).

### Turn start

- Create a root/session-scoped runtime state envelope.
- Arm the canonical search/read-debt journal with a static transport marker; do not classify user text.
- Do not print the reminder body because Jcode observer stdout is discarded and root `AGENTS.md` is already static prompt context.

### Before model

- Run synchronously before every actual provider request, including the initial request and requests following successful tools.
- Read the exact trusted root's `.lazy-harness/AGENTS.md` and place its complete bounded contents first in the request-scoped system reminder.
- Jcode supplies bounded structural request metadata and never requires raw provider output or unbounded conversation history.
- Before the first tool result, invoke `.lazy-harness/hooks/lifecycle/on-message-received.sh` as a static transport and pass through only strict `{"action":"allow","inject":{"body":"...","format":"system_reminder"}}` JSON.
- After successful correlated tool evidence exists, invoke `.lazy-harness/hooks/lifecycle/on-context.sh` with the bounded root/session `recent_tool_calls` envelope.
- Cap the complete UTF-8 reminder at 24,000 bytes. Dynamic lifecycle context is appended only within the remaining budget, so canonical grammar has priority.
- Empty, malformed, timed-out, or failed dynamic hook output omits only the dynamic section. Missing/empty/oversized canonical grammar or an untrusted root fails open with no stdout.
- The injected body is request-scoped dynamic system context. It is not canonical memory and must not alter Jcode's static prompt-cache portion.
- A root mismatch is persisted as a fresh empty state envelope before dynamic context is selected, so stale old-root evidence is removed even when no target-root tool has run yet.

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
- Keep `turn_end` detached and advisory. If `turn_followup` already produced a stop decision, do not duplicate that audit.
- If a synthetic continuation was issued, audit its completed response once at final `turn_end`.
- Clear per-turn evidence and followup audit markers after the final audit snapshot.

### Turn followup

- Invoke `.lazy-harness/hooks/lifecycle/on-response-completed.sh` only after the originating turn is fully committed.
- Accept only canonical strict injection JSON and normalize it to Jcode's `{"continue":{"body","reason","fingerprint"}}` contract; otherwise emit `{"stop":true}`.
- Bound the UTF-8 continuation body to 16 KiB and the complete decision to 32 KiB.
- Clear pending/recent per-turn evidence when the decision is produced so the synthetic turn cannot reuse stale proof.
- Derive a stable fingerprint from canonical root, session, and bounded body. Jcode app-core owns one-per-origin, duplicate, ask, user-input, cancellation, guardrail, and non-retryable-error suppression.
- Outside an exact trusted root, exit successfully with no output and no state.

## Prompt and option-gate boundary

- Trusted lazy roots suppress project-root `AGENTS.md`; canonical `.lazy-harness/AGENTS.md` is the project/team grammar entrypoint through `before_model`.
- `.jcode/prompt-overlay.md` is optional transport and must not contain canonical project policy.
- The approved Phase 1 baseline adds a generic `before_model` transport. Context reinjection remains a reported gap until the Jcode core implementation, adapter fixture, and trusted/untrusted live matrix pass.
- Jcode commit `eaa12fc30` adds a generic `ask` tool, session interaction broker, typed wire requests/answers/cancellation, local/remote picker, and NDJSON/ACP `needs_input` fallback. Commit `6597ac650` enforces one recommended option and bounded question/option/custom fields.
- A supported TUI advertises `native_interactions = true`; without that capability the tool returns immediately rather than hanging or reading command stdin.
- Native ask parity remains partial until the source-built picker and remote reconnect/disconnect matrix are exercised live.
- Jcode commit `dcc8ed100` adds the generic bounded `turn_followup` hook, app-core session controller, local/remote presentation, headless/server execution, cancellation, guardrail/error suppression, and wire lifecycle status.
- Bounded followup transport is installed and fixture-tested. Full parity remains partial until the source-built local/remote/headless live matrix is exercised.

## Security and state

- Never log raw user messages, assistant prose beyond Jcode's bounded turn-end field, tool results, secrets, or full tool inputs in persistent adapter state.
- Persist only canonical root-contained filesystem paths needed by guards plus tool name, status, timestamps, and hashes; reject URL-shaped, control-character, or out-of-root `path` values and never persist command/query/URL text.
- Resolve state under canonical `$LAZY_RUNTIME_ROOT` when explicitly provided; otherwise use the worktree git-dir/session runtime root, matching `runtime_paths.py`, and pass the same runtime environment to canonical hooks.
- An explicitly shared `$LAZY_RUNTIME_ROOT` may keep one session envelope, but a cwd root mismatch must replace that envelope immediately rather than retain or reactivate evidence from either root.
- Long-lived Jcode server processes must not share evidence between roots or sessions.

## Implementation map

- Status: Phases 1–3 core, unified activation, reversible launcher promotion, native same-session cwd restoration, independent review, and refreshed candidate verification complete; closing standard validation follows the final record mutation
- Primary files:
  - `/home/lazydino/dev/jcode/crates/jcode-base/src/hooks.rs` — strict bounded `before_model` execution, parsing, recursion suppression, request-kind classification, and dynamic-only application.
  - `.lazy-harness/scripts/agent-activate.ts` — unified Pi/OMP/Jcode transaction owner with stable adapter-source selection, global-hook repair, exact-root trust, content-free reporting, and Pi/OMP rollback.
  - `.lazy-harness/scripts/lazy-init.ts` — explicit post-init activation caller with framework-only opt-out.
  - `.lazy-harness/scripts/lazy-sync.ts` — trust-aware repair/report caller that never creates trust and updates its marker only after successful repair.
  - `.lazy-harness/scripts/jcode-package.ts` — launcher status/promotion/rollback validates immutable candidate provenance and preserves exact prior launcher state.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/agent/prompting.rs` — shared app-core provider request prompt boundary.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/cwd.rs` — shared cwd parser/resolver and same-session mutation contract.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/tool/cwd.rs` — LLM cwd tool and cwd-change metadata side effects.
  - `/home/lazydino/dev/jcode/crates/jcode-protocol/src/protocol.rs` — remote `SetCwd` request and `SessionCwd` event contract.
  - `/home/lazydino/dev/jcode/crates/jcode-tui/src/tui/app/turn_hooks.rs` — local TUI test-harness request boundary.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/tool/ask.rs` — bounded ask validation and typed answer/needs-input result.
  - `/home/lazydino/dev/jcode/crates/jcode-tool-core/src/lib.rs` — session interaction broker.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/server/client_interactions.rs` — answer/cancel correlation and session isolation.
  - `/home/lazydino/dev/jcode/crates/jcode-protocol/src/wire.rs` — native interaction capability and wire frames.
  - `/home/lazydino/dev/jcode/crates/jcode-tui/src/tui/interaction_picker.rs` — picker/custom/cancel UI.
  - `/home/lazydino/dev/jcode/crates/jcode-base/src/hooks/turn_followup.rs` — strict JSON, timeout, and byte-bound controller hook.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/turn_followup.rs` — session-scoped one-per-origin, fingerprint, cancellation, interaction, guardrail, and error bounds.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/agent/turn_followup.rs` — headless/server followup claim, synthetic message, execution, and lifecycle events.
  - `/home/lazydino/dev/jcode/crates/jcode-tui/src/tui/app/turn_followup.rs` — local system-generated followup presentation and queue transport.
  - `/home/lazydino/dev/jcode/crates/jcode-tui/src/tui/app/remote/turn_followup.rs` — remote lifecycle status presentation.
  - `.lazy-harness/scripts/jcode-adapter.ts` — trusted-root gating, hook normalization, canonical runtime state, owned locks, and canonical hook invocation.
  - `.lazy-harness/scripts/jcode-local-config.ts` — reversible local prompt transport, user-TOML preservation, private Git exclusion, and private backup storage.
  - `.lazy-harness/scripts/jcode-trust.ts` — mode-0600 exact canonical-root trust registry.
  - `.lazy-harness/scripts/jcode-package.ts` — TOML validation/merge/remove, trust commands, doctor, smoke, and formatting.
  - `.lazy-harness/bin/lazy` — Jcode CLI dispatch.
  - `.lazy-harness/scripts/self-test.py` — adversarial config/trust/runtime fake-hook coverage.
- Flow:
  1. Explicit install TOML-validates global hooks and the trusted-root local prompt transport, writes reversible managed state, then trusts the selected root.
  2. Jcode dispatches official events to `lazy jcode hook`.
  3. The adapter canonicalizes the live root and bridges shared lifecycle hooks only for an exact registry match.
  4. Marker-only/non-lazy projects return silently; doctor reports hooks, trust, TOML validity, and capability gaps.
  5. Native cwd changes preserve the session, rebuild target-root prompt sources, and cause the adapter to replace old-root state before target-root grammar or evidence is used.
- Key symbols:
  - `activeRoot` / `statePath` / `withState` — exact trust gate, canonical state path, stale-lock recovery, and ownership-safe cleanup.
  - `turnStart` / `preTool` / `postTool` / `turnEnd` — translate official lifecycle events without persisting raw command/query/URL text.
  - `loadTrustRegistry` / `updateTrustedRoot` / `writeTrustRegistry` — canonical root trust.
  - `installText` / `removeText` / `trustCommand` / `classifyHooks` — preserve valid TOML and stop on conflicts.
  - `updateLocalPromptTransport` / `inspectLocalPromptTransport` — own the private local flag, ignore metadata, backup, status, and exact removal contract.
  - `parse_cwd_command` / `resolve_cwd` / `Agent::set_working_dir` / `CwdTool` — Jcode core same-session cwd parsing, canonicalization, persistence, and tool transport in commit `71adb1853`.
- Tests / protection:
  - `.lazy-harness/tests/jcode-agent-adapter.md`
  - `.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter`
  - Jcode focused tests for cwd protocol/app-core plus `request_prompt_rebuilds_agents_from_updated_cwd_after_visible_conversation`.
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
