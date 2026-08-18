# Planning — Agent-Neutral Orchestration and Scoped Retrieval Pilot

Status: clean sequential Direct/Sol Scout/Spark Scout rerun completed; Direct and Sol Scout protocol-valid, Spark protocol-invalid; no model/runtime promotion approved
Date: 2026-07-24
Updated: 2026-07-27
Layer: Planning
Primary ADR: `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md`

## Rule digest

- Status: advisory
- Layer: Planning
- Scope: transient-plan
- Aliases:
  - orchestration pilot
  - critical-path benchmark
  - scoped retrieval scout
  - Luna Medium scout
  - A/B/C context-sharding experiment
- Applies when:
  - piloting bounded retrieval children or comparing single-agent, sequential, and parallel work decomposition
  - measuring whether context sharding reduces request-to-validation wall-clock without quality loss
- Must:
  - keep parent-global discovery and child-scoped reads during Phase 0
  - use bounded packets, explicit ownership, and one parent integrator/final validator
  - treat child output as evidence input, not canonical truth or parent read-debt proof
  - measure wall-clock first and context/token/rework as guardrails
  - distinguish role-bound read-only retrieval scouts from subagents separately authorized for writing, review, or implementation
- Must not:
  - add a queue, daemon, delegated permit, or permanent model default in Phase 0
  - claim prompt savings while the current runtime still injects the full grammar into child sessions
  - generalize the forensic packet/oracle replay latency to the intended initial record-only scout flow
- Record completion:
  - pilot launches, results, changed scope, or implementation approvals update this plan and ADR 0055 when the architecture changes
- Related records:
  - `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md`
  - `.lazy-harness/planning/workflow-churn-reduction-plan.md`
  - `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md`
  - `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - `.lazy-harness/evidence/2026-07-26-agent-neutral-orchestration-contract-canary.md`

## Objective

Test whether the same quality bar can be reached faster under a finite context window by applying:

```text
work elimination
→ bounded context sharding
→ dependency-aware parallelism
→ one integration and validation boundary
```

The primary metric is total request-to-validation wall-clock. The pilot does not optimize model response latency in isolation and does not treat more workers as success by itself.

## Confirmed pilot choices

- Orchestration semantics: Lazy-Harness core.
- First runtime adapter: Pi Subagents.
- Debt ownership: parent-global + child-scoped.
- Child prompt: thin derived Evidence Scout role, not an independent policy source.
- Parent proof: read the packet, then selectively reread decision-critical canonical evidence.
- Phase 0 bridge policy: no delegated evidence transfer; parent direct map/read debt remains mandatory.
- Packet-only dry design review: approved and completed as a records-only step on 2026-07-25.
- Two initial read-only governing-contract attempts failed safely; the separately approved exact-path post-reload canary passed on 2026-07-26.
- The user then approved one full Sequential B replay. All three fresh read-only branches completed with integration-eligible packets and matched the held-out diff/review/full-validation oracle; this closes the B fidelity gate only.
- After reviewing B, the user selected and separately approved one **A baseline measurement**. The first launch was invalidated by supervisor quiet auto-exit; the user then approved exactly one corrected launch-configuration retry. That retry completed and produced a fidelity-valid A replay.
- After completion, the user challenged the depth and latency. Review confirmed `110.300 s` worker runtime and `119.420 s` preflight-to-worker completion, followed by `560.981 s` of supervisor verification that checked all `11/11` claims and `18/18` evidence bindings. This exceeded ADR 0055's selective-read intent. The user selected **C. Planning** for this experiment-specific correction.
- On 2026-07-27 the user selected and approved one minimal **A → B** remeasurement: one run per treatment, the same strong model/corpus/oracle, no automatic retry, bounded selective supervisor reads, and separate worker/supervisor/record-closure timing. The first A launcher failed before Pi started because a bash-style assignment was passed to fish; the user separately approved exactly one launcher-only correction.
- The corrected A worker completed and the first selective verifier stopped because the session envelope recorded `7` `bash` calls, `1` `write`, and zero `read` tool calls while the result labeled `20` evidence entries as `successful direct read`. Targeted diagnostic proved that bash calls used `nl -ba`, `sed`, and `rg` to read the actual bounded bytes/ranges; the candidate guard accepts qualifying read-only shell evidence. The user confirmed the supervisor error and continuation without rerunning A. A then passed the held-out oracle, and one fresh Sequential B completed all three packets under the bounded selective protocol.
- User correction after result review: read-only is a **retrieval-role boundary**, not a restriction on every possible subagent. The initially invoked scouts whose purpose is only to load project records have no reason to modify or delete project files. Other subagents may write only in a separately approved writer/implementation role with explicit ownership.
- First replay corpus: the isolated read-debt guard candidate at `/home/lazydino/dev/lazy-harness.read-debt-guard`.
  - Expected branch: `fix/read-debt-subagent-false-evidence`.
  - Expected base/HEAD before the uncommitted candidate diff: `49691b9b76b3e2c45ea7eba9b56093155afc1614`.
  - Replay selection does not approve guard adoption, merge, commit, push, or deployment.
- Model attribution uses two stages:
  1. Stage 1 isolates orchestration: A/B/C use the same exact strong route, `openai-codex/gpt-5.6-sol`, for parent and retrieval workers.
  2. Stage 2 is optional and separately reviewed: keep the same strong parent and add `openai-codex/gpt-5.6-luna:medium` only as the retrieval-scout route.
- Every launch preflight records the exact resolved model identifier. If Luna is unavailable, the treatment returns blocked and stops for a user choice; no automatic fallback is allowed.
- Luna remains a pilot route, not a framework or host SSOT default.

### Approved three-way direct Parent vs Scout benchmark — stopped after Sol Scout output-path conflict

The user selected the recommended three-way isolation comparison after reviewing the existing forensic A/B, mini-Scout, and Luna evidence. This approval covers exactly one sequential run per arm against the same `record-decision-broker` objective:

1. **Direct Parent arm:** one fresh top-level Pi session, no subagents, exact `openai-codex/gpt-5.6-sol:low`.
2. **Same-model Scout arm:** one fresh Pi Subagents `scout`, exact `openai-codex/gpt-5.6-sol:low`.
3. **Fast-model Scout arm:** one fresh Pi Subagents `scout`, exact `openai-codex/gpt-5.3-codex-spark:low`.

The arms run sequentially to avoid resource contention. Each arm is project read-only, performs the current mandatory standalone complete overview, verifies root/branch/HEAD/tree identity, drills only the supplied concrete node, reads at most three selected canonical records plus two directly linked source/test bodies, and must not read this orchestration plan, prior benchmark packets/transcripts, or held-out Parent verification artifacts. The objective is the same as the Luna smoke: identify when response-completed work produces a Record Decision Packet, distinguish candidate capture from canonical promotion, and identify the implementation/test surfaces that protect that boundary.

All arms use one designated `/tmp` JSON artifact and a normal concise completion response rather than `structured_output`; this comparison measures retrieval/orchestration/model behavior and does not silently retry the prior Luna delivery failure. The shared output budget is at most eight claims, ten evidence bindings, eight combined unresolved/rejected/not-read entries, and 7,500 compact JSON characters. Overflow must return `needs-split`; invalid JSON, a false `complete`, missing evidence, route fallback, stale identity, project mutation, or unavailable exact model is retained as that arm's result with no retry or fallback.

The Parent performs one bounded post-run verification pass: mechanical validation of every artifact/hash/range/reference, direct semantic verification of all governing/conflicting/final-decision claims plus one deterministic low-risk claim per arm, and at most five unique canonical/source/test body reads across the union. Divergence beyond that budget makes the comparison inconclusive rather than expanding verification. Per-arm runtime, preflight-to-artifact wall-clock, turns, tools, input/output/cache/reasoning tokens, reported cost, duplicate overview/drill/read counts, artifact size, normal handoff outcome, and content fidelity are recorded. Shared Parent verification and record-closure time are measured separately and are not attributed to an individual arm.

The first Direct Parent launcher was invalidated before artifact creation: the interactive overlay returned/transferred while the eighth assistant turn was still streaming the designated `write` arguments. The preserved JSONL contains seven completed turns, thirteen completed `bash` calls, a `33.655 s` observed event span, and lower-bound completed usage of `41,255` input, `749` output, `140,288` cache-read tokens, and `$0.298889`; no project write tool began and the pre/post tree fingerprint remained `f370c95f2a74ee519f72f74f6f3e8bf2c710194b4b29e83388e6868f73ffac8b`. The arm produced no result artifact or structured exit reason, so it is not a benchmark sample. No automatic retry occurred. After this evidence was reported, the user explicitly approved exactly one launcher-only retry using headless dispatch with the same prompt, model, root, budget, and output path.

The approved launcher retry was also invalid before artifact creation. The headless dispatch notification reported `killed` after `16 s`; the session ended mid-third assistant turn after two completed turns and two `bash` calls, with a `12.914 s` observed event span and lower-bound completed usage of `19,055` input, `100` output, `9,728` cache-read tokens, and `$0.103139`. The launcher omitted `handsFree.autoExitOnQuiet=false`, leaving dispatch's documented quiet-exit default enabled; no structured process kill reason was emitted. No project write began, and the pre/post fingerprint remained `2f43b63fa36a4cbfd890fde1539105bb9c3f01e410a47a180e158cdddeedc3da`. The retry allowance was consumed and no Direct result exists.

After reviewing both invalid launchers, the user explicitly selected a clean three-way restart: discard both invalid Direct attempts from treatment metrics, establish a fresh post-record baseline, then run exactly one Direct Sol arm with dispatch quiet auto-exit explicitly disabled followed by one Sol Scout and one Spark Scout. The original objective, prompt semantics, read/output budgets, sequential order, no-fallback policy, selective Parent verification, and project read-only boundary remain unchanged. No retry is authorized for any clean-restart arm.

This one-sample comparison may separate same-model orchestration overhead from the fast-model effect, but it cannot set a default model, approve a thin prompt or delegated-evidence bridge, authorize live dogfood, or trigger runtime/schema/guard changes. No source, schema, runtime, test, graph, commit, push, sync, release, or additional model run is approved.

#### Clean-restart partial result — Direct valid, Sol Scout protocol-invalid, Spark not launched

- Fresh baseline captured at `2026-07-27T05:51:50Z`: root `/home/lazydino/dev/lazy-harness`, branch `main`, HEAD `49691b9b76b3e2c45ea7eba9b56093155afc1614`, status SHA-256 `60262864752109dd5e6700df6ba7ff713aad293beab59ecd19c2c8dcdd10c67f`, tree fingerprint `c038ffd46b0ec4fcfcde1c3bb45b65e56b25e98eca6506f1f0c2503682d4fd51`.
- **Direct Sol passed its arm contract.** Headless dispatch explicitly disabled quiet auto-exit. Runtime events recorded `gpt-5.6-sol`; the launcher requested `openai-codex/gpt-5.6-sol:low`, and no alternate route appeared. The first tool was the exact standalone complete overview. The compact designated artifact is `/tmp/lh-3way-record-benchmark/direct-sol-result.json`, `6,652` bytes, SHA-256 `a4b5c332bf627179f1a45296fa3baa97734b160f98b4ebcea29e3a8fc6160079`. Mechanical shape/budget/path/hash/range/reference checks passed, normal handoff was present, and pre/post root identity matched.
- Direct diagnostics: worker/launcher `131.159 s`, preflight-to-artifact `131.182 s`, `9` turns, `9` tools (`bash=7`, `write=2`), `85,080` input + `4,923` output = `90,003` tokens, `242,176` cache-read, `447` reasoning tokens, and `$0.694178` reported cost.
- **Sol Scout content passed but the arm protocol failed.** Run `327c26a6-a6e0-4325-80d1-0bf3f37ae700` resolved exactly `openai-codex/gpt-5.6-sol:low`, attempted no fallback, completed in `111.292 s`, used `8` turns / `8` tools, `53,823` input + `2,957` output = `56,780` tokens, `204,288` cache-read, and `$0.459969` reported cost. Preflight to recovered artifact was `159.091 s`; normal handoff was present.
- The builtin Scout runtime appended an authoritative output instruction that explicitly overrode the task's designated `/tmp/lh-3way-record-benchmark/scout-sol-result.json`. The expected file is absent. Instead the child used `write` on `.pi-subagents/artifacts/outputs/327c26a6-a6e0-4325-80d1-0bf3f37ae700/context.md` inside the project root (`7,301` bytes, SHA-256 `648f460781981fd80546124196031ac835c561b931c6eb7544af5737acf5907a`). The packet nevertheless declared `complete`. This violates both the designated-output and project-read-only gates, so the arm is protocol-invalid even though runtime execution exited `0`. The ignored `.pi-subagents` write is not covered by the unchanged git-status/tree fingerprint and was not deleted, staged, or rewritten by the Parent.
- The Parent used the entire five-body union budget once: broker SDD, record-write policy, broker TDD, generator source, and shadow helper. Both Direct `8/8` claims and the recovered Scout `8/8` claims were supported within their stated limitations. Both selected the same three canonical records and two implementation surfaces. The mechanical validator was corrected to require a non-empty `readMethod` string rather than an output-contract-absent tool-name enum; all path/hash/range/reference/budget checks remained unchanged. Final validator SHA-256 is `968125fa6820e167a9599c7073b691a89513d549668245a9b8d50817d5385c5b`.
- Diagnostic-only same-model ratios were Scout/Direct `0.849x` worker time, `0.631x` input+output tokens, `0.844x` cache-read tokens, and `0.663x` reported cost. They do not establish an orchestration improvement because the Scout arm violated its output/ownership contract and its preflight-to-artifact wall was longer than Direct.
- After the known output-path conflict was surfaced, the user selected **stop and record**. Spark was not launched, no retry/fallback was used, and no fast-model effect was measured. Overall verdict: **inconclusive-stopped-no-spark**. No model default, Scout topology, thin prompt, delegated-evidence bridge, runtime/schema/guard change, live dogfood, or treatment promotion follows.
- Transient closure: `/tmp/lh-3way-record-benchmark/partial-stop-closure.json`, `11,885` bytes, SHA-256 `3ed92a8c47dbfca6c219693eae40a0627c630f270fb915dc23253bf6d2741395`. This pointer summarizes privacy-reviewed metrics and artifact hashes; raw session/transcript bodies remain runtime evidence and are not copied here.

##### Discovery capture — partial three-way stop

- DDD: none — no domain/business term or invariant changed.
- SDD: candidate — a future separately approved runtime contract may need an explicit precedence rule between caller-designated artifacts and builtin role output persistence; no schema/runtime change is approved.
- BDD: none — no product-visible flow changed.
- TDD: candidate — a future separately approved fixture may prove that `output:false` or an equivalent launch contract prevents project-root output persistence while preserving a task-designated `/tmp` artifact. This run is evidence, not implementation approval.
- ADR: none — ADR 0055's Lazy-core/Pi-runtime responsibility split and selective Parent proof remain unchanged.
- SSOT: none — no permanent output path, model route, runtime owner, or launch default is approved.
- Planning: updated — this primary record owns the stopped benchmark result and user disposition.
- Candidate store: none — the bounded SDD/TDD follow-ups remain explicit here; no automatic promotion occurred.

### User-confirmed clean sequential rerun — preflight pending

- User correction: execute the three arms one at a time rather than concurrently. The stopped series was already sequential, so its Sol Scout failure was not resource contention between arms; it was the builtin Scout output instruction overriding the designated `/tmp` artifact with a project-local `.pi-subagents/**/context.md` write.
- Approval: establish one fresh baseline after this record update, then run exactly one new **Direct Sol → Sol Scout → Spark Scout** series. Each arm must complete and receive its immediate identity/artifact postflight before the next arm starts; no arms run concurrently.
- Exact routes remain `openai-codex/gpt-5.6-sol:low` for Direct and Sol Scout, then `openai-codex/gpt-5.3-codex-spark:low` for Spark Scout. Every arm has no fallback and no automatic retry.
- Both Scout launches use `output:false` to disable builtin project-local output persistence while the task still permits exactly one designated `/tmp` JSON result. This is a new clean launch envelope, not a retroactive repair of the prior Sol arm. Comparisons with the prior default-output Sol run remain configuration-confounded.
- The objective, concrete node, record/source/test read ceilings, claim/evidence/exclusion/serialized-byte budgets, normal concise handoff, Parent five-body union verification ceiling, and project read-only boundary remain unchanged.
- Invalid JSON, false `complete`, missing evidence, stale identity, fallback, unavailable exact model, project mutation, missing designated artifact, or output overflow is retained as that arm's one result. The sequence stops for Parent adjudication rather than retrying that arm.
- This approval does not authorize source/schema/runtime/test/graph changes, model defaults, thin-prompt or delegated-evidence bridge adoption, live dogfood, commit, push, sync, or release.

#### Discovery capture — clean sequential rerun approval

- DDD: none — no domain/business term or invariant changed.
- SDD: candidate — caller-designated artifact versus builtin role-output precedence remains a possible later runtime contract; no contract implementation is approved.
- BDD: none — no product-visible behavior changed.
- TDD: candidate — this clean series may provide evidence about `output:false` plus a task-designated `/tmp` artifact; it does not itself approve a regression fixture.
- ADR: none — ADR 0055 responsibility and trust boundaries remain unchanged.
- SSOT: none — no permanent output path, runtime owner, or model default is approved.
- Planning: updated — this primary record owns the user correction and the newly approved clean sequential rerun envelope.
- Candidate store: none — follow-up candidates remain bounded in this primary record.

### Clean sequential rerun result — Direct/Sol valid, Spark protocol-invalid

- Fresh baseline: `/tmp/lh-3way-sequential-rerun-20260727-v2/baseline.json`, captured `2026-07-27T06:42:55.338652+00:00`, SHA-256 `76ed7af000f0e17bb843509e5a269272281ebf48ce53a5830f6c5e8f4e696d68`. It bound root `/home/lazydino/dev/lazy-harness`, branch `main`, HEAD `49691b9b76b3e2c45ea7eba9b56093155afc1614`, status SHA-256 `60262864752109dd5e6700df6ba7ff713aad293beab59ecd19c2c8dcdd10c67f`, and tree fingerprint `f98d3b17d5472df0b1b495d4d0f4c1d65e8a1a9c2c5189914c97cc394ba3c0e0`. All three pre/post snapshots matched it.
- Execution was strictly **Direct Sol → Sol Scout → Spark Scout**, with one active arm at a time, exact requested routes, no fallback, and no automatic retry.
- **Direct Sol passed protocol and semantic fidelity.** Exact route `openai-codex/gpt-5.6-sol:low`; `146.393 s`, `10` turns, `11` tools, `62,589` input + `4,940` output = `67,529` tokens, `317,952` cache-read, `446` reasoning tokens, and `$0.620121`. The designated artifact is `6,843` bytes, SHA-256 `d57932b517f78a4896b65c0a28d7f7ea809d5fa18828f2438a715883ed5534c4`; mechanical validation passed and Parent evidence supported `8/8` claims.
- **Sol Scout passed protocol and semantic fidelity.** Exact route `openai-codex/gpt-5.6-sol:low`; `163.311 s`, `9` turns, `11` tools, `53,991` input + `4,976` output = `58,967` tokens, `248,832` cache-read, and `$0.543651`. The designated artifact is `6,375` bytes, SHA-256 `d1fdf70921203afa6fe0b6ca032e6aabd197b804903ed840a63377191cb753c6`; mechanical validation passed and Parent evidence supported `8/8` claims.
- **Spark Scout content passed selective semantic review but the arm protocol failed.** Exact route `openai-codex/gpt-5.3-codex-spark:low`; `85.421 s`, `13` turns, `21` tools, `165,709` input + `21,386` output = `187,095` tokens, `336,512` cache-read, and `$0.64828435`. Its artifact declared `complete` at `9,644` bytes, over the `7,500`-byte ceiling instead of returning `needs-split`. It also encoded canonical evidence as partial range entries, performed `11` project-body read invocations over `8` unique paths despite self-reporting `5`, read three unselected canonical records, omitted the required final `wc -c` check after its second write, and attempted one failed read of a misspelled non-designated `/tmp` path. No retry repaired these failures. The content's `8/8` claims were nevertheless supported within their limitations by the bounded Parent union read; content fidelity does not retroactively restore protocol fidelity.
- The Parent used exactly the five-body union ceiling: broker SDD, record-write policy, broker TDD, generator source, and shadow helper. Direct used `6` body-read invocations over `5` unique paths, Sol Scout used `5/5`, and Spark Scout used `11/8`; only Spark exceeded and falsely self-reported the ceiling.
- Same-model diagnostic: Sol Scout versus Direct was `1.116x` worker time, `0.873x` input+output tokens, `0.783x` cache-read, and `0.877x` reported cost. The valid Scout reduced context/cost but was `11.6%` slower, so this one sample does not show a same-model orchestration latency win.
- Fast-model diagnostic: Spark versus Sol Scout was `0.523x` worker time, but `3.173x` input+output tokens, `1.352x` cache-read, `1.192x` cost, `1.909x` tools, and protocol-invalid. Its faster response is not a quality-equivalent fast-model win and cannot promote Spark as a default.
- Both Scout launches used the combined `output:false` + `artifacts:false` envelope. Each produced its designated `/tmp` artifact and normal handoff, and no new project-local `.pi-subagents/**` file was observed in either launch window. The previous output-ownership conflict did not recur, but one sample cannot isolate `output:false` from `artifacts:false` or establish a permanent runtime default.
- Worker runtime summed to `395.125 s`. Fresh-baseline-to-Parent-verdict was `1,272.520 s`, leaving `877.395 s` as preflight, sequential handoff, postflight, and Parent verification time. Record closure begins after this verdict, is excluded from treatment performance, and is measured separately in `/tmp/lh-3way-sequential-rerun-20260727-v2/record-closure.json`.
- Verdict artifact: `/tmp/lh-3way-sequential-rerun-20260727-v2/series-verdict.json`, SHA-256 `cb7b1e9b92c2e4eebb056775536989bab38855a89d0c3c6740a1e518a9c45327`. The mechanical validator SHA-256 is `7886030a960e30afcbf6819339ec2146568e0fa86288ef0153207219a92dfb8a`. Raw sessions and runtime event logs remain transient/private runtime evidence and are not copied into this record.
- Overall verdict: **partial comparison only**. Direct versus Sol Scout is internally comparable and valid; the Spark branch is preserved as protocol-invalid. No model default, Scout topology, thin prompt, delegated-evidence bridge, live dogfood, runtime/schema/guard change, commit, push, sync, or release is promoted.
- Evidence-capsule decision: no second canonical evidence file is added. This existing primary Planning record carries the durable interpretation and bounded hashes; repeated command/session detail remains transient under the run directory.

#### Discovery capture — clean sequential rerun result

- DDD: none — no domain/business term or invariant changed.
- SDD: candidate — a later separately approved packet/runtime contract may enforce serialized-byte status, aggregated whole-file canonical evidence, and supervisor-observed body-read counts; no schema/runtime change is approved.
- BDD: none — no product-visible flow changed.
- TDD: candidate — later separately approved fixtures may cover the combined `output:false` + `artifacts:false` designated-artifact envelope and overflow/read-budget misreporting; this benchmark does not itself approve test changes.
- ADR: none — ADR 0055's Lazy-core/Pi-runtime boundary and selective Parent proof remain unchanged.
- SSOT: none — no model route, output path, launch flag, or runtime owner becomes a permanent default.
- Planning: updated — this primary record owns the completed fresh-series result and conservative interpretation.
- Candidate store: none — bounded SDD/TDD follow-ups remain explicit here; no automatic promotion occurred.

### Deferred follow-up — unnecessary delegation cost

The user clarified that the separate concern is not primarily which subagent name or destination is chosen. The observed problem is that the parent sometimes launches subagents when the work likely does not need delegation, causing avoidable child prompt/context/token cost.

- Keep this concern separate from the current read-debt guard canary and from future agent/model/root allowlisting.
- Do not add a routing hard gate, settings restriction, or source change in the current canary work unit.
- A later explicitly approved slice should compare `no delegation` against delegated execution and define measurable admission evidence before launch, including expected wall-clock/context benefit, decomposition need, review independence, and estimated child cost.
- Until that slice is approved, this is a planning backlog item rather than an active runtime rule. The exact-route read-only canary completed without adding routing or admission enforcement.

## Phase 0 working contract

### Parent obligations

For each fresh root-bound evidence epoch, the parent:

1. runs complete lean discovery,
2. reads governing canonical records,
3. selects concrete map nodes,
4. creates bounded work packets,
5. integrates child packets,
6. directly verifies conflict/high-risk/decision-critical evidence,
7. owns the final plan, mutation, and validation claim.

### WorkPacket dry-design baseline

The planning-level packet version is `0.1-dry`. It is a review contract, not an implemented JSON Schema or runtime permit.

```text
packetVersion
packetKind = work
packetId
workUnitId
rootRealpath
revision
treeFingerprint
parentEvidenceEpoch
objective
dependencies[] = prior packet ids
concreteMapNodes[]
governingRecordsReadByParent[]
allowedReadScope[]
forbiddenWriteScope[]
constraints[]
acceptanceCriteria[]
outputBudget { maxClaims, maxEvidence, maxUnresolved, maxArtifactPointers, maxOutputChars }
artifactPath
modelRoute { requested, resolved, fallbackPolicy }
```

Phase 0 Evidence Scouts always receive `forbiddenWriteScope = ["*"]`. A packet path or task sentence is an instruction, not evidence. Missing root identity, stale revision/tree/epoch, or an invalid concrete node must stop with an explicit non-success status rather than trigger free-form project expansion.

The first replay default budget is bounded to 12 claims, 20 evidence entries, 8 unresolved items, 4 artifact pointers, and 12,000 output characters. A child that cannot preserve the required evidence inside that budget returns `needs-split`; it must not silently truncate.

### EvidencePacket dry-design baseline

```text
packetVersion
packetKind = evidence
packetId
sourceWorkPacketId
workUnitId
status
boundedClaims[] { claimId, statement, evidenceRefs[], limitations[] }
evidence[] {
  evidenceId, path, contentHash,
  range { startLine, endLine } or symbol,
  readProvenance { toolName, resultStatus, observedAt }
}
validation[] { kind, command, outcome, exitCode, artifactPointer }
unresolved[] { kind, summary, blocking, recommendedNext }
artifactPointers[] { path, contentHash, mediaType }
provenance {
  rootRealpath, revision, treeFingerprint, evidenceEpoch,
  agentName, modelResolved
}
```

Allowed outcome statuses:

- `complete`
- `needs-more-context`
- `needs-split`
- `blocked-by-dependency`
- `ambiguous`
- `stale-root-or-epoch`
- `invalid-packet`
- `failed`

`artifact-pointer` is a delivery mechanism, not an outcome status, so it lives only in `artifactPointers[]`. `complete` may contain explicitly non-blocking unresolved notes, but it may not conceal a blocking gap.

Evidence entries count only successful direct child reads of root-contained canonical record/source/test bytes. Task text, map cues, unrelated tool arguments, failed reads, and child assertions without a referenced evidence entry are not packet evidence. Line ranges are 1-based and inclusive; `contentHash` binds the bytes used for the claim.

Raw child transcripts are not integration artifacts. The EvidencePacket is evidence input, not canonical truth and not automatic parent `requiredRead` proof.

### Phase 0 parent trust and fidelity sampling

The parent directly rereads every governing, conflicting, high-risk, and final-decision-determining claim. For the remaining low-risk claims, it checks a deterministic sample of at least one and at most three claims per child packet and records sampled precision. A failed sample invalidates the packet for integration and triggers sibling-claim review or a bounded rerun; it never silently lowers the bar.

### Thin Evidence Scout role

The runtime task/profile should state:

```text
You are a read-only Evidence Scout, not a decision maker.
Verify root/revision/epoch, stay inside the supplied concrete-node scope,
read canonical record/source/test bodies, and return bounded claims with
path/hash/range provenance. Do not mutate, promote records, choose for the
user, infer missing facts, call subagents, or return a raw transcript.
Return an explicit overflow/ambiguity status when the packet is insufficient.
```

This role text is derived guidance. The canonical semantics remain in ADR 0055 and the governing Lazy-Harness records.

## Experiment design

Use the same objective, starting tree, acceptance criteria, model-quality bar, and final validator across three treatments:

### A — Single agent

- Parent performs discovery, investigation, decision, implementation, and validation.
- Establishes wall-clock, peak context, compaction, duplicate-read, and rework baseline.

### B — Sequential bounded workers

- Parent owns global discovery and creates dependency-ordered packets.
- Fresh retrieval workers run one after another.
- Tests context sharding without parallelism.

### C — Dependency-aware parallel DAG

- Only independent branches with distinct artifact/file ownership run concurrently.
- Dependency edges remain sequential.
- Parent performs one integration and one final validation boundary.

## Evaluation corpus

1. **First historical replay — selected:** the completed read-debt guard work unit in the isolated worktree.
   - Launch preflight must verify root realpath, branch, base HEAD, current tree fingerprint, and unchanged intended candidate surface.
   - The known final diff hash, reviewer verdict, and full-validation result are held-out oracle evidence; they are not placed in scout prompts.
   - The replay objective is to reconstruct the false-`requiredRead` failure, intended contract, protected direct/nested-read behavior, rejected task-text/map/failed-read evidence, and remaining delegated-bridge boundary.
   - Read-only branches are: governing contract/ADR, helper/source behavior, and TDD/validation evidence.
   - Treatment A performs those reads in one parent context; B delegates the same branches sequentially; C delegates only the independent branches concurrently. All three use one parent integrator and the same final oracle.
   - Replay does not adopt or mutate the guard candidate.
2. **Later live dogfood:** apply the same packet discipline to a real bounded framework task only after the replay shows no quality regression.
3. WP1A, guard adoption, host sync, graph migration, and Record Writer rollout remain separate unless independently approved after replay review.

## Contract-branch canary result — 2026-07-26

### Approved and observed scope

- Approval covered one read-only governing-contract branch only; helper/source/self-test reads, held-out oracle evidence, source/schema/runtime mutation, the remaining sequential replay, A/B/C, and Luna remained out of scope.
- Work packet: `wp-read-debt-contract-01`; work unit: `lh-read-debt-guard-replay-20260725`; evidence epoch: `lh-read-debt-canary-20260725-contract-01`.
- Pi Subagents run: `f5504529-9c28-4f3c-94eb-4a9b2e3ed3aa`, fresh `scout`, requested route `openai-codex/gpt-5.6-sol`, no fallback.
- Target identity remained `/home/lazydino/dev/lazy-harness.read-debt-guard` at `49691b9b76b3e2c45ea7eba9b56093155afc1614`; the three-file intended diff stayed `25ff7aacbf2848026d26806d08ad76b01b8fa8d5547df60f72ce246064abac1b` after the run.
- The child made no project/source/canonical/runtime mutation. Its only write was the designated `/tmp` packet artifact.

### Runtime and artifact evidence

- Supervisor result: `failed`; acceptance: `rejected`; duration: `121106 ms`; turns: `7`; tools: `12`; tokens: `61689` input + `4865` output = `66554`; reported cost: `$0.550907`.
- Runtime-resolved route was `openai-codex/gpt-5.6-sol:low` with `thinking=low`; no fallback route was attempted.
- The first parallel `sha256sum` call ran before map-first debt was satisfied and was correctly blocked. The child then completed overview, three concrete drill-downs, three full direct reads, and a later successful identity/hash command.
- Structured output capture succeeded, and `/tmp/lh-read-debt-canary-contract-evidence.json` exists at `6811` bytes with SHA-256 `bedee8a0769805f059c206dd46a5b11cc0fdc34a84094c4b92baf5b5f2f1262f`. The official scout output nevertheless says the run failed before producing output, so artifact existence is not runtime acceptance.

### Parent packet checks

- Parent checks against the planning-level `0.1-dry` shape passed for field presence, budgets (`6` claims, `3` evidence entries, `2` unresolved entries), claim-reference existence, root/revision/fingerprint, and all three expected path/hash/1-based-range bindings.
- The parent directly reread all three record bodies and reviewed all six claims because they govern the branch. Five contract claims were supported; the identity claim failed fidelity review because its `evidenceRefs` pointed only to record bodies that do not prove root/revision/fingerprint/model.
- The same identity claim reported `modelResolved=openai-codex/gpt-5.6-sol`, while supervisor metadata resolved `openai-codex/gpt-5.6-sol:low`. Exact route provenance therefore cannot rely on child self-report alone.
- Under the existing parent-sampling rule, one failed governing claim invalidates the packet for integration. The child packet's `status=complete` is not the overall canary outcome.

### Failure seams

1. The task required both “return only structured output” and a generic checked-acceptance fenced prose report. The child produced schema-valid structured output but no acceptance report, so checked acceptance rejected it.
2. One early guard-denied hash command was recovered, yet the supervisor ended the step with exit `1`; its final error excerpt named output from a successful map drill-down rather than the failed pre-overview hash call. Failure attribution is therefore not reliable enough for a canonical runtime envelope.
3. Child-authored provenance omitted the runtime thinking suffix, proving that requested route, child-reported route, and supervisor-resolved route need separate treatment.
4. The dry-design phrase `forbiddenWriteScope=["*"]` and the required artifact destination need an explicit artifact-write exception before implementation; this canary used a narrower project/runtime write prohibition plus the designated `/tmp` output.

### Canary verdict and unapproved correction candidates

- Verdict: **failed with a structurally usable but untrusted packet**. Packet transport, bounded content, scoped direct reads, and hash/range binding were demonstrated; runtime acceptance, exact model provenance, execution-status authority, and all-claim fidelity were not.
- No automatic rerun is allowed. Candidate corrections for a separately approved rerun are: serialize map-first traversal before identity/hash actions; use structured-output-compatible scout acceptance; add a supervisor-owned execution envelope for state/acceptance/model/thinking; keep identity validation separate from semantic record claims; and specify the artifact-write exception.
- Evidence capsule: none for this intermediate failed canary. The packet, supervisor status, transcript, and metadata remain runtime artifacts; this plan stores the durable interpretation without copying raw transcripts.

## Corrected-envelope rerun result — 2026-07-26

- The user selected one same-scope rerun and kept the unrelated 37-row legacy graph migration deferred.
- Run `d22541b8` used a fresh `scout`, requested `openai-codex/gpt-5.6-sol`, resolved `openai-codex/gpt-5.6-sol:low`, used no fallback, and had generic acceptance explicitly disabled as intended.
- Supervisor result was still `failed` after `75995 ms`, `5` turns, `9` tools, `48939` input + `2602` output = `51541` tokens, and `$0.376515` reported cost.
- Execution order was corrected: overview ran alone first, followed by three drill-downs, three direct reads, one identity/hash command, and structured output. Every recorded tool result succeeded; the child called no `write` tool and changed no tracked target file.
- Runtime-owned structured output exists at `.pi-subagents/chain-runs/d22541b8/structured-output/pi-subagent-structured-Orqmt8/output.json`, `7836` bytes, SHA-256 `9353db803456a8b5ff518589fbc37a85dad276fd2c733d91ac72bb0e136ce2e0`. The official output file is empty.

### Rerun packet diagnosis

- The packet returned `status=stale-root-or-epoch`, `8` claims, `3` evidence entries, and `3` unresolved entries with a blocking `fingerprint-mismatch`. It did not claim supervisor success and used the requested `supervisor-attestation-required` model sentinel.
- The WorkPacket gave the expected fingerprint but described only “the three intended candidate files”; it did not enumerate their paths. The scout inferred the three readable canonical records and measured `780f183b7e5ed588966739dc32c3bd13e1a770682ef2b7602883a8a97695d36b`.
- Parent verification shows that hash is exactly the diff hash of the three record paths, while the intended candidate source/TDD paths — `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py`, `.lazy-harness/scripts/self-test.py`, and `.lazy-harness/tests/pre-action-search-evidence-guard.md` — still produce the expected `25ff7aacbf2848026d26806d08ad76b01b8fa8d5547df60f72ce246064abac1b`. Root, HEAD, record hashes/ranges, staged count, and tracked candidate state remained unchanged.
- The safe stop was correct, but `invalid-packet` or `needs-more-context` is more accurate than `stale-root-or-epoch`: the input omitted an exact fingerprint path set, so staleness was not established.
- Parent reread all three records and checked all eight claims. Seven were supported; `claim-outside-scope` cited canonical records for a task-specific scope assertion and therefore failed the packet's own evidence-reference rule. All three `observedAt` values were phase labels rather than actual observation timestamps, which is syntactically accepted by `0.1-dry` but insufficient for a future verified supervisor bridge.
- Despite every tool result carrying `isError=false`, the supervisor reported `bash failed (exit 1)` and excerpted a successful map drill-down. The subsequent runtime-source inspection identified this as a text-heuristic false positive, not a packet-status interpretation.

### Rerun verdict and next gate

- Verdict: **failed safely on an underspecified WorkPacket, with runtime failure attribution still untrustworthy**. The rerun fixed map ordering, generic acceptance conflict, child writes, and false model self-attestation; it did not establish a successful runtime envelope or an integration-eligible packet.
- A third retry is not automatic. A corrected packet would need explicit `fingerprintPaths[]`, missing-path classification as `invalid-packet`, actual observation timestamps or supervisor event references, task-scope statements outside semantic claims, and a runtime rule that distinguishes packet non-success from tool/process failure.

## Read-only Pi Subagents runtime inspection — 2026-07-26

The user selected runtime inspection before any third canary. No installed package, project source, schema, or runtime configuration was modified.

### Confirmed failure path

- Installed runtime: `pi-subagents@0.36.0`. Its structured-output tool writes validated JSON and returns `terminate: true` in `src/runs/shared/subagent-prompt-runtime.ts:382-414`, so a structured-only child normally has no later prose assistant message.
- `src/shared/utils.ts:418-488` implements `detectSubagentError`. When there is no later assistant text, it scans earlier Bash tool-result text even when the message explicitly has `isError=false`; its fatal patterns include broad `/timeout/i`.
- The successful ADR map output contained the identifier `LAZY_HARNESS_CATALOG_TIMEOUT_SECONDS`. That substring matched `/timeout/i`, so the detector fabricated `bash failed (exit 1)` and used the first 200 characters of the otherwise successful map output as error details.
- `src/runs/foreground/execution.ts:1043-1081` runs this textual detector before reading the captured structured-output file. The fabricated error changes exit code `0` to `1`, which prevents the valid structured JSON from being attached to the result.
- `src/runs/foreground/chain-execution.ts:1344-1353` then fails the chain solely because the corrupted child exit code is non-zero. The EvidencePacket's internal `status` was never interpreted by this path.
- `agentContract.version=1` separates execution/acceptance projections, but `src/runs/shared/agent-contract.ts:7-25` derives execution success from the already-corrupted exit code. It cannot repair this false positive after the fact.

### Bounded runtime correction proposal — not approved

1. In `detectSubagentError`, treat an explicit boolean `toolResult.isError` as authoritative: `false` skips Bash text heuristics; text parsing remains only as compatibility fallback when the flag is absent.
2. Treat a successful terminal `structured_output` result as a completion boundary so intentionally recovered earlier tool failures do not re-fail a schema-valid structured step.
3. Add regressions for successful Bash output containing `TIMEOUT` identifiers, `exit code 1` prose, and other fatal-pattern text; failed results with `isError=true`; legacy messages without the flag; recovered failure followed by valid structured output; and foreground/async chain parity.
4. Keep this fix in Pi Subagents, which owns execution/result delivery. Lazy-Harness should not add a second runtime-error parser. A plain-file canary is only a temporary diagnostic workaround and is not equivalent to schema-validated structured delivery.

### Upstream status — fix already released

- At inspection time, installed `pi-subagents` was `0.36.0`; `pi list` showed the unpinned user package `npm:pi-subagents`. npm and GitHub both reported `0.37.0` as latest.
- Upstream issue [#645](https://github.com/nicobailon/pi-subagents/issues/645) documents the same false-positive class: successful Bash output containing `setTimeout`/`TIMEOUT` was scanned as failure when no prose assistant response followed.
- Commit [`b8bebabe200db6b35fa666e8617a33b6ca3e0706`](https://github.com/nicobailon/pi-subagents/commit/b8bebabe200db6b35fa666e8617a33b6ca3e0706) removed successful-stdout scanning, preserved explicit `isError=true` failures, and added foreground/async regressions. It is included in release [v0.37.0](https://github.com/nicobailon/pi-subagents/releases/tag/v0.37.0).
- The v0.37.0 detector now ignores every tool result unless `isError=true` ([source](https://github.com/nicobailon/pi-subagents/blob/53945b578d8d4f2365dcb2f11c817f874fc91977/src/shared/utils.ts#L423-L463)); its regression explicitly protects successful Bash output containing `setTimeout` ([test](https://github.com/nicobailon/pi-subagents/blob/53945b578d8d4f2365dcb2f11c817f874fc91977/test/integration/detect-error.test.ts#L56-L90)).
- A read-only probe against the v0.37.0 tag returned `{hasError:false}` for `LAZY_HARNESS_CATALOG_TIMEOUT_SECONDS` with `isError=false`, while an explicit `isError=true` result containing `exit code 9` remained a failure with exit code `9`.
- Residual boundary: v0.37.0 still treats a tool-call-only assistant turn as insufficient recovery evidence for an earlier explicit failed tool result ([test](https://github.com/nicobailon/pi-subagents/blob/53945b578d8d4f2365dcb2f11c817f874fc91977/test/integration/detect-error.test.ts#L174-L203)). The released fix removes the exact all-success canary false positive, not every recovered-error/structured-only case.
- Pi package guidance gives `pi update --extension npm:pi-subagents` as the one-package update command. The user later approved that unpinned update and one post-restart exact-path canary.

### Approved package update — runtime reloaded

- Command: `pi update --extension npm:pi-subagents`. Result: one package changed; version moved from `0.36.0` to `0.37.0`.
- Installed `src/shared/utils.ts` SHA-256 is `2a163cda0ffaab373f008dc67d5002997b93b1b885f48266a6f44d5af26eecbc`, byte-identical to the v0.37.0 tag checkout.
- The update command reported 6 transitive npm audit findings (4 moderate, 2 high). No `npm audit fix`, force update, or unrelated dependency mutation was authorized or run.
- Process ancestry inspection showed that the active `pi` process predated the package update. The user then ran Pi's built-in `/reload`, which reloads extensions/resources without replacing the session.
- The separately approved post-reload governing-contract canary ran once with explicit fingerprint paths, actual timestamps, no unsupported task-scope claim, the same strong model route, and no source mutation or broader replay.

## Exact-path post-reload canary result — 2026-07-26

- Run `213ce8b7` used a fresh `scout`, requested `openai-codex/gpt-5.6-sol`, resolved `openai-codex/gpt-5.6-sol:low`, attempted no fallback, and used `agentContract.version=1`.
- Supervisor execution was `completed`, success `true`, exit `0`; acceptance was `not-required`. Runtime was `61,147 ms`, `5` turns, and `9` tools; reported usage was `65,059` input + `1,977` output tokens with `$0.429917` cost.
- Execution order matched the packet: one standalone complete overview, three concrete drill-downs, three direct full-record reads, one exact identity/fingerprint/timestamp verification, and one runtime-owned structured output. All nine tool results had `isError=false`.
- Structured packet status was `complete`: `7` claims, `3` evidence entries, `6` validation entries, `0` unresolved entries, and `0` artifact pointers. Packet size was `5,580` bytes; SHA-256 was `3ca6095a12f1c2b156a4c621e319de7f2876e48c2778818804e0d414518b45ee`.
- Parent checks passed for schema/budgets, every claim reference, all three exact path/hash/1-based-range bindings, successful direct-read provenance, ISO timestamp `2026-07-26T12:37:19Z`, root/revision/ordered three-path fingerprint, no fallback, and supervisor-owned model attestation. Parent direct review found all `7/7` governing claims supported.
- No identity/model/runtime/task-scope statement was encoded as a semantic claim. Root, revision, model sentinel, and fingerprint remained provenance/validation fields.
- The normal Markdown output artifact was empty because the child terminated through schema-valid `structured_output`. Under v0.37.0 this did not recreate the earlier false `bash failed (exit 1)` result.
- Target tracked state and staged count were unchanged; the preserved candidate diff remained `25ff7aacbf2848026d26806d08ad76b01b8fa8d5547df60f72ce246064abac1b`, with `0` staged paths.
- Verdict: **contract-canary pass; packet integration-eligible for this branch**. This proves the corrected execution envelope and packet fidelity for the bounded governing-contract branch only. It does not prove the remaining sequential replay, A/B/C benefit, prompt savings, delegated-evidence bridge, guard adoption, or unnecessary-delegation admission control.
- Durable validation detail: `.lazy-harness/evidence/2026-07-26-agent-neutral-orchestration-contract-canary.md`.

## Full Sequential B replay result — 2026-07-26

### Approved scope and packet sequence

- The user selected a fresh full Sequential B replay after the exact-path canary passed. Approval covered the governing-contract, helper/source, and TDD/validation branches in dependency order, all on the same strong route.
- Each branch used a fresh `scout`, `agentContract.version=1`, runtime-owned structured output, requested `openai-codex/gpt-5.6-sol`, and no fallback. A/C treatments, Luna, live dogfood, admission-control work, packet/runtime implementation, guard adoption, commit/push/sync/release, and unrelated mutation remained out of scope.
- Target identity stayed `/home/lazydino/dev/lazy-harness.read-debt-guard`, branch `fix/read-debt-subagent-false-evidence`, HEAD `49691b9b76b3e2c45ea7eba9b56093155afc1614`, with ordered three-path diff fingerprint `25ff7aacbf2848026d26806d08ad76b01b8fa8d5547df60f72ce246064abac1b` and staged count `0`.
- The known diff hash, reviewer verdict, and full-standard result remained held out from all three scouts and were opened only after packet/schema/provenance/fidelity checks passed.

### Supervisor and packet results

| Branch | Run / packet | Runtime | Turns / tools | Tokens | Cost | Parent-supported claims | Evidence bindings |
|---|---|---:|---:|---:|---:|---:|---:|
| Governing contract | `ca0dac45-980c-4418-a706-c0b3f6847544` / `wp-read-debt-sequential-b-contract-01-evidence` | `75,420 ms` | `5 / 9` | `59,464` | `$0.400891` | `9/9` | `3/3` |
| Helper/source | `568c6a85-aa55-4611-adad-ff1b2f673ad4` / `wp-read-debt-sequential-b-helper-01-evidence` | `97,266 ms` | `8 / 16` | `66,318` | `$0.503163` | `10/10` | `5/5` |
| TDD/validation | `6890fe5f-1e5b-4a0f-a84a-548db393f662` / `wp-read-debt-sequential-b-tdd-01-evidence` | `89,768 ms` | `7 / 13` | `60,690` | `$0.484388` | `8/8` | `4/4` |

- All three supervisor executions were `completed`, success `true`, exit `0`, acceptance `not-required`, review `not-requested`, and resolved `openai-codex/gpt-5.6-sol:low` with one attempted model and no fallback. All `38/38` recorded tool results had `isError=false`.
- Packet semantic status was `complete` for all three. Aggregate packet counts were `27` claims, `12` evidence entries, `2` explicitly non-blocking unresolved notes, and `0` artifact pointers. Packet bytes totaled `20,356`.
- Packet SHA-256 values were `572d239adeae53098893aa3c04294bc67b0ec88f8526a49afb370a6e3c2abc3e`, `7829801f300739198c3d836c6d76e8d103168d52306e1eb6813e49dfe28db810`, and `0917491a9552f02e09872fe5f83a6c20af2f843d0fd27b917648d515f6068b30` in branch order.

### Parent fidelity and held-out oracle comparison

- The parent directly reread all governing and final-decision-determining evidence ranges and accepted `27/27` claims. All `12/12` packet path/hash/1-based-range/direct-read/timestamp bindings matched current target bytes; no claim used identity/model/runtime/task-scope facts as semantic evidence.
- The helper packet correctly reconstructed successful direct/nested read filtering, rejection of delegated task text/map/non-read/failed evidence, journal error preservation, Pi evidence-epoch filtering, and the absence of a verified delegated-evidence bridge within the inspected ranges. Its repository-wide absence statement remained explicitly limited to those ranges.
- The TDD packet reconstructed the deny/allow matrix and canonical fast/focused/standard/full-regression boundaries without claiming tests had run. Its two unresolved items correctly stated that execution and held-out evidence were outside child scope and were non-blocking for packet fidelity.
- Held-out oracle comparison matched the same candidate fingerprint. Independent review reported no correctness blocker; its original nested-false-evidence coverage note is covered in the preserved final self-test/TDD bytes. The exact-tree standard oracle was `ok=true`, `fullRegression=true`, `evidenceReused=false`, `91.73s`, with `85` framework checks run and `0` skipped.
- Quality verdict: **Sequential B replay-equivalent and packet-integration eligible** for this historical corpus. It reconstructed the failure, intended contract, implementation boundary, regression protection, validation contract, and remaining delegated-bridge boundary without source/runtime mutation.

### Performance and duplication interpretation

- Sequential child runtime summed to `262,454 ms`. First child start through final child completion was `521,108 ms`; the remaining `258,654 ms` was sequential parent inspection/handoff time between children. Parent preflight at `13:03:47Z` through final post-run identity check at `13:13:26Z` was `579 s`.
- Aggregate child use was `178,694` input + `7,778` output = `186,472` tokens, `523,264` cache-read tokens, `20` turns, `38` tools, and `$1.388442` reported cost.
- Current Phase 0/runtime behavior repeated three complete overviews, nine drill-downs, and fourteen direct reads. The helper scout first made two broad in-scope reads and then five exact packet-bound rereads; the TDD record was directly read in both the governing and TDD branches. Every child still received the full project grammar.
- Raw recorded boundaries were B `579 s` and A `680.401 s`, while B used `2.245x` A's worker tokens, `2.019x` reported cost, `4.75x` tool calls, three overviews instead of one, and fourteen primary direct reads instead of eight. The A total includes an over-deep `560.981 s` supervisor replay and is not a clean performance comparator, so the raw `101.401 s` difference must not be promoted as a B speedup.

### Verdict and next gate

- Sequential B and Treatment A both pass the historical quality/fidelity gate.
- The performance comparison is not decision-grade: A's worker was bounded, but its supervisor verification replayed every claim/evidence binding instead of staying selective. Worker/compute metrics remain diagnostic; the raw A/B total-wall difference does not establish an orchestration winner.
- No corrected retry remains. Treatment C, Luna, admission-control implementation, live dogfood, guard adoption, or packet/runtime implementation still require a new option and execution gate.
- Durable validation detail is consolidated in `.lazy-harness/evidence/2026-07-26-agent-neutral-orchestration-contract-canary.md`.

## Treatment A baseline — corrected retry complete

### Purpose and control boundary

Treatment A supplies the missing no-delegation control for the same historical read-debt-guard corpus. It tests whether one fresh single agent can reconstruct the same governing contract, helper/source behavior, TDD/validation boundary, and held-out oracle with less request-to-validation wall-clock and compute than Sequential B. It does not implement delegation admission control or assume A will be faster.

### Proposed execution topology

- Use one fresh top-level single-agent session; do not use Pi Subagents, child fan-out, chains, parallel workers, or Luna.
- Request the same strong route, `openai-codex/gpt-5.6-sol`, with no fallback. Stop if the exact route cannot be confirmed.
- Keep the experiment supervisor outside the worker context. The supervisor owns preflight, held-out-oracle custody, final fidelity review, and metric comparison, but does not perform the worker's retrieval or reconstruction.
- Bind the run to `/home/lazydino/dev/lazy-harness.read-debt-guard`, branch `fix/read-debt-subagent-false-evidence`, HEAD `49691b9b76b3e2c45ea7eba9b56093155afc1614`, and the ordered three-path fingerprint `25ff7aacbf2848026d26806d08ad76b01b8fa8d5547df60f72ce246064abac1b`.
- Keep the target project read-only with staged count `0`. Runtime-owned or `/tmp` result artifacts are allowed; project, canonical, package, and runtime configuration mutation is forbidden.

### Comparable scope and isolation

1. Start the measured boundary immediately before target identity preflight.
2. In one fresh agent context, perform one complete lean overview, targeted drill-down/loading, and an integrated reconstruction across the same governing-contract, helper/source, and TDD/validation surfaces used by B.
3. Do not expose prior B packets/transcripts, this plan's B result section, the durable B evidence capsule, the known final diff interpretation, reviewer verdict, or full-standard result to the worker.
4. Require concrete path/hash/1-based-range provenance for claims used in the integrated result. The worker may return one bounded integrated artifact rather than three EvidencePackets.
5. After the worker submits, let the supervisor verify governing/final-decision evidence, compare the unchanged target with the held-out diff/reviewer/full-standard oracle, and perform the final identity check.
6. End the measured boundary after the supervisor's final target-state check and oracle verdict.

### Metrics and acceptance

Record total wall-clock, worker runtime, supervisor preflight/review time, turns, tool calls, input/output/cache-read tokens, reported cost, complete-overview/drill-down/direct-read counts, context compaction if observable, rework, and target-state drift. Mark unavailable metrics as unavailable rather than estimating them.

A is a valid baseline only when:

- the same historical failure, intended contract, deny/allow matrix, implementation boundary, regression protection, validation contract, and missing delegated-evidence bridge are reconstructed;
- every claim used by the supervisor passes direct fidelity review and the held-out oracle comparison has no correctness blocker;
- root, HEAD, fingerprint, staged count, and tracked target state remain unchanged;
- the exact strong route runs without fallback;
- the full request-to-verdict boundary is measured comparably to B's `579 s`; and
- no source/runtime/canonical mutation or fresh test execution is represented as part of the read-only baseline.

Sequential B becomes a candidate improvement only if it preserves the same quality while improving the comparable primary wall-clock without unjustified context/token/compute growth. A result does not automatically authorize C, Luna, admission-control implementation, live dogfood, guard adoption, or runtime/schema work.

### Stop conditions and validation boundary

Stop without an automatic retry on root/HEAD/fingerprint drift, concurrent target mutation, exact-model unavailability or fallback, held-out-oracle leakage into the worker, out-of-scope reads that invalidate comparability, project/runtime mutation, or an unobservable primary timing boundary. Report the failed baseline instead of repairing the protocol during the run.

This is a read-only replay, so it does not run a fresh full regression. The historical full-standard artifact remains a held-out oracle, not A execution evidence. Any post-result planning/evidence-record mutation receives focused `lazy check`, diff hygiene, record lint, and map validation under the canonical test strategy; a full regression is not rerun merely for an evidence-capsule update.

### First execution attempt — invalid before baseline

- The user explicitly approved one run under the proposal above. Preflight started at `2026-07-26T23:32:24Z` and verified the required root, branch, HEAD, ordered fingerprint, staged count `0`, and exactly the three intended tracked modifications. The model catalog contained `openai-codex/gpt-5.6-sol`.
- A fresh top-level Pi print-mode session was launched through `interactive_shell` dispatch as `treatment-a-baseline`, with `openai-codex/gpt-5.6-sol:low`, thinking `low`, a `read,bash,write` allowlist, no Pi Subagents, and a 900-second hard timeout.
- Session artifact: `/tmp/lh-treatment-a-session/2026-07-26T23-32-49-598Z_019fa0c6-2b3e-7ccf-a4e3-34006ed1285b.jsonl`, `38,661` bytes, SHA-256 `b0c7a18943cdab4b1a11489e9bbc81f58d263dc2870f1d01530d6320b401fd91`. Prompt SHA-256: `4e214915ba99d29474f7253ecd3ec48710bc5179a6d85d93605608df69595248`; preflight SHA-256: `3ec50d28818280e28951dd3c1fd7417d2e8c82853e5a2838cbec2d41b678652e`.
- Runtime metadata confirms the exact requested model and thinking level. The first and only assistant turn correctly called standalone complete overview; its tool result succeeded with `isError=false`. The recorded event span was `2026-07-26T23:32:49.598Z` through `23:32:57.263Z`. Partial usage was `10,175` input + `37` output = `10,212` tokens and `$0.051985`.
- The supervisor then reported the session as `killed`. There was no second assistant turn, final assistant text, drill-down, direct read, identity command, or `/tmp/lh-treatment-a-baseline-result.json`. The exact kill timestamp/reason was not retained in the Pi session JSONL.
- The launch left dispatch's documented `autoExitOnQuiet` default enabled. The successful print-mode worker became terminally quiet while awaiting its next model turn, so the observed sequence is most directly explained by the dispatch quiet auto-exit rather than model unavailability, read-debt rejection, or project failure. This attribution is high-confidence but not a structured runtime kill-reason attestation.
- Post-kill target checks preserved the same root, branch, HEAD, fingerprint `25ff7aacbf2848026d26806d08ad76b01b8fa8d5547df60f72ce246064abac1b`, staged count `0`, and three tracked modifications. No held-out oracle was opened and no test or validation command ran.
- Verdict: **invalid A attempt; no fidelity or performance baseline**. The measured boundary cannot be compared with B because the worker did not pass discovery into scoped loading or produce an integrated result.
- A bounded correction candidate was to preserve the same prompt/model/root/tool/timeout constraints while explicitly setting `handsFree.autoExitOnQuiet=false` and using a new isolated session/result path. That launch-only correction was later approved once and produced the valid baseline below.

### Corrected retry — valid baseline

- The user explicitly approved one corrected retry. It kept the same root, objective, bounded reads, exact strong route, thinking level, no-fallback policy, no-subagent rule, tool allowlist, and `900000 ms` hard timeout. The only behavioral launch correction was `handsFree.autoExitOnQuiet=false`; it used fresh session/result paths.
- Retry preflight began at `2026-07-26T23:40:19Z` and again matched root, branch, HEAD, ordered three-path fingerprint, staged count `0`, and exactly the three intended tracked modifications. Prompt SHA-256 was `c35969b6b668d8c9f51eac8c9f80653730fa4b70b97ae07ad132283a86df1980`; preflight SHA-256 was `b36411a0c24669eb223e9c0d5905c4934c860c54fc3a28a9cf2f29b528c144d6`.
- Session `/tmp/lh-treatment-a-retry-session/2026-07-26T23-40-28-362Z_019fa0cd-2b4a-74cd-a84b-418523899ce4.jsonl` is `391,998` bytes with SHA-256 `e85de56f98a2dfdfa93bd57eaf817abe1703294acfdd293ae83a9a2ab8c95103`. Runtime metadata recorded `openai-codex/gpt-5.6-sol` with `thinking=low`, equivalent to the requested route `openai-codex/gpt-5.6-sol:low`; there was one model route, no fallback, and no compaction event.
- The first tool call was the required standalone complete overview. The worker then ran five concrete drill-downs, verified identity, hashed and read the eight allowed paths, inspected only the three-path candidate diff, and wrote only the designated `/tmp` result. All `8/8` tool results succeeded; no subagent, test, build, validation, review agent, sibling checkout, prior packet/transcript, or held-out oracle appeared in the worker tool sequence.
- Result `/tmp/lh-treatment-a-baseline-retry-result.json` is valid JSON, `10,592` bytes, SHA-256 `ba676ee0528aaabdd609782f17345366ffe77e58296d955d5d5c85fc642af092`, with semantic status `complete`, `11` claims, `18` evidence entries, one non-blocking unresolved boundary, one overview, five drill-downs, and eight primary direct path reads.
- Supervisor-side structural, scope, transcript, hash, range, and direct-read checks passed. Parent direct review accepted `11/11` claims and `18/18` evidence bindings. Only after those checks did the parent open the held-out artifacts: independent review had no correctness blocker, and the historical exact-tree standard remained `ok=true`, `fullRegression=true`, `evidenceReused=false`, `91.73 s`, `85/85`, skipped `0`, jobs `4`.
- Worker session runtime was `110.300 s`; preflight through worker completion was `119.420 s`. Worker usage was `78,188` input + `4,842` output = `83,030` prompt/output tokens, `303,104` cache-read tokens, `9` assistant turns, `8` tools, and `$0.687752` reported cost.
- The raw preflight-to-final-oracle-verdict boundary ended at `2026-07-26T23:51:39Z` after `680.401 s`. Post-worker supervisor verification consumed `560.981 s`; no time segment is estimated or omitted.

### Measurement qualification — over-instrumented supervisor

- ADR 0055 requires packet plus **selective** direct reads and explicitly says the parent need not reread every child-read file. The pilot plan likewise requires all governing/conflicting/high-risk/final-decision claims plus only a deterministic low-risk sample.
- The A supervisor instead structurally checked the full transcript and then accepted every `11/11` claim and every `18/18` evidence binding, effectively reconstructing much of the worker's evidence again. Subsequent record closure added more user-visible latency outside the `680.401 s` benchmark boundary.
- Therefore A remains a fidelity-valid replay, but `680.401 s` is retained only as observed over-instrumented protocol cost, **not** as a clean single-agent performance baseline. `110.300 s` worker runtime and `119.420 s` preflight-to-worker completion remain diagnostic components; neither silently replaces the primary metric.

| Metric | Treatment A | Sequential B | A relative to B |
|---|---:|---:|---:|
| Raw preflight-to-verdict wall-clock | `680.401 s`* | `579 s` | `+17.5%` |
| Worker/child runtime | `110.300 s` | `262.454 s` | `-58.0%` |
| Input + output tokens | `83,030` | `186,472` | `-55.5%` |
| Cache-read tokens | `303,104` | `523,264` | `-42.1%` |
| Reported cost | `$0.687752` | `$1.388442` | `-50.5%` |
| Assistant turns / tool calls | `9 / 8` | `20 / 38` | `-55.0% / -78.9%` |
| Overview / drill-down / primary direct reads | `1 / 5 / 8` | `3 / 9 / 14` | `-66.7% / -44.4% / -42.9%` |

- Corrected verdict: **fidelity-equivalent A replay; performance baseline over-instrumented**. The raw table preserves what happened, but the `14.9%` apparent B advantage is not decision-grade because A's supervisor performed an all-claim/all-evidence replay. No treatment is promoted.
- Comparison artifact: `/tmp/lh-treatment-a-baseline-comparison.json`, SHA-256 `1b0e332f936ffc06e50ab87661055fd3e2d06e69340b83405e09e4c5787ffef6`.

## Minimal A/B remeasurement — completed with qualified comparison

- Approved boundary: reverse the earlier order to A then B; run each treatment once with `openai-codex/gpt-5.6-sol:low`, unchanged root/HEAD/fingerprint, no automatic retry, no fresh tests, and the historical held-out oracle. Supervisor proof was limited to all governing/high-risk/final claims plus three deterministic low-risk A samples, at most six target semantic evidence reads, and no full-transcript replay. Record closure is measured separately and excluded from treatment performance.
- Initial A launch: invalid before worker start, exit `127`. `interactive_shell` invoked fish and rejected the bash-style `run_dir=...` assignment. The user approved one corrected launcher attempt using `bash -lc`; prompt, model, root, scope, and verification budget were unchanged.
- Corrected preflight started `2026-07-27T01:17:53Z` and matched root `/home/lazydino/dev/lazy-harness.read-debt-guard`, branch `fix/read-debt-subagent-false-evidence`, HEAD `49691b9b76b3e2c45ea7eba9b56093155afc1614`, fingerprint `25ff7aacbf2848026d26806d08ad76b01b8fa8d5547df60f72ce246064abac1b`, staged count `0`, and the same three tracked modifications. Prompt SHA-256 was `5d72299a3669af2308f783b7c1faf55b8af6473ba212d02b6c107167ac79a954`.
- Corrected A session used the exact model with `thinking=low`, no fallback or compaction, `9` assistant turns, and `8/8` successful tool-result pairs. Worker runtime was `132.875 s`; preflight-to-worker completion was `142.728 s`. Usage was `81,850` input + `5,699` output = `87,549` tokens, `299,520` cache-read tokens, and `$0.729980` reported cost.
- Result `/tmp/lh-min-ab-rerun.Fry3fQ/treatment-a-result.json`, SHA-256 `1410f9473d741bbcc439c5e92284d6025c2e7767c91a1a63a2cab839b1b4b686`, declared `status=complete`, `11` claims, and `20` evidence entries. Structural shape, target identity, ranges, and all whole-file hashes matched current bytes.
- Initial supervisor verdict was incorrect. It equated the absence of a tool named `read` with absence of direct file inspection, although the A prompt/schema required actual direct-read evidence without mandating that specific tool name. Targeted session inspection showed bash call 4 used `nl -ba` over the bounded canonical/source files, call 5 reread the governing records with hashes and line numbers, call 6 used bounded `rg` symbol location, and call 7 used `nl -ba | sed` for the exact Pi/self-test ranges.
- Candidate guard source independently confirms the intended semantics: qualifying read-only bash commands matching `REQUIRED_READ_SHELL_RE` are accepted as required-read evidence unless they are deterministic-packet, retired-find, or lazy-map commands. Therefore the session's byte/range reads are eligible evidence; tool name `read` is not an implicit requirement. The first selective pass still reviewed the predeclared claims with six target semantic evidence reads plus one mandatory re-ground record read and did not replay the full transcript. Its `134.961 s` and `277.689 s` boundaries end at the now-overturned interim verdict, not the final A verdict.
- Corrected A final fidelity: the read-tool-only stop was a supervisor false negative. The held-out review reported no correctness blocker, and the unchanged exact-tree standard oracle remained `ok=true`, `fullRegression=true`, `evidenceReused=false`, `91.73 s`, `85/85`, skipped `0`, jobs `4`. A's content/provenance/identity therefore pass. No A rerun or fresh test execution occurred.
- A's final observed preflight-to-oracle boundary was `1,221.998 s`, but it includes the false stop, user correction, interim record closure, and resumed oracle work. It is retained as contaminated operational history, not a clean treatment metric. A's clean worker diagnostics remain `132.875 s`, `87,549` input+output tokens, `299,520` cache-read tokens, `8` tool calls, and `$0.729980`.
- Fresh Sequential B used runs `29aa5fcd-e005-41c7-a565-03c8d7d42386`, `6e6aba11-8131-4be2-ae1b-50d49ed39864`, and `2365c79d-e2c7-4d28-9436-4fc4b32d57b7`. All resolved `openai-codex/gpt-5.6-sol:low`, completed without fallback/compaction/tool errors, and produced `33` claims with `12` structured evidence entries.
- B parent proof stayed bounded: six target semantic reads total, one low-risk sample per packet (`boundary-loading`, `C1`, `layer-completeness`), all governing/high-risk/final claims, mechanical schema/hash/range/envelope checks, and no full-transcript replay. The TDD scout's first command used a root-binding `cd ... &&` prefix around the exact standalone overview; this preserved the no-batch/no-parallel-first-call invariant and was accepted without retry.
- B clean preflight-to-final-verdict was `784.702 s`. Child runtimes were `75.574 s`, `97.581 s`, and `93.331 s` (`266.486 s` sum); parent preflight/handoff/selective-verification was `518.216 s`. Usage was `217,451` input + `9,114` output = `226,565` tokens, `427,008` cache-read tokens, `19` turns, `34` tool calls, and `$1.574179`.
- Relative to A's worker diagnostics, B used `2.006x` worker runtime, `2.588x` input+output tokens, `2.156x` cost, and `4.25x` tool calls. Both treatments pass the same fidelity/oracle bar, but A's contaminated total prevents a decision-grade primary wall-clock winner.
- Corrected interpretation: this run is a **forensic fidelity stress-test**, not a benchmark of the intended initial record-only retrieval scouts. B deliberately used three sequential fresh sessions, repeated map traversal, source/TDD inspection, file hashes and line ranges, structured schema/provenance, session-envelope checks, selective parent rereads, and a held-out oracle. Its runtime therefore measures packet trust and replay overhead. It does not establish that lightweight record-reading subagents are slow, and its A-favoring worker/compute ratios must not be generalized to that target flow. A separate lightweight-scout measurement would require its own proposal and approval; none is launched by this correction.
- Result artifacts: `/tmp/lh-min-ab-rerun.Fry3fQ/treatment-a-final-oracle.json` (SHA-256 `cb52626fa6827d6e387388bbaf81419f6ea5f10425d46bfa55a0c2b4058961a2`), `/tmp/lh-min-ab-rerun.Fry3fQ/treatment-b-final.json` (SHA-256 `fadb7d560437be492f0ce9e158f6b562f9d04235bc5cbb648f4b115c1475c5c1`), and `/tmp/lh-min-ab-rerun.Fry3fQ/minimal-ab-rerun-stop-summary.json` (final closure hash reported after focused record validation).

## Lightweight record-retrieval Scout — confirmed responsibility and one-run smoke

### User-confirmed responsibility

The user confirmed that the initial retrieval Scout is not merely a path ranker. The Parent supplies one concrete map node and a focused objective; the Scout narrows candidates inside that node, reads the selected canonical records in full, reads only directly linked source/test evidence needed to support the bounded answer, and returns evidence the Parent can use. Recursive linked-chain expansion is excluded. If the bounded scope is insufficient, the Scout returns `needs-more-context` or `needs-split` rather than inferring or widening silently.

The Parent retains complete overview, direct governing-record reads, semantic conflict resolution, option gates, final synthesis, and final validation ownership. It reads the packet and then directly verifies every governing/conflicting/high-risk/final-decision claim plus one deterministic low-risk sample. Current guard semantics do not promote child reads into Parent read-debt evidence.

The handoff is evidence-oriented rather than summary-only. It preserves selected and materially rejected candidate paths, explicit record rules and prohibitions, path/hash/range provenance, conflict/unknown state, `parentRead[]` with reasons, and `notRead[]` for bounded exclusions. Read-only remains specific to this retrieval role; it is not a universal restriction on separately approved writer or implementation agents.

### External research grounding

This responsibility shape is consistent with, but not proven for this code-record corpus by, adjacent research and production guidance:

- Anthropic's multi-agent research and context-engineering reports use subagents as focused information filters that return condensed evidence to a lead agent, while warning that multi-agent work increases token cost and should be admitted only when the context/latency benefit is measurable.
- Speculative RAG (`arXiv:2407.08223`) delegates focused document processing to smaller specialists and retains a stronger generalist verification pass.
- SlimPLM (`ACL 2024, 2024.acl-long.242`) supports using a smaller proxy to decide what needs retrieval; RECOMP (`arXiv:2310.04408`) supports selective compression rather than forwarding every retrieved document.
- Lost in the Middle (`arXiv:2307.03172`), Sufficient Context (`arXiv:2411.06037`), and ALCE (`EMNLP 2023, 2023.emnlp-main.398`) motivate narrow high-signal context, explicit insufficiency outcomes, and concrete attribution instead of unverified summaries.

These sources justify a bounded smoke hypothesis, not framework adoption or a performance claim. Their principal evaluations are research/QA/RAG workloads rather than Lazy-Harness canonical-record retrieval.

### Approved one-run smoke envelope

- Approval: user-confirmed for one Planning update plus exactly one smoke run.
- Concrete feature node: `record-decision-broker`.
- Objective: identify the canonical rules that govern when response-completed work produces a Record Decision Packet, how candidate capture differs from canonical promotion, and which implementation/test surfaces protect that boundary.
- Runtime/model: one fresh Pi Subagents `scout` session requesting exact `openai-codex/gpt-5.6-luna:medium`; no automatic fallback and no retry.
- Mutation boundary: Scout is project read-only. No source, runtime, schema, guard, canonical record, graph, or project artifact mutation is permitted. Runtime-owned output may be stored under `/tmp`.
- Current-runtime caveat: the child may still receive the full Lazy-Harness grammar and must satisfy its own current map/read guard. This smoke cannot measure or claim an unimplemented thin-role prompt or delegated-evidence bridge.
- Read budget: at most three selected canonical records and at most two directly linked source/test bodies. No recursive link traversal.
- Output budget: at most ten claims, twelve evidence bindings, eight unresolved/exclusion entries, and 9,000 output characters. Overflow returns `needs-split`.
- Required handoff fields: status; root/revision/fingerprint/model provenance; selected records and selection reasons; materially rejected candidates and reasons; explicit rules/prohibitions; path/hash/range evidence; conflicts; unresolved items; `parentRead[]`; `notRead[]`.
- Parent proof: verify all governing/conflicting/final-decision claims and one deterministic low-risk claim, check packet/root/model identity mechanically, and do not replay the full child transcript by default.
- Measurements: preflight-to-packet wall-clock, child runtime, Parent selective-verification time, request-to-verdict time, turns/tool calls, input/output/cache tokens and reported cost when available, selected/read counts, and fidelity disposition.
- Stop conditions: unavailable Luna route, stale root/revision/fingerprint, project mutation, invalid/overflow packet, ambiguity requiring user choice, or failed child result. All stop without fallback or retry.
- Interpretation ceiling: report only smoke fidelity, latency, and observed overhead. Do not promote Luna, set a model default, infer a multi-Scout topology, claim a clean Parent-vs-Scout winner, or implement runtime/schema/guard changes from this single sample.

### Smoke result — completed, protocol-fail/no-retry

- Run: `00b2fe9a`; session: `/tmp/lh-luna-record-decision-broker-smoke-session/run-0/session.jsonl`.
- Route: runtime resolved `openai-codex/gpt-5.6-luna` with `thinking=medium`, matching the requested `openai-codex/gpt-5.6-luna:medium`; no fallback, retry, compaction, or tool error occurred.
- Execution shape: `9` assistant turns and `13` tool calls (`bash=5`, `read=6`, `grep=1`, `structured_output=1`). The first tool call was the exact standalone complete overview, then root/HEAD/branch/status identity matched and the concrete node was drilled.
- Child session wall-clock was `114.782 s`; preflight snapshot to packet was `272.012 s`; packet to bounded Parent verdict was `355.917 s`; preflight to verdict was `627.929 s`. The interactive approval timestamp was not preserved, so request-to-verdict is not claimed. Record closure remains separately excluded.
- Reported summed usage was `195,175` input, `4,963` output, `101,376` cache-read, and `1,078` reasoning tokens; reported cost was `$0.2350906`. These are one-smoke diagnostics under the current full-grammar/child-overview runtime, not a thin-scout estimate.
- Content result: the recovered packet selected the broker SDD, broker TDD, and ADR 0028; it read the generator and bounded self-test evidence; it returned `10` claims and `12` evidence bindings. Schema validation passed, every evidence reference resolved, every whole-file hash and range matched, and the project tree fingerprint remained byte-identical.
- Selective Parent review directly confirmed the governing SDD, ADR candidate-versus-canonical boundary and recorded status tension, TDD protection matrix, generator disposition/candidate/instruction source, and one low-risk exact-five-candidate fixture. Recovered content fidelity therefore passed.
- Protocol failure 1: compact JSON measured `12,062` characters against the approved `9,000` limit (`3,062`, or `34.02%`, over). The child exhausted the count ceilings but returned `status=complete` instead of `needs-split`.
- Protocol failure 2: the child successfully called `structured_output`, but the normal supervisor/intercom result reported `(no output)`. The Parent recovered the packet only by targeted session-envelope inspection, so the required end-to-end handoff did not succeed.
- Overall verdict: `protocol-fail-no-retry`. The content demonstrates that Luna can select and ground useful records in this sample, but the approved contract did not pass. No model promotion, second run, topology choice, live dogfood, or runtime/schema/guard implementation follows.
- Artifacts: preflight `/tmp/lh-luna-record-decision-broker-smoke-preflight.json` (`1d286f8c2be6bb9161bab3f0f5aa2f930d6a8efe288df41e3e363efb2d0aebea`); task `/tmp/lh-luna-record-decision-broker-smoke-task.md` (`0f24374745fb00ad890f8bebb8197233b0da8b0caa88ff13475ece5b075ea766`); schema `/tmp/lh-luna-record-decision-broker-smoke-schema.json` (`d7688cc45c3245f076b89e9aa4f46dce4a73753a8fb13a62a082ac0043d00ca1`); packet `/tmp/lh-luna-record-decision-broker-smoke-packet.json` (`4e1bb0728c34bf90ef432cee3da0a5771c7b24fbb594c638afab0c3945c76c8c`); session metrics `/tmp/lh-luna-record-decision-broker-smoke-session-metrics.json` (`ff70ca00f76de881e38f571ab791cb1c45675f4362e8d8906460ddb7475c00ce`); tree comparison `/tmp/lh-luna-record-decision-broker-smoke-tree-comparison.json` (`3c581e8ce877f5d821a60d11d72c8133411da42ac6bffa8a2876aa83cafc3933`); verdict `/tmp/lh-luna-record-decision-broker-smoke-verdict.json` (`63498d276124505170dc30c6943e36f80de544fa84bca528ef477ea5a9e7cfa9`).

## Metrics

### Primary

- request-to-validation wall-clock,
- critical-path length,
- time spent in discovery/loading, integration, and validation.

### Context and compute guardrails

- parent and per-child peak context,
- compaction count,
- prompt/output token proxy,
- total worker compute and fan-out count.

### Churn and quality

- duplicate map/read/tool/validation calls,
- handoff, merge, and rework time,
- wrong-root/stale-epoch/scope-overflow events,
- correctness and regression results,
- record continuity and design-review quality,
- scout claim precision under parent sampling.

## Acceptance criteria

A treatment is a candidate improvement only when:

1. the same acceptance checks and final validation pass,
2. no governing record, conflict, or high-risk boundary is missed,
3. every child claim used by the parent has concrete provenance,
4. parent direct evidence remains sufficient under current guard semantics,
5. context/token/compute do not grow without a wall-clock or quality benefit,
6. integration/rework does not erase the critical-path gain,
7. results are reproducible on at least one historical replay before live dogfood promotion.

No fixed percentage improvement is assumed before baseline measurement.

## Sequence and approval gates

1. **Packet-only dry design — complete:** packet fields, outcome vocabulary, ownership, replay corpus, attribution strategy, and no-fallback model policy are recorded here. Records only.
2. **Existing-runtime replay — full Sequential B passed:** the exact-path canary and all three fresh sequential branches are integration-eligible and match the held-out historical oracle. This establishes replay fidelity, not performance benefit.
3. **Treatment A baseline — complete after one corrected retry:** the first approved launch was invalidated by quiet auto-exit; the separately approved one-time launch correction completed with replay-equivalent fidelity and a measured A/B trade-off.
4. **A/B result review — stopped and qualified:** the user selected **stop and review**, then confirmed the over-verification lesson belongs in this Planning record. A's `680.401 s` total is retained as over-instrumented protocol cost, not a clean performance baseline; B is not promoted and no further treatment is approved.
5. **Minimal A/B remeasurement — complete as forensic fidelity stress-test:** corrected A and fresh Sequential B both pass fidelity against the same held-out oracle. The observed B overhead belongs to serial packet/provenance/oracle reconstruction, not the intended initial record-only scout path. No lightweight-scout speed conclusion, total-wall winner, or treatment promotion follows.
6. **Lightweight Luna smoke — completed, protocol-fail/no-retry:** recovered content passed bounded semantic review, but the packet exceeded its serialized output budget without `needs-split` and normal supervisor delivery returned no output. No second run or treatment promotion is authorized.
7. **One bounded Luna live dogfood — completed, protocol-invalid/no-retry:** the user selected the real task of assessing what the current missing `ts-morph` and `@earendil-works/pi-coding-agent` packages block and whether those failures prevent read-only Scout work.
   - Run `5d2e7bb1-d467-4ef1-9d67-9be81fbf250a` resolved exact `openai-codex/gpt-5.6-luna:medium`, used no fallback or retry, and preserved the project status and byte fingerprint. Runtime was `198.801 s`; the session recorded `19` assistant turns, `18` tool-call intents (`17` executed per supervisor), `336,327` input + `6,116` output tokens, `333,824` cache-read, `958` reasoning tokens, and `$0.8128108`.
   - The compact artifact `/tmp/lh-luna-live-dogfood-validation-blocker-20260727/result.json` is `6,692` bytes, SHA-256 `2dc6b4df0c22284b7245bb920eb4e445c1c0a28fec3275bd2cf3a76d89096033`. The first tool, identity checks, final `wc -c`, designated `/tmp` ownership, and no-project-mutation checks passed.
   - The arm nevertheless failed its protocol. The supervisor aborted after turn `19` exceeded the `16 + 2` turn envelope. The Scout also read four canonical records plus two source/config bodies (`6` unique paths) against the `3 + 2` / five-path ceiling, then declared `complete`; its `canonicalBodiesRead=3` and `linkedBodiesRead=0` self-report omitted the extra ADR read and two linked bodies. Mechanical validation therefore failed, and no retry repairs the result.
   - Bounded Parent review found the core content useful with one required scope correction: both project-root imports are unresolved; missing `ts-morph` blocks the non-BDD `code-change.ts` AST paths exercised by full self-test; the Pi package declares the Pi agent as a peer. However, the missing project-root Pi module blocks source-local package smoke/test or extension-loading paths, not every Pi runtime surface—the globally installed Pi/Subagents runtime successfully launched this exact Luna run.
   - The missing local packages therefore keep framework full regression incomplete, but they did not prevent this read-only Scout from running map/read/probe work. This distinction is evidence for later dependency-ownership review, not approval to install packages or promote Luna/runtime/schema/guard defaults.
   - Adjudication: `/tmp/lh-luna-live-dogfood-validation-blocker-20260727/adjudication.json`; final verdict `protocol-invalid-no-retry`.
8. **Contract implementation proposal:** only if evidence supports it, propose SDD/TDD/schema/profile-adapter changes.
9. **Verified delegated-evidence bridge:** separate, later approval; requires supervisor provenance and root/revision/epoch/path/hash proof.

The user's approval now covers Step 1 through the completed bounded Luna live dogfood under Step 7. That one-run allowance is consumed. C, another Luna run, automatic retry, dependency provisioning, admission-control implementation, guard adoption, packet/runtime implementation, model-default promotion, commit, push, sync, and release remain unauthorized.

Layer impact for this result: Planning updated. SDD candidate — future execution envelopes may need supervisor-owned serialized/read/turn counters rather than model self-report; no contract change is approved. TDD candidate — a later fixture may cover exact turn-budget completion and extra-body/self-report mismatch. DDD, BDD, ADR, and SSOT have no independent semantic delta.

## Dependencies and blockers

- Current Pi/OMP child sessions may still receive the full `.lazy-harness/AGENTS.md`; Phase 0 must not attribute savings to a thin prompt that is not implemented.
- The main branch has no verified delegated-evidence bridge.
- The false-`requiredRead` guard correction remains a validated source-only candidate in a separate worktree and is not deployed.
- The primary checkout contains unrelated concurrent changes; do not stage, revert, or absorb them into this pilot.
- Permanent packet schema paths, runtime ownership state, queue/retention, and lease keys remain unapproved.
- The 2026-07-27 minimal remeasurement is closed: A and B pass fidelity, A's total is contaminated by supervisor correction, B's clean total is available, and no automatic continuation or treatment promotion follows.
- The one-run Luna smoke exposed two bounded follow-up candidates—serialized-budget enforcement and structured-output delivery—but neither is approved for source/schema/runtime work, and the delivery symptom needs independent reproduction before being called a runtime defect.

## Out of scope

- queue or daemon implementation,
- a new agent execution engine,
- automatic canonical record writing,
- packet-only parent proof,
- full-grammar child prompt removal,
- host sync, commit, push, or release,
- graph migration,
- WP1A/WP1B/WP2/WP3 adoption.

## Implementation map

- Status: `none` — this is a records-only pilot plan; no source/schema/runtime files are selected for mutation.
- Current validated evidence:
  - `.lazy-harness/evidence/2026-07-26-agent-neutral-orchestration-contract-canary.md` — successful v0.37.0 exact-path canary, full Sequential B packet/oracle result, and corrected Treatment A baseline with A/B wall-clock and compute comparison.
  - `/tmp/lh-luna-record-decision-broker-smoke-verdict.json` — one-run Luna smoke verdict and pointers to the recovered packet/session/preflight evidence; transient runtime evidence, not canonical implementation truth.
- Existing runtime used by a future approved replay:
  - Pi Subagents provides fresh sessions, model override, chain/parallel execution, artifacts, and supervision.
  - Lazy-Harness current map/read debt remains parent-owned.
- Planned protection before framework adoption:
  - packet schema validation,
  - root/revision/epoch mismatch fixtures,
  - scoped-read and overflow fixtures,
  - task-text/failed-read false-proof fixtures,
  - parent sampling and packet replay equivalence,
  - single integrator/writer/final-validator ownership.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md`
  - SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`, `.lazy-harness/spec/platform/pi-agent-package.md`
  - TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md`
- Machine index:
  - no graph row added because the pilot has no approved implementation edge.

## Rule placement

- Rule: for this pilot, treat A's `680.401 s` total as over-instrumented protocol cost rather than a clean performance baseline; any future measurement proposal must predefine bounded selective supervisor verification and report worker, supervisor, and record-closure time separately.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`; ADR 0055 remains the architecture authority for selective parent proof.
- Why not AGENTS.md: this is an experiment-specific measurement correction, not confirmed universal all-agent grammar.
- Why not local notes: the correction affects shared project benchmark interpretation and must remain visible across runtimes and sessions.
- Confirmation: user-confirmed — after identifying the over-deep verification, the user selected **C. Planning record**; no SSOT policy, ADR amendment, or local-only rule was approved.
- Remeasurement correction: `successful direct read` means verified inspection of the actual bounded bytes/ranges; it does not imply a tool named `read` when the approved protocol allows qualifying read-only shell commands. Scope remains `transient-plan`; confirmation is user-confirmed after targeted session/source evidence.
- Benchmark-scope correction: user-confirmed on 2026-07-27 that only subagents initially invoked for record retrieval are inherently read-only; this is not a universal prohibition on every subagent role. The completed B replay is retained as a forensic fidelity/provenance stress-test and excluded from conclusions about lightweight initial record-reader latency. No rerun or implementation is approved.
- Lightweight-smoke placement: the user confirmed the Scout responsibility and approved exactly one records-plus-smoke work unit. Its useful content and failed envelope remain in this transient Planning record; the result does not independently change framework architecture, deployed behavior, schema, model defaults, or regression contracts.

### Clean sequential rerun correction

- Rule: run the newly approved Direct Sol, Sol Scout, and Spark Scout benchmark arms one at a time from one fresh baseline; disable builtin Scout output persistence with `output:false`, preserve each designated `/tmp` result, and retain no-fallback/no-retry plus project-read-only boundaries.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`.
- Why not AGENTS.md: this is a one-series experiment envelope and measurement interpretation, not universal agent grammar or an approved runtime default.
- Why not local notes: the correction governs shared project benchmark evidence across sessions and runtimes; it is neither private nor Pi/OMP-local preference.
- Confirmation: user-confirmed — the user selected **3개 모두 새 순차 실행** after the output-ownership conflict was distinguished from concurrent resource contention.

## Discovery capture

- DDD: none — no independent domain or business vocabulary was introduced.
- SDD: candidate — a future evidence schema may distinguish `toolName`, command method, and byte/range attestation explicitly so a generic `readMethod` label cannot be mistaken for a specific tool requirement. The Luna smoke additionally suggests enforcing the serialized packet budget before `complete` and defining delivery semantics for runtime-captured structured output; neither change is approved.
- BDD: none — ADR 0055 already defines retrieval children as read-only and separately bounds other orchestration roles; the correction removes an experiment-scope misinterpretation rather than changing deployed behavior.
- TDD: candidate — the prior read-tool false negative was an experiment-supervisor interpretation rather than a runtime regression. The Luna smoke now suggests, subject to separate approval and independent reproduction, fixtures for serialized-budget overflow → `needs-split` and structured-output delivery when legacy output/artifact persistence is disabled.
- ADR: none — ADR 0055's confirmed architecture and trust boundary are unchanged.
- SSOT: none — packet schema path, queue/retention, lease ownership, and permanent model defaults remain unapproved.
- Planning: updated — this primary record preserves the forensic A/B interpretation, the user-confirmed retrieval Scout responsibility, adjacent research grounding, and the completed one-run Luna smoke. The smoke is `protocol-fail-no-retry`; C, another Luna run, live/runtime/admission work, and treatment promotion remain unapproved.
- Candidate store: none — unresolved implementation contracts remain explicitly bounded in this primary planning record.
