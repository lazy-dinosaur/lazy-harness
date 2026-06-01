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
- If a policy is prevention-grade, repeated, or high-cost when missed, it must be surfaced or enforced before the miss becomes expensive; the final mechanism must preserve agent flow and avoid tool-specific adapter sprawl.

## Current dogfood finding

The observed failure mode is not that the rule records are missing. It is that the execution surface can fail to make agents consult and apply them before acting.

Symptoms observed on 2026-05-31:

- Agent read generic AGENTS-style command hints and shell/env files, but skipped the canonical Medivance dogfood runtime SSOT before reasoning about test instances.
- `response.completed` exists, but current generated Jcode wiring uses `blocking = false`, weakening the original completion-audit contract.
- `tool.execute.before` currently blocks dangerous bash, but does not generally ensure host-dependent rule recall.
- Record accumulation into DDD/SDD/BDD/TDD/ADR/SSOT appears lower when gates become advisory, because misses are reported after the response rather than surfaced naturally at the right moment.

## 2026-06-01 hard-gate experiment result

A hard-gate restoration experiment restored edit/write/multiedit blocking hooks and added tool-attached runtime/PR-style enforcement. The user rejected this direction because it felt too slow and too attached to concrete tools.

Result:

- Revert the hard-gate/tool-attached implementation.
- Keep the finding that rule recall must improve.
- Do not grow per-tool adapters as the primary architecture.
- Explore C+ v2 organic hybrid instead: ambient rule context, graduated guidance, soft action/journal continuity, and narrow hard stops only for irreversible or repeatedly failed boundaries.

## Required direction

Future fixes should restore mandatory behavior without turning the framework into a brittle or slow blocker:

1. Preserve current lazy-harness grammar injection through generated Jcode wiring and verify it continuously.
2. Improve rule recall before action, but prefer organic surfacing over broad edit/write blocking.
3. Keep `response.completed` as a backstop for missed record/capture work.
4. Add regression fixtures for concrete dogfood failures, but do not encode the final architecture as one-off tool-specific patches.
5. Keep workflow compression read-only/advisory unless it is explicitly wrapped by a mechanism that preserves canonical obligations.
6. Compare organic/free alternatives before implementing another enforcement mechanism.

## Implementation map

- Primary files:
  - `.lazy-harness/AGENTS.md` — shared framework grammar that defines mandatory record-first and record-as-output behavior.
  - `.lazy-harness/JCODE-INTEGRATION.md` — generated Jcode wiring guidance and hook expectations.
  - `.lazy-harness/scripts/jcode-wiring.ts` — generated `.jcode/config.toml` and harness file installation logic.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — completion backstop hook.
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — project-rule placement gate.
  - `.lazy-harness/ssot/medivance-dogfood-runtime-policy.md` — concrete runtime/test-instance policy skipped by the observed agent.
  - `.lazy-harness/planning/organic-hybrid-rule-guidance-plan.md` — current plan for C+ v2 organic hybrid exploration.
- Flow:
  1. User observes agents skipping mandatory lazy-harness rules.
  2. Hard-gate restoration is tested, then rejected for speed/tool-attachment reasons.
  3. The next design step is C+ v2 organic hybrid planning/ADR, not more tool-specific guards.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
  - Future fixtures for rule surfacing without broad hard gates.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`
  - ADR: `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md`
  - SDD: `.lazy-harness/spec/platform/project-rule-router.md`
  - SSOT: `.lazy-harness/ssot/rule-sources.md`
  - SSOT: `.lazy-harness/ssot/project-identity.md`

## Rule placement

- Rule: lazy-harness enforcement layers must not weaken into optional memory, but the replacement architecture should be organic/free and avoid broad slow blocking or tool-specific adapter sprawl.
- Scope: framework-global
- Primary record: `.lazy-harness/ssot/harness-enforcement-policy.md`
- Why not AGENTS.md: AGENTS is the operational grammar; this SSOT records the enforcement policy and dogfood result that should drive future architecture.
- Why not `.jcode`: this is shared framework behavior for all lazy-harness hosts, not a local/private Jcode-only workflow.
- Confirmation: user-confirmed

## Discovery capture

- DDD: none.
- SDD: future spec likely for ambient rule context, graduated guidance, soft action journal, and narrow hard-stop promotion.
- BDD: observed agent workflow failure captured as dogfood evidence; user wants a more organic/free workflow.
- TDD: future fixtures needed for skipped runtime/PR rule recall without broad hard gates.
- ADR: required before implementing C+ v2 organic hybrid.
- SSOT: updated, this record.
- Planning: `.lazy-harness/planning/organic-hybrid-rule-guidance-plan.md`.
