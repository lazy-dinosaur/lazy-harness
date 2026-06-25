# Capability Registry Regression

Status: accepted
Layer: TDD
Related SSOT: `.lazy-harness/ssot/capability-registry.md`
Related SDD: `.lazy-harness/spec/platform/capability-resolution.md`
Related ADR: `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - implementing capability registry tooling (`lazy capability add/list/resolve/candidates/audit`)
  - registering project customization that need not be a hard rule, or detecting candidate capabilities
- Must:
  - provide capability add/list/resolve/candidates/audit with deterministic, id-sorted, idempotent registry entries
  - resolve capabilities by discouragedActions so raw commands surface preferred replacements; keep candidate detection read-only
- Must not:
  - add blocking or hard-rule behavior in Phase 1/2 capability tooling
  - auto-promote candidates to `warn` or `block`
- Record completion:
  - changes to registry commands or candidate detection update this TDD plus the capability-resolution SDD and registry SSOT
- Related records:
  - `.lazy-harness/ssot/capability-registry.md`
  - `.lazy-harness/spec/platform/capability-resolution.md`
  - `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md`

## Regression

Project-specific customization can be useful without being a hard rule. Registry tooling must not turn every capability into a block-level hook.

## Required protection

Phase 1/2 must provide:

- `lazy capability add`
- `lazy capability list`
- `lazy capability resolve --intent <intent>`
- `lazy capability candidates`
- `lazy capability audit`

Phase 1/2 must not add blocking behavior.

Phase 2 add must:

- upsert deterministic id-sorted registry entries
- reject missing source records by default
- be idempotent on repeated identical input
- append/upsert knowledge graph capability rows
- preserve repeated multi-value flags for `--applies-when`, `--action`, and `--tag`
- preserve rulebook-specific fields: `preferredActions`, `discouragedActions`, `rulebookRecord`, and `requiresReasonForBypass`
- allow Option B `policyIds` links from capabilities to typed policy registry records
- resolve capabilities by `discouragedActions` so raw commands can surface preferred replacements
- keep framework-owned seed capability `sourceRecord` files in the Category A sync manifest so host `lazy capability audit` remains green after lazy-sync merges missing framework capability ids, while excluding host-owned capability source records from this framework manifest rule

Candidate detection must:

- stay read-only
- detect missing app-validation candidates from package validation scripts
- detect partial release workflow capabilities that lack concrete action labels
- avoid automatic `warn`/`block` promotion

## Layer completeness gate

- DDD: no domain/business rule.
- SDD: `.lazy-harness/spec/platform/capability-resolution.md`.
- BDD: agents should discover/default capabilities without surprising hard enforcement.
- SSOT: `.lazy-harness/ssot/capability-registry.md`, `.lazy-harness/ssot/capabilities.json`, and Option B links to `.lazy-harness/ssot/policies.json`.
- Sync: `.lazy-harness/manifests/init-categories.json` must include framework capability sourceRecord files.
- ADR: `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md`.

## Implementation map

- Status: `phase-2-implemented`
- Primary files:
  - `.lazy-harness/scripts/capability.ts`
  - `.lazy-harness/scripts/rulebook.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/manifests/init-categories.json`
  - `.lazy-harness/scripts/self-test.py`
- Key symbols:
  - `check_capability_registry_cli_phase1`
  - `capabilityCandidates`
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
