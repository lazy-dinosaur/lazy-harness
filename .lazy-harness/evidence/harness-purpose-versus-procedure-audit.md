# Harness purpose versus procedure — read-only causal audit

Status: analysis complete; no code, policy, baseline scores, or benchmark attempts changed. User requested checking whether procedure matters to the harness's actual purpose. No new model calls or paid experiments.

## Governing purpose

Current host records read: ADR 0001 (humans and AI compensate for each other's limitations); ADR 0005 (developer effort minimization, NOT framework minimalism; digest needs-review); framework-contract §§0/0.1; linked `plans/north-star-accuracy-and-no-regression.md` §§0/1/7. Core outcome: better actual development accuracy and fewer errors/regressions through relevant durable knowledge, traceability, tests and preserved decisions. These do not define success as maximizing tool-sequence conformance. Historical north-star implementation/gate details are not treated as the current runtime contract.

Current search-read-debt SDD digest expressly rejects turning Reader completion into exact-tool-sequence/admission/audit machinery, and retains bounded follow-up for incomplete/conflicting results. Its implementation map describes guarding mutation. Current enforcement SSOT permits a transitional generic evidence guard; this audit does not infer that all gating is unauthorized from older L3-only guidance-ladder text.

## Confirmed concrete failure

Across 33 frozen benchmark scenarios there were 56 failed tool calls. **45 were `subagent action=status` rejected by search-debt**: B 42, C 3. This is 80.4% of all tool errors, not 45 separate failed scenarios. B additionally had six pending-join shell blocks and one nonexistent source-path grep in the Parent lane; its total including child errors was 51. These are not evidence of 45 Luna reasoning failures.

Example: `/tmp/lh-reader-comparison-36-ST6iqJ/runs/slot-02/sessions/2026-09-08T03-01-03-632Z_01a07ef6-440f-7643-8363-003ac9e420bf.jsonl:12,14,16,18`: status/transcript inspection of the already launched Reader received “map-first traversal/read evidence must happen before action”. This information gathering is not a host mutation.

Causal source chain in frozen benchmark:
- `source/packages/lazy-harness-pi/extensions/lazy-harness/index.ts:604–628`: TS action classifier does not classify plain subagent status as an action; special-cases list/Reader launch/wait/join.
- Same file `:991–1029`: after local checks it invokes `on-tool-execute-before.sh` for the call anyway.
- `source/.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py:186–212`: Python independently treats every non-list/non-search-handoff subagent operation as an action. Status lacks those exceptions, so this later layer denies it.
- Main has the same broad Python fallback at `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py:172–190`; main TS classifier at `packages/lazy-harness-pi/extensions/lazy-harness/index.ts:417–432` also does not identify plain status as a mutation. The exact Reader/pending behavior is specific to the isolated implementation; do not imply it was merged to main.

This is a structural classification/coordination defect: a read-before-action gate blocks a read-only coordination path used to obtain the required evidence. It is not a literal universal deadlock because native notifications can still arrive. Repeated polling/continued work after a failed tool is also model noncompliance; the audit does not assign every failure exclusively to the harness.

## Experimental amplification (not production requirements)

`/tmp/lh-reader-comparison-36-ST6iqJ/runner.py:53,119` requires no retry/fallback and exposes no explicit wait tool in the six-tool selection. The sequential arm has no source work to overlap with child execution, so status/wait handling is especially consequential. Native notification yielding exists, but the experiment did not establish a reliable explicit waiting path for B before comparison. Therefore B/C is not a clean causal estimate of scheduling superiority.

`audit.py:65,84,91,96,137` combines all-tool-error-zero, exact overview/drill order, full task-envelope string equality, join ordering, and fixed read budgets into mechanical PASS. Some protect material correctness; others are experiment-control conditions. A semantically equivalent question, recoverable bad lookup, or an extra justified read can lower that column without making the final answer false. Frozen scores remain useful conformance observations but are not a direct measure of prevented domain mistakes/regressions.

All 33 tasks were read-only questions over four fixed cases, including synthetic-history recall. There were no actual feature edits, domain-invariant violations, affected-test omissions, or subsequent-session decision-retention trials. Thus this experiment cannot establish whether the harness's institutional memory achieves its overall north-star. It can establish the operational defects above.

## Interpretation and candidate direction (not implementation approval)

1. Preserve material invariants: correct root/task/revision, actual evidence content before relying on it, no fabricated evidence, authorized writes, relevant domain/behavior constraints, bounded spending, and appropriate regression validation/durable decision capture.
2. Treat scheduling, exact natural-language envelope spelling, and recoverable read-tool errors as separate coordination/efficiency observations unless concrete harm is shown. Fixed trial read quotas are not universal correctness definitions.
3. Candidate priority: clarify a root/run-bound read-only coordination capability consistently across TS/Python; provide an actual usable pending-result path; keep evidence liveness distinct from content adequacy. Do not wholesale allow subagent operations that mutate/spawn/steer other work.
4. Candidate priority: use bounded recovery already allowed by the normal contract instead of transplanting no-fallback canary constraints into everyday work. Preserve historical trial failures.
5. Candidate priority: evaluate real prevented mistakes, omitted constraints, regression outcomes, decision recall and user interventions alongside latency, Parent context and model-priced dollars. Luna's low cost means raw total tokens are not an independent cost penalty.

Repeated one-shot approval requests in the earlier workflow were also partly Parent-authored experiment scoping, not an unavoidable safety property. New scope, irreversible changes and budget increases still need user decisions; progress inside approved scope should not be needlessly handed back to the user.

Conclusion: the memory/accuracy purpose is not refuted, but goal-displacing procedural enforcement is a real problem in the current operational implementation and experiment design. Strengthen alignment with purpose rather than either deleting safety or adding more proof ceremony.

## Discovery capture

- DDD: no new confirmed domain concept.
- SDD/TDD: candidates — read-only subagent status classification parity, pending-result consumption without evidence-gate self-obstruction, purpose-level outcomes and bounded recovery tests.
- BDD: candidate — fewer unnecessary user interventions inside approved work.
- ADR/SSOT: no decision or policy promotion; existing purpose and mandatory boundaries remain.
- Planning: this evidence capsule captures findings and candidate priorities; no paid follow-up, main integration, graph migration, or source mutation authorized/performed.


## Proposed bounded repair — awaiting approval

Recommendation: repair the observed coordination boundary first, not remove the memory/grounding system or redesign the entire framework. Retain dedicated Reader ownership and isolate changes from main.

1. One consistent operation classification contract in TS/Python, tested with the same fixtures. Narrow initial allowance: read-only status inspection for the known Reader run bound to current root/session. Status is not complete evidence; do not admit a join based on status alone. Unknown/cross-root runs and launch/steer/mutation semantics must not become unrestricted by a blanket subagent exemption.
2. Verify the actual installed native completion/notification path and exposed tool set; make pending-to-content delivery a supported path rather than asking the model to improvise status/shell polling. Do not invent an unsupported wait tool or add a second proof protocol. Preserve observed packet content and root/revision/epoch/run binding.
3. Normal workflow retains already-specified bounded fallback/targeted supplementary reads within the approved scope and spend. An incomplete Reader may be recovered; wrong-root/unauthorized mutation and uncertain safety remain stops. Recovery budgets are separate from immutable no-fallback historical experiments and require explicit finite values before live execution.
4. Keep integrity/safety, answer quality, coordination efficiency, and experiment conformance as separate outcomes. Exact natural-language task spelling and universal zero-tool-errors are not product success criteria. Actual task identity, evidence applicability, authorizations and material correctness remain required.

Focused acceptance candidates: pending status works without granting evidence; TS/Python allow/deny parity; genuine content enables join; status-only/wrong-root/stale epoch/unauthorized writes remain denied; bounded recovery yields one substantive answer without user reapproval for an unchanged approved task. Runtime control-plane/recovery fixtures precede any small functional rerun; do not rerun the whole 36-slot matrix first.

No implementation, blanket gate removal, global routing/default switch, main integration, or new paid-run budget is approved by this proposal. Discovery capture: SDD/TDD/BDD candidates only in this existing capsule; no new canonical policy decision.
