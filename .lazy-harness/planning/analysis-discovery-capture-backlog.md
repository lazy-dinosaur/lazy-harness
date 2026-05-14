# Analysis Discovery Capture Backlog

Status: proposed
Date: 2026-05-14
Related ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`

## Problem

During large change analysis, an agent may discover many DDD/SDD/BDD/TDD/ADR/SSOT facts and create a useful implementation plan, but leave both the discovered facts and the plan only in chat.

This breaks lazy-harness's record-as-output promise. Future agents cannot reliably recover the layer discoveries or the plan.

## Backlog

### 1. Grammar update

- Add an `Analysis discovery capture` rule to `.lazy-harness/AGENTS.md`.
- Trigger: non-trivial analysis/planning, code analysis with layer discoveries, multi-step plan/backlog generation.
- Required output: write affected records, write candidate queue entries, or include/persist `Discovery capture` judgement.

### 2. SDD standard

- Create `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`.
- Define trigger cues, required judgement shape, candidate queue behavior, warning vs stop thresholds.

### 3. Candidate queue

- Introduce `.lazy-harness/knowledge/candidates.jsonl` if absent.
- Store unconfirmed discovered layer facts before promotion to canonical records.
- Link candidates to graph drafts where possible.

### 4. Lifecycle helper

- Add `.lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh`.
- Detect high-confidence analysis/planning responses with no touched layer/planning/candidate records.
- Start as warning unless explicit layer terms and multi-step plan are present.

### 5. Self-tests

- Extend `.lazy-harness/scripts/self-test.py` with fixtures:
  - discovered DDD/SDD/BDD/TDD/ADR/SSOT terms + no records → fail/warn expected.
  - discovered terms + `Discovery capture` judgement → pass.
  - discovered terms + candidate/planning file touched → pass.

### 6. Manifests/sync

- Ensure new ADR/SDD/helper/candidate convention syncs to hosts via manifest if applicable.

## Acceptance criteria

- Agents cannot finish a high-confidence analysis/planning turn that mentions discovered layer facts and a plan without either records, candidates, or an explicit judgement.
- The planned change is protected by self-tests.
- `python3 .lazy-harness/scripts/self-test.py` passes.
- `python3 .lazy-harness/scripts/doctor.py --profile smoke` passes.

## Discovery capture

- DDD: candidate gate needed because analysis can discover domain terms/business rules.
- SDD: candidate gate needed because analysis can discover contracts/components/APIs.
- BDD: candidate gate needed because analysis can discover user-visible flows.
- TDD: candidate gate needed because analysis can discover regression risks/protection cases.
- ADR: updated `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`.
- SSOT: related `.lazy-harness/ssot/project-identity.md` confirms this repo is the framework source of truth.
- Planning: this backlog created.

## Implementation map

- Status: `planned`
- Primary files:
  - `.lazy-harness/planning/analysis-discovery-capture-backlog.md` — this backlog.
  - `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md` — design decision.
- Key symbols:
  - `Discovery capture` judgement — planned completion/capture signal.
- Flow:
  1. ADR defines framework direction.
  2. Backlog breaks it into grammar, spec, candidate queue, lifecycle helper, tests, and sync work.
  3. Implementation promotes this plan into code and validation.
- Tests / protection:
  - planned `self-test.py` fixtures.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
  - SSOT: `.lazy-harness/ssot/project-identity.md`
- Machine index:
  - graph ids: `kg_plan_analysis_discovery_capture_backlog`
  - generated index key: `pending until implementation-index generator exists`
