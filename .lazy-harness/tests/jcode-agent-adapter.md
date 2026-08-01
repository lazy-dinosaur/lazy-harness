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
- Must not:
  - claim unsupported context reinjection, continuation, or native ask parity
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
| `jcode_doctor_capabilities` | Doctor with missing binary/config, trust, matching config, and conflicts | Structured report distinguishes availability, trust, hooks, conflicts, and gaps |
| `jcode_hook_untrusted_noop` | Invoke every hook in non-lazy and marker-only untrusted roots | Exit 0, no output, no repository script execution, no state files |
| `jcode_turn_start_arms_root` | Invoke turn-start in a temp lazy root | Root/session state is initialized without user-text classification |
| `jcode_before_model_initial` | Invoke before-model before any successful tool evidence | Strict bounded system-reminder JSON from the canonical static message hook is emitted |
| `jcode_before_model_post_tool` | Invoke before-model after one successful correlated file-touching tool | Strict bounded system-reminder JSON from `on-context.sh` includes structural recent-tool evidence |
| `jcode_before_model_fail_open` | Canonical context hook is empty, malformed, oversized, fails, or root is untrusted | Exit 0 with no stdout/stderr and no prompt mutation |
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
| BDD | no | Phase 1 is internal context transport; the later native ask phase will require a separate visible interaction judgment. |
| SSOT | yes | `.lazy-harness/ssot/harness-enforcement-policy.md` now owns the Pi/OMP/Jcode delivery boundary; runtime path ownership remains unchanged. |
| DDD | no | No domain term, entity, or business invariant changes. |

## Implementation map

- Status: Phase 1 core hook/config/prompt tests and focused adapter fixture pass; source-build live matrix pending
- Primary files:
  - `/home/lazydino/dev/jcode/crates/jcode-base/src/hooks.rs` — 11 strict parsing, bounds, timeout, recursion, request-kind, and dynamic-only injection tests.
  - `/home/lazydino/dev/jcode/crates/jcode-base/src/config_hook_tests.rs` — extracted hook config/default/env regression tests.
  - `.lazy-harness/scripts/self-test.py` — adversarial TOML, trust, secret-free state, runtime-root, deny-cleanup, before-model transport, and non-regression fixtures.
  - `.lazy-harness/scripts/jcode-adapter.ts` — runtime target under test.
  - `.lazy-harness/scripts/jcode-trust.ts` — exact-root trust registry target under test.
  - `.lazy-harness/scripts/jcode-package.ts` — install/doctor/smoke/remove/trust target under test.
  - `.lazy-harness/bin/lazy` — dispatch target under test.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter` — intended coverage includes Bun build, legal/invalid TOML, byte round trips, trust/untrust and relative-home attack, every-hook marker-only no-op, runtime isolation, URL/path secrecy, stale/ambiguous correlation, lock ownership/recovery, and true deny-cleanup failure.
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
- BDD: no independent delta.
- TDD: this record owns the regression contract.
- ADR: architecture decision linked above.
- SSOT: independent delivery-boundary delta in `.lazy-harness/ssot/harness-enforcement-policy.md`.
- Planning: staged implementation is tracked in `.lazy-harness/planning/jcode-runtime-adapter-pilot.md`.
