# ADR 0034 — Analysis Discovery and Plan Capture Gate

Status: proposed
Date: 2026-05-14

## Context

A host session can do substantial analysis, split work into headings, inspect code, and produce a plan, while discovering many facts that belong in DDD, SDD, BDD, TDD, ADR, or SSOT records.

The current framework has record-first search, user-correction convergence, implementation maps, and a TDD layer-completeness gate. However, those controls mostly fire when the agent is already writing a record or bug/regression note.

They do not sufficiently force capture when the agent is in an **analysis/planning pass** and discovers:

- new domain terms or business rules,
- component/API/contract changes,
- user-facing behavior scenarios,
- regression risks or protection cases,
- source-of-truth or ownership boundaries,
- architectural decisions/trade-offs,
- multi-step implementation plans or backlog items.

User feedback on 2026-05-14 clarified that the screenshot issue was not merely image/short-input ambiguity. The deeper failure was: the agent had analyzed a large upcoming project change, made a plan, and identified many likely DDD/SDD/TDD/BDD/SSOT items, but failed to persist them as records or planning artifacts.

## Decision

Adopt an **analysis discovery and plan capture gate**.

Whenever an agent performs non-trivial analysis/planning for a project change, before claiming completion or moving to implementation, it must either:

1. create/update the affected layer records and planning record, or
2. add explicit candidate entries for discovered knowledge that still needs confirmation, or
3. ask an option-gated question when layer ownership or plan scope is ambiguous.

The gate should cover both:

- **knowledge capture**: DDD/SDD/BDD/TDD/ADR/SSOT candidates discovered during analysis,
- **plan capture**: multi-step plans/backlogs generated during the session.

## Required judgement shape

A planning/analysis response or record should include a compact judgement like:

```md
## Discovery capture

- DDD: updated/candidate/none because ...
- SDD: updated/candidate/none because ...
- BDD: updated/candidate/none because ...
- TDD: updated/candidate/none because ...
- ADR: updated/candidate/none because ...
- SSOT: updated/candidate/none because ...
- Planning: updated/candidate/none because ...
```

If any item is `candidate`, it should be persisted in a safe queue such as `.lazy-harness/knowledge/candidates.jsonl` or a planning backlog record, not left only in chat.

## Proposed implementation

1. Extend `.lazy-harness/AGENTS.md` record-as-output grammar:
   - analysis/planning pass that discovers layer facts must end with discovery capture.
   - multi-step plan/backlog must be written to `.lazy-harness/planning/` unless intentionally transient.
2. Add SDD operating standard for the discovery capture gate.
3. Add lifecycle helper that detects likely analysis/planning completions without touched records:
   - cues: `plan`, `backlog`, `DDD`, `SDD`, `BDD`, `TDD`, `SSOT`, `ADR`, `discovered`, `implementation plan`, section headings, numbered multi-step plan.
   - if no DDD/SDD/BDD/TDD/ADR/SSOT/planning/candidate file changed, warn or stop depending on confidence.
4. Add self-test fixtures for:
   - analysis with discovered layers but no records → blocked,
   - analysis with discovery capture section → allowed,
   - analysis that writes candidate queue/planning record → allowed.

## Consequences

### Positive

- Prevents rich analysis from evaporating into chat history.
- Makes future agents aware of discovered domain/contract/behavior/test/SSOT facts.
- Turns implementation plans into durable backlog artifacts.
- Complements ADR 0033, which only protects TDD/regression completeness.

### Negative

- More turns will require small record/candidate writes.
- Hook detection can false-positive on casual discussion of plans.

### Mitigation

- Start as warning/recommendation for broad analysis cues.
- Escalate to stop only when explicit layer terms or multi-step backlog language appears and no record/candidate/planning artifact changed.
- Allow explicit `Discovery capture` judgement as a lightweight escape hatch.

## Implementation map

- Status: `planned`
- Primary files:
  - `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md` — this ADR.
  - `.lazy-harness/AGENTS.md` — planned concise grammar update.
  - `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md` — planned operating standard.
  - `.lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh` — planned lifecycle helper.
  - `.lazy-harness/scripts/self-test.py` — planned protection tests.
  - `.lazy-harness/planning/analysis-discovery-capture-backlog.md` — planned implementation backlog.
  - `.lazy-harness/knowledge/candidates.jsonl` — planned/candidate storage for unconfirmed discovered facts.
- Key symbols:
  - `check_analysis_discovery_capture_helper` (`.lazy-harness/scripts/self-test.py`) — planned test helper.
  - `Discovery capture` judgement — planned Markdown completion signal.
- Flow:
  1. Agent analyzes a non-trivial change and discovers layer facts or creates a multi-step plan.
  2. Agent writes affected records, candidate queue entries, or planning backlog.
  3. Lifecycle hook checks response/output and touched files.
  4. If analysis/planning facts were likely discovered but no capture happened, hook warns/stops.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0033-layer-completeness-gate.md`
  - ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
  - Plan: `.lazy-harness/planning/analysis-discovery-capture-backlog.md`
  - SDD: planned `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`
- Machine index:
  - graph ids: `kg_adr0034_decides_analysis_discovery_capture_gate`
  - generated index key: `pending until implementation-index generator exists`
