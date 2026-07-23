# tests

TDD plan and mapping. Auto-generated tests start as expected-fail or .skip until reviewed.

## Canonical test strategy

- For any test strategy / validation gate / "is Vitest required?" question, read `.lazy-harness/tests/test-strategy.xml` first before docs or package scripts.
- Store host test strategy in `.lazy-harness/tests/test-strategy.xml`.
- If missing or stale, discover from the current host root only: `package.json`, test configs, `tests/**`, source-local `__tests__`, and project docs.
- Do not use `find ..`, `grep ../`, or sibling repositories to infer host strategy.
- Human-facing `docs/test-strategy.md` is optional summary; this folder remains canonical.

## Trigger to fill

Code added/changed, regression entry created, spec sync.

## Status

- `.lazy-harness/tests/test-strategy.xml` is active and records fast, focused, standard, release, full-regression, worker, and product-validation boundaries.
- Update it when validation commands, scope, or gate semantics change.
- Auto-audited on update (Principle #1.2 Drafting and Auditing).
