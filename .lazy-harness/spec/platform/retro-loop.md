# SDD — Retro Learning Loop (feedback → KPT → gated promotion)

Status: accepted
Date: 2026-07-04
Layer: SDD
Related ADR: `.lazy-harness/decisions/0053-memory-device-storage-discipline.md`, `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`
Related plan: `.lazy-harness/planning/memory-device-implementation-plan.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - a real-use divergence, miss, or repeated failure is observed during work (agent or user)
  - running or interpreting `lazy retro feedback|report|resolve`
  - deciding whether a repeated failure pattern should become a record/policy/capability
  - harvesting user vocabulary for ADR 0053 surface-term seeding
- Aliases:
  - 회고 루프
  - retro loop
  - 피드백 루프
  - feedback loop
  - 실패 패턴
  - failure pattern
  - KPT
  - dogfood 피드백
- Must:
  - capture real-use failures/divergences as classified feedback (L1 implementation / L2 design / L3 spec) with a deterministic `kind` signature — instead of letting them evaporate in chat
  - treat 3+ entries of the same `kind` as a PATTERN CANDIDATE that the agent must surface to the user through an option gate
  - promote candidates only after user approval (to record/policy/capability), then `retro resolve` the entries with the resolution
  - store harvested user vocabulary in feedback entries; seed it as surface terms (ADR 0053) through the same gated flow
- Must not:
  - let the CLI decide promotion, importance, risk, or next actions (cli-tool-boundary; deterministic aggregation only)
  - auto-apply improvements without user approval (TimSquad improve principle)
  - use semantic scoring/matching for pattern detection (identical-signature counting only, ADR 0024 §2)
- Record completion:
  - changes to feedback schema, pattern threshold, or promotion flow update this SDD, the script, dispatcher, and `.lazy-harness/planning/memory-device-implementation-plan.md`
- Related records:
  - `.lazy-harness/decisions/0053-memory-device-storage-discipline.md`
  - `.lazy-harness/planning/memory-device-implementation-plan.md`

## Purpose

Closes the "improves with real use" identity gap (W4, memory-device plan): real-project divergences get captured, repeated failures become visible patterns, and confirmed patterns harden into records/policies — the dogfood feedback cycle built INTO the harness (user-ratified requirement, 2026-07-04).

## CLI contract

```bash
lazy retro feedback --level 1|2|3 --kind <lowercase-hyphen-signature> --message <text> [--vocab a,b] [--refs p1,p2] [--source agent|user]
lazy retro report [--format=json|md] [--dry-run]
lazy retro resolve --id <fb-id> --resolution <text>
```

- Storage: `.lazy-harness/retrospective/feedback.jsonl` (append-only entries; resolve rewrites status/resolution in place).
- Entry schema: `id`, `ts`, `level` (1|2|3), `kind`, `message`, `vocab[]`, `refs[]`, `source` (agent|user), `status` (open|resolved), `resolution`.
- Report: KPT markdown (Keep=resolved, Problem=open, Try=pattern candidates) + `vocabHarvest`; writes `retrospective/retro-<date>.md` unless `--dry-run`; `--format=json` for machine reads.
- Pattern rule: identical `kind` count ≥ 3 (deterministic; no fuzzy grouping). Level mix and harvested vocab are reported per pattern.
- Exit codes: 0 success; 1 missing root/id; 2 usage error.

## Promotion flow (agent + user, not CLI)

1. `lazy retro report` surfaces pattern candidates.
2. Agent presents an option gate (promote to which layer / defer / drop) — never self-selects.
3. On approval: write/update the canonical record (record-write-update-policy decision tree), seed harvested vocab as surface terms, then `lazy retro resolve` each entry citing the promotion.
4. Effect is measured at the next report (kind stops accumulating = fixed).

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/scripts/retro.ts` — feedback/report/resolve CLI.
  - `.lazy-harness/bin/lazy` — `retro` dispatcher.
  - `.lazy-harness/retrospective/feedback.jsonl` — feedback store.
  - `.lazy-harness/spec/platform/retro-loop.md` — this contract.
- Key symbols:
  - `cmdFeedback` / `cmdReport` / `cmdResolve` (`retro.ts`).
- Tests / protection:
  - self-test checks: candidate (batch with next commit-gate slice; validation currently by direct CLI runs recorded in the plan's W4 result).
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0053-memory-device-storage-discipline.md`
  - Planning: `.lazy-harness/planning/memory-device-implementation-plan.md`
- Machine index:
  - graph ids: `kg_retro_loop_cli_20260704`

## Rule placement

- Rule: real-use failures are captured as classified, signature-keyed feedback; 3-repeat patterns surface via option gate and only user approval promotes them; vocabulary harvest feeds surface-term seeding.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/retro-loop.md`
- Why not AGENTS.md: platform contract; grammar may later gain a one-line pointer (prompt-budget-sensitive, deferred).
- Confirmation: user-approved W4 execution 2026-07-04.

## Discovery capture

- DDD: none new (loop vocabulary already in holistic review).
- SDD: this contract.
- BDD: candidate — feedback-capture behavior scenario once the loop has real usage.
- TDD: candidate — self-test coverage for CLI schema/exit codes (next slice).
- ADR: none new; operates under ADR 0053/0016.
- SSOT: none.
- Planning: memory-device plan W4 result updated.
