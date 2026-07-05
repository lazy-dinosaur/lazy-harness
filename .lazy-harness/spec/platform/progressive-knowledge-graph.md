# Progressive Knowledge Graph Specification

Status: proposed
Layer: SDD
Related plan: `.lazy-harness/plans/progressive-knowledge-graph-pipeline.md`
Related ADR: `.lazy-harness/decisions/0028-progressive-knowledge-graph-backbone.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 그래프 스키마
  - graph schema
  - edge 종류
  - predicate
- Applies when:
  - capturing, confirming, querying, or promoting reusable knowledge facts
  - designing how candidates, graph drafts, and the canonical graph are stored or projected
- Must:
  - keep candidate/draft/canonical stores append-only; supersede confirmed graph records, never overwrite. Supersession may reuse the original `id` in a new append-only row carrying `status: superseded` (+ a `supersededBy` pointer): a same-`id` group with AT MOST ONE active (non-superseded) row plus superseded history is a legitimate historical trail, NOT a duplicate-id defect. Only 2+ ACTIVE rows sharing an `id` are a duplicate-id error (graph-hygiene enforces this; 2026-07-05)
  - require explicit confirmation to promote graph records into layer docs (promotion dry-run by default)
  - on subject+predicate conflicts, record conflict metadata and ask structured options
  - verify file/symbol facts via LSP/AST/source read, not guesses
  - migrate/supersede graph rows by their ACTUAL reason (is the fact still true and useful?), NOT by age or key-shape (user correction 2026-07-05). Legacy shape or an `--migration-plan` candidate only SURFACES a row; the LLM's verdict is KEEP (fact holds, row usable — shape alone is not a reason to churn), CONVERT (fact holds but legacy shape — append normalized row with the source-VERIFIED meaning, mapping hints are not truth, + same-id supersede marker), or SUPERSEDE (genuinely obsolete — cite the real reason, never "because old"). Detection tools never decide the verdict
- Must not:
  - silently promote unconfirmed conversation into canonical truth, or rely on blocking tool hooks as the main mechanism
- Record completion:
  - changes to store schemas, CLI behavior, or conflict handling update this SDD, the schemas, and self-test
- Related records:
  - `.lazy-harness/spec/platform/graph-hygiene.md`
  - `.lazy-harness/plans/progressive-knowledge-graph-pipeline.md`
  - `.lazy-harness/decisions/0028-progressive-knowledge-graph-backbone.md`
  - `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
  - `.lazy-harness/ssot/knowledge-graph-storage.md`
  - `.lazy-harness/ssot/implementation-map-storage.md`

## 1. Purpose

The progressive knowledge graph is the machine-readable backbone for lazy-harness knowledge.

It stores reusable facts from conversation, implementation, tests, user corrections, and code inspection in a form that can be queried, corrected, validated, and projected into DDD/SDD/BDD/TDD/ADR/SSOT human-readable records.

## 2. Non-goals

- Do not replace DDD/SDD/BDD/TDD/ADR/SSOT documents.
- Do not silently promote unconfirmed conversation into canonical truth.
- Do not use blocking tool hooks as the main behavior mechanism.
- Do not overwrite confirmed graph records without creating a supersession trail.

## 3. Data stores

| Store | Path | Role | Write policy |
|---|---|---|---|
| Candidate queue | `.lazy-harness/knowledge/candidates.jsonl` | Raw reusable knowledge candidates | append-only |
| Graph drafts | `.lazy-harness/knowledge/graph-drafts.jsonl` | Machine-readable draft graph records | append-only / dedupe by id |
| Canonical graph | `.lazy-harness/knowledge/graph.jsonl` | Confirmed graph records | append-only events, supersede not overwrite |
| Generated implementation index | `.lazy-harness/generated/implementation-index.json` | Rebuildable AI/LSP/AST/outline retrieval cache for file/symbol maps | derived / overwrite-on-regenerate |
| Layer docs | `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/**` | Human-readable projections | narrow append/update after confirmation |

## 4. Candidate record contract

```ts
type KnowledgeCandidate = {
  id: string;
  createdAt: string;
  source: 'conversation' | 'code' | 'test' | 'user-correction' | 'hook' | 'manual';
  utterance: string;
  detectedLayers: Array<'ddd' | 'sdd' | 'bdd' | 'tdd' | 'adr' | 'ssot'>;
  candidateType:
    | 'domain-term'
    | 'business-invariant'
    | 'contract-source'
    | 'user-behavior'
    | 'regression-fact'
    | 'decision-tradeoff'
    | 'source-of-truth'
    | 'ambiguous-knowledge';
  status: 'needs-confirmation' | 'confirmed' | 'rejected' | 'superseded';
  confidence: 'high' | 'medium' | 'low' | 'ambiguous';
  graphDraftIds: string[];
  evidence: KnowledgeEvidence[];
  questions: KnowledgeQuestion[];
};
```

## 5. Graph record contract

```ts
type KnowledgeGraphRecord = {
  id: string;
  createdAt: string;
  updatedAt: string;
  layer: 'ddd' | 'sdd' | 'bdd' | 'tdd' | 'adr' | 'ssot';
  kind:
    | 'claim'
    | 'term'
    | 'invariant'
    | 'contract'
    | 'scenario'
    | 'test'
    | 'decision'
    | 'source-of-truth'
    | 'implementation'
    | 'file'
    | 'symbol'
    | 'generated-index';
  subject: string;
  predicate: string;
  object: unknown;
  status: 'needs-confirmation' | 'confirmed' | 'superseded' | 'rejected' | 'stale' | 'needs-review';
  confidence: 'candidate' | 'confirmed' | 'code-evidence' | 'user-confirmed';
  evidence: KnowledgeEvidence[];
  links: KnowledgeLink[];
  provenance: KnowledgeProvenance;
  supersedes?: string[];
  conflicts?: string[];
};
```

## 6. Evidence contract

```ts
type KnowledgeEvidence = {
  type: 'conversation' | 'code' | 'test' | 'doc' | 'user-confirmation' | 'validation';
  path?: string;
  lines?: [number, number];
  quote?: string;
  messageId?: string;
  commit?: string;
};
```

## 7. Link contract

```ts
type KnowledgeLink = {
  rel:
    | 'specified_by'
    | 'validated_by'
    | 'implements'
    | 'depends_on'
    | 'protected_by'
    | 'decided_by'
    | 'supersedes'
    | 'conflicts_with'
    | 'source_of_truth_for'
    | 'implemented_by'
    | 'defines_symbol'
    | 'calls'
    | 'configured_by'
    | 'generates'
    | 'indexed_by';
  target: string;
};
```

## 7.1 Implementation map contract

Implementation mapping follows `.lazy-harness/spec/platform/implementation-map-standard.md`.

Rules:

- Human-facing layer records include a concise `Implementation map` section when implementation exists or is planned.
- Confirmed file/symbol/edge facts are represented in `knowledge/graph.jsonl` using implementation predicates such as `implemented_by`, `defines_symbol`, `calls`, `protected_by`, `configured_by`, and `indexed_by`.
- `generated/implementation-index.json` is a derived cache for AI/LSP retrieval and is not canonical truth.
- Function/class/component names must be verified through LSP/AST/outline/source read or equivalent evidence, not guessed.

## 8. Required CLI behavior

### 8.1 Plan

```bash
lazy intake --text "..." --plan
```

- detects candidates
- proposes graph drafts
- writes nothing

### 8.2 Capture

```bash
lazy intake --text "..." --capture
```

- appends candidate records
- appends graph drafts
- does not write canonical graph

### 8.3 Confirm

```bash
lazy intake --candidate <id> --confirm --answer A
```

- appends confirmed graph record
- records provenance
- leaves old records intact

### 8.4 Reject

```bash
lazy intake --candidate <id> --reject --reason "..."
```

- marks candidate rejected through append-only event/status
- does not delete the raw candidate

### 8.5 Query

```bash
lazy graph query --text "채팅 pc 사람 기준" --format context
```

- returns top confirmed graph records
- includes citations
- may include unresolved candidates only when directly relevant

### 8.6 Promote

```bash
lazy graph promote <kg_id> --to ddd --dry-run
lazy graph promote <kg_id> --to ddd --apply
```

- dry-run by default
- apply requires explicit confirmation
- projection must be narrow and schema-safe

## 9. Conflict behavior

If a candidate matches an existing graph record by `subject + predicate` but the object differs:

- do not overwrite
- create conflict metadata
- ask structured options:
  - A) existing graph is correct
  - B) new candidate supersedes existing
  - C) both are conditionally true
  - D) reject/defer
  - custom) type your own

## 10. Retrieval behavior

M45 private instructions should make agents prefer:

```text
lazy graph query / .lazy-harness records first
source search second
```

No blocking source-search hook is required for normal operation.

## 11. Validation requirements

- JSONL stores must parse.
- Schema metadata must pass doctor.
- `--plan` must not write files.
- `--capture` must write only candidate/draft stores.
- confirmed graph query must find records by subject, predicate, layer, and text.
- conflicts must not overwrite confirmed graph records.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/progressive-knowledge-graph.md` — SDD contract for candidate, draft, canonical graph, query, promotion, and implementation-map extensions.
  - `.lazy-harness/plans/progressive-knowledge-graph-pipeline.md` — implementation plan and storage model for the progressive graph pipeline.
  - `.lazy-harness/knowledge/README.md` — host-visible policy summary for graph stores.
  - `.lazy-harness/schemas/knowledge-candidate.schema.json` — JSON schema for candidate queue records.
  - `.lazy-harness/schemas/knowledge-graph-record.schema.json` — JSON schema for canonical/draft graph records and implementation-map edge rels.
  - `.lazy-harness/schemas/implementation-index.schema.json` — JSON schema for generated AI/LSP implementation cache.
- Key symbols:
  - `KnowledgeCandidate` (`.lazy-harness/spec/platform/progressive-knowledge-graph.md`) — TypeScript contract for candidate queue entries.
  - `KnowledgeGraphRecord` (`.lazy-harness/spec/platform/progressive-knowledge-graph.md`) — TypeScript contract for graph facts.
  - `KnowledgeEvidence` (`.lazy-harness/spec/platform/progressive-knowledge-graph.md`) — evidence citation contract.
  - `KnowledgeLink` (`.lazy-harness/spec/platform/progressive-knowledge-graph.md`) — cross-layer and implementation edge contract.
- Flow:
  1. `lazy intake --plan` detects candidates without writes.
  2. `lazy intake --capture` appends candidates and graph drafts.
  3. Confirmation promotes/supersedes graph records.
  4. Layer docs project human-readable explanations and `Implementation map` summaries.
  5. `generated/implementation-index.json` may cache file/symbol lookup for AI/LSP retrieval.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` — validates JSONL parse, schema metadata, and knowledge-intake detector behavior.
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke` — validates ADR freshness, schema metadata, and host/framework health gates.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0028-progressive-knowledge-graph-backbone.md`
  - ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
  - SSOT: `.lazy-harness/ssot/knowledge-graph-storage.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
- Machine index:
  - graph ids: `pending`
  - generated index key: `pending until implementation-index generator exists`
