# SDD — Promoted Project Command Boundary

Status: accepted
Date: 2026-08-04
Layer: SDD
Related architecture: ADR 0056 multi-runtime thin adapters
Related SDD: `.lazy-harness/spec/platform/guidance-ladder.md`, `.lazy-harness/spec/platform/policy-machinery-v2.md`
Related TDD: `.lazy-harness/tests/project-command-boundary.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - project command boundary
  - runtime-neutral project hard stop
  - 구조적 명령 차단
  - promoted command guard
- Surface terms:
  - check-project-command-boundary.py
  - commandBoundary
  - git-worktree-promotion/v1
  - raw git worktree add
  - protected remote rebranch
  - merge-tree preflight
- Applies when:
  - a host-owned project/team policy has completed L5 hard-stop promotion
  - Pi, OMP, or Jcode invokes a structured shell tool through the shared pre-tool lifecycle boundary
  - a host needs structural command prevention without copying canonical policy into a runtime prompt
- Must:
  - execute only promoted `level=block` policies with `runtime.mode=command-boundary` and `runtime.blocks=true`
  - read explicit structured shell tool name and arguments rather than user or assistant prose
  - prefer payload `working_dir`/`cwd` over inherited `LAZY_HOST_ROOT` so normalized events and isolated fixtures resolve the intended host
  - keep guard configuration and protected refs in the host-owned typed policy
  - use the shared pre-tool hook so Pi, OMP, and Jcode receive the same allow/deny result
  - fail open and stay silent for missing, malformed, non-block, disabled, or unsupported policies
  - preserve recovery commands such as `git cherry-pick --abort|--continue|--quit|--skip`
  - parse top-level newlines/control operators without treating shell redirection as extra Git revisions
  - honor `git cherry-pick -m/--mainline` when selecting the merge parent for preflight
- Must not:
  - hardcode a host/project name in framework runtime code
  - become a general shell semantic classifier
  - run mutating Git commands while deciding whether to allow a tool call
  - replace the canonical host promotion record, fixture, rollback, or user-confirmation requirements
- Record completion:
  - changes to payload parsing, supported guards, rollback semantics, or runtime wiring update this SDD and its TDD record
- Related records:
  - `.lazy-harness/spec/platform/guidance-ladder.md`
  - `.lazy-harness/spec/platform/policy-machinery-v2.md`

## Contract

`on-tool-execute-before.sh` invokes `check-project-command-boundary.py` after the framework-global destructive-command guard and before advisory search/read checks. The helper consumes the normalized lifecycle payload:

```json
{
  "event": "tool.execute.before",
  "working_dir": "/project/or/worktree",
  "tool": {
    "name": "bash",
    "args": { "command": "..." }
  }
}
```

Pi/OMP normalize shell aliases to this shape in the shared package. Jcode emits the same shape through its thin adapter. A deny is returned as a plain reason from the helper, then wrapped by the shared hook as `{ "action": "deny", "reason": "..." }`.

The helper activates only when a host policy contains:

```json
{
  "level": "block",
  "runtime": {
    "mode": "command-boundary",
    "blocks": true,
    "requiresExplicitContext": true,
    "commandBoundary": {
      "guard": "git-worktree-promotion/v1"
    }
  }
}
```

Policy Machinery block-readiness metadata, the canonical `## Hard-stop promotion` section, fixture path, validation-output evidence, and rollback criteria remain mandatory. The helper is an executor for an already-promoted host boundary, not an automatic promotion mechanism.

## `git-worktree-promotion/v1`

The first supported structural guard is intentionally narrow and policy-configured:

1. `blockRawGitWorktreeAdd=true` denies top-level `git worktree add`, including `git -C ...` and a preceding `cd ... &&` segment.
2. `blockProtectedRemoteRebranch=true` denies `git checkout -b/-B` or `git switch -c/-C` when the start point is a configured `origin/<protected>` ref. The safe path is the host's worktree helper.
3. `preflightPromotionCherryPick=true` identifies a destination-labelled promotion branch whose nearest reachable protected remote base matches the branch label. Before a single commit is cherry-picked, the helper runs read-only `git merge-tree --write-tree --merge-base <parent> HEAD <commit>` and denies predicted conflicts.
4. Multi-commit/range promotion cherry-picks are denied so each selected commit receives an independent preflight.
5. Recovery/control cherry-pick flags are allowed so an existing interrupted operation is never trapped by a newly installed guard.
6. Top-level newlines and control operators are inspected as separate statements, while shell redirections such as `2>&1` are excluded from revision counting.
7. Merge cherry-picks honor `-m/--mainline` and preflight against the selected parent.

Only explicit Git invocations are inspected. Text passed to `echo`, documentation edits, unrelated local branches, and hosts without the promoted policy remain unaffected.

## Rollback

- There is no synthetic per-call bypass. Runtime adapters do not expose a portable acknowledgement field for arbitrary shell tools.
- Host rollback is performed by demoting/retiring the policy or setting `runtime.blocks=false`; framework rollback removes the helper from the shared chain after host block policies are demoted.

## Implementation map

- Status: `implemented-focused-validation-passed`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-command-boundary.py` — load promoted host policies, parse explicit shell segments, enforce the supported structural guard, and run read-only merge-tree preflight.
  - `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` — shared Pi/OMP/Jcode deny chain.
  - `.lazy-harness/scripts/self-test.py#check_project_command_boundary` — block, allow, policy-demotion rollback, runtime-alias, newline, redirection, merge-mainline, clean-preflight, and conflict-preflight fixture.
  - `.lazy-harness/manifests/init-categories.json` — distributes the helper through the existing lifecycle-helper glob and this SDD/TDD contract as framework assets.
- Key symbols:
  - `load_boundaries` — accepts only explicitly promoted command-boundary policies.
  - `shell_segments` / `git_invocation` — narrow structured command parsing that preserves quoted text, separates top-level control flow/newlines, and excludes redirection from Git revision semantics.
  - `preflight_cherry_pick` — read-only destination promotion conflict prediction.
  - `evaluate_boundary` — guard dispatch and deny reason generation.
- Flow:
  1. Runtime adapter emits normalized structured tool payload.
  2. Shared pre-tool hook invokes the project command-boundary helper.
  3. Helper loads host-owned block policies and ignores every non-matching policy.
  4. A configured structural violation emits a canonical-record-linked deny reason; otherwise the helper stays silent.
  5. Runtime adapter translates the shared deny into its native block response.
- Protection:
  - `.lazy-harness/tests/project-command-boundary.md`
  - `.lazy-harness/scripts/self-test.py#check_project_command_boundary`
- Cross-layer links:
  - Architecture: ADR 0056 multi-runtime thin adapters
  - TDD: `.lazy-harness/tests/project-command-boundary.md`
- Machine index:
  - graph ids: `kg_project_command_boundary_sdd_20260804`, `kg_project_command_boundary_impl_20260804`, `kg_project_command_boundary_test_20260804`

## Rule placement

- Rule: execute explicitly promoted host-owned structural command boundaries through one runtime-neutral pre-tool helper.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/project-command-boundary.md`
- Why not AGENTS.md: this is an executable component contract, not per-turn grammar.
- Why not `.jcode`, `.pi`, or `.omp`: runtime adapters transport one shared result and must not own or duplicate project policy.
- Confirmation: user selected common structural hard-stop option 1 on 2026-08-04.

## Discovery capture

- DDD: no independent delta; no product/business vocabulary changed.
- SDD: independent delta; this record defines the shared command-boundary component contract.
- BDD: no independent product UI flow; runtime-visible deny behavior is implementation of the promoted policy.
- TDD: independent delta in `.lazy-harness/tests/project-command-boundary.md`.
- ADR: no new architecture beyond ADR 0056; the implementation follows the existing thin-adapter/shared-core decision.
- SSOT: independent framework enforcement-wiring note; individual project semantics stay host-owned.
- Planning: no separate backlog; implementation and focused fixture are in the same approved work unit.
