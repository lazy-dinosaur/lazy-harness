# Analysis Discovery Capture Gate

Status: accepted
Layer: SDD
Related ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
Related plan: `.lazy-harness/planning/analysis-discovery-capture-backlog.md`
Related graph spec: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`

## Purpose

Prevent substantial analysis/planning turns from leaving discovered DDD/SDD/BDD/TDD/ADR/SSOT facts or multi-step implementation plans only in chat history.

This gate complements the TDD layer-completeness gate. Layer completeness protects a record-writing path; analysis discovery capture protects the earlier analysis/planning path where the agent has not yet written records.

## Trigger

The gate applies when a response-completed payload strongly suggests that the agent performed non-trivial analysis/planning and mentioned multiple layer concepts or plan/backlog cues.

High-confidence cues include both:

1. Layer terms: at least three of `DDD`, `SDD`, `BDD`, `TDD`, `ADR`, `SSOT`, `Planning`, or their record directories.
2. Analysis/plan terms: `analysis`, `plan`, `planning`, `backlog`, `implementation plan`, `discovered`, `계획`, `분석`, `목차`, `코드분석`, or numbered multi-step work.

The helper should remain silent when the payload already shows record/candidate/planning capture.

## Completion contract

A triggered turn is complete only if at least one condition is true:

1. The same turn updates an affected layer record:
   - DDD: `.lazy-harness/domain/**`
   - SDD: `.lazy-harness/spec/**`
   - BDD: `.lazy-harness/behavior/**`
   - TDD: `.lazy-harness/tests/**`
   - ADR: `.lazy-harness/decisions/**`
   - SSOT: `.lazy-harness/ssot/**`
2. The same turn updates a planning artifact:
   - `.lazy-harness/planning/**`
3. The same turn updates a candidate/draft store:
   - `.lazy-harness/knowledge/candidates.jsonl`
   - `.lazy-harness/knowledge/graph-drafts.jsonl`
4. The response includes an explicit `Discovery capture` judgement naming DDD, SDD, BDD, TDD, ADR, SSOT, and Planning.
5. The agent stops and asks an option-gated question because layer ownership or plan scope is ambiguous.

## Required judgement

When facts are judged but not promoted to records yet, use:

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

If any item is `candidate`, append structured lines to `.lazy-harness/knowledge/candidates.jsonl` or create/update a `.lazy-harness/planning/` backlog. When multiple DDD/SDD/BDD/TDD/ADR/SSOT/Planning discoveries are present, capture each distinct candidate; do not satisfy the gate by recording only the first missing layer.

## Candidate queue behavior

Unconfirmed discoveries may be captured as `KnowledgeCandidate` records per `.lazy-harness/spec/platform/progressive-knowledge-graph.md`.

Minimum candidate fields for manual capture:

- `id`
- `createdAt`
- `source`
- `utterance`
- `detectedLayers`
- `candidateType`
- `status`
- `confidence`
- `graphDraftIds`
- `evidence`
- `questions`

Canonical promotion still requires explicit confirmation or a future validated safe rule.

Multi-candidate turns may also be represented by the Record Decision Broker MultiCandidate Packet (`recordDecision.recommendedRecords`) when the turn evidence is only safe paths/tool summaries. That packet is journal/advisory evidence, not canonical record mutation.

## Lifecycle helper behavior

`check-analysis-discovery-capture.sh` runs from `on-response-completed.sh`.

It emits STOP text when:

- high-confidence analysis/planning + layer cues are detected,
- no DDD/SDD/BDD/TDD/ADR/SSOT/planning/candidate/draft file was touched,
- and the response does not contain a complete `Discovery capture` judgement.

The STOP options are:

- update affected layer records,
- append candidates or graph drafts,
- create/update planning backlog,
- add a local `Discovery capture` judgement,
- ask the user when ambiguous,
- or record an intentional skip in `.lazy-harness/logs/skipped.jsonl`.

## Examples

### Incomplete

A response says: "I analyzed the appointment redesign and found DDD/SDD/BDD/TDD/SSOT impacts. Plan: 1... 2... 3..." but touches no records or planning/candidate files.

### Complete with planning

The same analysis also creates `.lazy-harness/planning/appointment-redesign-backlog.md` with layer candidates and implementation map.

### Complete with judgement

The response includes a `Discovery capture` block naming all required layers and explaining `none` or `candidate` for each.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md` — this SDD operating standard.
  - `.lazy-harness/AGENTS.md` — concise grammar for ADR 0034.
  - `.lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh` — response-completed guard.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — invokes the helper.
  - `.lazy-harness/scripts/self-test.py` — protects helper behavior and AGENTS wording.
  - `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md` — architectural decision.
- Key symbols:
  - `check_analysis_discovery_capture_helper` (`.lazy-harness/scripts/self-test.py`) — validates block/pass cases.
  - `run_analysis_discovery_capture_helper` (`.lazy-harness/scripts/self-test.py`) — fixture runner.
  - `Discovery capture` judgement — completion signal.
- Flow:
  1. Agent performs non-trivial analysis/planning.
  2. Helper detects layer + plan cues from response-completed payload strings.
  3. Helper checks same-turn record/planning/candidate capture or explicit judgement.
  4. Missing capture injects STOP text into the next assistant turn.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
  - SDD: `.lazy-harness/spec/platform/layer-completeness-gate.md`
  - SSOT: `.lazy-harness/ssot/knowledge-graph-storage.md`
  - Planning: `.lazy-harness/planning/analysis-discovery-capture-backlog.md`
- Machine index:
  - graph ids: `kg_sdd_analysis_discovery_capture_gate`
  - generated index key: `pending until implementation-index generator exists`
