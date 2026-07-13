# TDD — Pre-action Search Evidence Guard

Status: accepted
Layer: TDD
Date: 2026-06-04
Related SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
Related SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
Related SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`
Related candidate: `candidate_pre_action_legacy_search_performed_false_deny_apply_patch_gap_20260604`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - 증거 가드 회귀
  - search evidence guard
- Applies when:
  - editing the pre-action source-edit guard or its legacy search-performed compatibility helper
  - an edit is blocked despite prior harness-first record search/read, or patch-style mutation must be gated
- Must:
  - unblock source edits once valid root-bound `.lazy-harness` search/read evidence exists, including nested batch reads
  - recognize brace-syntax record scopes and treat `apply_patch`/namespaced patch as the same source-edit action
  - keep record-file and non-code-docs edits exempt; parse hook payloads safely via argv
  - after a non-extension mid-turn steer, deny later actions until fresh post-steer map/read evidence exists, and never count late results from pre-steer tool calls
- Must not:
  - false-deny edits after evidence exists, or let patch-style source mutation bypass the search gate
- Record completion:
  - changes to the guard semantics update this TDD plus the search-read-debt and pre-response SDDs
- Related records:
  - `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - `.lazy-harness/ssot/harness-enforcement-policy.md`

## Regression

A dogfood transcript showed the pre-action edit guard repeatedly blocking code edits even after the agent had performed harness-first record search/read work. The stale legacy `check-search-performed.sh` helper only inspected `recent_tool_calls` in a narrow shape and did not align with the newer generic search/read-debt evidence model.

Observed failure modes:

1. `batch` / `multi_tool_use` rows containing nested `read` calls for `.lazy-harness` records were not flattened, so valid record reads still produced an edit denial.
2. The deny text recommended `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/`, but the matcher looked only for literal `.lazy-harness/<dir>` substrings, so brace syntax could be denied.
3. Quoted bash payloads could fail-open because the helper embedded the JSON payload into a Python here-doc with shell quoting instead of passing it as argv.
4. `apply_patch` / namespaced patch-style mutation was not consistently treated as the same source-edit action, so it could bypass the same code-edit search gate that blocked `Edit`.
5. Pi mid-turn steering could inherit earlier-instruction `recent_tool_calls`; clearing only the cache was insufficient because a slow pre-steer parallel result could arrive later and repopulate it as apparently fresh evidence.

## Protected behavior

`check_tool_execute_before_hook` in `.lazy-harness/scripts/self-test.py` must protect all of the following:

- a code edit without prior harness/root-bound record search evidence is denied,
- a direct grep/agentgrep over `.lazy-harness` record dirs allows the edit,
- `lazy map --overview` can satisfy search-debt as search evidence, while map output never satisfies required-read debt and retired `lazy find` evidence is ignored,
- a bash grep using brace syntax such as `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/` allows the edit,
- a prior `batch` containing nested `read` calls for `.lazy-harness` records allows the edit,
- record file edits remain exempt so record capture is not blocked,
- non-code docs edits remain exempt,
- session cache still allows subsequent source edits after evidence is established,
- `apply_patch` or namespaced patch tools targeting source code without search evidence are denied instead of bypassing the guard,
- Pi/OMP steering clears prior evidence and advances an evidence epoch,
- a tool result whose tool call started before the steer does not satisfy post-steer debt,
- a fresh post-steer map/read result restores action permission.

## Layer completeness

- DDD: `.lazy-harness/domain/searchable-record-memory.md` defines instruction-scoped evidence.
- SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md` defines generic guard and post-steer evidence epoch semantics.
- BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md` requires fresh post-steer evidence without text/command classification.
- SSOT: harness enforcement and CLI semantic-authority boundaries remain unchanged.
- ADR: no new decision. ADR 0041 and existing hard-stop promotion policy still apply; the user approved this narrow generic steer boundary.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` — pre-action wrapper that chains generic read-debt permit and legacy search-performed compatibility helper.
  - `.lazy-harness/hooks/lifecycle/helpers/check-search-performed.sh` — legacy source-edit compatibility helper fixed to parse payloads safely, flatten nested recent tool calls, recognize current record scopes/brace syntax, and cover patch/apply_patch/namespaced patch source edits.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — modern static search/read-debt generic evidence guard that remains the primary search/read-debt mechanism.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — advances root evidence epochs on steering and filters tool results by their start epoch before exposing recent evidence to the guard.
  - `.lazy-harness/scripts/self-test.py` — `check_tool_execute_before_hook` regression scenarios.
  - `.lazy-harness/manifests/init-categories.json` — syncs this TDD record to hosts.
- Flow:
  1. `message.received` journals search/read debt for the current turn.
  2. Before action, `on-tool-execute-before.sh` runs `check-read-debt-permit.py` first.
  3. The compatibility `check-search-performed.sh` applies only to source-code edits and source-code patch/apply_patch/namespaced patch calls.
  4. The compatibility helper must accept prior root-bound `.lazy-harness` read/search evidence, including nested batch evidence.
  5. If no evidence exists, source code mutation still denies with the standard lazy-harness gate message.
  6. A non-extension mid-turn steer clears prior evidence; only results from tool calls started in the new epoch may re-satisfy the guard.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - Direct reproduction checks for brace grep allow, batch read allow, apply_patch no-search deny, namespaced apply_patch no-search deny, and Pi steer fresh-evidence re-arming.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`
  - Planning: `.lazy-harness/knowledge/candidates.jsonl#candidate_pre_action_legacy_search_performed_false_deny_apply_patch_gap_20260604`
- Machine index:
  - graph ids: `kg_tdd_pre_action_search_evidence_guard`, `kg_impl_check_search_performed_false_deny_fix`, `kg_test_check_tool_execute_before_guard_false_deny_fix`, `kg_pi_steer_evidence_epoch_impl_20260713`, `kg_pi_steer_evidence_epoch_test_20260713`
  - generated index key: pending regeneration; generated indexes are derived and non-canonical.

## Rule placement

- Rule: valid harness-first record search/read evidence must unblock pre-action source edits; stale legacy compatibility checks must not false-deny after evidence or allow patch-style source mutation to bypass the same guard.
- Scope: framework-global TDD/regression.
- Primary record: `.lazy-harness/tests/pre-action-search-evidence-guard.md`.
- Why not AGENTS.md: this is a regression/protection contract, not compact operating grammar.
- Why not `.jcode`: it must sync with lazy-harness framework code to every host.
- Confirmation: user-confirmed after dogfood transcript.

## Discovery capture

- DDD: instruction-scoped evidence added to searchable record memory.
- SDD: search-read-debt/pre-response guard contracts updated with steer evidence epochs.
- BDD: fresh post-steer evidence behavior captured.
- TDD: this record and Pi package smoke protect the regression.
- ADR: none; the change applies ADR 0041 without a command-specific policy branch.
- SSOT: harness enforcement policy and CLI semantic-authority boundary remain linked and unchanged.
- Planning: steer hardening promoted from `candidate-steer-readdebt-rearm-fresh-evidence-20260708` into accepted regression coverage.
