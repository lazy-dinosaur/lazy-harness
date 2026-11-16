# Host validation ownership and observation isolation

## Rule digest

- Status: needs-review
- Layer: TDD
- Scope: framework-global
- Aliases:
  - host validation ownership
  - benchmark observation isolation
  - framework runtime inventory
- Applies when: testing runtime host/product hardcoding or read-only retrieval benchmark behavior
- Must: use manifest ownership on installed hosts without relaxing authoring-source scanning; observe only owned benchmark fixtures; detect real writes/deletes; retain copy-failure cleanup and canonical-input protections.

## Approved scope / source provenance

User approved separately reproducing/repairing the two downstream validation failures. Candidate is an independent clone at `/Users/lazydino/dev/lazy-harness.fix-host-validation-isolation`, branch `fix/host-validation-isolation`, clean reviewed base `34fdd7e657ca57a446fbba4bc84e7514ad8341be`. Original dirty source/index and retained releases are not edited. Reader transport was not available in this active session; bounded map/record/source fallback was used without paid calls.

No publication, commit/push, global installation, nine-host redistribution or Pi rebind is authorized here. Candidate/source green and isolated-host green do not certify an existing installed host was updated. Actual installed failures remain failures until admitted delivery/retest.

## Reproduction and required protection

The new narrow regression on the unchanged base produced **4 pass / 8 fail**: host-local script misclassification, unrelated canonical writer misattribution, ambient-root leakage, missing isolated allocation/copy-failure handling, and mutation/delete boundary cases. Preserve that red evidence; a legacy CLI support statement is not validation.

- `host-local`: an undeclared operator script on an installed host is not framework-owned merely because it lives under scripts.
- `managed-leak`: declared runtime hardcoding still fails; no token suppression.
- `framework-local`: authoring-source scan still covers new/unlisted runtime files.
- `explicit-local`: a manifest-explicit nested local path is owned and still checked; no blanket local-folder exception.
- `missing-manifest`: ownership cannot be silently assumed.
- `external-writer`: an unrelated canonical writer is preserved, not restored or blamed for a benchmark fixture.
- `graph-write/delete`, `cache-write/delete`: real changes in the observed fixture still fail, including deletion and presence changes.
- `environment`: child CLI root is pinned to the fixture despite ambient host variables.
- `copy-failure`: owned allocation is cleaned and the original failure survives.
- Real integration runs the actual hardcoding guard, existing copy-helper protection and benchmark CLI shape/semantic-authority assertions without mocked command output.

Unit AST probes use controlled dependencies and minimal temporary inputs; they are not benchmark/host acceptance by themselves. The unmocked integration and final standard receipts must be reported separately. Existing lifecycle cleanup tests and BOTH registrations remain unchanged. Root runtime tmp is excluded by the existing helper, nested canonical tmp is preserved, canonical dangling links fail closed, and no application/dependency tree is copied.

## Implementation map

- `.lazy-harness/scripts/framework-runtime-ownership.ts`: managedRuntimeItems, isManagedRuntimePath, collectRuntimePaths; reuse manifest-path-matcher.ts rather than reimplement glob/exclude semantics.
- `.lazy-harness/scripts/self-test.py`: existing hardcoding check consumes scope-aware inventory; existing benchmark check owns a temporary fixture and delegates preserved assertions to `_check_retrieval_workflow_benchmark_fixture` with explicit root/env and presence+bytes comparisons.
- `tests/lazy-harness/host-validation-isolation.test.ts`: red/green narrow cases and actual integration; existing `lifecycle-temp-cleanup.test.ts` protects allocation ownership.
- `tests/lazy-harness/host-validation-host-probe.py`: real standard host-mode gate in a disposable harness-only copy; models runtime gitignore and fixture-only HEAD history without application/dependency copies or source commits.
- `.lazy-harness/manifests/init-categories.json`: existing scripts/*.ts distribution includes the selector; TDD/SDD explanatory records explicitly distributed.
- `.lazy-harness/spec/platform/framework-validation-isolation.md`: internal contract; existing benchmark public CLI/output and tests are not redesigned.
- Graph: kg_host_validation_inventory_20261115, kg_host_validation_benchmark_20261115, kg_host_validation_protection_20261115. Existing legacy implementation-index schema is not migrated or unrelated entries overwritten; source/record/graph remain authoritative pending a typed derived refresh.

## Layer completeness

| Layer | Judgement |
| --- | --- |
| SDD | Independent internal inventory JSON and benchmark fixture/observation contract: framework-validation-isolation.md. Public benchmark CLI/result shape unchanged. |
| BDD | No independent end-user workflow delta; correctness and failure attribution of self-tests only. |
| SSOT | Existing Category A distribution ownership is consumed, not reassigned. No host-local source movement, global bypass or new policy activation. Manifest only links new explanatory records. |
| DDD | No domain term/business rule change. |

## Validation capsule

### Actual final receipts (2026-11-15; no cached PASS)

- Source/candidate cwd for every command below: `/Users/lazydino/dev/lazy-harness.fix-host-validation-isolation`, branch `fix/host-validation-isolation`, unchanged HEAD `34fdd7e657ca57a446fbba4bc84e7514ad8341be`.
- Baseline red: `bun test tests/lazy-harness/host-validation-isolation.test.ts`, 4 pass/8 fail across initial12 cases; log `/var/folders/97/c1s7nf4s6jq_l8zjmzbpp0640000gn/T/pi-fabric-shell-Q0gzo3/output.log`.
- Final focused: `bun test tests/lazy-harness/host-validation-isolation.test.ts tests/lazy-harness/lifecycle-temp-cleanup.test.ts`, exit0,25 pass/0fail,84 assertions,9.09s. Includes actual guard/benchmark/helper and canonical evidence preservation. Log `/var/folders/97/c1s7nf4s6jq_l8zjmzbpp0640000gn/T/pi-fabric-shell-HLOZcv/output.log`.
- `bun run typecheck:node`: exit0. `bun run build:node`: exit0. Focused helper/test tsc: exit0.
- Pi typecheck under `/opt/homebrew/opt/node@22/bin` Node22.23.3: exit0 after candidate-only submodule659cdc782bef43fd77a79bbc5e77a16ad61d22ab and frozen vendor workspace dependencies. Root/node/vendor locks and gitlink are unchanged. No global binding or live monitoring/model activation.
- `lazy record-lint --fail-on-issues --format=json`:211 inspected,211 clean,issue0,exit0 after correcting our initial Scope/alias digest errors. Prior failures remain in logs; they were not baseline-blamed.
- Isolated host: `PATH=/opt/homebrew/opt/node@22/bin:$PATH python3 tests/lazy-harness/host-validation-host-probe.py`, actual fixture cwd `/private/var/folders/97/c1s7nf4s6jq_l8zjmzbpp0640000gn/T/host-validation-isolation-70p553j9/host`. Child command `.lazy-harness/bin/lazy validate --plan standard --scope host --evidence-cache off --format json`, exit0,fullRegression=true,118.673s,59 checks ran/31 intentional framework-only skips/jobs4. Host-local product marker remained in undeclared operator script. ApplicationCopies0/dependencyCopies0; fixtureRemoved=true. Log `/var/folders/97/c1s7nf4s6jq_l8zjmzbpp0640000gn/T/pi-fabric-shell-QbAbg3/output.log`.
- This is a representative disposable **host-mode** gate, not a rollout or actual installed Medivance host gate. Probe setup originally failed on wrongly excluded canonical evidence, unignored Python bytecode, and absent HEAD; all failure receipts are retained. Canonical evidence is now preserved, runtime gitignore is modeled, and only the disposable fixture receives a hooks-disabled empty HEAD seed. Candidate/source/user worktrees receive no commits.

### Earlier failed checkpoints — resolved by the approved follow-up below

- Final source command: `PATH=/opt/homebrew/opt/node@22/bin:$PATH .lazy-harness/bin/lazy validate --plan standard --scope framework --evidence-cache off --format json`; exit1 after300.044s. Fast static exit0 over8 changed files; full regression exceeded remaining299.838s and supplied no stdout tail. **fullRegression=false**. Log `/var/folders/97/c1s7nf4s6jq_l8zjmzbpp0640000gn/T/pi-fabric-shell-jqyO3d/output.log`. Timeout is not evidence of a particular failing check and no budget bypass/skip was used.
- Proper Node22 `bun run test:pi-capture`: Node capture33 pass/0fail (88679ms); subsequent offline monitoring suite77 pass/1fail. The private metadata-log case hits ENOENT at monitoring-attach-phase1.test.ts:199. Standalone exact case also fails0pass/1fail/30filtered,94ms,exit1; log `/var/folders/97/c1s7nf4s6jq_l8zjmzbpp0640000gn/T/pi-fabric-shell-qlXeFm/output.log`. This component is unmodified and failure is preserved, not attributed to the two fixes or repaired outside scope.
- Initial blanket `bun run test:run`:265 pass/12fail/2errors,108.92s,exit1. Missing vendor was prepared, but that blanket command is not certified green. Eight native A/B cases throw before fixtures because LAZY_READER_NATIVE_SYNC/ASYNC inputs are missing. Framework owner confirmed no currently approved exact paths: old custom pi-subagents removal was user-approved, and historical paths are not authorization. No fake Fabric substitution, automatic skips or retired-native reinstalls. A/B-to-Fabric contract alignment requires separate approval. Other initial capture failures are preserved rather than silently discounted.
- Overall source/installed-host completion and publication remain **blocked**. Source standard timeout, separate offline log failure and legacy native-input failures are distinct receipts. No source/user delivery commits, push, global installation, nine-host rollout or Pi rebind occurred. Primary task21 remains in_progress; separate approval blocker23 is pending.

### Approved follow-up: current Fabric verification alignment

User selected option1 on this follow-up: align obsolete Reader checks to current Fabric, normalize canonical TMP, and use an explicit bounded full-source budget. Existing two-checker patch remains intact; source/user delivery commits, push, publication, global settings/runtime, host sync and Pi rebind remain excluded. Host-local deployment binding was read for removal history only and is not copied into the public source.

Changed preconditions, not source suppression: `TMPDIR=/private/tmp PATH=Node22 bun run test:monitoring-attach` passed78/78,392 assertions,8.10s (abbexg log). Exactly the same source/assertions. Then `TMPDIR=/private/tmp PATH=Node22 lazy validate --plan standard --scope framework --max-seconds 900 --evidence-cache off --format json` passed90/90,0skipped,jobs4,exit0 after approximately348s (JfU755 log). This source green predates the new process-fixture batch and is not a final claim about that batch.

Current published contract already supersedes Pi native subagents with request→unchanged Fabric spawn→content-bearing wait→ledger join; OMP native is untouched. Preserve the legacy matrix as explicit historical input-dependent verification rather than replace native env with Fabric paths. Default current coverage must run actual Pi/Fabric processes with deterministic offline models, actual production hooks and runtime ledgers, not inject proxy events. Pin a separate test runtime so the production0.85 SDK pin and global installs are unchanged.

Prototype actual current Fabric0.136/Pi1.5.2 first launched, read and delivered real content but rejected join: fresh child did not trust project packages, so no child guard/ledger was loaded. Failure logs ekKMTJ and D22IOm preserve it. Explicit trust ONLY in the disposable private agent settings loads the real project package and passes1 process scenario/9assertions/9.57s (IzUua3). No guard or runtime source patched, no fake lineage/proxy/counters. Keep missing-child-guard as an explicit negative case. Expand to JSON/text × wait/source-first × capture/placement only after this real compatibility proof; do not label historical native8 as executed.

Layer completeness for follow-up: SDD—no new production API/semantics; exercise existing Fabric contract. BDD—no new production behavior; protect current content join/primary answer and untrusted-child refusal. SSOT—test-only pinned runtime/setup commands, not installation binding/default model/production dependency reassignment. DDD—no domain delta. This existing primary owns execution receipts; Reader regression TDD owns current-vs-historical coverage. New test files are not implementation of a new Reader or new transport.

### Final approved follow-up receipts — candidate verification complete

All below are actual content-bearing exit receipts in the same candidate root; no cache-based full-regression reuse or deployment claim. Legacy native8 was not run or counted as current success. Historical failures above remain preserved, not erased.

| Gate | Actual result | Raw log basename (under `/var/folders/97/c1s7nf4s6jq_l8zjmzbpp0640000gn/T/`) |
| --- | --- | --- |
| `bun run test:run` | exit0;302/302 owned Bun cases across13 files,100.93s, then33/33 Node SDK cases,91598ms;335 total,0fail/cancel/skip; `1 passed` compatibility marker | `pi-fabric-shell-NnO66o/output.log` |
| `TMPDIR=/private/tmp bun run test:fabric` | exit0;9/9 actual current process cases,285 assertions,74.03s | `pi-fabric-shell-PuzXyI/output.log` |
| `bun run test:fabric:setup` | exit0;frozen lock,318 installs checked across332 packages,no changes,120ms; lifecycle scripts disabled | `pi-fabric-shell-N4AaFQ/output.log` |
| `TMPDIR=/private/tmp .lazy-harness/bin/lazy validate --plan standard --scope framework --max-seconds 900 --evidence-cache off --format json` | exit0;ok/fullRegression=true,evidenceReused=false,406.153s;90 ran/0 skipped/jobs4, actual Node26 default | `pi-fabric-shell-qoetxB/output.log` |
| `TMPDIR=/private/tmp python3 tests/lazy-harness/host-validation-host-probe.py` | exit0;actual child standard host300,ok/fullRegression=true,evidenceReused=false,119.281s;59 ran/31 intended framework-only skips/jobs4;app/dependency copies0,fixtureRemoved=true | `pi-fabric-shell-GlvuLK/output.log` |
| `bun run typecheck:node`, `bun run typecheck:pi`, `bun run build:node` | all exit0 after final behavioral batch | `pi-fabric-shell-RICIzi/output.log`, `pi-fabric-shell-dntNqf/output.log`, `pi-fabric-shell-YyTLT1/output.log` |
| Pinned provider tsconfig / Bun fixture-runner tsc | both exit0;no skipLibCheck/type suppression. Node22 type definitions match SDK declaration contract; Bun globals are not leaked into Node provider typecheck | `pi-fabric-shell-ofh2x5/output.log`, `pi-fabric-shell-dGcQP0/output.log` |

The final isolated host was `/private/tmp/host-validation-isolation-v3pdqmol/host`; it is removed. Last source check covers the final runner, matrix, record/graph and independent runtime lock batch. Subsequent changes are only this result capsule/history heading; final record-lint/static/diff check are repeated for those documentation changes, not another expensive semantic suite.

The original first pinned-runtime matrix hit provider API errors in the actual1.5.0 worker (no getCurrentSystemPrompt function); two100s failures were retained and the remaining repeated wait was stopped (bOIa7e log). The test provider now supports its legacy context alongside Parent1.5.2 transcript system messages and emits a proper terminal error, rather than suppressing the failure or extending a per-case deadline. The missing-guard/untrusted first red became the explicit negative. Production Reader/guard/writer APIs, safety boundaries and SDK0.85.1 dependency pin remain unchanged.

Owned full-suite routing fixes the previous blanket-engine mismatch: all currently owned Bun cases run on Bun, the Node-only SDK file runs on Node with CLI-supported flags, vendor workspace keeps its own suite, and the retired native matrix is byte-preserved with explicit execution only. New matrix success is not old native execution or live authenticated/model-semantic success. Source/candidate remains HEAD34fdd7e with uncommitted changes pending review. No source/user delivery commit, push, global install/config/trust, nine-host sync, actual Medivance installation or Pi rebind occurred. User approval scope is implemented and locally verified; delivery requires separate approval.

### Local review / commit-PR preparation (approved follow-up)

User selected review and local commit/PR preparation after verification. This does not authorize push, PR create/edit, merge, publication, global install or Pi/host delivery. Fresh direct HTTPS fetch from lazy-dinosaur/lazy-harness main resolves to the same reviewed34fdd7e baseline; no upstream delta/rebase is needed. Current branch is fix/host-validation-isolation, still uncommitted. GitHub lookup found no existing PR. Candidate origin points at the retained LOCAL source; it is not a GitHub push destination and must not receive a delivery push.

Main semantic review P2 (unresolved): scripts/test-runner.mjs only recognizes the Node-only SDK when it is the sole argument. Mixed explicit Node+Bun test paths fall through to Bun with the Node SDK file included, contrary to the owned engine-routing contract. A synthetic argv observer (no actual test suite executed) returned exit0 and `1 passed` while observing Bun argv `[test, tests/lazy-harness/pi-capture-evidence.test.ts, tests/lazy-harness/affected/covered.test.ts]`. Reproducer: `/private/tmp/lazy-harness-review.khgIRm/argv-probe.cjs`; exact source branch is `onlyNode = supplied.length === 1 ...`. The current regression tests cover only a sole Bun target and historical blob preservation; the335-case green does not cover this mixed-input branch.

No production/test implementation fix was made during this review. Commit is held pending disposition. Independent read-only semantic review was requested from the framework owner, with no permission to edit/retest/publish. Local Why/What/Task/Validation draft is `.lazy-harness/tmp/pr-review/host-validation-draft.md` (runtime artifact, not a new canonical rule). This existing primary owns the finding; no independent SDD/BDD/SSOT/DDD delta is introduced by recording it. Final review findings and user-directed disposition will be appended here rather than silently counting prior tests as review clearance.

Review-wait observation: the read-only intercom ask did not yield a verdict before its330000ms observation deadline. This is a wait timeout, not a negative review result, successful review or cancellation of the peer. Do not retry the same request or claim independent clearance. No implementation/index/commit/remote mutation occurred; blocker25 captures the required user disposition for the confirmed mixed-target P2. Existing verification remains evidence only for covered input paths.

Independent read-only review verdict received after the observation timeout: **NOT_READY_FOR_COMMIT**, two P2 findings. (1) scripts/test-runner.mjs:21-27 independently confirms mixed explicit Node+Bun and Node-file-plus-options reach Bun; target/option separation or explicit rejection plus regressions is required. (2) packages/lazy-harness-pi/tests/fixtures/fabric-cli-runner.ts:51,102-105 always signals even the already-closed successful child's old process group, and timeout/error cleanup does not await bounded physical settlement after TERM. Delayed/ignored TERM can leave a child; PID/PGID reuse can target an unrelated group. This is source-based risk, not a reproduced orphan/PID-reuse incident. Required disposition: verify live ownership, await bounded close/escalate, and protect normal no-signal, timeout and ignored-TERM cases without broad pkill; preserve failure logs.

Reviewer found no additional blocker in the two checkers, manifest matching, owned benchmark isolation, runtime pin/frozen setup or current proxy/ledger and byte-preserved legacy handling. Limits: no new test execution, actual timeout/PID reuse/other platforms/transitive npm source not verified; this is a working-tree review, not future-head clearance. No source edits/commit/remote mutations. Both findings supersede the earlier pending-review status and must be fixed/reviewed or explicitly dispositioned before any commit. User option gate now covers both narrow test-infrastructure issues, not new production Reader logic or rollout.

User explicitly selected1 after both independent P2 findings: implement only engine target/option partition plus regression and owned-child termination/physical-settlement plus regression, then re-review and local commit/PR preparation. Global/runtime/native transport behavior, push/PR mutation/merge/rollout remain excluded. Use ChildProcess live ownership instead of stale numeric process groups; preserve the original failure and synthetic logs if cleanup cannot settle. Regression matrix covers mixed targets/Node flags/path normalization/unsupported-option fail-closed, normal-close no signal, TERM shutdown and ignored-TERM escalation. This is an internal test-tooling repair; no independent production SDD/BDD/SSOT/DDD delta, and the existing primary owns evidence.

P2 coherent repair batch: test-runner now normalizes concrete paths, expands requested directories, separates shared name-pattern flags and targets, and independently invokes Node/Bun. A Node lane rejects Bun-only timeout/unknown aggregate options before any engine starts; no silent loss/guessing of flags. Node capture forwards the translated name filter before the file. `fixtures/owned-child.ts#observeOwnedChild` observes the close/error lifecycle immediately after spawn; signals only a still-live ChildProcess handle (never saved numeric PID/negative PGID), awaits physical close, escalates ignored TERM to KILL with finite deadlines, and fails closed for inherited pipes that cannot settle. Current Fabric runner awaits that settlement and preserves an earlier failure/log rather than overwriting it with cleanup failure. No claims about all detached descendants/PID-reuse incidents or non-POSIX behavior are made.

Focused first red (zT5hK9):2 pass/9fail/1import-error, before routing/owned-child implementation; missing new helper is an explicit setup error, not a reproduced PID-reuse accident. Post-batch WAoPN1:16 pass/0fail,58 assertions,1.417s, including actual direct children normal/no-signal, graceful TERM, ignored TERM→KILL, exited-parent inherited-pipe no-signal, bounded unsettled-pipe refusal, and spawn error. Routing covers mixed files, absolute/relative/backslash paths, Node+pattern, directory and unsupported Node flags; argv observer runs no semantic suite. Source/test changes are narrow; existing checker/Reader/writer/guard/publication boundaries unchanged. Independent read-only re-review and full verification remain pending for this new fingerprint.

Implementation map addition: `packages/lazy-harness-pi/tests/fixtures/owned-child.ts` — `observeOwnedChild` owns lifecycle observation and bounded settlement; `tests/lazy-harness/owned-child-settlement.test.ts` protects actual process behavior. `scripts/test-runner.mjs#planTestRuns` separates concrete target/option lanes and is exercised by the existing routing regression. Node-only CLI filtering remains in `scripts/test-pi-capture.mjs`. No production API/domain/behavior delta is introduced; this primary TDD and current Reader test contract own the test-tooling assertions.

P2 final execution receipts on frozen6-code-blob fingerprint (no subsequent behavior edits): focused17/0,62 assertions,4.28s (AHNgBD), including the real mixed Node/Bun filtered subprocess; aggregate `bun run test:run`317/0Bun across14files95.16s then33/0Node82441.819ms,total350,exit0 (pwgP8y). Final `TMPDIR=/private/tmp .lazy-harness/bin/lazy validate --plan standard --scope framework --max-seconds 900 --evidence-cache off --format json` exit0,ok/fullRegression=true,evidenceReused=false,352.605s,90ran/0skip/jobs4 (zVrVbT). Final `TMPDIR=/private/tmp python3 tests/lazy-harness/host-validation-host-probe.py` exit0,fullRegression=true,107.064s,59ran/31framework-onlyskip/jobs4,application/dependencyCopies0,fixtureRemoved=true (uH6Pgl); actual disposable host `/private/tmp/host-validation-isolation-phkdfinn/host`. All raw log basenames are `pi-fabric-shell-<name>/output.log` under the same previously recorded temp root.

Post-P2 typecheck:node/typecheck:pi/build:node all exit0 (5gdonL/EHXl0P/DEA4jC); expanded typecheck:fabric-tests exit0 (f86aVh). Stable code blobs in order router/capture/owned-child/fabric-runner/routing-test/settlement-test:05e3c7cc32097e8b71adcfd362f55c2c80d30a8d,6e42ce4ad9add2433fa2c40d543b72de69ca39c4,99c303c1ad16d38a655227d0c8606eeb6b0194dd,3b26ee6c0121f6a0ad6f300ac61871b0d5f60a25,4a059000817be52de5f2710ee0182eee7ee54304,8f418eb88e99807e5afd1f062ec36bf952cb7b35. Independent re-review was requested on these exact sources and remains pending at this checkpoint. Existing NOT_READY is not silently converted into review clearance merely because tests pass. No commit/index/remote/global/installed-host mutations.

Independent read-only final disposition consumed (raw response UHz6gN/output.log): both original P2s are resolved on the six exact frozen blobs; no remaining P2 in that scoped re-review, and the two-item NOT_READY is withdrawn. Reviewer twice checked actual Git blobs and read actual focused/aggregate/type/source/host receipts; no additional suite or source mutation was performed by reviewer. This is working-tree scoped clearance, not approval of future heads, publication/global/live delivery or authenticated retrieval.

Non-blocking P3 retained without scope expansion: the actual live-child regression tests themselves lack a cleanup try/finally independent of the CUT. A future CUT regression or early assertion failure could bypass settlement and leave a synthetic interval child. No actual orphan/PID-reuse incident was reproduced; all current passing paths settle. Follow-up recommendation is a separate bounded test-cleanup insurance; it is not a remaining P2 and was not silently fixed/re-scored in the frozen implementation. Other platform/transitive dependency limits remain.

Local review/commit-PR preparation is complete, not actual commit or submission. Latest direct GitHub main fetch still resolves34fdd7e and candidate HEAD remains34fdd7e; original local retained origin is not a push destination. Candidate-local .git/info/exclude now excludes only `.lazy-harness/tmp/pr-review/` in addition to dependency ignores, so private draft/status/commit-message/staging-manifest artifacts are outside the submission. No tracked code/index/commit/remote mutation accompanies this metadata step. Proposed atomic classification: Fix, layers scripts/tests/docs/infra, no hospital-staff-visible feature change. A future commit must stage only the explicit26-file submission manifest and follow the user's separate actual-action approval; push/PR create/edit/merge/global/Pi/host rollout are not implied by review clearance.

User explicitly selected local commit option1 after scoped review clearance and the non-blocking P3 disclosure. Approval now permits one local Fix commit of the explicit26 submission files on fix/host-validation-isolation, with no P3 expansion, push, PR mutation, merge, global/Pi changes or installed-host delivery. The reviewed six implementation blobs and functional verification remain unchanged; only this approval receipt is added before staging. The resulting commit SHA belongs in the local commit receipt/Git history rather than a self-referential source edit.
