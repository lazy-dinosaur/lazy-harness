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

## 2026-05-26 installed host sync marker correction

Status: corrected-and-validated
Confirmation: validation evidence

Correction:

- The authoritative lazy-sync marker is `.lazy-harness/state/synced-from-commit`, not `.lazy-harness/state/source-revision`.
- A previous check looked for `source-revision` and incorrectly reported the marker as missing.
- The actual marker existed but was still at `f92d4c7...`, behind the latest source `8c1a96a...`.

Action taken:

- Re-ran `lazy-sync --force` for:
  - `/home/lazydino/dev/medivance`
  - `/home/lazydino/dev/medivance-pwa`
- Both markers now report:
  - `syncedFromCommit: 8c1a96a89c8c5ed3c5a13dad87b419b58fbbd651`
  - `sourceRoot: /home/lazydino/dev/lazy-harness`

Validation after correction:

- Medivance:
  - `lazy test` passed.
  - `lazy capability audit --format=json`: ok, count=3.
  - `lazy lifecycle-parity --format=json --fail-on-mismatch`: 13 pass, 0 fail.
- Medivance PWA:
  - `lazy test` passed.
  - `lazy capability audit --format=json`: ok, count=2.
  - `lazy lifecycle-parity --format=json --fail-on-mismatch`: 13 pass, 0 fail.

## Rule placement

- Rule: Installed-host sync freshness should be checked via `.lazy-harness/state/synced-from-commit`; `source-revision` is not the canonical marker.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/current-framework-roadmap-snapshot.md`
- Why not AGENTS.md: this is a correction to a point-in-time sync check, not a permanent agent instruction.
- Why not `.jcode`: this concerns shared lazy-harness sync state, not local/private Jcode wiring.
- Confirmation: validation evidence

## 2026-05-31 parallel-track clarification

Status: user-confirmed

Clarification:

```text
Track A — Capability Registry dogfood/evaluation and Track B — Lifecycle / response.completed Phase 3 were intentionally active in parallel.
They have different purposes and should not be collapsed into one plan.
```

Purpose split:

- Track A, Capability Registry: evaluate whether lazy-harness can discover/resolve/promote project-specific capabilities from real workflow evidence without over-hardcoding universal rules.
- Track B, Lifecycle / response.completed Phase 3: evaluate whether the response.completed lifecycle helper path is ready for an opt-in replacement plan with legacy comparison/debug fallback and rollback instructions.

Current state after 2026-05-31 checks:

- Track B Medivance-primary readiness run passed enough to draft the opt-in replacement plan/patch, but direct production hook replacement still requires explicit approval/review.
- Track A remains the other active evaluation track and should be run next or alongside the Phase 3 plan draft, using Medivance as primary evidence and PWA as secondary/contextual evidence until PWA development resumes.

Recommended next coordination:

1. Run Capability Registry evaluation on Medivance-primary evidence.
2. In parallel or immediately after, draft the Phase 3 opt-in replacement plan/patch.
3. Keep the outputs separate: capability promotion findings should not automatically imply lifecycle hook replacement approval, and lifecycle readiness should not automatically imply capability auto-promotion.

## Rule placement

- Rule: Capability Registry dogfood/evaluation and Lifecycle Phase 3 readiness are two separate active tracks that may progress in parallel but have different approval criteria.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/current-framework-roadmap-snapshot.md`
- Why not AGENTS.md: this is current roadmap coordination, not permanent harness grammar.
- Why not `.jcode`: this concerns shared lazy-harness framework roadmap state, not private Jcode-only workflow.
- Confirmation: user-confirmed

## Discovery capture

- DDD: none.
- SDD: no contract change.
- BDD: no new user behavior scenario.
- TDD: no regression change.
- ADR: no architecture decision yet; future direct replacement still needs explicit approval/review.
- SSOT: no source-of-truth change.
- Planning: parallel-track relationship clarified here.

## 2026-05-31 compare dogfood handoff pointer

Status: handoff-recorded

Current next-session entrypoint:

```text
.lazy-harness/planning/lifecycle-compare-dogfood-handoff.md
```

If the user asks to inspect accumulated dogfood/compare evidence, read that file first. It contains the current source/host state, compare log paths, ad hoc summary command, decision criteria, rollback instructions, and the explicit rule that production default replacement still needs approval.

Track status:

- Track A Capability Registry: source-side read-only candidates implemented; do not auto-apply.
- Track B Lifecycle Phase 3: compare-mode dogfood active in both Medivance and Medivance PWA through local/private user-owned Jcode wiring.

## Rule placement

- Rule: The lifecycle compare dogfood handoff is the canonical next-session entrypoint for accumulated compare evidence review.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/current-framework-roadmap-snapshot.md`
- Confirmation: user requested thorough records for next-session continuity.

## 2026-05-31 record omission finding — Medivance UI analysis

Status: observed-gap

User correction:

```text
A parallel Medivance session analyzed TreatmentPatientAddModal contact/session input typography but did not immediately capture the discovered facts in records.
```

Observed gap:

- `TreatmentPatientAddModal` 연락처/회차 typography details were present in chat/tool output but missing from exact searchable records until manually patched afterward.
- The missing facts were important because wrapper/container `text-[12px]` can be mistaken for actual input typography, while the real 연락처/회차 input values are `14px`.

Corrective action already applied in Medivance host worktrees:

- `/home/lazydino/dev/medivance/.lazy-harness/behavior/appointment-sheet-modal-redesign.md`
- `/home/lazydino/dev/medivance/.lazy-harness/spec/frontend/patient-treatment-surface-contract.md`
- `/home/lazydino/dev/medivance.fix-reservation-sheet/.lazy-harness/behavior/appointment-sheet-modal-redesign.md`
- `/home/lazydino/dev/medivance.fix-reservation-sheet/.lazy-harness/spec/frontend/patient-treatment-surface-contract.md`
- `/home/lazydino/dev/medivance.feat-calendar-renewal/.lazy-harness/behavior/appointment-sheet-modal-redesign.md`
- `/home/lazydino/dev/medivance.feat-calendar-renewal/.lazy-harness/spec/frontend/patient-treatment-surface-contract.md`

Framework backlog:

- Add a practical audit/check that detects when assistant output says "확인/발견" with concrete file/line/component facts but no subsequent record file change or candidate entry.
- Treat this as a record-discipline reliability gap, not a product bug.
- Do not rely on compare-mode lifecycle success as evidence that record discipline is complete; compare mode only checks helper parity, not semantic completeness of records.

## Rule placement

- Rule: Concrete discovered UI/component facts must be captured in host records immediately, especially when they correct a misleading wrapper-vs-actual-element interpretation.
- Scope: transient-plan/backlog
- Primary record: `.lazy-harness/planning/current-framework-roadmap-snapshot.md`
- Confirmation: user-corrected omission on 2026-05-31.

## Discovery capture

- BDD/SDD: Medivance host records were patched directly with the concrete TreatmentPatientAddModal typography facts.
- TDD: future framework protection could flag discovery-without-record patterns.
- ADR: no decision yet.
- SSOT: no source-of-truth change.
- Planning: this is a backlog item for record discipline reliability.

## 2026-05-31 correction capture gate implemented

Status: implemented

Correction capture:

User clarified that recurring agent mistakes should not merely be manually recorded after the fact. The framework itself must help prevent repetition.

Implemented behavior:

- Added `check-user-correction-capture.sh` to the response.completed lifecycle helper chain.
- The helper detects this pattern:
  1. user message contains concrete correction / repeated mistake cues (`아니`, `잘못`, `자꾸 실수`, `기록하는 게 아니`, `하네스 수정`, `잊지마`, etc.)
  2. assistant response acknowledges the correction (`맞습니다`, `죄송`, `제가 잘못`, `정정`, `누락`, etc.)
  3. the turn did not touch a durable `.lazy-harness` record/correction ledger.
- If all three are true, the hook emits STOP and tells the agent to add/update a record, append a correction candidate, or implement the harness fix with primary record/implementation map.

Why this matters:

```text
Manual host-record patching after the user complains is not enough.
The harness now blocks correction acknowledgement without durable convergence, so repeated mistakes are more likely to become searchable records or source-level fixes.
```

Implementation map:

- `.lazy-harness/hooks/lifecycle/helpers/check-user-correction-capture.sh`
  - New helper that scans `last_user_message`, `assistant_response`, and recent write tools.
  - Allows same-turn capture to `.lazy-harness/{ssot,spec,behavior,tests,decisions,planning,plans}/...`, `.lazy-harness/knowledge/corrections.jsonl`, or `.lazy-harness/logs/corrections.jsonl`.
- `.lazy-harness/hooks/lifecycle/on-response-completed.sh`
  - Runs the helper after `check-analysis-discovery-capture.sh` and before project-rule/option gates.
- `.lazy-harness/scripts/lifecycle-check.py`
  - Includes the helper in shadow/orchestrator parity order.
- `.lazy-harness/spec/platform/hook-performance-measurement.md`
  - Documents the correction-capture contract and allowed resolutions.
- `.lazy-harness/scripts/self-test.py`
  - Fixture proves acknowledgement without durable capture STOPs, and acknowledgement with `.lazy-harness` record write passes.

Layer completeness:

- SDD: yes, hook contract updated.
- TDD: yes, self-test fixture added.
- BDD: no user-facing app behavior change.
- SSOT: no schema/config/env ownership change.
- ADR: no new ADR; this implements existing ADR 0032 correction convergence behavior as an active lifecycle gate.
- Planning: this section records the implementation and rationale.

Rule placement:

- Rule: User correction acknowledgement must converge into a durable record/correction ledger or harness source fix with primary record, not just a chat apology.
- Scope: framework-behavior
- Primary record: `.lazy-harness/planning/current-framework-roadmap-snapshot.md`
- Confirmation: user-corrected on 2026-05-31.

## 2026-06-03 downstream runtime-state sync closeout

Status: completed-and-validated
Confirmation: validation evidence from downstream sync task `997504bq51`

Source repository:

- Source root: `/home/lazydino/dev/lazy-harness`
- Source commit synced: `de031ef54e33ec63ca21a8a16a2a9caef30db109` (`HARNESS isolate runtime state roots`)
- Source validation before downstream sync:
  - `.lazy-harness/bin/lazy test`: passed
  - pre-commit gate for `de031ef`: passed

Action taken:

- Ran `lazy-sync --force --from /home/lazydino/dev/lazy-harness` for:
  - `/home/lazydino/dev/medivance`
  - `/home/lazydino/dev/medivance-pwa`
- Both hosts were behind `3f5a8279a8f3...` and synced to `de031ef54e33...`.
- Sync summary for each host:
  - `updated: 33`
  - `unchanged: 134`
  - `missing: 0`
  - `knowledge/graph.jsonl` seed merge: `16` rows considered, `13` appended, `3` conflicts recorded, `0` plain

Validation after sync:

- Medivance (`/home/lazydino/dev/medivance`):
  - Marker `.lazy-harness/state/synced-from-commit`: `de031ef54e33ec63ca21a8a16a2a9caef30db109`
  - `.lazy-harness/bin/lazy test`: passed (`scope=host`, `ran=59`, `skipped=18`)
  - `.lazy-harness/bin/lazy capability audit --format=json`: `ok=true`, `count=3`
  - `.lazy-harness/bin/lazy lifecycle-parity --format=json --fail-on-mismatch`: `ok=true`, `fixtures=13`, `passed=13`, `failed=0`
  - Git status after sync: `## dev...origin/dev`
- Medivance PWA (`/home/lazydino/dev/medivance-pwa`):
  - Marker `.lazy-harness/state/synced-from-commit`: `de031ef54e33ec63ca21a8a16a2a9caef30db109`
  - `.lazy-harness/bin/lazy test`: passed (`scope=host`, `ran=59`, `skipped=18`)
  - `.lazy-harness/bin/lazy capability audit --format=json`: `ok=true`, `count=2`
  - `.lazy-harness/bin/lazy lifecycle-parity --format=json --fail-on-mismatch`: `ok=true`, `fixtures=13`, `passed=13`, `failed=0`
  - Git status after sync: `## main...origin/main`

Operational note:

- This section is a source-side closeout record. If committed after the sync, downstream hosts must be synced once more to the new closeout commit before claiming markers match source `HEAD`.

Rule placement:

- Rule: Downstream host sync closeouts should record the source commit, target hosts, marker evidence, validation commands, and post-sync git status.
- Scope: transient-plan/sync-evidence
- Primary record: `.lazy-harness/planning/current-framework-roadmap-snapshot.md`
- Why not AGENTS.md: this is point-in-time sync evidence, not a permanent operating instruction.
- Why not `.jcode`: this concerns shared lazy-harness source/host sync state, not local/private Jcode wiring.
- Confirmation: user explicitly requested both `dev/medivance` and `medivance-pwa` be synced and verified.

Discovery capture:

- DDD: no domain/business terminology change.
- SDD: no new sync contract; existing `lazy-sync` marker/drift contract applied.
- BDD: no user-facing app behavior change.
- TDD: no regression test change; downstream `lazy test` and lifecycle parity validated the synced runtime-state isolation changes.
- ADR: no new architecture decision.
- SSOT: sync marker source remains `.lazy-harness/state/synced-from-commit`.
- Planning: this closeout records the completed downstream sync/validation evidence.
