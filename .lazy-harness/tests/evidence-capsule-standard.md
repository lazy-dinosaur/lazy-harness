# TDD — Evidence Capsule Standard

Status: accepted
Date: 2026-06-06
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/evidence-capsule-standard.md`
Related SSOT: `.lazy-harness/ssot/capability-registry.md`
Related plan: `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - changing evidence capsule template headings, README guidance, capability registration, or self-test coverage
  - claiming validation/performance/visual/dogfood evidence should be reusable after the current session
- Must:
  - protect the template headings listed in the SDD
  - require a retention/privacy section and explicit raw transcript/secret redaction warning
  - keep `lazy-evidence-capsule` recommend-level, not warn/block
  - keep evidence capsule generation manual; hooks must not auto-write capsules
- Must not:
  - allow missing privacy guidance
  - allow capsule capability escalation without explicit record updates
  - treat evidence capsules as canonical truth over layer records/source code
- Related records:
  - `.lazy-harness/spec/platform/evidence-capsule-standard.md`
  - `.lazy-harness/ssot/capability-registry.md`
- Implementation hints:
  - Files: `.lazy-harness/templates/evidence-capsule.md`, `.lazy-harness/evidence/README.md`, `.lazy-harness/scripts/self-test.py`, `.lazy-harness/ssot/capabilities.json`
  - Tests: `.lazy-harness/scripts/self-test.py#check_evidence_capsule_standard_phase5`

## Regression cases

1. Missing heading in `.lazy-harness/templates/evidence-capsule.md` fails self-test.
2. Missing `Retention / privacy` guidance fails self-test.
3. `lazy-evidence-capsule` capability missing, wrong kind, or stronger-than-recommend level fails self-test.
4. Auto-writing evidence capsules from lifecycle hooks fails self-test.
5. Capability audit must pass with the registry entry.

## Layer completeness gate

- SDD: affected; `.lazy-harness/spec/platform/evidence-capsule-standard.md` defines the contract.
- BDD: no visible UI/user flow impact.
- SSOT: affected; `.lazy-harness/ssot/capabilities.json` adds a recommend-level checklist capability.
- DDD: no domain/business vocabulary impact.
- ADR: no new decision needed; current change implements an approved plan phase.

## Implementation map

- Status: `phase-5-implemented`
- Primary files:
  - `.lazy-harness/tests/evidence-capsule-standard.md` — this TDD record.
  - `.lazy-harness/spec/platform/evidence-capsule-standard.md` — standard contract.
  - `.lazy-harness/templates/evidence-capsule.md` — heading/privacy template.
  - `.lazy-harness/evidence/README.md` — storage and privacy guidance.
  - `.lazy-harness/ssot/capabilities.json` — recommend checklist capability.
  - `.lazy-harness/scripts/self-test.py` — regression checks.
- Key symbols:
  - `check_evidence_capsule_standard_phase5` (`self-test.py`)
- Flow:
  1. Self-test reads SDD/TDD/template/README/capability registry.
  2. It checks headings and privacy language.
  3. It runs capability audit.
  4. It scans lifecycle hooks for forbidden automatic evidence capsule writing.
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy capability audit --format=json`
