# Pi / OMP Agent Package Contract

Status: active
Layer: SDD

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - installing, smoke-testing, or debugging the Pi/OMP lazy-harness package or its extension bridge
  - wiring `before_agent_start`/`tool_call` events or `lazy pi`/`lazy omp` wrapper commands
- Must:
  - declare both `pi` and `omp` manifest sections; OMP must not depend on Pi fallback
  - keep separate `lazy pi`/`lazy omp` wrapper UX over one shared package core
  - normalize Pi shell aliases to `bash` before the guard, and resolve root from the live session cwd
  - preserve both Pi string and OMP string-array system prompts; scope runtime evidence by lazy root
  - force-load the FULL `.lazy-harness/AGENTS.md` grammar (§0–§2.5) into the system prompt at `before_agent_start`, once per session (jcode `load_harness_dir` parity), deduped by the `Lazy-Harness AI` title marker and fail-open — OMP/Pi otherwise only load a compact activation pointer, not the grammar body
  - keep the harness interactive grammar (record↔code conflict→ask, option gate, requirements-first) live across the turn: carry it in the `before_agent_start` reminder AND re-inject via the `context` event after file-touching tool results. The `context` re-grounding (`on-context.sh`, fed the turn's `recent_tool_calls`) runs `lazy map` on the touched paths and injects the ACTUAL matching `.lazy-harness/<layer>` record refs + `lazy policy list` operating policies — jcode "instructions relevant to files just read/edited — read and follow" parity: SURFACE the records, do not merely tell the agent to look — plus the relevant-record search (§2.1/§2.5) and turn-end capture (§2.4) mandates. If `on-context.sh` cannot produce that real body, the adapter must fail open silently instead of injecting a generic fallback reminder, because a generic reminder can loop without surfacing actionable relevant records. The `before_agent_start` reminder also carries a review/gap-analysis driver: enumerate policies (`lazy policy list`/`lazy capability list`) + governing records BEFORE reading code (AGENTS §1/§2.1)
  - surface the deterministic operating-rule/capability catalog (shared `helpers/operating_rule_catalog.py`; `lazy capability list` + `lazy policy list`) at BOTH the `before_agent_start` turn-start reminder (once-per-session baseline, via `on-message-received.sh`) and the `context` mid-turn re-grounding (per-turn refresh after file-ops, via `on-context.sh`) so stored project rules are visible before action (R3, ADR 0048 2026-06-28 amendment; jcode full-grammar parity). The catalog is a deterministic registry enumeration the agent matches itself — user-text-agnostic, advisory/visible, never a `lazy find --purpose` query backend (cli-tool-boundary, ADR 0041)
  - re-assert proactive record-first EVERY file-op turn (not only at session start): the `context` re-grounding (`on-context.sh`) carries a "Map-first BEFORE reading/editing more" push — run `lazy map --overview` + drill into governing records first, and on review/audit enumerate governing records + operating policies before reading code — so the once-per-session turn-start map-first protocol does not fade on long turns (ADR 0051 2026-06-28 amendment)
  - project the jcode-shape payload the `on-response-completed.sh` helpers expect: every `recent_tool_calls` entry carries a string `args_preview` AND an `edit_target` (the file actually written/edited — from `file_path`/`path`/`filePath` or `[PATH#TAG]` patch headers — which the 5d-3 gates scan instead of the args body so quoted source paths do not false-fire), and the `agent_end` payload carries `assistant_response` + `last_user_message` from `event.messages` — without these, satisfaction checks (e.g. analysis-discovery-capture #1/#2) can never pass under Pi/OMP and the gate loops until the continuation cap
  - keep OMP's native interactive `ask` selector active under tool discovery mode so harness option gates (AGENTS §2.3) render as native selectable choices, not plain A/B/C text
- Must not:
  - duplicate canonical policy in the extension, block read-only overview/parallel, or commit generated `.pi/`/`.omp/` by default
- Record completion:
  - changes to the package manifest, wrapper UX, or adapter bridge update this SDD and `check_pi_package_layout_and_contract`
- Related records:
  - `.lazy-harness/decisions/0043-pi-native-package-in-source-repo.md`
  - `.lazy-harness/decisions/0047-pi-omp-shared-package-separate-install-ux.md`

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
    "prompts": ["./prompts"]
  },
  "omp": {
    "extensions": ["./extensions"],
    "skills": ["./skills"],
    "prompts": ["./prompts"]
  }
}
```

OMP official source supports `package.json#omp` first and falls back to `package.json#pi`. The package must declare both so OMP does not depend on legacy Pi fallback behavior.

## Extension contract

`packages/lazy-harness-pi/extensions/lazy-harness/index.ts` must:

1. export a default Pi extension function,
2. resolve the active project cwd from live runtime state (`ctx.sessionManager.getCwd()` when present), then event cwd, then `ctx.cwd`, and walk upward to find `.lazy-harness/bin/lazy`,
3. handle `before_agent_start` by invoking `.lazy-harness/hooks/lifecycle/on-message-received.sh` through stdin JSON and appending the returned reminder body — which carries the harness interactive grammar (record↔code conflict, option gate, requirements-first; AGENTS §0/§2.3/§2.5) plus the search/read-debt protocol — to the system prompt,
4. handle `tool_call` by normalizing Pi tool payload into lazy lifecycle JSON and invoking `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh`,
5. return `{ block: true, reason }` only when the lazy hook emits a deny reason,
6. handle `tool_result` by retaining recent tool evidence for later guard invocations, and flagging the root for mid-turn re-grounding when a file-touching tool (`read`/`edit`/`write`/`grep`/`find`/`ls`) succeeds,
7. register convenience commands: `/lazy-map`, `/lazy-doctor`, `/lazy-test`, `/lazy-sync`, `/lazy-update`.
8. handle `agent_end` (Pi/OMP turn-end; the `response.completed` analogue, fired once per user prompt) by invoking `.lazy-harness/hooks/lifecycle/on-response-completed.sh` with lifecycle JSON, and drive a bounded continuation for any advisory inject body via `pi.sendUserMessage(body, { deliverAs: "followUp" })` so the agent addresses the gate after the current turn completes. `sendUserMessage` always triggers a turn, and `agent_end` fires while the agent is still `processing`; a bare call therefore throws `Agent is already processing. Use steer() or followUp()...`, so `deliverAs: "followUp"` is required to queue the continuation instead of starting one immediately. Loop safety is bounded on two axes: the SAME unresolved advisory drives at most `MAX_ADVISORY_CONTINUATIONS` (2) turns, and an alternating chain of different advisory bodies drives at most `MAX_ADVISORY_CHAIN_CONTINUATIONS` (1) follow-up turn; after the cap, the adapter must not send another chat/display message into the conversation and may only surface a transient UI notification/log. An empty advisory body (gate resolved) resets the per-lazy-root continuation counter.
9. handle `context` (fired before each LLM call) by injecting a compact re-grounding reminder message into `messages` — sourced from `.lazy-harness/hooks/lifecycle/on-context.sh`, computed once per turn and cached — only when a file-touching tool ran since the last injection. Bounded to one inject per new file-op batch, reset per turn, fail-open silently when the hook is missing or returns no parseable body. Do not inject a generic fallback reminder in that failure path. This replicates jcode's native "AGENTS/.jcode instructions relevant to files just read/searched/edited this turn — read and follow them for the next steps" re-injection, which Pi/OMP otherwise lack because they load AGENTS.md only once at session start. The injected message is a `UserMessage` (`role`/`content`/`timestamp`) wrapping the body in a `<system-reminder>` tag,
10. project a jcode-shape `agent_end` payload for the canonical `on-response-completed.sh` helpers: extract `assistant_response` and `last_user_message` from `event.messages`, and attach a string `args_preview` (path/command projection of `args`) to each `recent_tool_calls` entry. The 17 helpers were written for jcode's payload, which carried `args_preview` and the response prose; the Pi/OMP events expose `args` objects and `event.messages`, so the bridge MUST project them or gate satisfaction silently never triggers (the analysis-discovery-capture loop the user observed),
11. keep the OMP/Pi native `ask` selector available for option gates: on `before_agent_start`, add `ask` to the active tool set (`ensureAskToolActive` — add-only, only when the `ask` tool exists, i.e. interactive sessions) so tool discovery mode (>40 tools) does not hide it. Fail-open — runtimes without `getAllTools`/`setActiveTools` or non-interactive/subagent sessions fall back to plain-text option gates,

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

Project activation is separate from package installation. An activated project is identified by `.lazy-harness/bin/lazy`; the globally loaded extension must no-op when `ctx.cwd` cannot resolve that file. `lazy agent activate --target <repo>` creates project-local `.pi/APPEND_SYSTEM.md` and `.omp/APPEND_SYSTEM.md` pointer prompts and adds `.pi/` / `.omp/` to that repo's `.git/info/exclude`. `lazy init` keeps bootstrapping focused and prints the activation command after a successful install.

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
- OMP Phase 2 compatibility: `before_agent_start` must preserve both official Pi string `systemPrompt` values and OMP string-array `systemPrompt` blocks. When OMP sends `systemPrompt: string[]`, append the lazy reminder as a new prompt block instead of coercing the array to a comma-joined string.

## Implementation map

- `packages/lazy-harness-pi/package.json` — shared Pi/OMP package manifest with explicit `pi` and `omp` resource declarations.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — event bridge implementation.
  - `resolveInvocationCwd` keeps hook and `/lazy-*` command root selection aligned with the live Pi/OMP session cwd after runtime `/move` re-scopes the session.
  - `systemPromptIncludesBody` / `appendSystemPromptBody` preserve official Pi string prompts and OMP string-array prompt blocks during `before_agent_start` reminder injection.
  - the `context` handler + `pendingRegroundByRoot`/`regroundBodyByRoot`/`FILE_OP_TOOLS` state re-inject the harness grammar mid-turn after file-touching tool results, sourced from `on-context.sh` and reset each `before_agent_start`.
  - `ensureAskToolActive` (called on `before_agent_start`) adds OMP's native `ask` selector to the active tool set so tool discovery mode does not hide it; add-only, interactive-only, fail-open.
- `.lazy-harness/hooks/lifecycle/on-message-received.sh` — per-turn reminder body; carries the interactive grammar (AGENTS §0/§2.3/§2.5) plus the search/read-debt protocol.
- `.lazy-harness/hooks/lifecycle/on-context.sh` — compact mid-turn re-grounding body for the `context` event (jcode "relevant to files just read/edited" parity); leads with the relevant-record search (§2.1/§2.5) and turn-end capture (§2.4) mandates plus the interactive grammar.
- `packages/lazy-harness-pi/skills/*/SKILL.md` — skills exposed to Pi.
- `packages/lazy-harness-pi/prompts/lazy-harness.md` — prompt template.
- `packages/lazy-harness-pi/README.md` — separate Pi/OMP install/smoke/trust docs.
- `.lazy-harness/scripts/agent-activate.ts` — project-local activation writer for `.pi/APPEND_SYSTEM.md`, `.omp/APPEND_SYSTEM.md`, and `.git/info/exclude` entries; used after `lazy init` or directly via `lazy agent activate`.
- `.lazy-harness/scripts/pi-package.ts` — runtime-aware `lazy pi` and `lazy omp` install/list/remove/smoke/doctor wrapper; Pi maps to official `pi install/remove/list/-e`, OMP maps to official `omp plugin install/uninstall/list` and `omp -e`.
- `.lazy-harness/bin/lazy` — dispatches `lazy pi ...` and `lazy omp ...` to `pi-package.ts`, exposes `lazy agent activate`, captures a fresh `LAZY_INVOCATION_CWD`, and passes it as `LAZY_PI_TARGET_REPO` or `LAZY_OMP_TARGET_REPO` so nested lazy/pre-commit calls still target the caller cwd.
- `.pi/settings.json` — optional source-repo Pi local package attachment created by `pi install -l`; not committed by default.
- `~/.pi/agent/settings.json` — optional user-global package attachment created by `pi install` so all existing Pi projects load the extension.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — static contract validation.
  - Fake runtime smoke covers official Pi string `systemPrompt` and OMP string-array `systemPrompt` before-agent-start paths.
  - Fake runtime root isolation covers live `sessionManager.getCwd()` re-scope after `/move`, root-scoped recent tool evidence, and `/lazy-*` command cwd selection.
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
