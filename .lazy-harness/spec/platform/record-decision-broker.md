# SDD — Post-turn Record Decision Broker

Status: accepted
Date: 2026-06-01
Layer: SDD
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related SDD: `.lazy-harness/spec/platform/context-delivery-contract.md`
Related SDD: `.lazy-harness/spec/platform/response-rule-audit.md`
Related SDD: `.lazy-harness/spec/platform/record-write-update-policy.md`
Related TDD: `.lazy-harness/tests/record-decision-broker.md`
Related schema: `.lazy-harness/schemas/record-decision-packet.schema.json`
Related plan: `.lazy-harness/planning/native-context-broker-implementation-plan.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - designing or implementing post-turn record decision logic
  - deciding whether a completed turn needs record update, candidate capture, no-record-needed, or option gate
  - integrating Context Delivery packet evidence with record-completion audit
  - reducing false positives from broad “record needed” lifecycle gates
- Must:
  - output a structured Record Decision Packet before any automated record-write escalation
  - keep the explicit generator local and deterministic until response lifecycle integration has separate fixtures
  - support explicit `no-record-needed` for explanation/evaluation/inspection-only turns
  - require concrete turn evidence before `candidate-needed`, `record-updated`, or `option-gate-needed`
  - prefer updating existing canonical records before creating new records
  - keep packet output advisory/non-canonical until a user or explicit write path confirms a record update
  - avoid raw transcript storage; store paths, tool names, reasons, hashes, and compact evidence summaries only
  - keep clean turns silent in `response.completed` unless a later false-positive-safe fixture justifies advisory output
- Must not:
  - blindly write records from model inference alone
  - convert every edit into a record obligation
  - turn missing/ambiguous evidence into STOP output
  - bypass option-gate discipline when layer placement or user intent is ambiguous
- Record completion:
  - changes to Record Decision Packet shape, dispositions, evidence criteria, or broker/audit behavior update this SDD, schema, TDD record, ADR 0041, and the native context broker plan
- Related records:
  - `.lazy-harness/spec/platform/context-delivery-contract.md`
  - `.lazy-harness/spec/platform/response-rule-audit.md`
  - `.lazy-harness/spec/platform/record-write-update-policy.md`
  - `.lazy-harness/tests/record-decision-broker.md`

## Purpose

The Post-turn Record Decision Broker is the mirror image of Context Delivery.

Context Delivery answers:

```text
Before a turn, what context must the agent read?
```

Record Decision Broker answers:

```text
After a turn, what durable record action, if any, is justified by evidence?
```

Target flow:

```text
turn evidence
→ normalized record signals
→ Record Decision Packet
→ record update / candidate capture / no-record-needed / option gate
```

Phase 8 was the contract phase. The first generator phase adds an explicit local CLI that emits packet-shaped output from supplied evidence flags. It still does not add broad blocking and does not blindly write records. In short: no automatic blind record writes.

Generator command:

```bash
.lazy-harness/bin/lazy record-decision --message "상태 요약" --read-only --format=md
```

The generator is explicit/offline only: it does not run from `response.completed`, does not mutate records, and does not write journals.

## Packet shape

Record Decision Packet top-level shape:

```json
{
  "schemaVersion": "1.0",
  "generatedAt": "2026-06-01T00:00:00.000Z",
  "recordDecision": {
    "disposition": "candidate-needed",
    "confidence": 0.74,
    "trigger": "new-alias-found",
    "summary": "User confirmed a new surface alias that is not yet represented in records.",
    "evidence": [
      {
        "kind": "user-confirmation",
        "summary": "User confirmed 예약시트 means reservation sheet.",
        "confidence": 0.9
      },
      {
        "kind": "changed-file",
        "path": "src/features/reservations/ReservationTable.tsx",
        "summary": "Reservation table behavior was modified.",
        "confidence": 0.8
      }
    ],
    "recommendedRecords": [
      {
        "path": ".lazy-harness/behavior/reservation-management.md",
        "layer": "BDD",
        "action": "update",
        "reason": "UI flow or alias changed.",
        "confidence": 0.82
      },
      {
        "path": ".lazy-harness/knowledge/candidates.jsonl",
        "action": "append",
        "reason": "If canonical layer is not yet confirmed, capture as a candidate.",
        "confidence": 0.7
      }
    ],
    "instructions": [
      "Ask an option gate if the canonical layer is ambiguous.",
      "Do not write automatically from this packet alone."
    ]
  }
}
```

## Dispositions

| Disposition | Meaning | Allowed next action |
|---|---|---|
| `record-updated` | A durable canonical record or graph row was already updated in this turn. | Audit may stay silent or cite the record path. |
| `candidate-needed` | Evidence suggests durable capture is needed, but no confirmed canonical update exists yet. | Append candidate or ask user before canonical write. |
| `no-record-needed` | Turn was explanation, inspection, validation-only, or otherwise produced no durable project knowledge. | Stay silent. |
| `option-gate-needed` | Evidence indicates capture may be needed, but layer/path/meaning is ambiguous. | Ask 3-5 options with Recommended marker. |
| `deferred` | Evidence exists but is intentionally deferred by user instruction or pending validation. | Record backlog/planning pointer, no STOP. |

## Evidence kinds

Allowed evidence kinds:

- `user-confirmation`
- `user-correction`
- `changed-file`
- `changed-record`
- `changed-test`
- `context-delivery-required-read`
- `response-audit-advisory`
- `tool-call`
- `validation`
- `no-op`

Evidence must be compact and attributable. It may include paths and tool names. It must not include raw full transcript bodies.

## Recommended record actions

Allowed actions:

- `update`
- `create`
- `append`
- `candidate`
- `none`
- `ask-option-gate`

Rules:

1. Prefer `update` over `create` when an existing canonical record maps to the same layer/topic.
2. Use `candidate`/`.lazy-harness/knowledge/candidates.jsonl` when evidence is useful but canonical layer or wording is not confirmed.
3. Use `ask-option-gate` when DDD/SDD/BDD/TDD/ADR/SSOT placement is ambiguous.
4. Use `none` only with `no-record-needed` or when a record was already updated elsewhere.

## False-positive policy

The broker must explicitly model no-record-needed outcomes.

Examples that should produce `no-record-needed`:

- user asks for a status summary with no new facts,
- read-only investigation finds no new durable host knowledge,
- validation reruns only confirm already-recorded behavior,
- transient execution details with no reusable rule, contract, scenario, or decision.

Examples that may produce `candidate-needed` or `option-gate-needed`:

- user confirms a new alias or domain term,
- user corrects source-of-truth/ownership/project identity,
- implementation changes a mapped SDD/BDD/TDD area without matching record update,
- response audit advisory repeats across dogfood turns with concrete evidence.

## Relationship to response audit

Phase 8 does not replace `response-rule-audit.md`.

- Response Rule Audit detects narrow miss patterns and advisory evidence.
- Record Decision Broker normalizes the broader post-turn question: “what record action is justified?”
- Future `response.completed` integration may consume Record Decision Packets, but only after fixtures prove clean turns stay silent.

Initial integration is schema/test only. Runtime output remains unchanged.

## Relationship to Context Delivery

Record Decision Broker may consume Context Delivery evidence:

- `requiredRead` paths that were read before changes,
- packet confidence,
- candidate meanings and resolved aliases,
- packet evidence journal rows from `.lazy-harness/state/context-delivery-packets.jsonl`.

Context Delivery is pre-turn required-read. Record Decision Broker is post-turn record-write decision.

## Privacy and retention

- Packet is non-canonical unless written into a canonical record by an explicit path.
- Journaled packet rows, if added later, must be under `.lazy-harness/state/` and ignored by git.
- Packet evidence must not store raw full prompts, raw assistant responses, API keys, secrets, or full transcripts.
- Safe fields: record paths, source paths, layer labels, tool names, short hashes, compact summaries, confidence, disposition, action names.

## Implementation map

- Status: `generator-implemented`
- Primary files:
  - `.lazy-harness/spec/platform/record-decision-broker.md` - this SDD and post-turn packet contract.
  - `.lazy-harness/schemas/record-decision-packet.schema.json` - JSON Schema for packet-shaped outputs.
  - `.lazy-harness/scripts/record-decision-broker.ts` - deterministic explicit CLI generator from safe evidence flags to Record Decision Packet.
  - `.lazy-harness/bin/lazy` - exposes `lazy record-decision` against the current host root.
  - `.lazy-harness/tests/record-decision-broker.md` - false-positive and disposition fixture plan.
  - `.lazy-harness/scripts/self-test.py` - schema/document fixture validation.
  - `.lazy-harness/planning/native-context-broker-implementation-plan.md` - Phase 8 roadmap status.
  - `.lazy-harness/knowledge/graph.jsonl` - graph rows linking contract, schema, plan, and tests.
- Future implementation files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` - future consumer only after false-positive fixtures.
- Flow:
  1. Turn completes.
  2. Explicit generator normalizes supplied user confirmations, corrections, changed files, changed records, Context Delivery evidence, and validation evidence.
  3. Broker emits Record Decision Packet.
  4. If `record-updated`, audit can stay silent.
  5. If `candidate-needed`, future tooling may append `.lazy-harness/knowledge/candidates.jsonl` or ask before canonical write.
  6. If `option-gate-needed`, agent asks options before mutating records.
  7. If `no-record-needed`, response lifecycle stays silent.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_record_decision_broker_phase8`
    - validates schema/contract and generator output for `no-record-needed`, `candidate-needed`, `option-gate-needed`, and `record-updated`.

## Validation plan

Minimum Phase 8 validation:

- SDD includes `## Rule digest`.
- JSON schema loads as valid JSON.
- Schema includes all dispositions and evidence kinds.
- Sample `candidate-needed`, `no-record-needed`, and `option-gate-needed` packets satisfy required field expectations.
- Generator fixture emits expected `no-record-needed`, `candidate-needed`, `option-gate-needed`, and `record-updated` dispositions.
- TDD record covers false-positive clean-turn behavior.
- Manifest syncs this SDD to downstream hosts.

Future validation:

- Fixture: read-only status turn returns `no-record-needed`.
- Fixture: confirmed new alias returns `candidate-needed` with BDD/graph recommendations.
- Fixture: ambiguous layer returns `option-gate-needed` and no mutation.
- Fixture: same-turn record update returns `record-updated` and no audit output.
- Fixture: repeated advisory with concrete evidence can produce candidate, not STOP.

## Rule placement

- Rule: Post-turn record decisions must use a structured packet with explicit no-record-needed/candidate/option-gate dispositions before any automated record-write escalation.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/record-decision-broker.md`
- Why not AGENTS.md: this is a platform packet contract and lifecycle design, not compact base grammar.
- Why not `.jcode`: this must sync to hosts and be shared by lazy-harness scripts, hooks, records, and optional future brokers.
- Confirmation: user-confirmed by resuming Native Context Broker work after Phase 7 pause.

## Discovery capture

- DDD: no domain entity added; examples use reservation aliases only as framework fixtures.
- SDD: this record defines the Phase 8 post-turn broker contract.
- BDD: agent-visible behavior is future lifecycle guidance: clean turns stay silent; ambiguous record placement asks option gate.
- TDD: `.lazy-harness/tests/record-decision-broker.md` and self-test fixture protect the contract.
- ADR: ADR 0041 receives a Phase 8 implementation note.
- SSOT: rule lifecycle notes should reference Record Decision Broker as post-turn advisory packet, not hard-stop promotion.
- Planning: native context broker plan marks Phase 8 contract complete when committed.
