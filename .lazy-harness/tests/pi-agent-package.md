# Pi / OMP Agent Package Regression

Status: active
Layer: TDD

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - 패키지 회귀
- Applies when:
  - working on the in-repo Pi/OMP agent package install or wrapper UX
  - bridging agent extension events to lazy-harness lifecycle hooks or changing reminder/mutation-guard behavior
  - adding or changing a shared Pi/OMP package skill
- Must:
  - keep separate `lazy pi` and `lazy omp` wrapper command arrays plus explicit `package.json#omp` resources
  - bridge `before_agent_start`/`tool_call`/`tool_result`/`agent_end` to canonical hooks (incl. `agent_end` → `on-response-completed.sh` post-turn audit driven as a bounded continuation: `pi.sendUserMessage(body, { deliverAs: "followUp" })`, loop-capped by `MAX_ADVISORY_CONTINUATIONS` plus `MAX_ADVISORY_CHAIN_CONTINUATIONS`, falling back to non-steering display without a custom transport label); preserve OMP string-array `systemPrompt` blocks
  - re-scope hook root, recent-tool evidence, and `/lazy-*` execution to live session cwd after `/move`
  - ensure `lazy_move_project` switches directly through `ctx.switchSession` when available; it must not treat `sendUserMessage('/lazy-move ...', { deliverAs: 'followUp' })` as command execution, because that only queues an agent-visible user message
  - cache one overview plus directly read governing-record hashes for the active Pi/OMP work unit; valid later normal turns emit `reused-work-unit` and do not replay the system reminder
  - trigger pointer-only `context` injection only after the first successful mutation, never after reads/searches; the body stays within five lines and contains no map output, mapped record list, policy/capability catalog, or resolver result
  - keep exact source-work policy/capability resolution explicit and once per coherent mutation batch rather than automatically replaying it from file-touch context
  - on every non-extension, non-empty mid-turn steer, clear work-unit fingerprints, advance a root evidence epoch, and exclude tool results whose calls started in an older epoch
  - project the canonical lifecycle `agent_end` payload with user/assistant prose plus current-turn-only tool entries carrying `args_preview`, `edit_target`, `evidence_epoch`, and `is_error`; prior-turn/late results must not reach response-completion helpers, while failed current calls remain explicit structural facts
  - protect the opt-in `LAZY_PI_AGENT_END_TRACE=1` diagnostic: absent by default, written under `$LAZY_RUNTIME_ROOT`, structural fingerprints only, no conversation prose/tool args/results, fail-open, and no change to queued continuation behavior
  - keep OMP's native `ask` selector active (`ensureAskToolActive` on `before_agent_start`) so option gates render as selectable choices under tool discovery mode; add-only, interactive-only, fail-open
  - surface a visible per-start `lazy-harness read-debt` marker with runtime marker/root/status/phase/tool-guard (`status=armed`, `status=not-armed(synthetic-turn)`, `status=not-armed(hook-empty)`, `status=not-armed(hook-timeout)`, `status=not-armed(hook-error)`) plus concise hook detail for failures; synthetic/steering starts are debug-only and must not create read-debt journal rows, large hook payloads must be handed to Python helpers by temp-file/ref rather than argv/env to avoid ARG_MAX hook-empty/error loops, and lazy-root action tools still block with `read-debt not armed` plus status/detail when the turn did not arm
  - project-local activation must merge `.pi/settings.json` with project-owned skill paths (`../.claude/skills`, `../.codex/skills`, `../.agents/skills`) and `enableSkillCommands: true` without relying on global wildcard behavior
  - expose `lazy-architecture-refactor` through the shared `skills/` resource with separate map/source approval gates, exact digest confirmation, stop rules, and no enforcement
  - keep fake-runtime regression fixtures hermetic: copy the extension beside bounded Pi/TypeBox peer stubs instead of assuming repository-local or machine-global peer resolution
- Must not:
  - invent a second policy engine or let OMP silently fall back to Pi-only packaging
- Record completion:
  - changes to package wrappers, extension bridge, or activation prompts update this TDD plus its SDD/ADR
- Related records:
  - `.lazy-harness/spec/platform/pi-agent-package.md`
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md`
  - `.lazy-harness/decisions/0043-pi-native-package-in-source-repo.md`
  - `.lazy-harness/decisions/0047-pi-omp-shared-package-separate-install-ux.md`
  - `.lazy-harness/spec/platform/code-organization-profile.md`

## Regression target

The in-repo Pi/OMP package must remain installable through separate Pi and OMP wrapper UX and must bridge agent extension events to canonical lazy-harness lifecycle hooks without inventing a second policy engine.

## Protected fixtures

| Case | Trigger | Expected |
|---|---|---|
| `pi_omp_package_manifest_resources` | Parse `packages/lazy-harness-pi/package.json` | Manifest name is `@lazy-dinosaur/lazy-harness-pi`; keywords include `pi-package` and `omp-plugin`; both `pi.*` and `omp.*` resource sections point to package-local extensions, skills, and prompts |
| `pi_clean_default_no_project_settings` | Inspect source checkout | `.pi/settings.json` is absent by default after factory reset; project-local Pi attachment is generated only by an intentional install command |
| `pi_fake_runtime_hermetic_peers` | Run extension fake-runtime smokes from a clean checkout where Pi exists only as a runtime/global package | The fixture copies current extension source beside bounded `SessionManager` and TypeBox stubs; Bun never depends on machine-global peer lookup or a repository-local Pi install |
| `pi_install_guidance` | Inspect package README and SDD | Global bootstrap and project-local activation commands are documented, including that the package is not installed by default after a clean reset |
| `cross_platform_dependency_guidance` | Inspect installer, README, package README, and SDD | macOS/Linux prerequisites are documented; installer requires `git`, `bun`, and `python3` before mutation and prints OS-specific install hints |
| `pi_validation_commands` | Inspect extension and package prompt | `/lazy-check`, `/lazy-validate`, and `/lazy-test` are registered; prompt guidance uses fast edit loops, one final standard plan, and explicit fresh full regression only. |
| `lazy_pi_wrapper_guidance` | Inspect package README, SDD, `.lazy-harness/bin/lazy`, and `.lazy-harness/scripts/pi-package.ts` | `lazy pi install/list/remove/smoke/doctor` is documented and dispatched; install defaults to global bootstrap; remove requires explicit scope; dry-run is supported |
| `lazy_pi_wrapper_dry_run` | Run `pi-package.ts` dry-run fixtures | Default/global install, explicit local install, local remove, and one-run smoke dry-run produce the exact Pi command arrays without mutating settings |
| `lazy_pi_wrapper_doctor_no_smoke` | Run `pi-package.ts doctor --no-smoke --format=json` | Doctor is safe in environments without persistent Pi package settings and reports that smoke is skipped/non-mutating |
| `lazy_omp_wrapper_guidance` | Inspect package README, SDD, `.lazy-harness/bin/lazy`, and `.lazy-harness/scripts/pi-package.ts` | `lazy omp install/list/remove/smoke/doctor` is documented and dispatched separately from `lazy pi` |
| `lazy_omp_wrapper_dry_run` | Run `pi-package.ts` with `LAZY_AGENT_RUNTIME=omp` and lazy CLI OMP dispatch fixtures | OMP install/remove/smoke dry-runs produce exact `omp plugin link`, `omp plugin uninstall`, and `omp -e` command arrays without mutating plugin settings |
| `lazy_omp_wrapper_doctor_no_smoke` | Run OMP doctor no-smoke in non-strict mode | Doctor is safe in environments without persistent OMP plugin settings and reports that smoke is skipped/non-mutating |
| `lazy_pi_source_target_isolation` | Run `lazy pi install --local --dry-run` and direct `pi-package.ts` from another cwd with stale parent `LAZY_INVOCATION_CWD`, plus explicit `--target-repo` | Source package path stays in the lazy-harness source checkout while target repo resolves to caller/explicit repo; direct wrapper ignores stale parent invocation cwd unless `LAZY_PI_TARGET_REPO` or `--target-repo` is set |
| `lazy_pi_global_bootstrap_no_harness_noop` | Fake runtime calls `before_agent_start` from a temp directory without `.lazy-harness/bin/lazy` | The globally loaded extension returns `undefined` and injects no lazy-harness reminder |
| `lazy_agent_activation_prompts` | Run `lazy agent activate` twice against a temp initialized Git repo with hostile isolated `JCODE_HOME` | `.pi/APPEND_SYSTEM.md` and `.omp/APPEND_SYSTEM.md` contain managed pointer prompts, `.pi/settings.json` contains project-relative Claude/Codex/Agents skill paths plus `enableSkillCommands: true`, output is idempotent, and no Jcode field/state is read or created |
| `lazy_init_sync_pi_omp_activation` | Initialize and sync a temporary Git host without Jcode state | Init and sync activate or repair Pi/OMP independently; marker publication remains transactional |
| `lazy_pi_local_settings_git_exclude` | Inspect `.pi/settings.json` and target repo exclude behavior | Generated `.pi/settings.json` is allowed only when untracked and `.pi/` is present in `.git/info/exclude`; local install dry-run reports the exclude path |
| `pi_extension_before_agent_start_bridge` | Inspect extension source and fake runtime | First work-unit grounding calls `on-message-received.sh` and injects `REMINDER. Ground this work unit once...`; later valid normal turns emit `status=reused-work-unit` without another system prompt. Failure/synthetic markers remain explicit and guarded. |
| `omp_before_agent_start_system_prompt_array` | Fake OMP runtime calls `before_agent_start` with `systemPrompt: string[]` | The original prompt block remains an array element and the lazy reminder is appended as a new block, not comma-joined into one string |
| `pi_extension_tool_call_bridge` | Inspect extension source | Source contains `tool_call`, calls `on-tool-execute-before.sh`, and returns `{ block: true, reason }` only when hook output supplies a reason |
| `pi_extension_shell_alias_guard` | Fake Pi runtime calls `tool_call` with `cmd`, `terminal`, `bash`, and `batch` shell actions after `before_agent_start` | All action shell variants block until root-bound read/search evidence exists; if `before_agent_start` did not arm the turn, lazy-root action tools block with `read-debt not armed` and the not-armed status instead of silently allowing action |
| `pi_extension_tool_result_evidence` | Inspect extension source | Source contains `tool_result` and records recent tool calls for evidence guard payloads |
| `pi_extension_root_scoped_recent_tools` | Fake Pi runtime touches repo A and repo B in one process | Repo B does not see repo A's `recent_tool_calls`; repo A retains its own recent tool evidence |
| `pi_extension_lazy_move_project_switches_directly` | Fake Pi runtime registers `lazy_move_project`, exposes `ctx.switchSession`, and executes the tool with `autoSwitch:true` | The tool calls `switchSession` exactly once, does not send `/lazy-move` as a follow-up user message, delivers the optional prompt in the switched session, and returns an explicit manual `/lazy-move` instruction when `ctx.switchSession` is unavailable |
| `pi_extension_move_rescopes_root_state` | Fake OMP/Pi runtime keeps stale `ctx.cwd` but changes `ctx.sessionManager.getCwd()` after `/move` | Hook payloads, `LAZY_HOST_ROOT`, recent tool evidence, and `/lazy-*` command execution re-scope to the live session cwd |
| `pi_extension_steer_rearms_fresh_evidence` | Fake Pi runtime establishes valid evidence, starts a second read, receives a non-extension `streamingBehavior:'steer'`, then delivers the old read result and attempts a write | The transformed steer reminder says earlier evidence is stale; the old result is ignored; the write blocks; a read call/result started after the steer restores permission; no command-name or steer-text classifier is involved |
| `pi_extension_agent_end_bounded_continuation` | Inspect extension source | `agent_end` drives any advisory inject body as a continuation via `sendUserMessage(body, { deliverAs: "followUp" })` (a bare `sendUserMessage` at turn-end throws `Agent is already processing`, so `followUp` queues it after the current turn); the same unresolved advisory is capped at `MAX_ADVISORY_CONTINUATIONS` turns and alternating advisory chains are capped at `MAX_ADVISORY_CHAIN_CONTINUATIONS`, then suppresses chat/display messages and only emits transient UI notification/log; an empty body resets the per-root counter, and a new human prompt distinct from the queued advisory body resets the cap while synthetic follow-up turns keep it |
| `pi_extension_reminder_carries_interactive_grammar` | Fake runtime calls `before_agent_start` in a harness root | Reminder body includes the interactive grammar (record↔code conflict / option gate / requirements-first), not only the search/read-debt protocol |
| `pi_extension_context_regrounds_once_per_work_unit` | Fake runtime grounds with overview + direct record read, performs reads then mutations, starts another normal turn, changes a governing record, and explicitly steers | Reads/searches produce no context injection; the first successful mutation produces one pointer-only reminder; a later normal turn reuses valid hashes with `status=reused-work-unit`; changed/deleted governing records and explicit steer re-arm fresh grounding. |
| `pi_context_code_organization_profile` | Resolve framework and host-only source policies/capabilities explicitly before a coherent source batch | Canonical registry matches remain available without being injected automatically after file reads; record-only context receives no source-adaptation block. |
| `pi_extension_context_noop_without_mutation` | Fake runtime fires `context` after reads/searches but without a successful mutation result | `context` returns `undefined`; read-only evidence never causes prompt replay. |
| `pi_extension_agent_end_canonical_payload` | Fake runtime fires `tool_result` (write to `.lazy-harness/knowledge/candidates.jsonl`) then `agent_end` with `event.messages` (user + assistant), capturing the payload via a fake `on-response-completed.sh` | Captured payload carries `assistant_response`, `last_user_message`, and current-turn tool fields including `args_preview`, `edit_target`, `evidence_epoch`, and `is_error` |
| `pi_extension_agent_end_current_turn_tool_scope` | Fake runtime completes one read, leaves another result late, starts a new normal turn, then records a failed fetch and ends a third tool-free turn | Turn two payload contains only the current failed fetch with `is_error: true`; completed/late turn-one reads are absent; turn three has no inherited tool calls |
| `pi_extension_agent_end_structural_trace` | Run the fake runtime with trace disabled, with explicit-root trace enabled, without an explicit root so canonical `runtime_paths.py` resolves the path, with a forced trace-write failure, and through 55 additional trace turns | No trace exists by default; opt-in rows contain bounded role/content-kind metadata, byte counts/hashes, tool names, and hook/advisory fingerprints without raw conversation/tool content; a 16-part message records only 12 kinds plus total/truncation metadata; the canonical fallback writes under the session runtime root; forced write failure still delivers one `followUp`; retention keeps exactly the newest 50 rows |
| `pi_extension_agent_end_fresh_source_trace` | Start `pi -e packages/lazy-harness-pi -p` with trace enabled, let it exit normally after map/read grounding and one complete seven-layer judgement, then inspect the runtime-only structural row | Assistant and last-user projections are present, hook status is `0`, hook stdout/stderr and advisory are empty, and no continuation occurs; this proves current-source non-reproduction for the controlled case, not the historical session cause. Evidence: `.lazy-harness/evidence/2026-07-14-pi-agent-end-structural-trace.md` |
| `pi_extension_ensure_ask_tool_active` | Fake runtime with `ask` present in `getAllTools` but not in `getActiveTools` calls `before_agent_start` | Extension calls `setActiveTools` with the existing active set plus `ask` (add-only); a runtime missing the `ask` tool or the tool APIs is a graceful no-op (no throw) |
| `pi_package_skills` | Inspect package skills | core wrappers plus `lazy-architecture-refactor` expose valid `SKILL.md` resources to both Pi and OMP |
| `architecture_refactor_skill_contract` | Inspect `lazy-architecture-refactor/SKILL.md` | required records, exact map digest, confirmation ref, separate source gate, single-batch boundary, stop rules, no enforcement, and no canary source edit are explicit |

## Automated coverage

Implemented by:

```text
.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract
```

This check is `FRAMEWORK_ONLY` because `packages/lazy-harness-pi` is source-repo package code, not currently a Category A downstream mirror artifact.

## Manual/current-host smoke

After implementation, run:

```bash
bun packages/lazy-harness-pi/extensions/lazy-harness/index.ts
.lazy-harness/bin/lazy pi install --dry-run
.lazy-harness/bin/lazy pi install --local --dry-run
.lazy-harness/bin/lazy pi install --global --dry-run
.lazy-harness/bin/lazy pi remove --local --dry-run
.lazy-harness/bin/lazy agent activate --target /path/to/project --dry-run
.lazy-harness/bin/lazy pi smoke --dry-run
.lazy-harness/bin/lazy pi doctor --no-smoke
.lazy-harness/bin/lazy omp install --dry-run
.lazy-harness/bin/lazy omp remove --dry-run
.lazy-harness/bin/lazy omp smoke --dry-run
.lazy-harness/bin/lazy omp doctor --no-smoke
.lazy-harness/bin/lazy pi smoke
/path/to/lazy-harness/.lazy-harness/bin/lazy pi install --local --dry-run
.lazy-harness/bin/lazy pi install --local --dry-run --target-repo /path/to/other/repo
LAZY_HARNESS_PI_PACKAGE=/path/to/lazy-harness/packages/lazy-harness-pi
pi -e "$LAZY_HARNESS_PI_PACKAGE" --help
pi install "$LAZY_HARNESS_PI_PACKAGE" --no-approve
pi install -l "$LAZY_HARNESS_PI_PACKAGE" --approve
omp -e "$LAZY_HARNESS_PI_PACKAGE" --help
omp plugin link "$LAZY_HARNESS_PI_PACKAGE"
omp plugin list
```

## Layer completeness

- Primary canonical record: `.lazy-harness/tests/project-rule-placement-gate-loop.md`; this package TDD is an independent adapter regression delta.
- SDD: `.lazy-harness/spec/platform/pi-agent-package.md` defines normal-turn evidence epochs and active-turn-only `agent_end` projection.
- BDD: no separate canonical record; the user-visible false placement follow-up is the primary TDD regression correction.
- SSOT: no package runtime-path/schema delta; `.lazy-harness/ssot/gate-fingerprint-state.md` owns the related project-rule fingerprint narrowing.
- DDD: no domain terminology or business invariant delta.
- TDD: this record protects the package bridge; the primary TDD record protects the end-to-end placement regression.
- ADR: no new decision; existing Pi/OMP bridge and lifecycle decisions remain unchanged.

## Implementation map

- `packages/lazy-harness-pi/package.json` — fixture for explicit `pi` and `omp` package manifest resource paths.
- `.lazy-harness/scripts/pi-package.ts` — fixture for runtime-aware `lazy pi` and `lazy omp` wrapper command construction and safe dry-run behavior.
- `.lazy-harness/bin/lazy` — fixture for wrapper dispatch and fresh per-invocation `LAZY_PI_TARGET_REPO` / `LAZY_OMP_TARGET_REPO` handoff.
- `.lazy-harness/scripts/agent-activate.ts` — fixture for project-local Pi/OMP activation prompt files, project-local skill settings, and `.git/info/exclude` entries.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — fixture for root-scoped recent tool state, live session cwd resolution after runtime `/move`, read-debt status/detail markers, normal-turn and steer evidence epochs, late-result exclusion, current-turn-only `agent_end` projection, and opt-in content-free tracing.
- `.pi/settings.json` — optional generated project-local Pi settings; activation ensures project-owned `../.claude/skills`, `../.codex/skills`, and `../.agents/skills` load with `enableSkillCommands`, while local package install may add package attachment; absent in clean default.
- `~/.pi/agent/settings.json` — optional generated global package install path; not committed to the repository and absent after factory reset.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — fixture for hook bridge events plus `/lazy-check`, `/lazy-validate`, and explicit fresh/full `/lazy-test` commands.
- `packages/lazy-harness-pi/prompts/lazy-harness.md` — fixture for fast edit-loop, focused-check, and one-final-standard-boundary guidance.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts#appendSystemPromptBody` — fixture for official Pi string prompt and OMP string-array prompt compatibility.
- `.lazy-harness/hooks/lifecycle/on-message-received.sh` — fixture for the per-turn reminder carrying the interactive grammar.
- `.lazy-harness/hooks/lifecycle/on-context.sh` — fixture for mechanical source-intent derivation and source-only host policy/capability guidance.
- `.lazy-harness/hooks/lifecycle/helpers/operating_rule_catalog.py` — fixture for bounded catalog enumeration, canonical resolver rendering, discovery-only copy, and explicit no-chain/no-rerun guidance.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — fixture for pre-context batching, failed-hook pending retry, at-most-once-per-turn injection, same-turn suppression after a cached body, and reset on fresh turn/steer.
- `packages/lazy-harness-pi/skills/*/SKILL.md` — fixture for shared Pi/OMP skill availability.
- `packages/lazy-harness-pi/skills/lazy-architecture-refactor/SKILL.md` — approval-gated architecture map and one-seam source-refactor contract.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` plus `_check_pi_agent_end_current_turn_scope` — regression implementation, including hermetic fake peer modules, live-session `/move` re-scope, post-steer re-arming, current-turn canonical lifecycle projection, failed-call structure, trace privacy/default-off/runtime-root assertions, and queued follow-up preservation.
- Machine index:
  - `kg_pi_agent_end_structural_trace_impl_20260714`
  - `kg_pi_agent_end_structural_trace_test_20260714`
  - `kg_pi_context_once_per_turn_20260818`

## Rule placement

- Rule: Pi package regression coverage must include OMP `before_agent_start` string-array `systemPrompt` compatibility so reminder injection does not collapse prompt blocks.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/pi-agent-package.md`
- Why not AGENTS.md: this is adapter regression coverage, not global prompt grammar.
- Why not `.jcode`: this protects shared Pi/OMP package behavior, not private Jcode wiring.
- Confirmation: inferred-from-runtime-evidence

## Rule placement

- Rule: Regression coverage must protect separate `lazy pi` and `lazy omp` wrapper command arrays plus explicit `package.json#omp`, so OMP does not silently fall back to Pi-only packaging.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/pi-agent-package.md`
- Why not AGENTS.md: this is package installer regression coverage, not global prompt grammar.
- Why not `.jcode`: this protects shared Pi/OMP package behavior, not private Jcode wiring.
- Confirmation: user-confirmed

## Rule placement

- Rule: Pi/OMP package regression coverage must protect runtime `/move` re-scope so stale `ctx.cwd` cannot leak hook root, recent tool evidence, or `/lazy-*` command execution across projects.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/pi-agent-package.md`
- Why not AGENTS.md: this is adapter regression coverage, not global prompt grammar.
- Why not `.jcode`: this protects shared Pi/OMP package behavior, not private Jcode wiring.
- Confirmation: confirmed-from-OMP-runtime-source

## Discovery capture — Pi agent-end trace

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: updated in `.lazy-harness/spec/platform/pi-agent-package.md`.
- BDD: none because trace collection is opt-in and does not alter normal agent behavior.
- TDD: updated because this record owns the fake-runtime protection.
- ADR: none because no payload or continuation semantics changed.
- SSOT: updated in `.lazy-harness/ssot/runtime-and-shared-state.md`.
- Planning: updated in the analysis-discovery capture backlog; fresh live reproduction remains pending.

## Discovery capture — current-turn tool scope

- Primary narrative remains `.lazy-harness/tests/project-rule-placement-gate-loop.md`; this record only carries the independent Pi/OMP adapter fixture delta.
- The fake runtime covers completed prior-turn evidence, a late old-turn result, a failed current-turn fetch, and a following tool-free turn.
- No new BDD/DDD/ADR record is warranted; SDD and SSOT impacts are linked in the layer-completeness matrix above.

## Discovery capture — bounded mid-turn re-grounding

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: updated in `.lazy-harness/spec/platform/pi-agent-package.md` because the adapter cadence and resolver-reuse contract changed.
- BDD: none because the agent-visible correction is fully owned by the platform adapter contract rather than a product flow.
- TDD: updated here with same-turn suppression, fresh-turn reset, and catalog no-chain/no-rerun fixtures.
- ADR: updated in `.lazy-harness/decisions/0048-operating-rule-storage-apply-repair.md` because the earlier per-file-op surfacing decision was narrowed after dogfood evidence.
- SSOT: none because policy/capability registry ownership, schema, and levels did not change.
- Planning: updated in `.lazy-harness/planning/workflow-churn-reduction-plan.md` as the primary work-unit narrative.
