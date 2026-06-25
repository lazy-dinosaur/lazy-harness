# Rule Binding PR Body Guard Regression

Status: superseded-by-response-rule-audit
Layer: TDD
Related SSOT: `.lazy-harness/ssot/rule-lifecycle.md`
Related SDD: `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
Replacement SDD: `.lazy-harness/spec/platform/response-rule-audit.md`
Related ADR: `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md`
Superseded by: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`

## Rule digest

- Status: deprecated
- Layer: TDD
- Scope: framework-global
- Applies when:
  - working on PR-body rule enforcement or the legacy rule-action-boundary helper
  - asking why tool-attached `gh pr` PR-body denial was replaced by digest + response audit
- Must:
  - surface PR description guidance via relevant-record digest before response; audit catches ignored PR rules
  - keep `check-rule-action-boundary.py` a no-op shim and the generated Jcode bash hook safety-only
- Must not:
  - encode project policy as bash/GH-specific tool adapters or block `gh pr create/edit` from the legacy helper
- Record completion:
  - PR-body rule protection now lives in the response-rule-audit TDD/SDD; update those on change
- Related records:
  - `.lazy-harness/spec/platform/response-rule-audit.md`
  - `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
  - `.lazy-harness/ssot/rule-lifecycle.md`
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md`

## Regression

A stored PR body rule can be missed if the agent does not recall the host record before creating or editing a PR.

This original regression remains important. Phase 5 changes the protection mechanism.

## Superseded protection

Before Phase 5, a host with a stored PR description format rule caused `gh pr create` / `gh pr edit` bash commands with malformed bodies to be denied by `check-rule-action-boundary.py`.

That tool-attached protection is now superseded because project policy should not be encoded as bash/GH-specific adapters.

## Current required protection

1. `check-rule-action-boundary.py` is a no-op compatibility shim.
2. Generated `.jcode/hooks/check-bash.sh` keeps only generic destructive shell safety.
3. PR description guidance is surfaced through relevant-record digest before response.
4. `response.completed` audit catches strong evidence that a surfaced PR body rule was ignored.

## Protected cases

Self-test coverage must prove:

- malformed `gh pr create --body ...` is **not** blocked by the legacy action-boundary helper,
- valid PR bodies also pass the legacy helper,
- generated Jcode bash hook does not contain `check-rule-action-boundary.py`, `BOUNDARY_OUT`, or `gh pr` project-policy phrases,
- generated Jcode bash hook still contains destructive shell safety denies,
- response-rule audit emits when a surfaced PR description rule is ignored,
- response-rule audit stays silent when PR body has `Why`, `What`, and `Task` headings.

## Layer completeness gate

- DDD: no domain rule.
- SDD: superseded action-boundary contract lives in `.lazy-harness/spec/platform/rule-binding-action-boundary.md`; replacement audit contract lives in `.lazy-harness/spec/platform/response-rule-audit.md`.
- BDD: agent-visible behavior changes from pre-tool denial to pre-response guidance plus post-response audit.
- SSOT: `.lazy-harness/ssot/rule-lifecycle.md` owns current lifecycle semantics.
- ADR: ADR 0039 is superseded for enforcement by ADR 0041.

## Implementation map

- Status: `phase5-superseded`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-rule-action-boundary.py` — no-op compatibility shim.
  - `.lazy-harness/scripts/jcode-wiring.ts` — safety-only generated bash hook.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — replacement response audit helper.
  - `.lazy-harness/scripts/self-test.py` — Phase 5 fixture tests.
- Key symbols:
  - `check_rule_action_boundary_legacy_no_project_policy` — verifies no tool-attached PR denial remains.
  - `check_jcode_wiring_bash_safety_only_hook` — verifies generated bash hook is safety-only.
  - `check_response_rule_audit_from_surfaced_digest` — verifies replacement PR miss audit.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
- Machine index:
  - graph ids: `kg_phase5_rule_binding_pr_guard_superseded`, `kg_phase5_response_audit_replaces_pr_guard`

## Discovery capture

- DDD: none.
- SDD: action-boundary SDD superseded and response-rule-audit remains active.
- BDD: user-visible feedback moves later in lifecycle for action guidance.
- TDD: this record updated to the new protection surface.
- ADR: ADR 0039 superseded by ADR 0041.
- SSOT: rule lifecycle SSOT updated.
