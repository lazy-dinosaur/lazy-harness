# SDD — Document Resource Ingestion

Status: accepted
Date: 2026-05-20
Layer: SDD
Related: `.lazy-harness/spec/platform/project-profile.md`, `.lazy-harness/scripts/knowledge-intake.ts`

## Contract

Document Resource Ingestion is a separate framework capability from Project Profile.

Its job is to read useful project documents outside `.lazy-harness`, judge their trustworthiness, deduplicate or quarantine them, and reproduce confirmed knowledge as durable lazy-harness records/resources.

Project Profile may consume ingestion outputs, but Project Profile should not own the whole ingestion pipeline.

## Inputs

Root-bound host documents only, unless the user explicitly points elsewhere:

- `README.md`
- `docs/**`
- architecture notes
- onboarding docs
- product briefs
- legacy planning docs
- design-system notes
- release notes or migration notes

## Output artifacts

- `.lazy-harness/project/document-intake.xml` or equivalent ledger
- `.lazy-harness/knowledge/candidates.jsonl` for uncertain facts
- DDD/SDD/BDD/TDD/ADR/SSOT records for confirmed durable facts
- source provenance links from generated records back to original document path/section
- duplicate clusters and conflict groups with selected resolution or defer reason

## Processing pipeline

```text
scan external docs
→ summarize source evidence
→ score freshness/authority/contamination risk
→ cluster duplicate or overlapping claims
→ classify durable facts into DDD/SDD/BDD/TDD/ADR/SSOT/project resources
→ ask option gates for ambiguous or architectural decisions
→ write/update records with source references
→ keep an intake ledger for assimilated, skipped, rejected, and quarantined claims
```

## Trust policy

- Treat stale, duplicate, and polluted documents as normal inputs, not failures.
- Classify each source or claim as `authoritative`, `candidate`, `historical`, `duplicate`, `conflicting`, or `rejected`.
- Freshness signals include modification time, references to current file paths, package/schema/API names that still exist, links from active records, and user confirmation. Freshness alone is not authority.
- Authority signals include explicit user confirmation, current `.lazy-harness` records, active code/config/tests, release docs, and project-owned source-of-truth docs. A newer document can still be polluted or wrong.
- Duplicate handling should cluster overlapping claims and keep the strongest source/provenance chain instead of creating repeated records.
- Contamination handling should quarantine suspicious facts into `.lazy-harness/knowledge/candidates.jsonl` or the intake ledger with a reason.
- Do not promote facts to DDD/SDD/BDD/TDD/ADR/SSOT until confirmed by code, tests, records, or the user.
- Conflict handling should present an option gate with 3-5 choices and a recommended path when there is enough evidence. Do not auto-resolve architectural conflicts from old docs.
- Do not copy large documents verbatim into records. Extract decisions, contracts, invariants, flows, risks, and validation policy.

## Implementation map

- `.lazy-harness/scripts/knowledge-intake.ts`
  - Existing Stage 1 detector for knowledge candidates from text; currently read-only and never writes records.
- Future script: `.lazy-harness/scripts/document-resource-ingestion.ts`
  - Planned inspect/plan/apply entrypoint for document scanning, scoring, clustering, and record reproduction.
- Future skill: `/lazy-doc-ingest` or equivalent
  - Planned framework-owned skill wrapper for running the ingestion flow separately from `/lazy-project-profile`.
- `.lazy-harness/spec/platform/project-profile.md`
  - Consumes ingestion outputs when available but does not own document ingestion.

## Discovery capture

- DDD: candidate, ingested docs may seed domain vocabulary/invariants.
- SDD: updated, this contract separates document ingestion from Project Profile.
- BDD: candidate, ingested docs may seed user flows.
- TDD: candidate, ingested docs may seed test strategy/regression facts.
- ADR: candidate, ingested docs may contain decisions/tradeoffs needing ADRs.
- SSOT: candidate, source authority and ownership rules may become SSOT records.
- Planning: updated, Project Profile plan should reference ingestion as a separate optional precursor.
