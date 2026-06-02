# TDD — Record Decision Broker

Status: accepted
Date: 2026-06-01
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/record-decision-broker.md`
Related schema: `.lazy-harness/schemas/record-decision-packet.schema.json`
Related plan: `.lazy-harness/planning/native-context-broker-implementation-plan.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - changing Record Decision Packet schema or broker behavior
  - adding post-turn record-decision audit/runtime behavior
  - changing false-positive handling for record-needed/no-record-needed lifecycle decisions
- Must:
  - cover `candidate-needed`, `no-record-needed`, and `option-gate-needed` packet shapes
  - run the explicit `record-decision-broker.ts` generator for core dispositions as the baseline for runtime integration
  - prove response.completed shadow integration journals sanitized observations while staying silent by default
  - prove clean/read-only/explanation turns can be represented as `no-record-needed`
  - prevent automatic record writes from packet inference alone
  - require concrete evidence before `candidate-needed` or stricter audit output
  - keep ambiguous layer/path cases in `option-gate-needed`, not mutation
- Record completion:
  - changes to Record Decision Broker schema, dispositions, evidence kinds, or runtime integration update this TDD record and `.lazy-harness/spec/platform/record-decision-broker.md`

## Regression cases

1. **Clean explanation turn**
   - Given: user asks for status or explanation, no new durable facts.
   - Expected packet: `disposition=no-record-needed`, `trigger=explanation-only` or `validation-only`, recommended action `none`.
   - Expected lifecycle behavior: silent.

2. **Confirmed new alias**
   - Given: user confirms a new alias/surface term such as `기능패널`.
   - Expected packet: `disposition=candidate-needed`, evidence includes `user-confirmation`, recommended BDD or candidate graph record.
   - Expected lifecycle behavior: candidate/option guidance, not blind canonical write.

3. **Ambiguous layer placement**
   - Given: evidence suggests a record may be needed, but DDD/SDD/BDD/TDD/ADR/SSOT placement is ambiguous.
   - Expected packet: `disposition=option-gate-needed`, recommended action `ask-option-gate`.
   - Expected lifecycle behavior: ask 3-5 options, no record mutation before user choice.

4. **Same-turn record update**
   - Given: implementation changed and matching `.lazy-harness` record/graph update is visible.
   - Expected packet: `disposition=record-updated`, evidence includes `changed-record`.
   - Expected lifecycle behavior: silent or concise confirmation, no extra advisory.

5. **Deferred by user**
   - Given: user explicitly says to pause/defer after current phase.
   - Expected packet: `disposition=deferred`, evidence includes user instruction and planning path.
   - Expected lifecycle behavior: stop at the requested boundary.

## Current protection

The generator and response shadow fixtures are now active.

- `.lazy-harness/scripts/self-test.py#check_record_decision_broker_phase8`
  - validates SDD presence and key language,
  - validates schema title, required top-level fields, dispositions, evidence kinds, triggers, and actions,
  - validates sample `candidate-needed`, `no-record-needed`, and `option-gate-needed` packet shapes.
  - runs `.lazy-harness/scripts/record-decision-broker.ts` for `no-record-needed`, `candidate-needed`, `option-gate-needed`, and `record-updated` cases.
- `.lazy-harness/scripts/self-test.py#check_record_decision_shadow_response_completed`
  - validates `response.completed` helper chain registration,
  - validates read-only turns stay silent and journal `no-record-needed`,
  - validates source edits stay silent by default while journaling `candidate-needed`,
  - validates explicit advisory mode emits `ADVISORY` text without blocking language,
  - validates ambiguous mutations journal `option-gate-needed` without raw user text,
  - validates same-turn record edits journal `record-updated` silently.

## Future protection

- Add HostApp/PWA dogfood fixture once enough packet evidence is collected.
- Add stricter response.completed advisory/escalation fixtures only after shadow rows prove low false-positive risk.

## Implementation map

- Primary files:
  - `.lazy-harness/spec/platform/record-decision-broker.md` — contract being tested.
  - `.lazy-harness/schemas/record-decision-packet.schema.json` — schema under test.
  - `.lazy-harness/scripts/record-decision-broker.ts` — explicit generator under test.
  - `.lazy-harness/hooks/lifecycle/helpers/check-record-decision-shadow.py` — response.completed shadow helper under test.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — helper chain registration under test.
  - `.lazy-harness/scripts/lifecycle-check.py` — orchestrator helper chain registration under test.
  - `.lazy-harness/bin/lazy` — exposes the generator as `lazy record-decision`.
  - `.lazy-harness/scripts/self-test.py` — current contract fixture.
  - `.lazy-harness/planning/native-context-broker-implementation-plan.md` — Phase 8 status.
- Future files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — future stricter packet consumer only after shadow fixtures and dogfood evidence.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_record_decision_broker_phase8`
  - `.lazy-harness/scripts/self-test.py#check_record_decision_shadow_response_completed`

## Layer completeness

- DDD: no domain entity change; examples are framework fixtures.
- SDD: `.lazy-harness/spec/platform/record-decision-broker.md` captures the contract and response shadow bridge.
- BDD: default visible behavior is still silent; optional advisory mode can surface candidate/option-gate guidance without blocking.
- TDD: this record and self-test protect the false-positive surface.
- ADR: ADR 0041 records Phase 8 as organic post-turn packet design.
- SSOT: `.lazy-harness/ssot/rule-lifecycle.md` references Record Decision Broker as advisory lifecycle stage.

## Rule placement

- Rule: Record Decision Broker tests must prove no-record-needed/option-gate/candidate cases before runtime escalation.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/record-decision-broker.md`
- Why not AGENTS.md: this is a regression fixture plan, not base operating grammar.
- Why not `.jcode`: this is shared lazy-harness framework validation.
- Confirmation: inferred from accepted Phase 8 SDD and user-confirmed continuation.
