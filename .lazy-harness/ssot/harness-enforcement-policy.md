# SSOT — Harness Enforcement Policy

Status: accepted
Date: 2026-05-31
Layer: SSOT
Confirmation: user-confirmed

## Rule

Lazy-harness enforcement layers must not be weakened into optional memory or best-effort behavior.

The harness is mandatory infrastructure for agents that operate inside a lazy-harness host:

- Jcode wiring must reliably load the current lazy-harness grammar and project-local harness overlays.
- Agents must retain and apply the core rules during a session: record-first lookup, default-unknown, option gates, requirements-first execution, rule placement, and record-as-output.
- DDD/SDD/BDD/TDD/ADR/SSOT records are not optional notes. They are the canonical institutional memory and must continue accumulating when confirmed facts, rules, contracts, behavior, tests, or decisions are discovered.
- Advisory routing, telemetry, workflow compression, and non-blocking lifecycle hooks may improve throughput, but must not reduce the effective enforcement of canonical layer obligations.
- If a policy is prevention-grade, repeated, or high-cost when missed, it must be bound to an action boundary or guaranteed completion gate rather than relying only on post-response advice.

## Current dogfood finding

The observed failure mode is not that the rule records are missing. It is that the execution surface can fail to force agents to consult and apply them before acting.

Symptoms observed on 2026-05-31:

- Agent read generic AGENTS-style command hints and shell/env files, but skipped the canonical Medivance dogfood runtime SSOT before reasoning about test instances.
- `response.completed` exists, but current generated Jcode wiring uses `blocking = false`, weakening the original completion-audit contract.
- `tool.execute.before` currently blocks dangerous bash, but does not generally enforce host-dependent record lookup before bash-based investigation or runtime commands.
- Record accumulation into DDD/SDD/BDD/TDD/ADR/SSOT appears lower when gates become advisory, because misses are reported after the response rather than forced before or during the relevant action.

## Required direction

Future fixes should restore mandatory behavior without turning every preference into a brittle hard block:

1. Preserve current lazy-harness grammar injection through generated Jcode wiring and verify it continuously.
2. Promote prevention-grade record-first checks to action boundaries where they can prevent the mistake.
3. Keep `response.completed` as a guaranteed backstop for missed record/capture work.
4. Add regression fixtures for the concrete dogfood failures that caused the policy change.
5. Keep workflow compression read-only/advisory unless it is explicitly wrapped by a gate that preserves the canonical obligations.

## Implementation map

- Primary files:
  - `.lazy-harness/AGENTS.md` — shared framework grammar that defines mandatory record-first and record-as-output behavior.
  - `.lazy-harness/JCODE-INTEGRATION.md` — generated Jcode wiring guidance and hook expectations.
  - `.lazy-harness/scripts/jcode-wiring.ts` — generated `.jcode/config.toml` and harness file installation logic.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — completion backstop hook.
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — project-rule placement gate.
  - `.lazy-harness/ssot/medivance-dogfood-runtime-policy.md` — concrete runtime/test-instance policy skipped by the observed agent.
  - `.lazy-harness/planning/model-quality-dogfood-findings.md` — related dogfood findings about action-boundary placement.
- Flow:
  1. User observes an agent skipping mandatory lazy-harness rules.
  2. The finding is captured here as enforcement policy, not local `.jcode` preference.
  3. Implementation should adjust wiring/gates/tests in the source repo, then sync to downstream hosts for validation.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
  - Future focused regression fixture for Medivance named test instance record-first lookup.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`
  - ADR: `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md`
  - SDD: `.lazy-harness/spec/platform/project-rule-router.md`
  - SSOT: `.lazy-harness/ssot/rule-sources.md`
  - SSOT: `.lazy-harness/ssot/project-identity.md`

## Rule placement

- Rule: lazy-harness enforcement layers must not be weakened; Jcode wiring and record/capture gates must make canonical rules effectively mandatory, not optional memory or best-effort advice.
- Scope: framework-global
- Primary record: `.lazy-harness/ssot/harness-enforcement-policy.md`
- Why not AGENTS.md: AGENTS is the operational grammar; this SSOT records the enforcement policy and dogfood finding that should drive wiring/gate implementation.
- Why not `.jcode`: this is shared framework behavior for all lazy-harness hosts, not a local/private Jcode-only workflow.
- Confirmation: user-confirmed

## Discovery capture

- DDD: none.
- SDD: candidate changes to Jcode wiring and action-boundary contracts.
- BDD: observed agent workflow failure captured as dogfood evidence.
- TDD: future regression fixture needed for skipped Medivance dogfood runtime SSOT.
- ADR: existing ADR 0016/0037 remain relevant; future ADR may be needed if blocking semantics change.
- SSOT: updated, this record.
- Planning: implementation follow-up needed for wiring/gate fixes.
