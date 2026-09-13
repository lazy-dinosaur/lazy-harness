# SSOT — Harness Enforcement Policy

Status: accepted
Date: 2026-05-31
Layer: SSOT
Confirmation: user-confirmed

## Rule digest

- Status: active
- Layer: SSOT
- Scope: framework-global
- Aliases:
  - 강제 정책
  - enforcement 수준
  - 하네스 강제
- Applies when:
  - user discusses whether lazy-harness rules are mandatory or advisory
  - 사용자가 하네스 규칙, 기억, 인지, 기록 누락, 저장한 것을 안 따르는 문제를 이야기한다
  - user asks why stored rules are not being followed
  - deciding record completion, response lifecycle guidance, or tool-specific policy migration
- Must:
  - keep canonical records mandatory for confirmed rules, decisions, corrections, contracts, behaviors, and regressions
  - surface a direct framework-structured search prompt before response when host context is likely needed; keep deterministic query/digest CLIs explicit/manual helpers
  - audit missed rules and missing records after response with `response.completed`
  - preserve current debt journaling only as transitional deployed behavior; the accepted target launches one dedicated Harness Reader and joins its response before action
  - let the Reader own stored DDD/SDD/BDD/TDD/ADR/SSOT/Planning retrieval while the Parent concurrently inspects code/tests or immediately needed behavior
  - do not require duplicate Parent record reads after successful Reader completion
  - avoid solving stored-rule recall by adding per-tool project-policy adapters; only explicitly promoted, narrow, runtime-neutral structural command boundaries may execute through the shared pre-tool helper
- Record completion:
  - user-confirmed enforcement policy changes update this SSOT and link ADR/planning records
- Related records:
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - `.lazy-harness/decisions/0059-pi-primary-jcode-decommission.md`
  - `.lazy-harness/spec/platform/pi-agent-package.md`
  - `.lazy-harness/spec/platform/project-command-boundary.md`
  - `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`
  - `.lazy-harness/spec/platform/record-write-update-policy.md`
## Rule

Lazy-harness enforcement layers must not be weakened into optional memory or best-effort behavior.

The harness is mandatory infrastructure for agents that operate inside a lazy-harness host:

- The Pi stable adapter and OMP Experimental adapter share `packages/lazy-harness-pi` plus `.lazy-harness/hooks/lifecycle/*`; destructive-command blocking remains in `check-destructive-command.py`, while explicitly promoted host structural boundaries execute through `check-project-command-boundary.py` via `on-tool-execute-before.sh` (ADR 0059).
- Agents must retain and apply the core rules during a session: record-first lookup, default-unknown, option gates, requirements-first execution, rule placement, and record-as-output.
- DDD/SDD/BDD/TDD/ADR/SSOT records are not optional notes. They are the canonical institutional memory and must continue accumulating when confirmed facts, rules, contracts, behavior, tests, or decisions are discovered.
- Advisory routing, telemetry, workflow compression, and non-blocking lifecycle hooks may improve throughput, but must not reduce the effective enforcement of canonical layer obligations.
- If a policy is prevention-grade, repeated, or high-cost when missed, it must be surfaced or enforced before the miss becomes expensive; the final mechanism must preserve agent flow and avoid tool-specific adapter sprawl.

## Runtime delivery boundary (2026-08-22)

User-confirmed by ADR 0059:

- Pi is the stable primary runtime.
- OMP remains Experimental through the shared Pi/OMP package and separate install UX.
- Active Jcode adapter, hook, trust, prompt-transport, launcher-promotion, and typed-routing integration is decommissioned.
- Runtime-neutral lifecycle payloads, work-unit grounding, bounded validation, progress, project-command boundaries, and distribution-aware audits remain canonical framework behavior.
- Historical Jcode records remain searchable decision evidence but do not authorize active runtime integration.
## Active memory loop policy

User-confirmed on 2026-06-01:

The issue is bigger than any one PR/runtime rule. Lazy-harness must become an active memory loop:

```text
write complete records
→ maintain indexes/digests as helper metadata
→ inject direct framework-structured search prompts before response
→ LLM/searcher searches records/source/tests directly
→ audit after response
→ update records again
```

The framework should not rely on agents manually remembering every stored rule, and it should not solve recall by attaching project policy to each tool.

## Mandatory records vs organic rule guidance

User-confirmed on 2026-06-01:

Lazy-harness should distinguish two classes of obligations:

1. **Record-as-output obligations are mandatory.**
   - Confirmed project rules, source-of-truth corrections, decisions, scenarios, contracts, and regression cases must still converge into the correct `.lazy-harness` layer.
   - It is acceptable for these record-completion obligations to be strong/forced because they protect the framework memory itself.
2. **Non-record action guidance should not become tool-specific policy.**
   - Do not encode rules as `when bash then ...`, `when gh then ...`, `when dev-cli then ...`, or `when GitHub MCP then ...`.
   - Instead, host-dependent turns should receive a pre-response direct-search prompt and be checked through response-completed audit/backstop; deterministic record-query/digest CLIs remain explicit/manual helpers.

Target loop:

```text
mandatory record completion for canonical memory
+
pre-response direct-search prompt for action guidance
+
response.completed audit for missed rules/records
```

This preserves strong memory guarantees while avoiding broad slow blocking and tool-specific adapter sprawl.

## Hook policy

Hooks remain important, but policy should move to the response lifecycle:

```text
pre-response direct-search prompt
+
search/read debt journal from message.received when required context is unresolved
+
response.completed audit/backstop
```

Tool-specific policy hooks should be removed or migrated. Tool hooks may remain only as generic transport, destructive safety, logging, search/read evidence guards, and explicitly L5-promoted structural command executors whose canonical semantics/configuration remain host-owned. Search/read debt is produced at message.received as a direct framework-structured search prompt, and the generic guard may deny action only when the LLM/searcher has not left required direct search/read evidence. Project rules should not be authored as runtime-specific `bash`, `gh`, `dev-cli`, or GitHub MCP adapters.

## 2026-08-04 promoted project command-boundary result

The user selected common structural hard-stop option 1 after a Medivance dogfood session read the PR/worktree SSOT but later reused the same worktree for a protected destination branch and reached a cherry-pick conflict.

Accepted boundary:

- Canonical project semantics and hard-stop promotion evidence remain in the host `.lazy-harness` policy/SSOT/TDD records.
- `.lazy-harness/hooks/lifecycle/helpers/check-project-command-boundary.py` is a project-name-free executor for explicitly promoted `level=block`, `runtime.mode=command-boundary` policies.
- The helper reads only structured shell tool input and policy configuration. It never classifies user/assistant prose.
- Pi and OMP reach the helper through the same `on-tool-execute-before.sh` chain.
- The first supported guard denies raw worktree creation and protected-remote rebranching, and runs read-only merge-tree conflict preflight for destination-labelled single-commit promotion cherry-picks.
- Recovery commands remain allowed; malformed/unconfigured hosts fail open; explicit bypass requires structured policy acknowledgement plus a reason.

This is not a return to the rejected broad hard-gate experiment. It is the L5 exception already allowed by the guidance ladder: user-confirmed, narrow, fixture-protected, reversible, and canonically host-owned.

Migration target:

- Inventory existing tool-attached project policy checks.
- Keep minimal destructive safety.
- Move PR/runtime/release/DB guidance into relevant-record query + compact digest + response audit.
- Remove tool-attached policy checks once response-lifecycle coverage is proven by fixtures.

## 2026-06-01 Phase 5 migration result

Phase 5 migrated the first tool-attached project-policy exemplar out of the bash/GH action boundary:

- `check-rule-action-boundary.py` is retained only as a no-op legacy compatibility shim.
- generated `.jcode/hooks/check-bash.sh` is destructive shell safety only.
- PR body structure is covered by pre-response relevant-record digest plus `response.completed` response-rule audit.
- ADR 0039 and rule-binding action-boundary SDD are superseded for project-policy enforcement.

This keeps the mandatory memory loop strong while avoiding concrete tool adapter sprawl.

## 2026-06-02 search/read debt journal result

User-confirmed after dogfood screenshots:

```text
검색을 먼저 하게 강제하고 그다음에 작업하는거로 하는거지
```

Accepted policy:

- Deleted query-helper producers must not be reintroduced as default semantic authority in `message.received`; use direct LLM/searcher root-bound evidence instead.
- The LLM or searcher agent performs semantic expansion and root-bound search first.
- When a correlated direct-search row or packet has concrete `requiredRead` paths or fallback searches, missing evidence becomes search/read debt and the generic evidence guard denies action until direct search/read evidence exists.
- This is packet-scoped, not a concrete-tool project-policy adapter.
- The current transport is `message.received` direct-search prompt plus a generic `tool.execute.before` evidence guard plus `response.completed` audit/backstop; the core semantics are protocol-agnostic and ACP-compatible.

User-corrected after implementation:

- A non-LLM hook must not be treated as the semantic authority for multilingual/user-surface intent such as Korean `기능패널` mapping to English records or code.
- The LLM or a searcher agent must perform semantic expansion and root-bound search.
- The harness should measure whether search/read happened and guard action when the agent tries to act without that grounding.
- Therefore the active prevention model is two-stage:
  1. **search-debt** for ambiguous/low-confidence host-context turns: no search evidence before action triggers the generic evidence guard.
  2. **read-debt** after concrete records/files are known: no read evidence for required paths before action triggers the generic evidence guard.

## 2026-08-26 Harness Reader ownership correction

User-confirmed correction: the mandatory memory loop should be satisfied by a dedicated read-only Reader searching the stored harness memory, not by making the Parent search records first and then prove/reread them through debt bookkeeping.

Accepted target flow:

```text
work-unit start
→ launch Harness Reader for complete map-first record retrieval
∥ Parent inspects source/tests or immediately needed behavior
→ wait for Reader response
→ complete: merge policies/facts and proceed
→ incomplete/conflict/failure: bounded Parent follow-up or option gate
```

The Reader searches and reads relevant DDD/SDD/BDD/TDD/ADR/SSOT/Planning records and returns policies, facts, conflicts, missing information, record paths, and status. The Parent retains decisions, mutation, integration, and validation. Successful Reader completion does not create routine Parent read debt or require candidate admission, provenance proof, independent audit, or agreement receipts.

The isolated `work/reader-runtime-v1` source/test slice now narrows the debt infrastructure: one dedicated Reader plus explicit content join can satisfy the guard, while the existing direct journal/map/read path remains the unavailable/non-complete fallback. Main integration is still unapproved. The v1–v3 proof-remediation direction is not revived.
## 2026-06-01 Phase 6 guidance ladder result

Phase 6 added the promotion criteria before adding any new hard stop:

- default rule guidance remains record digest surfacing plus response audit,
- hard stops are L5 guidance only,
- a hard stop requires a canonical `## Hard-stop promotion` section,
- the promotion section must document user confirmation, miss/risk evidence, softer coverage analysis, fixture, narrowness, and rollback,
- `.lazy-harness/scripts/hard-stop-promotion-audit.py` validates promotions in strict mode.

This preserves the existing plan: continue the active memory loop first, then fix weaknesses only when evidence justifies a narrow promotion.

## Current dogfood finding

The observed failure mode is not PR-specific and not caused by missing records alone. The framework stores project rules, source-of-truth facts, contracts, behaviors, tests, decisions, and workflow rules, but agents can later fail to consult and apply any of those stored records before acting.

Symptoms observed on 2026-05-31:

- Agent read generic AGENTS-style command hints and shell/env files, but skipped the canonical HostApp dogfood runtime SSOT before reasoning about test instances.
- `response.completed` exists, but current generated Jcode wiring uses `blocking = false`, weakening the original completion-audit contract.
- `tool.execute.before` currently blocks dangerous bash, but does not generally ensure host-dependent rule recall.
- Record accumulation into DDD/SDD/BDD/TDD/ADR/SSOT appears lower when gates become advisory, because misses are reported after the response rather than surfaced naturally at the right moment.

## 2026-06-01 hard-gate experiment result

A hard-gate restoration experiment restored edit/write/multiedit blocking hooks and added tool-attached runtime/PR-style enforcement. The user rejected this direction because it felt too slow and too attached to concrete tools.

Result:

- Revert the hard-gate/tool-attached implementation.
- Keep the finding that rule recall must improve.
- Do not grow per-tool adapters as the primary architecture.
- Explore C+ v2 organic hybrid instead: ambient rule context, graduated guidance, soft action/journal continuity, and narrow hard stops only for irreversible or repeatedly failed boundaries.

## Required direction

Future fixes should restore mandatory behavior without turning the framework into a brittle or slow blocker:

1. Preserve lazy-harness grammar and lifecycle delivery through the Pi stable / OMP Experimental shared package over `.lazy-harness/hooks/lifecycle/*` scripts (ADR 0059).
2. Improve rule recall by launching one dedicated Harness Reader while the Parent uses the same time for code/test or immediate-behavior investigation.
3. Join the Reader response before plan/mutation/completion; handle incomplete/conflict/failure explicitly instead of routine duplicate Parent reads.
4. Keep `response.completed` as a backstop for missed record/capture work.
5. Add focused regression fixtures for the simple Reader/Parent/join flow, but do not encode an admission/proof/audit framework.
6. Keep narrow destructive/structural hard stops separate from record retrieval.
7. Compare the simple joined flow against Direct Parent only after implementation; do not revive debt or proof complexity merely to preserve the experiment.

## Implementation map

- Status: `live-r2-terminal-incomplete; per-read-ledger/child-boundary/adversarial-shell/fallback enforcement reviewed-ok-and-standard-green; main-integration-pending`
- Primary files:
  - `.lazy-harness/AGENTS.md` — compact Reader-first/Parent-lane/content-join/direct-fallback grammar.
  - `packages/lazy-harness-pi/agents/record-reader.md` — read-only stored-record retrieval role.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — dedicated Reader child tool boundary, launch-bound cumulative/per-read/positive-ledger checks, join/fallback/epoch/fingerprint, and print-output adapter.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` / `check-search-performed.sh` — successful join evidence, failed-join evidence truncation, fresh fallback, and conservative Parent source-shell parity.
  - `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` — chains runtime-agnostic destructive safety and promoted host structural command boundaries before advisory evidence checks.
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-command-boundary.py` — executes host-owned promoted command-boundary policies without project-name or runtime-specific policy hardcoding.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — completion backstop hook.
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — project-rule placement gate.
  - `.lazy-harness/ssot/medivance-dogfood-runtime-policy.md` — concrete runtime/test-instance policy skipped by the observed agent.
  - `.lazy-harness/planning/organic-hybrid-rule-guidance-plan.md` — current plan for C+ v2 organic hybrid exploration.
- Flow:
  1. One dedicated Reader loads canonical record memory while the Parent investigates source/tests.
  2. `lazy_reader_join` requires content marker, run/root revision/evidence epoch, canonical paths, positive internally consistent counters, cumulative budget, derived per-read cap/max observed limit, and zero failed calls.
  3. A complete join supplies record fingerprints; failed joins discard pre-join evidence before fallback. Native source read/grep/find and strict simple shell grep/rg remain available, while Reader child and shell mutations stay blocked.
  4. Response-completed stays a backstop; print mode preserves primary stdout and sends advisory to stderr, while TUI/JSON/RPC keep bounded follow-up.
  5. Narrow destructive/structural hard stops remain separate from record retrieval.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract`
  - `.lazy-harness/scripts/self-test.py#check_tool_execute_before_hook`
  - `.lazy-harness/scripts/self-test.py#check_read_debt_permit_generic_external_action`
  - focused isolated checks plus final standard/full self-test passed; independent blocker re-review returned `OK`.
  - `.lazy-harness/evidence/dedicated-reader-runtime-v1-20260906.md`
  - `.lazy-harness/evidence/dedicated-reader-live-canary-r2-20260906.md`
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`
  - ADR: `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md`
  - ADR: `.lazy-harness/decisions/0059-pi-primary-jcode-decommission.md`
  - SDD: `.lazy-harness/spec/platform/project-rule-router.md`
  - SDD: `.lazy-harness/spec/platform/pi-agent-package.md`
  - SDD: `.lazy-harness/spec/platform/project-command-boundary.md`
  - SSOT: `.lazy-harness/ssot/rule-sources.md`
  - SSOT: `.lazy-harness/ssot/project-identity.md`

## Rule placement

- Rule: lazy-harness enforcement layers must not weaken into optional memory, but the replacement architecture should be organic/free and avoid broad slow blocking or tool-specific adapter sprawl.
- Scope: framework-global
- Primary record: `.lazy-harness/ssot/harness-enforcement-policy.md`
- Why not AGENTS.md: AGENTS is the operational grammar; this SSOT records the enforcement policy and dogfood result that should drive future architecture.
- Why not `.jcode`: this is shared framework behavior for all lazy-harness hosts, not a local/private Jcode-only workflow.
- Confirmation: user-confirmed
- Reader ownership correction: user-confirmed on 2026-08-26; Reader owns stored harness retrieval, Parent owns concurrent code/behavior investigation, and Reader completion replaces routine Parent debt work.
- Isolated implementation: user-approved full coherent worktree slice; main integration and release remain separate decisions.
## Discovery capture

- DDD: none.
- SDD: future spec likely for ambient rule context, graduated guidance, soft action journal, and narrow hard-stop promotion.
- BDD: observed agent workflow failure captured as dogfood evidence; user wants a more organic/free workflow.
- TDD: future fixtures needed for skipped runtime/PR rule recall without broad hard gates.
- ADR: required before implementing C+ v2 organic hybrid.
- SSOT: updated, this record.
- Planning: `.lazy-harness/planning/organic-hybrid-rule-guidance-plan.md`.

## 2026-06-04 pre-action search evidence false-deny fix

Status: accepted
Related TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md`

User-confirmed dogfood finding:

```text
검색했는데도 legacy edit guard가 막는 상황은 버그다.
```

Accepted policy clarification:

- The active prevention model remains packet-scoped generic search/read-debt plus response audit/backstop.
- Legacy source-edit compatibility checks must not contradict that model by denying after valid harness-first record search/read evidence.
- Compatibility checks must recognize the evidence shapes the harness itself recommends, including brace-style `.lazy-harness/{domain,...}` searches and nested batch reads.
- Patch-style and namespaced patch-style source mutation must not bypass the same no-search source-edit guard that applies to Edit/Write/MultiEdit.
- This fix does not promote a new broad project-specific hard gate; it removes stale false-deny/false-bypass behavior from an existing compatibility helper.

Implementation map update:

- `.lazy-harness/hooks/lifecycle/helpers/check-search-performed.sh` — corrected compatibility helper.
- `.lazy-harness/scripts/self-test.py#check_tool_execute_before_hook` — regression fixture covering brace grep, batched reads, apply_patch, and namespaced apply_patch.
- `.lazy-harness/tests/pre-action-search-evidence-guard.md` — canonical TDD record.

## Discovery capture — Harness Reader ownership correction

- DDD: updated — Harness Reader/Parent code lane/Reader join vocabulary.
- SDD: updated — current debt implementation and accepted supersession direction.
- BDD: updated — parallel Reader/Parent behavior.
- TDD: updated — planned join/fallback scenarios; no false passing claim.
- ADR: updated — responsibility boundary corrected.
- SSOT: updated here — mandatory recall remains; debt transport is transitional.
- Planning: updated — v3 proof remediation superseded by simple Reader join backlog.

## Discovery capture — Reader enforcement implementation

- DDD: implementation status only.
- SDD/BDD/TDD: isolated Reader/join/output behavior implemented and focused-green.
- ADR: ownership unchanged; status updated.
- SSOT: updated here because the enforcement source now accepts exact Reader join while preserving direct fallback.
- Planning: isolated implementation remains unintegrated; live model/review/main gates remain.
