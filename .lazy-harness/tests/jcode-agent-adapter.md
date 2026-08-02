# TDD — Jcode Agent Adapter Regression

Status: active
Date: 2026-08-01
Layer: TDD
Related ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
Related SDD: `.lazy-harness/spec/platform/jcode-agent-adapter.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - Jcode adapter regression
  - lazy jcode smoke
  - Jcode hook test
- Surface terms:
  - before_model injection
  - native ask picker
  - interaction session isolation
  - needs_input fallback
  - bounded turn followup
  - followup fingerprint
  - pre_tool gate
  - root isolation
  - config backup
  - install remove round trip
- Applies when:
  - changing Jcode adapter hooks, configuration merge, CLI dispatch, or root isolation
  - claiming Jcode support or parity with Pi/OMP
- Must:
  - protect untrusted/non-lazy no-op and explicit trusted-root activation
  - protect pre-tool allow/block translation and root/session evidence isolation
  - protect reversible idempotent TOML-safe config changes
  - protect trust registry, secret-free state, and canonical runtime-root sanitation
  - keep Pi/OMP regression coverage green
  - protect strict bounded initial and post-tool `before_model` injection without changing untrusted-root no-op behavior
  - protect bounded native ask, typed answer/cancel routing, continuation suppression, and unsupported-runtime fallback
  - protect strict bounded `turn_followup`, exactly-one origin control, stable fingerprinting, and ask/input/cancel/guardrail/error suppression
  - protect private reversible trusted-root `ignore_project_agents` configuration and canonical grammar injection priority
- Must not:
  - claim full live context, continuation, or native ask parity before the corresponding source-build matrix passes
- Record completion:
  - Jcode adapter bugs update this regression record and its layer matrix
- Related records:
  - `.lazy-harness/spec/platform/jcode-agent-adapter.md`
  - `.lazy-harness/tests/pi-agent-package.md`

## Regression target

The Jcode adapter must reuse canonical lazy-harness hooks only for exact user-trusted roots, preserve unrelated user config, persist no raw command/query/URL secrets, and never contaminate evidence across projects, sessions, or runtime roots.

## Protected fixtures

| Case | Trigger | Expected |
|---|---|---|
| `jcode_cli_dispatch` | Run `lazy jcode ...` | Dispatcher invokes the dedicated Jcode package/adapter surface, not `pi-package.ts` |
| `jcode_install_dry_run` | Install against a temporary TOML config with `--dry-run` | Desired managed commands are reported and no file changes |
| `jcode_install_backup_and_preserve` | Install against config containing unrelated sections/hooks | One backup is created; unrelated TOML values remain unchanged |
| `jcode_install_idempotent` | Install twice | Second run is a no-op and creates no duplicate hook values |
| `jcode_install_conflict` | Existing managed hook key has unrelated command | Stop before mutation and report the conflict |
| `jcode_remove_exact_only` | Remove after install across empty, LF/trailing-blank, and CRLF configs; then remove against unrelated values | Managed exact values and adapter-created empty table are removed; all unrelated bytes and values remain |
| `jcode_toml_legal_variants` | Install with commented `[hooks]` header and quoted hook keys | No duplicate table or invalid TOML is produced; conflicts stop before mutation |
| `jcode_path_with_spaces` | Source adapter path contains spaces | Managed command is shell-quoted and parsed as one executable path |
| `jcode_trust_registry` | Install/trust/untrust two canonical roots and attempt a repository-relative `JCODE_HOME` registry | Only exact user-home trusted roots activate; marker-only/relative-home attacker roots are silent |
| `jcode_local_prompt_transport` | Install/trust against a Git-backed lazy root containing unrelated local TOML | Only marker-owned `ignore_project_agents = true` is merged, the file is ignored, and backups stay in private Git metadata |
| `jcode_local_prompt_remove` | Remove with an explicit target or untrust a managed root | Only marker-owned key/table/file and exact managed exclude entry are removed; user-owned TOML remains |
| `jcode_local_prompt_conflict` | User-owned local config sets `ignore_project_agents = false` | Stop before trust/global-hook mutation and preserve the file byte-for-byte |
| `jcode_local_prompt_transaction_rollback` | Global hook write or local backup preparation fails after planning | Local config, Git exclusion, global hooks, and trust registry remain at their pre-command state |
| `jcode_remove_target_no_trust` | Run `remove --target` for an untrusted lazy root | Managed removal may run, but no trusted-root entry is created |
| `jcode_doctor_capabilities` | Doctor with missing binary/config, trust, matching config, and conflicts | Structured report distinguishes availability, trust, hooks, conflicts, and gaps |
| `jcode_hook_untrusted_noop` | Invoke every hook in non-lazy and marker-only untrusted roots | Exit 0, no output, no repository script execution, no state files |
| `jcode_turn_start_arms_root` | Invoke turn-start in a temp lazy root | Root/session state is initialized without user-text classification |
| `jcode_before_model_initial` | Invoke before-model before any successful tool evidence | Strict bounded system-reminder contains complete canonical `.lazy-harness/AGENTS.md` followed by static dynamic context |
| `jcode_before_model_post_tool` | Invoke before-model after one successful correlated file-touching tool | Canonical grammar remains first and bounded `on-context.sh` structural evidence is appended |
| `jcode_before_model_fail_open` | Canonical grammar is missing/empty/oversized or root is untrusted | Exit 0 with no stdout/stderr and no prompt mutation; malformed dynamic context alone does not remove valid canonical grammar |
| `jcode_before_model_exact_byte_bound` | Canonical grammar plus wrapper fits within 24,000 UTF-8 bytes | Complete grammar is injected; only dynamic context yields remaining budget |
| `jcode_before_model_failed_dynamic` | Dynamic lifecycle hook prints valid-looking JSON but exits nonzero | Canonical grammar remains injected and failed dynamic output is discarded |
| `jcode_ask_validation` | Ask has fewer than 3 or more than 5 options, duplicate/invalid ids, multiple recommended options, or oversized fields | Tool rejects before opening an interaction |
| `jcode_ask_broker_resume` | Supported client answers a pending ask | The same tool call resumes with typed selected/custom/cancelled JSON |
| `jcode_ask_session_isolation` | Wrong session, duplicate, late answer, disconnect, or broker replacement occurs | Wrong/duplicate/late answers are rejected and disconnect/replacement cancels the waiter |
| `jcode_ask_picker` | Local/remote picker receives navigation, custom, Enter, or Escape | Selection/custom/cancel is typed, custom input is bounded, and recommended remains visual metadata |
| `jcode_ask_headless_acp_fallback` | NDJSON or ACP has no native interaction capability | Structured `needs_input` is emitted immediately and no stdin wait occurs |
| `jcode_ask_suppresses_followup` | Picker is open while auto-poke or queued followup scheduling runs | No synthetic continuation dispatches until the interaction closes |
| `jcode_turn_followup_strict_output` | Controller emits valid, malformed, oversized, failed, or timed-out output | Only one bounded strict continuation is accepted; every other outcome stops normally |
| `jcode_turn_followup_exactly_once` | One real-user turn completes and the controller requests continuation more than once | Exactly one synthetic message can be claimed for that origin |
| `jcode_turn_followup_loop_bounds` | Fingerprint repeats, an ask is open, user input arrives, cancellation occurs, provider guardrail fires, or a non-retryable error occurs | Followup stops and cannot recursively create another allowance |
| `jcode_turn_followup_local_remote_headless` | Local TUI, remote server/client, and run-once paths receive a followup decision | System-generated status is explicit and the shared app-core controller owns bounds outside TUI-only state |
| `jcode_turn_followup_adapter_audit` | Trusted response-completed hook emits one bounded injection body | Adapter emits strict Jcode continuation JSON, clears per-turn evidence, avoids duplicate stop audits, and audits the issued synthetic response once |
| `jcode_pre_tool_blocks_canonical_deny` | Canonical before-tool hook emits deny | Adapter writes reason to stderr and exits 2 |
| `jcode_pre_tool_allows` | Canonical before-tool hook is silent | Adapter exits 0 |
| `jcode_post_tool_success_evidence` | Successful read post-tool follows one fresh matching pre-tool; URL-shaped `path` is also attempted | Only canonical root-contained filesystem-path evidence is retained; raw command/query/URL text is absent |
| `jcode_post_tool_failure_not_evidence` | Failed, stale, or two parallel same-tool post-tool correlations | Entries cannot satisfy later mutation debt and stale/ambiguous pending rows are removed |
| `jcode_runtime_root_override` | Hook receives explicit `LAZY_RUNTIME_ROOT` | Adapter state and canonical hook journals share that exact root; default resolution remains worktree/session scoped |
| `jcode_lock_and_deny_cleanup` | Ownerless stale lock, live foreign lock at session-end, replaced-owner recovery, and canonical deny with state-save failure | Stale lock recovers, foreign/new owner survives, and deny still exits 2 |
| `jcode_root_session_isolation` | Interleave hooks for two roots and sessions | No state or evidence crosses either boundary |
| `jcode_turn_end_advisory` | Turn-end with bounded assistant text and tool evidence | Canonical audit runs once; no false claim of blocking or continuation |
| `jcode_pi_omp_non_regression` | Run existing Pi/OMP package fixture | Existing package contract remains unchanged and green |

## Validation route

During implementation:

1. run `.lazy-harness/bin/lazy check` during edit loops,
2. run the focused Jcode adapter self-test function or fixture,
3. run LSP/type diagnostics for changed TypeScript,
4. after the final mutation run `.lazy-harness/bin/lazy validate --plan standard` once.

Direct repeated `lazy test` runs are not part of the edit loop.

## Layer completeness

| Layer | Independent delta? | Judgement |
|---|---|---|
| SDD | yes | `.lazy-harness/spec/platform/jcode-agent-adapter.md` defines the new hook/config/runtime contract. |
| BDD | yes | `.lazy-harness/behavior/jcode-native-ask.md` owns picker behavior and `.lazy-harness/behavior/jcode-bounded-followup.md` owns visible system continuation/status behavior. |
| SSOT | yes | `.lazy-harness/ssot/harness-enforcement-policy.md` now owns the Pi/OMP/Jcode delivery boundary; runtime path ownership remains unchanged. |
| DDD | no | No domain term, entity, or business invariant changes. |

## Implementation map

- Status: Phases 1–3 focused hook/config/controller/protocol tests and adapter fixture pass; source-build live matrix pending
- Primary files:
  - `/home/lazydino/dev/jcode/crates/jcode-base/src/hooks.rs` — 11 strict parsing, bounds, timeout, recursion, request-kind, and dynamic-only injection tests.
  - `/home/lazydino/dev/jcode/crates/jcode-base/src/config_hook_tests.rs` — extracted hook config/default/env regression tests.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/tool/ask.rs` — ask validation and broker/no-broker tests.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/server/client_interactions.rs` — cross-session and duplicate/late response tests.
  - `/home/lazydino/dev/jcode/crates/jcode-tui/src/tui/interaction_picker.rs` — picker selection/cancel/custom bound tests.
  - `/home/lazydino/dev/jcode/crates/jcode-base/src/hooks/turn_followup.rs` — strict parsing, malformed/oversized output, timeout, and normal-stop tests.
  - `/home/lazydino/dev/jcode/crates/jcode-app-core/src/turn_followup.rs` — exactly-one, repeated fingerprint, pending interaction, cancellation, guardrail, and error tests.
  - `/home/lazydino/dev/jcode/crates/jcode-protocol/src/protocol_tests/misc_events.rs` — followup lifecycle wire round-trip.
  - `.lazy-harness/scripts/self-test.py` — adversarial TOML, trust, secret-free state, runtime-root, deny-cleanup, before-model transport, and non-regression fixtures.
  - `.lazy-harness/scripts/jcode-adapter.ts` — runtime target under test.
  - `.lazy-harness/scripts/jcode-trust.ts` — exact-root trust registry target under test.
  - `.lazy-harness/scripts/jcode-package.ts` — install/doctor/smoke/remove/trust target under test.
  - `.lazy-harness/scripts/jcode-local-config.ts` — local prompt transport merge/remove/privacy target under test.
  - `.lazy-harness/bin/lazy` — dispatch target under test.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter` — coverage includes Bun build, legal/invalid global and local TOML, local config privacy/removal, canonical initial/post-tool grammar injection, trust/untrust and relative-home attack, every-hook marker-only no-op, runtime isolation, URL/path secrecy, stale/ambiguous correlation, lock ownership/recovery, and true deny-cleanup failure.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/jcode-agent-adapter.md`
  - ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
  - TDD: `.lazy-harness/tests/pi-agent-package.md`
- Machine index:
  - graph ids: `kg_jcode_agent_adapter_test_20260801`, `kg_jcode_agent_adapter_runtime_20260801`, `kg_jcode_agent_adapter_install_20260801`, `kg_jcode_agent_adapter_trust_20260801`
  - generated index key: pending regeneration

## Rule placement

- Rule: Jcode support claims require reversible config, canonical pre-tool gating, root/session isolation, and Pi/OMP non-regression evidence.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/jcode-agent-adapter.md`
- Why not AGENTS.md: these are adapter regression cases, not per-turn grammar.
- Why not `.jcode`: protection belongs to framework self-tests and canonical TDD records.
- Confirmation: user-confirmed 2026-08-01

## Discovery capture

- DDD: no independent delta.
- SDD: independent delta linked above.
  - BDD: independent visible followup delta in `.lazy-harness/behavior/jcode-bounded-followup.md`.
- TDD: this record owns the regression contract.
- ADR: architecture decision linked above.
- SSOT: independent delivery-boundary delta in `.lazy-harness/ssot/harness-enforcement-policy.md`.
- Planning: staged implementation is tracked in `.lazy-harness/planning/jcode-runtime-adapter-pilot.md`.
