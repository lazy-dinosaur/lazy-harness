# ADR 0039 — Rule Lifecycle Bindings for Executable Project Rules

- Status: Superseded for project-policy enforcement
- Date: 2026-05-26
- Superseded: 2026-06-01 by `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` Phase 5
- Trigger: Medivance dogfooding found that PR body format rules were stored in records but missed during PR creation.

## Rule digest

- Status: deprecated
- Layer: ADR
- Scope: framework-global
- Applies when:
  - evaluating old rule lifecycle binding / action-boundary hard blocks
  - deciding whether to add tool-specific project policy for bash, gh, dev-cli, or GitHub MCP
  - migrating PR body enforcement away from `tool.execute.before`
- Must:
  - treat the original rule-binding/action-boundary enforcement model as historical context
  - prefer ADR 0041 organic hybrid: pre-response relevant-record digest plus `response.completed` audit
  - keep generic destructive shell safety separate from project/team policy guidance
- Must not:
  - use this ADR as authority to add new concrete-tool project policy adapters
  - block PR description format at bash/GH tool boundary by default
- Record completion:
  - changes to this supersession update `.lazy-harness/spec/platform/rule-binding-action-boundary.md`, `.lazy-harness/ssot/rule-lifecycle.md`, and Phase 5 tests
- Related records:
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - `.lazy-harness/spec/platform/response-rule-audit.md`
  - `.lazy-harness/ssot/harness-enforcement-policy.md`

## Historical context

Lazy-harness already routed newly discovered rules into canonical records and prevented `.jcode` / Jcode memory from becoming the project rule store. Dogfooding exposed a second failure mode:

```text
Correct storage does not guarantee future action-time recall.
```

A Medivance PR body rule existed in `.lazy-harness/ssot/pr-description-format.md`, but a PR was still written with `Summary / Validation / Context` instead of the required `Why / What / Task` structure.

## Original decision

ADR 0039 originally adopted a Rule Lifecycle / Rule Binding model:

1. A durable rule could be `captured`, `bound`, `enforced`, `advisory-only`, or `retired`.
2. Rules that affect future high-risk actions needed machine-readable binding metadata or explicit advisory-only status.
3. Action-boundary helpers could enforce bindings before external mutation.
4. PR body format was the first exemplar.

The first implementation blocked malformed `gh pr create/edit` bodies through `check-rule-action-boundary.py` called by generated `.jcode/hooks/check-bash.sh`.

## Supersession

Phase 5 supersedes the tool-attached enforcement portion of this ADR.

ADR 0041 keeps the underlying problem statement but changes the architecture:

```text
message.received relevant-record query
→ compact digest before response
→ normal assistant action
→ response.completed audit/backstop
→ narrow hard stops only after evidence
```

Reasons for supersession:

- The tool-attached model would require adapters for bash, gh, dev-cli, GitHub MCP, release tools, DB tools, etc.
- It made normal work feel brittle and slow.
- It conflicted with the user-confirmed direction to keep non-record action guidance organic rather than tool-specific.

## Consequences after Phase 5

- `check-rule-action-boundary.py` remains only as a no-op legacy compatibility shim.
- New generated `.jcode/hooks/check-bash.sh` keeps generic destructive shell safety only.
- PR body structure is protected by pre-response relevant-record surfacing and response-rule audit fixtures.
- Mandatory record-completion obligations remain mandatory and may still be audited/forced through response lifecycle helpers.
- Future hard stops belong to Phase 6 promotion criteria, not this ADR.

## Implementation map

- Status: `superseded-by-adr-0041-phase5`
- Primary files:
  - `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md` — this historical/superseded ADR.
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` — replacement architecture decision.
  - `.lazy-harness/spec/platform/rule-binding-action-boundary.md` — SDD updated to legacy compatibility.
  - `.lazy-harness/ssot/rule-lifecycle.md` — SSOT updated to organic response lifecycle.
  - `.lazy-harness/hooks/lifecycle/helpers/check-rule-action-boundary.py` — no-op compatibility shim.
  - `.lazy-harness/scripts/jcode-wiring.ts` — generated bash hook is safety-only.
  - `.lazy-harness/spec/platform/response-rule-audit.md` — replacement audit surface.
  - `.lazy-harness/scripts/self-test.py` — Phase 5 fixtures.
- Protection:
  - `check_rule_action_boundary_legacy_no_project_policy`
  - `check_jcode_wiring_bash_safety_only_hook`
  - `check_response_rule_audit_from_surfaced_digest`
- Machine index:
  - graph ids: `kg_phase5_adr0039_superseded`, `kg_phase5_rule_lifecycle_organic_model`

## Rule placement

- Rule: ADR 0039 is historical for the stored-rule recall failure, but no longer authorizes project-policy enforcement through concrete tool adapters.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md`
- Why not AGENTS.md: this is an architecture decision supersession, not runtime grammar.
- Why not `.jcode`: this is shared framework architecture.
- Confirmation: user approved Phase 5 on 2026-06-01.

## Discovery capture

- DDD: no domain vocabulary change.
- SDD: `.lazy-harness/spec/platform/rule-binding-action-boundary.md` updated.
- BDD: no app UI flow change.
- TDD: Phase 5 self-tests protect supersession.
- ADR: this ADR supersession recorded; ADR 0041 remains active.
- SSOT: `.lazy-harness/ssot/rule-lifecycle.md` updated.
