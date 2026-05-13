# Progressive Knowledge Graph Specification

Status: proposed
Layer: SDD
Related plan: `.lazy-harness/plans/progressive-knowledge-graph-pipeline.md`
Related ADR: `.lazy-harness/decisions/0028-progressive-knowledge-graph-backbone.md`

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
