# Planning — Retro-Loop-First Development Path (Proposal)

Status: absorbed (2026-07-04) — Phase 1 lives on as W4 of `.lazy-harness/planning/memory-device-implementation-plan.md`; do not execute from this record
Date: 2026-07-04
Layer: Planning
Source: 2026-07-04 harness deep-dive discussion; user asked "어떤식으로 발전시키는게 최적?" and requested the full plan before choosing
Related planning: `.lazy-harness/planning/current-framework-roadmap-snapshot.md`, `.lazy-harness/planning/competitive-evaluation-and-positioning-2026-06.md`, `.lazy-harness/planning/external-agent-harness-reference.md`
Related candidates: `candidate-harness-deep-dive-adoption-shortlist-20260704`, `candidate-flexibility-improvement-identity-proof-path-20260704` (`.lazy-harness/knowledge/candidates.jsonl`)
Related ADR: `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`, `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`

## User-ratified requirement (2026-07-04)

The user confirmed the WHY of this plan (requirement framing only — NOT execution approval, per ADR 0038):

- lazy-harness is a PRODUCT; dogfooding exists so that real-project use surfaces cases that diverge from intent or work poorly, those get confirmed with the user, and the harness improves from them — and that feedback mechanism must be built INTO the harness itself (retro loop = product requirement, not an add-on).
- Current-state assessment confirmed with evidence: information ACCUMULATION works well (229 records / 656 graph rows / 52 ADRs, record-lint 160/160 clean, same-session correction convergence). USAGE is only half-proven: map-first retrieval and 77% token saving are real, but this very session produced a dogfood finding — the first-pass research summary missed TimSquad (scattered across plans/, candidates.jsonl, ADR mentions) until the user's memory corrected it; measured evidence remains post-hoc (guard emissions ≠ prevented violations, R1 unmeasured). Findings of this class are exactly what `lazy retro feedback` must capture instead of dissolving in chat.

## Why this ordering (keystone argument)

Roadmap snapshot (2026-05-26) constrains: (1) pause new hard guards; next period = dogfooding + evidence collection; stronger policy only after a repeated failure is proven; (2) long-term goal = automatic capability confirmation/promotion (collect evidence → infer → score → promote). A retro learning loop IS that mechanism, and serves triple duty:

1. Completes the "improves with use" half of the identity claim (missing failure-pattern→rule-reinforcement cycle, confirmed by 2026-07-04 source-level deep dive).
2. Provides the "repeated failure proven" evidence that any future hard gate (e.g. Stop-deny) requires — hard-gate decisions become evidence-driven instead of taste-driven.
3. Generates the data R1 (memory-gain vs friction A/B) needs.

Therefore Stop-deny/lint/measurement are sequenced AFTER the loop, gated on its evidence.

## Phase 0 — Decision + records (0.5d, no code)

- New ADR: adopt retro learning loop, organic style — promotion always via user option gate, no auto-apply (TimSquad improve principle), not a hard gate (roadmap pause respected).
- New planning record: retro-loop implementation plan (supersedes/absorbs this proposal).
- Promote candidates: deep-dive shortlist item (1) + proof-path candidate → converge into the ADR/plan (`promoted-to-record`).

## Phase 1 — Retro loop MVP: evidence engine (1–2 weeks)

Reuse (no new infra): data sources `state/validations.jsonl`, hook-timings (10,268 turns), `logs/skipped.jsonl`, `questions/open.xml`, `candidates.jsonl`; storage `.lazy-harness/retrospective/` (exists: audits/, metrics/); promotion targets `ssot/policies.json` + `capabilities.json` + record layers.

New (exactly 3 pieces, small-core):

1. `lazy retro feedback` — L1(impl)/L2(design)/L3(spec) classified append to `retrospective/feedback.jsonl` (user or AI).
2. `lazy retro report` — read-only aggregation: KPT report + pattern detection = identical failure signature 3+ occurrences (deterministic matching only; ADR 0024 §2 no custom search algorithms) → `retrospective/retro-<date>.md`.
3. Promotion flow — detected FP/SP patterns presented via option gate → on approval promote to record/policy/capability + candidates history.

Validation criteria: self-test schema/CLI checks pass via `lazy test`; first KPT report from real data; E2E one pattern promoted through option gate to a record; evidence capsule recorded.

## Phase 2 — R4 heterogeneous host proof (parallel with Phase 1, 2–4 calendar weeks)

- USER DECISION REQUIRED: pick 1–2 heterogeneous-stack projects.
- `lazy init` → daily use → loop accumulates per-host evidence.
- Done when: per-host record growth + first loop report outside Medivance.

## Phase 3 — Evidence-gated follow-ups (each behind its own option gate, order unfixed)

| Follow-up | Trigger evidence | Work |
|---|---|---|
| Stop-deny gate | retro detects repeated "completion declared without validation" pattern | narrow ADR 0016 amendment → response.completed promoted to deny-capable |
| Contradiction lint | real record-vs-record contradiction found | record-lint cross-record checks (gentle-pi guardrails class) |
| Conditional triggers | friction complaints / path-risk patterns | capability trigger conditions path×diff×phase (R3) |
| R1 A/B measurement | sufficient loop data | measurement design → results into competitive-evaluation record |

## Risks / invariants

- Scope creep → Phase 1 fixed at 2 CLIs + 1 flow; no daemon/automation.
- Auto-promotion runaway → none: every promotion user-gated (roadmap auto-promotion stays long-term).
- Unchanged: dev-time advisory (ADR 0016), LLM-as-semantic-authority (ADR 0024), record-first; no TimSquad code ports (structure reference only); no new external deps (ADR 0013).

## Alternatives presented (not chosen; gate returned no input)

A. Loop-first (recommended, this plan) / B. Proof-first (R4+R1 before loop; weakness: measuring with thin data) / C. Cheap-detection-first (P2 lint+triggers; weakness: identity gap stays) / D. Stop-deny-first (conflicts with roadmap hard-guard pause; needs ADR 0016 amendment first).

## Discovery capture

- DDD: none.
- SDD: none yet; Phase 1 CLI contracts would need an SDD when approved.
- BDD: none.
- TDD: none yet; Phase 1 validation criteria become TDD records when approved.
- ADR: candidate — Phase 0 proposes a retro-loop ADR; not written (approval pending).
- SSOT: none.
- Planning: updated — this record (incl. 2026-07-04 user-ratified requirement + current-state assessment).

## Rule placement

- Not applicable yet: no user-confirmed rule; this is an unapproved proposal. Confirmation: pending (option gate returned no input, 2026-07-04).
