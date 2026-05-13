# Progressive Knowledge Graph Pipeline Plan

Date: 2026-05-13
Status: proposed
Purpose: make lazy-harness improve as it is used by turning conversation, code discoveries, bug fixes, and user corrections into a durable, queryable, correctable knowledge graph across DDD/SDD/BDD/TDD/ADR/SSOT.

## 1. North star

The development environment should get better every time it is used.

```text
conversation / implementation / debug / correction
→ detect reusable knowledge
→ capture as candidate
→ classify into graph layer(s)
→ verify against existing graph + code evidence
→ ask when ambiguous or conflicting
→ confirm / correct / reject
→ promote to canonical graph
→ project human-readable DDD/SDD/BDD/TDD/ADR/SSOT views
→ future agents retrieve it before work
→ validation graph protects it
```

## 2. Core principle

Do not silently auto-confirm knowledge.

Allowed automatically:

- detect candidate facts
- store raw candidate records
- attach source/evidence references
- detect conflicts with existing graph records
- propose graph drafts
- ask structured A/B/C/D questions
- mark stale/superseded candidates after confirmation

Not allowed automatically:

- overwrite confirmed facts
- promote ambiguous facts to canonical graph
- choose one primary layer when multiple layers are plausible
- rewrite human-facing DDD/SDD/BDD/TDD/ADR/SSOT docs without confirmation

## 3. Storage model

### 3.1 Candidate queue

Append-only, captures what was said or discovered before it is trusted.

```text
.lazy-harness/knowledge/candidates.jsonl
```

Shape:

```json
{
  "id": "ki_20260513_001",
  "createdAt": "2026-05-13T15:10:00Z",
  "source": "conversation|code|test|user-correction|hook",
  "utterance": "채팅 메시지에서 PC 기준은 deviceId/pcLocationId...",
  "detectedLayers": ["ddd", "sdd"],
  "candidateType": "domain-term|business-invariant|contract-source|user-behavior|regression-fact|decision-tradeoff|source-of-truth|ambiguous-knowledge",
  "status": "needs-confirmation|confirmed|rejected|superseded",
  "confidence": "high|medium|low|ambiguous",
  "graphDraftIds": ["kgd_chat_message_identity_pc"],
  "evidence": [],
  "questions": []
}
```

### 3.2 Graph draft queue

Machine-readable candidate graph records. These may be created automatically but are not canonical until confirmed.

```text
.lazy-harness/knowledge/graph-drafts.jsonl
```

Shape:

```json
{
  "id": "kgd_chat_message_identity_pc",
  "candidateId": "ki_20260513_001",
  "layer": "ddd",
  "kind": "claim",
  "subject": "ChatMessage",
  "predicate": "has_pc_identity_fields",
  "object": ["deviceId", "pcLocationId"],
  "status": "needs-confirmation",
  "confidence": "candidate",
  "evidence": [
    { "type": "code", "path": "prisma/schema/chat.prisma", "lines": [54, 75] }
  ],
  "links": [
    { "rel": "specified_by", "target": "sdd.chat-message-contract" },
    { "rel": "validated_by", "target": "tdd.chat-message-identity" }
  ],
  "conflicts": []
}
```

### 3.3 Canonical graph

Confirmed, queryable knowledge backbone.

```text
.lazy-harness/knowledge/graph.jsonl
```

Canonical graph records must have:

- stable id
- layer
- subject
- predicate
- object
- status
- evidence
- provenance
- updatedAt

Statuses:

```text
confirmed
superseded
rejected
stale
needs-review
```

### 3.4 Human-facing projections

DDD/SDD/BDD/TDD/ADR/SSOT documents remain the human-readable projection of graph knowledge.

```text
.lazy-harness/domain/**
.lazy-harness/spec/**
.lazy-harness/behavior/**
.lazy-harness/tests/**
.lazy-harness/decisions/**
.lazy-harness/ssot/**
```

Rule:

```text
graph = machine backbone
layer docs = human view / canonical explanation
```

## 4. Layer graph model

All layers become graph node/edge types.

| Layer | Node kinds | Common predicates | Common edges |
|---|---|---|---|
| DDD | term, entity, invariant, business-rule | means, has_identity_field, forbids, requires | specified_by, validated_by, decided_by |
| SDD | api, schema, ipc, contract, component-interface | accepts, returns, derives_from, source_is | implements, validates, depends_on |
| BDD | scenario, actor, user-flow, acceptance | sees, can_do, must_happen_before | exercises, validates, protects |
| TDD | regression, test, fixture, protection | protects, reproduces, fails_when | validates, guards, covers |
| ADR | decision, tradeoff, policy | chooses, rejects, supersedes, rationale | explains, constrains, supersedes |
| SSOT | config, env, generated-source, registry | source_of_truth_for, owns, generates | feeds, constrains, invalidates |

## 5. Automatic add/correct behavior

### 5.1 No existing graph record

```text
candidate detected
→ graph draft generated
→ status=needs-confirmation
→ structured ask generated
→ on confirmation: append to graph.jsonl
→ optionally project to layer docs
```

### 5.2 Existing matching graph record

```text
candidate detected
→ match subject/predicate/object
→ attach evidence/provenance if new
→ no new ask unless it changes meaning
```

### 5.3 Existing conflicting graph record

```text
candidate detected
→ match subject/predicate but object differs
→ create conflict record
→ ask user:
   A) existing graph is correct
   B) new candidate supersedes existing
   C) both are true under conditions
   D) reject/defer
   custom) type your own
```

If superseded:

- old graph record status becomes `superseded`
- new graph record status becomes `confirmed`
- edge added: `{ "rel": "supersedes", "target": "old_id" }`

### 5.4 Code contradicts graph

```text
source inspection / validation finds contradiction
→ create conflict candidate with code evidence
→ mark existing graph as needs-review, not overwritten
→ ask user or require ADR/SSOT confirmation when policy-level
```

## 6. CLI surface

Initial commands:

```bash
lazy intake --text "..." --plan
lazy intake --text "..." --capture
lazy intake --candidate ki_x --confirm --as ddd
lazy intake --candidate ki_x --reject --reason "..."
lazy graph query --subject ChatMessage
lazy graph query --layer ddd --predicate has_identity_field
lazy graph conflicts
lazy graph promote kg_x --to domain/chat.md
```

Implementation can live first in:

```text
.lazy-harness/scripts/knowledge-intake.ts
.lazy-harness/scripts/knowledge-graph.ts
```

Then expose through:

```text
.lazy-harness/bin/lazy intake
.lazy-harness/bin/lazy graph
```

## 7. Retrieval behavior

Before work, agent should prefer M45 private instructions to know the rule:

```text
consult graph + records before source guessing
```

Retrieval path:

```text
user request / changed file
→ query knowledge graph by subject/token/layer
→ include top confirmed graph records with citations
→ include unresolved candidates only if directly related
→ then inspect source if needed
```

The graph query result should be compact:

```text
[lazy-harness graph]
1. DDD confirmed: ChatMessage has pc identity fields deviceId/pcLocationId
   evidence: prisma/schema/chat.prisma:54-75
2. SDD confirmed: chat.getRooms omits ignored deviceId in logged-in mode
   evidence: decisions/2026-05-13-chat-cpu-safe-optimization.md
```

## 8. Validation behavior

Validation graph consumes canonical graph records.

Examples:

- If DDD invariant changes, require matching BDD/TDD coverage.
- If SDD contract changes, require spec or contract-diff evidence.
- If TDD regression exists without protectedBy, fail smoke/full validation.
- If SSOT record changes, require generated/source consumers to be checked.
- If graph conflict exists with status `needs-review`, validation warns or blocks depending on severity.

## 9. Implementation stages

### Stage KG-0 — Schema and directories

Deliverables:

- `.lazy-harness/knowledge/README.md`
- `.lazy-harness/knowledge/candidates.jsonl`
- `.lazy-harness/knowledge/graph-drafts.jsonl`
- `.lazy-harness/knowledge/graph.jsonl`
- `.lazy-harness/schemas/knowledge-candidate.schema.json`
- `.lazy-harness/schemas/knowledge-graph-record.schema.json`

Validation:

- JSONL parse
- schema metadata check
- empty container tolerance

### Stage KG-1 — Capture candidates

Extend `knowledge-intake.ts`:

```bash
bun .lazy-harness/scripts/knowledge-intake.ts --text "..." --capture
```

Behavior:

- append candidate to `knowledge/candidates.jsonl`
- generate graph draft to `knowledge/graph-drafts.jsonl`
- do not touch `graph.jsonl`

Validation:

- `--plan` writes nothing
- `--capture` appends exactly one candidate batch
- duplicate candidate dedupes by stable hash

### Stage KG-2 — Confirm/reject candidates

Extend CLI:

```bash
knowledge-intake.ts --candidate <id> --confirm --answer A
knowledge-intake.ts --candidate <id> --reject --reason "..."
```

Behavior:

- confirmed draft moves/appends into `graph.jsonl`
- candidate status updates through append-only event or status record
- rejected candidate is retained with reason

Validation:

- confirmed graph record is queryable
- rejected candidate does not appear in confirmed graph query

### Stage KG-3 — Conflict detection

Add graph matching:

```text
subject + predicate match, object differs → conflict
```

Deliverables:

- conflict entry in candidate/draft
- structured ask with A/B/C/D/custom

Validation fixtures:

- existing `ChatMessage has_pc_identity_fields = [deviceId]`
- new candidate `[deviceId, pcLocationId]`
- conflict is detected, no overwrite occurs

### Stage KG-4 — Graph query and context output

Add:

```bash
knowledge-graph.ts query --text "..." --format context
```

Validation:

- query for `채팅 pc 사람 기준` returns ChatMessage identity graph records
- output has citations
- max top N prevents context dump

### Stage KG-5 — Projection to layer docs

Add:

```bash
knowledge-graph.ts promote <kg_id> --to ddd|sdd|bdd|tdd|adr|ssot --dry-run
knowledge-graph.ts promote <kg_id> --to ddd --apply
```

Policy:

- dry-run by default
- apply requires explicit confirmation or CLI flag
- projection should be narrow, append-only, and schema-safe

### Stage KG-6 — M45 instruction integration

Update private `.jcode/rules/*.md` guidance:

- Use `lazy graph query` before source search for project-knowledge questions.
- Use `lazy intake --capture` when reusable knowledge appears.
- Use confirmation flow before canonical graph promotion.

No blocking tool hooks required for normal behavior.

### Stage KG-7 — Validation graph integration

- layer-impact and validation-planner read `graph.jsonl`
- missing links create warnings/questions
- unresolved conflicts influence validation severity

## 10. Success criteria

A working progressive environment means:

1. New reusable knowledge from conversation is captured as candidate without being lost.
2. Candidate can become confirmed graph only through explicit confirmation or a safe, auditable rule.
3. Incorrect graph knowledge can be superseded, not silently overwritten.
4. Future queries retrieve graph records before source guessing.
5. DDD/SDD/BDD/TDD/ADR/SSOT all exist as graph layers and human-readable projections.
6. Validation uses graph links to choose checks and find missing coverage.
7. M45 private instructions make agents follow this without fragile blocking hooks.
