# TDD — Guidance Ladder Hard-stop Promotion

Status: accepted
Layer: TDD
Date: 2026-06-01
Related SDD: `.lazy-harness/spec/platform/guidance-ladder.md`
Related SSOT: `.lazy-harness/ssot/rule-lifecycle.md`
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - 사다리 승격 회귀
  - hard stop 승격 테스트
- Applies when:
  - promoting a rule to a hard-stop or blocking hook, or auditing hard-stop promotion records
  - deciding whether softer guidance layers were insufficient before blocking
- Must:
  - treat hard stops as last-rung behavior; promoted hard stops carry a complete `## Hard-stop promotion` section (status, boundary, scope, confirmation, evidence, softer coverage, fixture, narrowness, rollback)
  - strict audit must fail invalid promotion records and pass valid ones only when the fixture path exists
- Must not:
  - add a blocking hook the moment a rule exists, without proof softer layers were insufficient
  - conflate generic destructive-shell safety with project/team hard-stop promotion
- Record completion:
  - changes to promotion criteria or the audit checker update this TDD plus the guidance-ladder SDD and rule-lifecycle SSOT
- Related records:
  - `.lazy-harness/spec/platform/guidance-ladder.md`
  - `.lazy-harness/ssot/rule-lifecycle.md`
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`

## Regression class

Lazy-harness must not regress from organic guidance back into broad or tool-attached hard blocks.

The failure mode is:

```text
A rule exists → framework immediately adds a blocking hook
```

without proof that softer layers were insufficient.

## Protected behavior

Phase 6 protection requires:

1. Hard stops are last-rung behavior, not default behavior.
2. A promoted hard stop must have a canonical `## Hard-stop promotion` section.
3. Active/proposed promotions must document:
   - status,
   - exact boundary,
   - scope,
   - user confirmation,
   - miss/risk evidence,
   - existing softer coverage or why it is insufficient,
   - existing fixture path,
   - narrowness rationale,
   - rollback path.
4. The audit checker fails invalid promotion records in strict mode.
5. Valid promotion records pass only when the fixture path exists.
6. Source tree scan passes when no invalid promotions exist.
7. Generic destructive shell safety remains separate from project/team hard-stop promotion.

## Fixtures

`check_guidance_ladder_hard_stop_promotion` creates temporary records:

- invalid active promotion missing required fields and fixture path → strict audit fails,
- valid active promotion with all fields and an existing fixture file → strict audit passes,
- source scan → strict audit passes for committed lazy-harness records.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/guidance-ladder.md` — SDD contract.
  - `.lazy-harness/scripts/hard-stop-promotion-audit.py` — audit checker.
  - `.lazy-harness/scripts/self-test.py` — fixture runner.
  - `.lazy-harness/ssot/rule-lifecycle.md` — lifecycle SSOT links Phase 6 promotion.
- Key symbols:
  - `extract_sections` (`hard-stop-promotion-audit.py`) — finds promotion sections outside code fences.
  - `validate_section` (`hard-stop-promotion-audit.py`) — checks field completeness, allowed scope, and fixture existence.
  - `check_guidance_ladder_hard_stop_promotion` (`self-test.py`) — protects Phase 6 criteria.
- Flow:
  1. A record proposes or activates a hard stop.
  2. The record includes `## Hard-stop promotion` metadata.
  3. Audit checker validates required evidence and fixture path.
  4. Self-test protects invalid and valid cases.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_guidance_ladder_hard_stop_promotion`
  - `python3 .lazy-harness/scripts/hard-stop-promotion-audit.py --strict`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/guidance-ladder.md`
  - SSOT: `.lazy-harness/ssot/rule-lifecycle.md`
  - ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
- Machine index:
  - graph ids: `kg_phase6_guidance_ladder_tdd`, `kg_phase6_guidance_ladder_self_test`

## Layer completeness

- DDD: no domain vocabulary change.
- SDD: `.lazy-harness/spec/platform/guidance-ladder.md` added.
- BDD: no app UI flow change; agent behavior remains surfaced/audited by default.
- TDD: this record plus self-test fixture.
- ADR: ADR 0041 updated with Phase 6 note.
- SSOT: rule lifecycle and harness enforcement policy updated.

## Discovery capture

- Planning: Phase 6 outputs and validation status are captured in `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`.
- Candidate: Project Profile pre-response bootstrap remains a later weakness candidate in `.lazy-harness/knowledge/candidates.jsonl`, not a Phase 6 plan change.
