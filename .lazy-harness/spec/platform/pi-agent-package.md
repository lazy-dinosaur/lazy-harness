# Pi / OMP Agent Package Contract

Status: active
Layer: SDD

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - Pi 확장
  - pi extension
  - 패키지 계약
- Applies when:
  - installing, smoke-testing, or debugging the Pi/OMP lazy-harness package or its extension bridge
  - wiring `before_agent_start`/`tool_call` events or `lazy pi`/`lazy omp` wrapper commands
- Must:
  - declare both `pi` and `omp` manifest sections; OMP must not depend on Pi fallback
  - keep separate `lazy pi`/`lazy omp` wrapper UX over one shared package core
  - normalize Pi shell aliases to `bash` before the guard, and resolve root from the live session cwd
  - preserve both Pi string and OMP string-array system prompts; scope runtime evidence by lazy root
  - force-load the FULL `.lazy-harness/AGENTS.md` grammar (§0–§2.5) into Parent and ordinary Pi/OMP agent system prompts at `before_agent_start`, once per session, deduped by the `Lazy-Harness AI` title marker and fail-open — OMP/Pi otherwise only load a compact activation pointer, not the grammar body
  - exempt only the explicit package-owned `LAZY_HARNESS_ROLE: record-reader/v2` marker from ordinary Parent lifecycle: Parent keeps full AGENTS grammar, complete overview discovery, governing-record reads, map approval/reopening, and semantic authority; the Reader receives one dedicated two-mode Work Packet contract, canonical records-only enforcement, steer-preserved role identity, and no Parent response-completion hook. Mode must be explicit and never inferred from objective text; root/revision verification must use three separate exact probes (`pwd`, git root, HEAD) because compound shell probes remain blocked; the Reader launch transport must disable native supervisor/intercom coordination and set equal soft/hard limits to the packet tool budget so `contact_supervisor` and premature soft nudges are absent; no v1/faithful experiment profile is exposed
  - implement `candidate-map` as a non-authoritative evidence-question/coverage proposal over Parent-supplied facets/inventory/concrete nodes, and `claim-evidence` as loading of one Parent-approved bundle; conserve input coverage, use root/revision/snapshot/overview/epoch identity plus path/hash/range provenance, force `needs-remap` for new questions/overlap/dependency changes, and return overflow instead of false completion
  - use compact `record-reader-admission/v2` for new packets while retaining archived v1 validation: Parent envelope keeps full identity/scope and a canonical digest; model payload emits the digest plus normalized `F/I/N/V/R/Q/B/D` refs, one record/range table, and one coverage authority. Candidate coverage remains <=32 ids and claim question/facet bases <=16. Output uses a <=6,000 soft target and <=12,000 hard cap: over-target evidence remains valid with a warning, while hard-cap overflow returns non-success rather than trimming. Admission independently validates digest, short-id/range references, exact coverage/node/claim closure, and success consistency. Runtime tool/lifecycle enforcement and Parent semantic/source/merge authority remain unchanged.
  - keep Reader evidence process-local and non-transferable: Reader start/steer must not clear or establish Parent work-unit fingerprints; Reader tool results must not enter Parent evidence/recent-tool caches; Reader `context` and `agent_end` must bypass Parent lifecycle. Pi Subagents supplies fresh child runtimes, while sequential same-process fixtures protect the isolation contract
  - keep the harness interactive grammar live without replaying it: force-load the full `.lazy-harness/AGENTS.md` once per Parent/ordinary runtime session, then keep normal-turn reminders pointer-only
  - establish Pi/OMP grounding once per work unit: after one successful `lazy map --overview` result and one directly read governing record, cache the overview marker plus that record’s content hash; later normal messages reuse valid fingerprints with visible `status=reused-work-unit` and no system-prompt replay
  - invalidate work-unit reuse only for a new runtime session, explicit non-extension steer, or changed/deleted governing-record fingerprint. A normal message boundary alone must not re-arm debt; genuinely new-scope judgement stays LLM-owned and user text is never classified in lifecycle code
  - invoke `on-context.sh` only after the first successful mutation result (`edit`/`write`/patch family), never after reads/searches. Its body is pointer-only, at most five lines, and may not run or inject map output, record lists, operating-rule catalogs, or exact-intent resolver output
  - keep operating-rule/capability catalogs and exact-intent resolution explicit/on-demand. Agents resolve the single immediate source-work intent when needed and reuse the result; hooks do not enumerate every rule or resolve profiles after file reads
  - when source code changes, let the agent explicitly resolve the exact mechanical source-work intent once before the coherent mutation batch. The framework Code Organization Profile remains a recommend-level baseline, host additions remain preserved, and no context hook may infer architecture/profile or replay resolver results after reads
  - re-ground and RE-ARM MID-TURN steered user input: Pi's default Enter steers mid-turn and skips `before_agent_start`, so a steered instruction would otherwise inherit the previous topic's read-debt evidence and lose the §2.1 record-search push. For every non-extension, non-empty `event.streamingBehavior === "steer"`, the `input` handler must (1) advance a root-scoped evidence epoch, (2) clear prior recent-tool evidence, (3) transform the text with a compact steer re-ground reminder that fresh post-steer map/read evidence is required and prior approvals may be stale per ADR 0038, and (4) force the next `context` call to re-inject the harness re-grounding body. Every allowed `tool_call` is tagged with its start epoch; a `tool_result` from an older epoch must not repopulate evidence after the steer. This is generic transport enforcement: no steer-text classification, command allowlist, or semantic debt row. Empty and extension-injected inputs remain exempt (ADR 0051 2026-07-03 amendment; fresh-evidence hardening user-approved 2026-07-08).
  - project the canonical lifecycle payload that `on-response-completed.sh` helpers expect: every current-turn `recent_tool_calls` entry carries string `args_preview`, `edit_target`, `evidence_epoch`, and `is_error`; `agent_end` carries `assistant_response` + `last_user_message` from `event.messages`. Normal turn starts advance the root evidence epoch, and `agent_end` must filter out older epochs. This preserves structural failed-call evidence without letting stale calls satisfy or trigger lifecycle helpers
  - keep `agent_end` diagnostics opt-in, fail-open, runtime-local, and content-free: `LAZY_PI_AGENT_END_TRACE=1` may append structural message roles/content kinds, byte counts/hashes, recent tool names, hook status/fingerprints, and advisory fingerprints to `$LAZY_RUNTIME_ROOT/logs/pi-agent-end-trace.jsonl`; default behavior writes nothing and the trace must never contain conversation prose, tool arguments, or tool results
  - keep OMP's native interactive `ask` selector active under tool discovery mode so harness option gates (AGENTS §2.3) render as native selectable choices, not plain A/B/C text
  - surface a short visible per-start read-debt marker (`lazy-harness read-debt`, runtime marker, root, `status=armed|not-armed(synthetic-turn)|not-armed(hook-empty)|not-armed(hook-timeout)|not-armed(hook-error)`, `phase=armed|debug`, optional `hook=<detail>`, `tool-guard=ready`) so users can distinguish extension-loaded/armed turns from stale, synthetic/steering, timed-out, hook-failed, or empty-hook sessions. The hook payload may include large conversation context, so `on-message-received.sh` must not pass the raw payload through argv/env; it must use a temp-file/ref path handoff for Python helpers to avoid ARG_MAX (`argument list too long`) failures. Synthetic/steering turns must remain debug-only: do not create a read-debt journal row, but do display the not-armed status/reminder. If a lazy-root action tool runs while the turn was not armed, block with a read-debt-not-armed reason that includes the status/detail
  - write project-local Pi skill settings during `lazy agent activate`: merge `.pi/settings.json` with `skills: ["../.claude/skills", "../.codex/skills", "../.agents/skills"]` plus `enableSkillCommands: true`, so project-owned Claude/Codex/Agents skills are loaded without relying on global wildcard behavior
  - surface pending host record migration at turn-start (user-approved resume-surfacing decision, 2026-07-05; graph probe added same day): the `on-message-received.sh` reminder appends a deterministic `Host record migration PENDING` line via `helpers/host_migration_state.py` (bounded fail-open probes: `lazy record-lint --format=json` + `lazy graph-hygiene --migration-plan --format=json`, each timeout < extension hook budget) when any count > 0, pointing at the guided `lazy-record-quality`/`lazy-memory-backfill`/`lazy-graph-migrate` resume paths — closes the gap where `[Next steps]` stdout was visible only to whoever ran `lazy update` and host agents never saw pending backfill/graph state (retro `fb-mr7g01i9-ui`). Host-state-derived only, never user-text classification; never rewrites records or graph rows
- Must not:
  - duplicate canonical policy in the extension, block Parent/ordinary read-only overview/parallel work, let the Reader run overview or infer packet mode from user text, or commit generated `.pi/`/`.omp/` by default
- Record completion:
  - changes to the package manifest, wrapper UX, or adapter bridge update this SDD and `check_pi_package_layout_and_contract`
  - CO-CHANGE COMPLETENESS (user-confirmed rule, 2026-07-05): any framework surface change (CLI command/flag/format rename or removal, contract/schema change, help-text change) must update ALL referencing distributed artifacts IN THE SAME CHANGE — `packages/lazy-harness-pi/skills/*/SKILL.md`, `packages/lazy-harness-pi/prompts/**`, extension bridge, `bin/lazy` help text, and parser dual-forms (`--flag value` / `--flag=value`) — so a downstream `lazy update` + live-linked Pi package always deliver a mutually consistent state. Precedent defects: `--format=jcode-prompt` left in lazy-impl-map-migrate after the `agent-prompt` rename; `init [--target=DIR]` help vs space-only parser (both fixed 5d88a31).
- Related records:
  - `.lazy-harness/decisions/0043-pi-native-package-in-source-repo.md`
  - `.lazy-harness/decisions/0047-pi-omp-shared-package-separate-install-ux.md`
  - `.lazy-harness/spec/platform/code-organization-profile.md`

## Purpose

Provide a shared Pi Coding Agent / Oh My Pi (OMP) package that installs lazy-harness behavior without a separate repository, while keeping Pi and OMP install UX separate.

## Package root

```text
packages/lazy-harness-pi/
```

This package is framework-source owned. It is installed into Pi or linked into OMP by local path and locates the active host root at runtime.

## Manifest contract

`packages/lazy-harness-pi/package.json` must include:

```json
{
  "name": "@lazy-dinosaur/lazy-harness-pi",
  "keywords": ["pi-package", "omp-plugin"],
  "pi": {
    "extensions": ["./extensions"],
    "skills": ["./skills"],
    "prompts": ["./prompts"],
    "subagents": { "agents": ["./agents"] }
  },
  "omp": {
    "extensions": ["./extensions"],
    "skills": ["./skills"],
    "prompts": ["./prompts"]
  },
  "pi-subagents": { "agents": ["./agents"] }
}
```

OMP official source supports `package.json#omp` first and falls back to `package.json#pi`. The package must declare both so OMP does not depend on legacy Pi fallback behavior.

## Extension contract

`packages/lazy-harness-pi/extensions/lazy-harness/index.ts` must:

1. export a default Pi extension function,
2. resolve the active project cwd from live runtime state (`ctx.sessionManager.getCwd()` when present), then event cwd, then `ctx.cwd`, and walk upward to find `.lazy-harness/bin/lazy`,
3. handle `before_agent_start` in two role modes: Parent and ordinary roles invoke `on-message-received.sh` and receive the full interactive grammar plus search/read-debt reminder; only the package-owned `LAZY_HARNESS_ROLE: record-reader/v2` marker receives the compact role reminder without `.lazy-harness/AGENTS.md`. Inside that one trusted role, the Work Packet—not raw objective classification—must explicitly select `candidate-map` or `claim-evidence`. The Reader verifies identity with three separate calls—`pwd`, `git rev-parse --show-toplevel`, and `git rev-parse HEAD`; shell separators/compound probes remain denied. Its launch transport disables native supervisor/intercom coordination, uses `soft == hard == budget.toolCalls`, and passes a strict per-packet `outputSchema`; a leaked `contact_supervisor` remains role-blocked as defense in depth. It may use only Pi Subagents' internal `structured_output`, drill the exact supplied concrete-node commands, directly read/grep canonical record layers, and run exact `git hash-object -- <canonical-record-path>` for working-tree content provenance; complete overview, source, mutation, broad search, file output, and recursion remain blocked. The visible marker includes `profile=record-reader/v2`,
4. handle `tool_call` by normalizing Pi tool payload into lazy lifecycle JSON and invoking `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh`,
5. expose `lazy_move_project` as a tool that prepares the target/worktree and, when `ctx.switchSession` is available, calls the same direct session-switch implementation as `/lazy-move`; it must not claim success by queuing `/lazy-move` as a follow-up chat message because Pi follow-ups are agent-visible user messages, not registered command executions. When direct switching is unavailable, the tool must return an explicit manual `/lazy-move ...` instruction instead of saying it queued the switch,
6. return `{ block: true, reason }` when the lazy hook emits a deny reason; additionally, if a lazy root is detected but the active turn has no armed read-debt packet and an action tool is about to run, block with a `read-debt not armed` diagnostic that names the status rather than silently allowing action,
7. handle `tool_result` by retaining bounded root-scoped history for later guards and tagging each accepted result with its current evidence epoch/error state. Only the first successful mutation result (`edit`/`write`/patch family) may mark the root pending for one context reminder; reads/searches never schedule context replay. Results whose call began in an older normal-turn/steer epoch are ignored. Reader results bypass Parent history, work-unit fingerprints, pending context, and lifecycle state entirely.
8. register convenience commands: `/lazy-map`, `/lazy-doctor`, `/lazy-check`, `/lazy-validate`, `/lazy-test`, `/lazy-sync`, `/lazy-update`. `/lazy-check` is the edit-loop default, `/lazy-validate --plan standard` is the one-final-boundary path, and `/lazy-test` explicitly requests a fresh full regression.
9. handle `agent_end` (Pi/OMP turn-end; the `response.completed` analogue, fired once per user prompt) by invoking `.lazy-harness/hooks/lifecycle/on-response-completed.sh` with lifecycle JSON and only tool results whose evidence epoch matches the active turn. Current-turn failed calls remain present with `is_error: true`; earlier-turn calls are excluded. Drive a bounded continuation for any advisory inject body via `pi.sendUserMessage(body, { deliverAs: "followUp" })` so the agent addresses the gate after the current turn completes. `sendUserMessage` always triggers a turn, and `agent_end` fires while the agent is still `processing`; a bare call therefore throws `Agent is already processing. Use steer() or followUp()...`, so `deliverAs: "followUp"` is required to queue the continuation instead of starting one immediately. Loop safety is bounded on two axes: the SAME unresolved advisory drives at most `MAX_ADVISORY_CONTINUATIONS` (2) turns, and an alternating chain of different advisory bodies drives at most `MAX_ADVISORY_CHAIN_CONTINUATIONS` (1) follow-up turn; after the cap, the adapter must not send another chat/display message into the conversation and may only surface a transient UI notification/log. An empty advisory body (gate resolved) resets the per-root counter. A new human prompt also resets the cap when it differs from the queued advisory body, while synthetic follow-up turns retain the cap so they cannot loop.
10. handle `context` (fired before each LLM call) by injecting a compact re-grounding reminder message into `messages`—sourced from `.lazy-harness/hooks/lifecycle/on-context.sh`—at most once per normal turn after the first successful mutation batch. Parallel or sequential mutations that complete before the first callback collapse into that batch; reads/searches never set pending state, and later mutations in the same turn do not restart re-grounding after a body has been cached/injected. `before_agent_start` and explicit Parent mid-turn steer clear the cached body for a fresh evidence epoch; Reader `context` always bypasses this Parent lifecycle without consuming pending Parent state. Missing, failed, empty, or malformed context hooks fail open for the current callback but retain pending state for one retry. Neither hook nor extension may classify user text or invent policy semantics. The injected message is a `UserMessage` wrapping the body in a `<system-reminder>` tag.
11. project a canonical `agent_end` lifecycle payload for the `on-response-completed.sh` helpers: extract `assistant_response` and `last_user_message` from `event.messages`; attach `args_preview`, `edit_target`, `evidence_epoch`, and `is_error` to each recent-tool entry; and filter entries to the current normal-turn evidence epoch. The bridge may retain older root-scoped calls for bounded context use, but response-completion helpers must never receive them. Failed current-turn calls remain structural facts and cannot be presented as successful capture.
12. keep the OMP/Pi native `ask` selector available for option gates: on `before_agent_start`, add `ask` to the active tool set (`ensureAskToolActive` — add-only, only when the `ask` tool exists, i.e. interactive sessions) so tool discovery mode (>40 tools) does not hide it. Fail-open — runtimes without `getAllTools`/`setActiveTools` or non-interactive/subagent sessions fall back to plain-text option gates,
13. use one root-scoped evidence epoch for both normal turns and mid-turn steering. Every `before_agent_start` advances the epoch so `agent_end` cannot inherit prior-turn tools. For non-extension, non-empty mid-turn steers (`event.streamingBehavior === "steer"`), advance again, clear prior recent evidence, append a compact `<system-reminder>` requiring fresh post-steer map/read evidence, and set pending re-ground (clearing the cached body). Tag every allowed `tool_call` with its start epoch and accept its `tool_result` only while that epoch still matches; this excludes late results from both earlier normal turns and pre-steer parallel tools. No steer-text classification or command-specific policy is allowed.
14. when and only when `LAZY_PI_AGENT_END_TRACE=1`, write content-free `pi-agent-end-trace/v1` rows to `$LAZY_RUNTIME_ROOT/logs/pi-agent-end-trace.jsonl` after `on-response-completed.sh` returns. Resolve the path through `runtime_paths.py` or an explicit `LAZY_RUNTIME_ROOT`; include only structural role/content-kind metadata, byte counts/hashes, bounded tool names, hook status/fingerprints, and advisory fingerprints. The trace keeps the newest 50 rows, at most 40 message shapes per row, 12 content-kind entries per message, and 40 tool names; metadata strings are capped (128 characters maximum, with tighter role/kind/signal caps). Retention rewrites through a temporary file plus atomic rename. Trace resolution or writing failure is fail-open and must not change continuation behavior.

Pi shell aliases `cmd`, `command`, `shell`, and `terminal` must normalize to lazy `bash` before the guard runs. Otherwise shell actions can bypass read-debt enforcement because the canonical helper classifies `bash` as an action tool.

## Install contract

Clean default:

The source checkout must not require active Pi installation settings. After a factory reset, `~/.pi/agent/` and project-local `.pi/settings.json` may be absent. The package remains installable from source, but it is not installed by default.

Cross-platform dependency contract:

- Base lazy-harness installation requires `bash`, `git`, `bun`, `python3`, and a git repository target. The public installer must fail before mutation with macOS/Linux install hints when `git`, `bun`, or `python3` is missing.
- `curl` is required only for the remote `curl ... | bash` installer form and Bun's official install command.
- Pi wrapper commands require the official `pi` binary on `PATH`; OMP wrapper commands require `omp` on `PATH`. `lazy pi/omp doctor` reports missing binaries without mutating settings unless `--strict` is requested.
- Antigravity MCP Google ADC bridge export commands require `gcloud` only for servers using `authProviderType: "google_credentials"`.

Recommended wrapper commands:

```bash
.lazy-harness/bin/lazy pi install
.lazy-harness/bin/lazy pi install --local
.lazy-harness/bin/lazy pi install --global
.lazy-harness/bin/lazy pi list
.lazy-harness/bin/lazy pi smoke
.lazy-harness/bin/lazy pi doctor
.lazy-harness/bin/lazy pi remove --local
.lazy-harness/bin/lazy pi remove --global
.lazy-harness/bin/lazy omp install
.lazy-harness/bin/lazy omp list
.lazy-harness/bin/lazy omp smoke
.lazy-harness/bin/lazy omp doctor
.lazy-harness/bin/lazy omp remove
.lazy-harness/bin/lazy agent activate --target /path/to/project
```

The wrapper keeps the package path consistent, supports `--dry-run` for install/remove/smoke, and intentionally defers npm/standalone publishing until official Pi and OMP runtime smoke are stable.

Pi persistent install defaults to the user-global runtime bootstrap: `lazy pi install` maps to `pi install <package> --no-approve`. `--global` remains accepted as explicit spelling, and `--local` remains available for advanced project-local package attachment. Pi persistent remove still requires explicit `--local` or `--global` because it is destructive. OMP persistent install uses **live dev-link** via `omp plugin link <path>` (NOT `omp plugin install`, which snapshots a stale copy into `~/.omp/plugins/node_modules` and does not track source) — this gives OMP the same live-source tracking Pi gets from its `.pi/settings.json` package path, so a framework source change propagates to all OMP hosts with no reinstall. It is independent of Pi `.pi/settings.json`. Use `lazy omp smoke` for one-run, non-persistent OMP loading.

The wrapper separates two roots:

- **source root** — the lazy-harness checkout containing `packages/lazy-harness-pi`; default is the wrapper's own source checkout.
- **target repo** — the repository whose Pi settings are affected by `--local`; default is the original invocation cwd, even if the wrapper later changes directory internally.

For another repo, call the wrapper by full path from that repo:

```bash
cd /path/to/other/repo
/path/to/lazy-harness/.lazy-harness/bin/lazy pi install --local
```

This maps to a target-repo-local Pi install using the source package path:

```bash
pi install -l /path/to/lazy-harness/packages/lazy-harness-pi --approve
```

`--local` also ensures the target repo's `.git/info/exclude` contains `.pi/` before persistent install, so generated project-local Pi settings are not accidentally committed to teammate repos. `--global` writes user-global Pi settings only.
Project activation is separate from package installation. An activated project is identified by `.lazy-harness/bin/lazy`; the globally loaded extension must no-op when `ctx.cwd` cannot resolve that file. `lazy agent activate --target <repo>` transactionally creates project-local `.pi/APPEND_SYSTEM.md` and `.omp/APPEND_SYSTEM.md` pointer prompts, merges `.pi/settings.json` with project-relative skill paths (`../.claude/skills`, `../.codex/skills`, `../.agents/skills`) and `enableSkillCommands: true`, and adds `.pi/` / `.omp/` to that repo's `.git/info/exclude`. `lazy init` activates the explicitly selected new project by default; `--skip-agent-activation` retains framework-only installation. `lazy sync` checks or repairs Pi/OMP activation independently of any retired runtime state. Pi is stable; OMP remains Experimental.

Global install for all Pi projects:

```bash
pi install /path/to/lazy-harness/packages/lazy-harness-pi --no-approve
```

This creates/writes user-global Pi settings with a path relative to the user's global Pi settings directory. The exact relative path is machine-specific, for example:

```json
{
  "packages": ["../../dev/lazy-harness/packages/lazy-harness-pi"]
}
```

Global install is required when Pi is used from multiple existing projects. Project-local install only affects the current repository.

Project-local install:

```bash
pi install -l /path/to/lazy-harness/packages/lazy-harness-pi --approve
```

This creates/writes source-repo project-local Pi settings with a path relative to that repo's `.pi/settings.json`, for example:

```json
{
  "packages": ["../packages/lazy-harness-pi"]
}
```

Project-local `.pi/settings.json` is generated only when intentionally attaching this checkout. It must not be committed as the default clean state.

One-run smoke:

```bash
pi -e /path/to/lazy-harness/packages/lazy-harness-pi --help
omp -e /path/to/lazy-harness/packages/lazy-harness-pi --help
```

OMP persistent plugin link:

```bash
omp plugin link /path/to/lazy-harness/packages/lazy-harness-pi
omp plugin uninstall @lazy-dinosaur/lazy-harness-pi
```

## Boundaries

- The extension is a bridge, not a duplicate policy engine.
- The canonical prompt/runtime behavior remains in `.lazy-harness/hooks/lifecycle/**` and `.lazy-harness` records.
- Pi `tool_call` is a hard-block surface; the extension must preserve the recent relaxed policy by blocking only actual mutation/evidence guard denials.
- Read-only overview batch/parallel behavior must not be blocked by this package.
- Pi shell aliases `cmd`, `command`, `shell`, and `terminal` must not bypass the guard.
- Because Pi/OMP extensions run with project extension permissions, package README must document the trust boundary.
- Global install must avoid cross-repo evidence contamination: runtime state such as `recent_tool_calls` and active packet IDs is scoped by detected lazy root.
- Record Reader dispatch disables the Pi Subagents supervisor bridge, aligns runtime tool-call soft/hard limits with the packet tool budget including a reserved final `structured_output`, supplies the compact-v2 dynamic schema, and exposes that internal tool only with active absolute schema/capture paths. Output soft target/hard cap are independent of tool-call limits. Parent rejects any non-valid independently rebuilt receipt before bundle approval or success use; no default model or semantic/merge authority is introduced.
- OMP Phase 2 compatibility: `before_agent_start` must preserve both official Pi string `systemPrompt` values and OMP string-array `systemPrompt` blocks. When OMP sends `systemPrompt: string[]`, append the lazy reminder as a new prompt block instead of coercing the array to a comma-joined string.

## Implementation map

- `packages/lazy-harness-pi/package.json` — shared Pi/OMP package manifest with explicit `pi` and `omp` resources plus package-owned `./agents` discovery for Pi Subagents.
- `packages/lazy-harness-pi/agents/record-reader.md` — single opt-in v2 role with two modes, full Parent envelope + compact output digest, short-id catalogs, normalized provenance/coverage, soft 6k target/hard 12k cap, fixed-point remap, bridge-off/equal tool budget, overflow, and Parent reread rules.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — event bridge implementation plus role-aware prompt/tool/lifecycle isolation and `/lazy-check`, `/lazy-validate`, and explicit fresh/full `/lazy-test` command surfaces.
  - `resolveInvocationCwd` keeps hook and `/lazy-*` command root selection aligned with the live Pi/OMP session cwd after runtime `/move` re-scopes the session.
  - `systemPromptIncludesBody` / `appendSystemPromptBody` preserve official Pi string prompts and OMP string-array prompt blocks during `before_agent_start` reminder injection.
  - `lazyAgentRole` recognizes only the v2 marker; `recordReaderReminder` preserves Parent authority, compact-v2 digest/reference guidance, output soft/hard policy, bridge-off/equal tool budget, and separate probes across start/steer. `recordReaderToolDenial` keeps the same records-only tool boundary and schema/capture-gated `structured_output`.
  - `ReadDebtStatus` / `classifyReadDebtStatus` / `steeringReminder` distinguish armed human turns from synthetic, hook-empty, hook-timeout, and hook-error turns; synthetic turns get a no-journal steering reminder and not-armed action block status/detail.
  - `workUnitEvidenceByRoot` / `observeWorkUnitEvidence` / `workUnitEvidenceValid` cache one overview plus governing-record content hashes, reuse them across later normal turns, and invalidate on record drift or explicit steer.
  - the `context` handler + `REGROUND_MUTATION_TOOLS` trigger one pointer-only reminder after the first successful mutation, never after reads/searches; failed hooks retain pending state only for that mutation boundary.
  - `evidenceEpochByRoot` / `toolCallEpochsByRoot` still isolate active-turn response payloads and reject late pre-steer results without classifying user text.
  - `ensureAskToolActive` keeps the native option selector available; `writeAgentEndTrace` remains opt-in and content-free.
- `.lazy-harness/hooks/lifecycle/on-message-received.sh` — first-grounding pointer body and sanitized debt row; no inventory/catalog replay.
- `.lazy-harness/hooks/lifecycle/on-context.sh` — five-line pointer-only mutation-boundary reminder; performs no map, record, catalog, or resolver subprocess.
- `.lazy-harness/hooks/lifecycle/helpers/operating_rule_catalog.py` — explicit/on-demand registry discovery and resolver rendering; no longer imported by turn/context reminder bodies.
- `packages/lazy-harness-pi/skills/*/SKILL.md` — skills exposed to Pi.
- `packages/lazy-harness-pi/prompts/lazy-harness.md` — prompt template with fast edit-loop, focused-check, one-final-standard-boundary, and no evidence-only rerun guidance.
- `packages/lazy-harness-pi/README.md` — separate Pi/OMP install/smoke/trust docs.
- `.lazy-harness/scripts/agent-activate.ts` — project-local activation writer for `.pi/APPEND_SYSTEM.md`, `.omp/APPEND_SYSTEM.md`, `.pi/settings.json` project skill entries, and `.git/info/exclude` entries; used after `lazy init` or directly via `lazy agent activate`.
- `.lazy-harness/scripts/pi-package.ts` — runtime-aware `lazy pi` and `lazy omp` install/list/remove/smoke/doctor wrapper; Pi maps to official `pi install/remove/list/-e`, OMP maps to official `omp plugin link/uninstall/list` and `omp -e`.
- `.lazy-harness/bin/lazy` — dispatches `lazy pi ...` and `lazy omp ...` to `pi-package.ts`, exposes `lazy agent activate`, captures a fresh `LAZY_INVOCATION_CWD`, and passes it as `LAZY_PI_TARGET_REPO` or `LAZY_OMP_TARGET_REPO` so nested lazy/pre-commit calls still target the caller cwd.
- `.pi/settings.json` — optional generated project-local Pi settings; `lazy agent activate` ensures project-owned `../.claude/skills`, `../.codex/skills`, and `../.agents/skills` are present, while `pi install -l` may add local package attachment. Not committed by default.
- `~/.pi/agent/settings.json` — optional user-global package attachment created by `pi install` so all existing Pi projects load the extension.
- `packages/lazy-harness-pi/scripts/record-reader-admission.ts` — one CLI facade: archived v1 schema/validation plus compact v2 digest generation, dynamic candidate/claim schemas, normalized reference validation, exact coverage/claim closure, 6k soft-target warnings, 12k hard-cap rejection, and deterministic receipts.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — legacy v1 compatibility plus compact candidate/claim digest/schema/reference/coverage/remap, soft/hard budget, integration-scale-under-target, profile mutation, and fake-runtime enforcement fixtures; semantic correctness remains Parent-audited.
- `.lazy-harness/scripts/self-test.py#check_code_organization_profile` — explicit recommend-only registry resolution and pointer-context separation.
  - Fake runtime smoke covers official Pi string `systemPrompt` and OMP string-array `systemPrompt` before-agent-start paths.
  - Fake runtime Reader smoke proves only v2 is exposed, no Parent grammar is appended, an unowned same-name `structured_output` is denied, Pi Subagents schema/capture runtime ownership plus concrete-node map/canonical read/hash and one-layer grep pass, `contact_supervisor`, Reader overview, root-wide/source/oversized searches, and mutation block, OMP arrays remain intact, steer preserves the two-mode boundary, and Reader activity cannot alter Parent evidence.
  - Fake runtime root isolation covers live `sessionManager.getCwd()` re-scope after `/move`, root-scoped recent tool evidence, and `/lazy-*` command cwd selection.
  - Fake runtime steer smoke covers prior-evidence invalidation, late pre-steer result exclusion, immediate action denial, and recovery after a fresh post-steer map/read result.
  - Fake runtime `agent_end` smoke covers current-turn-only tool projection (including failed current calls and late/previous-turn exclusion), canonical lifecycle payload fields, trace default-off behavior, runtime-root placement, no-raw-content fingerprints, and unchanged `followUp` advisory delivery.
- Machine index:
  - `kg_pi_agent_end_structural_trace_impl_20260714`
  - `kg_pi_agent_end_structural_trace_test_20260714`
  - `kg_pi_context_once_per_turn_20260818`
  - `kg_record_reader_evidence_profile_impl_20260823`
  - `kg_record_reader_two_mode_decision_20260823`
  - `kg_record_reader_two_mode_contract_impl_20260823`
  - `kg_record_reader_two_mode_contract_test_20260823`
  - `kg_record_reader_separate_probe_impl_20260823`
  - `kg_record_reader_separate_probe_test_20260823`
  - `kg_record_reader_compact_output_budget_decision_20260824`
  - `kg_record_reader_compact_contract_implementation_20260824`
  - `kg_record_reader_compact_contract_test_20260824`
  - `kg_record_reader_compact_contract_initial_review_20260824`
  - `kg_record_reader_compact_contract_review_remediation_20260824`
  - `kg_record_reader_compact_contract_review_closure_20260824`
- `.lazy-harness/decisions/0043-pi-native-package-in-source-repo.md` — repo placement decision.
- `.lazy-harness/decisions/0047-pi-omp-shared-package-separate-install-ux.md` — shared package with separate install UX decision.

## Rule placement

- Rule: Pi install UX should use `lazy pi` wrapper commands first; npm/standalone publishing remains deferred until official Pi and OMP runtime smoke are stable.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/pi-agent-package.md`
- Why not AGENTS.md: this is a Pi package installer contract, not general prompt grammar.
- Why not `.jcode`: this is shared lazy-harness Pi adapter behavior, not private Jcode preference.
- Confirmation: user-confirmed

## Rule placement

- Rule: Pi and OMP must use separate wrapper UX (`lazy pi ...` / `lazy omp ...`) while sharing the package core and explicit `pi`/`omp` manifest sections; OMP must not rely on `pi` fallback for normal operation.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/pi-agent-package.md`
- Why not AGENTS.md: this is package installer/runtime contract, not general prompt grammar.
- Why not `.jcode`: this is shared lazy-harness Pi/OMP package behavior, not private Jcode preference.
- Confirmation: user-confirmed

## Rule placement

- Rule: Pi/OMP adapter reminder injection must preserve OMP string-array system prompt blocks while keeping official Pi string prompt compatibility.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/pi-agent-package.md`
- Why not AGENTS.md: this is package adapter runtime compatibility, not general prompt grammar.
- Why not `.jcode`: this is shared Pi/OMP package behavior, not private Jcode wiring.
- Confirmation: inferred-from-runtime-evidence

## Rule placement

- Rule: Pi adapter must keep source package path and target repo separate, protect generated `.pi/` settings from team commits, and scope runtime evidence by lazy root before recommending global install.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/pi-agent-package.md`
- Why not AGENTS.md: this is a Pi adapter install/runtime isolation contract, not general prompt grammar.
- Why not `.jcode`: this is shared lazy-harness Pi package behavior, not private Jcode preference.
- Confirmation: user-confirmed

## Rule placement

- Rule: Pi/OMP adapter root selection must follow the live session manager cwd after runtime `/move`; stale `ctx.cwd` is only a fallback.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/pi-agent-package.md`
- Why not AGENTS.md: this is package adapter runtime compatibility, not general prompt grammar.
- Why not `.jcode`: this is shared Pi/OMP package behavior, not private Jcode wiring.
- Confirmation: confirmed-from-OMP-runtime-source

## Discovery capture — Pi agent-end trace

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: updated because this record owns the opt-in trace contract and privacy boundary.
- BDD: none because trace collection is disabled by default and does not alter agent flow.
- TDD: updated in `.lazy-harness/tests/pi-agent-package.md` and the fake-runtime fixture.
- ADR: none because the diagnostic preserves ADR 0051 payload and continuation semantics.
- SSOT: updated in `.lazy-harness/ssot/runtime-and-shared-state.md` with the runtime-only path.
- Planning: updated in `.lazy-harness/planning/analysis-discovery-capture-backlog.md`; fresh live reproduction remains pending.

## Discovery capture — current-turn response evidence

- Primary canonical record: `.lazy-harness/tests/project-rule-placement-gate-loop.md`.
- SDD: this record has an independent adapter-contract delta for normal-turn evidence epochs, current-turn filtering, and explicit failed-call structure.
- BDD: no independent product flow; the corrected user-visible follow-up behavior is captured in the primary regression record.
- TDD: `.lazy-harness/tests/pi-agent-package.md` and the fake runtime protect the bridge.
- SSOT: no Pi runtime-path/schema ownership delta; project-rule fingerprint input is updated separately in `.lazy-harness/ssot/gate-fingerprint-state.md`.
- DDD/ADR: no independent delta.

## Discovery capture — bounded mid-turn re-grounding

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: updated here because this record owns the Pi/OMP context cadence and resolver-reuse contract.
- BDD: none because no independent product-visible flow changed; this is adapter guidance behavior.
- TDD: updated in `.lazy-harness/tests/pi-agent-package.md` and `check_pi_package_layout_and_contract`.
- ADR: updated in `.lazy-harness/decisions/0048-operating-rule-storage-apply-repair.md` because dogfood narrowed the earlier R3 cadence decision.
- SSOT: none because no registry schema, level, ownership, or storage boundary changed.
- Planning: updated in `.lazy-harness/planning/workflow-churn-reduction-plan.md`; the existing work-unit record remains primary.

## Rule placement — Record Reader evidence-loader profile

- Rule: Parent and ordinary Pi/OMP roles retain full Lazy-Harness operating grammar, complete overview discovery, governing reads, candidate-map approval/reopening, and semantic authority; only the explicit package-owned v2 Reader receives the records-only `candidate-map | claim-evidence` Work Packet contract and tool/lifecycle ceiling.
- Scope: framework-global, opt-in experimental component.
- Primary record: `.lazy-harness/spec/platform/pi-agent-package.md`.
- Why not AGENTS.md: this is role-aware package delivery and an evidence-loading component contract, not a rule every Parent agent should execute.
- Why not local notes: the profile is distributed framework package behavior shared by runtime adapters.
- Confirmation: user-confirmed the isolated Reader/two-mode/admission work, then selected compact v2 implementation with a 6,000 soft target and 12,000 hard cap to avoid accuracy loss from a fixed 6,000 ceiling. Live compact runs, main integration, automatic scheduling, Source Verifier, Writer, delegated debt, defaults, and promotion remain unapproved.
