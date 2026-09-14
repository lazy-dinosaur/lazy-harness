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
  - protect the dedicated Reader resource, exact launch envelope, content-not-ack join, cumulative budgets/failures, direct fallback, and non-interactive primary-answer preservation implemented in the isolated worktree
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
  - typecheck the complete Pi extension and real SDK integration test with Node22 declarations and execute that integration suite on Node22; keep Bun CLI/test ambients separate
  - keep fake-runtime regression fixtures hermetic: copy the extension beside bounded Pi/TypeBox peer stubs instead of assuming repository-local or machine-global peer resolution
- Must not:
  - invent a second policy engine or let OMP silently fall back to Pi-only packaging
  - count a generic child completion acknowledgement as Reader content delivery or treat an advisory-only print-mode message as a complete Parent answer
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

## Dedicated Reader topology fixtures — standard-verified in isolated worktree

The user-approved isolated implementation passed focused fixtures, final standard/full self-test, and independent blocker re-review; live model smoke and main integration remain pending:

| Case | Trigger | Expected |
|---|---|---|
| `pi_package_record_reader_resource` | Inspect package manifest and `agents/` | Exactly one `lazy-harness.record-reader` is exposed through Pi Subagents; proof/admission machinery is absent |
| `pi_reader_parent_lifecycle_isolation` | Dedicated Reader replacement system prompt contains `RECORD_READER_ROLE_MARKER` | Reader bypasses Parent reminder/context/response handlers but retains a dedicated child tool guard; Parent on the same root remains active |
| `pi_reader_child_tool_boundary` | Reader calls tools after role detection | Only canonical record read/grep and exact overview/drill/pwd/revision bash are allowed; source reads, mutation, compound bash, and arbitrary commands block |
| `pi_reader_parent_parallel_lanes` | Start a Reader-managed work unit | Native `read`/`grep`/`find` and simple shell `grep`/`rg` (head/tail/wc filters only) remain available; chained/redirection/substitution/write-option/nested shell mutations block |
| `pi_reader_derived_per_read_cap` | Launch with count/total limits such as `6/1200` | Task/state require `maxLinesPerRead=200`; mismatched cap, over-observed limit, failed calls, or impossible zero/inconsistent ledger cannot join complete and must enable fallback |
| `pi_reader_wait_ack_not_join` | Async Reader process reports `complete` without result content in Parent context | Plan/mutation/completion remains blocked; liveness acknowledgement alone is not a join |
| `pi_reader_content_join` | Matching run/root revision/epoch packet arrives with complete marker, canonical paths, in-budget counters, and zero failures | `lazy_reader_join` caches record fingerprints and permits action without duplicate Parent reads |
| `pi_reader_noncomplete_fallback` | Packet is missing, `incomplete`, `conflict`, failed, over-budget, mismatched, or invalidated by steer | Join fails or bounded Parent fallback remains; no silent success |
| `pi_reader_agent_contract_v1_read_only` | Reader completes without edits under Agent Contract v1 and `acceptance:false` | Runtime accepts the read-only result; no legacy no-edit completion failure |
| `pi_print_advisory_preserves_primary_answer` | In exact `ctx.mode === "print"`, `agent_end` receives an advisory after Parent synthesis | No follow-up assistant turn is queued; primary stdout survives and advisory text is emitted to stderr |
| `pi_tui_json_rpc_advisory_delivery` | Same advisory under non-print modes | Existing bounded `followUp` behavior remains; print-specific stderr separation does not alter these modes |

Validation/review capsules: `.lazy-harness/evidence/dedicated-reader-runtime-v1-20260906.md` and `.lazy-harness/evidence/dedicated-reader-live-canary-r2-20260906.md`.

Live R2 confirms agent discovery, Reader lifecycle isolation, content-before-join, honest incomplete handling, no duplicate Parent record reads, source preservation, and print stdout/stderr separation. It also reproduces `1,350/1,200` Reader lines and Python false-block of Parent source `rg`; the user selected and isolated source implements derived per-read cap plus guard parity without a model rerun.

### Layer completeness — Reader topology regression

| Layer | Independent delta | Disposition |
|---|---|---|
| DDD | no | Existing Harness Reader/Parent lane/join terms are sufficient |
| SDD | yes | Pi package and search-read-debt contracts define resource, content join, budget/fallback, and print output |
| BDD | yes | LLM-owned retrieval adds result-content and caller-output scenarios |
| SSOT | yes | Enforcement SSOT records exact successful Reader join plus direct fallback; no persistent settings owner changed |
| ADR | yes | ADR 0055 reaffirms subagent Reader as target rather than Parent fallback |

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
- `packages/lazy-harness-pi/agents/record-reader.md` and `package.json` — dedicated canonical-record-only role and Pi Subagents registration.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — role isolation plus dedicated child tool boundary, strict Parent safe-shell classifier, launch-bound cap/max-observed/positive-ledger join, fallback/steer/fingerprint lifecycle, and print stderr separation.
- `.pi/settings.json` — optional generated project-local Pi settings; activation ensures project-owned `../.claude/skills`, `../.codex/skills`, and `../.agents/skills` load with `enableSkillCommands`, while local package install may add package attachment; absent in clean default.
- `~/.pi/agent/settings.json` — optional generated global package install path; not committed to the repository and absent after factory reset.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — fixture for hook bridge events plus `/lazy-check`, `/lazy-validate`, and explicit fresh/full `/lazy-test` commands.
- `packages/lazy-harness-pi/prompts/lazy-harness.md` — fixture for fast edit-loop, focused-check, and one-final-standard-boundary guidance.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts#appendSystemPromptBody` — fixture for official Pi string prompt and OMP string-array prompt compatibility.
- `.lazy-harness/hooks/lifecycle/on-message-received.sh` — Reader-first/content-join/direct-fallback first-grounding reminder.
- `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` and `check-search-performed.sh` — strict safe-shell parity and truncation of all pre-join evidence after non-complete or errored-complete join.
- `.lazy-harness/hooks/lifecycle/on-context.sh` — fixture for mechanical source-intent derivation and source-only host policy/capability guidance.
- `.lazy-harness/hooks/lifecycle/helpers/operating_rule_catalog.py` — fixture for bounded catalog enumeration, canonical resolver rendering, discovery-only copy, and explicit no-chain/no-rerun guidance.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — fixture for pre-context batching, failed-hook pending retry, at-most-once-per-turn injection, same-turn suppression after a cached body, and reset on fresh turn/steer.
- `packages/lazy-harness-pi/skills/*/SKILL.md` — fixture for shared Pi/OMP skill availability.
- `packages/lazy-harness-pi/skills/lazy-architecture-refactor/SKILL.md` — approval-gated architecture map and one-seam source-refactor contract.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract`, `check_read_debt_permit_generic_external_action`, and `check_tool_execute_before_hook` — child boundary, exact/derived budgets, max-observed/failed/impossible ledgers, safe source lane, adversarial shell/nested forms, failed-join evidence truncation, fallback/path/steer/output, and complete/incomplete guard coverage.
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

## Pi target typecheck closure

This is the primary TDD record for the isolated B type follow-up, not semantic
capture acceptance or live adoption. The prior five-diagnostic mixed Node/Bun
command is retained as failing evidence, not relabeled as a canonical Pi check.

- `appendSystemPromptBody` overloads preserve string → string and string[] →
  string[]; the Pi `before_agent_start` event is contextually typed by its SDK.
  The implementation still filters OMP blocks exactly as before. Existing fake
  Pi/OMP prompt-shape assertions and both move paths remain protected.
- `MoveProjectDetails` explicitly describes both existing tool results through
  `AgentToolResult`, including boolean autoSwitch and optional switchedSessionFile.
  No registration, session-switch or tool-return runtime behavior changes.
- `bun run typecheck:pi` checks all extension sources plus the actual
  `pi-capture-evidence.test.ts` and transitive SDK declarations using the Pi
  workspace's pinned Node22 types. No skipLibCheck, ambient shim, library exclusion
  or global compiler is used. `bun run test:pi-capture` actually executes Node's
  native TypeScript stripping and node:test, not Bun with Node-only typechecking.
- The existing 25 capture cases retain their full real ExtensionRunner/read/write/
  hook assertions. Only test hooks/assert API, portable import.meta path and timeout
  syntax move from Bun to Node. No model calls or third-party native insert/replace
  coverage is implied. `check_analysis_discovery_capture_helper` runs the canonical
  Pi typecheck and test scripts; the framework registry remains 89 checks.
- Genai 1.52.0 imports MCP client types despite its optional ^1.25.2 peer;
  the source development manifest explicitly supplies compatible SDK 1.30.0.
  This adds no MCP runtime enablement, connection or installed-module patch.
- Node22 @types/node 22.19.19 matches Pi's own development declarations and retains
  PlatformPath. Root @types/node 26.5.0 remains only Bun1.3.14 supporting declarations.
  Workspaces + the Pi config's explicit typeRoots prevent cross-target mixing.
- gaxios7.3.1 assumes callable global fetch has no required preconnect property.
  Bun's full global fetch does require it; public gaxios7 and even8 declarations
  remain incompatible. The SDK-on-Bun integration-test mode is no longer claimed;
  no upstream declaration repair is claimed. Production Node22 is the test target.
- `typecheck:bun` and its D07 historical `typecheck:node` alias are unchanged;
  the semantic-invalid/valid and absent/decoy-global-tsc protections are unchanged.
  `typecheck:bun-tests` checks the real Bun affected-test source and Bun package CLI.
  Detector sample test files with intentionally unbound test globals remain input
  fixtures for source analysis, not executable test targets.

### Target closure layer completeness

| Layer | Judgment |
| --- | --- |
| SDD | Independent target contract: Pi SDK integration executes/checks on Node22; see `.lazy-harness/spec/platform/pi-agent-package.md`. Prompt/move runtime behavior is unchanged. |
| BDD | No independent delta: all capture outcomes and primary-answer/advisory separation remain unchanged. |
| SSOT | Independent dependency/config delta is owned by `package.json`, `packages/lazy-harness-pi/package.json`, `bun.lock` and Pi `tsconfig.json`; this section records why the existing Node/Bun support split needs two declaration roots and the optional MCP peer. No state/ownership policy change. |
| DDD | No independent delta: no domain terminology/business rule changes. |

### Target closure implementation map

- `package.json` — `typecheck:pi`, `test:pi-capture`, `typecheck:bun-tests` commands;
  unchanged D07 Bun alias and local compiler.
- `packages/lazy-harness-pi/tsconfig.json` — complete extension + SDK integration
  coverage with Node22 type root, module-preserve/bundler resolution with the node condition and declaration checking.
- `packages/lazy-harness-pi/package.json`, `bun.lock` — locked Node22 workspace types;
  root manifest locks the supported MCP declaration peer.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` —
  `appendSystemPromptBody`, `MoveProjectDetails`, `before_agent_start`, tool execute.
- `tests/lazy-harness/pi-capture-evidence.test.ts` — unchanged structural scenarios
  on native node:test / node:assert with actual SDK dispatch and full hooks.
- `.lazy-harness/scripts/self-test.py#check_analysis_discovery_capture_helper` —
  invokes both canonical Pi scripts without adding/removing top-level checks.
- `.lazy-harness/tests/test-strategy.xml` — discoverable runtime-specific commands.
- Graph: `kg_b_pi_target_typecheck_closure`.

### Declaration consumer limitation

Pi's official extensions documentation specifies jiti, and shipped
`dist/core/extensions/loader.js#loadExtensionModule` uses createJiti with SDK
aliases/virtual modules; it does not compile extension modules with NodeNext.
The canonical semantic check uses module preserve / bundler / customConditions
node with the complete SDK declaration graph. Native Node22 execution is checked
separately, rather than inferred from permissive import resolution.
A preserved failed NodeNext checkpoint exposes 39 Pi-AI generated model declaration
JSON imports missing attributes; the corresponding emitted JS correctly uses
`with { type: "json" }`. No NodeNext certification or upstream declaration repair
is claimed. The root manifest also declares Pi-AI0.85.1 explicitly because the
integration test directly imports its AssistantMessage type; no transitive hoisting
is assumed after a clean workspace install.

### Review P1 — Node validation cache identity

The Node-executed Pi typecheck and integration suite make Node an actual
full-regression dependency. `validation-governor.py#toolchain_fingerprint` now
includes the existing `command_signature("node")`: resolved executable path,
version output, or explicit missing signature. Previously changing/removing only
Node left a successful evidence key reusable. No runtime support policy changes.

`self-test.py#_check_node_validation_cache`, invoked by the existing
`check_bounded_validation_governor_cli`, stores synthetic successful cache evidence
and checks real signature/key/cache functions under isolated version-only executable
PATHs. Same-version/different-path, same-path/different-version, and missing Node
must all miss; unchanged and restored Node reuse are positive controls. This
fixture does not impersonate a passing Pi suite. The top-level registry stays89.

| Layer | Review-fix judgment |
| --- | --- |
| SDD | Independent cache identity correction in `.lazy-harness/spec/platform/bounded-validation-governor.md`: include Node beside Python/Bun/Git. |
| BDD | No independent delta; existing valid-cache reuse and stale-cache rerun behavior is preserved. |
| SSOT | `.lazy-harness/tests/test-strategy.xml` names the corrected toolchain inputs; cache storage/schema and dependency/runtime support policies are unchanged. |
| DDD | No domain delta. |

Implementation map: governor `toolchain_fingerprint` / `command_signature`;
self-test `_check_node_validation_cache` / `check_bounded_validation_governor_cli`;
`.lazy-harness/tests/bounded-validation-governor.md#protected-fixtures`.
Graph: `kg_b_pi_node_cache_identity`.

## Discovery capture — Reader topology TDD design

- DDD: none; no new term required.
- SDD: updated in Pi package and search-read-debt contracts.
- BDD: updated with content-bearing join and primary-answer preservation.
- TDD: updated here with focused-green fixtures and the immutable failing live witness; a corrected live model run is still pending.
- ADR: updated to reaffirm dedicated Reader ownership.
- SSOT: none; runtime/config storage unchanged.
- Planning: isolated implementation is focused-green; live model, main integration, commit/push/release remain unapproved.

## Discovery capture — Reader topology TDD implementation

- DDD — `none`: no independent domain rule changed.
- SDD — `updated`: implemented package/join/debt/output and post-R2 adversarial guard contracts.
- BDD — `none`: existing Reader content/final-output scenarios remain sufficient.
- TDD — `updated`: implemented fixtures cover child boundary, ledger, shell, fallback cache, and immutable live failure without overclaim.
- ADR — `none`: ownership and direct-fallback decision are unchanged.
- SSOT — `updated`: exact complete join and failed-join reset semantics are captured in enforcement policy.
- Planning — `updated`: static implementation, independent blocker re-review (`No issues found`, isolated `OK`), and standard validation (`76.201s`) are complete; new live model and integration remain gated.

## R3 launch-budget remediation regression

- The valid Reader launch omits `toolBudget`. Explicit all-tool or read-only block budgets, including null, are rejected before a child starts; this prevents conflating six body reads with six total calls.
- Existing valid-launch and pending-source-rg fixtures remain green requirements. Redirection is still rejected, not silently stripped or allowed.
- Distributed Parent prompt must say to omit `toolBudget`, prohibit `2>/dev/null`, drain a pending notification before one final, and avoid incomplete join in a terminal no-fallback canary.
- Implementation: `packages/lazy-harness-pi/extensions/lazy-harness/index.ts#readerLaunchValidationError`; `packages/lazy-harness-pi/prompts/lazy-harness.md`; `.lazy-harness/AGENTS.md`; protection: `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract`.

### Discovery capture / layer completeness

| Layer | Judgment | Reason |
|---|---|---|
| DDD | none | No domain delta. |
| SDD | updated | Pi package launch rejects the incompatible budget override. |
| BDD | updated | Pending-failure guidance drains before a single final response. |
| TDD | updated | Executable launch rejection and prompt regressions above. |
| ADR | none | Reader ownership unchanged. |
| SSOT | none | No config/storage ownership change. |
| Planning | updated | User approved fixing R3 problems; historical terminal result remains immutable. |

## R4 actual-notification regression

- Matching native Reader completion content closes the content-receipt barrier without `subagent_wait`.
- Legacy wait completion or stale-epoch notification cannot substitute for delivered content.
- A second Reader launch in the same evidence epoch is rejected.
- Invalid budgets/paths/counters still fail after a matching notification, not merely because notification was absent.
- Source: `index.ts#observeReaderPacket`, launch/context/join handlers; test: `self-test.py#check_pi_package_layout_and_contract`.
- Discovery capture: SDD/TDD updated; DDD/BDD/ADR/SSOT none (restore selected content-bearing join behavior); Planning updated through R4 evidence. Actual source-path guessing and retry violations remain live-model behavior risks, not silently fixed by static tests.

## R5 absolute operands and tool-surface regression

Fixtures accept same-root absolute canonical read and grep operands, while rejecting sibling-prefix roots, source paths, and traversal. Existing relative operand tests remain. Join identifiers remain relative. Protection: `self-test.py#check_pi_package_layout_and_contract`, `index.ts#readerToolPath/isReaderRuntimeToolAllowed`.

Actual SDK zero-model initialization verifies explicit read/grep/find/bash/subagent/lazy_reader_join availability; no prompt/model request occurs. This validates tool activation, not model behavior or final answer quality. Evidence `/tmp/lh-reader-tool-preflight-88q_8qyl/check.ts` and `result.json`.

Discovery capture/layer completeness: SDD updated (native operand normalization and launcher preflight), TDD updated (fixtures and SDK evidence), Planning updated (R5 terminal and remaining run boundary); DDD/BDD/ADR/SSOT none (no new domain, user flow, ownership, or persistent configuration).

## Reader status coordination repair regression

The shared `packages/lazy-harness-pi/fixtures/reader-status-inspection.json` table drives both the package fake runtime and the Python lifecycle hook. It permits ordinary/transcript status only for the exact pending Reader run at the current root/evidence epoch. Wrong/unknown run, stale epoch, wrong root, non-pending state, launch/resume, and mutation-like status extras remain denied. The package fixture additionally proves that a status result containing a fake complete marker and canonical path cannot replace native `subagent-notify` content; the hook fixture proves the same result cannot seed modern or legacy evidence before a write. Existing native content join and fresh bounded fallback cases remain the positive completion/recovery controls.

### Layer completeness matrix

| Layer | Independent delta | Disposition |
|---|---|---|
| SDD | yes | Search/read-debt contract now defines trusted owned-status classification and bookkeeping exclusion. |
| BDD | yes | LLM-owned retrieval distinguishes purposeful inspection/native yield from polling and content join. |
| SSOT | no | No configuration, schema, persistent owner, or authorization registry changed. |
| DDD | no | Existing Reader/run/join vocabulary is sufficient. |

### Implementation map — status coordination repair

- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts#isOwnedReaderStatusInspection` — independently validates exact operation, owned run, pending state, root-scoped current epoch, and read-only argument shape; trusted state is projected outside model-owned tool args for the hook.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts#readerStatusInspectionContext` — projects root/run/evidence/current-epoch/pending transport state; allowed status skips tool-call epoch, recent-call, and fingerprint bookkeeping.
- `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py#is_owned_reader_status_inspection` — independently evaluates the same shared cases before exempting status from pre-grounding action classification.
- `packages/lazy-harness-pi/fixtures/reader-status-inspection.json` — one bounded TS/Python parity table.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` and `#check_read_debt_permit_generic_external_action` — actual adapter and actual hook invocation, fake-status non-evidence, native content join, denials, and existing incomplete-fallback protection.
- Cross-layer: `.lazy-harness/spec/platform/search-read-debt-contract.md`; `.lazy-harness/behavior/llm-owned-record-retrieval.md`.

Discovery capture: primary TDD updated for the confirmed regression; SDD and BDD carry independent contract/agent-flow deltas; SSOT/DDD have no independent delta; ADR/Planning are unchanged because ownership, architecture, budgets, live comparison, and integration gates did not change.

Review follow-up: management operations carrying the Reader marker and an otherwise valid launch envelope are rejected before state creation (`action` must be absent on native launch, including rejecting null). Python handles action-bearing controls before free-text search-handoff exemptions. Fixtures include marker-bearing resume/steer/stop, malformed status task markers, oversized transcripts, and invalid epoch/pending metadata. This protects operation semantics, not exact natural-language task spelling.

## Native lifecycle, identity, and actual accounting regression — isolated follow-up

User approved the host plus an isolated upstream copy, not installed dependency mutation or another paid comparison. Primary canonical record: this TDD. Preserve the earlier waiting-only terminal, ID substitution, over-budget read, and inaccurate self-report witnesses.

| Protection | Expected |
|---|---|
| Real SDK delayed content | Parent finishes independent turn first; pending notification and unscanned terminal-result paths both deliver content and cause exactly one substantive continuation, not merely process exit. |
| Real SDK child guard | Native agent discovery resolves agent-relative `subagentOnlyExtensions`; SDK loads the guard under the explicit built-in allowlist. |
| Concurrent seventh read | Six admissions charge 1,200 lines under 6/1,200; seventh is denied before read execution and failure count becomes one. |
| Failed body read / over-limit | Failed admitted read charges count/lines; over-limit request is denied before read; model zero-failure prose cannot replace actual ledger. |
| ID confusion / spoof / stale / sibling | Arbitrary first UUID ignored; omitted join identity/counters bind to runtime-owned values; supplied child ID/counter mismatch, stale ledger, and sibling notification reject complete. |
| Fallback | Missing/nonterminal ledger and noncomplete results preserve fresh bounded Parent fallback; existing Python modern/legacy debt regressions remain. |

### Layer completeness matrix

| Layer | Independent delta | Disposition |
|---|---|---|
| SDD | yes | Pi package and search/read-debt define structural notification identity, runtime-owned session ledger, optional join defaults, and content-drain contract. |
| BDD | yes | Delayed content triggers substantive continuation; admission failures and identity confusion recover without polling or self-report authority. |
| SSOT | no | Existing native session state owns the ledger; no new persistent configuration owner, global setting, or canonical storage location. |
| DDD | no | Existing Reader/run/join terms suffice; no domain-rule change. |

### Implementation map — native follow-up

- `packages/lazy-harness-pi/agents/record-reader.md` — supported child-only guard loading.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — `parseReaderRunId`, `startReaderMeter`, `persistReaderMeter`, `readDeliveredReaderLedger`, `observeReaderPacket`, child tool handlers, and `lazy_reader_join`; admission/result/terminal runtime ledger and default owned binding.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — structural launch IDs, notification metadata, ledger fixture, default join ID and existing adversarial/fallback checks.
- `.lazy-harness/scripts/self-test.py#check_read_debt_permit_generic_external_action` — existing fresh direct fallback and status-not-evidence protections.
- Approved upstream copy `/tmp/lh-reader-native-followup-hf9m835b/pi-subagents`: `src/runs/background/{auto-drain,completion-batcher,notify,result-watcher}.ts` and `src/extension/index.ts` are inspected lifecycle seams (completion-batcher itself unchanged); `test/reader-delivery-sdk.test.ts` and `test/reader-accounting-sdk.test.ts` execute offline against the real installed SDK with scripted, zero-cost providers.
- `.lazy-harness/evidence/reader-coordination-repair-and-comparison.md` — exact reproduction, commands, approval, result and isolation capsule.

Discovery capture: TDD primary with independent SDD/BDD deltas above; SSOT/DDD/ADR no independent delta. Runtime entries are transport/accounting, not an admission/proof stack or semantic completeness oracle. Historic live failures remain unchanged; no new live trial, main integration, or default-readiness claim. Legacy graph migration (37 rows) remains a separate user-guided backlog, not silently rewritten here.


### Native launcher and review follow-up

- SDK pre-hook schema/unknown-tool errors are reconciled from actual child agent_end results, deduplicated against settled IDs; invalid-read then valid-read cannot seal a zero-failure ledger or join complete.
- Already-held notification batches are tested in addition to completions arriving during drain.
- `test/reader-native-launcher.test.ts` in the approved upstream copy runs actual CLI, detached native runner, child SDK, host guard, notification and Parent join against a scripted provider with network denial. It initially exposed an unpublished active-run marker and the native `Task: ` transport prefix. Source repairs publish the initial running index before runner authorization, clean it on startup failure, and unwrap the documented prefix before meter parsing. Retained end-to-end assertions now pass: delayed child, machine ledger, default-owned join and substantive continuation.
- Additional implementation seam: upstream `src/runs/background/async-execution.ts#spawnRunner/persistPreProceedStartupFailure`. No installed-package modification. Existing four-row layer matrix still applies.
- Review81958866 BLOCK findings repaired; focused follow-up5838725e OK. Final focused tests19/19,160 assertions; strict host tsc PASS. Upstream targeted transitive check has236 baseline/236 candidate diagnostics, no introduced diagnostics; full upstream type cleanliness is NOT claimed.

## Trusted full-ledger path handoff regression

User-approved isolated repair of the six-category benchmark slot16: six actual successful reads versus five submitted paths must not require duplicate Parent retrieval. Effective join paths come from all own keys of the trusted terminal ledger; optional legacy assertions may be omitted/empty or a distinct subset, never a source of additional evidence. Unread/outside/duplicate/malformed supplied paths still fail. All effective paths remain canonical-checked and rehashed; omissions cannot hide a changed/deleted file or remove its cached fingerprint. Root/revision/epoch/model/task/session, completion, read-budget and failure checks remain mandatory.

### Implementation map

- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — `lazy_reader_join` derives the full path set, validates optional assertions and rehashes all files before caching; details return actual paths.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — shipped fixture covers six-read/five-path and omitted-path success, unread/duplicate refusal, changed omitted-path refusal and post-join invalidation when an omitted file changes. Existing identity/budget/traversal/notification tests remain.
- `packages/lazy-harness-pi/prompts/lazy-harness.md` and `packages/lazy-harness-pi/README.md` — recommend omission of runtime-owned run/counter/path fields rather than manual recopying.
- Isolated SDK test `/tmp/lh-reader-native-followup-hf9m835b/pi-subagents/test/reader-accounting-sdk.test.ts` — actual child SDK six-distinct-read ledger, omitted/empty/subset success, unread/duplicate/outside/traversal/absolute/malformed assertions and changed/deleted omitted-file failure. This is supplementary local evidence, not a shipped test dependency.
- Contract: `.lazy-harness/spec/platform/search-read-debt-contract.md`, `.lazy-harness/spec/platform/pi-agent-package.md`; behavior: `.lazy-harness/behavior/llm-owned-record-retrieval.md`; evidence: `.lazy-harness/evidence/reader-coordination-repair-and-comparison.md`.

### Layer completeness

| Layer | Judgment |
|---|---|
| SDD | Independent delta: authoritative path derivation, legacy subset compatibility and effective-path response documented in join contract. |
| BDD | Independent delta: path omission alone no longer forces Parent fallback; unsafe assertions still do. |
| SSOT | No independent delta: runtime ledger storage/ownership and canonical-record authority unchanged. |
| DDD | No independent delta: no new domain terms or business rules. |

Discovery capture: one bounded repair, primary TDD here; no installed/main integration or live paid benchmark implied.
