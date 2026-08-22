# TDD — Promoted Project Command Boundary

Status: accepted
Date: 2026-08-04
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/project-command-boundary.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - project command boundary regression
  - worktree promotion hard-stop fixture
  - merge-tree guard test
- Surface terms:
  - check_project_command_boundary
  - check-project-command-boundary.py
  - git-worktree-promotion/v1
- Applies when:
  - changing the shared pre-tool helper chain
  - changing promoted project command policy parsing or Git promotion preflight
  - claiming Pi/OMP parity for a structural command hard stop
- Must:
  - prove both block and allow cases
  - prove all normalized runtime shell aliases receive the same result
  - prove non-shell text is not classified
  - prove policy demotion removes the runtime block
  - prove top-level newline separation, shell redirection exclusion, and merge-mainline parent selection
  - prove an inherited `LAZY_HOST_ROOT` cannot override the structured fixture `working_dir`
  - prove clean and conflicting single-commit merge-tree outcomes
  - prove recovery commands remain allowed
- Must not:
  - touch a real host product branch or worktree during the fixture
  - rely on network access or a remote Git server
- Record completion:
  - fixture changes update this record and the SDD implementation map
- Related records:
  - `.lazy-harness/spec/platform/guidance-ladder.md`

## Regression contract

`.lazy-harness/scripts/self-test.py#check_project_command_boundary` creates an isolated temporary host and Git repository with a host-owned `level=block` policy.

Blocked cases:

- raw `git worktree add`, including shell aliases, `git -C`, and `cd ... &&` forms
- `git checkout -B ... origin/staging`
- `git switch -c ... origin/test`
- a raw worktree command after a top-level newline separator
- a conflicting single-commit cherry-pick on a destination-labelled promotion branch
- multi-commit promotion cherry-pick without one-at-a-time preflight

Allowed cases:

- `bun wt new <slug> --base <destination>`
- an ordinary local branch created from `HEAD`
- non-shell text containing a forbidden command
- `git cherry-pick --abort` recovery
- policy demotion/disablement removes the runtime block
- a clean single-commit promotion cherry-pick with ordinary shell redirection
- `-m/--mainline` selects the requested merge parent for preflight
- a clean single-commit promotion cherry-pick after automatic read-only merge-tree preflight

The fixture creates local `refs/remotes/origin/staging` directly, so it proves Git topology behavior without mutating a real host or using network access.

## Validation evidence

- 2026-08-04 focused import execution passed for `check_project_command_boundary()`, `check_jcode_agent_adapter()`, and `check_policy_machinery_v2()` after reviewer fixes.
- Python compilation, policy/capability audits, strict block-readiness, hard-stop promotion audit, record-lint, and `git diff --check` passed.
- 2026-08-04 independent high-effort review reproduced newline, redirection, merge-mainline, policy-rollback, and synthetic-bypass defects; all five are fixed and covered by focused regressions.
- Closing `lazy test` exposed inherited `LAZY_HOST_ROOT` overriding temporary fixture roots; both structural helpers now prefer the normalized payload root, matching runtime event ownership and making parallel fixtures deterministic.
- Final framework standard validation remains the closing work-unit gate after this last record mutation.

## Layer completeness matrix

| Layer | Independent semantic delta? | Judgement |
|---|---:|---|
| DDD | No | No domain/business vocabulary or invariant changed. |
| SDD | Yes | `.lazy-harness/spec/platform/project-command-boundary.md` defines the executable component contract. |
| BDD | No | No product UI/user flow changed; deny output realizes a host policy. |
| SSOT | Yes | Framework enforcement wiring is recorded in the framework SSOT; host semantics remain in host SSOT/policy records. |

## Implementation map

- Status: `post-review-focused-validation-passed-awaiting-standard`
- Test implementation:
  - `.lazy-harness/scripts/self-test.py#check_project_command_boundary`
- Protected implementation:
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-command-boundary.py`
  - `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh`
- Fixture flow:
  1. Create a temporary lazy-harness host and promoted block policy.
  2. Exercise identical normalized payloads for Pi/OMP-compatible shell names.
  3. Assert narrow block, allow, and policy-demotion rollback behavior.
  4. Assert newline-separated commands, redirection exclusion, and merge-mainline parent selection.
  5. Initialize a local Git topology with synthetic `origin/staging`.
  6. Assert clean merge-tree allow and conflicting merge-tree deny.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/project-command-boundary.md`
- Machine index:
  - graph id: `kg_project_command_boundary_test_20260804`

## Discovery capture

- Primary canonical record: this TDD record owns the regression scenario.
- SDD: independent component-contract delta, linked above.
- BDD: no independent delta.
- SSOT: independent enforcement-wiring delta only; no host rule is duplicated in framework SSOT.
- DDD: no independent delta.
- ADR: no independent trade-off beyond accepted ADR 0056.
- Planning: no deferred backlog discovered.
