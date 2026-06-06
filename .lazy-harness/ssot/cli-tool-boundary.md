# CLI Tool Boundary

Status: accepted
Layer: SSOT
Scope: framework-global
Date: 2026-06-06
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`

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
  - `.lazy-harness/spec/platform/search-read-debt-contract.md`
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
  - `.lazy-harness/scripts/prompt-budget.py` — allowed measurement tool.
  - `.lazy-harness/scripts/context-index.ts` — allowed deterministic generated index cache.
- Removed/deferred examples:
  - task-router static classifier and automatic route telemetry.
  - operational-state packet prototype user-text classifier.
  - deleted query-helper prototypes that accepted raw user messages.
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - grep/static checks for forbidden auto semantic CLI invocation and deleted helper absence.


## Record Index Header boundary review — 2026-06-06

Decision: existing SSOT is sufficient for SCR-303/SCR-304. No new ADR is required for the contract-only SDD/TDD phase.

Reasoning:

- `## Index header` is record-authored metadata in canonical records.
- The SDD/TDD phase does not add parser/cache code.
- Future deterministic cache/listing work remains allowed only as retrieval/listing/cache generation.
- Raw-user-message query, ranking, required-read, confidence, intent, risk, gate, next-action, or candidate-meaning output remains forbidden.
- A generated cache/header hit cannot satisfy search/read debt by itself.

Boundary for SCR-401:

- Decision: canonical future cache/listing name is `record-index`.
- ADR: `.lazy-harness/decisions/0042-record-index-cache-naming.md` records the naming trade-off.
- Scope: deterministic record-authored metadata listing/cache generation only.
- Existing `context-index` may remain only as a legacy/deprecated compatibility alias during SCR-402 migration, if implementation tests justify it.
- New docs/contracts must not describe `context-index` as the canonical name for searchable record memory.
- SCR-402 remains implementation work and must preserve no raw-message query input, no semantic authority outputs, and no cache-hit evidence satisfaction.

Discovery capture:

- DDD: `.lazy-harness/domain/searchable-record-memory.md` defines semantic-authority terms.
- BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md` defines behavior scenarios.
- SDD: `.lazy-harness/spec/platform/record-index-header.md` defines the field/consumer contract.
- TDD: `.lazy-harness/tests/record-index-header.md` defines fixture expectations.
- ADR: `.lazy-harness/decisions/0042-record-index-cache-naming.md` captures SCR-401.
- SSOT: this section records SCR-305.
- Planning: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` records status and next gate.
