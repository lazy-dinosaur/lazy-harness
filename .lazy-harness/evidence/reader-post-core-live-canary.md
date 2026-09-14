# Evidence: Post-core Reader live canary

## Scope and authority

User approved a small actual-model check after the reviewed shared RESULT parser and headless primary-answer repairs. Four slots: short-fact A/B, then change-impact B/A. A uses original synchronous native; B uses patched asynchronous native. Both use the same repaired host snapshot. Parent/scorer Astra medium, Reader Luna low. No main integration, installation, deployment, retries, historical rescoring or expanded benchmark.

Candidate: `/tmp/lh-reader-sync-async-2T2VQR/post-core-canary-01`.
Freeze: `f3cddba25c817087a67b1abd25e3a0591b536905525b95b12f7b05a1b0a25781`.
Preparation workflow: `98d8f6e1-f343-41fd-b22f-dfc7e51eec3b`; reviewer `5f97ffe6-1677-4d2b-9bb0-cdb6729454fd` READY. Parent read full review and independently verified freeze/approval/settlement/carry hashes and empty run directory before creating exact acceptance. Executor `c780b0b9-f42a-4a15-ad9b-e14abb18deda` completed.

## Results

Four attempts and four blind scores completed, two usable pairs, no fallback or integrity stop. Both actual synchronous joins succeeded; all four Readers delivered complete packets with matching terminal ledgers. All four primary answers remained intact across real post-response advisory stderr, with one nonempty Parent answer each and no later Parent request admission. These are observed live cases, not universal lifecycle guarantees; incomplete/conflict branches were not exercised.

| Question | A seconds | B seconds | Semantic A/B | Claims A/B |
|---|---:|---:|---|---|
| short-fact | 150.781405 | 89.372276 | pass/pass | 3/3, 3/3 |
| change-impact | 260.632323 | 116.335945 | fail/fail | 3/5, 3/5 |

Mean substantive latency A205.706864s/B102.854111s. B was faster in both observed pairs, but two pairs cannot establish statistical/general superiority. Failed semantic answers remain timed as substantive answers, not relabeled successes. Both change-impact answers omitted full regression protections and coordinated SSOT/SDD/TDD updates; primary-answer preservation alone does not certify coverage.

Parent peak-context mean A20711.5/B24200.5 tokens. Measurement cost A$0.84818388/B$1.33095036: faster B was more expensive and used more Parent context in this sample. One Parent broad-scope grep denial per arm persisted on change-impact; all four Readers had zero failed tools. Search-interface/lane usability was explicitly deferred, not fixed by this patch.

## Usage and preservation

New Parent$2.132586 + Reader$0.04654824 + scorer$0.17841 = $2.35754424. Prior measured/scoring carry-in$17.34436148 is counted once. Cumulative priced usage$19.70190572; remaining monitored$30 target headroom$10.29809428. This is operational priced usage, not invoice certification or a hard ceiling. Preparation/control overhead is separate.

Executor reconciled87 new requests and12 actor starts/ends; outstanding empty, stop null, no unknown liability, eight Parent/scorer credential-cleanup receipts true and no remaining auth.json under new runs. Frozen run/score/report invoked once each. Main, installed packages, source/acceptance and old matrix history were not changed during execution. Runtime output override replaced the shared handoff only after preserving the old monitored-04 handoff with hash `0e288a674677f3b9bc615677dc932d9ce243e9b1b09e6d3a3e8062abee1b10ed`.

## Artifacts

Under the candidate's `runs/evidence/`: `execution-report.stdout.json`, `execution-reconciliation.json`, `join-primary-preservation-audit.json`, `lifecycle-evidence.json`, command exit/log files and `prior-handoff-preservation.json`. Raw slots01–04 and sealed/unblinded scores retain all candidate text, original tool failures and judgments. Parent inspected representative actual native join/terminal-ledger audit evidence; complete cross-actor reconciliation is executor evidence.

## Interpretation and Discovery capture

The two demonstrated core defects did not recur in this live sample. Async is a promising speed choice, not yet evidence of universally better cost, quality or maintenance value. No further paid execution is authorized by completing this canary.

Discovery capture: one evidence capsule for the live work unit. DDD/SDD/BDD/TDD/ADR/SSOT: no independent semantic delta; the approved core contracts and regressions remain in `.lazy-harness/tests/reader-result-primary-answer.md`, `.lazy-harness/spec/platform/search-read-debt-contract.md` and `.lazy-harness/behavior/llm-owned-record-retrieval.md`. Planning candidate: investigate remaining change-impact coverage and deferred scoped search usability before claiming broad answer quality. Core repair evidence: `.lazy-harness/evidence/reader-result-primary-answer-repair.md`. Historical results remain unchanged.
