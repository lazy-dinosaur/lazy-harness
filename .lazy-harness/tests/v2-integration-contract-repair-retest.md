# TDD — V2 T1 integration contract repair and bounded retest

## Rule digest

- Status: advisory
- Layer: TDD
- Scope: host-project
- Scope note: host-specific experiment package
- Aliases:
  - T1 integration contract repair
  - 통합 계약 재시험
- Applies when: `tr-int-live-09` failure or the separate `tr-int-live-10` contract-repaired T1 retest is interpreted.
- Must: distinguish undisclosed fixture schema from model error; require accurate ordinary unified-diff paths and hunk counts; preserve failed runs and predecessor bytes; never promote posthoc format diagnostics to live-run success or canonical knowledge.

## Owner-approved work unit

The owner approved one separate preserved sibling, a participant-visible field/patch contract repair, and one bounded real-model T1 retest. The run remained requirement-following integration rather than retrieval-effectiveness or production verification. The approval prohibited fallback, retry loops, hidden gold, canonical apply, and replacement of failed downstream stages with scripted success.

## Cause audit

`tr-int-live-09/rendered-parent-review/work.json` supplied the baseline function and natural-language rule but did not name `recurrence_freq`, `recurrence_exceptions`, `update_exceptions`, or null-vs-non-null recurrence semantics. Therefore the 09 model's alternate field and operation names are not a proven violation of a disclosed fixture contract. The proven direct 09 failure is the extra `*** End Patch` row, rejected as `PATCH_ROW_DENIED` before bwrap behavior execution.

The frozen source `D05-F006-A04` requires three joint conditions, stable deduplication, a non-null recurrence test, an other-owner permission check, and series soft delete otherwise. `tr-int-live-10` exposed those meanings as a public disposable-fixture API without private rubric data or gold implementation. It also explicitly required one ordinary unified diff, accurate hunk counts, the sole path `clinic_rules.py`, and no fence or Begin/EndPatch sentinel.

## Regression outcome

Focused offline safety validation passed 5 tests before dispatch. It covered the 10 public source scenarios inside the existing bwrap isolation plus negative path, context, hunk-count, sentinel, fence, stale-run, preservation, and request-disclosure checks.

The one live retest made two settled calls: Reader 1680 and Work 1681. Work used the disclosed fields and source-backed branch semantics, retained `claimed_test_status=not_run`, and omitted forbidden sentinels/fences. Its hunk header claimed old=5/new=18 while its actual rows were old=4/new=20. The strict parser stopped with `PATCH_HUNK_COUNT_MISMATCH`; actual bwrap behavior testing, Recorder, Digester, and fresh semantic review did not run. There was no retry. A separately labeled posthoc header-only diagnostic passed all 10 bwrap assertions, but is not live T1 success or reviewer evidence.

Cost increased by $0.0014300, from spent $32.24717571 to $32.24860571; held remained $2.04543422. Unknown holds 1, 895, and 989 remained. Calls were 2 of at most 8. No canonical knowledge was applied.

## Layer completeness

| Layer | Independent delta? | Decision |
|---|---|---|
| SDD | no | The schema is an experiment-only participant contract, not a product API/component contract. |
| BDD | no | No product-visible flow changed. |
| SSOT | no | Existing ledger, budget, provider route, and ownership rules were used without changing their authority. |
| DDD | no | Synthetic fixture names and outcomes do not establish production domain rules. |

## Evidence capsule

- Plain Korean report: `experiments/v2-agentic-wiki-fragment-01/tr-int-live-10/report-ko.html`
- Evidence capsule: `experiments/v2-agentic-wiki-fragment-01/tr-int-live-10/evidence-capsule.json`
- Raw requests: `broker/request-1680.json`, `broker/request-1681.json`
- Raw outputs: `responses/reader.json`, `responses/work.json`
- Failure: `failure.json`
- Format-only diagnostic receipt: `runs/posthoc-format-only/test-receipt.json`
- Preservation manifest: `preservation-manifest.json` (128 files, zero mismatch at checkpoint)

## Implementation map

- `experiments/v2-agentic-wiki-fragment-01/tr-int-live-10/render_requests.mjs`: publishes the participant-visible fixture and strict patch contracts; builds role requests.
- `experiments/v2-agentic-wiki-fragment-01/tr-int-live-10/sandbox_adapter.py`: strict single-file unified-diff parser and bwrap-only materialization/test boundary.
- `experiments/v2-agentic-wiki-fragment-01/tr-int-live-10/root_test_t1.py`: read-only root oracle for the 10 disclosed source scenarios.
- `experiments/v2-agentic-wiki-fragment-01/tr-int-live-10/test_live_integration.py`: focused positive and negative regression coverage plus predecessor preservation checks.
- `experiments/v2-agentic-wiki-fragment-01/tr-int-live-10/run.mjs`: single-use guarded Reader→Work→root-validation→Recorder→Digester→review sequence with failure stop.
- Primary planning context: `../planning/v2-vision-feasibility-research.md`.

## Unified stage-contract offline repair — sibling 11

The owner corrected the framing: coherent input/output/validator/next-stage contracts are basic harness engineering responsibility, not optional design. The preserved sibling `experiments/v2-agentic-wiki-fragment-01/tr-int-contracts-offline-11/` fixes that independent contract delta without rewriting 09/10 evidence or promoting the posthoc 10-assertion result to live success.

`contract.json` v1.0.0 is the single declaration used by rendered participant instructions/examples, exact model-output validators, and next-stage builders. Stage payloads remain distinct inside one envelope. Host provenance is a separate wrapper: model fields cannot contain trusted hashes, byte/line counts, commands, exit/test status, approval, controller confirmation, or apply state. Work returns only the allowed relative path plus complete content; the host computes diff/hash and runs root assertions in the preserved bwrap boundary. Recorder cannot report success against a failed host receipt, and failed/nonzero/timeout/stage-error flows cannot produce downstream successful artifacts. Citation-object existence is mechanical; semantic meaning remains reviewer judgement.

Focused offline validation: `python3 -m unittest -v test_contract_chain.py` passed 9 tests. It covers actual rendered request→schema→validator→next-input for all five stages; invalid JSON/version/missing/extra host field; task/stage/swap/hash tamper; traversal/absolute/other path/symlink/stale run; actual nonzero and timeout plus stage error; no downstream success after failure; retain/null rewrite `not_applicable`; legitimate update proposal; cited-object existence without keyword semantics; bwrap/network/synthetic-root/no-credential/read-only-oracle/resource boundaries; and immutability of selected 09/10 evidence. `offline-evidence/evidence-index.json` preserves normal and failure summaries. These are explicit authored/mock outputs, not empirical model evidence.

### Layer completeness

| Layer | Independent delta? | Decision |
|---|---|---|
| SDD | no | The versioned contract remains experiment-local and is not a production API/component contract. |
| BDD | no | No user-visible product flow changed. |
| SSOT | no | Provider, ledger, authority, and canonical-apply ownership are unchanged. |
| DDD | no | Disposable fixture names and rules establish no production domain rule. |

### Implementation map

- `tr-int-contracts-offline-11/contract.json`: authoritative versioned envelope, stage payload, public instruction/example, operation, and controller non-apply definition.
- `chain.py`: derives renderers, validators, host provenance wrappers, and next-stage builders.
- `sandbox_adapter.py`: precondition-checked complete-file materialization, host diff/hash, and constrained bwrap receipt.
- `offline_fixture.py`: explicit authored-output full-chain and failure-stop evidence; no provider call.
- `test_contract_chain.py`: nine focused contract/chain/isolation/preservation regressions.
- `live_runner.py`: default-off/non-dispatch future gate stub; no import-time dispatch.

## Finished contract wiring — sibling 12

The user correction is authoritative: **“basic consistency is engineering responsibility.”** Parent review rejected sibling 11 as completion for two concrete reasons: `chain.py` replaced frozen 07 source evidence with an English paraphrase plus `Unrelated...` placeholders, and `live_runner.py` hard-coded `provider_dispatch_implemented:false` and always exited 2. The preserved sibling `experiments/v2-agentic-wiki-fragment-01/tr-int-contracts-finished-12/` repairs exactly those gaps without modifying 07/09/10/11 bytes and without authorizing or making a paid trial.

`source_packet.py` now imports T1 and all three supplied candidates from the frozen 07 files, verifies the evidence packet path/hash plus every original source-file hash and exact decoded quote/quote hash, and carries exact path/hash/line/quote metadata into the Reader request. `canonical_copy()` preserves the exact D05-F006-A04 quote and lineage. No placeholder candidate text remains.

`live_runner.py` is now the working authoritative Reader → Work → bwrap receipt → Recorder → Digester → fresh Reviewer orchestrator. Offline tests inject only the transport; they still route the full production runner and execute generated `clinic_rules.py` in the approved bwrap boundary. The live transport calls `provider_bridge.mjs`, which imports the installed guarded broker from 09/10; there is no direct SDK configuration fallback or ledger/reservation bypass. Default remains dry-run. Live mode requires `--live`, the separate `EXPLICIT_T1_LIVE` approval token, exact current-ledger preflight, a 5–8 call declaration, allocation at most $1, and a new output directory. No paid dispatch was performed.

Host wrappers now validate expected predecessor request/output hashes in addition to task, contract version, kind, and self hash/byte consistency. A failed or malformed stage, provider timeout/unknown transport, or nonzero host receipt stops the chain without retry or downstream model call. Model summaries remain claims; host bwrap outcome is authoritative.

Focused validation passed 17 tests. Persistent fixture-origin trace and report are linked by `experiments/v2-agentic-wiki-fragment-01/tr-int-contracts-finished-12/evidence-capsule.json` and `report-ko.html`. Readback recorded spent $32.24860571, held $2.04543422, latest 1681, unknown-held 1/895/989; the offline run preserved ledger bytes.

### Layer completeness

| Layer | Independent delta? | Decision |
|---|---|---|
| SDD | no | The repaired contract and runner remain experiment-local rather than a production API/component contract. |
| BDD | no | No product-visible flow or actual model trial occurred. |
| SSOT | no | Existing provider route, ledger, budget, authority, and canonical-apply ownership are unchanged. |
| DDD | no | Exact frozen source is evidence input; the disposable fixture does not establish a new production domain rule. |

### Implementation map

- `tr-int-contracts-finished-12/source_packet.py`: exact frozen-07 path/hash/quote loader and verifier.
- `tr-int-contracts-finished-12/chain.py`: contract-derived renderer, validator, predecessor-bound wrappers, next-stage builders, and exact canonical copy.
- `tr-int-contracts-finished-12/live_runner.py`: default-off production orchestration and injectable transport seam.
- `tr-int-contracts-finished-12/provider_bridge.mjs`: live-only adapter to the existing guarded Luna broker.
- `tr-int-contracts-finished-12/test_finished_runner.py`: source integrity, authorization, full offline transport-seam orchestration, stop/no-retry, ledger, and schema regression coverage.
- `tr-int-contracts-finished-12/offline-evidence/actual-entrypoint-success/`: request/response/host-receipt fixture trace from the production runner.
- `tr-int-contracts-finished-12/evidence-capsule.json`: concise evidence and readback index.
- `tr-int-contracts-finished-12/report-ko.html`: required human-readable completed-versus-untested report.

## Owner-approved actual T1 live run — sibling 13

The owner explicitly authorized one `EXPLICIT_T1_LIVE` run with five normal calls maximum, no retries, allocation at most $1, the existing global-$80/stage-$8/reserve-$2.60 limits, the installed guarded Luna-medium `openai-codex-responses` SSE route, manual redirect denial, and `maxRetries=0`. The non-overwriting execution copy `experiments/v2-agentic-wiki-fragment-01/tr-int-contracts-actual-13/` preserved sibling 12. Before dispatch its client response wait was mechanically aligned to 270 seconds, beyond the guarded broker's existing 240-second abort deadline, so ledger settlement or unknown-hold persistence could finish; focused validation passed 17 tests.

Fresh preflight matched spent $32.24860571, held $2.04543422, latest 1681, and unknown-held 1/895/989. The live chain reached Reader receipt 1682, Work receipt 1683, and host bwrap validation. Reader selected D05-F006-A04 and stated the relevant branch, stable dedupe, permission, and soft-delete requirements. Work returned a complete `clinic_rules.py` that implemented those branches, but its `update_exceptions` result added `master_id` and `occurrence_date` keys beyond the trusted fixture oracle's required result shape. The read-only oracle failed its first strict equality with `HOST_EXECUTION_NONZERO_EXIT` (exit 1, 42.996 ms). The runner stopped without retry; Temporary Recorder, Digester, and fresh semantic Reviewer were not called, so no record text, knowledge proposal, or reviewer finding exists and semantic success is not claimed.

The two settled calls cost $0.0024666 total and 64,832.814 ms provider wall time. Readback was spent $32.25107231, held $2.04543422, latest 1683, with unknown-held 1/895/989 unchanged. No fallback, canonical apply, Medivance/DB operation, commit, migration, install, settings change, or search expansion occurred. This is one authored requirement-following supplied-candidates fixture failure, not retrieval, production, or general V2 readiness evidence.

### Evidence capsule

- Korean report: `experiments/v2-agentic-wiki-fragment-01/tr-int-contracts-actual-13/report-ko.html`
- Execution capsule: `experiments/v2-agentic-wiki-fragment-01/tr-int-contracts-actual-13/actual-live-evidence-capsule.json`
- Raw Reader/Work: `runs-live/t1-actual-epoch139-01/responses/reader.validated.json`, `responses/work.validated.json`
- Host receipt and diff: `runs-live/t1-actual-epoch139-01/host-outcome.json`, `runs/actual-t1/observed.patch`
- Failure stop: `runs-live/t1-actual-epoch139-01/failure.json`
- Recorder/Digester/Reviewer: absent by required failure-stop semantics.

### Layer completeness

| Layer | Independent delta? | Decision |
|---|---|---|
| SDD | no | The execution reused the experiment-local contract; no product API/component contract changed. |
| BDD | no | No product-visible flow changed. |
| SSOT | no | Existing provider, ledger, budget, route, and ownership authority remained unchanged. |
| DDD | no | The disposable fixture failure establishes no production domain rule. |

### Implementation map

- `tr-int-contracts-actual-13/live_runner.py`: executed bounded orchestration with the client deadline aligned beyond the broker-owned abort deadline.
- `tr-int-contracts-actual-13/runs-live/t1-actual-epoch139-01/`: actual provider requests/responses, route proof, generated diff, bwrap receipt, and failure stop.
- `tr-int-contracts-actual-13/actual-live-evidence-capsule.json`: hashes, source lineage, route, cost, ledger, outcome, and direct raw paths.
- `tr-int-contracts-actual-13/report-ko.html`: human-readable preparation-versus-actual result and limitations.

## Public-contract audit correction — offline sibling 14

The user's engineering correction is authoritative: a harness must audit every enforced assertion/parser/output condition against participant-visible requirements or a justified host-only security boundary, rather than blaming a model for an undisclosed fixture convention. Re-reading the actual Reader 1682 and Work 1683 requests showed that run 13 disclosed branch, stable-deduplication, permission, and nullness rules, but did **not** disclose a closed `delete_schedule` return object or forbid extra return keys. Reader 1682 also explicitly asked Work to normalize the master ID and extract the occurrence date. Therefore the prior sentence that characterized the two extra keys alone as an actual model-correctness failure was too strong. This correction preserves the original run-13 failure and raw artifacts: the strict equality oracle did fail with exit 1, but that receipt cannot by itself prove violation of the disclosed business requirements.

The separate non-overwriting sibling `experiments/v2-agentic-wiki-fragment-01/tr-int-contracts-public-audit-14/` copies and hash-checks the actual 1682/1683 request/response and exact materialized Work file. The original model file SHA-256 and the response content SHA-256 both equal `3235981c80594e96e51bdc00dcc702cea02f8b79baa50ba56e968afc502cd9a6`. An offline-only bwrap reassessment used those exact bytes, the same synthetic-root/no-network/no-credential/resource boundary, and a read-only requirement oracle. Nine disclosed-behavior scenarios had zero required-value failures. `master_id` and `occurrence_date` were recorded separately as undeclared extras, not silently accepted and not rejected as generic extras. The extra-key policy, observable master-ID normalization, occurrence-date return-field meaning, and production mapping remain unresolved.

This posthoc result is not a new model success, does not complete the provider chain, and does not overwrite the failed run. Temporary Recorder, Digester, and fresh semantic Reviewer still never ran. The live broker implementation remains present and default-off; no model call occurred. The client response deadline remains 270 seconds over the broker's 240-second abort deadline. Ledger bytes were unchanged; readback remains spent `$32.25107231`, held `$2.04543422`, latest `1683`, unknown-held `1/895/989`.

Sibling 14 contract version 1.2.0 makes stage payload closure and the actual stage-specific validator rules participant-visible from the same `contract.json` used by renderers and validators. Its T1 oracle checks only disclosed required fields/values and reports undeclared extras/input mutation separately. Eleven focused offline tests cover all five stage request→schema→validator→next-input paths plus materially different negatives: wrong operation, lost date, false-as-null, dedupe loss, permission error, false-success promotion, traversal/newline/payload closure, Recorder contradiction, Digester rewrite policy, Reviewer completeness, and harmless-extra controls. These tests establish fixture-oracle guard behavior only, not production correctness, model quality, or V2 readiness.

### Layer completeness

| Layer | Independent delta? | Decision |
|---|---|---|
| SDD | no | The corrected contract remains an isolated experiment-local API and does not change a product component contract. |
| BDD | no | No product-visible flow and no new model trial occurred. |
| SSOT | no | Provider route, ledger, budget, canonical ownership, and apply authority are unchanged. |
| DDD | no | The correction distinguishes disclosed fixture rules from unresolved mappings; it establishes no production domain rule. |

### Evidence capsule and implementation map

- `tr-int-contracts-public-audit-14/requirements-validation-matrix.md`: finite assertion/parser/stage/sandbox/transport matrix with actual 1682/1683 raw references and unresolved assumptions.
- `tr-int-contracts-public-audit-14/preserved-13/`: byte-identical copies of the actual requests, responses, failure, host receipt, and materialized model file.
- `tr-int-contracts-public-audit-14/public_oracle.py` and `root_test_t1.py`: disclosed-required-semantics evaluator and read-only bwrap entrypoint; extras are report-only unresolved scope.
- `tr-int-contracts-public-audit-14/posthoc-offline/receipt.json`: exact-byte hashes, sandbox receipt, ledger hash preservation, required-value observations, and extra-value assessment.
- `tr-int-contracts-public-audit-14/contract.json` and `chain.py`: future participant-visible stage contracts, renderers, validators, and next-stage builders.
- `tr-int-contracts-public-audit-14/sandbox_adapter.py`: inherited bwrap path and limits with both oracle files mounted read-only.
- `tr-int-contracts-public-audit-14/live_runner.py` and `provider_bridge.mjs`: inherited working guarded transport, default-off and unused in this correction.
- `tr-int-contracts-public-audit-14/test_public_contract_audit.py`: eleven focused stage and semantic-oracle robustness regressions.
- `tr-int-contracts-public-audit-14/report-ko.md`: corrected Korean human report headed with the no-new-call disclosure.
- `tr-int-contracts-public-audit-14/evidence-capsule.json`: the single correction capsule; it explicitly preserves run 13 as failed and absent downstream stages as absent.

## User-approved posthoc downstream continuation — sibling 15

The user explicitly approved continuing the same work unit from preserved Reader 1682, Work 1683, the original run-13 strict failure, and the sibling-14 exact-byte reassessment. The approved branch was `origin=posthoc_continuation`, not a new clean end-to-end run: no Reader/Work replay, no promotion of the original failure, and no implicit decision on extra-key policy or source-ID normalization.

The new non-overwriting sibling `experiments/v2-agentic-wiki-fragment-01/tr-int-posthoc-downstream-15/` prepared a closed public Recorder → Digester → fresh semantic Reviewer contract. Controller-owned evidence carries both `original_response` and `host_reassessment`; the model cannot author hashes, receipts, approval, apply state, or unresolved flags. Five offline tests passed, including malformed-role rejection, no hidden required payload field, exact readback of the original failure plus nine disclosed required-value passes, Digester nonmutation policy, and Reviewer completeness.

Actual dispatch stopped before the first research call. The installed guarded broker closed during readiness with `STAGE1_SOCKET_NOT_CREATED` at `fragment-role-capability-02/broker.mjs:102`. No Recorder request was dispatched, so no temporary record, digestion proposal, or fresh Reviewer finding exists. There was no retry, alternate CLI/provider/model, Reader/Work replay, or canonical apply. Ledger remained spent `$32.25107231`, held `$2.04543422`, latest `1683`, unknown-held `1/895/989`; added model cost was `$0`.

### Evidence capsule and layer completeness

- Report: `tr-int-posthoc-downstream-15/report-ko.html`.
- Capsule: `tr-int-posthoc-downstream-15/evidence-capsule.json`.
- Contract and controller: `contract.json`, `run.py`, `provider_bridge.mjs`.
- Offline regression: `test_posthoc_downstream.py` (5 passed).
- Broker preflight artifact: `runs-live/posthoc-downstream-01/provider-runtime/broker/stage-budget.json`; it is not a model receipt.
- SDD/BDD/SSOT/DDD: no independent delta. This is an experiment-local diagnostic contract and an infrastructure-stop result; product API, visible flow, authority/config ownership, and production domain rules did not change.

## Socket root-cause repair and one approved continuation — sibling 16

The sibling-15 diagnosis omitted decisive startup observability: it did not preserve the bridge argv, cwd, bounded process exit, owned stderr, or exact socket-path bytes. Direct filesystem evidence now confirms the cause rather than inferring it from the historical tiny pilot. From the project-root cwd, the requested sibling-15 relative socket pathname was 138 bytes, while Node created a socket at the first 108 bytes, ending in `posthoc-downstream-01/provide`. The broker then checked the untruncated absolute `provider.sock` pathname and raised `STAGE1_SOCKET_NOT_CREATED`. Sibling 13 has a successful route proof, but its argv/cwd/environment were not captured, so its effective bind string cannot honestly be reconstructed after the fact.

The non-overwriting sibling `experiments/v2-agentic-wiki-fragment-01/tr-int-socket-repair-continuation-16/` kept the same installed guarded broker protocol and route while putting only the broker runtime in a unique `/tmp/lh-v2-16-*` `mkdtemp` directory. It verifies mode 0700, current-uid ownership, and non-symlink status; the actual socket path was 34 bytes. Durable broker requests, responses, route proof, and diagnostics were copied into sibling 16, while only the owned socket/runtime/process was closed. A same-config 30-second startup probe made zero model dispatches, produced zero request artifacts, exited 0 with empty stderr, removed its runtime, and left the ledger byte-identical. An authored, explicitly non-gold format example passed the exact three-stage renderer→validator→next-stage chain; the forced Recorder status enum was participant-visible.

The one approved `origin=posthoc_continuation` execution then made exactly three settled research calls, receipts 1684–1686, on `openai-codex/gpt-5.6-luna` medium through the guarded Responses SSE route. Recorder 1684 truthfully kept the original strict failure separate from the qualified nine-scenario posthoc pass and preserved unresolved extra-key, ID-normalization, and production-mapping scope. Digester 1685 returned `needs_review` with no rewrite, preserved the exact-source/public-fixture distinction, and did not apply canonical knowledge. Fresh Reviewer 1686 returned an actual packet but was rejected with `REVIEW_EVIDENCE_MISSING`: it cited internal names not among the three allowed top-level visible object IDs and also claimed the three model stages had not executed, contradicting receipts 1684–1686. There was no retry or silent stage-label change; the raw Reviewer packet is evidence, not a validated semantic review or downstream completion.

All three calls settled for `$0.006465` total and 44,567.863 ms provider wall time. Readback became spent `$32.25753731`, held `$2.04543422`, latest `1686`, with unknown-held `1/895/989` unchanged. The original run 13 remains failed; sibling 14 remains a qualified host reassessment; extra-key policy and source-ID normalization remain unresolved/untested; no Reader/Work rerun, fallback, canonical apply, commit, migration, install, retrieval expansion, database, or production operation occurred.

### Evidence capsule, implementation map, and layer completeness

- `tr-int-socket-repair-continuation-16/preflight-evidence/rootcause.json`: requested/observed socket paths and byte lengths plus the run-13 observability limitation.
- `provider_bridge.mjs`: same guarded broker protocol with a short owned private runtime root, lifecycle evidence, and durable artifact copy-out.
- `run.py`: exact format-chain preflight, zero-dispatch ledger-invariance startup probe, bounded bridge diagnostics, and the unchanged three-stage continuation controller.
- `runs-live/posthoc-continuation-16-01/`: three actual requests and transport packets, validated Recorder/Digester packets, rejected raw Reviewer packet, route proofs, process diagnostics, and failure stop.
- `evidence-capsule.json`: primary exact-readback capsule with separate upstream and actual packet hashes, ledger rows, route, root cause, and reviewer rejection.
- `report-ko.html`: human-readable root cause, actual reached stages, actual Recorder and Digester content, rejected Reviewer assertions, limitations, paths, cost, and timing.
- SDD/BDD/SSOT/DDD: no independent delta. The repair and continuation remain experiment-local; no product API, visible product flow, authority/config ownership, or production domain rule changed.

## Owner-approved evidence consolidation and pause

The owner approved pausing new model calls and consolidating established findings versus harness-caused uncertainty after the repeated failures. Consistent participant instructions, output schemas, validators and handoffs are baseline engineering responsibility, not an optional feature to repeatedly ask the owner to design. Offline fixture passes must not be presented as real-model readiness or end-to-end success.

Established within bounded evidence: run 13 stopped at a strict return-object comparison whose extra-key prohibition was not disclosed; the exact same generated file passed nine disclosed-guarantee scenarios in the separate sibling-14 posthoc check. Neither finding proves extra-field semantics, master-ID normalization or production correctness. Sibling 16 actually produced Recorder and Digester outputs preserving failure/qualified-pass distinctions and returning needs_review without rewriting. Its Reviewer output was rejected; interpreting historical versus current execution facts remains a concern, not proof of a general model incapability.

Still unproved: a clean uninterrupted real-model full chain, correct incorporation of a genuine knowledge change, general reliability, retrieval/no-miss benefit, production correctness, and reduced human review effort. No aggregate success rate or usable-system readiness follows from these runs.

Proposed next minimal experiment (not dispatched or newly approved here): one already-settled work result, exact source, and one clearly dated observed event -> actual temporary record -> digestion proposal; compare against the visible source/event directly in Parent review. Keep automated reviewer evaluation separate so reviewer schema errors do not redefine actor quality. Use immutable before/after content, explicit unresolved scope, no canonical apply. Do not add more search methods, test roles, or cases until this single flow has an interpretable result. This is a proposal, not an established correction to all prior issues.

Evidence reuse: sibling-14 posthoc-offline/receipt.json and requirements-validation-matrix.md; sibling-16 actual Recorder/Digester/Reviewer packets and capsule above. Display-only consolidation: experiments/v2-agentic-wiki-fragment-01/tr-int-socket-repair-continuation-16/status-explained-ko.html. No new model request, source implementation or reassessment was performed for this consolidation. SDD/BDD/SSOT/DDD: no independent delta.

## Owner-approved minimal Recorder → Digester experiment — sibling 17

The owner approved exactly one settled work observation, one actual temporary Recorder request, and one actual Digester proposal, with direct Parent comparison against the frozen source/event and no automated Reviewer call. The selected outcome was the already-proven sibling-16 broker socket-runtime repair only: the preserved root-cause artifact records a requested 138-byte project-relative pathname versus the observed 108-byte socket pathname; the private short runtime used a 34-byte socket, passed zero-dispatch readiness with ledger bytes unchanged, and the repaired guarded route later settled actual request 1684. This does not reopen the unresolved run-13 extra-key semantics or expand into retrieval, code-work evaluation, or a full pipeline.

Before dispatch, sibling `experiments/v2-agentic-wiki-fragment-01/tr-minimal-record-digest-17/actual-run-01/` froze an exact active quote from `.lazy-harness/ssot/runtime-and-shared-state.md`, the timestamped observed-event sequence, and a four-ID public evidence registry. Five focused offline tests and authored shape examples passed. A same-configuration startup probe then reached readiness with zero request artifacts and byte-identical ledger state. The public schemas disclosed all required fields, enums, citation IDs, forbidden host-owned fields, and nullable rewrite policy. Historical event time and current task time were explicitly separated.

The actual bounded run made exactly two settled Luna-medium calls on the installed guarded `openai-codex-responses` SSE route with manual redirect denial and `maxRetries=0`: Recorder receipt 1687 and Digester receipt 1688. The host passed the validated Recorder object unaltered into the Digester request. Recorder returned `observed_with_limits`, the long-path condition, the short private `mkdtemp` action, the one-configuration scope, and evidence IDs `EVT-1` through `EVT-3`. Digester proposed `update` with a concrete broker-runtime-socket bullet and cited `SRC-1`, `EVT-1`, and `EVT-2`. That proposal has **pending Parent authority** and was not applied to the active SSOT. Structure and citation provenance were host-validated; semantic correctness was not auto-scored.

Ledger readback moved from spent `$32.25753731`, held `$2.04543422`, latest `1686` to spent `$32.25971331`, held `$2.04543422`, latest `1688`; unknown-held `1/895/989` stayed unchanged. Added cost was `$0.002176` and provider wall time was `25,191.621234 ms`. There was no retry, fallback, Reviewer call, canonical apply, commit, migration, install, settings, database, Medivance, or production operation.

### Evidence capsule, implementation map, and layer completeness

- `tr-minimal-record-digest-17/contract.json`: the two small public task schemas and rewrite policy.
- `run.py`: input freeze, authored offline validation, zero-call readiness/ledger gate, exact Recorder handoff, two-call controller, structural/provenance validation, and Korean report rendering.
- `provider_bridge.mjs`: the existing guarded route with the established short private mode-0700 `mkdtemp` runtime; argv/cwd/socket diagnostics omit credential values.
- `test_minimal_chain.py`: five focused source-freeze, schema, citation, time-boundary, and unaltered-handoff tests.
- `actual-run-01/source-before.json`, `observed-event.json`, and `evidence-registry.json`: direct Parent comparison inputs frozen before dispatch.
- `actual-run-01/requests/` and `responses/`: exact raw two-stage requests, transport packets, and actual validated model outputs.
- `actual-run-01/evidence-capsule.json`: single exact readback capsule with hashes, route, calls, cost, latency, ledger, proposal authority, and limits.
- `actual-run-01/report-ko.html`: plain Korean four-box source/fact/record/proposal comparison and limitations.
- SDD/BDD/SSOT/DDD: no independent delta. The schema and orchestration are experiment-local; the model's `update` is a non-authoritative proposal, not a changed component contract, visible product flow, runtime ownership rule, or domain rule.

## Owner-approved Digester preservation retest — sibling 18

Sibling 18 reused the byte-exact sibling-17 source, observed event, evidence registry, and actual Recorder 1687 object. Its general public instruction requires supplement-versus-replacement and target identification, preservation of unaffected assertions/conditions/exceptions/scope/ownership, evidence-backed changed/removed statements, no local-to-framework generalization, complete replacement text or a located supplement, and retain/needs_review when evidence or authority is insufficient. It contains no prescriptive socket gold sentence.

Five focused offline tests protect exact predecessor hashes, the unaltered Recorder handoff, visible enums/rendering policy, null/complete output combinations, and host append preservation. After a zero-dispatch ledger-invariance probe, exactly one Luna-medium Digester call settled as receipt 1689. The model returned a broker-socket supplement. The host-only hypothetical append retained the original broad rule byte-for-byte and applied nothing. Direct comparison still leaves the supplement's relationship to `LAZY_RUNTIME_ROOT`/`other ephemeral state` and exception authority unresolved, so schema passage and mechanical preservation are not semantic success or generalized causal improvement.

Ledger readback was spent `$32.25971331→$32.26089431`, held `$2.04543422`, latest `1688→1689`, unknown-held `1/895/989`; added cost `$0.001181`, provider wall `13,748.748404ms`. Recorder/Reviewer/retry/fallback/Jev/install/API research/canonical apply/DB/production/commit/migration calls or operations were zero. Raw request/response/capsule and Korean report are under `tr-digester-preservation-retest-18/actual-run-01/`.

### Layer completeness

| Layer | Independent delta? | Decision |
|---|---|---|
| SDD | no | The public schema is experiment-local and does not change a product API or component contract. |
| BDD | no | No product-visible flow or canonical apply occurred. |
| SSOT | no | The active runtime rule, ledger ownership, budgets, provider route, and apply authority were not changed. |
| DDD | no | One local broker observation establishes no production domain rule. |

### Implementation map

- `tr-digester-preservation-retest-18/contract.json`: one public schema for dispositions, targets, fields, enums, and rendering combinations.
- `run.py`: exact-input/hash gate, frozen prompt criteria, zero-call readiness, one-call controller, structural validation, host append/display, capsule, and Korean report.
- `provider_bridge.mjs`: existing guarded Luna-medium broker through a short owned private runtime, capped at one call and `$0.50`.
- `test_preservation_retest.py`: five focused preservation/visibility/no-gold regressions.
- `actual-run-01/evidence-capsule.json`: exact readback, hash comparison, cost/time/ledger, direct-comparison uncertainty, and raw artifact paths.

## Owner-approved observation-versus-authority retest — sibling 19

The owner approved one experiment-local same-case Digester retest to distinguish an observed workaround and evidence-supported suggestion from authority to amend or except a normative rule. The approval did not authorize a product-policy or canonical SSOT change. The new non-overwriting sibling `experiments/v2-agentic-wiki-fragment-01/tr-digester-authority-retest-19/` reused the byte-exact sibling-17 source, observed event, evidence registry, and Recorder 1687 object; sibling-17 and sibling-18 proposals were comparison-only report inputs and were not included in the model request.

The frozen general instruction required separate observational and normative outputs, comparison against existing scope/conditions/ownership, retention of the existing rule, explicit unresolved treatment when relationship or authority is unknown, and preservation of useful bounded learning. It supplied no exact disposition or socket-specific answer. Five direct semantic-review questions were frozen before dispatch, without keyword/token scoring. Six focused offline tests passed and the same-route zero-dispatch readiness probe left ledger bytes unchanged.

Exactly one Luna-medium Digester call settled as receipt 1690 on the installed guarded `openai-codex-responses` SSE route with manual redirect denial and `maxRetries=0`. The actual model packet returned `needs_review`, kept `normative_proposed_change=null`, retained a separately labeled bounded observational note and mitigation candidate, stated that the experiment supplied no authority to amend/except/supersede the active source rule, and left the relationship to `LAZY_RUNTIME_ROOT` unresolved. These are model statements for direct Parent inspection, not trusted authority assertions or a semantic success grade. The host accepted the public schema, preserved the existing rule unchanged, and applied no canonical rule.

Ledger readback was spent `$32.26089431→$32.26243471`, held `$2.04543422`, latest `1689→1690`, unknown-held `1/895/989`; added cost `$0.0015404`, provider wall `16,686.405097ms`. Recorder, Reviewer, retry, repair loop, fallback, canonical apply, product policy, Jev, install/download/settings, Medivance/DB, commit, migration, and retrieval expansion were zero.

### Layer completeness

| Layer | Independent delta? | Decision |
|---|---|---|
| SDD | no | The public schema and prompt are experiment-local and do not change a product API or component contract. |
| BDD | no | No product-visible flow or canonical apply occurred. |
| SSOT | no | The active runtime rule, ownership, route, ledger, and apply authority remain unchanged. |
| DDD | no | One local broker observation establishes no production domain rule. |

### Evidence capsule and implementation map

- `tr-digester-authority-retest-19/contract.json`: public separation of observational note, normative proposed change, authority basis, existing-rule relationship, retained assertions, and unresolved relations.
- `run.py`: exact predecessor gates, frozen criteria/questions, authored shape validation, unaltered Recorder handoff, zero-dispatch readiness, one-call controller, structural validation, non-apply assembly, capsule, and Korean report.
- `provider_bridge.mjs`: existing guarded Luna-medium broker through a short owned private runtime, capped at one call and `$0.50`.
- `test_authority_retest.py`: six focused same-input, no-gold, public-schema, frozen-question, shape, and rendering-policy tests.
- `actual-run-01/evidence-capsule.json`: approval/goal, exact input/request/response hashes, cost/time/ledger readback, review questions, and bounded limitations.
- `actual-run-01/report-ko.html`: Korean-first direct comparison of original, sibling-17 proposal, sibling-18 preservation proposal, sibling-19 model packet, dated facts, retained/unknown statements, and raw request/response links.

## Owner-approved three-disposition Digester run — sibling 20

The owner approved exactly three actual Digester calls under one strengthened general instruction and one public schema: keep a correct rule when a later event adds no durable fact, append a compatible authorized fact without rewriting the original, and replace only an explicitly authorized affected part while preserving everything else. The new non-overwriting sibling `experiments/v2-agentic-wiki-fragment-01/tr-three-disposition-20/` reused frozen source `D04-F028-A04` for three neutral-ID, self-contained authored simulations. Source lineage, event authorship/confidence, experiment-copy-only authority, private expected meaning/allowed alternatives, and input hashes were frozen before dispatch. The cases are not independent samples and do not claim actual Medivance policy changes.

Seven focused offline tests passed before dispatch. A same-guard mode-0700 short-private-runtime readiness probe made zero model requests and left ledger bytes unchanged. Exactly three Luna-medium calls then settled through the installed guarded `openai-codex-responses` SSE route with manual redirect denial and `maxRetries=0`, receipts 1691–1693, with no retries, fallback, Recorder, Reviewer, retrieval, canonical apply, or production/DB operation. KAPPA returned a schema-valid retain that preserved all original behavior. LAMBDA's raw text expressed a useful, non-lossy located audit supplement but added an extra top-level `envelope` wrapper; the disclosed public validator rejected it, no next-stage render was produced, and it remains a failed case rather than being repaired post hoc. MU returned a schema-valid complete replacement changing only the explicitly authorized old-action deactivation clause in the experiment copy while retaining every other source condition.

The evidence-linked manual first pass therefore records 2 accepted useful/non-lossy outputs and 1 public-schema failure with useful raw semantic intent; it is not Parent certification or an enum-match benchmark. Ledger spent moved `$32.26243471→$32.26520831`, held stayed `$2.04543422`, latest moved `1690→1693`, and unknown-held `1/895/989` stayed unchanged. Added runtime-reported cost was `$0.0027736`. Provider model-wall sum was `58,024.646841 ms`; actual first-dispatch-to-last-response wall was `58,087.419943 ms`, leaving nonnegative measured controller overhead `62.773102 ms`. Preparation-to-report timing is stored from the real UTC/monotonic start and explicitly excludes later Parent final review; it is not total human/developer time.

### Layer completeness

| Layer | Independent delta? | Decision |
|---|---|---|
| SDD | no | The shared schema, validator, and renderer are experiment-local and do not change a product API or component contract. |
| BDD | no | Authored simulations and an unapplied copy render do not change a product-visible flow. |
| SSOT | no | No actual Medivance rule, provider setting, budget owner, ledger policy, or apply authority changed. |
| DDD | no | The three simulations establish no production domain rule and reuse one source rather than independent samples. |

### Evidence capsule and implementation map

- `tr-three-disposition-20/contract.json` and `cases.json`: one public output contract plus neutral self-contained source-before/event/authority packets with exact frozen lineage.
- `run.py`: identical general instruction, private pre-dispatch expected-meaning freeze, zero-dispatch readiness, exactly-three-call controller, same public validator, next-stage render, separate timing measures, capsule, and Korean report.
- `provider_bridge.mjs`: installed guarded Luna-medium route, three-call cap, `$1` maximum allocation, short private runtime, no fallback/retry.
- `test_three_disposition.py`: seven focused source-lineage, no-gold, common-instruction/schema, rendering, event disclosure, and guard-bound tests.
- `actual-run-01/requests/`, `responses/`, and `rendered/`: exact inputs, raw transport, accepted/invalid outputs, and only valid next-stage renders.
- `actual-run-01/manual-first-pass.json`, `summary.json`, `evidence-capsule.json`, and `report-ko.html`: evidence-linked first pass, receipts/cost/timing, exact readback, and Korean Parent-inspection report.

## Owner-approved offline wire-format repair — sibling 21

The owner set the current priority to step-1 offline response-format repair only. Jev, low-parallel synthesis, threshold batch-parallel, multi-query/links, paid calls, and full-flow execution remain future ideas already held in Parent planning and are not duplicated or implemented here. The short non-overwriting sibling `experiments/v2-agentic-wiki-fragment-01/tr-wire-normalization-21/` adds one lossless compatibility rule: prefer the canonical envelope directly, or accept one outer object whose sole key is `envelope` and unwrap it exactly once before applying the unchanged sibling-20 full binding, payload, citation, rendering, unknown-field, and host-ownership validation.

Offline replay read the exact KAPPA, LAMBDA, and MU transport texts from actual run 20 through the shared parser, validator, and renderer. KAPPA and MU remained direct; LAMBDA became explicitly `normalized`, while its original model-contract compliance remains false and the original run-20 failure artifact remains failed and byte-unchanged. LAMBDA's unwrapped JSON value equals the validated canonical value and its proposal text is unchanged. This is posthoc compatibility evidence, not empirical model improvement or semantic certification. Structural acceptance remains separate from manual semantic review; no keyword score or three-parses-imply-quality rule exists.

The replay made zero paid calls and no canonical apply. Exact ledger readback stayed unchanged before/after: spent `$32.26520830999992`, held `$2.0454342200000015`, latest receipt `1693`, unknown-held `[1,895,989]`. Actual replay start-to-report elapsed time and link-check results are stored in `offline-replay-01/summary.json`; no model-time claim is made.

### Layer completeness

| Layer | Independent delta? | Decision |
|---|---|---|
| SDD | no | The normalization contract is experiment-local and changes no public product API or framework component contract. |
| BDD | no | Offline replay and an unapplied experiment-copy render do not change a product-visible flow. |
| SSOT | no | Host authorization, canonical ownership, provider route, budget, and ledger policy remain unchanged. |
| DDD | no | Wire compatibility creates no production domain rule or semantic correctness claim. |

### Evidence capsule and implementation map

- `tr-three-disposition-20/wire_normalizer.py`: duplicate-aware, byte/depth-bounded JSON parsing; direct-or-one-wrapper classification; recursive host-owned-field denial; raw/canonical hashes and transformation metadata.
- `tr-three-disposition-20/run.py`: actual runner validates expected transport stage/case/text, imports the shared normalizer with `ALLOW_SINGLE_ENVELOPE_WRAPPER=False`, and preserves the installed broker/guard/private socket and 270-second timeout path without SDK changes.
- `tr-wire-normalization-21/contract.json`: public accepted-wire-form contract with canonical-direct preferred and one lossless wrapper compatibility form.
- `tr-wire-normalization-21/replay.py`: exact run-20 offline replay through the shared validator and next-stage renderer, ledger/original-artifact readback, Korean report, and link check.
- `tr-wire-normalization-21/test_wire_normalization.py`: direct/wrapper positives plus duplicate keys, mixed siblings, nested wrappers, multiple/trailing JSON, types, missing/unknown/binding/citation, forged host fields, byte/depth, no-repair, default-off, and exact LAMBDA losslessness cases.
- `tr-wire-normalization-21/offline-replay-01/{summary.json,evidence-capsule.json,report-ko.html,link-check.json}`: direct/normalized outcomes, equality and unchanged-text proof, immutable run-20 hashes, exact ledger readback, limitations, Korean human report, and checked links.

## Owner-approved new-task full-flow attempt — sibling 22

The owner approved one fresh Reader → Work → host behavior test → Temporary Recorder → Digester experiment using the frozen-07 T2 Chat memo existing-row exception. The non-overwriting sibling `experiments/v2-agentic-wiki-fragment-01/tr-new-task-fullflow-22/` froze the exact three supplied fragments, complete public fixture inputs/outputs and twelve behavior assertions, source/fixture/host/apply authority, requirements-to-test mapping, expected meaning, and allowed alternatives before dispatch. It enabled the sibling-21 lossless one-wrapper normalizer for this new run while preserving direct, normalized, rejected, and original-contract-compliance states separately.

Six focused offline tests passed once, including the actual bwrap boundary, full request handoff, direct/wrapper acceptance, duplicate/mixed/nested/multiple/type/binding/extra/host-field negatives, failure semantics, and Digester retain rendering. A same-route private-mode-0700 readiness probe made zero model calls and left the ledger byte-identical. The actual run then settled Reader receipt 1694 and Work receipt 1695. Reader was canonical-direct and selected `D04-F037-A02`. Work returned complete fixture source whose branch text appears aligned on bounded direct inspection, but its public payload used `file` as a string and placed `content` beside it instead of the disclosed `file:{path,content}` object. The unchanged full validator rejected it with `PAYLOAD_INVALID`; this was not a one-wrapper case and was not repaired. Therefore actual host execution, Temporary Recorder, and Digester did not run. No retry, gold substitution, unauthorized continuation, canonical apply, or product operation occurred.

Ledger spent moved `$32.26520830999992→$32.26687890999992`, held stayed `$2.0454342200000015`, latest moved `1693→1695`, and unknown-held `[1,895,989]` stayed unchanged. Added runtime-reported cost was `$0.0016706`; provider wall sum was `20,113.500471 ms`, first-call-to-last-response wall was `20,154.774449 ms`, and measured controller overhead was `41.273978 ms`. The Korean report exists at `actual-run-01/report-ko.html` and labels the schema-valid Reader, rejected Work call, absent downstream stages, raw semantics, and unresolved production scope without claiming whole-flow success.

### Layer completeness

| Layer | Independent delta? | Decision |
|---|---|---|
| SDD | no | The public full-flow schema and normalizer enablement remain experiment-local and change no product API or framework component contract. |
| BDD | no | The disposable fixture attempt stopped before host execution and changed no product-visible flow. |
| SSOT | no | Frozen source authority, provider route, budget, ledger ownership, and canonical-apply ownership were reused unchanged. |
| DDD | no | One failed authored-fixture transport shape establishes no production domain rule. |

### Evidence capsule and implementation map

- `tr-new-task-fullflow-22/contract.json`, `run.py`, `root_test_t2.py`, and `wire_normalizer.py`: disclosed four-stage contract, actual guarded controller, immutable bwrap oracle, and reused lossless normalizer.
- `tr-new-task-fullflow-22/test_fullflow.py` and `offline-check-receipt.json`: six pre-dispatch checks, including one actual sandbox run and negative shape/chain checks.
- `tr-new-task-fullflow-22/actual-run-01/{input-freeze.json,requirements-test-mapping.json,preflight.json}`: exact source/meaning/authority/test freeze and zero-call readiness.
- `tr-new-task-fullflow-22/actual-run-01/requests/` and `responses/`: exact Reader and Work requests, transport receipts, accepted Reader, and preserved rejected Work text.
- `tr-new-task-fullflow-22/actual-run-01/{normalization,summary.json,failure.json,evidence-capsule.json,closeout.json,report-ko.html}`: direct-versus-rejected classification, actual stop, corrected two-receipt accounting, plain-Korean report, and non-apply evidence.

## Owner-approved structured-output full-flow repair — sibling 23

Installed `@earendil-works/pi-coding-agent@0.86.1` / `@earendil-works/pi-ai@0.86.1` source was inspected before dispatch. `OpenAICodexResponsesOptions` and `buildRequestBody` expose no text `response_format` or response JSON-schema option on the guarded ChatGPT Codex backend path. The same installed path supports constrained function-tool arguments: the pi-ai README documents `constrainedSampling:{type:"json_schema",strict:"require"}`, `resolveJsonSchemaStrictSampling`/`makeStrictJsonSchema` implement it, and `convertResponsesTools` serializes `strict:true`. A no-network transport-injected preflight preserved the actual serialized `tool_choice:"required"`, one `submit_stage_result` function tool, exact JSON Schema, and `strict:true`. No optional live capability probe was needed.

The short non-overwriting sibling `experiments/v2-agentic-wiki-fragment-01/tr-structured-output-fullflow-23/` uses one machine-readable public contract as the source for request JSON Schema, exact examples, strict tool schema, and host validation. Sibling-21 normalization remains explicitly enabled, but strict tool outputs were all direct. Before calls, the T2 fixture clarified the previously ambiguous create-versus-non-shared ordering: create is rejected first even for a non-shared endpoint, and a thirteenth disclosed assertion protects it. This is a disclosed contract-clarity change and retest confound, not an identical-contract comparison with sibling 22.

Nine focused tests passed after the failed serialization-probe diagnosis was corrected to normalize direct-API context and use a synthetic JWT solely with injected no-network transport. Coverage includes the actual renderer→validator→next-stage chain, forced missing/type/sibling-22-wrong-shape rejects, exact serializer fields, direct/wrapper normalization, and bwrap behavior. A same-route mode-0700 readiness probe made zero model calls and left the ledger unchanged.

The bounded actual run settled exactly four Luna-medium calls through the installed guarded `openai-codex-responses` SSE route with manual redirect denial and `maxRetries=0`: Reader 1696, Work 1697, Temporary Recorder 1698, and Digester 1699. Every request config preserved `tool_choice:required` and `strict:true`; the backend accepted all four and every actual tool-argument object passed the same public host contract directly (`direct=4`, `normalized=0`, `rejected=0`). Work returned a complete `clinic_rules.py`; the network-unshared synthetic-root bwrap oracle passed all 13 disclosed assertions. Recorder accurately labeled the result a disposable fixture observation. Digester returned `retain`, `proposed_rewrite:null`, preserved the existing assertions, and separated observed fixture success from authority. No canonical apply or automated semantic score occurred; Parent direct semantic review remains external.

Ledger spent moved `$32.26687890999992→$32.27009810999992`, held stayed `$2.0454342200000015`, latest moved `1695→1699`, and unknown-held `[1,895,989]` stayed unchanged. Added runtime cost was `$0.0032192`; provider-wall sum was `57,333.601786 ms`, first-call-to-last-response wall was `57,424.279387 ms`, controller overhead was `90.677601 ms`, and preparation-to-report was `586,212.558926 ms`, excluding Parent review. No retry, fallback, SDK install/upgrade, provider/config/auth mutation, DB/Medivance operation, commit, migration, retrieval expansion, or canonical apply occurred.

### Layer completeness

| Layer | Independent delta? | Decision |
|---|---|---|
| SDD | no | Strict-tool and stage contracts remain experiment-local; no product/framework public API contract changed. |
| BDD | no | The disposable fixture flow changes no product-visible behavior. |
| SSOT | no | Provider route, credentials, budgets, ledger ownership, and canonical-apply authority remained unchanged. |
| DDD | no | One authored T2 fixture establishes no production domain rule. |

### Evidence capsule and implementation map

- `tr-structured-output-fullflow-23/capability-evidence.json` and `serialization-evidence.json`: installed versions/symbols/docs and the four separated support-evidence levels.
- `contract.json` and `run.py`: one public machine schema, derived exact examples, host validator, guarded four-stage orchestration, immutable source inputs, timing, ledger, and non-apply handling.
- `provider_bridge.mjs` plus `fragment-role-capability-02/broker.mjs`: same guarded backend with a single required strict function tool and preserved transmitted tool schema.
- `test_fullflow.py`, `focused-check.log`, and `root_test_t2.py`: nine focused regressions and the read-only 13-assertion oracle.
- `actual-run-01/provider-runtime/broker/request-config-1696.json` through `request-config-1699.json`: exact transmitted strict-tool contracts.
- `actual-run-01/responses/`, `host-outcome.json`, `summary.json`, and `evidence-capsule.json`: actual four-stage packets, bwrap receipt, cost/timing/ledger, and direct-normalization counts.
- `actual-run-01/report-ko.html`: Korean-first report with runtime support, contract change, reached stages, actual Recorder/Digester, limitations, and raw evidence links.

## Bounded same/different whole-flow replication — sibling 24

Sibling `experiments/v2-agentic-wiki-fragment-01/tr-capability-repeat-24/` preserved sibling23 and ran exactly two previously exposed cases: unchanged T2 and contrasting T1. Six focused tests plus strict serializer inspection passed before dispatch; offline bwrap good/bad controls passed once per case. Actual guarded receipts 1700–1707 all settled. T2 passed 13 disclosed assertions and T1 passed nine disclosed scenarios under its pre-disclosed required-field, stable-order, nullness, and extra-key report-only contract. Both actual Recorder and Digester stages completed; both Digester proposals retained existing rules and applied nothing. No retry, repair, grader, search, canonical apply, production/DB operation, or workflow implementation occurred.

A report-only timing calculation failed after all eight calls because preparation-start omitted `monotonic_ns`. The original stderr remains. No provider call was repeated; `finalize_existing.py` reconstructed the report from settled ledger receipts and immutable actual outputs. Per-call/provider and case timing remain receipt-backed; preparation-to-report is UTC-wall only and labeled accordingly.

### Layer completeness

| Layer | Independent delta? | Decision |
|---|---|---|
| SDD | no | The strict tool and task contracts remain experiment-local. |
| BDD | no | No product-visible or operational approval/apply/rollback flow changed. |
| SSOT | no | Existing provider route, ledger, budget, ownership, and non-apply authority were reused. |
| DDD | no | Supplied disposable T1/T2 fixture rules establish no new production domain rule. |

### Evidence and implementation map

- `tr-capability-repeat-24/run.py`: two-case freeze, derived public schemas, exact handoff, bwrap host checks, failure-stop/no-retry, ledger/cost/timing controller.
- `provider_bridge.mjs`: eight-call cap on the same required strict-tool guarded backend and short private runtime.
- `test_fullflow.py`, `root_test_t2.py`, `root_test_t1.py`, `public_oracle.py`: six focused regressions plus disclosed 13-assertion and nine-scenario behavior oracles.
- `actual-run-01/{reuse-t2,contrast-t1}/`: raw requests, actual strict-tool outputs, normalization receipts, diffs, and host outcomes.
- `actual-run-01/{summary.json,ledger-cost-time-table.json,evidence-capsule.json,report-ko.html}`: exact readback, limits, cost/time, and Korean report.
