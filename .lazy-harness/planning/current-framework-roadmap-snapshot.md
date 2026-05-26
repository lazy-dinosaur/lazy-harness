# Current Framework Roadmap Snapshot

Status: active-roadmap-snapshot
Date: 2026-05-26
Confirmation: user requested a full record of current state and where to resume

## Summary

Current implementation work should pause on new hard guards. The next period is mostly dogfooding and evidence collection, with only low-risk planning/cleanup work unless a repeated failure proves a stronger policy is needed.

The framework direction is:

```text
Lazy-harness provides policy machinery, not one universal project policy.
Projects decide whether a capability/rule is discover, recommend, default, warn, or block.
The framework supplies records, registry, adapters, evidence accumulation, audit, sync, and tests.
```

## Current pushed state

Recent pushed commits include:

- `684b390 Add rule lifecycle action-boundary guard`
- `d692fae Add capability registry phase one`
- `f7e4891 Add capability registry upsert command`
- `f069d9a Record lifecycle phase three readiness gate`
- `cc7efe0 Add lifecycle readiness gate-state cleanup`
- `a951fba Add lifecycle real payload fixture intake`
- `f92d4c7 Tolerate existing lifecycle fixture candidates`
- `040cb46 Record model quality dogfood findings`

Current unpushed/uncommitted item at time of this snapshot:

- `.lazy-harness/planning/model-quality-dogfood-findings.md` has an added principle: lazy-harness should provide configurable policy machinery rather than hardcoding universal enforcement decisions.

## Track A — Capability Registry

### Implemented

- `lazy capability list`
- `lazy capability resolve`
- `lazy capability audit`
- `lazy capability add`
- canonical registry: `.lazy-harness/ssot/capabilities.json`
- capability kinds:
  - `script`
  - `skill`
  - `prompt`
  - `hook`
  - `command`
  - `tool-adapter`
  - `validation`
  - `checklist`
  - `audit`
- capability levels:
  - `discover`
  - `recommend`
  - `default`
  - `warn`
  - `block`

### Dogfood status

- Medivance has 3 registered capabilities:
  - `medivance-pr-body-template`
  - `medivance-release-workflow-skill`
  - `medivance-lazy-test-validation`
- Medivance PWA has 2 registered capabilities:
  - `medivance-pwa-lazy-test-validation`
  - `medivance-pwa-baseline-validation`

### Important direction

The target is not permanent manual candidate review. The long-term goal is automatic capability confirmation/promotion:

1. collect evidence automatically
2. infer candidate capabilities
3. score confidence and risk
4. auto-promote low-risk capabilities when criteria are met
5. use dogfooding to tune false positives/false negatives and thresholds

### Do next

Do not implement more Capability Registry code immediately unless needed. Let Medivance and PWA run under real use for 1-2 days, then run an evaluation:

- `lazy capability audit --format=json`
- `lazy capability list --format=json`
- representative resolves:
  - `creating_pull_request`
  - `validating_changes`
  - `validating_app_changes`
  - `preparing_release`
  - `release_dispatch`
- compare against real commands/skills/workflows used during the window
- identify missing auto-promotions and false positives

## Track B — Lifecycle / response.completed Phase 3

### Implemented

- lifecycle parity runner
- shadow lifecycle check path
- `lazy gate-state list|clear-stale`
- `record-audit` self-source warning
- `lazy lifecycle-fixture inspect|append|list`
- sanitized real payload candidate intake
- lifecycle parity now loads sanitized candidate fixtures

### Dogfood status

- Medivance lifecycle fixture candidate count: at least 1
- Medivance PWA lifecycle fixture candidate count: at least 1
- both hosts have passed lifecycle parity with candidate fixtures included: 13/13
- open gate state was cleaned to count 0 across source, Medivance, and PWA during the readiness cleanup

### Important direction

Production replacement of `response.completed` is still deferred.

`response.completed` should remain a backstop. Prevention-grade policies need action-boundary placement, but only when dogfooding shows the policy deserves `warn` or `block`.

### Do next

Before any production replacement:

1. run final readiness checklist from `.lazy-harness/planning/lifecycle-phase3-readiness-checklist.md`
2. re-sync source to Medivance and PWA if source changed
3. run:
   - source self-test + doctor
   - host `lazy test`
   - host `lifecycle-parity --fail-on-mismatch`
   - host `gate-state list`
   - host `record-audit --source /home/lazydino/dev/lazy-harness`
4. if passing, draft a Phase 3 opt-in replacement plan with legacy/debug fallback
5. do not replace production hook without explicit user approval

## Track C — Model quality / guard placement dogfood

### Finding

Gemini 3.5 session showed operating-quality issues:

- response.completed regression/record reminder arrived too late
- PR body/PR creation workflow mistakes before guard coverage
- branch/worktree confusion
- detach/background command weakness
- record policy confusion around ignored `.lazy-harness`
- GitHub MCP parameter/schema friction

### Current mitigation

Already mitigated:

- bash `gh pr create/edit` body format now has action-boundary guard
- Medivance PR creation intent resolves to PR body capability
- lifecycle fixture/capability/gate-state plumbing is in place on dogfood hosts

Not yet mitigated:

- GitHub MCP PR creation/edit guard
- branch/worktree preflight
- long-running command detach policy
- model/profile-sensitive risk routing
- Fix commit regression preflight before `git commit`

### Important design constraint

Do not overuse hard guards.

When a failure appears, classify it first:

1. better discovery/capability routing
2. soft default/warning
3. hard action-boundary block
4. no framework rule

Most project-specific capabilities should start as `discover`, `recommend`, or `default`. Promote to `warn`/`block` only after risk and dogfood evidence justify it.

### Do next

Do not implement a new guard immediately. Start a dogfood observation window for model-quality findings. If the same failure repeats, then design the relevant capability/rule binding at the least-forceful effective level.

Likely future candidates:

- Fix commit regression preflight: likely `default`/`warn` first, not immediate `block`
- branch/worktree preflight: likely `default` or `warn`
- long-running command detach policy: likely `recommend`/`default`
- GitHub MCP PR adapter: likely `warn` or validation adapter
- model risk routing: likely `recommend/default`, not block

## Track D — Throughput and transparency backlog

Captured but not implemented:

1. Parallel initial record search
2. Work transparency / resumable progress log
3. Parallel-safe record writes

Important dogfood lesson:

- dry-run/read evidence and mutating cleanup for the same file must be serialized
- do not run dry-run and write in the same parallel batch if the dry-run output is used as evidence

### Do next

Not urgent unless session interruption or throughput becomes the bottleneck. If work resumes here, start with `lazy progress checkpoint` because it improves handoff/resume safety without adding hard policy.

## Recommended resume order

1. Commit this roadmap snapshot and the updated model-quality principle.
2. Stop adding new hard guards for now.
3. Use Medivance and Medivance PWA normally for dogfooding.
4. When the user asks for evaluation, run:
   - Capability Registry evaluation
   - Lifecycle Phase 3 readiness checklist
   - Model-quality finding review
5. Only after evidence review choose the next implementation slice.

## Rule placement

- Rule: Current lazy-harness work should pause new hard guard implementation and proceed through dogfood/evidence evaluation; the framework should provide configurable policy machinery rather than hardcoding universal enforcement decisions.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/current-framework-roadmap-snapshot.md`
- Why not AGENTS.md: this is a point-in-time roadmap and resume guide, not permanent universal agent grammar.
- Why not `.jcode`: this is shared framework roadmap state, not local/private Jcode-only workflow.
- Confirmation: user-requested state capture

## Discovery capture

- Capability Registry: dogfood/evaluation pending, auto-confirmation target recorded.
- Lifecycle Phase 3: readiness tooling implemented, production replacement deferred.
- Model quality: finding captured, guard overuse constraint recorded, no immediate implementation.
- Throughput/transparency: backlog captured, not active.
