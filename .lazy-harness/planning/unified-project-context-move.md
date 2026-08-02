# Planning — Context-Preserving Project Folder Move

Status: completed
Date: 2026-08-02
Layer: Planning
Primary ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
Related SDD: `.lazy-harness/spec/platform/pi-agent-package.md`
Related SDD: `.lazy-harness/spec/platform/jcode-agent-adapter.md`
Related SDD: `.lazy-harness/spec/platform/host-root-resolution.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: transient-plan
- Confidence: high
- Aliases:
  - lazy move
  - 다른 폴더로 이동
  - 컨텍스트 유지 이동
  - project context move
- Surface terms:
  - lazy move
  - /move
  - session cwd
  - current project root
  - AGENTS reload
- Applies when:
  - implementing the user-corrected project-folder move semantics
  - changing the active project root while preserving the current conversation/session context
- Must:
  - accept an existing target project directory and change the active session cwd without creating a new conversation session
  - preserve the current conversational context across the move
  - resolve all subsequent lazy-harness hooks, tool execution, records, runtime evidence, and commands from the new live session cwd
  - replace the old root grammar with the target directory's current project instructions on the next model boundary; in an exact trusted lazy-harness root, the target `.lazy-harness/AGENTS.md` becomes authoritative
  - reset or isolate old-root read-debt/tool evidence so it cannot authorize actions in the new root
  - restore the complete prior in-memory cwd/context state if persistence fails, so server, client, UI, and saved session cannot diverge
  - make every remote reconnect/subscription advertise the current live session cwd rather than the original launcher cwd
- Must not:
  - create a Git worktree, branch, or directory
  - run project activation as part of folder movement
  - create a fresh session and claim conversational context was preserved
  - continue injecting or enforcing the previous root's `.lazy-harness/AGENTS.md`
  - infer or invent a target path
- Record completion:
  - the corrected restore plan was explicitly approved by the user on 2026-08-02
  - Jcode core commits `71adb1853`, `2f44249d1`, and `d58409274` plus focused core/adapter regressions are complete
  - completed after independent review, record lint, refreshed lazy-patched installation verification, and the closing standard validation gate
- Related records:
  - `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
  - `.lazy-harness/spec/platform/pi-agent-package.md`
  - `.lazy-harness/spec/platform/jcode-agent-adapter.md`
  - `.lazy-harness/spec/platform/host-root-resolution.md`
  - `.lazy-harness/tests/pi-agent-package.md`
  - `.lazy-harness/tests/jcode-agent-adapter.md`

## User correction

User correction confirmed on 2026-08-02:

1. Worktree creation belongs to each development project and is explicitly out of scope.
2. The requested command only moves the active agent session to an already existing folder.
3. The current conversation/context must remain available after moving.
4. The session must stop carrying the previous folder's AGENTS/lazy-harness grammar.
5. Subsequent model requests and tools must load and obey the target folder's current AGENTS/project instructions; for an exact trusted lazy-harness root, this means the target `.lazy-harness/AGENTS.md` and target-root records instead.

This correction invalidates the earlier worktree-first proposal and its execution approval.

## Existing baseline

- Pi/OMP already have a native runtime `/move` concept. The lazy-harness adapter resolves the active root from `ctx.sessionManager.getCwd()` before stale event/`ctx.cwd`, so hooks and `/lazy-*` commands re-scope after a live cwd change.
- The custom `/lazy-move` and `lazy_move_project` are semantically different: they currently create and switch to a new `SessionManager` session, so they do not satisfy the corrected same-session context requirement.
- Jcode's adapter already resolves every hook root from live `JCODE_HOOK_CWD`/payload cwd and injects that trusted root's canonical `.lazy-harness/AGENTS.md` on every `before_model` request. If Jcode changes the live session cwd correctly, adapter grammar selection naturally follows the new root.
- The current lazy-harness Jcode adapter does not itself expose an official active-session cwd mutation surface.

## Historical custom Jcode comparison

Read-only history review in `/home/lazydino/dev/jcode` found that the prior custom feature was the native **session cwd command**, not a worktree or project-session switch:

- `e50b14e8a` — `feat: add session cwd command`
  - added `src/cwd.rs`
  - exposed `/pwd`, `/cwd`, `/cwd <path>`, and `/cd <path>`
  - changed `app.session.working_dir` in the existing session, persisted that same session, refreshed initial context where permitted, reloaded project commands, and invalidated the session picker
  - regression explicitly asserted that conversation context was preserved
- `88f5b2a94` — documented the session cwd commands.
- `f0b35112d` — added remote-session cwd support with protocol `Request::SetCwd` and `ServerEvent::SessionCwd`.
- `ba12fdfda` — exposed an LLM `cwd` tool and its cwd-change side effects.
- `cba0f3f51` — propagated cwd tool changes to clients.

Comparison result:

1. Same session/history: matched. The old implementation mutated `session.working_dir`; it did not create a new session ID.
2. Existing directory only: matched. Its canonical path resolver rejected missing or non-directory targets.
3. New project context: substantially matched. Project commands and skills were refreshed, and current provider prompt construction resolves AGENTS/overlays/preferred tools from `session.working_dir` per request.
4. Remaining caveat: the old `refresh_initial_session_context_message()` path refreshes only before visible conversation has begun in current code. Therefore the restored design must explicitly protect the post-conversation two-root case and rely on per-request dynamic system prompt rebuilding, not only initial-context replacement.
5. Current code state: `crates/jcode-app-core/src/agent/provider.rs#Agent::set_working_dir` remains, but the old cwd parser, `SetCwd`/`SessionCwd` protocol, and `CwdTool` surfaces are absent.

Recommended reuse path: re-port the old native cwd parser/resolver, same-session mutation/save flow, remote protocol, LLM tool, project-command/skill refresh, and regression coverage onto the current Jcode crate layout. Do not invent a separate lazy-harness worktree or new-session move mechanism.

## Revised plan proposal

Execution approved by the user on 2026-08-02 after the historical Jcode cwd comparison.

### Review finding and user-selected repair

- Bounded independent review found one P2: commit `71adb1853` mutated live cwd/context before `session.save()`, so a persistence failure could leave server memory on the target root while the saved session, client, or UI remained on the prior root.
- The user selected option A on 2026-08-02: snapshot the complete pre-change live state, attempt the cwd transition and persistence, and restore the prior state on save failure.
- The failure path must emit no successful `SessionCwd` event or cwd-tool success metadata and must leave local slash-command state, remote server/client state, and persisted state consistent.
- Focused failure-injection tests are required before candidate installation.
- A later independent review found one P1 remote lifecycle gap: the reconnect loop retained its initial launch cwd and could overwrite a successful same-session `/cwd` transition on reconnect.
- The user selected option A on 2026-08-02: include the reconnect repair in this work unit so A → `/cwd` B → reconnect remains on B, with focused regression coverage before candidate installation.

### Phase 1 — Restore the proven Jcode cwd contract

1. Re-port the historical `/pwd`, `/cwd [path]`, and `/cd <path>` same-session behavior onto the current Jcode crate layout.
2. Reuse the surviving `Agent::set_working_dir` seam and restore session persistence, remote `SetCwd`/`SessionCwd`, client propagation, and LLM `cwd` tool behavior.
3. Keep one semantic contract across runtimes: target existing directory, preserve session/conversation, change live cwd, then re-ground against the new root.
4. Do not emulate movement by opening a new process/session or queuing slash text as a user message.

### Phase 2 — Move surface

1. Prefer the proven native Jcode command surface: `/cwd <existing-target-directory>` with `/cd` alias and `/pwd` inspection. A separate `lazy move` CLI is unnecessary unless another runtime needs a wrapper.
2. Validate that the target exists and is a directory; require explicit target input. The native Jcode cwd command remains generic, while lazy-harness hooks activate only when the resulting root is exact-trusted.
3. Change the active runtime session cwd in place.
4. Clear old-root pending/recent tool evidence and read-debt state for that session.
5. Trigger a next-model re-ground boundary so the target directory's current project instructions replace the old root; exact-trusted lazy roots receive their complete `.lazy-harness/AGENTS.md`.

### Phase 3 — Runtime adapters

1. Pi/OMP: no source change in this work unit. Their native same-session `/move` path and `sessionManager.getCwd()` root selection already provide the reference semantics; the separate custom new-session `/lazy-move` surface is a future independently approved cleanup if still desired.
2. Jcode: restore the official same-session cwd transition in Jcode core. The lazy-harness adapter consumes the updated payload cwd, prefers it over stale hook env, clears old-root evidence at the next `before_model`, and loads the new trusted root grammar.
   Remote reconnect/subscription must source its advertised cwd from the current live session state after `SessionCwd`, never from an immutable launch-time copy.
3. Do not add a generic `lazy move` wrapper in this work unit.

### Phase 4 — Regression and records

1. Add a two-root fixture with distinct AGENTS markers and distinct runtime evidence.
2. Assert conversation/session identity is unchanged while cwd changes.
3. Assert the old marker disappears, the new root marker appears, and old-root evidence cannot satisfy new-root action gates.
4. Update ADR 0056, Pi/Jcode SDDs, host-root SDD, and Pi/Jcode TDD records with an explicit layer-completeness matrix.
5. Run focused tests, independent review, and one final `.lazy-harness/bin/lazy validate --plan standard` after the last mutation.

## Stop conditions

- Stop if the implementation would create a new session/process while claiming context preservation.
- Stop if old-root AGENTS or runtime evidence remains active after the cwd transition.
- Stop if the target is not an existing explicit directory.
- Stop before creating/removing any worktree, branch, directory, trust entry, or project activation state.

## Implementation map

- Implemented source:
  - `/home/lazydino/dev/jcode` commit `71adb1853` — shared cwd parser/resolver, local `/pwd`/`/cwd`/`/cd`, remote protocol/client fanout, persisted `Agent::set_working_dir`, LLM cwd tool, skill/header refresh, and post-conversation target-root AGENTS regression.
  - `/home/lazydino/dev/jcode` commit `2f44249d1` — transactional live-session snapshot/restore, cwd-tool failure propagation, remote error-only response gating, and local/server save-failure regressions.
  - `/home/lazydino/dev/jcode` commit `d58409274` — established same-session reconnect subscriptions advertise the live session cwd; initial or different-session subscriptions retain launch-cwd behavior.
  - `.lazy-harness/scripts/jcode-adapter.ts#activeRoot` — request payload cwd is authoritative when present; stale inherited hook cwd is ignored during the transition.
  - `.lazy-harness/scripts/jcode-adapter.ts#beforeModel` — root mismatch is atomically persisted as an empty target-root state envelope before target grammar/context selection.
  - `.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter` — same session/runtime, stale env cwd, root-A evidence, and root-B grammar/evidence regression.
- Historical/source seams:
  - Historical Jcode `src/cwd.rs` at commit `e50b14e8a` — prior native same-session cwd parser/resolver and mutation flow to re-port into the current crate layout.
  - Historical remote/tool commits `f0b35112d`, `ba12fdfda`, and `cba0f3f51` — protocol, LLM tool, and client propagation reference behavior.
  - Current `crates/jcode-app-core/src/agent/provider.rs#Agent::set_working_dir` — surviving current seam for cwd mutation.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts#resolveInvocationCwd` — prefers live `sessionManager.getCwd()` and re-scopes hooks to the changed cwd.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts#switchToProjectSession` — current new-session implementation that does not satisfy the corrected requirement.
  - `.lazy-harness/scripts/jcode-adapter.ts#activeRoot` — selects the current trusted root from live Jcode cwd evidence.
  - `.lazy-harness/scripts/jcode-adapter.ts#canonicalGrammar` / `beforeModelDecision` — loads the selected root's canonical AGENTS grammar per provider request.
  - `.lazy-harness/spec/platform/host-root-resolution.md` — caller/live worktree root boundary.
- Implemented flow: explicit existing target → runtime-native same-session cwd change → preserve session id/messages → next request resolves target directory → adapter persists empty target-root evidence → target project instructions replace old grammar; exact-trusted lazy roots use the target `.lazy-harness/AGENTS.md`.
- Validation: Jcode formatting/check, focused cwd/protocol/prompt tests, transactional rollback tests, and `tui::app::remote::tests::remote_cwd_change_is_advertised_on_same_session_reconnect` passed; lazy-harness focused adapter contract passed on 2026-08-02. Independent review found no remaining P1/P2 release blocker in the repaired cwd paths.
- Installed rollout: Jcode lock reconciliation commit `daf9d3d90` adds only the missing root `jcode-provider-core` dev-dependency lock entry. Candidate `~/.jcode/builds/lazy-patched/versions/daf9d3d90-b6ee0d1e472a-release-bb2f6034b9335651/jcode` reports embedded hash `daf9d3d90`; strict provenance, source/binary digests, offline help, launcher status, trusted-root doctor, and stable/current preservation pass.
- Review repair: both user-selected option A repairs are committed, independently reviewed, installed, and verified. The final standard validation is the closing gate after this record mutation.

## Rule placement

- Rule: project movement changes the active session root while preserving conversation context; runtime grammar and evidence must follow the new root immediately.
- Scope: framework-global runtime-adapter contract.
- Primary durable decision after revised approval: ADR 0056 amendment.
- Primary planning record before approval: this file.
- Confirmation: user-corrected and implementation-approved on 2026-08-02.

## Discovery capture

- ADR: independent semantic correction, same-session cwd transition rather than new-session/worktree preparation.
- SDD: independent runtime and CLI contract delta across Pi/OMP, Jcode, and host-root resolution.
- BDD: visible behavior is context preserved while active project instructions change; covered through runtime SDD/TDD unless a separate UI is added.
- TDD: two-root same-session grammar/evidence isolation regression required.
- SSOT: live runtime cwd becomes the active project root; no project ownership or trust-registry ownership change.
- DDD: no business-domain delta.
- Planning: this corrected record supersedes the discarded worktree-first proposal.
