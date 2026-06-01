# TDD — Context Broker Dogfood Collector

Status: accepted
Date: 2026-06-01
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/context-broker-dogfood.md`
Related SDD: `.lazy-harness/spec/platform/context-delivery-contract.md`
Related SDD: `.lazy-harness/spec/platform/record-decision-broker.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - changing `lazy context-dogfood`
  - changing Native Context Broker dogfood row fields or privacy behavior
  - changing dogfood collection before response.completed integration
- Must:
  - verify collector rows are sanitized and do not contain raw case messages
  - verify collector uses host-local `context-delivery` and `record-decision` CLIs
  - verify collection-only decisions are `no-record-needed`
  - verify markdown dry-run output works without writing collector JSONL
  - keep runtime hook integration out of this collector test
- Record completion:
  - changes to collector behavior, row shape, default cases, or privacy fields update this TDD and `.lazy-harness/spec/platform/context-broker-dogfood.md`

## Regression cases

1. **Sanitized JSON output**
   - Given a fixture host and case `reservation::예약시트 고쳐줘`.
   - Expected: JSON output contains `caseLabel=reservation`, a message hash, and no raw `예약시트 고쳐줘` string.

2. **Host-local context delivery**
   - Given fixture host records and source files.
   - Expected: collector invokes host-local `lazy context-delivery --journal` and reports `contextDelivery.ok=true`.

3. **Collection-only record decision**
   - Given a dogfood collection turn.
   - Expected: record decision disposition is `no-record-needed`, because the collector itself is validation/data collection, not durable record creation.

4. **Packet journal privacy check**
   - Given `context-delivery --journal` was called.
   - Expected: latest packet journal row has message hash and does not contain raw message.

5. **Markdown dry-run**
   - Given `--dry-run --format=md`.
   - Expected: markdown summary renders and collector output JSONL is not required.

## Current protection

- `.lazy-harness/scripts/self-test.py#check_context_broker_dogfood_collector`
  - creates a fixture host with `.lazy-harness/bin/lazy`, `context-delivery.ts`, `context-index.ts`, and `record-decision-broker.ts`,
  - runs the collector against that host,
  - validates JSON/JSONL privacy and `no-record-needed`,
  - validates markdown dry-run output.

## Implementation map

- Primary files:
  - `.lazy-harness/spec/platform/context-broker-dogfood.md` — contract under test.
  - `.lazy-harness/scripts/context-broker-dogfood.ts` — collector implementation.
  - `.lazy-harness/bin/lazy` — `context-dogfood` dispatcher.
  - `.lazy-harness/scripts/self-test.py` — fixture implementation.
- Related files:
  - `.lazy-harness/scripts/context-delivery.ts`
  - `.lazy-harness/scripts/record-decision-broker.ts`
  - `.gitignore`
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_context_broker_dogfood_collector`

## Layer completeness

- DDD: none.
- SDD: `.lazy-harness/spec/platform/context-broker-dogfood.md` defines the contract.
- BDD: none; no product UI behavior.
- TDD: this record and self-test protect the collector.
- ADR: ADR 0041 records the dogfood-before-hook-integration decision.
- SSOT: `.lazy-harness/ssot/rule-lifecycle.md` references explicit dogfood collection before response lifecycle escalation.

## Rule placement

- Rule: Context Broker dogfood collector must validate sanitized evidence and no-record-needed before hook integration.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/context-broker-dogfood.md`
- Why not AGENTS.md: this is a regression fixture contract, not base agent grammar.
- Why not `.jcode`: this is shared lazy-harness validation.
- Confirmation: user-confirmed option B.
