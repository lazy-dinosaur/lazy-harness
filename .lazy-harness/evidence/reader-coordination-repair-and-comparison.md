# Reader coordination repair and paired comparison

Status: isolated code repair and focused verification complete; final standard and paired live comparison pending.

## Approval and preservation

User approved proceeding with the purpose-aligned repair and measuring how it differs in accuracy and other outcomes. Then explicitly selected `12회·$10 한도 (Recommended)` for 3 question types ×2 repetitions ×before/after, including comparison Parent/Reader and scoring costs. Implementation/review overhead is tracked separately. No main integration or historical trial retry.

Baseline frozen before edits: `/tmp/lh-reader-control-repair-eqm7rr7m/baseline`, `baseline-manifest.json` (615 files). Main `/home/lazydino/dev/lazy-harness` unchanged. Source work confined to `/tmp/lazy-harness-reader-runtime-v1`.

## Implemented difference

Before: plain owned Reader status falls through the Python generic subagent action gate, although the TS classifier did not treat it as mutation; coordination could not obtain progress without prior canonical evidence.

After: adapter-owned current root/run/epoch/pending metadata accompanies status inspection outside caller arguments. TS and Python agree on a narrow ordinary/transcript status allowance. Status is excluded from epochs/recent-call/fingerprint evidence; complete-looking transcript text cannot enable join or writes. Unknown/root/stale/management operations remain outside this exemption. Marker-bearing management calls cannot masquerade as launches; native launch must omit action.

Native notification remains the existing actual content path. Explicit guidance says yield control without a user-facing terminal answer when there is no independent work; no status/shell polling. This remains model guidance, not runtime-enforced output suppression. Normal bounded direct fallback remains available; no new unlimited retries or live recovery budget was invented.

## Verification

- Shared fixture table covers owned status, bad root/run/epoch/pending, malformed/oversized operands, marker-bearing management, and fake content.
- Package adapter fixture, generic Python guard, actual lifecycle hook (19 scenarios), strict resolved extension tsc: PASS.
- Implementation delegate `f478235c`; delayed attention notices arrived after its confirmed completion.
- Independent review `50731261` BLOCK: Reader marker could exempt management action. Corrected and regression-tested; follow-up `75126202` OK.
- No new live outcome claimed yet; waiting behavior and practical accuracy must be measured, not inferred from static tests.

## Discovery capture

Primary TDD `.lazy-harness/tests/pi-agent-package.md` includes four-row SDD/BDD/SSOT/DDD completeness matrix. SDD/BDD changed independently; SSOT/DDD/ADR no new ownership/config/architecture decision. This capsule captures Planning/verification/live approval without duplicating canonical rules. Implementation map and graph `kg_reader_owned_status_coordination_repair` link actual source/tests.

## Final static checkpoint and paired launch preparation

Final standard PASS 114.316s (full self-test 113.696s); source remains independently reviewed. Actual hook before/after probe using the same 18 cases: baseline has 2 false blocks and 4 false allows relative to the intended narrow control contract; repaired has 0/0. This measures hook classification, not 18 real agent answers or successful unauthorized mutations. Full adapter fixtures separately cover launch/management separation and status-not-evidence.

Paired runner `/tmp/lh-reader-control-repair-eqm7rr7m/comparison/run.py` prepared with 12 fixed slots: short lookup, runtime/shared ownership, validation workflow; two repetitions each under before/after, balanced AB/BA order. Both use Sol Medium + Luna Low, identical prompts except root/revision, equal per-case Reader budgets and Parent four-read/1,000-line allowance including bounded recovery. No exact natural-language-envelope or zero-tool-error requirement is used as answer correctness. Both receive normal bounded fallback rather than historical no-fallback restrictions.

Two frozen product snapshots, actual same-tool SDK preflight PASS, four offline comparison tests PASS. Comparison launch stop $8.50 reserves $1.50 for blinded scoring within selected $10; implementation/review costs are separate. No retries or midmatrix repairs. Actual native yield remains model guidance, so accuracy/time effects remain unproven until runs finish.

## Terminal paired outcome

12/12 attempts completed without retries. Independent full-answer semantic PASS before 2/6, after 4/6; required-claim coverage 23/26 →17/26, because after slot10 ended with a waiting statement and no substantive answer. Substantive completion 6/6 →5/6. After slot6 exceeded Reader allowance (7 reads/1,400 lines vs6/1,200) and reported inaccurate counters; a run-ID mismatch rejected join, and direct fallback produced a correct answer. Therefore semantic success plus budget conformance is 2/6 →3/6, not 4/6. No default-readiness conclusion.

Median wall 140.406→122.994s, mean measurement dollars $0.483704→$0.422429, median Parent peak context 51,317→41,011. Failed attempts remain included: excluding the repaired waiting-only terminal, repaired substantive-answer median is 136.838s. No newly allowed owned-status call occurred naturally; the one before status call was fleet-wide, outside the exemption. The live differences cannot be causally attributed to the narrow status repair.

Initial blind scorer had a source-export defect: selected evidence files were mistaken for a complete directory. Full frozen sources and independent focused correction repaired the three affected judgments; original scores and corrected judgments are both preserved, answers unchanged. Comparative execution+scoring cost $6.30384524 (measurement $5.43680324, scoring $0.867042), within selected $10. Implementation/review children separately $7.919462; interactive Parent preparation overhead unmetered here. All24 actor usage summaries remain identical on reread; source manifests verified and disposable auth removed.

Terminal report: `/tmp/lh-reader-control-repair-eqm7rr7m/comparison/report.md`; machine results and independent scores adjacent. Discovery capture: TDD/Planning candidates remain for print/native-notification completion, actual Reader cap/ledger enforcement and run-ID transport; root causes are not established and no further source edits/live runs performed. Existing tool-signature policy/code discrepancy is noted, not changed in this work. SDD/BDD may need follow-up after root-cause confirmation; SSOT/DDD no newly confirmed delta. Main integration remains outside scope.

### Follow-up causal inspection (read-only source/log investigation)

User asked why the mixed outcome occurred. Confirmed narrower mechanisms, without new implementation or reruns:

- Slot10 Parent emits its waiting-only last message at 06:36:58.978Z; Reader completes at 06:37:00.260Z, 1.282 seconds later. No native notification/join appears in the Parent transcript afterward. Prompt-level yielding did not produce the required Parent continuation. Exact native lifecycle defect remains unlocalized; do not blame Reader semantic incapacity for this missing answer.
- Slot6 launch text/details identify outer async run `83ddb0cc-a706-43ee-bc04-e2640fc6d264`. Notification footer instead exposes a session path containing child execution ID `31e601ec-5761-4c78-94eb-838058c62889`; Parent supplies the latter to join. This is a confirmed identifier substitution, not a randomly missing Reader result. Identity rejection itself is correct.
- Actual `index.ts#isReaderRuntimeToolAllowed` read admission checks canonical path, and the Reader `tool_call` branch returns immediately on that allowance; no cumulative body-read ceiling is charged there. Join validates supplied numeric ledger against supplied/launch bounds, not an authoritative child tool-call ledger. Thus the implementation does not make the prompt's per-run body-read allowance an admission-time cap. Slot6's seventh successful read and inaccurate self-report demonstrate the gap. Whether the child loaded every intended extension is separate and not established by this inspection.
- Static fixtures passed their constructed inputs, while the actual lifecycle/identifier/self-reported accounting interaction remained insufficiently protected. Narrow status-classification repair is not equivalent to complete asynchronous task reliability. Semantic omissions and policy/code conflation also remain separate from transport success.

Discovery capture: refined the existing TDD/Planning candidates for #342; no new canonical runtime rule, no approved implementation plan, no main change. Original terminal experiment manifest remains unchanged.

### Proposed follow-up scope — awaiting selection

User asks how to strengthen the design. Proposal, not execution approval or canonical policy: (1) inspect the actual supported native/print lifecycle and protect pending-to-content-to-Parent-continuation completion, without inventing a wait API or relying on waiting prose; (2) bind join identity to the adapter-owned current launch rather than model-selected session IDs, retaining root/revision/epoch checks and rejecting supplied mismatches; (3) meter actual child read admissions/results in runtime-owned state and enforce explicitly configured per-run ceilings, with terminal/incomplete accounting independent of model prose; (4) verify answer claims against actually inspected implementation and distinguish documented intent, observed code, missing coverage, and unverified absence. No universal six-read quota or zero-error rule is proposed.

Prefer one bounded lifecycle/identity/accounting repair with real native integration regressions (late completion, mismatched identity, seventh-read denial, failed-read charging, inaccurate self-report, bounded recovery). Existing predicate fixtures alone are insufficient. Semantic checking remains a separate model task, not a deterministic truth guarantee. New live comparisons require separate finite scope/cost selection; no main integration. Discovery capture: refine existing #342 TDD/Planning candidates; this paragraph is a proposal only, not a new runtime rule. Detailed implementation depends on read-only native lifecycle investigation.

### Approved follow-up investigation and external boundary

User selected execution/identity/accounting repair plus native integration regressions, excluding new live comparison and main integration. Read-only scout7416b097 failed before a child session persisted (`Cannot read properties of undefined (reading create)`). Foreground worker ff557007 investigated but made no edits and stopped at the external lifecycle boundary; its runtime classified the no-edit implementation result as failed. No product source modifications in this follow-up yet.

Parent independently inspected installed `pi-subagents/src/runs/background/{auto-drain,completion-batcher,notify}.ts` and `src/extension/index.ts`: hasOutstandingWork includes queued/running jobs and background providers; successful completion notifications default to a150ms debounce (1000ms max wait); timers are unref'ed; notifier disposal settles pending batches without emission. Native agent_end awaits active work, not an explicit notification-flush barrier. This provides a concrete candidate race consistent with slot10, but the complete SDK/print race has NOT yet been reproduced by an offline integration test. Worker found no documented public delivery-flush API. Configuration-level completionBatch disable exists but is not evidence of a per-Reader solution or end-to-end correctness.

Scope decision needed: separately isolated upstream lifecycle investigation/patch versus host-only identity/accounting with headless-completion limitation retained. Do not edit installed dependencies, assume sleep/polling fixes delivery, or silently expand integration scope. Existing TDD/Planning candidate #342 remains open.

## Approved isolated native follow-up — implementation checkpoint

Approval: `/tmp/lh-reader-native-followup-hf9m835b/approval.json` authorizes this host and `/tmp/lh-reader-native-followup-hf9m835b/pi-subagents` only. Installed package, main source, global settings, commits/pushes, and paid comparisons remain excluded. Implementation children may not delegate further. Local `node_modules` symlinks resolve installed SDK/dependencies read-only; no package installation or global mutation.

### Reproduction and source mechanism

Before source patch, `bun test /tmp/lh-reader-native-followup-hf9m835b/pi-subagents/test/reader-delivery-sdk.test.ts` failed under the real Pi SDK: expected two scripted provider turns, received one (612ms total). Parent had finished its independent response, Reader content was still in the default completion batch, and substantive continuation was absent. Zero real provider/model calls. This preserves rather than reruns the historical paid trial.

Inspected SDK source: `/home/lazydino/.bun/install/global/node_modules/@earendil-works/pi-coding-agent/dist/core/agent-session.js` (`_emitExtensionEvent`, `_runAgentPrompt`, `sendCustomMessage`, queued-message continuation after `agent_end`), `extensions/types.d.ts` (`appendEntry`, `sendMessage`), and `sdk.d.ts`. Native `src/runs/shared/child-session.ts` loads explicit extensions and binds print sessions; `agents/agents.ts#resolveAgentRelativeExtensionPaths` and `runs/shared/child-tool-plan.ts#resolvePiLaunchToolPlan` support agent-relative child-only extensions. Native `subagent-runner.ts` publishes final results before its final `writeStatusPayload`.

### Minimal changed seams

- Upstream copy `src/runs/background/notify.ts`: `beginDrain` flushes held completions and disables batching only during headless drain; supported `sendMessage` uses `followUp` and structured outer-run/session-file metadata. Normal interactive batching/dispose retention remains.
- `src/runs/background/result-watcher.ts`: `deliverResult` tracks real in-flight promises; `drainPendingDelivery` bypasses coalescer timers for owned terminal files, awaits delivery, and fails explicitly if owned content remains undelivered.
- `src/runs/background/auto-drain.ts` and `src/extension/index.ts`: drain content before quiescence and before reporting failed work; bracket headless work drain with the notifier delivery scope. No sleep, new poller, wait tool, or repeated nudge.
- Host `index.ts`: structural launch IDs; optional join run/counters default to runtime-owned values while explicit mismatches reject; Reader admissions/results/failures/terminal state persist via supported `pi.appendEntry` in its native session. Join accepts only the terminal ledger from native notification metadata, bound to root/revision/epoch/model/task/session and actual successful canonical file hashes.
- `agents/record-reader.md`: explicit `subagentOnlyExtensions: ../extensions/lazy-harness/index.ts`. Parent/source and Reader/canonical boundaries, one Reader per epoch, existing launch ceilings (no universal six cap), and fresh bounded fallback remain.

### Verification and boundaries

Focused host checks `check_pi_package_layout_and_contract` and `check_read_debt_permit_generic_external_action`: PASS. Strict resolved extension `tsc -p /tmp/lh-reader-resolved-typecheck.json`: PASS after correcting an optional revision narrowing (initial TS2322 failure preserved here).

Real SDK protection in the upstream copy: `test/reader-delivery-sdk.test.ts` covers late native notification and terminal-result-file delivery to substantive Parent output; `test/reader-accounting-sdk.test.ts` covers native extension resolution/loading, seven concurrent reads, failed-read charges, over-limit denial, default owned identity/counters, explicit child-ID confusion, spoofed counts, sibling notification, stale ledger, failed read, and noncomplete fallback. The last checkpoint before final discovery/failure-path additions was 12 PASS / 80 assertions / 1.055s. Final exact checkpoint output is captured in upstream `test/reader-validation.json`; Parent owns final standard validation after review.

Primary TDD `.lazy-harness/tests/pi-agent-package.md` contains the SDD/BDD/SSOT/DDD matrix and exact implementation map. SDD/BDD have independent deltas; SSOT/DDD/ADR none. Graph/cache adds one source-grounded follow-up row without migrating historic rows. Rule placement: existing platform contract/TDD, not a global operating policy. Discovery capture: implemented structural delivery/accounting repair; semantic selection and substantive answer correctness beyond the scripted facts remain model judgment. No new live comparison or default-readiness claim.

Remaining integration boundary: host join intentionally fails closed on an unpatched installed notifier (missing structured identity) or missing/disabled child ledger. Both isolated changes must be reviewed together before separately approved integration. Native SDK offline tests are not a paid-model quality comparison, and these fixtures do not claim full upstream regression coverage. Legacy graph migration 37 rows remains pending; offer guided resume separately, never rewrite it automatically.


## Native follow-up closure (isolated only)

Independent review81958866 found unmetered pre-hook SDK argument errors and a missing upstream return-type property; both fixed and protected. Test-only worker a010ef6b added a full actual CLI/detached-runner test, unlike earlier SDK tests that reconstructed handlers. Its initial18PASS/1FAIL and findings report remain unchanged. It exposed two additional seams: running status was persisted before its active-run index, and native task text prepends `Task: `. Parent published the index before startup authorization with failed-state cleanup, and unwrapped only the native prefix. The unchanged native success assertions now pass. Review5838725e: OK.

Final focused run:19PASS,0FAIL,160 assertions,13.95s, including real native launch → delayed child completion → native content → Parent runtime-ledger join → substantive answer. Scripted providers only; test network guard reported no network attempts and cleanup found no surviving sandbox native runners. Strict resolved host tsc PASS. Upstream same-dependency transitive check236 baseline/236 candidate errors, zero new diagnostics; not a clean/full upstream typecheck or suite claim. Installed upstream313-file manifest unchanged. Parent final standard follows the final record batch.

This closes the scoped structural repair and offline reproduction, NOT model-level answer accuracy or deployment. No new paid comparison; no installed dependency/global settings/main mutation. Host `/tmp/lazy-harness-reader-runtime-v1` and upstream `/tmp/lh-reader-native-followup-hf9m835b/pi-subagents` require coordinated, separately approved integration. Earlier experiment data/failures and37-row guided migration backlog remain intact.

## Latest combined-patch benchmark — separately approved

After clarifying that the prior12-run results predated the latest fixes, user explicitly selected another `12회·$10 한도 (Recommended)`. New frozen run root `/tmp/lh-reader-latest-paired-8ak8p70m`. Same3questions,2repetitions, balanced12-slot matrix and exact prior common prompt (root/revision substitutions only). Before uses the original pre-status-repair host plus frozen unpatched upstream; after uses latest verified host AND isolated upstream together. Existing experiments are not changed or retried. Deployment/main/globalsettings remain untouched.

Measured Parent+Reader spending launch threshold $8.50 preserves $1.50 for independent scoring, total selected $10; in-flight overshoot possible and disclosed. Preparation uses no model calls. Fresh source/upstream/input manifests, actual SDK tools/discovery preflight PASS, five offline design tests PASS. Initial discovery probe wrongly used project-only rather than native default both scope; corrected without source/config alteration. SDK-created empty auth stores removed; no credentials present before launch. Raw attempted reads and runtime-owned admitted counters will be reported separately so a correctly blocked over-cap attempt is not mistaken for an executed overrun. Accuracy uses original predeclared claims and full-source blinded evidence, not the earlier partial-evidence export.

Status: prepared for new live execution, not yet an outcome. Latest offline19-test success is not used as a live-model accuracy claim.

### Latest combined-patch benchmark terminal result

New live12/12 finished. Latest host+upstream were BOTH loaded from frozen copies, not merely offline tested. Independent adjudicated full-answer pass3/6 before and3/6 latest; requiredclaims present26/26 both, substantive outputs6/6 both. Median time135.589→131.536s (−3.0%), mean time149.478→134.586s; mean measurement cost$0.495290→$0.515037 (+4.0%); median Parent peak context52,061→46,674.5 (−10.3%). No observed accuracy improvement. Small sample/three repeated questions; not causal/general superiority evidence.

Actual machine ledgers appear in all6latest runs and match observed admissions; executed limits6/6 both. Latest slot6 attempted a seventh read, which was blocked, unlike the prior unblocked-overrun witness; raw-attempt conformance5/6, admitted-limit conformance6/6. Its fallback answer passed. Latest slot2 had a rejected canonical-lane grep and successful semantic fallback. Slot10 supplied wrong accounting despite available defaults: join correctly rejected, redundant retry rejected, then substantive but semantically incorrect answer. Complete joins4/6→3/6; fallbacks2→3; failed tools4→4. Neither arm exhibited waiting-only completion in this sample; no measured frequency improvement is claimed.

Both arms' validation answers conflated documented conservative fallback with actual uncertain-signature hashing. Each arm also had one materially wrong implementation assertion. Initial scorer22ea71b7 yielded2/6 each; blinded qualification adjudication8e9a5866 accepted explicit record-only attribution for one answer per arm, final3/6 each. Raw answers/initial judgments retained. Full frozen source evidence supplied from outset. Remaining semantic discrepancies are observations, not approval for new source fixes.

Measurement$6.06196068 + independent scoring/adjudication$0.901134 = **$6.96309468** within new$10approval. No new paid runs beyond12, no main/installed/global mutation. Both snapshot manifests verified;24actor usage reread matches, disposable auth removed. Report `/tmp/lh-reader-latest-paired-8ak8p70m/report.md`, metrics `results.json`, runtime accounting `reader-admission-audit.json`, scores `scoring/validated-scores.json`.

Discovery capture: completed bounded comparison; TDD/Planning future candidates are model use of optional runtime accounting defaults, unnecessary join retries, and source-vs-record semantic verification. Existing structural repair remains isolated and independently tested. No new canonical rule/SSOT/DDD decision or automatic integration is inferred from these results.

## Astra Medium solo versus Reader — separately approved preparation

User explicitly selected both parents `openai-codex/gpt-6-astra:medium`, solo versus latest runtime `gpt-5.6-luna:low` Reader, and a NEW maximum12runs/$10 combined execution/scoring budget. Frozen root `/tmp/lh-astra-solo-reader-z8pen9ds`. Both arms use byte-identical latest host and patched native upstream snapshots from the completed comparison; no product mutation. Solo receives the sum of prior Parent+Reader read-call/line ceilings, not merely the smaller Parent-only allowance. Both parents can request up to250lines per read; delegated Reader retains its existing150/200 caps. Solo has only read/grep/find/bash active; delegated adds native subagent/join. Same questions/oracles; balanced pairs reordered so first six attempts cover all three questions before repetitions, subject to budget.

Zero-model SDK preflight verified actual Astra registration, Medium support through reasoning capability, model pricing, Reader guard discovery and tools. Astra registered per-million input/output/cache-read rates$10/$50/$1; model-priced usage, not token counts as dollars. Five offline design checks PASS, source/upstream/input manifests frozen. Measurement allocation$8.50 reserves$1.50 scoring. In addition to the hard launch threshold, stop before a new matched pair when twice the highest prior per-run cost would exceed that allocation (initial per-run projection$1); incomplete matrices remain reportable, no budget extension/retry. This may finish fewer than12 attempts. No performance or accuracy outcome yet; old Sol figures will not be pooled into Astra results. Preparation probe initially used a removed getModel export; corrected to current SDK ModelRuntime.getModel, no model requests incurred.

Discovery capture: confirmed bounded same-parent-model topology comparison, captured here as evidence; no new SDD/BDD/SSOT/DDD product contract, no global model-default or deployment change. Legacy37-row graph migration stays separate and user-guided.

### Astra comparison terminal — budget-stopped after four complete pairs

Frozen runner stopped before slot9 using its prospective pair-cost rule, not an agent crash. Actual8attempts,4perarm; lookup twice, ownership once, validation once perarm. Slots9–12 unlaunched. No retry or midmatrix repair. Scorer447b7edd independently evaluated full-source blinded outputs: semanticPASS4/4 each, requiredclaims15/15 each, substantiveanswers4/4 each, readbudgets4/4 each. Both Astra configurations correctly described the policy/code tool-signature discrepancy missed in previous Sol samples; this is not a separately controlled Astra-vs-Sol result.

Solo vs delegated: median122.501→114.008s (−6.9%), mean123.988→116.764s; mean model-priced cost$1.042340→$0.742627 (−28.8%); median Parent peak context39,820.5→32,785 (−17.7%). Solo had0failedtools; delegated2canonical-lane grep rejections, both recovered within budget and produced correct answers. Delegated completejoins2/4, fallbacks2/4, all4terminal runtimeledgers consistent with observed counts. No waiting-only terminal or executed overrun. On this limited sample solo was not better overall, while retaining simpler/error-free orchestration. No universal superiority/default readiness claim.

Measurement$7.1398668 + independent scoring$0.600395 = **$7.7402618**. Pair forecast$2.3182 exceeded remaining$8.50measurementallocation before ninth launch; actualunusedbudget does not reopen stopped trials after scoring. All12actor usage summaries (8Parents+4Readers) unchanged after recheck; source/upstream/input manifests preserved; temporaryauthremoved. No installed/main/global mutation or integration. Report `/tmp/lh-astra-solo-reader-z8pen9ds/report.md`; metrics `results.json`; scores `scoring/validated-scores.json`; stopreceipt `budget-stop.json`.

Discovery capture: completed approved bounded topology measurement in this primary evidence capsule. No independent SDD/BDD/SSOT/DDD product delta or model-default decision. TDD evidence confirms observed ledger/recovery behavior, not broader reliability. Existing coordination/semantic-verification followups remain separate; no new fix or paid matrix is authorized by the result.

### Astra fallback explanation — exact trace/source diagnosis

User asked why recovery occurred. Frozen slots2and7 both attempted native grep with `path: .lazy-harness` and `glob: {behavior,spec,tests,decisions,ssot,domain,planning,plans}/**/*` (order varies). The glob expresses canonical-layer targeting, but `isReaderRuntimeToolAllowed()` in the frozen extension lines647–662 checks only path(s), requiring an explicit canonical-layer prefix such as `.lazy-harness/spec`; it does not consider `glob` when deciding admission. Thus the umbrella root was rejected. This diagnoses the actual predicate, not a claim that every root+glob combination is safe to permit.

Neither was a read-budget overrun: terminal admitted reads2/4 (300/600lines) and3/4 (450/600lines). The shared error text mentions either lane or budget and does not identify which condition failed. Both Parents submitted explicit incomplete joins, received fallbackAllowed:true, and finished correct answers within their remaining allowances. These were two occurrences of the same grep argument/guard mismatch, not observed network failures or lost notifications. No code fix or guard relaxation is approved by this explanatory question. Discovery capture: exact empirical detail appended to the existing benchmark evidence capsule; no independent product-layer decision.

## Six-category Astra read-only comparison — approved and prepared

User approved read-only6types (short fact, multi-record synthesis, policy/code discrepancy, missing-guarantee uncertainty, bug diagnosis, hypothetical change impact), max24measuredruns/$30. Both parents Astra Medium, delegated Luna Low; same frozen source/runtime and aggregate read-call/line ceilings. Source scope remains this harness, not6independent products. First12slots coverall6types once perarm, next12reverseorder repetitions. Questionbank/oracles are grounded in actual source/records; no source bug seeded, no actual implementation task, no stopped corpus/holdout reopened.

Root `/tmp/lh-astra-six-category-LvDzmIWL`. Preparation worker cad6d9f7 timed out after30minutes with a localcopy/inspection tool call pending; its$0.164588 recorded model usage and partial artifacts are retained. Parent continued preparation without relaunching that child or any measuredcandidate. Independent reviewer2744d15c confirmed question/oracle/paireddesign validity, flagged soft spending cap and missing post-audit mandatory-condition stops; total preparation/review recorded$0.731507.

User then explicitly selected conservative headroom with possible in-flight overshoot rather than absolute request-level cap. Runner now limits measurement allocation to min($23,$30-controlcost-$3scoringreserve), retains pairforecast stop, and stops after saved audit on failed mandatory model/root/identity/ledger/Parentbudget/source/mutation/credential checks. Actual Reader admissions are mandatory; raw denied Reader attempts and ordinary recoverable lookup errors remain separate outcome diagnostics. Prior bad integrity cannot be silently resumed.9offline design/admission tests PASS and zero-model SDK preflight PASS.

Final pre-launch manifest verification detected preparation drift in362files across host/upstream copies. Inspected diffs include formatting, but the complete cause is not asserted. Original archived snapshots are intact. Changed preparation copies were preserved under `preflight-drift-preserved/`; exact original manifest-matching bytes restored, and frozen source/upstream made non-writable (git and derived host runtime directories remain writable; dependency symlink targets untouched). All input/source/upstream hashes then PASS. No measuredtrial existed, so no candidate result was repaired or rerun. Details `preflight-source-drift.json`; original review and disposition preserved. This guards against treating preparation tooling as implicitly read-only.

Discovery capture: new approved experiment and preparation blockers captured in existing primary evidence capsule; no independent product-layer semantic delta or integration/default decision. Results remain unknown until actual trials and independent scoring finish. Main/installed/global settings are not modified by this work.

### Six-category terminal result — cost/context advantage, latency disadvantage

All24planned measurements completed once (12perarm, two repetitions of six read-only types), no retry or midmatrix change. Independent blinded scorer530e6d14: semanticPASS12/12 each, essentialclaims50/50 each, substantiveanswers12/12 each, uncertaintycalibration sound for all24. No material errors/essential omissions identified; citation imprecision recorded separately. Complete identical source evidence supplied; no scoring correction needed.

Solo vs Reader: mean elapsed83.191→93.606s (+12.5%); median75.516→81.334s (+7.7%); mean cost$0.778426→$0.595361 (−23.5%); median Parent peak context36,177.5→21,532.5 (−40.5%). The broader trial reverses the earlier small-sample speed advantage: Reader is cheaper/context-lighter but not generally faster. Accuracy is tied at a ceiling; do not claim greater intelligence, universal superiority, or automatic/default routing readiness.

Per-type means (solo→Reader seconds; dollars): short82.506→76.060;$0.7620→$0.5269; multi-record65.111→108.791;$0.5657→$0.7045; policy-code67.561→91.993;$0.6349→$0.6462; missing-guarantee70.091→63.961;$0.7285→$0.3007; bug-diagnosis87.729→92.683;$0.9130→$0.6669; impact126.147→128.148;$1.0665→$0.7271. Alltypes2/2 semanticPASS perarm. Multi-record was worse on both cost/time with delegation; document count alone is not a proven selection rule. Six task types share trace/runtime/validation themes, not six independent products; no code-writing outcome or forced-outage/steer stress suite measured.

Reader10/12completejoins,2fallbacks,1failedtool; solo0failedtools. Slot16 join supplied5paths against6runtime-recorded reads (knowledge-graph-storage.md omitted), correctly rejected then recovered. Slot21 Parent explicitly chose conflict join after complete Reader packet; successful fallback transition, not failedtool/crash. Both finalanswerspassed. Multi-record Reader times78.223/139.358s vs solo64.400/65.821; bug Reader78.137/107.228 vs solo87.194/88.263. Fallback contributes to variation but even nonfallback multi-record was slower. With2repetitions no statistical tail-stability claim.

All12Reader ledgers match admitted counts/lines, all24declared read budgets/mandatorychecks conform. No waiting-only terminal, wrongidentity/root/model or mutation observed. Rechecked36actor usage summaries match; source/upstream/input hashes preserved; temporaryauthremoved. Measurement$16.4854396 + scoring$0.617431 + preparation/review$0.731507 = **$17.8343776** in this experiment. Includes failedprepchild; separately unmetered interactive Parent overhead excluded. Under$30target/$23measurementallocation. No main/installed/global mutation or integration.

Report `/tmp/lh-astra-six-category-LvDzmIWL/report.md`, metrics `results.json`, scores `scoring/validated-scores.json`; all preparation failures/drift originals and reviewdispositions remain preserved. Discovery capture: completed approved measurement; evidence favors a cost/latency tradeoff rather than unconditional Reader adoption. No independent SDD/BDD/SSOT/DDD product delta or new model-default decision. Existing followups remain separate and unapproved for implementation.

## Automatic trusted path handoff repair — isolated

User explicitly approved runtime-owned automatic path handoff after the six-read/five-submitted slot16 failure. `lazy_reader_join` now derives ALL successful paths from the trusted terminal ledger, accepts omitted/empty/distinct-subset legacy path assertions without narrowing that set, and rejects unread/outside/duplicate/malformed assertions. All ledger paths are canonical-checked and rehashed before caching, including any omitted from the Parent list. Effective paths are returned in join details. Identity, native content delivery, counters/budgets/failure checks are unchanged. Prompt/README recommend omitting already runtime-owned fields instead of recopying them.

Primary TDD `.lazy-harness/tests/pi-agent-package.md` records SDD/BDD deltas and SSOT/DDD no-independent-delta matrix. Shipped self-test adds six-read/five-path, omitted-path, unsafe assertion and omitted-file hash/cache coverage. Supplementary actual child-SDK tests cover six distinct reads, empty/default/subset paths, unread/external/traversal/absolute/duplicate/malformed assertions and changed/deleted omitted files. Existing actual nativeCLI/detached Reader lifecycle regression retained.

Scoped evidence root `/tmp/lh-reader-path-handoff-2RXt3zGH` preserves before copies and logs.31offlineSDK/nativeCLItests,266assertions PASS (9.69s); strict resolvedhost TypeScript PASS. LSP identified newly introduced test-helper name shadowing, fixed before execution; remaining standalone externaltest diagnostics concern preexisting Bun/type-only-export resolution, not a claim of clean upstream types. Independent fresh review e2b8c33c OK (read-only review, no independent rerun). Source policy/capability resolve returned no matching extra rule; code-organization applied locally, no line-count splitting/unrelated refactor. Final standard validation pending below.

No installed runtime/main/global changes, new paid benchmark, or performance improvement claim. This repairs a reproducible handoff failure, not semantic correctness. Previous benchmark archives remain immutable. Graph/index updated with one new implementation mapping; legacy migration untouched.

### Path handoff shipped-fixture checkpoint

Initial standard run failed (99.288s), retained in `standard.log`. Focused diagnosis found two existing phrase-contract checks whose terminology had been removed from updated prompt/README, plus a newly added synthetic notification missing the real native completion prefix. Restored the counter terminology while retaining automatic defaults and corrected the fixture notification; production notification authentication was not weakened. Focused `check_pi_package_layout_and_contract` now PASS, including full-path cache invalidation. These preparation/test failures are preserved in focused logs rather than relabeled. No implementation-source change followed independent review; only prompt wording and fixture transport fidelity were corrected. Final standard rerun follows this last coherent correction.

### Automatic path handoff terminal validation

Final standard PASS80.335s with fresh full regression (`evidenceReused:false`, no errors);31offlineSDK/nativeCLItests266assertions and focused shipped-package fixtures PASS; resolvedhost TypeScript PASS. Independent review e2b8c33c OK; minor fixture/wording corrections after review are documented above. Receipt `/tmp/lh-reader-path-handoff-2RXt3zGH/final-validation.json`, patch `repair.patch`, hashes `final-source-manifest.json`. No revised live-model benchmark or deployment performed. Model handoff omission is structurally repaired without permitting unread evidence or weakening existing identity/hash/budget guards.

## Automatic-handoff six-category remeasurement — terminal

User approved same6categories×2reps×2arms, NEWmax24/$30target with conservativeheadroom. Evidence `/tmp/lh-astra-handoff-remeasure-PQfqgX2u`, artifactmanifest `a932fedc6c9b52e73c566b0368ac2fda3f0e926cb84e4521c7570650e1f3c9b1`. Prepworker1f37f092 failedbeforechildstart(create undefined,0reportedusage); user explicitlyapproved Parentdirectpreparation; preservedfailure. Twozero-modelSDKpreflights, genuine scriptednativeCLItest and9offlinedesigntestsPASS. No main/installed/global mutation.

24/24completed, allintegrity/budgetchecksPASS. Independentblindscorer755f3bf7: solo12/12(50/50claims),Reader11/12(49/50claims), allsubstantive. Reader slot3fallback answer incorrectly treated knowledge/*.jsonl universally ascanonical, includingcandidates/drafts; originalfailure andscorepreserved. All12joincalls omittedrecordPaths; all10completejoins returnedexacttrustedledgerpathset,0pathhandoffmismatches. TwoReadergrep umbrella-path failures(slots3,7) producedincompletejoins/fallback; remaininglookupissue wasnotpartofapprovedrepair. Totalfallbacks2/12 unchangedfromprior, notzerofailureclaim.

Solo/Reader meantime86.865/95.323s, median80.110/91.605s, meancost$0.7801085/$0.58467149, medianParentcontext36,628/22,784.5. Readercost−25.1%, context−37.8%, meantime+9.7%; noaccuracy/speedwin. Measurement$16.37735984+scoring$0.571300=total$16.94865984; Parentinteractiveoverheadseparatelyunmetered.36actorusagesummaries/all12ledgers verified; source/upstream/inputmanifestshashes and24originalanswerhashes unchanged; disposableauthremoved. Oldsixcategorysnapshot+8approvedhandofffiles inbotharms; no unrelatedgraph/capsule updatesinmeasurementcandidate. Previouscomparison is historical, notcausalpatch-onlytrial.

Discoverycapture: thissingleevidencecapsule recordsapproval/results/residuallookupissue; no newcanonicalrule or automaticmigration. Detailedmetrics,categorybreakdown,scoreandreceipts in report.md/results.json/scoring/validated-scores.json/usage-verification.json.

### User-confirmed evaluation priority

User considers the measured modest latency increase acceptable and gives substantial weight to lower cost and lower Parent context (−25.1% and −37.8% in this trial). This is an evaluation preference, not approval to tolerate incorrect answers, deploy/install the candidate, change global defaults, or launch additional paid trials. The observed 11/12 Reader correctness and remaining lookup failures stay visible as separate quality concerns.

## Production integration preparation — blocked on distribution route

User approved integration preparation/validation only, not commit/push/merge/install/settings. Read-only discovery and scratch three-way probes captured in `/tmp/lh-reader-integration-prep-q6oyf1oh/{report.md,comparison.json,merge-probes/}`: same HEAD58fbcbf, existing main uncommitted work, 11 overlapping text-conflict files. Native installed/tested packages both0.66.0 but5repairfiles differ; inspected installed notifier lacks required tested completion identity/drain wiring. Globalharness binding uses maincheckout; nativebinding is npm:pi-subagents. Distribution/ownership route needs confirmation before preparing deployable pair. No source integration or installed-combination smoke performed; main/global untouched.

### Production risk review — user-requested, no implementation

Detailed findings `/tmp/lh-reader-integration-prep-q6oyf1oh/report.md`. Offline actualnative installed-copy/newharness combination FAILED13.93s: Parent settled~6.54s beforeReader terminal content; same fixture with testedpatchednative PASS10.71s/30assertions. Zero paidmodel calls; installed/main source unchanged. Confirmed prerequisite: paired native delivery repair, notharness-only activation. Found additional AGENTS.md:39 manualpath/counter guidance inconsistent with prompt automaticdefaults; remeasurement had explicitomission instruction so normalgrammaralignment remainsunverified.11textconflicts are records/planning/JSONL, mostlystatus/scenario differences; runtimecodehasnooverlappingmain edits, selftesttextmergecleanbutcombinedexecutionuntested. Preserve main-onlypolicies/manifests and append-onlyknowledge; no blanketours/theirs. Matching0.66.0 versiondoesnotidentify patchedruntime; distribution/rollback route unresolved. Known2grep failures/1semantic error and no code-writing/TUIdeployment coverage remain separate. This capsule captures findings only, not permission to fix/deploy or a passing integrated release.
