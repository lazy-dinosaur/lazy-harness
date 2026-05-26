# Capability Registry Regression

Status: accepted
Layer: TDD
Related SSOT: `.lazy-harness/ssot/capability-registry.md`
Related SDD: `.lazy-harness/spec/platform/capability-resolution.md`
Related ADR: `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md`

## Regression

Project-specific customization can be useful without being a hard rule. Registry tooling must not turn every capability into a block-level hook.

## Required protection

Phase 1/2 must provide:

- `lazy capability add`
- `lazy capability list`
- `lazy capability resolve --intent <intent>`
- `lazy capability audit`

Phase 1/2 must not add blocking behavior.

Phase 2 add must:

- upsert deterministic id-sorted registry entries
- reject missing source records by default
- be idempotent on repeated identical input
- append/upsert knowledge graph capability rows

## Layer completeness gate

- DDD: no domain/business rule.
- SDD: `.lazy-harness/spec/platform/capability-resolution.md`.
- BDD: agents should discover/default capabilities without surprising hard enforcement.
- SSOT: `.lazy-harness/ssot/capability-registry.md` and `.lazy-harness/ssot/capabilities.json`.
- ADR: `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md`.

## Implementation map

- Status: `phase-2-implemented`
- Primary files:
  - `.lazy-harness/scripts/capability.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/self-test.py`
- Key symbols:
  - `check_capability_registry_cli_phase1`
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
