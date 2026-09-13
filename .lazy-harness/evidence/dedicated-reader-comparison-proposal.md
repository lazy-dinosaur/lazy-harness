# Reader comparison — requirements and proposal

Status: budget-bounded comparison complete: 33/36 scenarios (11 per arm), last block unstarted at frozen launch threshold. Independent blinded scoring complete. No parallel-default promotion.

Confirmed request: compare stability, speed, cost, and context consumption after R6 functional success. Main integration remains separate. The unused R7/R8 functional-repair allowance is not repurposed as benchmark authorization.

Grounding: current retrieval-workflow-benchmark SDD describes deterministic helper byte/token proxies, not live model quality, billed usage, or end-to-end stability. Its historical plan is not a current live-comparison protocol. R6 is a successful single case, not a comparative baseline.

Proposed arms: A Sol Medium reads records and source directly; B Sol Medium + Luna Low Reader with sequential source inspection after Reader delivery; C same models with parallel Reader/source inspection. A/C assesses total practical change; B/C isolates scheduling with the same model topology. Do not infer model-only causality from A/C.

Proposed pilot: four task categories (short lookup, multiple records, source/record cross-check, long-context follow-up), three repetitions per arm = 36 scenario runs, with Reader calls and independent scoring counted separately. Same source snapshot, questions, per-case total evidence allowances, required answer quality, tool availability, and timeouts. Balanced execution order; fresh sessions except explicitly prescribed follow-up turns. Record provider cache hits rather than asserting cold caches. No benchmark source/prompt changes mid-matrix; concrete defects produce preserved terminal outcomes and a separately versioned proposal, not silent reruns.

Metrics: first-attempt semantic/protocol success and tool/launch/join failure counts; wall time to correct substantive delivery, median/range and paired differences; provider-reported input/output/cache usage and total Parent+Reader estimated cost, including failed attempts and cost per successful answer; Parent peak context separately from cumulative billed input, Reader context, packet size, tool output bytes and repeated reading; follow-up recall/accuracy. Missing provider telemetry is reported unavailable, never as zero. Small pilot does not establish high-percentile latency or production reliability.

Cost controls to confirm: provider-reported cost ceiling for starting further work (not a hard billing guarantee; an already running request may overshoot), including review calls. No fabricated dollar estimate from R6 alone.

Discovery capture: DDD/SDD/BDD/TDD/ADR/SSOT no independent semantic changes; Planning candidate captured here pending explicit selection. No new model executions or source mutations for this proposal.


## Approved preparation and launch boundary

- Artifact root: `/tmp/lh-reader-comparison-36-ST6iqJ`; explicit `approval.json` captures both selections.
- 36 slots: four fixed questions repeated three times under A/B/C; all six within-block arm order permutations used twice. Equal aggregate per-case body-read allowances.
- Same frozen 615-file snapshot and same harness extension across arms. A lacks subagent runtime/tools (documented fallback); B has an explicit sandbox-only sequential scheduling treatment; C uses parallel scheduling. No product/main source changes.
- Long-history arm is controlled synthetic-history recall (~25 KB), not naturally accumulated multi-turn reliability.
- Preparation worker `a4682ed3` failed before a persisted model session; preserved. Delegate `1ac2a695` prepared only. Parent corrected epoch, baseline extension parity, repetitions, history size and mechanical audit gaps before any launch. First review `a3228f1c` found four issues; all fixed with fixtures; follow-up `2325a68f` OK.
- 15 offline tests PASS. Actual zero-model SDK preflight PASS across all three tool sets. Source/input hashes verified. Benchmark input manifest SHA-256 `b018ade59f20642e23f2a5dabb247e6571fa8906c6fe8a3ec3d2b00a5bc19fa2`.
- Preparation and review reported cost $4.250116 entered in external ledger. Measurement launch stop is $17 including that ledger, reserving $3 of approved $20 for scoring. Missing telemetry, timeout with uncertain pending child, or source drift stops the matrix; no failed slot retry or midmatrix repair.
- Parent and child cumulative usage/cost, per-request input+cache context, tool/packet bytes, source/notification/join timing, actual budgets/paths/task payload, and failures are audited. Independent blinded semantic scoring remains pending.

Discovery capture: confirmed execution scope captured here; no independent DDD/SDD/BDD/TDD/ADR/SSOT policy change. Main integration and legacy 37-row graph migration remain separate and unperformed.


## Terminal comparison result

Full report `/tmp/lh-reader-comparison-36-ST6iqJ/report.md`; per-attempt data `comparison-results.json`; independent blinded scorer `c1cecab0`. Exact 33 candidate IDs and score cardinalities checked before reporting; raw answers untouched. All frozen source/input hashes recomputed and matched; copied run credentials removed. Manifest `ARTIFACT-SHA256SUMS`: `ffea33e52d5a4e5411b51fa724ae1901bb3f33aa11cd636748b43fc5c6d35df8`.

| Metric | A direct | B sequential | C parallel |
|---|---:|---:|---:|
| Semantic/source-content PASS | 11/11 | 7/11 | 9/11 |
| Strict protocol PASS | 7/11 | 0/11 | 6/11 |
| Joint PASS | 7/11 | 0/11 | 5/11 |
| Median wall seconds (all attempts) | 91.506 | 135.465 | 114.196 |
| Mean measurement cost USD | 0.409573 | 0.365294 | 0.384972 |
| Cost per semantic success incl. failures | 0.409573 | 0.574033 | 0.470521 |
| Median Parent peak context input tokens | 46,928 | 27,036 | 34,374 |
| Combined provider tokens (11 attempts) | 2,134,033 | 3,841,516 | 3,724,736 |

Parallel vs direct: Parent peak -26.8%, combined tokens +74.5%, median time +24.8%, mean attempt cost -6.0% but semantic-success cost +14.9%. Context-window pressure and cumulative spending are distinct. No performance superiority or stable/default adoption claim follows.

B failed tools in every attempt, dominated by waiting/polling actions rejected by existing search-debt guards. This is a defect/interaction of the tested sequential configuration, not proof that sequential scheduling itself is intrinsically unreliable. The intended B/C causal scheduling comparison is therefore confounded. A/C also differs in model topology and tool availability. Exact-envelope and read-budget failures are separated from answer-content failures.

Measurement cost $12.75822456; preparation/prelaunch reviews $4.250116; independent scoring $0.421917; total reported $17.43025756. Slots34–36 have no start receipts: the frozen $17 measurement launch stop preserved scoring reserve; no silent budget reallocation or reruns. Remaining tasks have not been called successful or failed. Four questions with 3/3/3/2 repetitions per arm and ~25KB synthetic-history recall do not prove production reliability, natural multi-turn behavior or tail latency.

Discovery capture: Planning result captured here. SDD/TDD candidate only: investigate sequential wait/status versus search-debt boundary before any new version; do not silently repair this matrix. DDD/BDD/ADR/SSOT no independent change; no routing/default policy promoted. Main, previous terminal experiments, and 37-row graph migration remain unchanged. Further repair/comparison requires a separate version and decision.


## User-confirmed interpretation clarification

User clarified that increased token volume is acceptable given Luna's very low cost. For this comparison, do not treat combined raw tokens as an independent adoption penalty or proxy for dollars. Keep correctness, actual provider-reported cost (split by model), latency, and Parent context pressure separate. This is an evaluation preference, not a global routing/configuration change.

Observed measurement split (11 attempts/arm): C Parent $4.130129, Luna Reader $0.10456076, Reader 2.469% of combined cost; B Parent $3.907848, Reader $0.1103828, Reader 2.747%. Thus the raw token increase is not the principal dollar concern. Correct-answer cost remains descriptive and includes failed Parent attempts.

“Protocol” in the report denotes experiment compliance (map/drill/read order; assigned lanes; configured budgets; exact task/identity envelope; actual content-before-join; zero tool errors; preservation), not an independent judgment that an otherwise correct answer is wrong or dangerous. Timing or exact-envelope deviations can fail that strict column while answer content passes. Practical adoption should distinguish material failures (missing/wrong answers, missing evidence, wrong identity/root, duplicate costly work) from benchmark-specific compliance deviations; the frozen original scores are not relabeled.

Discovery capture: confirmed interpretation preference captured in this evidence capsule; no independent DDD/SDD/BDD/TDD/ADR/SSOT rule or implementation change.
