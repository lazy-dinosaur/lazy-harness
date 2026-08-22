# TDD — Jcode Integration Decommission

Status: active
Date: 2026-08-22
Layer: TDD
Primary ADR: `.lazy-harness/decisions/0059-pi-primary-jcode-decommission.md`
Related SDD: `.lazy-harness/spec/platform/pi-agent-package.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - Jcode removal regression
  - Pi-only activation regression
- Applies when:
  - removing or auditing Jcode integration
  - changing agent activation, init, sync, runtime CLI, manifests, policies, or lifecycle adapters
- Must:
  - prove Pi activation and OMP Experimental behavior remain functional without Jcode state
  - prove active Jcode CLI, adapter, hooks, trust, transport, policy, capability, and distribution surfaces are absent
  - preserve runtime-neutral grounding, lifecycle payload, progress, validation, and command-boundary coverage
  - protect exact machine rollback and user-owned configuration during decommission
- Must not:
  - require a Jcode binary, JCODE_HOME, trusted-root registry, or `.jcode` project transport for Pi/OMP operation
  - delete historical Jcode records or the rollback snapshot as part of source validation
- Record completion:
  - fixture changes update this TDD and ADR 0059

## Regression matrix

| Case | Trigger | Expected |
|---|---|---|
| `runtime_support_policy` | Inspect ADR/SSOT/package records | Pi is stable primary; OMP is Experimental; Jcode is decommissioned |
| `lazy_cli_no_jcode` | Inspect/run CLI help | No active `lazy jcode` dispatcher or help command remains |
| `agent_activate_pi_omp_only` | Run activation in an isolated initialized host with hostile `JCODE_HOME` | Pi/OMP files, Pi skill settings, and excludes are managed; no Jcode state is read or written |
| `lazy_init_pi_omp_only` | Initialize an isolated host | Explicit target receives Pi/OMP activation only |
| `lazy_sync_pi_omp_repair` | Sync an isolated host with no Jcode state | Pi/OMP activation is checked/repaired independently and marker publication remains transactional |
| `jcode_sources_absent` | Inspect active source tree | Adapter/package/trust/local-config scripts and typed Jcode routing helper are absent |
| `jcode_registry_absent` | Audit policies/capabilities | No active Jcode typed-routing policy/capability remains |
| `jcode_distribution_absent` | Inspect init manifest | No active Jcode adapter/channel/typed-routing contract or integration guide is distributed |
| `runtime_neutral_payload_preserved` | Run Pi fake runtime | Current-turn lifecycle payload, evidence epochs, error structure, continuation bounds, and trace privacy remain unchanged |
| `runtime_neutral_progress_preserved` | Run validation progress fixture | `LAZY_PROGRESS` behavior remains active and runtime-neutral |
| `machine_exact_cleanup` | Inspect decommission receipt | Managed hooks/trust/local flag are gone; launcher is exactly restored; unrelated config and stable/current pointers are preserved |

## Layer completeness

| Layer | Independent delta? | Judgement |
|---|---|---|
| SDD | yes | Pi/OMP activation and package contract no longer depend on Jcode install/trust. |
| BDD | yes | Jcode native ask/follow-up behavior is retired; Pi/OMP user behavior is unchanged. |
| SSOT | yes | Supported runtime delivery becomes Pi stable plus OMP Experimental. |
| DDD | no | No business/domain invariant changes. |

## Implementation map

- Status: implemented-focused-green-awaiting-final-standard
- Primary files:
  - `.lazy-harness/scripts/agent-activate.ts`
  - `.lazy-harness/scripts/lazy-init.ts`
  - `.lazy-harness/scripts/lazy-sync.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/self-test.py`
  - `.lazy-harness/manifests/init-categories.json`
  - `.lazy-harness/ssot/policies.json`
  - `.lazy-harness/ssot/capabilities.json`
- Protected tests:
  - `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract`
  - new decommission assertions in `.lazy-harness/scripts/self-test.py`
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0059-pi-primary-jcode-decommission.md`
  - SDD: `.lazy-harness/spec/platform/pi-agent-package.md`
  - SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`

## Rule placement

- Rule: source and machine decommission must remove Jcode integration without regressing Pi/OMP or reusable runtime-neutral behavior.
- Scope: framework-global.
- Primary record: `.lazy-harness/tests/jcode-decommission.md`.
- Confirmation: user-confirmed removal scope on 2026-08-22.
