# Model Quality Dogfood Findings

Status: active-dogfood-findings
Date: 2026-05-26
Confirmation: user-provided Gemini 3.5 session transcript and current framework checks

## 2026-05-26 Gemini 3.5 session operating-quality finding

User provided a Gemini 3.5 test-session transcript showing these issues:

- response.completed regression/record reminders happened after the response, so they were too late to prevent the mistake.
- PR body/PR creation workflow had mistakes before guard coverage.
- branch/worktree handling was shaky.
- detached/background execution was not robust.
- record reasoning was initially wrong, then corrected after gitignore inspection.
- PR API/tool call had parameter/title mistakes.

Current-state classification after checking latest lazy-harness and Medivance hosts:

- Already mitigated after the observed session:
  - PR body format for `gh pr create/edit` is now guarded by `check-rule-action-boundary.py` through `.jcode/hooks/check-bash.sh`.
  - Medivance `creating_pull_request` resolves to `medivance-pr-body-template` through Capability Registry.
  - Lifecycle fixture/capability/gate-state dogfood plumbing is synced to Medivance and Medivance PWA.
  - Current host health: gates=0, lifecycle parity 13/13, capability audits pass.
- Still not fully mitigated:
  - response.completed remains post-response by nature, so any prevention must be moved to action-boundary hooks/capabilities or preflight helpers.
  - branch/worktree discipline needs a dedicated capability/guard or workflow helper.
  - detached/background execution needs a dedicated command capability or guard for long-running dev commands.
  - GitHub MCP PR creation/edit surfaces are not yet covered by the bash/GH CLI PR body guard.
  - model suitability/routing policy for lower-reliability models is not yet codified.

Initial recommendation:

1. Treat this as a model-quality dogfood case, not only a Gemini critique.
2. Add model/profile-sensitive capability routing later:
   - risky branch/worktree/release/PR mutation work should prefer stronger coordinator/reviewer profiles.
   - lightweight UI/code edits can use faster models if guarded by action-boundary checks and validation.
3. Add future capabilities/guards for:
   - worktree/branch preflight
   - long-running command detach policy
   - GitHub MCP PR mutation adapter
   - PR metadata completeness, including title/body/base/head checks

## Rule placement

- Rule: The Gemini 3.5 session transcript is a model-quality dogfood case; recent PR/capability/lifecycle guards mitigate some failures, but branch/worktree, detach, GitHub MCP PR mutation, and model routing safeguards remain future backlog.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/model-quality-dogfood-findings.md`
- Why not AGENTS.md: this is a dogfood finding/backlog, not a finalized universal agent rule.
- Why not `.jcode`: this concerns shared lazy-harness model/profile and action-boundary behavior, not local/private Jcode-only preference.
- Confirmation: user-provided transcript plus current-state checks

## Discovery capture

- SDD: candidate model/profile-sensitive capability routing and GitHub MCP PR mutation guard.
- TDD: candidate fixtures for branch/worktree preflight, detach policy, and PR mutation metadata completeness.
- ADR: candidate decision on model routing risk tiers.
- SSOT: possible future model/profile capability policy.
- Planning: this record is the active dogfood finding.

## 2026-05-26 hook timing clarification — prevention depends on action-boundary placement

Status: user-confirmed analysis
Confirmation: user-provided Jcode agent discussion plus current code inspection

Current code-state finding:

- Jcode hook plumbing is available and working:
  - `.jcode/config.toml` registers `tool.execute.before` for bash via `.jcode/hooks/check-bash.sh`.
  - `.jcode/config.toml` registers `response.completed` via `.lazy-harness/hooks/lifecycle/on-response-completed.sh`.
- The active bash pre-tool hook now calls `.lazy-harness/hooks/lifecycle/helpers/check-rule-action-boundary.py` before the generic shell danger checks.
- PR body format is now an action-boundary guard and can deny malformed `gh pr create/edit` before mutation.
- Regression registry enforcement is still in `.lazy-harness/hooks/lifecycle/helpers/check-fix-regression.sh`, invoked from `on-response-completed.sh`, so it remains post-response/backstop behavior.

Conclusion:

```text
This is not primarily a Jcode design failure. Jcode exposes the necessary pre-tool and response lifecycle surfaces. The remaining issue is lazy-harness policy placement: policies that must prevent mutations need to run at action boundaries, while response.completed should remain a backstop.
```

Implications:

- Fix-commit regression registry checks should move or duplicate into a bash action-boundary guard for `git commit` commands, especially `Fix:` commits.
- Post-commit can still generate candidate entries after successful commits.
- response.completed should continue as final reminder/backstop.
- GitHub MCP PR mutation surfaces still need an adapter because bash `gh pr` guards do not cover MCP calls.
- Model differences matter less as more critical policies move to action boundaries, but complex judgment/routing still benefits from stronger models.

Suggested future guard chain:

```text
git commit before execution -> tool.execute.before bash guard checks Fix:/regression expectations
successful git commit -> post-commit candidate/metadata generation
response.completed -> final backstop for missed records or stale state
```

## Rule placement

- Rule: Prevention-grade policies must be bound to action boundaries; response.completed is a backstop, not a substitute for pre-mutation guards.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/model-quality-dogfood-findings.md`
- Why not AGENTS.md: this is a dogfood finding and implementation backlog, not a finalized universal agent rule yet.
- Why not `.jcode`: this concerns shared lazy-harness hook policy placement, not local/private Jcode-only preference.
- Confirmation: user-provided analysis plus current code inspection

## 2026-05-26 design constraint — avoid guard overuse

Status: user-confirmed design constraint
Confirmation: user-confirmed

Constraint:

```text
Do not overuse hard guards. If every preference becomes a block-level rule, lazy-harness loses its value as a flexible framework and becomes a brittle rule trap.
```

Design implication:

- Keep the Capability Registry level model central:
  - `discover`
  - `recommend`
  - `default`
  - `warn`
  - `block`
- Only use `block` for prevention-grade boundaries where violation causes hard-to-recover damage or repeatedly observed high-cost failures.
- Prefer `discover/recommend/default` for workflow conveniences, model guidance, and project-specific best practices.
- Prefer telemetry + dogfood tuning before promoting a policy to `warn` or `block`.
- When a response.completed finding appears, first classify whether it needs:
  1. better discovery/capability routing,
  2. a soft default/warning,
  3. a hard action-boundary block,
  4. or no framework rule at all.

## Rule placement

- Rule: Lazy-harness must avoid guard overuse; hard blocks are reserved for high-risk or repeatedly proven prevention-grade failures, while most project capabilities should remain discover/recommend/default first.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/model-quality-dogfood-findings.md`
- Why not AGENTS.md: this is an implementation design constraint still being tuned through dogfooding, not final universal grammar.
- Why not `.jcode`: this is shared framework design policy, not local/private Jcode-only workflow.
- Confirmation: user-confirmed

## 2026-05-26 framework principle — provide policy machinery, not one global policy

Status: user-confirmed design principle
Confirmation: user-confirmed

Principle:

```text
Guards, warnings, defaults, and notifications are project-specific policy choices. Lazy-harness as a framework should provide the machinery to express, route, and enforce those choices, not hardcode one global policy for every project.
```

Implications:

- A policy like regression preflight, worktree preflight, detach policy, or PR mutation guard should be represented as a capability/rule binding with level and scope.
- The framework should support `discover`, `recommend`, `default`, `warn`, and `block` consistently.
- The project/host should decide which level applies based on risk, dogfood evidence, and user/team confirmation.
- Framework code should focus on reusable mechanisms:
  - capability registry
  - action-boundary adapters
  - candidate/evidence accumulation
  - audit/reporting
  - sync/wiring
  - test fixtures
- Framework defaults may be conservative examples, but host policy must remain configurable.

## Rule placement

- Rule: Lazy-harness should provide configurable policy machinery for project-specific guards/warnings/defaults rather than hardcoding universal enforcement decisions.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/model-quality-dogfood-findings.md`
- Why not AGENTS.md: this is a framework architecture principle still being shaped through dogfooding, not final universal instruction text.
- Why not `.jcode`: this is shared lazy-harness framework design, not local/private Jcode-only workflow.
- Confirmation: user-confirmed
