# TDD — Pre-action Search Evidence Guard

Status: accepted
Layer: TDD
Date: 2026-06-04
Related SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
Related SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
Related SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`
Related candidate: `candidate_pre_action_legacy_search_performed_false_deny_apply_patch_gap_20260604`

## Regression

A dogfood transcript showed the pre-action edit guard repeatedly blocking code edits even after the agent had performed harness-first record search/read work. The stale legacy `check-search-performed.sh` helper only inspected `recent_tool_calls` in a narrow shape and did not align with the newer generic search/read-debt evidence model.

Observed failure modes:

1. `batch` / `multi_tool_use` rows containing nested `read` calls for `.lazy-harness` records were not flattened, so valid record reads still produced an edit denial.
2. The deny text recommended `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/`, but the matcher looked only for literal `.lazy-harness/<dir>` substrings, so brace syntax could be denied.
3. Quoted bash payloads could fail-open because the helper embedded the JSON payload into a Python here-doc with shell quoting instead of passing it as argv.
4. `apply_patch` / namespaced patch-style mutation was not consistently treated as the same source-edit action, so it could bypass the same code-edit search gate that blocked `Edit`.

## Protected behavior

`check_tool_execute_before_hook` in `.lazy-harness/scripts/self-test.py` must protect all of the following:

- a code edit without prior harness/root-bound record search evidence is denied,
- a direct grep/agentgrep over `.lazy-harness` record dirs allows the edit,
- a bash grep using brace syntax such as `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/` allows the edit,
- a prior `batch` containing nested `read` calls for `.lazy-harness` records allows the edit,
- record file edits remain exempt so record capture is not blocked,
- non-code docs edits remain exempt,
- session cache still allows subsequent source edits after evidence is established,
- `apply_patch` or namespaced patch tools targeting source code without search evidence are denied instead of bypassing the guard.

## Layer completeness

- DDD: no domain/business entity changed.
- SDD: impacted. `.lazy-harness/spec/platform/search-read-debt-contract.md` is the generic guard contract; this TDD clarifies the legacy compatibility helper must respect the same root-bound evidence semantics and not behave as a concrete-tool allowlist.
- BDD: impacted only for agent workflow behavior. Expected agent behavior after fix is that valid harness-first search/read evidence unblocks mutation, while no-search source mutation remains blocked.
- SSOT: impacted. `.lazy-harness/ssot/harness-enforcement-policy.md` records the static search/read-debt evidence policy and the rejection of broad stale edit gates.
- ADR: no new decision. ADR 0041 and existing hard-stop promotion policy still apply.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` — pre-action wrapper that chains generic read-debt permit and legacy search-performed compatibility helper.
  - `.lazy-harness/hooks/lifecycle/helpers/check-search-performed.sh` — legacy source-edit compatibility helper fixed to parse payloads safely, flatten nested recent tool calls, recognize current record scopes/brace syntax, and cover patch/apply_patch/namespaced patch source edits.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — modern static search/read-debt generic evidence guard that remains the primary search/read-debt mechanism.
  - `.lazy-harness/scripts/self-test.py` — `check_tool_execute_before_hook` regression scenarios.
  - `.lazy-harness/manifests/init-categories.json` — syncs this TDD record to hosts.
- Flow:
  1. `message.received` journals search/read debt for the current turn.
  2. Before action, `on-tool-execute-before.sh` runs `check-read-debt-permit.py` first.
  3. The compatibility `check-search-performed.sh` applies only to source-code edits and source-code patch/apply_patch/namespaced patch calls.
  4. The compatibility helper must accept prior root-bound `.lazy-harness` read/search evidence, including nested batch evidence.
  5. If no evidence exists, source code mutation still denies with the standard lazy-harness gate message.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - Direct reproduction checks for brace grep allow, batch read allow, apply_patch no-search deny, and namespaced apply_patch no-search deny.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`
  - Planning: `.lazy-harness/knowledge/candidates.jsonl#candidate_pre_action_legacy_search_performed_false_deny_apply_patch_gap_20260604`
- Machine index:
  - graph ids: `kg_tdd_pre_action_search_evidence_guard`, `kg_impl_check_search_performed_false_deny_fix`, `kg_test_check_tool_execute_before_guard_false_deny_fix`
  - generated index key: pending regeneration; generated indexes are derived and non-canonical.

## Rule placement

- Rule: valid harness-first record search/read evidence must unblock pre-action source edits; stale legacy compatibility checks must not false-deny after evidence or allow patch-style source mutation to bypass the same guard.
- Scope: framework-global TDD/regression.
- Primary record: `.lazy-harness/tests/pre-action-search-evidence-guard.md`.
- Why not AGENTS.md: this is a regression/protection contract, not compact operating grammar.
- Why not `.jcode`: it must sync with lazy-harness framework code to every host.
- Confirmation: user-confirmed after dogfood transcript.

## Discovery capture

- DDD: none.
- SDD: search-read-debt/pre-response guard contracts updated or linked.
- BDD: agent workflow expectation captured above.
- TDD: this record is the regression protection.
- ADR: none.
- SSOT: harness enforcement policy linked.
- Planning: bug candidate promoted from candidates into accepted TDD/regression after reproduction and fix.
