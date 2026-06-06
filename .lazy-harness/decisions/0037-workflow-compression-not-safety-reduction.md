# ADR 0037 — Workflow Compression Router Superseded

Status: superseded
Date: 2026-05-19
Superseded on: 2026-06-06
Superseded by: `.lazy-harness/ssot/cli-tool-boundary.md`, `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`

## Context

This ADR originally introduced a read-only `lazy route` workflow-compression router and later allowed `response.completed` to automatically collect route telemetry from raw user messages.

User-confirmed correction on 2026-06-06 changed the boundary:

```text
CLI is a tool only.
LLM/searcher owns intent, importance, read priority, write-need, risk, gate, and next-action judgment after reading evidence.
```

## Decision

Supersede the route classifier approach.

Removed/deferred:

- `lazy route`, `lazy route-summary`, and `lazy route-audit` CLI commands,
- `.lazy-harness/scripts/task-router.ts`,
- `.lazy-harness/fixtures/task-router/**`,
- automatic `response.completed` route telemetry from raw user messages,
- tests that expected CLI intent/risk/gate/record-capture classification.

The original safety intent remains valid: workflow compression must not reduce record-first search, default-unknown epistemics, option gates, queue closure, layer completeness, implementation maps, or commit-time validation.

## Replacement pattern

Allowed:

- deterministic indexes and graph/navigation maps,
- candidate retrieval helpers that return paths, matched fields, and fallback commands,
- measurement/hygiene/validation CLIs,
- explicit LLM/searcher-invoked helpers.

Forbidden:

- static lifecycle hooks or CLIs classifying raw user text into intent/risk/importance/gate/required-read/record-write/next-action,
- automatic route telemetry that records such classifications,
- treating generated helper output as semantic authority before the LLM/searcher reads evidence.

## Implementation map

- Removed source:
  - task-router script and task-router fixtures.
- Updated source:
  - `.lazy-harness/bin/lazy` — no route commands.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — no automatic route classifier telemetry.
  - `.lazy-harness/scripts/self-test.py` — protects removal and CLI tool boundary.
  - `.lazy-harness/AGENTS.md` — points to CLI-as-tool boundary instead of router advice.
- Canonical replacement:
  - `.lazy-harness/ssot/cli-tool-boundary.md`
  - `.lazy-harness/spec/platform/search-read-debt-contract.md`

## Rule placement

- Rule: workflow compression cannot use static CLI/user-text classifiers as semantic authority; CLI is a tool only.
- Scope: framework-global
- Primary record: `.lazy-harness/ssot/cli-tool-boundary.md`
- Why not AGENTS.md: the durable policy needs SSOT/SDD/TDD and implementation maps; AGENTS can carry only a compact reminder.
- Why not `.jcode`: this is framework behavior, not local/private Jcode workflow.
- Confirmation: user-confirmed
