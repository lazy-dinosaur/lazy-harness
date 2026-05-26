# ADR 0039 — Rule Lifecycle Bindings for Executable Project Rules

- Status: Accepted
- Date: 2026-05-26
- Trigger: Medivance dogfooding found that PR body format rules were stored in records but missed during PR creation.

## Context

Lazy-harness already routes newly discovered rules into canonical records and prevents `.jcode` / Jcode memory from becoming the project rule store. Dogfooding exposed a second failure mode:

```text
Correct storage does not guarantee future action-time recall.
```

A Medivance PR body rule existed in `.lazy-harness/ssot/pr-description-format.md`, but a PR was still written with `Summary / Validation / Context` instead of the required `Why / What / Task` structure.

## Decision

Adopt a Rule Lifecycle / Rule Binding model:

1. A durable rule can be `captured`, `bound`, `enforced`, `advisory-only`, or `retired`.
2. Rules that affect future high-risk actions need machine-readable binding metadata or an explicit advisory-only status.
3. Action-boundary helpers may enforce bindings before external mutation.
4. PR body format is the first exemplar.

## Options considered

A. Prompt/wiring only — rejected because the observed failure was prompt recall drift.
B. Ad hoc PR hook only — insufficient because the framework needs a general rule installation concept.
C. General Rule Lifecycle plus PR guard exemplar — chosen.
D. Audit-only — useful later but too late for external mutations.

## Consequences

Positive:

- Converts stored rules into executable policies.
- Gives record-audit a future target: report enduring rules without bindings.
- Keeps `.jcode` pointer-only while still using generated hooks to call framework logic.

Risks:

- Binding metadata can become stale if records move.
- Too many block-level bindings could slow agents down or cause noisy denials.
- Additional tool surfaces beyond bash/GH CLI need later adapters.

## Implementation map

- Status: `implemented-first-exemplar`
- Primary files:
  - `.lazy-harness/ssot/rule-lifecycle.md`
  - `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
  - `.lazy-harness/tests/rule-binding-pr-body-guard.md`
  - `.lazy-harness/hooks/lifecycle/helpers/check-rule-action-boundary.py`
  - `.lazy-harness/scripts/jcode-wiring.ts`
  - `.lazy-harness/scripts/self-test.py`
- Validation:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
