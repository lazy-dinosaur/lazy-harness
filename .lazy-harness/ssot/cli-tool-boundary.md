# CLI Tool Boundary

Status: accepted
Layer: SSOT
Scope: framework-global
Date: 2026-06-06
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related SDD: `.lazy-harness/spec/platform/context-delivery-contract.md`

## Rule digest

- Status: active
- Layer: SSOT
- Scope: framework-global
- Applies when:
  - adding or changing CLI helpers, lifecycle hooks, generated indexes, search/query helpers, context delivery, or record/write helpers
  - a tool would inspect raw user text, rank candidate importance, choose required reads, decide whether records should be written, choose risk/intent/gate, or pick the next action
- Must:
  - treat CLI programs as tools the LLM/searcher explicitly invokes when useful
  - keep semantic judgment with the LLM/searcher after root-bound record/source/test reads
  - limit deterministic CLIs to retrieval, listing, normalization, linking, measurement, validation, hygiene, and cache generation
  - return candidate evidence, matched fields, paths, and fallback commands without declaring importance or required action
  - keep generated indexes and helper packets non-canonical
- Must not:
  - run static CLI classifiers from lifecycle hooks to decide user intent, risk, importance, gates, required reads, or record-write need
  - infer user intent from keywords such as `fix`, `bug`, `고쳐`, `수정`, `구현`, or `검증`
  - label tool output as required-read, high-confidence, self-resolve-before-change, option-gate-needed, record-needed, or next-action based on raw user text
  - make CLI output the semantic authority handed to the LLM before the LLM has reasoned over evidence
- Record completion:
  - changes that add or remove CLI semantic authority update this SSOT, affected SDD/TDD records, and implementation maps
- Related records:
  - `.lazy-harness/ssot/rule-sources.md`
  - `.lazy-harness/spec/platform/context-delivery-contract.md`
  - `.lazy-harness/spec/platform/pre-response-rule-context.md`

## Rule placement

- Rule: CLI is only a tool; the LLM/searcher owns intent, importance, read priority, write-need, risk, gate, and next-action judgment after reading evidence.
- Scope: framework-global
- Primary record: `.lazy-harness/ssot/cli-tool-boundary.md`
- Why not AGENTS.md: the durable policy needs implementation maps, tests, and related records; AGENTS may point to it later but should not be the only canonical store.
- Why not `.jcode`: this is lazy-harness framework policy shared by hosts, not a local/private Jcode preference.
- Confirmation: user-confirmed

## Implementation map

- Primary files:
  - `.lazy-harness/ssot/cli-tool-boundary.md` — canonical boundary rule.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — static transport that does not classify raw user text.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — must not run static route/user-intent classifiers.
  - `.lazy-harness/scripts/context-delivery.ts` — explicit candidate retrieval tool; must not label candidates as required or important.
  - `.lazy-harness/scripts/prompt-budget.py` — allowed measurement tool.
  - `.lazy-harness/scripts/context-index.ts` — allowed deterministic generated index cache.
- Removed/deferred examples:
  - task-router static classifier and automatic route telemetry.
  - operational-state packet prototype user-text classifier.
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - grep/static checks for forbidden auto semantic CLI invocation.
