# SDD — Search/Read Debt Contract

Status: accepted
Date: 2026-06-06
Layer: SDD
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
Related TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - changing `message.received` search/read debt journaling
  - changing the generic pre-action evidence guard
  - changing response audit handling of unsatisfied search/read debt
- Must:
  - store only sanitized search/read debt rows in `$LAZY_RUNTIME_ROOT/state/search-read-debt.jsonl`
  - keep debt rows static/protocol-level, not selected by a raw user-text classifier
  - use safe message/session hashes and bounded counters, never raw prompts or transcripts
  - let the LLM/searcher satisfy debt by root-bound record/source/test search and reads
  - let `check-read-debt-permit.py` measure whether evidence exists before action
  - allow explicit safe-purpose `lazy find` evidence to satisfy search-debt, but never required-read debt
  - keep response audit advisory/backstop, not semantic routing
- Must not:
  - generate required-read lists, confidence scores, intent/risk/gate, or next-action from raw user text
  - treat any generated cache or helper output as proof that the LLM/searcher read evidence
  - reintroduce deleted query/backbone helper CLIs as lifecycle semantic authority
- Record completion:
  - changes to journal name, row shape, evidence tools, or guard semantics update this SDD, `.lazy-harness/spec/platform/pre-response-rule-context.md`, `.lazy-harness/tests/pre-action-search-evidence-guard.md`, `.lazy-harness/tests/pre-response-rule-context.md`, and implementation maps.

## Runtime row shape

The runtime journal is non-canonical and session-scoped:

```json
{
  "event": "message.received.search-read-debt",
  "instructionLevel": "harness-first-static",
  "messageIdHash": "16-char-hash",
  "sessionIdHash": "16-char-hash",
  "fallbackSearchCount": 1,
  "epochSeconds": 1780000000.0
}
```

Allowed fields are transport/evidence bookkeeping only. They are not semantic judgments.

## Flow

```text
message.received
→ append sanitized static search/read-debt row
→ inject compact harness-first reminder with mandatory `lazy map --overview` and repeated exact query/fallback CLI
→ LLM/searcher inspects whole record/feature/graph structure, repeats query-map over multiple candidate tokens/files/layers, then performs root-bound record/source/test search/read
→ generic pre-action guard allows mutation only after evidence exists
→ response.completed audits misses as a backstop
```

## Implementation map

- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — writes static `message.received.search-read-debt` rows and injects the compact reminder with mandatory overview-first and repeated query-map CLI.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — blocks action before root-bound evidence exists.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — audits unsatisfied debt after response.
  - `.lazy-harness/scripts/lifecycle-check.py` — mirrors `search-read-debt.jsonl` in sandbox fidelity checks.
  - `.lazy-harness/scripts/self-test.py` — protects row name, guard behavior, and deleted helper absence.
- Runtime state:
  - `$LAZY_RUNTIME_ROOT/state/search-read-debt.jsonl` — non-canonical sanitized journal.
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy prompt-budget --format=md`

## Layer completeness impact

- SDD: replaces the removed candidate helper contract with the static debt contract.
- TDD: guard and pre-response records must reference `search-read-debt.jsonl`.
- SSOT: CLI boundary remains the authority for no semantic CLI classification.
- BDD: no product UI flow.
- DDD: no domain/business rule.

## Rule placement

- Rule: runtime search/read-debt is static transport evidence, not candidate selection or semantic routing.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/search-read-debt-contract.md`
- Why not AGENTS.md: this is platform runtime contract with implementation map and tests.
- Why not `.jcode`: shared framework behavior, not local/private wiring.
- Confirmation: user-confirmed correction on 2026-06-06.

## Purpose-scoped find evidence

`lazy find --purpose ...` is a cue-only retrieval command. The guard may count a tool event or command/output blob containing `mode: "purpose-scoped-find"` or `lazy find --purpose <safe-purpose>` as **search evidence** for search-debt rows when the purpose is:

- `fact`, `record`, `information`,
- `rulebook`, `rules`, `operating-rule`, `operating-rules`,
- `test`, `tests`, `validation`,
- `capability`, `capabilities`,
- `source`, `implementation`.

The guard must not count `architecture`, `design`, or `full` purpose output as satisfying search-debt by itself. Purpose-scoped find evidence is never read evidence for concrete `requiredRead` paths.
