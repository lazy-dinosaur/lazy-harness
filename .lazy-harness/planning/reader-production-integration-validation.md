# Reader production integration validation

## Rule digest

- Status: active
- Layer: Planning
- Scope: host-project
- Applies when:
  - resuming the user-approved isolated Reader integration verification
- Must:
  - preserve existing main work and interrupted candidate changes
  - confine integration mutations to the disposable candidate
  - verify combined behavior rather than substitute earlier benchmark results
  - obtain separate approval before commit, push, main merge, install or settings changes

## Confirmed scope and interruptions

User approved integration preparation/verification and explicitly requested continuation after accidental termination. No new paid benchmark or activation is authorized.

Candidate `/tmp/lh-reader-integration-validation-301g6zau/candidate` is a disposable clone, branch main at `58fbcbf5e9d632bf9b0e7a87857ad8ed05f01f7b`. That branch name does not authorize changing the real main checkout. Partial state is preserved in `interrupted.patch`, `interrupted-status.txt`, `retry2.patch`, `retry2-status.txt`; input hashes in `source-hashes-before.txt`.

Worker30186647 stopped during preparation without final verification. Resume lookup was unavailable; a later request rejected acceptance:false, and the next same-protocol attempt was aborted (mission0e3e8064-a8be-42c7-90fc-c33fe85b6bb7). User confirmed accidental termination and asked to retry. Retain failures; continue the same subagent protocol, not an unapproved external CLI fallback.

## Remaining sequence

1. Verify partial candidate and source preservation; do not discard/reclone.
2. Reconcile Reader delta with all main-only policy/capability/manifest work. Eleven record conflicts largely concern chronological status and added scenarios. Preserve valid JSONL additions and stop on genuinely conflicting facts; do not bulk migrate legacy rows.
3. Align candidate AGENTS join guidance with automatic runtime-owned path/counter defaults, retaining identity/hash/assertion protections.
4. Run combined SDK/accounting/delivery/native fixtures, resolved host TypeScript, focused package regression and final standard validation. Preserve failed checks and distinguish fresh versus cached validation.
5. Review candidate and request separate publication/activation approval.

## Risks and evidence

Installed native runtime plus new harness failed genuine offline CLI verification: Parent exited approximately6.54s before Reader completion. Tested patched native runtime passed. Both declare0.66.0, so version text alone does not establish compatibility. Global harness binding references actual main; native binding is npm. Paired distribution/rollback remains undecided.

Latest read-only benchmark retained two grep-prefix errors and one semantic error; it does not prove TUI/code-writing/deployment readiness. Legacy37graph migration remains separate and may be resumed through a user-approved guided batch, not this integration.

## Implementation map

- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — Reader identity, full-ledger join and fallback.
- `.lazy-harness/AGENTS.md`, `packages/lazy-harness-pi/prompts/lazy-harness.md` — candidate invocation guidance alignment.
- `.lazy-harness/scripts/self-test.py`, `.lazy-harness/tests/pi-agent-package.md` — combined regression protection.
- `.lazy-harness/spec/platform/search-read-debt-contract.md` — existing join contract.
- `.lazy-harness/evidence/reader-coordination-repair-and-comparison.md` — historical verification and current findings.
- `/tmp/lh-reader-integration-prep-q6oyf1oh/report.md` — conflict/compatibility evidence.
- `/tmp/lh-reader-native-followup-hf9m835b/pi-subagents` — read-only patched runtime and test input.

## Discovery capture

| Layer | Disposition |
|---|---|
| DDD | none — no new domain definition |
| SDD | none — existing contract reused; combined verification pending |
| BDD | none — existing delivery/fallback scenarios reused |
| TDD | none — regression execution pending; no new passing claim |
| ADR | none — distribution decision not made |
| SSOT | none — installed ownership/settings unchanged |
| Planning | updated — confirmed scope, interruptions and remaining steps captured here |

This bounded execution plan is not a new general operating policy or a completion claim.

## Final-check checkpoint and approved continuation

Run `ecf06bcb-256d-48c3-bead-0a9d01043e61` timed out after 1,200,000ms. Candidate state remains preserved in `timeout.patch`, `timeout-status.txt` and `timeout-checkpoint.json` under `/tmp/lh-reader-integration-validation-301g6zau`. No deployment readiness claim follows from the timeout.

Observed child transcript evidence: initial SDK invocation failed because LAZY_READER_HOST_ROOT was omitted; corrected candidate-root invocation passed 31 tests/266 assertions in 15.48s. TypeScript and focused package checks passed. `final-standard-clean.json` reports PASS75.638s with fresh full regression. Exact final-file coverage after restoration and original-source preservation remain to be confirmed; retain initial failures.

User selected same-work continuation restricted to final checks/report. Native resume succeeded as `e368fed1-6933-42cf-bb0e-2f6cba906d8f`. Remaining work: verify final candidate hashes and source preservation, finalize per-file merge dispositions and patch, then independent review. Do not restart implementation or change deployment/settings.

The candidate-ID concern was a false conflict: all three sources contained the identical ordered four-event history for `candidate-capture-gate-post-judgement-runtime-conflict-20260714`. Preserve every event unchanged; do not collapse by entity ID or reopen resolved decisions.

### Discovery capture — checkpoint delta

- DDD: none — no new domain definition.
- SDD: none — existing contract unchanged; verification evidence is not a new API contract.
- BDD: none — existing scenarios unchanged.
- TDD: none — execution results captured in this checkpoint; exact-final coverage still pending, no new regression specification.
- ADR: none — no distribution or architecture decision made.
- SSOT: none — installed ownership and settings unchanged.
- Planning: updated — timeout evidence, user-approved narrow resume, and remaining final checks recorded here.

### Worker completion and independent review

Resumed worker delivered `/tmp/lh-reader-integration-validation-301g6zau/report.md` and `final.patch`. Post-restoration native suite reports 31 tests/266 assertions passed in9.37s. Parent independently checked patch SHA-256 `56094d52945e39632b30763e579b9cb89b248815c3c4d349b931489e86ee402e` and standard-result SHA-256 `d6c82e63db52e951642d330600512730c06246aa7bf74509adaa7d8b5dce7223`, and `git diff --check` passed. These checks do not establish semantic merge correctness.

Worker preservation report documents main validation-ledger drift; all-source byte immutability must not be claimed. Parent corrected report wording: omitted-environment initial test was an accidental invocation failure, not an expected negative test. Read-only independent reviewer `f434db64-5a32-4c62-8d56-3bf5b758ed1c` is examining merge fidelity, automatic-default guidance, native pairing and patch/evidence integrity. Preparation remains pending independent review; deployment remains unauthorized.

Discovery capture: Planning updated with completion receipts and review status. DDD/SDD/BDD/TDD/ADR/SSOT none: no new definitions, contracts, scenarios, regression requirements, design decisions or ownership changes at this evidence-only checkpoint.

### Preparation-only closure

Independent review `/tmp/lh-reader-integration-validation-301g6zau/independent-review.md` returned OK with notes, no actionable findings, for preparation only. Reviewer examined eleven conflict resolutions, generated-index mapping preservation, runtime/default guidance, and native pairing. Reviewer did not rerun tests or all 1,584 preservation hashes; those limitations remain.

Parent separately resolved the patch-applicability evidence gap: copied the 34 affected paths from current main into `/tmp/lh-reader-integration-validation-301g6zau/parent-apply-check-6awo78y6`, ran both `git apply --check` and actual `git apply` there successfully, and compared all affected results to candidate bytes/symlinks/executable bits: zero mismatches. Receipt: `parent-apply-verification.json`. This verifies affected-path equivalence, not whole-tree byte/mode equivalence. Actual main was not patched.

Task349 preparation/validation is complete. Installed native compatibility/distribution and separately authorized activation remain unresolved; no commit, push, installation or production merge is approved or performed. Benchmark semantic and grep-prefix limitations remain unchanged.

Discovery capture: Planning updated with independent-review disposition, Parent patch-application receipt and preparation-only closure. DDD/SDD/BDD/TDD/ADR/SSOT none — no independent semantic delta.

### Maintenance concern — discussion only, no activation approval

User questioned the maintenance burden of carrying a patched pi-subagents dependency across upstream updates and asked whether unmodified upstream or another approach can work. This is requirements discussion, not approval to activate the prepared pair or implement an alternative.

Confirmed evidence is narrow: the tested installed-native version failed the chosen delayed asynchronous CLI delivery fixture, while the patched copy passed. This does not prove every integration with unmodified pi-subagents is impossible.

Unverified alternatives for comparison, not selected plans: use unmodified pi-subagents with a blocking/foreground child contract if it can deliver complete content; own a dedicated Reader invocation outside pi-subagents while accounting for the resulting lifecycle/cancellation/cost ownership; retain direct Parent reads to avoid the dependency change. No alternative has been tested or adopted in this checkpoint.

Discovery capture: Planning updated with the user's maintenance concern and bounded unknowns. DDD/SDD/BDD/TDD/ADR/SSOT none — no confirmed new contract, behavior, regression requirement, architecture choice or ownership change. Existing patched-pair validation remains historical evidence, not proof that a fork is necessary.

### New comparison request — scope/budget selection pending

User requested testing unmodified synchronous Reader against the patched asynchronous Reader and is willing to accept additional maintenance if the repaired approach proves preferable. This confirms comparison intent, not an unconditional deployment or external-dependency ownership decision.

Proposed sequence: first run offline compatibility/delivery/integrity preflight on disposable copies. If unmodified synchronous execution cannot satisfy the same actual-content, full-ledger and failure-accounting guarantees, stop and report that specific failure instead of silently patching upstream or weakening the join. If feasible, freeze identical task/source/model/budget inputs and only the declared necessary integration differences; alternate execution order and collect fresh results for both arms. Historical benchmark results are context, not a newly paired control.

Compare semantic answer quality, complete content delivery, fallback/tool failure counts, end-to-end latency, actual priced Parent+Reader usage and Parent peak context. Use independent blinded scoring and preserve every failed attempt. No implementation decision solely from a small-sample average. Native compatibility preflight does not certify TUI/code-writing/restart deployment readiness.

Proposed paid measurement/scoring choices, awaiting user selection: 6 questions ×2 repetitions ×2 Reader arms =24 attempts, $30 ceiling; or add direct Parent baseline for36 attempts/$40; or first6 questions ×1 repetition ×2 arms =12 attempts/$15 exploratory only. These are proposed ceilings, not predicted expenditure or previously available budget. Interactive preparation/control overhead is separate. No paid experiment has started. Source/upstream installations remain unchanged.

Discovery capture: Planning updated with confirmed comparison intent and pending experimental choices. DDD/SDD/BDD/TDD/ADR/SSOT none — no alternative implementation contract or dependency deployment decision adopted. Test strategy reused; a selected executable protocol must pin the guarantees and budget before measurement.

User-confirmed selection: two Reader arms, 6 questions ×2 repetitions ×2 arms =24 maximum measured attempts, $30 total measurement/scoring ceiling (preparation/control overhead separate). User explicitly reiterated speed comparison: measure end-to-end launch-to-substantive-answer time including Reader waiting/join/fallback, report paired per-question deltas plus mean/median/range. Reader-only time is supplementary, not the primary speed claim; small-sample tails are descriptive only. Existing quality, failure, cost and context measures remain. Scratch root `/tmp/lh-reader-sync-async-2T2VQR`; offline compatibility and preparation come before paid execution. Planning updated; no other layer decision.

### Offline preparation infrastructure blocker

Worker `b5c5208a-dd19-485c-8251-de5135d33a04` (workflow `03466292-fa72-49d4-a3c0-c104906a934d`) reports ambient pi-lens postprocessing applied unsolicited autofixes to copied host/native trees, including syntax-breaking changes and pipeline crashes. Exact-arm byte guarantees therefore cannot currently be claimed. No SDK tests or paid benchmark calls have run, according to the worker. Original-input preservation and detailed attribution await the checkpoint receipts.

Supervisor request `480d442d-6915-4f50-8c57-d022e8d13511` answered: stop with structured blocked verdict; preserve initial manifests, drift inventory, partial patches and errors; do not restore while autofix is active or change global settings/execution protocol. Review/measurement stages must not proceed. Any remediation must be scoped to non-mutating postprocessing and explicitly verified before a same-protocol retry. This is an infrastructure blocker, not evidence that synchronous Reader on unmodified upstream is infeasible.

Discovery capture: Planning updated with blocker and preservation/stop instructions. DDD/SDD/BDD/TDD/ADR/SSOT none — no new domain, Reader contract, behavior or deployment decision; root-cause confirmation and remediation selection remain pending.

Checkpoint finalized: workflow `03466292-fa72-49d4-a3c0-c104906a934d` returned `preparation-stopped`; child completed its blocked report, not the experiment. A queued earlier follow-up expired after child termination; supervisor stop instructions were separately acknowledged. No retry or execution-mode switch occurred.

`/tmp/lh-reader-sync-async-2T2VQR/preparation-handoff.md` reports 404 changed copied-path instances (93 host +109 native per arm). Available initial content/mode/symlink manifests match original inputs, excluding .git/node_modules/__pycache__ and dependency symlink targets; no blanket all-environment preservation claim. Drift patches and raw postprocessing logs are retained. Measurement/scoring calls:0. No supported session-local non-mutating switch was established; the minimal remaining prerequisite is read-only investigation of that isolation path before restoration/revalidation. Planning updated; DDD/SDD/BDD/TDD/ADR/SSOT none at this checkpoint.

### Read-only isolation investigation

Installed pi-lens `docs/settings.md` documents three project-scoped mutation controls: `format.enabled`, `autofix.enabled`, `actionableWarnings.autoFix.enabled`. Setting all three false in a disposable `.pi-lens.json` can disable formatting/autofix without disabling diagnostics. Installed `dist/clients/project-lens-config.js#findNestedProjectMutationValue` searches from the edited file to its project root; `dist/clients/lens-config.js#resolvePiLensFlagWithSource` confirms project/nested precedence over global defaults, with truthy CLI flags taking precedence. No nested .pi-lens.json/pi-lens.json was found in current scratch copies during inspection.

This is a supported disposable-project configuration route, not a proven session-only switch or a guarantee covering all pi-lens side effects. Proposed next step: apply controls only to experimental roots (including each copied host/native root so nested Git roots cannot hide the config), then run a tiny write/postprocessing hash probe before restoring fresh source copies and retrying the same subagent protocol. Existing contaminated copies stay preserved. No settings have been changed by this investigation; global settings and installed packages remain outside mutation scope.

The 404 changed paths establish byte drift, not 404 behavioral regressions. Behavior equivalence and reported syntax failures were not independently established. Discovery capture: Planning updated with evidence and proposed bounded remedy; DDD/SDD/BDD/TDD/ADR/SSOT none pending adoption.

User explicitly approved experimental-folder-only mutation controls and same-protocol resumption, retaining 24 attempts/$30. Parent placed identical `.pi-lens.json` controls (`format.enabled=false`, `autofix.enabled=false`, `actionableWarnings.autoFix.enabled=false`) at scratch root and each existing A/B host/native root. No global config or installed package was edited. Effective non-mutation still requires a small child-runtime probe before recopy/testing; configuration presence alone is not a passing test.

Discovery capture: Planning updated with bounded remediation approval and exact local configuration paths. SSOT none — disposable experiment setup only, no host/global policy or ownership delta; DDD/SDD/BDD/TDD/ADR none.

After native completion of `571d8052-842a-4a17-aeae-2b8ed86df3a4`, Parent independently hashed the deliberately unformatted TS probe: SHA-256 `fca07812892c0ffd506b53a1c30bc9eedb6bb462a1f0150260f67908e6434666`, matching initial/post-tool hashes. Receipt `evidence/parent-after-terminal-probe-check.json` under experimental root records the narrow boundary PASS, not universal non-mutation proof. Same worker resumed as `3b22847d-9abe-49d0-8675-e6ae1de66c66` for fresh-copy manifest verification and offline synchronous viability/preparation only. Paid measurement remains gated by preparation review. Discovery capture: Planning updated; all six canonical semantic layers none (execution evidence only).

Offline fixture checkpoint: worker reports retry-01 copied sources remained equal after postprocessing, and patched-async native launcher passed30assertions before fixture correction. Unmodified-sync invocation reached native execution but could not discover the scripted test provider through foreground child-only extension loading; this is a fixture setup failure, not a proven Reader delivery failure. Supervisor request `57c3923b-73d9-4f93-ad39-9285bbd0d0ba` approved an identical sandbox-only provider registration via subagentOnlyExtensions in both arms, preserving production body/tools/host extension and network guard. Both actual invocation paths must be rerun with the same fixture; native bytes, trusted ledger checks and paid agent definitions must remain unaffected. Failed attempts retained; no paid calls authorized at this stage. Discovery capture: Planning updated with fixture correction and validation boundary; DDD/SDD/BDD/TDD/ADR/SSOT none — no adopted production contract or regression-policy delta.

Worker reports exact-arm offline viability PASS:14 real CLI Parent→native Reader→join tests,471 assertions across identical scripted-provider fixtures. Tested negatives include wrong run ID/stale epoch/counter assertions/unread paths/post-read hash change/failed-read accounting; subset assertions retain full actual-read hashes. ArmA native remains unmodified; adaptation is host-side sync launch gate and receipt-delivery mapping. This is not live speed/quality evidence.

Supervisor request `4adb6301-fd0e-4873-b06d-12c11c35aa4c`: accepted a bounded intermediate handoff containing viability receipts, frozen six questions/24 balanced slots, offline runner/tests and protocol. It is explicitly NOT measurement-ready: live execution entrypoint and defensible pre-admission $30 budget controls remain missing. Historical post-call budget estimates do not prove a hard ceiling. Existing experiment approval remains valid; no paid calls, scope expansion or blanket completion claim. Parent to review and continue the smallest missing live-admission slice, not create a new framework. Discovery capture: Planning updated with evidence and remaining blocker; DDD/SDD/BDD/TDD/ADR/SSOT none — experimental adaptation is not adopted production behavior.

Offline checkpoint completed: `retry-01/frozen/protocol.md` and preparation-handoff.md explicitly remain not measurement-ready. Offline suite14/471 and runner10tests are reported PASS; freeze1923entries has manifest SHA-256 `c08c94ddfe654c3ea5474178ec926b3568bad071efe42c01dcfb9c47aac91415`. Seven historical reference rows have current-source hash drift needing scorer evidence validation, not automatic oracle rejection or blind reuse. No live attempts occurred.

Same worker resumed as `df323457-b12d-440a-81ec-9deb1557bbd1` to finish the smallest live admission/execution slice, first checking whether actual openai-codex provider requests honor output bounds sufficient for the approved ceiling. Generic SDK options or abort are not assumed hard cost control. If unsupported, report that concrete blocker before building more budget infrastructure. Paid calls remain prohibited until fresh acceptance. Planning updated with remaining work; DDD/SDD/BDD/TDD/ADR/SSOT none (no production adoption).

Provider-budget blocker reported by worker: both selected models route through installed openai-codex-responses. Eight offline serializer calls reportedly omitted output-limit fields despite maxTokens1/37; intercepted synthetic42-token responses were accepted. This is local SDK serialization evidence, not a remote backend enforcement test. Registry128000 maximum is not treated as a billing guarantee; arbitrary onPayload injection is unverified.

Supervisor request `dda08f96-94c7-4c35-b29c-4382cd47cf72` answered: stop with precise versioned evidence; no paid calls, speculative provider patch or broader executor build. The unresolved issue is the approved strict $30 pre-request ceiling, not A/B Reader viability. Changing it to monitored expenditure with possible in-flight overrun requires user confirmation; existing approval must not be silently reinterpreted. Discovery capture: Planning updated; DDD/SDD/BDD/TDD/ADR/SSOT none — no provider contract change or budget relaxation adopted.

User explicitly selected monitored actual-spend operation: $30 becomes a target, with possible in-flight overrun accepted; strict guaranteed ceiling is superseded, not retroactively satisfied. `approval-monitored-budget.json` preserves this amendment alongside original approval. Parent operational allocation reserves $5 scoring headroom and stops new measurement work conservatively before $25 observed spend, considering outstanding requests; these are admission targets, not provider-enforced caps. Twenty-four maximum attempts, unchanged arms/models/questions, no measured retries, full end-to-end speed and actual actor accounting remain. Fresh preparation acceptance is still required before paid execution.

Live worker `df323457-b12d-440a-81ec-9deb1557bbd1` received a queued follow-up with amended scope; delivery is not yet confirmed. Preserve provider-bound failure evidence, then finish minimal monitored executor rather than building a new hard-cap framework. Discovery capture: Planning updated with user-confirmed budget amendment; DDD/SDD/BDD/TDD/ADR/SSOT none — experiment-only budget choice, not production provider or ownership change.

Monitored executor handoff delivered under `monitored-01/`: real scripted A/B runner/scorer/admission-denial E2E reported PASS,9 Python tests and4 tool-envelope tests/17assertions PASS; freeze18325entries/163availabledependency packages SHA-256 `98103033c11cfb1182e1b5da4305de0e198120b22147b631db3ef735482a28f4`. These are offline fixture results, not measured speed or actual billed spend. No acceptance file or paid calls yet.

Fresh read-only reviewer `3a32d5e2-3c46-44db-b0eb-10ad6fedf36b` now checks actual monitored run.py/monitor.ts, endpoint/cost integrity, confinement, frozen arm fairness, blind scoring and no-retry admission. Parent read PROTOCOL.md; observer overhead/censoring/partial pairs and accepted budget overrun remain explicit limitations. Discovery capture: Planning updated with implementation handoff and pending preflight review; DDD/SDD/BDD/TDD/ADR/SSOT none — experiment machinery is not adopted production behavior.

Sleep/review recovery: user confirmed laptop sleep during reviewer interval. Empty Markdown output did not mean no review: structured artifact for `3a32d5e2-3c46-44db-b0eb-10ad6fedf36b` contains BLOCK with twoP1 and twoP2 findings. Parent recovered the verdict to `monitored-preflight-review-recovery.md` and directly confirmed unguarded failure-path logging in monitor.ts and broad denial reconciliation waiver in run.py. Preserve these findings; sleep does not negate code evidence. No paid trial had begun, so no measured run needs replacement.

Same worker resumed as `3141a5ea-3ea0-43a1-bea0-d05fa8ce9ab2` for a bounded repair: fail-closed monitor exception paths, narrow clean-denial handling without masking integrity/usage/actor failures, blinded final-endpoint adjudication before speed aggregation, and effective search-binary pinning. Keep prior freeze/evidence historical, add focused fault injections and final offline runner/freeze receipts, then targeted reviewer followup before paid acceptance. Discovery capture: Planning updated; DDD/SDD/BDD/TDD/ADR/SSOT none — experimental instrumentation fixes not adopted production behavior.

Repair handoff delivered in `monitored-02/`, preserving rejected monitored-01. Worker reports16Python tests,5Bun tests/29assertions,6actualCLI admission/settlement fault cases and realA/B/scorer E2E PASS; final report separation covered by units/artifact recheck. Newfreeze SHA-256 `7ce28140f8f72d57d00401b9a38dbfc646aa97631dea2054fa64a4ff5be8c74e` (18331entries,163availablepackages). These are offline receipts; measuredattempts0/24, no paidacceptancefile.

Targeted same-reviewer followup resumed as `ac3dba4d-a0ca-458a-83c5-113b6f931139`, scoped to four fixes and introduced risks, including lazy first-denial session handling and blind endpoint adjudication. Read-only, no paid calls. Discovery capture: Planning updated with new candidate identity and pendingreview; DDD/SDD/BDD/TDD/ADR/SSOT none — experimental instrumentation not production policy.

Targeted reviewer completed with structured READY/no findings for monitored-02. Parent read full structured result, independently ran `python3 run.py verify` returning reviewed SHA-256 `7ce28140f8f72d57d00401b9a38dbfc646aa97631dea2054fa64a4ff5be8c74e`, confirmed empty runs directory and wrote exact-freeze review-acceptance.json. This is pilot acceptance only, not deployment.

Task351 preparation complete; task352 actualpilotexecution in progress. Fresh execution-only worker dispatched within workflow `d1235c6d-ed59-4772-ae04-08ad3440475b` (mission `b600e89f-2a07-4d75-914e-790f2809032e`) to run frozen measurement once, score only if admission permits, and report actual speed/quality/cost/context. Paidcalls authorized under existing monitoredtarget amendment; no retry, repair, newfreeze or environmentchange. Dispatch is not evidence any measuredslot has completed. Discovery capture: Planning updated with review/acceptance/execution identity; DDD/SDD/BDD/TDD/ADR/SSOT none — experimental execution only.

Live pilot stopped after slot01 A/short-fact: executor reports integrity error `missing/duplicate native launch or Reader`, no Reader/join/endpoint candidates, known Parent cost$0.168078, empty outstanding map but total attempt pricedUSD unknown, credentials removed. Exit0 represents controlled integrity stop, not success. No retries or scoring performed; no paired comparison exists.

Supervisor request `a85f0daf-a28f-4e3b-9b19-d7eda36ab1a9` authorized frozen report once plus read-only reconciliation/handoff only. Scoring and all further model requests remain blocked. Preserve raw Parent/tool/monitor events and identify launch failure only from existing artifacts; do not silently fix/restart. Task352 remains incomplete. Discovery capture: Planning updated with failed firstattempt and remaining evidence task; DDD/SDD/BDD/TDD/ADR/SSOT none pending diagnosis.

Failure reconciliation completed: actual Parent requested subagent discovery (`action:list, capabilities:true`), then the prescribed synchronous Reader launch; both were denied by the experimental monitor, followed by one denied git-status probe. Parent source inspection of monitored-02/monitor.ts:86–90 confirms unconditional `++launches` before argument validation: discovery consumes the only launch allowance, so the subsequent real launch is rejected. This is a comparison-guard defect, not evidence against original native synchronous delivery.

Normalized toolFailures was empty despite3 raw isError tool executions/guard denials; tool-result-only collection misses blocked tool calls. Preserve both normalized output and raw facts, do not silently replace historical results. One attempted A slot failed in31.69601354s terminal time, no substantive latency or usable pair;23slots unattempted. Known Parent usage$0.168078, Parentpeak10933tokens; total attempt integrity remains unknown. No speed/quality superiority conclusion.

Candidate repair scope for user confirmation: keep discovery read-only and separate from real launch admission; increment launch allowance only for validated admitted launches; collect blocked-tool failures without double counting; add realistic discovery→launch and blocked-tool reporting regressions. Original no-retry matrix stays terminal; any replacement live pilot requires explicit authorization/new version. Discovery capture: Planning updated; TDD candidate regression scenarios captured here pending approved repair, SDD/BDD candidate experimental guard/accounting corrections only; DDD/ADR/SSOT none.

User approved guard correction and offline revalidation ONLY; a replacement paid comparison requires separate approval. Same implementation worker resumed as `8171779e-8cf5-4df9-87ad-bb1ee79ac82b` for minimal monitored-03: narrow read-only discovery distinct from validated launch admission, blocked-tool error reconciliation without duplicates, and real discovery→nativeReader→join runner fixtures in both arms. Preserve monitored-02 failedmatrix/freeze/spend, no acceptancefile or paidretry. Planning updated with confirmedscope; existing SDD/BDD/TDD experimental repair candidates remain pending implementation/review, DDD/ADR/SSOT none.

Monitored-03 offline handoff delivered:21Python tests,6Bun tests/52assertions and actual nativeA/B discovery→admission→join/scorer E2E reported PASS;4distinctParenttoolerrors perarm deduplicated. Newfreeze `2049ede264626fff42b444a813f7e8a85796e792eb7897d433603504cac3e26d` (18332entries). Prior02freeze/39protectedhistoricalfiles unchanged peraudit. New run/score explicitly reject paidexecution. These are fixture results, not livepilot improvement.

Targeted reviewer resumed as `5bc240c0-5d84-4061-870f-08622fa14861` for counter/discovery/errorunion repair and introducedrisks only. Any READY verdict is offline-repair acceptance, not paidpilot authorization. Discovery capture: Planning updated; experimental SDD/BDD/TDD candidates remain underreview, DDD/ADR/SSOT none.

Monitored-03 reviewer `5bc240c0-5d84-4061-870f-08622fa14861` returned structured READY with one P2 note, OFFLINE repair only. Parent read complete structured artifact and independently verified SHA-256 `2049ede264626fff42b444a813f7e8a85796e792eb7897d433603504cac3e26d`. Discovery/admission/error-reporting fixes accepted for the exercised paths; no paid acceptance created.

Residual P2: legacy ID-less denial matching may merge same-role/tool/reason failures across different known sessions; reviewer says existing single-Parent historical and A/B fixture evidence unaffected. Preserve note and require session-compatible matching regression before any future general reporting claim. No renewed paid pilot is authorized; old failedslot/spend remain unchanged. Discovery capture: Planning updated with offline-review acceptance and residual reporting candidate; TDD/SDD candidate scope retained here, BDD/DDD/ADR/SSOT none at this checkpoint.

User explicitly approved proceeding with proper repair and fresh comparison after proposed sequence: remainingfix→regression/review→new24max$30monitoredpilot, first resolving historicalusageuncertainty; stop if unresolved. Recorded approval at experimentroot/replacement-approval.json; conservative accounting includes verifiedprior measuredspend towardtarget, preparation/control separate. No permission to bypassunknownusage or overwritefailedmatrix.

Workflow `f3ebf4da-bfa1-4ea6-81e0-d7eb44569c48` sequences fresh boundedworker and targetedreviewer for monitored-04: session-compatiblelegacydenialmatching, independenthistoricalsettlement evidence, reviewedcarry-in/headroom, exactnewacceptancegate. Paidexecution remains behind Parentacceptance of reviewedfreeze; no installeddependency/native/globalmutations. Task352 inprogress. Discovery capture: Planning updated with confirmedreplacementauthority andworkflowidentity; experiment reporting/regression candidates continue here, no production semanticdelta.

Replacement04 preparation and targetedreview complete: reviewer8546dff4 READY/noissues; Parent read fullstructuredreview and independently verified freeze `dee7797a7817ff1dade6505bc32398101e93b1b4a95f005519d750b367925235`, settlement `87810a2b8f5b34988e10aa875f622e58017300aad1187c51283dd23b02d71cb9`, approval `b1ab36036f2905ed5a99e1aa80856a2cb0120ccb47033014def146648ae5d5ca`, empty04runs. Historicaloperationalsettlement$0.168078 accepted with affirmativepreexecutionblock+foursettlementevidence, notinvoiceguarantee; oldunknownstop/resultsunchanged. Parentcreated04review-acceptance.json.

Executor same-protocolresumed `288d7c56-5d40-4811-be91-a858833c8f78` toexecute04once, scoreonlyifpermitted, reportactualpairedoutcomes. $30targetincludesprior$0.168078; no newmatrixretries/repairs. Dispatchnotcompletion. Parent capabilitylist initially hit read-debtgate; satisfied mainrootmapoverview→copiedbenchmarkrecorddrill→canonicalread and repeatedsameprotocol listsuccessfully; noexecutionmodefallback. Discovery capture: Planning updated withsettlement/acceptance/dispatch; no newproductionlayerdelta.

Monitored-04 live execution/scoring completed:24/24 scored,12 paired observations, no integrity stops/unscored/outstanding actors. Parent read attempt-results.csv. Mean substantive latency A130.180s/B102.465s; pairedB-A mean-27.714s, median-25.188s, all12pairsBfaster. Semantic A8/12 B9/12; essentialclaims A44/50 B37/50. Crucial pathasymmetry: A fallback12/12 (alljoinerrors `synchronous Reader result lacks successful content-bearing runtime identity`), Bfallback2/12 and10completejoins. This is observed end-to-end fallback-inclusive comparison, NOT evidence of pure synchronousvsparallel advantage or normal A viability. No adoption recommendation justified yet.

Measurementcost A$8.93549660/B$7.08023688, scoring$1.16055; newtotal$17.17628348 plusprior$0.168078 = $17.34436148. Worker reconciled72newactors/546settlements, stopnull,outstandingempty, credentialcleanupcomplete. PeakParentcontext mean A36837.75/B24293.08; median36790/21134.5. Quality/latency modeladjudicated; laterpartialanswers displacedearlierfullanswers in4slots; norescoring. Rawreports/reconciliation under04runs/evidence; nofurtherpaidworkauthorized.

Discovery capture: Planning records completedmeasurement and unresolved A syncidentity/join candidate for read-onlydiagnosis; TDD/SDD candidate failure signature captured here, otherproductionlayers none. Task352 overallcomparison objective remains unresolved because A didnotexercise successfulnormaljoin. Executor runtimeoutputoverride replaced rootmeasurement-execution-handoff.md after preservingoldhandoffbyte-for-byte at04runs/evidence/prior-monitored-02-handoff.preserved.md withreceipt; old02matrixunchanged. No patches or diagnosis applied duringmatrix.

User requested fixing syncfailure and structurally addressing async problems, then confirmed continuedisolation after Parent clarified realimplementationworktree `/tmp/lazy-harness-reader-runtime-v1` branchwork/reader-runtime-v1 versusstandalonebenchmarkcopies. Follow-up workflow `e67b80a9-97aa-4a7d-b10f-a6e4c3d21c00` launches two readonlyscouts: actualsyncnativeidentityshape/fixturegap and asyncincompletejoins/laneguard/answercontinuation/coverage. Outputs experimentroot/followup-analysis/{sync-cause,async-cause}.md. Sourcepatches await concreteboundedproposal; no newpaidbenchmark/main/installedchanges. Task353 inprogress;354analysis tracked;352pendingnormalpathinterpretation.

Re-grounded once for follow-up after read-debtblockedcapabilitydiscovery: mainoverview→copiedllm-owned-record-retrievalBDDdrill→actualBDDread, sameprotocollistsuccess. Discovery capture: Planning updated withconfirmedfollow-upscope/isolation andactiveinvestigation; no unconfirmedrootcausepromoted.

Two readonlyscouts completed with actualevent/code evidence. Syncrootcause is hostadapter packetparsing: all12Apackets quoted root/revision/epoch withMarkdownbackticks, while synccomparesrawvalues and asyncstripsdelimiters. Native run/session/content werepresent. Ninepackets complete, twoincomplete, oneconflict; never convert all12tosuccess. Scriptedofflineproviders usedbarevalues, explainingfixturegap.

Asyncmechanisms are distinct: B7/B16 Readercanonicalgrepoperand/lane mismatch produced correctlydelivered incompletepackets withoutbodybudgetexhaustion; Parentbroadgrepdenials belongbenchmarkmonitor, not .lazy-harness/scripts ownership. B11/B20/B24 andA12 deliveredfullanswers thenhostpostresponseadvisories triggerednarrowreplacementanswers. Nativeasynccontentdeliverysucceeded inthosecases; no notifierredesignprovenneeded. Endpointscoring exposedgenuineanswerpreservationdefect; no historicalrescore.

Proposedboundedrepair for confirmation: sharedstrictresultpacketparser (notlaunchtaskparser), balancedoptionalbackticks andunambiguousidentity/status; truthfulincomplete/conflictfallback; preservecompleteprimaryanswer byseparatingrequiredReaderdelivery frompostansweradvisories, retainingadvisoryvisibility/actionrequirements. Additionalcanonical-scopedsearchsurface isseparatescopechoice; do notpermitumbrellabodysearchbasedonlyonglob. Reports followup-analysis/sync-cause.md andasync-cause.md includeactualpath/line evidence andregressiondesigns. Discovery capture: Planning updated; SDD/BDD/TDD repaircandidates identified, DDD/ADR/SSOT none untilscopeconfirmation. Frozen04/main/installedpackagesunchanged.

User selected 핵심 두 건 우선: implement sharedresultpacket/statushandling andprimaryanswerpreservation in separate Readerworktree, withreal-failure-shapedregressiontests andtargetedreview. Canonical-scopedsearchinterface deferred; existinglaneguardsunchanged. No newpaidbenchmark ormain/nativeinstalledintegration. Records/tests must preservevalidincomplete/conflict, runtime-ownedidentity/fullledger/hashes andadvisoryvisibility withoutoptionaladvisories replacingheadlessanswers.

Core-repair implementation checkpoint (user-approved two-core scope): current isolated worktree now has shared strict RESULT parsing, native synchronous receipt adaptation with default async unchanged, and typed headless print/JSON non-steering advisory output. Added parser/transport/full-ledger negatives and actual native CLI production capture/placement multi-claim tests. Validation/review pending; one evidence capsule `.lazy-harness/evidence/reader-result-primary-answer-repair.md` owns receipts, risks and final outcome. Baseline dirty status/diff/file hashes preserved under `/tmp/lh-reader-sync-async-2T2VQR/core-repair/`; pre-existing previewContent unknown-return diagnostic retained by supervisor approval. No native/main/frozen/global changes, new search surface, budget increase, paid calls or historical rescore. Discovery capture: primary TDD reader-result-primary-answer plus independent SDD/BDD updates; SSOT/DDD/ADR no independent delta.

Post-core live canary outcome and detailed costs are recorded in `.lazy-harness/evidence/reader-post-core-live-canary.md`: four normal joins and preserved answers, two faster B pairs, equal limited semantic coverage; smallsample and higherBcost/context remain explicit. User selected asynchronous direction as preference, not deployment authorization.

Architecture discussion candidate (not approved implementation): user asks whether owning Reader execution inside a Pi harness plugin is preferable to maintaining pi-subagents fork, and raises ownIDE with scope concerns. Existing packages/lazy-harness-pi/package.json already registers Pi extensions/skills/prompts/agents. ADR0055 currently keeps orchestration semantics core-owned and PiSubagents asfirstthinruntime; replacing Reader transport is an explicit adapter decision, not wholesaleembedding orautomaticIDEexpansion. Proposed bounded option: keepportablecore, useexistingPi package, investigate a small ownedasyncReader executor reusingPi model/session/toolfacilities while retainingepoch/identity/ledger/answerpreservation; avoidcopyinggeneralpi-subagents scheduler/UI/worktreefleet. Feasibility and maintenance benefit are unverified; cancellation/drain/orphan/usage responsibilities must be mapped before approval. Discovery capture: Planning candidate recorded; ADR/SDD/SSOT updates pending userchoice andtechnicalevidence, no production/config mutation.

User clarified discussion is whole-harness installation/operation, not just Reader replacement; now asks Pi-plugin versusMCP versusownIDE recommendation withoutconfirmedchoice. Task356 scopeupdated toarchitecturecomparison, noimplementation. InstalledPi docs/packages.md explicitlysupport npm/git/localpackageinstall andproject-localscope; existingpackagealreadyregistersextensions/skills/prompts butprivate:true, so onecommandpublishedwhole-harnessdistributionisnotyetproven. Candidate recommendation: portableharnesscoreandproject-ownedrecords, Pi plugin asprimarylifecycleadapter andinstallationentrypoint, optionalMCP exposure forcross-clienttools later; ownIDEdeferred. MCPtoolaccessalone doesnotestablishhost-specificturn/childdelivery/primaryanswerownership withoutclientintegration. Installation/update/data-preservation andcurrentCLIdependencybundling requirefeasibilitywork. Discovery capture: Planningcandidateonly; ADR/SDD/SSOT decisionspending, no source/deploymentchanges.

### Discovery capture — Whole-harness delivery discussion

- DDD: none — no new confirmed domain vocabulary.
- SDD: candidate — portable core, Pi lifecycle adapter and optional MCP tool adapter boundaries; public API feasibility and complete installation packaging remain unverified.
- BDD: none — existing Reader/Parent join and primary-answer preservation behavior remains governing; no new user flow approved.
- TDD: none — no new implementation or executable test contract in this architecture discussion.
- ADR: candidate — recommend Pi plugin as primary delivery/runtime integration, MCP as optional interoperability, and defer own IDE; this recommendation is not an adopted decision.
- SSOT: candidate — installation/update dependency ownership, supported Pi versions and separation of installed code from project-owned .lazy-harness records require confirmation; no configuration or ownership policy changed.
- Planning: updated — task356 now compares whole-harness delivery and installation, superseding Reader-only feasibility scope. Next analysis must assess public API sufficiency, packaging/dependency requirements, update/removal data preservation and maintenance burden before proposing implementation.

This is candidate capture, not multi-layer canonical promotion. Existing architecture records remain authoritative; no duplicate ADR/SDD/SSOT documents, implementation, installation or deployment was performed.

### Discovery capture — Upstream merge inspection (2026-09-12)

User requested verification after another agent's fixes were merged. Read-only source inspection refreshed origin/main with git fetch --no-write-fetch-head; no checkout, pull, merge, rebase or test execution. Remote main confirmed by ls-remote as 80cf3be485d22a8036723e415f8b4e95f897786f. Local main and Reader worktree HEAD remain 58fbcbf5e9d632bf9b0e7a87857ad8ed05f01f7b with existing dirty changes.

Merged changes: #2 / 47db095 graph, sync and semantic-validation integrity; #3 / 68e6d07 typed capture evidence and Node-target validation; #4 / 80cf3be merges 8f6b13f host-owned document validation scope. Inspected upstream diffs for self-test.py, validation-governor.py and Pi index.ts. Upstream index.ts and self-test.py overlap paths owned by existing Reader changes; this is overlap evidence, not a demonstrated merge conflict. Integration must preserve both behavior sets and current dirty changes. The separately reported whole-tree fixture-copy, TimeoutExpired tail and run_check_captured buffering repairs are not present in the inspected upstream diffs; do not conflate them with the three merged PRs.

- DDD: none.
- SDD: none — upstream contracts not re-authored during inspection.
- BDD: none — no local behavior change.
- TDD: none — no fresh validation or regression changes; merge presence is not validation of the combined Reader candidate.
- ADR: none — previous plugin direction remains pending design.
- SSOT: none — source/config ownership unchanged.
- Planning: updated — upstream changes are available but not yet absorbed into the dirty Reader worktree; bounded integration and combined validation require a separate approved batch. Existing experiment receipts remain tied to their frozen pre-integration source.

Integration approval / prelaunch blocker: user approved proceeding on the merged baseline. Task357 opened for combined upstream/Reader integration, without installation/push/new paid benchmark or plugin rewrite. Before any child launch, both the advertised pi-subagents skill read and `subagent action=guide topic=workflows` failed ENOENT. The entire `/home/lazydino/.pi/agent/npm/node_modules/pi-subagents` path is absent even though the current session exposes cached subagent tool/agent discovery. No child launched and no run id exists; no alternate execution protocol used. Task358 blocks357 pending runtime-path/package resolution. Main and Reader remain dirty at58fbcbf; tracked binary diffs and status manifests are preserved under `/tmp/lh-reader-sync-async-2T2VQR/upstream-integration-prelaunch-{main,reader}.{diff,status}` (untracked contents remain in place, not included in those diffs). Discovery capture: Planning updated; DDD/SDD/BDD/TDD/ADR/SSOT none for this infrastructure stop.

Reload recovery: configured local-packages/pi-subagents-readfix-1 contains acorn; after user /reload, native workflow parser validation succeeded. Retry workflow704a33cc-43ca-4014-9902-e4359bd0734a launched child8fef7adf-3a7b-4623-8b3f-54b0a30ee2e8 but failed before any assistant/tool output. Crucially this was NOT30minutes of integration: events show run.started1789278835276, timed_out1789278835911 carrying already-expired deadlineAt1789268158817, and terminalduration7666ms. Cause of the stale deadline is not established (do not assert model slowness or suspend). Process-terminal observed, resume unavailable, no supervisor asks, no handoff, no saved child session. Transcript contains only initial/user/custom grounding events. Reader tracked delta hash remains e38c613e9246e3ffdd5c174ef21751cbd424fc209167fcc5d4a92c44852477c4, matching preservedprelaunchdiff; root /tmp/lazy-harness-reader-runtime-v1 branchwork/reader-runtime-v1 HEAD58fbcbf unchanged. Metadata zero usage is not invoice proof. Discovery capture: Planning updated; no independent DDD/SDD/BDD/TDD/ADR/SSOT delta. A fresh same-protocol retry can use a new admission deadline; no alternateCLI or global repair authorized.
