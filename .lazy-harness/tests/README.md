# tests

TDD plan and mapping. Auto-generated tests start as expected-fail or .skip until reviewed.

## Canonical test strategy

- Store host test strategy in `.lazy-harness/tests/test-strategy.xml`.
- If missing or stale, discover from the current host root only: `package.json`, test configs, `tests/**`, source-local `__tests__`, and project docs.
- Do not use `find ..`, `grep ../`, or sibling repositories to infer host strategy.
- Human-facing `docs/test-strategy.md` is optional summary; this folder remains canonical.

## Trigger to fill

Code added/changed, regression entry created, spec sync.

## Status

- Empty is valid (Principle #10 Empty-Container Tolerance)
- Will be filled when triggers fire (Principle #6 Trigger-Based Growth)
- Auto-audited on update (Principle #1.2 Drafting and Auditing)
