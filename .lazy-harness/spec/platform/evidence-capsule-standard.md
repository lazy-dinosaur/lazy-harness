# SDD — Evidence Capsule Standard

Status: accepted
Date: 2026-06-06
Layer: SDD
Related plan: `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`
Related TDD: `.lazy-harness/tests/evidence-capsule-standard.md`
Related SSOT: `.lazy-harness/ssot/capability-registry.md`
Related template: `.lazy-harness/templates/evidence-capsule.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 증거 캡슐
  - evidence capsule
  - 검증 증거
  - 재현 기록
- Applies when:
  - a work unit makes non-trivial validation, performance, visual, migration, or cross-host claims
  - validation evidence is too large or too important to remain only in chat, commit text, or transient logs
  - closing a phase or commit where future agents need reproducible commands/results/context
- Must:
  - keep evidence capsules optional and human-authored; do not auto-write them from hooks
  - use `.lazy-harness/templates/evidence-capsule.md` as the checklist/template when a capsule is needed
  - put durable capsules under `.lazy-harness/evidence/` with privacy-reviewed content
  - record commands, results, interpretation, reproduction steps, related records, and retention/privacy notes
  - redact or summarize raw transcripts, credentials, secrets, personal data, and excessive logs
  - link capsules to records/commits/plans when they support a claim
- Must not:
  - treat an evidence capsule as canonical truth ahead of DDD/SDD/BDD/TDD/ADR/SSOT records or source code
  - require a capsule for every small edit or routine focused test
  - store raw private transcripts, raw tool-event payloads, credentials, tokens, or unrelated product data
  - make default `message.received` or response hooks write capsules automatically
- Record completion:
  - changes to template headings, required privacy posture, capability level, or automatic writing behavior update this SDD, TDD, template, and self-test coverage
- Related records:
  - `.lazy-harness/tests/evidence-capsule-standard.md`
  - `.lazy-harness/ssot/capability-registry.md`
  - `.lazy-harness/spec/platform/search-read-debt-contract.md`
- Implementation hints:
  - Files: `.lazy-harness/evidence/README.md`, `.lazy-harness/templates/evidence-capsule.md`, `.lazy-harness/ssot/capabilities.json`, `.lazy-harness/scripts/self-test.py`
  - Tests: `.lazy-harness/scripts/self-test.py`, `.lazy-harness/tests/evidence-capsule-standard.md`

## Purpose

Evidence Capsules make validation claims reproducible without turning the runtime into an evidence logger.

They answer:

```text
What was validated, with which commands/data/context, what did it mean, and how can a future agent reproduce or audit the claim?
```

## When to write one

Use an evidence capsule for:

- cross-host or downstream dogfood findings,
- long-running benchmarks or performance measurements,
- visual fidelity / screenshot / Figma comparison evidence,
- database, migration, security, or destructive-action dry-run evidence,
- phase closure summaries where commands/results are more detailed than a commit message,
- investigations where the same evidence is likely to be reused by later agents.

A capsule is usually unnecessary for:

- tiny edits validated by one focused unit test,
- purely mechanical formatting changes,
- failures that are immediately fixed and fully captured by a TDD record or commit message.

## Required headings

`.lazy-harness/templates/evidence-capsule.md` defines the stable headings:

1. `# Evidence: <topic>`
2. `## Scope`
3. `## Environment`
4. `## Commands`
5. `## Results`
6. `## Interpretation`
7. `## Reproduce`
8. `## Related records`
9. `## Retention / privacy`

## Work-unit closure checklist

Before closing a non-trivial work unit, ask:

- Required records read?
- Validation run?
- Evidence capsule needed for non-trivial claims?
- Record/project map update needed?
- Commit message includes confidence/validation?

The checklist is recommend-level, not a hard gate.

## Capability registration

In the framework source checkout, `.lazy-harness/ssot/capabilities.json` registers `lazy-evidence-capsule` as:

- `kind`: `checklist`
- `level`: `recommend`
- `checklistPath`: `.lazy-harness/templates/evidence-capsule.md`

It recommends the standard when closing non-trivial or evidence-heavy work, but it must not block commits or mutate records automatically.

Downstream host capability registries are host-owned. A host may opt in to the `lazy-evidence-capsule` capability, but synced framework self-tests must not fail solely because a downstream host has not added that host-local registry entry. The synced template and SDD/TDD records remain usable without a capability entry.

## Implementation map

- Status: `phase-5-implemented`
- Primary files:
  - `.lazy-harness/spec/platform/evidence-capsule-standard.md` — this SDD contract.
  - `.lazy-harness/tests/evidence-capsule-standard.md` — TDD/regression record for headings, privacy, recommend-only capability, and no automatic writing.
  - `.lazy-harness/evidence/README.md` — explains durable capsule storage and privacy posture.
  - `.lazy-harness/templates/evidence-capsule.md` — reusable template/checklist.
  - `.lazy-harness/ssot/capabilities.json` — registers `lazy-evidence-capsule` as recommend-level checklist in the framework source checkout; downstream copies may keep host-owned registry entries.
  - `.lazy-harness/manifests/init-categories.json` — syncs the SDD/TDD/template/README framework assets while keeping actual capsule content host-authored.
  - `.lazy-harness/project/feature-navigation.xml` — maps evidence assets under `test-doctor` as validation/closure support.
  - `.lazy-harness/scripts/self-test.py` — protects headings, privacy note, capability audit, feature map, and no automatic evidence writer.
  - `.lazy-harness/knowledge/graph.jsonl` — records implementation/protection/capability links.
- Key symbols:
  - `check_evidence_capsule_standard_phase5` (`self-test.py`) — validates the standard/template/capability invariants.
- Flow:
  1. Agent decides a capsule is useful for a non-trivial claim.
  2. Agent copies `.lazy-harness/templates/evidence-capsule.md` to a dated/topic file under `.lazy-harness/evidence/`.
  3. Agent fills summarized, privacy-reviewed evidence with commands/results/reproduction.
  4. Capsule links back to records/plans/commits and never supersedes canonical records/source.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy capability audit --format=json`
  - `.lazy-harness/bin/lazy doctor --profile=smoke`
- Cross-layer links:
  - TDD: `.lazy-harness/tests/evidence-capsule-standard.md`
  - SSOT: `.lazy-harness/ssot/capability-registry.md`
  - Planning: `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`
- Machine index:
  - graph ids: `kg_evidence_capsule_standard_specifies_contract`, `kg_evidence_capsule_template_implements_standard`, `kg_evidence_capsule_standard_protected_by_self_test`, `kg_evidence_capsule_capability_registered`

## Discovery capture

- DDD: none.
- SDD: this record defines evidence capsule semantics.
- BDD: no user-visible UI flow change.
- TDD: `.lazy-harness/tests/evidence-capsule-standard.md` protects template/capability/no-auto-write behavior.
- ADR: no new decision; implements Phase 5 of the approved compression plan.
- SSOT: capability registry gains a recommend-level checklist entry.
- Planning: Phase 5 of `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`.
