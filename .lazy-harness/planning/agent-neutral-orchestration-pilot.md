# Planning — Agent-Neutral Orchestration and Scoped Retrieval Pilot

Status: dedicated Reader runtime standard-verified and independently reviewed in isolated worktree; live model smoke and main integration pending; v1–v3 proof candidates remain historical failed evidence
Date: 2026-07-24
Updated: 2026-09-04
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
  - planning the dedicated Harness Reader, Parent code/behavior lane, and join-before-action flow
  - comparing the simple joined flow with Direct Parent after implementation
- Must:
  - make one dedicated Reader own complete stored-record inventory plus task-relevant canonical reads across DDD/SDD/BDD/TDD/ADR/SSOT/Planning
  - let the Parent concurrently inspect source/tests or immediately needed behavior
  - join the ordinary Reader response before plan/mutation/completion
  - avoid duplicate Parent record reads after `complete`; use bounded fallback for `incomplete|conflict|failure`
  - keep one Parent integrator/writer/final validator
- Must not:
  - implement the superseded v1–v3 admission/provenance/audit/agreement proof architecture
  - make the Parent preselect Reader record nodes or require routine Parent rereads for debt
  - add a queue, daemon, delegated permit, persistent model default outside the explicit Reader route, or main integration without separate approval
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
- Harness record ownership: dedicated Reader inventories/searches/reads relevant canonical records across all stored layers.
- Parent lane: concurrent source/tests or immediately needed behavior; Parent retains decisions, mutation, integration, and validation.
- Join: Parent waits for ordinary `complete|incomplete|conflict` Reader response before action; successful completion does not require duplicate Parent debt reads.
- Current direct debt hooks: transitional deployed behavior pending separately approved replacement.
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
8. **Medivance five-arm record-reader benchmark — completed, no promotion:** the user approved one sequential records-only comparison on Medivance `main@74315a091ae914e95114625467a067384d18abc5` for the user-facing question `예약관리의 예약 받기/예약 안받기 정책`. One fresh Direct Parent `openai-codex/gpt-5.6-sol:medium` arm and four fresh `delegate` arms (`sol:medium`, `luna:low`, `luna:medium`, `luna:xhigh`) received the same prompt, performed complete map discovery, selected canonical records themselves, and were forbidden from product-source reads and project mutation.
   - Direct Sol-medium completed in `101.523 s`, `6` turns / `11` tools, with `89,323` input, `3,829` output, `240,128` cache-read tokens, and `$0.681549`; bounded Parent review found all six core record groups and all fifteen critical policy facts.
   - Luna-low completed in `91.418 s`, `9` turns / `11` tools, with `91,284` input, `3,065` output, `418,816` cache-read tokens, and `$0.030311`. It was the only delegated arm faster than Direct and was about `95.6%` cheaper by reported cost, but it found only four of six core record groups and repeated the stale all-selectable-target wording instead of the latest state-subset rule. It is not safe as an autonomous policy authority.
   - Luna-medium completed in `234.766 s`, `20` turns / `19` tools, with `104,206` input, `10,251` output, `1,276,416` cache-read tokens, and `$0.058671`. It found only two of six core groups and omitted operating-hours/holiday authority plus the full staff-schedule boundary; this one sample does not support a medium default.
   - Luna-xhigh recovered all six core groups and all fifteen facts, but exceeded the `20 + 2` turn envelope after `32` turns / `34` tools. Its session span was `351.113 s`, with `187,663` input, `13,929` output, `3,243,520` cache-read tokens, and `$0.119118`. The recovered file is content-eligible evidence only; the arm is protocol-failed.
   - Subagent Sol-medium likewise recovered complete content but exceeded the envelope after `23` turns / `22` tools. It took `188.284 s`, consumed `115,406` input, `6,750` output, `1,680,384` cache-read tokens, and `$1.619722`; same-model delegation was slower and more expensive than Direct in this envelope.
   - The experiment exposed an avoidable delivery cost: caller-designated file output caused child `write`/`edit`/`read`/`wc` cleanup loops. The next proposal should use a dedicated record-reader role with no write/edit tools, normal compact response delivery, complete discovery, direct full record reads, and bounded one-hop canonical cross-link/backlink closure. It should make Luna a retrieval aid while Parent Sol-medium retains conflict resolution and selective canonical rereads.
   - Parent-context saving remains the intended benefit, but exact peak-context reduction was not exposed by the runtime. The measurable handoffs were `5,671–7,483` characters; total delegated compute/context increased in every arm. A real parallel Parent-code / child-record shadow task is still required to establish end-to-end wall-clock and Parent-context benefit.
   - Medivance tracked state and the pre-existing untracked `0.43.78` remained unchanged. Transient comparison: `/tmp/medivance-record-reader-benchmark-20260822/comparison.md`, SHA-256 `6cf4e7c8fd73b406bd125752d1963fbf767871b3fc13ffc4652186d8580ba97d`; metrics SHA-256 `cbd195215f91e6bac96a0d71e869d5eacef77f7319637ad54152cdf6e7774bcf`.
9. **Contract implementation proposal:** only if evidence supports it, propose a dedicated records-only reader profile and focused SDD/TDD changes; no source or runtime implementation is approved by the benchmark.
10. **Verified delegated-evidence bridge:** separate, later approval; requires supervisor provenance and root/revision/epoch/path/hash proof.

The user's approval now covers Step 1 through the completed Medivance five-arm benchmark under Step 8. The approved run allowance is consumed. A dedicated record-reader implementation, model default, additional benchmark, live parallel shadow task, delegated-evidence bridge, automatic Record Writer, source/schema/guard mutation, commit, push, sync, and release remain separately approval-gated.

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
- SDD: candidate — a separately approved dedicated Record Reader contract may need records-only tool scope, normal response delivery without child file editing, complete discovery plus bounded one-hop canonical closure, and explicit incomplete/conflict outcomes. No profile/schema/runtime change is approved.
- BDD: none — the benchmark evaluates internal record retrieval and does not change product-visible behavior.
- TDD: candidate — a later focused fixture may compare core-record recall, critical-rule fidelity, source-read prohibition, project-state preservation, turn-envelope completion, and compact response delivery across exact model routes. No regression implementation is approved.
- ADR: none — ADR 0055's confirmed architecture and trust boundary are unchanged.
- SSOT: none — packet schema path, queue/retention, lease ownership, and permanent model defaults remain unapproved.
- Planning: updated — this primary record now preserves the forensic A/B history, earlier Luna failures, and the completed Medivance five-arm record-reader benchmark. The benchmark supports a narrower dedicated-reader proposal, not a model/runtime/default promotion.
- Candidate store: none — unresolved implementation contracts remain explicitly bounded in this primary planning record.

## Prospective real-work Record Reader quality shadow — approved 2026-08-25

### User-confirmed direction

The user selected **실작업 읽기 Shadow** before integration or Writer planning and then explicitly approved execution. This work unit measures whether the dedicated `record-reader/v2` preserves real-work semantic quality; it does not authorize canonical mutation, a delegated-evidence permit, a runtime/model default, or production integration.

### Frozen ten-case protocol

- Count exactly ten distinct user/project work units. A calibration run, same-candidate remediation, or retry does not count as another passed case.
- Use the committed `record-reader/v2` contract and `record-reader-admission/v2` representation from experiment revision `e6fd2abbad5a13e3c2f37a53160f2e862d8b69f2`; any contract change starts a new protocol version rather than rewriting prior outcomes.
- Each counted case freezes root/revision, Parent catalogs and packet bytes, mode, budgets, and an independently retained Parent baseline before opening the Reader result.
- Run the Reader in fresh context, blinded from Parent answers/oracles, records-only, project read-only, no supervisor/intercom contact, no fallback, and no automatic retry.
- Exercise both explicit modes across the suite. A work unit may use a candidate-map pass followed by a separately approved claim-evidence bundle, but each candidate remains first-attempt evidence.
- Retain full child session, packet, generated output schema, captured payload, deterministic admission receipt, Parent audit, pre/post project fingerprint, timing/cost metadata, and review disposition.
- Coverage must include ordinary retrieval, cross-layer evidence, conflict or supersession, missing evidence or option-gate behavior, alias/backlink discovery, and stale/remap/overflow handling. If ten natural cases do not cover the matrix, the proof remains incomplete rather than filling it with synthetic passes.

### Acceptance gate

The suite passes only when all counted cases satisfy the applicable contract and the aggregate has:

- 100% recall for governing, conflicting, superseded/reverted, high-risk, and final-decision facts in the frozen Parent baseline;
- zero unsupported factual claims and zero stale-current substitutions;
- exact path/hash/range provenance and exact supplied facet/inventory coverage;
- correct non-success status for missing evidence, conflict, remap, stale identity, dependency block, or overflow;
- output at or below the 6,000-character soft target when feasible and never above the 12,000-character hard cap;
- zero forbidden source/generated/session/external access, zero project mutation, and zero oracle disclosure;
- Parent direct rereads for governing/conflicting/high-risk/final facts; Reader output never clears Parent read debt;
- independent post-suite methodology and semantic-quality reviews with no unresolved semantic Medium or higher.

A failed first attempt remains failed. A fresh unseen replacement may test a corrected future contract, but it cannot relabel the original case or satisfy this frozen-version ten-case gate.

### Outcome boundary

Passing this shadow permits only a separately approved plan for opt-in, read-only, non-canonical proposal shadowing. Automatic Writer, canonical record mutation, daemon/queue, delegated-evidence permits, production reviewer provenance, merge, release, and the deferred 37-row graph migration remain out of scope.

### Evidence root

Persistent evidence is stored outside canonical project records under `/home/lazydino/.local/share/lazy-harness-proofs/record-reader-real-work-shadow-v1-20260825`; this Planning record owns the durable direction and final bounded verdict, while raw prompts/sessions stay evidence-only.

### Rule placement

- Rule: validate real-work Record Reader quality before any integration or Writer planning.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`.
- Why not AGENTS.md: this is a bounded experiment protocol and approval state, not universal agent grammar.
- Why not local notes: the plan and verdict must remain shared across project sessions and runtimes.
- Confirmation: user-confirmed — the user selected the recommended real-work shadow and then said `진행해줘`.

### Discovery capture

- Planning: this record is the sole canonical owner of the ten-case shadow protocol and status.
- SDD: no independent delta; the existing Reader contract is frozen for this protocol.
- TDD: no independent delta yet; case evidence remains outside canonical records until a validated contract defect or regression is confirmed.
- ADR: no independent delta; ADR 0055 Parent/Reader authority remains unchanged.
- DDD/BDD/SSOT: no independent delta.
- Graph: no implementation edge or canonical graph row is added for a read-only experiment.

### Case `rw-001-reader-quality-status` — failed first attempt

- Source: actual user work unit asking whether Reader quality was validated and what should proceed next.
- Two retained launcher/preflight failures occurred before any Reader child started and do not count as Reader attempts.
- The first actual Luna High Reader candidate preserved the core question structure, all facet/inventory ids, Parent authority, and no-promotion boundary, but failed the frozen gate.
- Protocol/capture blocker: it consumed all 14 allowed probe/map/read/hash calls, then attempted required `structured_output` as blocked call 15; fallback prose is not an admitted runtime capture.
- Semantic provenance blocker: it cited Planning lines `700-783` as the Medivance benchmark even though the benchmark is at `681-695`, so critical benchmark facts were not bound to the cited bytes.
- Additional provenance defect: it cited `784-829` for the shadow section, which starts at `773` and ends at file line `828`.
- Independent review also found the frozen Parent baseline mis-cited A1-A4 by one line and A9 by a different section. Those oracle defects remain frozen and are not silently repaired.
- Mechanical schema admission passed for reconstructed JSON values, proving only payload shape/cardinality; transport execution and exact semantic provenance independently failed.
- Safety passed on the declared measured project surface: correct identity-probe order, no forbidden access, no mutation calls, no supervisor contact, and identical pre/post HEAD/status/diff/inventory hashes.
- `claim-evidence` was not run because the candidate-map gate failed. No same-case retry can count as a V1 pass.
- Frozen V1 verdict: **FAILED**. One counted failed first attempt makes its all-ten-pass acceptance criterion unattainable.
- Evidence: `/home/lazydino/.local/share/lazy-harness-proofs/record-reader-real-work-shadow-v1-20260825/cases/rw-001-reader-quality-status`.
- Next action requires a user decision: continue nine cases for diagnostic breadth only, stop and design a corrected V2 with ten unseen work units, or stop the shadow while retaining this failure.

### Recovery direction — V2 selected, execution approval pending

The user selected **V2 설계 후 새 10건**. Frozen V1 remains failed and closed; `rw-001` is never relabeled or reused as a counted V2 case.

The proposed V2 must, before any counted candidate:

1. mechanically validate every Parent oracle path/hash/range against frozen source bytes;
2. run a non-counting transport canary proving the required `structured_output` call executes within the exact packet/tool budget;
3. freeze an operational call formula that leaves one final submission call and returns overflow/split before repeated body reads consume it;
4. separate payload-schema admission, transport/capture attestation, and exact-range attestation; all three must pass;
5. retain first-attempt failures and use ten entirely unseen actual project work units;
6. preserve Parent authority, bridge-off transport, equal soft/hard budgets, 6,000/12,000-character limits, no mutation, no automatic retry, and no model/runtime/integration promotion.

This selection authorizes plan design, not source/runtime modification or V2 execution. The rw-001 failure introduced new constraints, so the earlier execution approval is stale until the Parent proposes the corrected protocol and the user explicitly renews execution approval.

#### Rule placement

- Rule: close failed V1 and design a corrected V2 before any further counted Reader-quality run.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`.
- Why not AGENTS.md: this is an experiment recovery decision, not universal agent grammar.
- Why not local notes: the failure and recovery boundary must remain shared project evidence.
- Confirmation: user-confirmed — `V2 설계 후 새 10건`.
- Execution approval: user-confirmed — build only a disposable V2 proof harness, require oracle and transport non-counting preflight success, then collect ten entirely unseen actual work units sequentially; stop immediately on a failed preflight or counted case.

### V2 non-counting preflight — failed and stopped

- Positive/negative oracle fixtures passed: valid exact path/hash/range/text evidence was admitted, while shifted range, EOF, and wrong-hash fixtures were rejected.
- Payload admission passed as `proposal-ready`. Transport/capture passed with Luna High, bridge off, exact probe order, one map/read/hash per node, 10 of 14 total calls, and successful final `structured_output`.
- Exact range syntax, frozen record hashes, and EOF bounds passed. Project preservation passed over the declared HEAD/status/diff/625-row inventory surface.
- Mandatory oracle-fact overlap failed with eight errors. Four A1/A2 errors expose a method defect: semantically equivalent detailed ADR ranges were rejected only because they did not overlap the digest lines selected by the oracle. A5 is likewise restated at another canonical line.
- Independent semantic audit also found real candidate defects that the method false negatives do not excuse: Q3 referenced the wrong R2 range index for the generated-output rule, and Q4 referenced ranges that omit the actual Phase-0 prohibition at ADR line 138.
- Independent review verdict: **FAIL**. V2 preflight is frozen; no same-canary repair is counted or relabeled.
- V2 suite verdict: **NOT PROVEN** with zero counted cases. Per the approved stop rule, no real-work case may start.
- Evidence: `/home/lazydino/.local/share/lazy-harness-proofs/record-reader-real-work-shadow-v2-20260825`.
- Planning remains the primary owner because the defect is in an unintegrated disposable proof protocol. SDD/TDD now have a confirmed future candidate—separate mechanical range validity from semantic support—but no source/runtime contract or regression fixture is changed without a newly approved protocol.
- Next action requires a new user decision: stop Reader shadowing, or design a new protocol version that keeps deterministic syntax/hash/bounds checks while assigning semantic evidence support to frozen Parent plus independent review rather than exact overlap with one oracle span.

### Proposed V3 protocol — design selected, execution approval pending

V1 and V2 remain immutable failures. V3 does not repair, relabel, or reuse either candidate or canary.

1. **Two unseen non-counting preflight arms.** One fresh `candidate-map` arm and one distinct fresh `claim-evidence` arm use different objectives and canonical records from V1/V2. Both must pass before any counted work unit starts.
2. **Parent oracle before candidate.** The Parent freezes objective facets, inventory, critical evidence atoms, exact supporting quotes/ranges, record hashes, snapshot, and expected authority boundaries before candidate output. Deterministic admission rejects an invalid oracle before launch.
3. **Oracle is audit evidence, not a citation whitelist.** Candidate evidence may use any exact canonical range. A candidate is not mechanically rejected merely because its supporting bytes differ from the Parent oracle span.
4. **Mechanical range integrity only.** Deterministic admission verifies allowed path, frozen content hash, `L<start>-L<end>` syntax, EOF bounds, valid evidence indexes, required evidence presence, exact coverage keys/cardinality, output budget, transport capture, and project preservation. It does not claim semantic equivalence.
5. **Independent semantic adjudication.** After the candidate is frozen, the Parent and one fresh independent reviewer separately map each candidate question/claim atom to its cited bytes and each critical oracle atom to candidate coverage. The reviewer receives the frozen oracle and candidate but not the Parent verdict until its review is frozen.
6. **Pass rule.** A preflight or counted case passes only when payload, transport, mechanical provenance, preservation, Parent semantic audit, and blinded independent semantic audit all pass and agree. Every critical atom must be represented; every substantive candidate atom must be fully supported; no authority expansion, answer substitution, or unjustified promotion is allowed.
7. **Disagreement and invalid-oracle rule.** Parent/reviewer disagreement or a reviewer-discovered oracle defect stops the case as a protocol failure. It is never resolved by silently changing the frozen oracle or candidate.
8. **Ten unseen actual work units.** After both preflight arms pass, collect exactly ten distinct real project/user work units. Each must pass `candidate-map` before its paired `claim-evidence` run. Synthetic filler, V1/V2 reuse, and same-candidate remediation do not count.
9. **Immediate stop.** Any failed preflight arm or counted first attempt freezes that protocol version as not proven and prevents later cases from restoring an all-pass claim.
10. **Authority and transport unchanged.** Parent owns discovery, governing reads, semantics, mutation, validation, record placement, and promotion. Reader remains bridge-off Luna High with fresh context, no fallback/retry, equal 14/14 tool limits, 6,000/12,000-character limits, no mutation, and no Parent read-debt clearance.
11. **Promotion remains separately gated.** V3 success would authorize only a later integration proposal. It does not authorize a delegated-evidence permit, persistent model default, runtime integration, Writer, queue, daemon, canonical mutation, merge, release, or the deferred 37-row graph migration.

#### V3 rule placement

- Rule: distinguish mechanical provenance integrity from semantic evidence support while retaining a frozen pre-candidate Parent oracle and independent blinded review.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`.
- Why not AGENTS.md: this is an unexecuted experimental protocol, not universal framework grammar.
- Why not local notes: V1/V2 failure boundaries and any successor acceptance contract require shared reviewable project evidence.
- Confirmation: user-confirmed direction — `V3 설계`; V3 execution approval is still pending.
- Layer completeness: no SDD/TDD/ADR/DDD/BDD/SSOT source delta until V3 execution is separately approved and produces an integration-worthy contract; no graph edge is added.
- Execution approval: user-confirmed — implement and run only the two unseen disposable V3 non-counting preflight arms. Even if both pass, no counted real-work case starts without another explicit approval.

### V3 non-counting preflight — failed on arm 1 and stopped

- The Parent oracle and its shifted-range/hash/EOF negative fixtures passed before launch.
- The `candidate-map` packet passed payload admission as `proposal-ready` at 5,320 compact characters.
- Transport/capture passed: Luna High, bridge off, exact probe order, one map/read/hash per each of three nodes, 13 of 14 calls, and successful final `structured_output`.
- Mechanical provenance failed: candidate record R2 declared `L164-L174` for `.lazy-harness/ssot/rule-sources.md`, whose frozen body has 173 lines. Q2 directly referenced that invalid range index.
- The semantic Parent/independent audits were not run because the deterministic path/hash/range gate failed first.
- Project preservation passed over the declared HEAD/status/diff/625-row inventory surface.
- Per the approved immediate-stop rule, the distinct `claim-evidence` arm was never prepared or launched beyond its pre-candidate oracle draft; it cannot run under V3.
- V3 verdict: **NOT PROVEN** with zero counted cases. The candidate is frozen and cannot be repaired, retried, or relabeled.
- Evidence: `/home/lazydino/.local/share/lazy-harness-proofs/record-reader-real-work-shadow-v3-20260825`.
- Discovery candidate: bridge-off structured transport now passed in both V2 and V3, but exact model-authored provenance remains unreliable under the fixed 14-call contract. Any future protocol would need a separately approved provenance mechanism, such as Parent-bound line-count metadata, without editing candidate output after capture.
- Layer completeness: Planning remains the sole owner of this unintegrated experiment result; no SDD/TDD/ADR/DDD/BDD/SSOT or graph mutation is authorized.
- Next action requires a user decision: end Reader shadowing, perform methodology analysis only, or design another protocol version without reusing V1/V2/V3 candidates.

### Final user decision — Reader shadow stopped

- Confirmation: user-confirmed — `Reader shadow 중단`. No V4 design, methodology follow-up, candidate, or counted collection is authorized.
- Final bounded result: V1 had one counted first-attempt failure and zero passes; V2 and V3 failed non-counting preflight before any counted case. Exact provenance and semantic Reader quality remain **NOT PROVEN**.
- Transport-only evidence is narrower: bridge-off Luna High structured capture passed in V2 and V3. It does not override the provenance/semantic failures or authorize integration.
- Final evidence: `/home/lazydino/.local/share/lazy-harness-proofs/record-reader-real-work-shadow-v3-20260825/FINAL-VERDICT.json` (`sha256:4322fca9f1345ca7463f78cf8660fe967f0575cdfff47ae1b7f46bbbed902f14`).
- Task #104 is cancelled after a negative validation outcome rather than marked successful. Task #108 is the pending proof gate. Task #103 remains blocked by #108.
- Reader integration, delegated-evidence permit, persistent Reader model default, automatic retry, Writer, Record Integrator, queue/daemon, canonical mutation, merge/release, and the deferred 37-row graph migration remain unauthorized.
- A future restart requires a new explicit user request, a new protocol version, unseen evidence, exact provenance, and clean independent semantic/methodology review.

#### Final rule placement

- Rule: terminate the current Reader-quality shadow series and retain NOT PROVEN as the integration gate.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`.
- Why not AGENTS.md: this is a bounded experiment verdict, not universal framework grammar.
- Why not local notes: the no-go boundary must remain shared project evidence for later integration decisions.
- Confirmation: user-confirmed.
- Discovery capture: Planning updated; no independent DDD/SDD/BDD/TDD/ADR/SSOT or graph delta because no Reader/runtime implementation was integrated.

### Quality-preservation objective restored — user correction

The user clarified that the target was misunderstood in the preceding reassessment. **Accuracy does not need to exceed the existing Direct Parent workflow.** The intended experiment remains the objective already stated at the top of this record: reach the same quality bar faster and/or with lower Parent-context, token, or cost pressure.

The correct gate is:

1. Direct Parent map-first retrieval and semantic output define the baseline quality bar.
2. A delegated treatment may use the same map and reading rules; delegation is an execution/context-sharding treatment, not a new retrieval algorithm.
3. The delegated result must first be quality-equivalent under the same oracle/fidelity criteria.
4. Only after equivalence passes may wall-clock, Parent context, token use, or cost determine whether delegation is beneficial.
5. No accuracy increase over the Direct Parent baseline is required.

The prior `Reliability-first reassessment`, replacement-method options, and deterministic evidence-ledger recommendation were based on a Parent misunderstanding and are withdrawn. No map redesign, Parent-only replacement direction, or new evidence-ledger architecture is selected or approved by this correction.

V1–V3 remain immutable failed evidence and the Reader shadow remains stopped. Their result means the frozen Reader candidates/protocols did not prove baseline-equivalent quality; it does **not** change the experiment's objective or establish that the existing map-first baseline needs greater accuracy. Task #108 continues to gate any fresh, explicitly approved attempt to re-prove equivalence before integration.

#### Corrected rule placement

- Rule: orchestration may optimize performance/context/cost only while preserving the existing Direct Parent quality bar; it does not need to improve that bar.
- Scope: framework-global architecture objective plus transient pilot interpretation.
- Primary durable record: `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md`.
- Planning record: this section corrects the misinterpreted objective and retains the frozen V1–V3 no-go evidence.
- Why not AGENTS.md: no new universal workflow or runtime behavior is approved.
- Why not local notes: the experiment objective and integration gate are shared project knowledge.
- Confirmation: user-confirmed.
- Layer completeness: ADR and Planning corrected. No independent DDD/SDD/BDD/TDD/SSOT/source/graph delta because no runtime contract or implementation changed.

No new Reader run, protocol, replacement method, integration, or implementation is authorized by this clarification.

### Model-attribution restart request — requirements gate

The user explicitly requested another bounded test and raised the possibility that the prior Reader failures were model-dependent. This reopens requirements/design for a fresh protocol version; it does not repair, rerun, relabel, or reuse V1–V3.

The hypothesis is plausible but unproven: V1 mixed a hard call-budget/transport failure with provenance defects, V2 exposed both an over-constrained oracle-overlap method and real semantic evidence-index defects, and V3 failed on one model-authored EOF-invalid range. None isolates model choice as the sole variable.

Three bounded designs remain materially different:

1. **Controlled two-arm model attribution (Recommended):** freeze one unseen Parent oracle and run the identical Reader packet, context, tool budget, output limits, no-fallback/no-retry rule, and admission/audit path once with the prior `openai-codex/gpt-5.6-luna:high` route and once with the current Direct Parent route `openai-codex/gpt-5.6-sol:max`. Only the model route varies.
2. **Practical same-model quality preflight:** run only `openai-codex/gpt-5.6-sol:max` and relax the prior tight call budget enough to complete. This tests whether quality equivalence is attainable but cannot distinguish model from budget/protocol effects.
3. **Three-arm attribution:** compare Luna High, Sol Medium, and Sol Max under identical constraints. This gives a reasoning/model gradient but costs more and still begins with one non-counting unseen case.

All designs use a disposable harness, frozen pre-candidate Parent baseline, immutable arm outputs, project read-only preservation, deterministic mechanical checks, and blinded independent semantic review. The current main checkout contains no integrated Record Reader profile or admission source, and no test result can authorize integration without a later explicit gate.

#### Restart rule placement

- Rule: a new Reader proof may test model attribution while preserving the Direct Parent quality-equivalence objective and immutable V1–V3 failures.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`.
- Why not AGENTS.md or SDD/TDD: the exact experimental arm is not yet selected and no runtime contract/source has changed.
- Confirmation: user-confirmed restart request; exact arm/protocol execution awaits the option gate because the candidate designs answer different questions.
- Layer completeness: Planning only; no independent DDD/SDD/BDD/TDD/ADR/SSOT/source/graph delta.

No candidate launches until the user selects the attribution design.

#### User-selected execution — Luna High versus Sol Medium

The user explicitly excluded Sol Max and confirmed that the target Reader routes are Sol Medium or Luna High. The approved preflight is therefore one controlled two-arm comparison:

- arm A: `openai-codex/gpt-5.6-luna:high`;
- arm B: `openai-codex/gpt-5.6-sol:medium`;
- one fresh unseen non-counting objective and one Parent oracle frozen before either arm;
- identical Reader role, semantic objective/facets/inventory/nodes, allowed records, context mode, tool/output budgets, no fallback, no retry, transport capture, mechanical admission, preservation checks, and blinded semantic review;
- each arm's envelope `modelRoute`, derived contract digest, and schema digest differ only as required to bind the actually executed route; the execution model is the sole treatment variable.

Sol Max is outside this experiment. A pass is bounded evidence for the passing model on this unseen preflight only; it does not erase V1–V3, prove the full ten-case gate, or authorize production integration. A failed arm remains frozen and stops any broader suite pending another user decision.

- Confirmation: user-confirmed model constraint and execution choice in response to the native model-test gate.
- Layer completeness: Planning only; the disposable proof harness and external evidence root are non-canonical until a separately approved integration contract exists.

### V4 model-attribution preflight — completed, strict FAIL

The approved unseen non-counting comparison used one frozen Parent oracle and identical semantic task, records, budgets, output limits, bridge-off fresh transport, no fallback, no automatic retry, mechanical gates, and Parent plus blinded independent semantic audits. Route-bound envelope/digest fields differed only for the executed model.

- Evidence root: `/home/lazydino/.local/share/lazy-harness-proofs/record-reader-model-attribution-v4-20260825`.
- Parent oracle admission passed before either arm (`sha256:f6493f8fb6f8964dc72901850016b072b38d1d7ec4487e4b3881758cab3627a5`).
- One Luna launcher was killed before any transport/child session existed; it is retained as launcher-only evidence and was replaced without creating or relabeling a candidate.
- **Luna High strict FAIL:** 14 calls, two non-identical successful `structured_output` calls, and therefore an in-session replacement/retry. Attempt 1 had valid ranges but failed payload admission; the selected final attempt passed payload admission at 5,006 characters but declared `R3[2] L248-L266` for a 263-line record. Parent and blinded independent audits also agreed that oracle A4's cache-fallback behavior was missing. Candidate `sha256:cb7590efcef829b118bb43a1beed6cb8bfdcae49d911774f1548da91f550d18b`.
- **Sol Medium strict FAIL but stronger candidate:** 13 calls and one structured output; payload admission, exact range integrity, project preservation, and Parent plus blinded independent semantic audits all passed. The frozen V3-derived transport whitelist rejected three exact allowed-record `nl -ba` reads. No out-of-scope read or project-safety breach was observed, but the frozen arm remains failed. Candidate `sha256:be563960795eb26c3a7fd99034b995708e8ec0c8e0f77fdd319a55402319b77c`.
- Diagnostic metrics: Luna High `187.185s`, 14 tools, 166,660 reported total tokens, `$0.02990372`; Sol Medium `71.437s`, 13 tools, 290,143 reported total tokens, `$0.44333`. This one case is not a performance ranking.
- Independent methodology review verdict: **FAIL / BLOCK**. The strict neither-passed verdict is correct; the Sol result is only a bounded association because the model-selected numbered-read strategy confounds clean model-only causality, and Luna violated the one-shot methodology.

Bounded conclusion: Sol Medium is the stronger next candidate for output quality on this one case, but neither arm passed the complete frozen contract. This does not prove model-only superiority, general model ranking, the ten-case Reader quality gate, or integration readiness. V1–V4 remain immutable; Task #108 remains the proof gate.

Final proof hashes:

- verdict `sha256:d2881b62eb6b8066c906457f1d741cf63c18cfd145fb0e1e7f389e9e635028c0`;
- attestation `sha256:0d237bcab9dd173b6a367d622a1212f0f1c1a90861aca8a6363b7d49dd0b668c`;
- 218-row manifest `sha256:0718428619556ef8b186baa07ec2b2b8384359c5f48e138049aa233c957ce9c4`.

#### V4 rule placement

- Rule: model-attribution evidence may rank a future candidate only after preserving strict frozen failures and separating semantic/range results from transport-method compliance.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`.
- Why not SDD/TDD yet: an exact numbered-read mechanism is a confirmed future contract/fixture candidate, but V4 failed and no runtime integration or contract change is approved.
- Confirmation: user-confirmed execution; result-derived interpretation is Parent-verified plus independently reviewed.
- Layer completeness: Planning updated. No independent DDD/SDD/BDD/TDD/ADR/SSOT/source/graph delta because the Reader remains disposable and unintegrated.

No V5, counted suite, Reader integration, delegated-evidence permit, Writer, queue/daemon, merge/release, or deferred 37-row graph migration is authorized without a new user decision.

### V5 selected — uniform exact numbered-read A/B

The user selected the recommended follow-up after V4: one new unseen non-counting Luna High versus Sol Medium comparison with the read strategy fixed identically across both arms.

Approved constraints:

- V1–V4 remain immutable and are never repaired, rerun, or relabeled;
- one objective and canonical record set not used by the V4 validation-cadence case;
- both arms must use exactly `nl -ba -- <allowed-record-path>` once per supplied record and must not use the `read` tool for record bodies;
- the exact numbered-read commands are preauthorized only for supplied canonical record paths and remain read-only;
- identical semantic packet, root/revision/snapshot, 14-call ceiling, 6,000/12,000-character limits, bridge-off fresh context, no fallback, no automatic retry, and exactly one final `structured_output`;
- arm A `openai-codex/gpt-5.6-luna:high`; arm B `openai-codex/gpt-5.6-sol:medium`;
- deterministic payload/transport/range/preservation checks plus Parent and blinded cross-model semantic audits;
- any arm failure remains frozen, but both approved arms complete so the model comparison is available.

This V5 selection authorizes only the disposable two-arm preflight and its audits. It does not authorize counted cases, Reader integration, a permanent model default, delegated read-debt evidence, Writer, queue/daemon, merge/release, or the 37-row graph migration.

- Confirmation: user-selected `동일 줄번호 A/B (Recommended)`.
- Layer completeness: Planning only; no SDD/TDD/ADR/DDD/BDD/SSOT/source/graph delta unless a later result earns a separately approved contract change.

### V5 uniform numbered-read result — `SOL_MEDIUM_ONLY_PASS`

V5 used a new runtime-decommission objective and record set, a prevalidated six-atom Parent oracle, and the identical mandatory `nl -ba -- <allowed-record-path>` strategy for both models. Both arms ran exactly 13 calls—three identity probes, three maps, three numbered reads, three hashes, and one structured output—with identical budgets, bridge-off fresh context, no fallback/retry, and unchanged project boundaries.

- Evidence root: `/home/lazydino/.local/share/lazy-harness-proofs/record-reader-uniform-numbered-v5-20260825`.
- Parent oracle admission passed before either arm (`sha256:99bfac09966ea3d1e05cbdcf436e65f2d09640c1d855dbfe9af7a219b38fa1bc`).
- **Luna High:** all mechanical gates passed—one structured output, payload admission, exact call sequence, ranges, hashes, and project preservation. Parent and blinded Sol Medium reviewer agreed on semantic **FAIL**: Q3 only partially grounded distribution-aware audit preservation because it omitted the only range explicitly naming it; Q5 only partially grounded cross-layer completion because it omitted the explicit layer-completeness matrix. Candidate `sha256:77f99d96ae87a7da9a0fd32b129fee7b09856f5d7300d0a2dcbb669dcc342a55`.
- **Sol Medium:** complete frozen V5 **PASS**. Payload, exact transport sequence, range integrity, project preservation, Parent semantic audit, blinded Luna High semantic audit, and agreement all passed. Candidate `sha256:0863fae16b89139a684e7f5249aca6ca59590385515c4761757d87611ca7ac95`.
- Diagnostic metrics: Luna High `91.464s`, 13 tools, 193,190 reported total tokens, `$0.01668056`; Sol Medium `75.111s`, 13 tools, 296,553 reported total tokens, `$0.458423`. This one preflight is not a general performance or cost ranking.
- Independent methodology review: **PASS**, no P0/P1/P2 findings. It confirmed a distinct unseen case, uniform treatment, valid oracle, one-shot/no-retry behavior, unchanged candidates, preservation, and `SOL_MEDIUM_ONLY_PASS` as the narrowest defensible conclusion.

Bounded conclusion: Sol Medium has now preserved the Direct Parent quality bar under the complete frozen Reader contract for one unseen non-counting preflight with the strategy confound removed. Luna High did not. This is real candidate-selection evidence, but it does not prove a general model ranking, the ten-case quality gate, or integration readiness. Task #108 remains pending.

Final proof hashes:

- verdict `sha256:b78c90c634e850cbc11613b7382d42f03b45705cc801f37f6cf5b923f5e8113f`;
- attestation `sha256:14d0110099fb6142e20c87b8b99425a0a697012bb7cfea5fecec8f47a4012bd7`;
- 202-row manifest `sha256:1e573939a9c083d61a244d3588c9d4329a9120efa96d16f40817b2af28feedb9`.

#### V5 rule placement

- Rule: under a uniform exact numbered-read protocol, Sol Medium is the only target model that passed this unseen preflight; model promotion still requires the separately approved real-work quality suite.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`.
- Why not SDD/TDD yet: V5 validates a disposable protocol/candidate, not an integrated Reader contract. The numbered-read mechanism and fixtures become SDD/TDD candidates only if the user approves the broader proof/integration path.
- Confirmation: user-selected V5 execution; candidate and methodology outcomes are Parent-verified and independently reviewed.
- Layer completeness: Planning updated. No independent DDD/SDD/BDD/TDD/ADR/SSOT/source/graph delta because no Reader runtime integration or canonical contract changed.

No ten-case suite, Reader integration, permanent model default, delegated-evidence permit, Writer, queue/daemon, merge/release, or deferred 37-row graph migration is authorized without a new user decision.

### V6 selected — Sol Medium `claim-evidence` preflight

The user selected `claim-evidence 1건 (Recommended)` after V5. V6 is one new unseen non-counting Sol Medium arm for the Reader mode that has never completed a real-work quality preflight.

Approved constraints:

- V1–V5 remain immutable; no prior candidate, objective, or record set is reused;
- Sol Medium only: `openai-codex/gpt-5.6-sol:medium`;
- a Parent-approved candidate map and bundle freeze Q/F/N/dependency/shared-owner scope before launch;
- the unseen objective covers complete lean discovery, targeted loading, concrete map traversal, map-cue versus direct-read proof, search/read debt, and invalid free-form/fallback retrieval;
- exact supplied nodes: ADR 0049, the Map-First Retrieval SDD, and the Search/Read Debt SDD;
- mandatory `nl -ba -- <allowed-record-path>` once per record, exact 13-call plan under the 14-call ceiling, one final structured output, bridge off, fresh context, no fallback, no retry, and project read-only;
- deterministic payload/transport/range/preservation checks plus Parent and blinded independent semantic audits;
- any failure freezes V6 and returns to the user before a counted suite.

This selection authorizes only V6 and its audits. It does not authorize the ten-case suite, integration, a permanent model default, delegated read-debt evidence, Writer, queue/daemon, merge/release, or graph migration.

- Confirmation: user-selected `claim-evidence 1건 (Recommended)`.
- Layer completeness: Planning only; no SDD/TDD/ADR/DDD/BDD/SSOT/source/graph delta unless a later result earns a separately approved contract change.

### V6 Sol Medium `claim-evidence` result — FAIL

V6 used a new map-first retrieval objective, a Parent-approved Q1–Q3/F1–F3/B1 candidate map, a prevalidated eight-atom oracle, the V5 exact numbered-read method, and one fresh bridge-off Sol Medium run with no fallback/retry.

- Evidence root: `/home/lazydino/.local/share/lazy-harness-proofs/record-reader-claim-evidence-v6-20260826`.
- Parent oracle admission passed before launch (`sha256:700b6ad3e5825ed37ef4fd1cb6f5408fa01b7b133b35782a064de1eca8f58cca`).
- Reader transport passed: exact 13-call sequence, one structured output, correct Sol Medium route, bridge off, no forbidden access, and project preservation.
- Payload admission reported `complete`, but strict range integrity failed. All nine range strings used bare `Lx-Ly` values instead of the required `Lx-Ly: description` form; dependent claim evidence indexes consequently failed. Candidate `sha256:f637d8e43d6a102777ce35cf9025da1062e1b0c4890dab882f1d74daf9f689d6`.
- This exposed a confirmed admission-layer gap: `record-reader-admission/v2` accepted non-empty bare range strings in claim-evidence mode, while the role contract, overlay, and downstream range gate require the descriptive format. The downstream gate correctly blocked the candidate.
- Parent and the final valid blinded independent audit agreed on semantic **FAIL**. C1–C5 are individually supported and correctly scoped, but A2 and A4–A8 details are missing: explicit policy boundary, complete-index field contract, first-grounding/raw-classifier boundary, visible reuse/fresh-packet behavior, and steer non-classification. Therefore `status=complete` and empty gaps are not semantically justified.
- Independent-review transport wrote two zero-byte supervisor output files despite successful structured-output calls. Exact arguments were recovered with hashes and receipts; the first recovered audit was retained as validator-invalid due synthetic `candidate-metadata` ownership, and a fresh replacement audit validated. The Reader candidate/oracle were never changed.
- Diagnostic metrics: `74.412s`, 13 tools, 280,807 reported total tokens, `$0.464415`.
- Independent methodology review: **FAIL**, confirming two P1 classes—bare-range admission and semantic `complete` overclaim—while accepting the audit-output recovery, reviewer replacement disclosure, and immutable candidate/oracle evidence.

Bounded conclusion: V6 is a validly recorded failed non-counting preflight. V5 still proves one Sol Medium candidate-map preflight, but Sol Medium claim-evidence quality is not proven; the ten-case suite must not start. Task #108 remains pending.

Final proof hashes:

- verdict `sha256:1512c37f5241e9e35026925a035f0c579a04cd172cad70a2502897206311029e`;
- attestation `sha256:b89c72a374c2889268dba8dac0550a80eef645876b9f72ac92b857566689467d`;
- 144-row manifest `sha256:3e997c14008966fb00fbde2b168efc2179c764c8b2503049e8f37ce80b57098f`.

#### V6 rule placement

- Rule: claim-evidence promotion requires strict descriptive ranges and semantic completeness beyond individually supported claims; payload admission alone cannot justify `complete`.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`.
- Why not SDD/TDD yet: the failed disposable proof confirms future contract/fixture candidates for claim-mode range-pattern admission and `complete` semantic coverage, but no source/runtime contract change is approved.
- Confirmation: user-selected V6 execution; result is Parent-verified and independently reviewed.
- Layer completeness: Planning updated. No independent DDD/BDD/ADR/SSOT/source/graph delta; SDD/TDD remain candidates pending a new user decision.

No retry, V7, ten-case suite, Reader integration, permanent model default, delegated-evidence permit, Writer, queue/daemon, merge/release, or deferred 37-row graph migration is authorized without a new user decision.

### V7 selected — corrected disposable `claim-evidence` preflight

The user selected `V7 수정 preflight (Recommended)` after V6. V7 remains disposable and uses one entirely new unseen Sol Medium claim-evidence objective.

Approved corrections and boundaries:

- preserve immutable V1–V6 candidates and evidence; no V6 repair, retry, or relabel;
- patch only the V7 generated structured-output schema so every record range must match `L<start>-L<end>: <description>` before the internal structured-output tool can accept it;
- freeze a Parent-approved atomic checklist and require every checklist id to appear in the correct Q/F-scoped claims; deterministic atom-coverage admission runs before semantic review;
- use a new record-writing/layer-completeness objective and record set distinct from V4–V6;
- Sol Medium only, exact numbered reads, 13-call plan, one structured output, bridge off, fresh context, no fallback/retry, and project read-only;
- original payload admission, patched-schema receipt, strict range gate, atom coverage, Parent audit, blinded independent audit, and methodology review must all pass;
- any failure freezes V7 and returns to the user before a ten-case suite.

V7 authorizes no source/runtime integration or canonical Reader contract change. It does not authorize the ten-case suite, permanent model default, delegated read-debt evidence, Writer, queue/daemon, merge/release, or graph migration.

- Confirmation: user-selected `V7 수정 preflight (Recommended)`.
- Layer completeness: Planning only; SDD/TDD remain future candidates until a successful disposable result and a separate implementation decision.

### V7 corrected Sol Medium `claim-evidence` result — PASS

V7 used a new record-completion/layer-completeness objective and record set, a prevalidated ten-atom oracle, Parent-approved PA1–PA10/Q1–Q3/F1–F3/B1 scope, and the V5 numbered-read transport.

- Evidence root: `/home/lazydino/.local/share/lazy-harness-proofs/record-reader-claim-evidence-v7-20260826`.
- Parent oracle admission passed before launch (`sha256:3ca17545d8b1af8fec1edcb8fb52bf0f606fbf7bcab286972d6c69a3118ae81a`).
- The disposable structured-output schema changed only `records[].ranges[]` to require `L<start>-L<end>: <description>`. Positive/negative fixtures proved descriptive ranges pass and V6-style bare ranges fail.
- Parent atom coverage fixtures proved all PA1–PA10 ids and Q/F ownership are required; labels explicitly did not claim semantic support.
- Sol Medium passed every mechanical gate: exact 13-call transport, one structured output, original payload admission, patched-schema receipt, strict range integrity, PA1–PA10 coverage, and project preservation. Candidate `sha256:c11ebc0966f39e3d9dc617f48875cca64f2bda75ef351d523e0017553b0b6703`.
- Parent and blinded Luna High audits independently passed: all A1–A10 were represented, all C1–C4/PA1–PA10 semantics were supported by attached descriptive ranges, complete status was justified, and Parent authority was preserved.
- Diagnostic metrics: `83.641s`, 13 tools, 323,713 reported total tokens, `$0.471898`.
- Independent methodology review: **PASS**, no P0/P1 findings and no P2 affecting the verdict. It confirmed a fresh case, target-only schema patch, fixture behavior, atom coverage without semantic substitution, one-shot transport, preservation, unchanged candidate/oracle, and V7 PASS as the narrowest conclusion.

Bounded conclusion: Sol Medium has now passed one unseen non-counting preflight in each Reader mode—V5 `candidate-map` and V7 corrected `claim-evidence`. This establishes a viable candidate and disposable contract shape, but it does not prove the ten-case real-work quality gate, a general model ranking, or production integration. Task #108 remains pending.

Final proof hashes:

- verdict `sha256:e6dd7ad04da8a2ab33a3f7cfbb75c810391aae69e6d97892a0990dadfdf4123d`;
- attestation `sha256:e7605e4e84a4b9988e1c1f4b6b659889de4085be2b3716c38a2008429539d370`;
- 157-row manifest `sha256:4131c5ca2c0b0ef258d9a4ac4af14ccb2689c7137fb357c5fe1a21e1a7e8c1a4`.

#### V7 rule placement

- Rule: claim-evidence quality requires schema-enforced descriptive ranges, deterministic Parent atom coverage, and independent semantic proof; Sol Medium passed this disposable shape once.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`.
- Why not SDD/TDD yet: V7 proves a disposable contract candidate. Production range-schema and atom-coverage integration still require a separate source contract/TDD decision.
- Confirmation: user-selected V7; result is Parent-verified and independently reviewed.
- Layer completeness: Planning updated. No independent DDD/BDD/ADR/SSOT/source/graph delta; SDD/TDD remain implementation candidates.

No ten-case suite, source integration, permanent model default, delegated-evidence permit, Writer, queue/daemon, merge/release, or deferred 37-row graph migration is authorized without a new user decision.

### V8 selected — Sol Medium ten-case real-work quality gate

The user selected `10건 품질 게이트 (Recommended)` after V5/V7 passed one unseen non-counting preflight in each Reader mode.

Approved suite boundary:

- exactly ten distinct unseen project work units, frozen in advance as five `candidate-map` and five `claim-evidence` cases;
- corrected V7 disposable range-schema and Parent-atom coverage gates apply to every case;
- each case freezes a fresh Parent oracle, objective, nodes, facets/inventory or approved Q/F/bundle scope, root/revision/snapshot, and negative boundaries before its candidate launches;
- Sol Medium only, fresh context, bridge off, exact numbered reads, one structured output, no fallback, no retry, project read-only;
- each candidate receives original payload admission, patched-schema, strict range, atom coverage, transport, preservation, Parent semantic, blinded independent semantic, and agreement checks;
- cases run sequentially; the first failed preflight/counted case freezes V8 as NOT PROVEN and prevents later cases from restoring it;
- same-candidate remediation, prior-case reuse, synthetic filler, and relabeling do not count;
- even ten passes authorize only a separate integration proposal, never automatic Reader integration or model-default promotion.

Frozen work-unit catalog: project-command boundary, architecture guidance, policy machinery, Project Profile V2, implementation-map storage, evidence capsules, external-context policy, memory-device storage, runtime shared state, and record-decision broker. Exact record sets and case modes live in the V8 protocol artifact.

- Confirmation: user-selected `10건 품질 게이트 (Recommended)`.
- Layer completeness: Planning only while the suite remains disposable; no SDD/TDD/source delta until a later integration decision.

### V8 ten-case gate — stopped at case 01, NOT PROVEN

V8 froze ten distinct work units and started sequential execution with the corrected range-schema and Parent-atom gates. Case 01 used the project-command boundary `candidate-map` objective.

- Evidence root: `/home/lazydino/.local/share/lazy-harness-proofs/record-reader-quality-suite-v8-20260826`.
- Case 01 oracle admission passed before launch (`sha256:30dd38c0a848a3241964bc2467e1f7d0ef31bcc5159e35e5fa1fb155787ec0d1`).
- Sol Medium passed payload admission, patched descriptive-range schema, strict ranges, exact ten-call transport, one structured output, and project preservation. Candidate `sha256:6510b86a9e630a656df2c693eee0635560dc364ec62d2628089579f67c306d69`.
- The candidate used visible `PA1:` through `PA6:` labels, covered every F1–F4/I1–I4 input, and Parent plus blinded independent audits both passed all PA1–PA6/A1–A6 semantics, proposal-ready state, intended I3 overlap, and authority boundary.
- The frozen `atom_coverage_v8.py` checker nevertheless recognized only bracket syntax `[PA1]`. Neither the protocol, case objective, semantic task, Parent map, nor work packet required brackets; they required PA labels. The checker therefore reported all six labels missing despite candidate compliance.
- Independent methodology review: **FAIL / NOT PROVEN**. It classified the bracket-only matcher as an uncommunicated P1 overconstraint, confirmed semantic PASS, and required case 01 to remain a frozen strict protocol failure because post-candidate validator correction/remediation is forbidden.
- Per the immediate stop rule, case 01 is counted as strict FAIL and cases 02–10 remain NOT RUN. No later result can restore V8.

Bounded conclusion: V8 does not show a Sol Medium semantic-quality regression; it shows a pre-candidate suite-validator defect. Reliability policy still forbids relabeling the case, correcting the checker against the frozen output, or continuing the suite. The ten-case quality gate remains NOT PROVEN and Task #108 remains pending.

Final proof hashes:

- verdict `sha256:ce5514ada039cf2e02db9550d73a91153f85b688a94b59419fac1a007ec28154`;
- attestation `sha256:8a2e2abc0af0753f8de55a9358edd762cb9fd054532ce25f72c757738b78ad4c`;
- 144-row manifest `sha256:e44a98dd5a363f6927e079193dcc8b706e2f7d7314873268b956bb7a451d986f`.

#### V8 rule placement

- Rule: a counted suite case cannot be relabeled after an uncommunicated validator overconstraint; semantic PASS is retained separately from strict protocol FAIL.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`.
- Why not SDD/TDD yet: V8 exposes a future atom-label contract/fixture candidate, but no source/runtime integration or validator correction is approved.
- Confirmation: user-selected ten-case suite; outcome is Parent-verified and independently reviewed.
- Layer completeness: Planning updated. No independent DDD/BDD/ADR/SSOT/source/graph delta; SDD/TDD remain candidates pending a new decision.

No V8 rerun, V9, cases 02–10, source integration, permanent model default, delegated-evidence permit, Writer, queue/daemon, merge/release, or deferred 37-row graph migration is authorized without a new user decision.

### Experiment contract implementation selected

The user selected `실험 계약 구현 (Recommended)` after V8 demonstrated that repeated disposable checker drift—not Sol Medium semantic quality—was blocking the suite.

Approved implementation scope:

- target existing worktree/branch `/tmp/lazy-harness-record-reader-thin-profile` / `experiment/record-reader-thin-profile`;
- update the experiment `record-reader/v2` role and `record-reader-admission/v2` implementation so descriptive range syntax and atom-id syntax/ownership are explicit, schema-enforced, and consistently admitted;
- replace ad-hoc PA text parsing with an unambiguous contract field or equally explicit pre-candidate grammar that both prompt and validator share;
- add positive/negative regressions for range syntax, atom coverage, Q/F ownership, unknown/missing atoms, and success-state consistency;
- preserve label presence as mechanical coverage only; semantic support remains Parent plus independent review;
- run focused and standard experiment validation plus independent review;
- do not modify or relabel V1–V8 evidence, integrate into main, set a permanent model default, or launch another quality suite.

- Confirmation: user-selected `실험 계약 구현 (Recommended)`.
- Layer completeness: experiment SDD/TDD/source updates are authorized in the experiment branch; main remains Planning-only until a later integration decision.

#### Discovery capture — experiment contract implementation

- DDD: none — no domain term, entity, or business invariant changes.
- SDD: candidate/authorized in the experiment branch — `record-reader/v2` and `record-reader-admission/v2` will define descriptive-range and explicit atom-id/Q-F ownership contracts; main SDD remains unchanged until integration approval.
- BDD: none — no product-visible or agent-user interaction flow changes in this implementation slice.
- TDD: candidate/authorized in the experiment branch — positive/negative fixtures will cover range syntax, missing/unknown atoms, Q/F ownership, success-state consistency, and mechanical-versus-semantic boundaries.
- ADR: none — ADR 0055 Parent authority, read-debt ownership, and integration gates remain unchanged.
- SSOT: none — no runtime owner, persistent model default, config path, schema authority in main, or supported-runtime status changes.
- Planning: updated — this record owns the user-confirmed experiment-only implementation scope, target worktree, validation/review requirements, and no-integration boundary.
- Graph: none — no confirmed main implementation edge exists; experiment graph updates, if any, require verified source symbols and stay on the experiment branch.

The experiment no longer depends on a manual session switch: the Parent launched direct Pi CLI dispatch `reader-contract-impl` in `/tmp/lazy-harness-record-reader-thin-profile`. The target CLI is the sole writer there and owns target-root grounding/implementation; the main worktree remains Planning/policy-only.

#### Correction capture — agent-owned CLI fallback

- Error: after `lazy_move_project` reported `ctx.switchSession` unavailable, the Parent incorrectly asked the user to run `/lazy-move` even though an approved target path and `interactive_shell` Pi CLI were available.
- User-confirmed correction: use the available CLI directly; do not offload a recoverable agent-context transition to the user.
- Applied action: initial dispatch `reader-contract-impl` was not active progress—it waited at the approved project-trust prompt for 19 minutes, then exited 1 because project/global extensions both registered `lazy_move_project`. The Parent accepted the approved target trust prompt, followed the CLI hint, and relaunched as `reader-contract-impl-ne` with `pi -ne`.
- Verified current state: `reader-contract-impl-ne` is running in `/tmp/lazy-harness-record-reader-thin-profile`; startup output shows target branch status inspection and `.lazy-harness/AGENTS.md` loading, so implementation has begun rather than merely holding a live process.
- Status-claim boundary: future supervision must observe a target-root action after trust/authentication/startup gates before calling a CLI task “in progress.”
- Durable behavior: `.lazy-harness/behavior/agent-owned-target-context-transition.md`; typed policy/capability id `agent-owned-target-context-transition`.
- Boundary: a manual user command remains valid only after an unapproved/unverified target, unavailable/failed CLI launch, or conflicting writer blocks the agent-owned path.

##### Rule placement

- Rule: an available agent-owned target-root CLI precedes manual user handoff after direct switching is unavailable.
- Scope: framework-global operating behavior.
- Primary record: `.lazy-harness/behavior/agent-owned-target-context-transition.md`.
- Why not local notes: this is reusable shared behavior, not a private shortcut.
- Confirmation: user-confirmed on 2026-08-26.

##### Discovery capture

- DDD: none — no domain semantics changed.
- SDD: updated — operating-rule resolution exposes preferred/discouraged target-transition actions.
- BDD: updated — the new behavior record owns the corrected user-facing flow.
- TDD: updated — rulebook regression records positive/negative resolution boundaries.
- ADR: updated — ADR 0055 captures Parent responsibility and rejects recoverable user offload.
- SSOT: updated — `policies.json` and `capabilities.json` store canonical semantics/action binding.
- Planning: updated — this section records the concrete error, correction, failed first dispatch, verified `pi -ne` retry, and experiment boundary.
- Follow-up layer judgement: BDD/TDD/Planning updated for the startup-supervision scenario; DDD/SDD/ADR/SSOT have no independent semantic delta beyond the already configured transition policy.

### Experiment contract independent review — FAIL pending remediation choice

Luna High read-only review `reader-contract-review-ne` completed after the extension-free retry. It found the core Reader contract structurally consistent but did not certify the worktree/slice.

Findings:

- **P1 — mixed dirty diff:** the nine approved paths contain 1,164 additions / 38 deletions, but `.lazy-harness/scripts/self-test.py`, `.lazy-harness/knowledge/graph.jsonl`, and the experiment Planning record also contain pre-existing Parent Work-Unit Trace/Truth Binding work that the Reader implementation preserved. The reviewer cannot certify the entire HEAD diff as Reader-only even though those unrelated changes predated this implementation.
- **P2 — negative fixture gaps:** admission enforces exact ownership closure, but fixtures do not test drift between two valid approved Q/F ids, multi-atom claim unions, or `false` values for all three mandatory semantic-boundary booleans.
- **P2 — evidence attribution:** the implementation ran focused checks and `lazy validate --plan standard` successfully after mutation, but the existing graph validation-evidence row predates the new atom/range delta. A current, bounded evidence record/row must replace any implication that the older row proves this change; no live Reader/model adherence was tested or authorized.

Passed by independent inspection: descriptive range schema/runtime alignment, Parent A* catalog, candidate and claim ownership closure, success-state closure, `semanticAuthorization=false`, mandatory Parent + independent semantic review, archived-v1 path retention, graph JSON/link closure, and no integration/model-default/live-suite permission.

Status: implementation exists and standard validation passed, but independent review verdict remains **FAIL**. No target mutation, relabeling, commit, push, integration, or live suite may proceed until the user chooses the remediation boundary.

#### Discovery capture — review findings

- DDD: none — no domain semantics changed.
- SDD: candidate — clarify evidence attribution and clean-slice certification only if the selected remediation changes contract records.
- BDD: none — no new user-visible flow beyond the already captured CLI supervision correction.
- TDD: candidate — add valid-ID Q/F drift, multi-atom union, and semantic-boundary-false negatives.
- ADR: none — Parent authority and no-integration decisions remain unchanged.
- SSOT: none — no runtime/model/config authority changed.
- Planning: updated — independent FAIL, exact findings, passed inspection surface, and pending remediation decision are recorded here.

The original mixed-worktree implementation remains preserved and will not be relabeled or used as the clean certification candidate.

### Clean Reader contract worktree selected

The user selected `Clean worktree (Recommended)` to resolve the independent review findings.

Approved remediation boundary:

- create `/tmp/lazy-harness-record-reader-contract-clean` on branch `experiment/record-reader-contract-v2` from frozen base `e6fd2abbad5a13e3c2f37a53160f2e862d8b69f2`;
- reimplement only the Reader atom/range contract against that clean base, without copying unrelated Parent Trace/Truth Binding changes;
- include the P2 missing regressions for drift between valid approved Q/F ids, multi-atom claim unions, and `false` values for all mandatory semantic-boundary booleans;
- write current validation/evidence attribution for this exact clean delta instead of relying on the older compact-contract graph row;
- run focused checks, one final standard validation, and a fresh independent read-only review;
- keep the original mixed worktree immutable as failed-review evidence;
- do not run a live Reader/suite, integrate into main, set a model default, commit, push, merge, release, or start the deferred graph migration.

#### Discovery capture — clean remediation

- DDD: none — no domain semantics change.
- SDD: candidate/authorized in the clean experiment branch — explicit ownership/range/admission contract only.
- BDD: none — no product-visible flow change.
- TDD: candidate/authorized — complete the exact negative fixture matrix identified by review.
- ADR: none — existing Parent authority and no-integration decisions remain unchanged.
- SSOT: none — no runtime/model/config authority changes.
- Planning: updated — exact path, branch, base, isolation, validation, review, and no-integration boundaries are user-confirmed.

The clean worktree is the sole writer target for remediation; the prior dirty experiment worktree remains read-only evidence.

### Clean Reader contract independent review — FAIL pending numeric-bound decision

Luna High review `reader-contract-clean-review` confirmed the clean isolation and the previously missing ownership/boundary fixtures, but found three new issues:

- **P1 — oversized reversed bounds:** `record-reader-admission.ts` compares parsed bounds with `Number(...)`; values above the safe-integer boundary can round together, so `L9007199254740993-L9007199254740992: reversed` is admitted.
- **P2 — schema/admission boundary wording:** the generated JSON Schema correctly enforces descriptive syntax only; arbitrary `start <= end` comparison is performed by admission. Current contract wording and TypeBox expectations imply schema-level relational rejection that standard regex schema cannot provide.
- **P2 — stale catalog examples:** `packages/lazy-harness-pi/README.md` and the experiment Planning summary still say `F/I/N/V`, omitting required Parent `A*` semantic atoms.

Independently passed: exact nine-file clean diff (282 insertions / 50 deletions), correct branch/base, no Parent Trace/Truth changes, atom/Q/F closure, valid-id drift negatives, multi-claim union negatives, all four semantic-boundary booleans, archived v1, current scoped graph evidence, and no live/integration/model-default permission.

Status remains **FAIL**. The clean implementation is frozen until the user selects the numeric-bound repair; no same-output relabeling or integration claim is allowed.

#### Discovery capture — clean review

- DDD: none.
- SDD: candidate — define either arbitrary-size integer admission ordering or an explicit bounded line-number contract; clarify schema-format versus admission-order ownership.
- BDD: none.
- TDD: candidate — add the oversized reversed-bound regression and align schema/admission expectations.
- ADR: none — no architecture trade-off changes unless a numeric ceiling is selected.
- SSOT: none.
- Planning: updated — clean review evidence, exact findings, passed surface, and pending numeric decision are recorded.

### BigInt range repair selected

The user selected `BigInt 비교 (Recommended)`. The clean branch will compare parsed range bounds as arbitrary-size integers, preserve schema ownership of descriptive syntax only, assign ordering to admission, add the oversized reversed-bound regression, and correct every `F/I/N/V` example to include `A`. No numeric ceiling is introduced.

- SDD: authorized — clarify schema-format versus admission-order ownership without changing the wire syntax.
- TDD: authorized — protect ordinary and oversized reversed ranges plus the schema/admission split.
- ADR/SSOT/DDD/BDD: no independent delta.
- Planning: updated — user-confirmed numeric strategy and repair scope recorded.
- Integration/live-suite/model-default/commit/push/release/graph-migration gates remain closed.

### Clean Reader contract final independent review — PASS

Luna High final review `reader-contract-bigint-review` passed the clean branch after direct admission probes.

Verified:

- branch `experiment/record-reader-contract-v2`, HEAD/merge-base `e6fd2abbad5a13e3c2f37a53160f2e862d8b69f2`;
- exactly nine approved unstaged files, zero staged/untracked files, and no Parent Trace/Truth or unrelated paths;
- ordinary reversed syntax is structurally accepted by the JSON Schema but rejected by admission, matching the documented schema-format/admission-order boundary;
- oversized reversed `L9007199254740993-L9007199254740992: reversed` is rejected by exact BigInt ordering; ordered oversized control is admitted;
- atom/Q/F closure, exact multi-claim union, valid-id ownership drift negatives, all four semantic-boundary booleans, Parent + independent semantic review requirement, archived-v1 compatibility, and static-only graph evidence;
- `git diff --check` passed and no live Reader/suite, integration, model default, commit, push, merge, promotion, or file mutation was performed by the reviewer.

Independent findings: P0 none, P1 none, P2 none. One non-blocking P3 remains: historical summaries at the experiment Planning line 255 and baseline ADR 0055 line 209 omit `A*`; current required examples at Planning line 55 and package README line 203 are correct. The ADR is outside the approved nine-file clean delta, so no post-review mutation was made.

Bounded conclusion: the **clean experiment contract implementation is mechanically certified PASS**. This does not prove live Sol Reader adherence, semantic fidelity on unseen work, delegated read-debt transfer, integration safety, or permanent model selection. Task #108 and every integration/live-suite gate remain pending.

#### Discovery capture — final clean review

- DDD: none.
- SDD: clean experiment contract implemented and independently passed; main integration remains unapproved.
- BDD: none.
- TDD: clean negative matrix implemented and independently passed; live model behavior remains untested.
- ADR: none — P3 baseline summary drift is retained as a non-blocking candidate because ADR mutation was outside the approved slice.
- SSOT: none.
- Planning: updated — final PASS, exact evidence boundary, P3 residual, and remaining gates are recorded.

### Clean contract freeze + two-mode live preflight selected

The user selected both recommended next steps:

1. create one **local-only commit** on `experiment/record-reader-contract-v2` containing exactly the independently passed nine-file delta; no push or PR;
2. after freezing that commit, run exactly two fresh unseen Sol Medium preflights: one `candidate-map` and one `claim-evidence`.

Preflight boundary:

- author and admit fresh Parent oracles before either Reader launch;
- use the committed clean contract, exact numbered reads, fresh contexts, bridge off, no fallback/retry, one structured output, project read-only, and independent semantic review;
- choose work units not used by V1–V8 and freeze both before case 01 launch;
- fail fast: the first failed case stops the two-case preflight;
- even two passes prove only initial live wire-contract adherence and permit a later full-quality-gate proposal; they do not prove Task #108, integration, model default, Writer, debt transfer, merge/release, or graph migration.

#### Discovery capture — selected preflight

- DDD: candidate only if a fresh oracle introduces a new project term; otherwise none.
- SDD: no new production contract delta; the committed clean experiment contract is the frozen test subject.
- BDD: none.
- TDD: Planning/proof-only disposable preflight; no production TDD promotion without a later integration decision.
- ADR: none.
- SSOT: none — no permanent model/default/config authority.
- Planning: updated — local commit, exact two-mode preflight, oracle-first/fail-fast/no-integration boundaries are user-confirmed.

### Clean contract locally frozen

Local-only commit `fe73a23262fc40b9bb49da02fd2d729f557428aa` (`feat: harden record reader v2 contract`) was created on `experiment/record-reader-contract-v2`. The commit contains exactly the independently passed nine files; worktree and index are clean. No push, amend, merge, tag, or config change occurred.

This commit is the immutable contract/revision subject for the selected two-mode preflight.

### Two-mode preflight frozen

External proof root `/home/lazydino/.local/share/lazy-harness-proofs/record-reader-clean-two-mode-preflight-20260826` is frozen at `FROZEN-NOT-EXECUTED` against clean commit `fe73a23262fc40b9bb49da02fd2d729f557428aa`. Both fresh cases, Parent oracles, structured atom maps, unchanged committed output schemas, exact tool protocols, pre-run fingerprints, and freeze receipts existed before any candidate launch.

- case 01 `clean-preflight-01-regression-registry` (`candidate-map`): oracle `sha256:1362b5e57162efb404babe8d583624e7c7452939fd3a7a7d38fcba01786030de`; contract digest `sha256:5d5a348227d63804038fc1687a9f55e88936050201acfc4b56143958825a4297`; freeze `sha256:310a246535cb69386b6dbecfb82401bda116cafc19d093802dc3ed4a51551a9f`.
- case 02 `clean-preflight-02-prompt-budget` (`claim-evidence`): oracle `sha256:c4499c51e7a70727b5c2d1467fae13c7cd0014b19b3b8b5ad02a4c4731239a1f`; contract digest `sha256:94b5c395ab541ffebe0c7da9a534704a2b200f70790a5aba00ce9bb9ad165986`; freeze `sha256:85535b5936b77df515145eedee4f815f2b2ece7493d69224d3a6fa78181d0bff`.
- committed contract source digest: `sha256:8b2420ba9e14c6e146e0bfb25b91a25f58b44c134482715af8e83756d771b3cf`.
- frozen 82-file manifest digest: `sha256:a1f2c3f2e3818d8038314fb6fd2defa145e4d2e097dad7144ef865b6caa93ac7`.
- independent Parent verification confirmed the manifest, both oracle validators, launch guard, exact subject HEAD/cleanliness, and absence of sentinel, candidate/session/transport output, or verdict.

The user’s existing execution approval permitted the separate top-level sentinel and case 01 launch. Fail-fast remained mandatory: case 02 could run only if case 01 passed mechanical admission, Parent semantic review, independent blinded semantic review, agreement, and finalization.

### Two-mode live preflight closed — failed-fast

The preflight is `CLOSED-FAILED-FAIL-FAST`. The clean subject commit and project were preserved; no candidate repair or verdict relabeling occurred.

Case 01 `clean-preflight-01-regression-registry`:

- execution-approval sentinel: `sha256:d8a03612de87da43a7055a1983738a9b899b7a42ecd1bf439681a0b4838ede96`;
- immutable candidate: `sha256:adad39b0cc03226c76a413d52dfa0093fe45ef4ed6be39919fc19e86b873408b`;
- capture, structured atom exact-once closure, arbitrary-size range/source-line integrity, and project preservation passed;
- committed deterministic admission failed: the broad overlap group had no single co-located owning bundle, and bundle B3 omitted both endpoints for D1-D4; output was also 1,032 compact code points above the 6,000 soft target, which was warning-only;
- the frozen tool-order checker failed because it expected both numbered reads before both hashes. This is also a P1 methodology defect: the committed Reader role requires `git hash-object` after each directly read body, and the candidate followed that role. The strict checker result remains failed and was not relabeled;
- Parent semantic audit failed A2/A4/A5 structured ownership; independent blinded audit failed A8 and dependency/gap placement. Both audit verdicts were `fail`, but exact atom-support agreement failed;
- the frozen Parent oracle’s A8 expected-text checklist omitted the no-registry-mutation-authority clause that remained present in the frozen semantic atom. This P1 oracle defect explains part of the Parent/blinded disagreement and cannot repair the candidate;
- the frozen generic extractor expected a JSON capture envelope while transport returned raw candidate JSON. Parent preserved stdout bytes exactly and independently matched them to the sole session `structured_output` value; the capture-shape gap is recorded as P1 methodology risk, not hidden or used to alter candidate bytes;
- strict case verdict: `sha256:8a8ce0587f65cdafd21ace424be141bcd23efdd4e7d1784581acbf9f4d22782c`, `valid=false`, `approvedForNextCase=false`.

Case 02 `clean-preflight-02-prompt-budget` was `NOT-RUN-FAIL-FAST`; no candidate, transport, child session, or case verdict exists.

Closure evidence:

- final preflight verdict `sha256:f6d68b77d826c87ac60560123ff0243b8e4f5e5d6d1611df27e9fabf8a35a114`;
- closure attestation `sha256:ddb4c309b0b4b073353135852b4c635d2738822dbcf11230088d0f9dfc9a7873`;
- execution manifest `sha256:a884fa6d4a5718e60c2f94fb0c1bb13608d17a7c4d063dac2530a5b003a17da0`;
- clean subject HEAD `fe73a23262fc40b9bb49da02fd2d729f557428aa`.

Outcome: the corrected static contract remains independently implementation-reviewed, but fresh Sol Medium live adherence and Direct Parent semantic-quality equivalence are not proven. Task #108, integration, permanent model defaults, Writer, debt transfer, merge/release, and graph migration remain closed.

#### Discovery capture — failed preflight

- DDD/SDD/BDD/TDD/ADR/SSOT: no independent production semantic delta; the experiment exposed proof-tool/oracle defects and one failed candidate, not an authorized contract change.
- Planning: updated with immutable candidate/verdict hashes, fail-fast closure, methodology defects, and closed authorities.
- Future work candidates, requiring a new user option/approval before mutation or launch: repair the capture contract and role-consistent tool-order attestation; repair the A8 oracle checklist; then freeze a wholly new candidate and decide whether another bounded preflight is warranted.

### User-selected stop boundary

The user initially selected **freeze and stop** after the failed-fast closure. After clarifying that the static implementation passed but live readiness failed, the user reopened the work only for a **remediation plan proposal**. No implementation, proof-tool/oracle mutation, new preflight preparation or launch, integration proposal, model-default change, merge, push, release, or graph migration is authorized yet.

### Reader remediation plan proposal — approval pending

Goal: separate methodology defects from the model’s real candidate-map defects, repair both without touching immutable V1–V8 or the failed clean preflight, and require a wholly new candidate before any quality claim.

#### Phase 1 — preserve and branch

1. Keep commit `fe73a23262fc40b9bb49da02fd2d729f557428aa`, failed candidate `sha256:adad39b0cc03226c76a413d52dfa0093fe45ef4ed6be39919fc19e86b873408b`, both failed audits, and every prior proof root immutable.
2. If execution is later approved, create a new isolated remediation worktree/branch from `fe73a23262fc40b9bb49da02fd2d729f557428aa`; never mutate the clean-certification or failed-proof worktrees.

#### Phase 2 — repair proof methodology first

1. Replace the ambiguous capture path with one frozen capture contract: transport stdout must be raw JSON, the tool must parse the child JSONL session, require exactly one final `structured_output`, prove object equality, and byte-preserve the raw candidate. Positive, duplicate-output, malformed-stdout, and stdout/session-mismatch fixtures are required.
2. Generate expected tool order from ordered node pairs: three probes; every map drill; then for each node, exact `nl -ba -- <path>` immediately followed by `git hash-object -- <path>`; one final `structured_output`. This aligns the checker with the committed Reader role instead of grouping all reads before all hashes.
3. Require Parent oracle validation to cover the complete semantic-atom meaning. A8 must include the no-registry-mutation-authority clause; partial token checklists cannot silently narrow an atom.
4. Harden semantic-audit validation to require the exact A* set, unique rows, exact candidate/oracle hashes, substantive reasons, and verdict consistency. Agreement remains exact and non-authorizing.
5. Verify all methodology changes with synthetic fixtures only. No live Reader run is allowed in this phase.

#### Phase 3 — harden actual Reader candidate-map guidance

1. Keep deterministic admission ownership unchanged unless a separate contract review disproves it. The failed candidate exposed real output defects that the current admission correctly rejected.
2. Make proposal-ready invariants explicit in `record-reader.md` and the Work Packet overlay: every question has exactly one bundle; every declared overlap/cycle group has exactly one bundle containing the entire group; every dependency has exactly one owning bundle containing both endpoints.
3. Add a bounded pre-submission checklist requiring the Reader to downgrade from `proposal-ready` when any overlap, dependency, bundle, atom-ownership, gap, or overflow invariant is unsatisfied.
4. Preserve exact structured A* ownership and add explicit handling for compound atoms such as A8 so question text and ownership cannot omit a semantically distinct clause.
5. Reduce duplicated question/risk/bundle prose toward the 6,000-character soft target without deleting evidence; the 12,000 hard cap remains unchanged.

#### Phase 4 — regression and independent static certification

1. Add focused admission/profile fixtures for valid co-located overlap ownership, split-overlap rejection, missing dependency endpoint rejection, role-consistent read/hash order, complete compound-atom oracle coverage, and raw-transport capture matching.
2. Run focused compilation/checks, then one standard validation after the final mutation.
3. Require a new independent high-reasoning review of the bounded remediation diff. Any P1/P2 finding freezes that candidate as failed; no same-candidate repair may change its verdict.

#### Phase 5 — separately approved new preflight

1. After static certification, freeze a new external proof root with two fresh, previously unused work units and Parent oracles before any launch. The failed regression-registry candidate is not rerun or relabeled as counting evidence.
2. Request a separate execution approval. Then run Sol Medium with bridge off, fresh context, exact reads, no fallback/retry, and fail-fast.
3. Each case must pass unchanged schema/admission, capture/session equality, role-consistent tool sequence, atom/range/preservation gates, Parent semantic review, independent blinded semantic review, and exact agreement.
4. Two passes would prove only bounded live contract adherence and permit a later Task #108 quality-suite proposal. They still would not authorize integration, a permanent model default, Writer, debt transfer, merge/release, or graph migration.

#### Proposed completion criteria

- methodology fixtures all pass before a live candidate exists;
- remediation diff is isolated, bounded, and independently certified with no P1/P2;
- both new cases pass every mechanical and semantic gate without post-candidate repair;
- all failed artifacts remain immutable and clearly separate from any new result.

#### Discovery capture — remediation plan

- SDD/TDD candidate delta: Reader role guidance and regression fixtures, only if later execution approval is granted.
- Planning: updated with the proposed phases and gates.
- ADR/DDD/BDD/SSOT: no independent delta at plan stage.
- Execution state: `PLAN-PROPOSED-NOT-APPROVED`.

### Remediation execution approval

The user approved Phases 1–4 only: isolated implementation, proof-methodology repair, Reader guidance hardening, focused regression/standard validation, and independent static certification. The user selected `/tmp/lazy-harness-record-reader-remediation-v1` as the new worktree path. Live Reader/model execution, a new preflight proof root, integration, permanent model defaults, merge, push, release, Writer, debt transfer, and graph migration remained unapproved.

### Remediation v1 static certification — failed and frozen

The isolated candidate reached green executable validation before review: 30 offline proof fixtures, focused Pi package check, Python compile, three-entry Bun build, 773-row graph parse, `git diff --check`, `lazy check`, and final standard validation all passed. Parent also corrected the candidate’s sequence fixture from the generic `read` tool to the required exact `nl -ba -- <path>` followed by the matching hash before that final validation. No live Reader/model run occurred.

Independent Luna High static review nevertheless returned **FAIL** with three P1 and two P2 findings:

1. **P1 runtime contradiction** — Reader guidance requires exact `nl -ba`, but `recordReaderShellAllowed` blocks it while the generic `read` tool remains allowed.
2. **P1 incomplete-node acceptance** — sequence validation maps every contract node but does not require `packet.reads` to cover the exact node set, so a node can lack its body-read/hash pair.
3. **P1 audit/blinding defect** — audit validation requires Parent status and packet-finding equality, conflating structural validation with agreement and preventing an honest blinded disagreement from remaining visible.
4. **P2 output-root safety gap** — external-only capture protection derives the project root only from caller cwd and skips containment when no root is found.
5. **P2 provenance gap** — oracle/audit evidence validates record ids and range indexes but does not bind candidate record paths/hashes to contract nodes and validated sequence provenance.

Per the approved Phase-4 stop rule, this exact candidate is immutable failed-review evidence and may not be repaired or relabeled. The reviewer-generated `.pi-subagents/` runtime directory was relocated out of the worktree as a mechanical artifact; the restored candidate scope is exactly ten unstaged paths at unchanged HEAD `fe73a23262fc40b9bb49da02fd2d729f557428aa`.

Frozen closure:

- archive: `/home/lazydino/.local/share/lazy-harness-proofs/record-reader-remediation-v1-static-review-20260826`;
- candidate bundle: `sha256:c9ad258fb551bb48b796971d01980a38c5fc943e808bf712cef6d174fcaa7089`;
- candidate manifest: `sha256:26a5b3b47021ef0eac80abe0d5b305f10fe78a7d7fd528bc0b3742529a2e4f49`;
- independent review: `sha256:2146c6f4b0be38d8bf0296dfdaca4a6b2ea20507c87b0075969709b6db88c03f`;
- final verdict: `sha256:f83abc659e6071889a158534f995824cfd126cb4b0229d57bf5ff3bf4af67b5b`;
- closure manifest: `sha256:4d649e88c7147b7302f0963e8fc403d3095906e76b36606b32781ed56a87b4ce`.

Outcome: Phases 1–3 produced useful but uncertified code; Phase 4 failed as designed. No live preflight, integration, default model, Writer, merge/push/release, or graph migration is authorized. A wholly new remediation candidate requires a new user decision and must address all five findings without modifying this frozen candidate.

#### Discovery capture — remediation v1 failure

- SDD/TDD: candidate changes remain experiment-only failed evidence; no canonical promotion or integration delta.
- Planning: updated with review findings, immutable hashes, and the stop boundary.
- ADR/DDD/BDD/SSOT: no independent delta.
- Execution state: `STATIC-CERTIFICATION-FAILED`; user option gate required.

### Remediation v2 execution approval

The user approved a wholly new static remediation candidate at `/tmp/lazy-harness-record-reader-remediation-v2`, based again on clean commit `fe73a23262fc40b9bb49da02fd2d729f557428aa` rather than on the frozen v1 diff. Scope is limited to the five independent-review findings:

1. runtime permits exact canonical `nl -ba -- <path>` and denies generic Reader body reads;
2. sequence requires exact set equality between contract nodes and one ordered read/hash pair per node;
3. audit structure validation is separated from an explicit agreement gate so honest blinded disagreements remain valid and visible, with packet-finding identity supplied by a frozen blinded catalog rather than Parent oracle content;
4. capture requires an explicit bound project root and fails closed when it cannot prove output paths are external;
5. candidate record path/hash and cited provenance bind to contract nodes plus validated session read/hash results.

The new candidate must add focused positive/negative fixtures, retain the already-correct proposal-ready guidance and admission ownership, run offline focused/full validation, and receive a fresh independent high-reasoning static review. Any P1/P2 freezes v2 as failed. No live Reader/model run, preflight proof root, integration, default model, Writer, merge/push/release, or graph migration is authorized.

### Remediation v2 static certification — failed and frozen

The clean-base v2 candidate reached green Parent validation: 51 hermetic proof fixtures, focused Pi package check, Python compile, two-module Bun build, 773-row graph parse, `git diff --check`, `lazy check`, and final standard validation (`73.475s`) passed. Parent also corrected actual Pi session parsing from generic `tool` to real `message.role=toolResult`, then used immutable failed case-01 bytes for a non-counting compatibility check: byte-preserving capture receipt `sha256:b3c5fcbbb976f31383ec9c7997a6a7f64f7df366d5f51d3d2a64af283bfd9041` and exact ten-call sequence receipt `sha256:2917a5ce2ae094a9d3f3bcaf00497665dad8088f4f8aae4ed4f6fc1ab212f052` passed. This did not alter the historical case’s admission/semantic failure and was not live/model-quality evidence.

Independent Luna High static review wrote a complete report before its dispatch process was killed and returned **FAIL** with four P1, four P2, and one non-blocking P3 finding:

1. **P1 root/revision result gap** — sequence binds the three probe command strings and result presence but not their output to the actual Git root and expected revision.
2. **P1 non-hash result gap** — probe, map, and `nl` result errors, empty content, and malformed shapes can pass because only matching result presence is required; hash text alone receives content validation.
3. **P1 range/body provenance gap** — cited range syntax/order is checked, but ranges are not bounded against or derived from the actual line-numbered `nl` result.
4. **P1 admission-authority gap** — the proof contract/candidate checks do not mechanically bind compact `record-reader-admission/v2`, mode, contract digest, ownership/coverage semantics, non-authorizing booleans, or an admission receipt.
5. **P2 caller-cwd output gap** — relative capture output paths remain caller-cwd dependent; absolute-path safety cases pass but the grammar does not require absolute outputs.
6. **P2 rollback fixture gap** — partial-create rollback exists in source but no fixture forces candidate-create success followed by receipt-create/write failure.
7. **P2 map-scope gap** — the runtime map guard accepts noncanonical in-root paths rather than restricting map nodes to canonical record layers.
8. **P2 top-level result-shape gap** — real Pi role-wrapped `toolResult` passes, but top-level `type: toolResult` is neither parsed nor explicitly rejected/protected by fixtures.

Per the approved stop rule, v2 is now immutable `FAILED-STATIC-CERTIFICATION` evidence. The exact eleven-path worktree remains unstaged at unchanged HEAD `fe73a23262fc40b9bb49da02fd2d729f557428aa`; no same-candidate repair or verdict change is authorized.

Frozen closure:

- archive: `/home/lazydino/.local/share/lazy-harness-proofs/record-reader-remediation-v2-static-review-20260826`;
- candidate bundle: `sha256:d3c775320937ff9e0a3e0b2a830b44429dd091e4843bb5c346d8c8c9cfa9d3e7`;
- candidate manifest: `sha256:9e7bad0827673d3c23c5ba17fcf3b7139366af5d9929841332044626d8a16e44`;
- independent review: `sha256:61d3b15d959b10ca3f7acf891392f59bc3426e7d01aab45d30f7041a86022fb2`;
- final verdict: `sha256:bf2a7f40ff5eb11e19d5cc1502c8558e5cf34d6714d75a6d1c34992324bb30f9`;
- closure manifest: `sha256:72f60f723c6652062e37d6882e17e59602595522d8c42e5a933683df6a65d2a8`.

Outcome: static v2 failed as designed despite green executable checks. No live Reader/model preflight, integration, permanent model default, Writer, merge/push/release, or graph migration is authorized. Any further attempt must be a wholly new remediation candidate with a new user decision and must address all eight blocking P1/P2 findings without modifying v2.

#### Discovery capture — remediation v2 failure

- SDD/TDD: v2 remains experiment-only failed evidence; no canonical promotion or integration delta.
- Planning: records independent findings, immutable hashes, and stop boundary.
- ADR/DDD/BDD/SSOT: no independent delta.
- Execution state: `STATIC-CERTIFICATION-FAILED`; user option gate required.

### Remediation v3 design approval — planning only

After v2 closure, the user selected **Design v3 only**. This authorizes requirements/methodology planning and this Planning update only. It does not authorize a worktree, implementation, mutation of v1/v2, live Reader/model execution, a preflight proof root, integration, a default model, Writer, merge/push/release, or graph migration.

#### V3 authority model

1. Start any later candidate from exact clean contract commit `fe73a23262fc40b9bb49da02fd2d729f557428aa`; v1/v2 are immutable evidence and must not be inherited, repaired, or relabeled.
2. Replace the duplicate proof-contract authority with a small frozen proof envelope that references one exact compact `record-reader-admission/v2` contract by file hash and recomputed `contractDigest`. Derive nodes, modes, semantic atoms, and output schema from that admission contract rather than restating them.
3. Bind the envelope to canonical absolute project-root realpath, exact full expected HEAD, case id, compact-contract file hash/digest, generated-schema hash, required admission outcome/status, and blinded packet-finding identities.
4. The proof CLI must call the existing exported `assertContract`, `buildRecordReaderOutputSchema`, `computeRecordReaderContractDigest`, and `admitRecordReaderOutput` authorities. A sequence receipt is valid only when the exact captured candidate matches the final structured object, its `contractDigest` matches, unchanged admission returns the envelope-required valid/success/status outcome, and the receipt binds candidate bytes plus admission/schema hashes. Proof code may not reimplement or weaken compact admission.

#### V3 session and provenance closure

1. Parse an explicit closed set of actual Pi result shapes: role-wrapped `message.role=toolResult`, top-level `type=tool_result`, and top-level `type=toolResult`. Normalize each once, retain call id, exact text payload, shape, and error metadata, reject duplicate calls/results, reject recognized-but-malformed or result-like unknown shapes, and require explicit non-error success.
2. Verify result content, not only command order: `pwd` realpaths to the envelope root; `git rev-parse --show-toplevel` realpaths to the same root; `git rev-parse HEAD` exactly equals expected HEAD; every map and `nl` result is nonempty and non-error; every hash result is exact lowercase 40/64 hex.
3. Preserve exact sequence set equality: three probes, every contract-node map, exactly one immediate `nl -ba -- <canonical-path>` plus matching hash pair per node, and exactly one final structured output with no extra call/result or duplicate id.
4. Parse each actual `nl -ba` result as consecutive line numbers beginning at 1, including blank lines. Bind per-node result hash and line count into the sequence receipt. Validate every candidate range against its matching node’s actual line count and emit a deterministic hash of each exact numbered range slice; invented/out-of-bounds ranges fail before semantic review.
5. Bind each candidate record one-to-one to the admission-contract node path and observed immediate hash. The sequence receipt also binds session bytes, final object, compact admission receipt, project root/revision probes, and all per-range attestations. Mechanical provenance remains non-authorizing.

#### V3 runtime and artifact safety

1. Restrict Reader map commands to existing canonical record-layer paths only, using the same root/layer/shell-metacharacter checks as `nl` and hash. Overview remains exact; in-root source/config/test-script map nodes are denied. Generic Reader `read` stays absent/denied.
2. Require every CLI filesystem argument to be absolute. Output paths must be distinct, nonexisting, outside the explicit actual Git root after existing-parent realpath resolution, and created exclusively. Relative outputs fail before resolution, making interpretation caller-cwd independent.
3. Keep byte-preserving capture and exactly-one-final-object equality. Refactor capture IO behind a narrow injectable adapter so fixtures can force first-create success followed by second-create/write failure and prove both partial files are removed; production CLI uses only the real exclusive-write adapter.
4. Preserve deterministic canonical JSON plus trailing-newline receipts and closed per-command option grammar. Every receipt/output command writes only to an explicit new absolute path under an external proof root; unknown, duplicate, missing, or command-inapplicable options fail.

#### V3 blind review and fixtures

1. Freeze a catalog containing contract/candidate/sequence commitments, exact atom and packet-finding identities, and only an opaque Parent-oracle hash. Independent audit validation receives no Parent oracle path/content and may disagree while remaining structurally valid.
2. Reveal both separately validated reviews only to the explicit agreement command. It must inventory every atom, packet, and verdict disagreement, return nonzero with deterministic `valid:false/agreed:false`, and never repair either review.
3. Add focused negatives for wrong/extra/multiline probe outputs; all non-hash error/empty/malformed results; duplicate/orphan/unknown result shapes; each accepted Pi result shape without double counting; missing/extra/reordered nodes; nonconsecutive `nl`; out-of-bounds/forged ranges; compact digest/schema/admission/status substitution; relative/same/in-root/symlink outputs; forced rollback failures; and noncanonical in-root map targets.
4. Add positives for blank/tab-bearing numbered bodies, exact oversized range ordering, caller-cwd-independent absolute outputs, valid compact candidate-map and claim-evidence admission, honest blinded disagreement, and archived real Pi `toolResult` bytes as non-counting parser evidence.

#### V3 execution gates

1. A later execution request must first choose a wholly new worktree path and approve one bounded static candidate. One writer owns that worktree; no live Reader/model run occurs.
2. Parent reads the complete diff, runs focused fixtures/build/graph/diff checks, and runs one final standard validation after the last mutation.
3. A fresh independent high-reasoning reviewer must examine runtime guard, exact result semantics, compact-admission authority, root/output safety, range provenance, blinding, package exposure, and implementation-map truth. Any P1/P2 freezes v3 permanently as failed.
4. Static PASS would authorize only a separate user question about freezing and executing a wholly new two-case live preflight. It would not itself authorize that preflight or any integration/promotion.

#### Discovery capture — remediation v3 design

- Primary canonical record: this Planning section; no implementation record is promoted.
- SDD/TDD candidates: proof envelope/admission binding, closed session-result grammar, line-range attestations, absolute-output/rollback contract, canonical map guard, and focused fixtures if execution is later approved.
- BDD/DDD/ADR/SSOT: no independent delta at design-only stage.
- Execution state: `SUPERSEDED-BY-HARNESS-READER-JOIN-CORRECTION`; no v3 proof implementation is authorized.

### User correction — Harness Reader owns stored records; Parent owns the parallel code lane

The user corrected the repeated Reader-remediation premise. Reader is required, but not as a Parent-selected-node evidence scout and not as a proof-producing replacement for Parent debt. The intended workflow is:

```text
work-unit start
→ launch one Harness Reader
   → complete lazy map overview
   → search/select/read relevant DDD/SDD/BDD/TDD/ADR/SSOT/Planning records
   → return policies, facts, conflicts, missing information, paths, status
∥ Parent inspects source/tests or immediately needed behavior
→ Parent waits for Reader response
→ merge record context with code reality
→ plan / mutate / validate
```

The Reader owns all stored harness policy/fact retrieval. The Parent does not preselect concrete record nodes, does not sit idle, and does not reread Reader-covered records merely to satisfy `requiredRead` or search/read debt. Parent direct reads are bounded to Reader failure/incomplete/conflict, an obviously omitted layer, or editing that exact canonical record.

The v1/v2 failures remain immutable historical evidence, but their admission/provenance/audit/agreement problem is no longer the implementation target. The v3 proof-envelope plan above is superseded and must not be executed.

#### Simple replacement backlog — execution not approved

1. Define one thin Reader role: root-bound, read-only, harness records only, no source-code analysis, no mutation/decision/validation/fan-out.
2. At Parent work-unit start, launch Reader asynchronously with root/revision/current task. Reader itself runs complete harness map inventory and relevant cross-layer record reads.
3. Parent concurrently investigates source/tests or immediately needed behavior.
4. Add one join before plan/mutation/completion. Consume ordinary Reader output with `complete|incomplete|conflict`; no admission, tool-sequence proof, independent audit, or agreement receipt.
5. On `complete`, do not require duplicate Parent record reads. On `incomplete|conflict|failure`, perform bounded Parent follow-up or option gate.
6. Retire or narrow `search-read-debt.jsonl`, `check-read-debt-permit.py`, direct Parent `requiredRead` enforcement, and related prompt/audit language for Reader-managed work units. Preserve only unrelated destructive safety, promoted structural command boundaries, record-as-output, and response-completed capture backstops.
7. Add focused tests for launch concurrency, join-before-action, complete/no-reread, failure fallback, steer invalidation, Reader layer coverage, and strict read-only/no-code boundaries.
8. Benchmark only after this simple flow works. Compare quality/wall-clock/context with Direct Parent; do not introduce proof infrastructure to rescue a failed benchmark.

No worktree, source mutation, Reader launch, model run, integration, default-model change, merge/push/release, or graph migration is authorized by this record-only correction.

#### Discovery capture — Harness Reader ownership correction

- DDD: updated — Harness Reader, Parent code lane, Reader join.
- SDD: updated — debt contract records accepted supersession direction and current transitional implementation.
- BDD: updated — Reader record retrieval runs in parallel with Parent code/behavior investigation and joins before action.
- TDD: updated — planned replacement scenarios; no implementation/pass claim.
- ADR: updated — parent-global/child-scoped debt and proof-remediation direction superseded.
- SSOT: updated — mandatory recall remains; Reader completion is the target mechanism and debt hooks are transitional.
- Planning: updated here — v3 proof plan superseded; simple implementation backlog is execution-not-approved.

## User correction — Parent Sol Medium, delegated Luna with calibrated effort (2026-09-04)

The user corrected the model-routing premise after the practical native-read R6 comparison:

- one non-delegated Parent treatment uses exact `openai-codex/gpt-5.6-sol:medium`;
- actual parallel worker/subagent treatments use the `openai-codex/gpt-5.6-luna` family;
- Luna thinking effort is not assumed and must be found empirically under a quality-non-regression gate;
- `read_batch` is an I/O tool shape inside whichever agent invokes it, not a subagent/model route.

The completed practical R6 artifact at `/tmp/lh-native-read-batch-practical-ab-r6-20260904` explicitly used Sol Medium for all eight arms. It remains immutable, valid directional evidence about ordinary versus grouped reads in a Parent-like model session, but it is not evidence for Luna child cost, quality, or effort. The previously proposed fixed Luna-Low eight-arm rerun was cancelled before launch when the user supplied this correction.

### User-selected staged effort search

The user selected a lowest-sufficient-effort staircase and then authorized only the first rung: four fresh Luna Low child runs, one for each frozen R6 workload shape. The calibration fixes ordinary native reading to avoid confounding model effort with `read` versus `read_batch`; each child is fresh, read-only, no-fallback, no-retry, and evaluated against the frozen Sol Medium oracle before cost, tokens, or time count.

A Luna effort passes a case only when it has no critical-fact omission, no materially wrong or unsupported claim, reaches at least that case's frozen Sol Medium semantic score, and preserves exact evidence/current-versus-history boundaries. A failed Low case may move to Medium only after a new user decision; High and XHigh remain similarly gated. The first passing effort would be the minimum sufficient effort for that workload shape; failure through XHigh would make Luna unsuitable for that shape.

Approved artifact root: `/tmp/lh-parent-sol-child-luna-effort-r1-20260904`. Frozen preparation contract SHA-256 is `5118f0690d6bc646aae6672e1d7b4a355f49eb75dc56cb7c818d6e745c31bba0`. Preflight passed with four byte/mode/symlink-identical 621-file-plus-one-symlink source copies, exact Luna availability, matching R6 prompt hashes, no preexisting child outputs/sessions, and no higher-effort authority. Four Luna Low delegate children are the only approved model runs in this stage.

### Authority boundary

This correction does not configure a permanent Parent or child model default, integrate a Reader, add `read_batch`, change the Pi package, or authorize Medium/High/XHigh runs. Current supervising-session usage is excluded from treatment metrics. Actual Sol-Parent-plus-Luna-parallel topology validation and framework rule/contract implementation remain later decisions after the effort screen.

### Rule placement and discovery capture

- Rule: Parent-only uses Sol Medium; delegated workers use Luna with effort selected by measured quality equivalence, while I/O shape remains an independent decision axis.
- Scope: user-confirmed architecture direction plus transient calibration plan.
- Primary record: `.lazy-harness/planning/agent-neutral-orchestration-pilot.md` until a passing calibration and separate framework-rule decision justify promotion.
- Why not AGENTS/SSOT yet: no Luna effort or deployed model default has passed this work-unit gate.
- Confirmation: user-confirmed; Luna Low four-case first rung explicitly approved.
- DDD: none; no domain vocabulary delta.
- SDD/BDD/TDD/ADR/SSOT: candidate only; no active contract, behavior, regression, architecture-default, or config mutation yet.
- Planning: updated here with the correction, frozen baseline distinction, quality gate, approved run ceiling, and artifact path.

### Luna Low first rung — setup-invalid and stopped

Run `4e81f415-6a76-4856-a022-92a81891be1e` launched exactly four fresh `openai-codex/gpt-5.6-luna:low` delegate children concurrently. Runtime resolved the exact model/thinking for all four, used no fallback, and started no higher-effort child. One child was officially complete and three were rejected; zero arms are admitted to the effort gate.

The failure is primarily a Parent launch-envelope defect. The Parent omitted `acceptance:false`, so the runtime auto-inferred a checked implementation contract requiring edits, tests, and review despite the explicit read-only tasks. Supplying per-task output paths also injected an authoritative write instruction: case 1 wrote its external result and was accepted, while cases 2–4 returned substantive prose but were rejected for making no edits. This attempt is not retried or repaired in place.

Strict source-copy preservation also failed. Map/hook execution added only runtime-derived `.lazy-harness/.gitless/**` and Python `__pycache__` files; no preexisting path changed or disappeared. Independently, every child exceeded its prompt-declared requested-line ceiling, and the steer case also exceeded its body-read-count ceiling. These instruction-adherence failures remain visible rather than being excused by the acceptance defect.

Recovered content is directional only: Luna Low scored `9/10`, `13/16`, `24/24`, and `16/20` across the four cases (`62/70` total versus the frozen Sol Medium ordinary baseline's `68/70`). All `14/14` critical criteria were present, but only validation policy matched its per-case Sol score. Because the protocol is setup-invalid, these numbers neither select nor reject Luna Low and do not authorize Medium escalation.

Observed invalid-attempt diagnostics: parallel wall `77.665s`, summed child span `250.767s`, input/output `196,902/5,969`, cache-read `551,424`, reasoning `1,174`, and reported cost `$0.05757168`. Artifact root: `/tmp/lh-parent-sol-child-luna-effort-r1-20260904`; terminal result: `terminal-attempt-1.json`; report: `report-attempt-1.md`. Artifact validation passes only the faithful characterization of the invalid attempt.

Next action requires a new user choice among a fresh corrected Low protocol (`acceptance:false`, no child output write contract, runtime-derived state excluded from canonical preservation), treating the diagnostic as insufficient and proposing Medium, or stopping without an effort selection. No automatic retry, Medium/High/XHigh run, model default, Reader integration, base-rule change, `read_batch` integration, commit/push/release, or graph migration is authorized.

#### Discovery capture — Luna Low setup-invalid stop

- DDD: none.
- SDD/TDD: candidate — a future corrected calibration envelope must explicitly disable inferred writer acceptance, avoid child output-path writes, and distinguish canonical source preservation from runtime-derived files; no production contract/test change is approved.
- BDD/ADR/SSOT: none; model routing remains a confirmed direction without a deployed effort/default.
- Planning: updated with the immutable setup failure, directional-only content, exact metrics, and renewed user-decision gate.

### Corrected Luna Low R2 — second setup-invalid stop

The user selected a fresh corrected four-case Low protocol. R2 used separate synthetic Git snapshots with identical tracked tree, `acceptance:false`, `output:false`, `artifacts:false`, Parent-side output recovery, exact Luna Low, fresh contexts, and no fallback/retry. Run `7b9ab447-2c53-4d21-9583-fccf4de66675` returned normal substantive answers from all four children with no mutation tool calls and byte-identical tracked HEAD/index/tree.

All four were nevertheless post-completion failed. Runtime reported `acceptance:not-required`, proving the first acceptance/output conflict was removed. Direct installed-source inspection then identified a separate role-level boundary: async builtin `delegate` uses the legacy/default completion mutation guard independently of acceptance and converts a no-edit result to exit 1. In the inspected background runner, `agentContract.version=1` disables that guard unless `completionGuard:true` is explicitly selected. R2 did not opt into v1, so it remains immutable setup-invalid evidence rather than being relabeled from its recovered prose.

Two additional instruction-adherence failures remain genuine: the steer case requested `1,600/800` lines and the Jcode case `1,500/1,200`. Single-record and validation-policy stayed exactly within their read/line budgets. Directional content scored `10/10`, `11/16`, `24/24`, and `17/20` (`62/70` versus Sol Medium `68/70`); only single-record and validation-policy matched their baseline. These values cannot select Low because every official arm failed, but they must not be hidden if a new protocol is considered.

R2 diagnostics: parallel wall `80.981s`, summed child span `215.637s`, input/output `183,743/4,597`, cache-read `578,048`, reasoning `1,227`, reported cost `$0.05382596`. Artifact root: `/tmp/lh-parent-sol-child-luna-effort-r2-20260904`; root-cause note: `completion-guard-root-cause.md`; terminal: `terminal.json`. Validation proves faithful characterization, four exact model routes, answer recovery, tracked preservation, no mutation calls, and zero counted arms—not an effort pass.

The approved corrected-run allowance is consumed. No automatic third launch, Agent Contract v1 canary, Medium/High/XHigh escalation, model default, Reader/base-rule/read-batch integration, commit/push/release, or graph migration follows. A new user choice is required.

#### Discovery capture — corrected R2 setup-invalid stop

- DDD/BDD/ADR/SSOT: none.
- SDD/TDD: candidate — the subagent launch contract may need explicit Agent Contract v1 or a read-only role that disables completion-mutation expectations; this is runtime evidence, not an approved package change.
- Planning: updated with the second immutable setup failure, direct installed-source cause, directional content, budget violations, metrics, and closed run allowance.

### Agent Contract v1 read-only canary — PASS

The user selected exactly one non-counting canary before any third four-case launch. Run `50987854-acfa-4891-9465-d47fa312e417` used a fresh `openai-codex/gpt-5.6-luna:low` builtin delegate with `agentContract.version=1`, `acceptance:false`, `output:false`, and `artifacts:false`. It completed normally with `acceptance:not-required`; the legacy no-edit completion failure did not recur.

The canary's first call was the exact complete overview. It used `2/2` reads and exactly `320/320` requested lines, returned a normal substantive answer, called no mutation tool, had no failed tool result, and preserved synthetic Git HEAD/index/tracked tree. Runtime was `35.797s`, `5` turns, `4` tools, `29,892` input, `692` output, `74,752` cache-read, `215` reasoning tokens, and `$0.00830384`.

Artifact root: `/tmp/lh-parent-sol-child-luna-effort-r3-v1-canary-20260904`; answer SHA-256 `8402cacc6b98379cc15c38bb6f3c98958620adab20b22f470639cf15fc2f93c3`; manifest SHA-256 `0408e84abcfa8f5fc0dededb3b8047a426b78e7ec9d651e3b02d129fe398d0f7`. The pass proves the corrected transport envelope once; it is non-counting and does not itself select Luna Low effort.

The canary allowance is consumed. Four fresh v1-contract Low quality arms, Medium/High/XHigh escalation, persistent model configuration, Reader/base-rule/read-batch integration, commit/push/release, and graph migration remain separately gated.

#### Discovery capture — Agent Contract v1 canary

- DDD/BDD/ADR/SSOT: none.
- SDD/TDD: candidate — explicit Agent Contract v1 is now verified as the bounded read-only delegate envelope for one canary; no production package contract or fixture is approved yet.
- Planning: updated with the one-run PASS, exact transport/source/budget evidence, metrics, artifacts, and next execution gate.

### Luna Low four-case quality calibration — workload-specific result

After the non-counting Agent Contract v1 canary passed, the user explicitly approved four fresh counting Luna Low quality arms. Run `6a680465-caf9-40f3-b097-673085ce6822` completed all four with exact `openai-codex/gpt-5.6-luna:low`, `agentContract.version=1`, `acceptance:false`, `output:false`, no fallback/retry, no failed tool result, no mutation call, and unchanged synthetic Git HEAD/index/tracked tree.

Parent quality-first scoring against the frozen Sol Medium oracle produced:

| Workload | Protocol | Luna Low | Sol Medium baseline | Effort gate |
|---|---|---:|---:|---|
| Single canonical record | FAIL — `360/320` lines | `10/10` | `10/10` | FAIL |
| Sequential steer/source/test | FAIL — `5/4` reads, `1685/800` lines | `12/16` | `15/16` | FAIL |
| Independent validation policy | PASS — `4/6` reads, `1200/1200` lines | `24/24` | `24/24` | **PASS** |
| Broad Jcode active/history audit | PASS — `5/6` reads, `1200/1200` lines | `17/20` | `19/20` | FAIL |

Luna Low covered all `14/14` critical criteria and scored `63/70` versus Sol Medium's `68/70`, but only validation-policy synthesis satisfied runtime, semantic, evidence, budget, and preservation gates together. Low is therefore not a global child default. It is a bounded workload-specific pass for independent validation-policy synthesis in this one sample; single-record, sequential steer, and broad active-versus-history audit remain Medium candidates.

Only the quality-equivalent validation case permits efficiency comparison: Sol Medium ordinary versus Luna Low was `46.420s → 38.326s` (-17.44%), `6/8 → 4/6` turns/tools, `110,863 → 86,804` provider total tokens (-21.70%), and `$0.31012000 → $0.01121432` (-96.38%). Different Parent/subagent system envelopes and one sample prevent pure model causality or a universal default claim.

The four-arm aggregate completed in `65.531s` parallel wall and cost `$0.04927724`, but aggregate performance is not promoted because three workload shapes failed the quality gate. Artifact root: `/tmp/lh-parent-sol-child-luna-effort-r4-low-quality-20260904`; terminal SHA-256 `88f35039bb01aabd21eb300fd43eb8e863799bdb7cead7764724d637d584aad1`; report SHA-256 `a8d1cc2a1c7e1f81c5045abd6f4a40861c270002c3ec59ddede97348e80295ea`; manifest SHA-256 `a8196dd69876955caf62232d5f6c8e655efe28028f264ca58aa8800ea7423794`.

No Medium/High/XHigh treatment, persistent model configuration, Reader integration, base retrieval-rule implementation, `read_batch` integration, commit/push/release, or graph migration is authorized. The staged method now requires a user decision on Medium for the three failed workload shapes.

#### Discovery capture — Luna Low workload result

- DDD: none; no domain vocabulary change.
- SDD: candidate — eventual child routing may require workload/effort selection plus explicit Agent Contract v1, but no deployed contract changes.
- BDD: candidate — Parent/child tool and model choice remains adaptive behavior pending a complete effort ladder.
- TDD: candidate — future regression may protect read-only Agent Contract v1 and workload effort routing after implementation approval.
- ADR: candidate — Parent Sol Medium / child Luna architecture direction is confirmed, but effort mapping and deployment are incomplete.
- SSOT: none; no model/default/settings mutation.
- Planning: updated here with the first valid four-case Low result, qualified efficiency, Medium candidates, artifact identities, and renewed execution gate.

### Actual Sol Medium Parent topology A/B — terminal no-go

The user corrected that the Parent is always exact `openai-codex/gpt-5.6-sol:medium`; Luna is only a worker/subagent route. The current supervising session is not a treatment and its usage is excluded. The user then selected and explicitly approved one actual broad-audit topology pair:

1. fresh Direct Parent — Sol Medium, no child;
2. fresh Delegated Parent — Sol Medium, exactly one fresh Luna Medium child, Parent retains source verification, join, semantic correction, and final answer.

Both arms use byte-identical synthetic Git snapshots of the frozen Jcode active-versus-history case, run sequentially, and forbid fallback/retry, tracked mutation, validation, and persistent settings. The delegated Parent must run one concurrent source/CLI/registry lane, consume the child before answering, and preserve child/Parent metrics separately. Quality against J1–J10 precedes Parent-context, total compute, cost, and wall time.

Artifact root: `/tmp/lh-sol-parent-luna-child-topology-ab-r1-20260904`. Preflight passed with Parent configs explicitly pinned to Sol Medium, delegated-child route pinned to Luna Medium, three equal tracked trees, package/tool availability, zero preexisting sessions/statuses, and exact prompt/contract hashes. Contract SHA-256 is `4ef8ba6002abdb16dd6390c0e25e761a145aaac7400cc2d530bb94610ffa358f`; preflight SHA-256 is `cfa9cd05811393e168c8e14e392a488caa8f9add4b688ce062359c32efedd66a`. The sequential pair was dispatched as `sol-luna-topology-ab`.

This approval covers exactly two Parent sessions plus one Luna Medium child. It does not authorize another child, retry, High/XHigh, persistent Parent/child defaults, Reader/base-rule/read-batch integration, commit/push/release, or graph migration.

#### Discovery capture — actual topology approval

- DDD/SDD/BDD/TDD/ADR/SSOT: no active delta before the result.
- Planning: updated with the corrected Parent identity, actual two-arm topology, model-session ceiling, quality-first gate, source/metric boundaries, artifact root, and live dispatch.

The pair completed once in `167.593s` with exact identities, two Parent sessions, one child session, no fallback/retry, no mutation calls, and all three tracked source trees preserved. The runtime-complete status does not make the delegated topology admissible:

| Output | Score | Critical | Protocol |
|---|---:|---:|---|
| Direct Sol Medium Parent, delivered | `17/20` | `4/4` | PASS |
| Delegated Parent, transport-selected output | `0/20` | `0/4` | FAIL — discovery capture only |
| Delegated Parent, recovered pre-gate answer | `16/20` | `3/4` | diagnostic only |

The exact Luna Medium child completed one successful model attempt and its `3,319`-byte `subagent-notify` payload reached the Parent before synthesis. The delegated route nevertheless failed three frozen gates: the Parent emitted a shell-quoting syntax error and continued despite the terminal-on-failure rule; the child requested `1,400/1,200` lines; and the post-response discovery-capture gate generated a second assistant answer, so `pi --print` delivered only the `408`-byte capture instead of the substantive Parent answer. The recovered answer remained below the direct control, partially verified the live lazy CLI/registry surface, and still omitted the manifest's retired-history overwrite role.

Performance is diagnostic only. Direct versus delegated Parent-only versus Parent+child was: wall `56.559s → 110.889s`; turns `5 → 10 → 14`; tools `8 → 10 → 18`; Parent input `55,313 → 41,707` (-24.60%); Parent peak input `25,410 → 13,468` (-47.00%); provider total tokens `122,478 → 303,006 → 383,105`; and reported cost `$0.35820300 → $0.43131300 → $0.44116552`. Thus the smaller Parent input did not translate into lower cumulative context, total compute, cost, or wall time.

Actual Sol Medium Parent plus generic Luna Medium `delegate` is therefore `NO-GO` for this broad-audit sample. Luna Medium sufficiency was not demonstrated, and High/XHigh must not be launched automatically. This is not a rejection of the accepted dedicated Reader architecture: the current package did not expose that Reader or its join/debt bridge. Sol Medium Parent direct reading remains only the deployed fallback until the Reader slice is implemented. Before any new topology run, dedicated Reader registration, content-bearing join, cumulative child budget handling, failed-tool terminal behavior, and post-response final-output preservation need a separately approved implementation.

Artifact root: `/tmp/lh-sol-parent-luna-child-topology-ab-r1-20260904`; analysis SHA-256 `e533221bab5982b365a195ff34c62a59ca576582ca989f55968bfc47d287475d`; Parent evaluation SHA-256 `9cb7f1d213a5a39976ba03235225d1394696d3a0eac7e339a05e5cb5f9a73497`; terminal SHA-256 `5926147116d9fcfd25a5794bd1f5d0c394cf20d35e104ca1a8306e5e1f9d1d13`; report SHA-256 `e02a773ccf0cea4d5b0a0ec66d37338e2b9750c5b8518d740b991a6cd657e04c`; manifest SHA-256 `a63b5eb93cca86bc301cc9adb93ced843df26bc707cd549a6ddc0a96a6e05802` (`42` files).

#### Discovery capture — actual topology outcome

- DDD: none; no domain vocabulary changed.
- SDD: candidate — any future Parent/child contract must define child budget arithmetic, failed-call termination, custom-message result join, and final transport selection; no deployed contract changed.
- BDD: candidate — a post-response capture follow-up replaced the designated `--print` answer; preserve as future behavior evidence rather than implementing now.
- TDD: candidate — future approval may add regression cases for the three failed boundaries; no test record changed.
- ADR: candidate — the topology remains unselected and no permanent model routing was promoted.
- SSOT: none; no persistent model/default/settings mutation.
- Planning: updated here with immutable treatment identity, quality/protocol outcome, directional metrics, artifact hashes, terminal no-go, and renewed execution gate.

### Calibration closure corrected — temporary fallback, dedicated Reader target reaffirmed

The earlier `안전 라우팅 확정` disposition closed model-effort escalation, but it must not be read as changing retrieval ownership back to the Parent. The user explicitly corrected that subagent-based reading was already selected and the system must be made to fit that architecture.

Accepted target:

- Parent treatment remains exact `openai-codex/gpt-5.6-sol:medium` and retains decisions, mutation, integration, validation, and final-answer ownership.
- One dedicated `lazy-harness.record-reader` subagent owns complete map-first canonical `.lazy-harness` retrieval for a Reader-managed work unit.
- The Parent concurrently owns source/tests or an immediately needed behavior lane, then waits for the content-bearing Reader packet before plan/mutation/completion.
- A completion-only wait acknowledgement is not the join. The packet must carry `LAZY_HARNESS_READER_RESULT: complete|incomplete|conflict`, policies, facts, conflicts, missing information, and record paths into Parent context.
- `complete` replaces duplicate Parent record reads; non-complete/missing/mismatched/budget-exceeded/steered results use bounded Parent fallback.
- The caller-visible Parent answer must survive post-response advisories. In Pi text/print mode, an advisory-only last response is delivery failure.
- Luna Low remains the bounded Reader-model candidate from the quality result; Luna Medium/High/XHigh has no selected role and no escalation is approved.

At the correction/design checkpoint, main remained transitional and did not meet the target: `packages/lazy-harness-pi/agents/` was absent, the package manifest had no Reader registration, direct Parent debt remained deployed, and the 2026-09-04 run manually used a builtin generic `delegate`. That immutable run confirmed child content reached Parent before synthesis, then exposed separate Parent-to-caller print-mode loss.

Contract/TDD design was updated in `.lazy-harness/behavior/llm-owned-record-retrieval.md`, ADR 0055, `.lazy-harness/spec/platform/search-read-debt-contract.md`, `.lazy-harness/spec/platform/pi-agent-package.md`, `.lazy-harness/tests/pre-action-search-evidence-guard.md`, and `.lazy-harness/tests/pi-agent-package.md`. It covers package Reader registration, asynchronous parallel lanes, content-not-ack join, Agent Contract v1 read-only completion, cumulative budget/fallback, steer invalidation, and primary-answer preservation across print/TUI/JSON/RPC modes.

That design-only approval did not itself authorize an agent file, manifest, extension, guard, prompt, model run, commit/push/release, beacon work, or graph migration. A later explicit option selection authorized the isolated full implementation described below.

#### Discovery capture — Reader architecture correction

- DDD: none; existing Reader/Parent/join terms remain sufficient.
- SDD: updated for Reader resource/result/join/output contracts.
- BDD: updated for content-bearing join and caller-visible answer behavior.
- TDD: updated with planned failing-to-passing fixtures and full layer matrix; no new passing claim.
- ADR: updated because the user reaffirmed Reader ownership after the generic-delegate result was misinterpreted.
- SSOT: none; deployed settings/enforcement remain transitional and unchanged.
- Planning: corrected here so direct Parent reading is only a temporary fallback and the dedicated Reader remains the selected target.

### Dedicated Reader runtime v1 — isolated full implementation

The user selected **격리 worktree 전체 구현**. Worktree `/tmp/lazy-harness-reader-runtime-v1` on branch `work/reader-runtime-v1` was created from clean main `58fbcbf5e9d632bf9b0e7a87857ad8ed05f01f7b`; main dirty state was not reset, cleaned, staged, or absorbed. Nine current Reader design/ownership records were copied before source mutation, and the linked `agent-owned-target-context-transition` BDD was added unchanged when record-lint proved ADR 0055 required it.

Implemented coherent slice:

- `packages/lazy-harness-pi/agents/record-reader.md` — simple `record-reader/reader-join-v1`; complete overview, self-selected drill-down, canonical record reads, cumulative `8/1600` role ceiling, failed-tool stop, `complete|incomplete|conflict` packet; no source/mutation/validation/recursion/output-file/proof machinery.
- `packages/lazy-harness-pi/package.json` — exposes `./agents` through `pi.subagents.agents` and `pi-subagents.agents`; no OMP-subagent claim.
- `.lazy-harness/AGENTS.md`, `on-message-received.sh`, package prompt, and package README — Reader-first path, explicit Luna Low/Agent Contract v1 launch guidance, Parent source/test lane, content join, and bounded direct fallback.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — `ReaderRunState`, exact launch envelope, run/wait liveness tracking, pending-action barrier, explicit `lazy_reader_join`, root revision/evidence epoch/canonical path/fingerprint checks, cumulative budgets and zero failed calls, work-unit reuse, steer invalidation.
- `check-read-debt-permit.py` and `check-search-performed.sh` — exact successful join satisfies both current and legacy evidence paths; incomplete/error joins do not.
- `agent_end` output safety — exact `ctx.mode === "print"` preserves substantive stdout and emits advisory to stderr without a second assistant turn; non-print modes retain bounded follow-up.
- `.lazy-harness/scripts/self-test.py` — package/resource/no-proof checks, Reader launch/join/budget/fallback/reuse/steer fake runtime, complete-join allow vs incomplete-join deny, and print-mode stderr separation.

Focused revalidation is green after all review fixes: TypeScript bundle, Python/shell/JSON syntax, `check_pi_package_layout_and_contract`, and `check_tool_execute_before_hook` (`15` scenarios). The independent reviewer re-read refreshed map/drill/current diff, verified all former P1/P2 seams, and returned `No issues found` / isolated merge verdict `OK`. The final standard attempt 2 then passed in `173.797s`, including full self-test `173.216s`. Live model/package-discovery smoke and main integration remain intentional residual gates. Evidence: `.lazy-harness/evidence/dedicated-reader-runtime-v1-20260906.md`.

No model run, main integration, local commit, push, release, persistent model default, Reader proof/admission helper, `read_batch`, beacon/holdout action, or 37-row graph migration occurred.

#### Discovery capture — Reader runtime v1 implementation

- DDD: implementation status linked to existing Reader/Parent/join terms.
- SDD: package and search/read-debt contracts updated with actual symbols and behavior.
- BDD: scenarios 9–9d have an isolated implementation.
- TDD: focused and full standard fixtures pass; live model gate remains explicit.
- ADR: ownership unchanged; isolated implementation status updated.
- SSOT: exact successful join now satisfies isolated enforcement while direct fallback remains.
- Planning: updated here with worktree identity, source surface, reviewer findings/fixes, independent `OK`, final standard pass, and remaining live/integration gates.

#### Standard validation attempt 1 — failed, corrected without retrying outcomes

The first final `lazy validate --plan standard` ran once and failed only in full-self-test. Diagnostic capture identified D06 concrete-provider text in executable self-test code and the missing canonical `First grounding only` reminder phrase; two doctor failures were the same D06 cause. Code-level model validation now binds any explicit launch model to the task `model:` field while package grammar selects Luna Low, the self-test uses a neutral fixture model, and the hook retains the canonical phrase. Focused doctor/message/package/guard checks passed, then standard attempts 2 and 3 passed. Attempt 1 remains immutable failed evidence.

#### Live canary R1 preflight — superseded before model launch

The user approved exactly one fresh Sol Medium Parent → Luna Low dedicated Reader canary with no retry and no main integration. R1 was prepared at `/tmp/lh-reader-runtime-live-canary-r1-20260906` with a clean synthetic source, exact package/model availability, contract SHA-256 `007fcfa7cb090c1a47001b9bc0c6b7f8262634e16caac802ad21a4f32968a54c`, and preflight SHA-256 `b1bf6176dbc557421a5ce75d9d8ad98d9a6f34ce7a41c96075433b519c084843`. No model session started.

Pre-launch source review found a real prerequisite gap: the dedicated Reader's `systemPromptMode: replace` role would still receive the Parent package's `before_agent_start`, tool, context, and `agent_end` lifecycle injection. R1 was therefore sealed `SUPERSEDED-BEFORE-MODEL` rather than consuming the approved canary on a known-invalid setup.

The isolated implementation now detects `LAZY_HARNESS_ROLE: record-reader/reader-join-v1` through `RECORD_READER_ROLE_MARKER`, records that separate process root in `readerRuntimeRoots`, and bypasses Parent lifecycle handlers only inside the Reader process. A fake-runtime fixture proves Reader isolation and proves a normal Parent on the same root remains active. Focused and final standard validation passed before R2; R1 remains immutable and is not a retryable run.

#### Live canary R2 — terminal incomplete, delivery/join safety passed

R2 at `/tmp/lh-reader-runtime-live-canary-r2-20260906` consumed the one approved live allowance with one exact Sol Medium Parent and one exact package-discovered Luna Low Reader. Contract SHA-256: `a862ad2fb3751fa1e2d2fda71ff6432b597d3d692515e673b710adf6cad7480c`; preflight SHA-256: `16bb781569278e58f309e734053391098227b7031b6ee526bd8dd699f566f3cb`; 25-file artifact manifest SHA-256: `1887f55e6f597dd7ea27e85bac1ada571e82dff82e374685a8f7fc8b0f36ca3f`.

Confirmed working: package agent discovery; exact fresh Agent Contract v1 launch; Reader lifecycle isolation; exact first complete overview; Reader-selected map/record lane; one content notification before join; zero duplicate Parent canonical reads; honest `incomplete` join; no fallback/retry/mutation; source preservation; and print primary stdout with advisory stderr/no second assistant response.

The canary is not a functional or quality pass. Reader used five reads but requested `350+280+280+220+220=1,350` lines against `1,200`, so it returned `LAZY_HARNESS_READER_RESULT: incomplete`. Parent correctly stopped without a policy answer. The Parent's parallel source lane also delivered zero evidence: a safe source `rg` was false-blocked because Python `READ_ONLY_SHELL_RE` lagged TypeScript, then a compound `printf`/`find` follow-up was treated as an action and blocked by the pending join. Original `parentSessionCount=2` is a recursive runner measurement error; actual topology was one Parent plus one nested Reader.

No semantic score or performance promotion is admitted. Diagnostic totals only: `63.982s`, 11 combined turns, 13 tools, 161,900 provider tokens, `$0.23108784`. Canonical evidence: `.lazy-harness/evidence/dedicated-reader-live-canary-r2-20260906.md`.

The user selected a static correction, not a rerun: bind `maxLinesPerRead=floor(maxRequestedLines/maxReadCalls)` through task/role/launch/join (R2 → `200`) and align safe Parent source inspection. Any new live canary requires a new option/approval.

#### R2 static correction adversarial review

The implementation now binds derived `maxLinesPerRead` plus `maxObservedReadLimit`, requires a positive internally consistent complete ledger, retains a dedicated Reader-child tool boundary, and discards all pre-join evidence after non-complete or errored-complete joins. Parent pending-safe shell use is deliberately narrow: native read/grep/find or simple shell grep/rg with head/tail/wc only; chaining, redirection, substitution, shell find/tree, git write-output forms, `rg --pre` including quoted/escaped variants, write-capable filters, and nested namespaced bash remain actions.

Adversarial reviews were preserved rather than overwritten:

- `c95c0dab` found compound/nested shell bypass, pre-incomplete source evidence satisfying fallback debt, and missing over-observed/failed-call tests; fixed.
- resumed review `f0234446` failed before review with `Cannot read properties of undefined (reading 'create')`; preserved as reviewer infrastructure failure.
- `9c85790c` found shell find/delete and write-capable filters; fixed.
- `453aa92a` found write-output options on tree/git; fixed by narrowing base commands.
- `172c7842` found unsafe syntax hidden in an optional `cd` operand; fixed by validating the operand before stripping.
- `b596b5a2` found quoted/escaped `rg --pre`; fixed through dequote/backslash normalization and rejecting all `$` expansion.
- `5d390957` found Reader-child unrestricted bash, errored-complete fallback evidence retention, and impossible zero-read ledgers; fixed with a dedicated child tool allow boundary, failed-join truncation in both current/legacy guards, and positive/path/count/max consistency checks.
- `6b366bed` found the legacy session cache was checked before terminal Reader joins and exact fresh `lazy map` was not recognized after reset; fixed by truncating/invalidation before the cache fast path and adding cache seed/clear/recovery scenarios.

Focused package, generic read-debt, and 19-scenario hook checks pass after these fixes. Final independent blockers-only review `7bd36fb6` returned `No issues found` / isolated `OK`. Standard validation passed (`76.201s`, full self-test `75.869s`); no model rerun or main integration is authorized.

#### Discovery capture — post-R2 static closure

- DDD — `none`: no independent domain vocabulary or rule delta.
- SDD — `updated`: child tool, complete-ledger, shell, and fallback/cache contracts.
- BDD — `none`: no independent user-visible flow delta.
- TDD — `updated`: adversarial package/debt/hook regressions plus independent review and standard validation.
- ADR — `none`: Reader ownership and fallback decision unchanged.
- SSOT — `updated`: isolated enforcement is static-green; main activation/integration remains gated.
- Planning — `updated`: this lineage preserves every finding, fix, reviewer failure, and remaining approval boundary.

All facts are confirmed; no candidate/draft queue entry is needed. No discovery-capture step is skipped.

#### Fresh Reader canary proposal — planning approved, execution not approved

User selected `새 canary 계획 (Recommended)`. This authorizes planning only. The following is a proposal, not a launch receipt or an approved experiment contract.

1. Prepare a fresh, separately identified one-shot run from the corrected isolated source. Preserve all R1/R2 artifacts and the existing static closure archive unchanged. Bind actual source-file hashes as well as Git revision, because this worktree contains uncommitted changes. Do not reuse or overwrite an existing run directory.
2. Use one fresh exact Sol Medium Parent and one package-discovered Luna Low Reader, with fresh sessions, explicit model/thinking, Agent Contract v1, acceptance/output/artifacts disabled for the read-only child. No escalation or retry. Reader chooses canonical targets from complete overview; Parent does not preselect or duplicate those record reads.
3. Proposed task: explain current bounded-validation policy and verify its implementation through the Parent source/test lane. Reader supplies the policy records; Parent gathers independent source/test evidence while Reader is pending. The final prompt and claim checklist must be frozen and presented before execution approval.
4. Proposed Reader budget: 6 body reads, 1,200 requested lines total, 200 lines per read. Audit actual tool calls, including maximum observed limit and failed calls, rather than trusting packet counters alone.
5. Preflight before any model launch: resolve exact available model identifiers without substituting; verify package discovery, source hashes, prompt/checklist, fresh session paths, and child/Parent runtime wiring. TypeScript dependency-resolution diagnostics remain a validation limitation: successful Bun bundling is not a clean TypeScript typecheck. Do not label these resolved solely because they were deferred in the supervising session.
6. Functional PASS requires actual Reader content before join, a valid complete join, positive consistent ledger, zero failed tools, source-lane evidence delivered before join, no duplicate Parent canonical reads, no mutation, and substantive Parent stdout with advisories separate. Incomplete/conflict/error/budget failures stop the run and are terminal non-PASS; do not recover a failed canary by silently adding fallback reads or another child.
7. Score the frozen claim checklist for correctness, omissions, unsupported claims, uncertainty, and current/history boundaries before reporting efficiency. All critical claims must be correct with no material unsupported claim. Record wall time, turns, tools, tokens, and combined Parent/Reader cost only as diagnostic observations; this single run is neither an A/B comparison nor proof of performance improvement.
8. After an explicit execution approval, prepare/run at most that one approved canary and capture its outcome under a new identity. Main integration, activation, settings, commit, push, release, and the 37-row graph migration remain separately gated regardless of outcome.

##### Discovery capture — fresh canary planning

- DDD — `none`: no new domain concept.
- SDD — `none`: existing Reader/join contract is unchanged.
- BDD — `none`: existing parallel record/source scenario is unchanged.
- TDD — `candidate`: proposed live acceptance/checklist above awaits approval; not a completed regression result.
- ADR — `none`: ownership and routing decisions unchanged.
- SSOT — `none`: no settings or authority change.
- Planning — `updated`: planning-only approval, proposed protocol, diagnostic limitation, and execution boundary captured here. This planning section owns the unapproved proposal; no duplicate candidate record is needed.

##### Frozen R3 question and checklist — preparation only

After the user's request to continue, exact inputs were prepared at `/tmp/lh-reader-canary-r3-preparation-c2vytczu` without launching a model or overwriting any historical artifact.

- `prompt.md` SHA-256: `c370086ac3f0139142f487c235af2d431fdad8dc0871ce91fe44f78e689ca561`.
- `checklist.json` SHA-256: `a9b008a32f91d907e0be8770e5d0e48d39547e767c2559f0675cb2ef96b1198b`.
- `preparation.json` binds actual current source hashes plus revision and reports `PREPARED-NOT-LAUNCHED`.
- Exact Sol/Luna model names were listed by the installed CLI; this is not authentication, runtime-success, or package-discovery evidence.
- Eight critical criteria cover edit cadence, fast/full distinction, plan budgets/release gate, direct-test permission, reuse, invalidation, source verification, and uncertainty. Rubric remains 2/1/0/-2; all critical claims must score 2 with protocol compliance.
- Parent is limited to two body reads/500 requested lines; Reader to six/1,200/200. Reader chooses its own record targets. Do not expose the evaluator checklist to either participant.
- Remaining preflight: isolated runtime/package discovery and actual transport identity. No model allowance consumed. Existing TypeScript dependency diagnostics remain unresolved; no clean typecheck is claimed.

Discovery capture remains Planning `updated`, TDD `candidate`, DDD/SDD/BDD/ADR/SSOT `none`; exact inputs are a preparation artifact, not promoted runtime policy or a successful live result.

##### R3 one-shot execution approval and dispatch

The user subsequently selected `사전점검 통과 후 1회 실행 (Recommended)`, including the stated TypeScript diagnostic limitation. This supersedes the planning-only launch restriction for exactly one fresh R3 canary; it does not authorize retries, R2 repair, main integration, or release.

- Approval and frozen source manifest: `/tmp/lh-reader-canary-r3-preparation-c2vytczu/execution-approval.json` and `source-manifest.json`.
- Preflight passed unchanged prompt/checklist/source identities, package-discovered Reader, exact listed models, credentials presence, and empty run/session directories. This does not itself prove successful authentication or model execution.
- One-shot launcher uses exclusive `run/started.json`, exact Sol Medium Parent, and a 900-second execution deadline; the prompt permits exactly one Luna Low Reader.
- Dispatched through interactive shell `ember-dune`. Runtime artifacts remain in that fresh root. Result and exact actual transport identities require transcript audit; no PASS is claimed at dispatch.
- Discovery capture: Planning `updated`; TDD `candidate` pending actual result; DDD/SDD/BDD/ADR/SSOT `none`. Historical R2 and existing frozen archives are unchanged.

##### R3 terminal outcome — no retry

R3 completed process execution but is **TERMINAL-INCOMPLETE — no retry**. Actual topology was one Sol Medium Parent plus one Luna Low Reader (run `342a08d1-fff2-4be8-b084-de2354908670`). Wall time 86.228s; 153,288 combined provider tokens; reported combined cost $0.17487652. Manifest-bound source bytes were preserved; no substantive answer was delivered.

Parent added a total-tool `hard:6, block:*` cap, consuming five calls on discovery/identity before body reads; only one of six requested Reader reads succeeded. The requested 1,200-line/per-read-200 budget was not exceeded. Parent source inspection used forbidden `2>/dev/null`, so the guard correctly rejected that command; no safe-rg false block is established. After an initial terminal response, a late child notification caused incomplete join and a second terminal response, so literal stop semantics were also not satisfied.

Primary evidence: `.lazy-harness/evidence/dedicated-reader-live-canary-r3.md`; fresh-root `analysis.json` and `terminal-outcome.json` preserve raw-session-derived findings. Static review success and process exit 0 are not live functional PASS.

Candidate-only follow-up: clarify total-tool versus body-read budget, constrain Parent source commands to allowed forms, and settle stop/late-notification behavior. No remediation or new live run is approved by the consumed one-shot allowance. Discovery capture: TDD/Planning `updated`, DDD/SDD/BDD/ADR/SSOT `none`; candidate remediation stays here, not silently promoted to policy.


##### User-approved R3 remediation — isolated source change

The user explicitly requested fixing confirmed problems and continuing. Implemented in the isolated worktree: reject explicit Reader `toolBudget` before launch; task-envelope fields own body limits; Parent grammar prioritizes native source tools and explicitly prohibits redirection; pending failures drain child completion before one final and avoid incomplete join in no-fallback canaries. This preserves safety guards rather than weakening them to accept a blocked command. Runtime result suppression is not claimed: final-response cadence is distributed guidance, protected by prompt checks.

Primary regression record: `.lazy-harness/tests/pi-agent-package.md#r3-launch-budget-remediation-regression`. Discovery capture: SDD/BDD/TDD/Planning updated; DDD/ADR/SSOT none. R3/R2 and frozen artifacts remain untouched. Focused package, generic debt, and 19-scenario hook checks passed. Independent review `95c84821` returned `No issues found` / `OK with notes`; final standard checkpoint remains. No fresh live success or main integration is claimed. TypeScript module/type resolution is still not clean and is not dismissed by successful bundling.


##### R4 terminal result and native-notification repair

R4 is terminal-incomplete, not retried: `/tmp/lh-reader-canary-r4-kcrjrt6k`, manifest `d8fedd2120f5dadb68c344b94f1f5cba6165d0523280cb773ca74288f89885b9`. Reader succeeded at six reads/1,200 requested lines with zero failed calls and delivered complete content. Parent guessed a nonexistent source path, continued after its error, then join rejected delivered content because the runtime watched only legacy subagent_wait. Later retries also violated the no-retry protocol; no quality PASS.

The real adapter defect has now been corrected in the isolated worktree: `observeReaderPacket` handles typed native subagent-notify during context, matches active root/revision/epoch and complete marker, and sets content receipt before the context early return. One launch per epoch prevents same-epoch ambiguity. Complete join requires delivered content, not legacy wait acknowledgement. Tests cover notification-only success, stale/wait-only denial, duplicate launches, and the existing budget/path failure cases after valid notification. Parent guidance now requires discovering existing source paths before reading.

Independent review `535a2bf3` stopped without findings because map/diff files were not available to its restricted tools. Resume `5f6cd540` failed with `Cannot read properties of undefined (reading 'create')`. Fresh review `ec84d66d`, supplied materialized map/drill/exact diff, returned `No issues found` / `OK`. These are separate review outcomes; none relabels R4.

Evidence capsule: `.lazy-harness/evidence/dedicated-reader-r4-follow-through.md`. Discovery capture: SDD/TDD/Planning updated; DDD/BDD/ADR/SSOT none (restore the already selected delivery contract). Main integration and subsequent live success remain unclaimed. Source-path choice and protocol adherence by the Parent remain behavioral risks.


##### R5 terminal and static correction

R5 `/tmp/lh-reader-canary-r5-oxzfxc9q` is terminal-incomplete, no retry. Parent correctly omitted total-tool budget, but native grep/find were not activated by the launcher. Reader's five absolute canonical operands were rejected, and a later relative read succeeded; actual requested ledger was six/1,200 while reported lines were 1,000. No source verification or successful join/quality result.

Fixed native Reader path normalization for exact-root absolute read/grep operands, preserving relative join identifiers, traversal/layer restrictions, and sibling-root rejection. Added executable path cases. Actual zero-model SDK preflight `/tmp/lh-reader-tool-preflight-88q_8qyl/result.json` confirms explicit `read,grep,find,bash,subagent,lazy_reader_join` tools all active. Future live launch must use this explicit allowlist and assert runtime tool availability, not infer it from package discovery. No new live run is authorized by R5's consumed one-shot allowance.

Primary regression: `.lazy-harness/tests/pi-agent-package.md#r5-absolute-operands-and-tool-surface-regression`. Discovery capture: SDD/TDD/Planning updated; DDD/BDD/ADR/SSOT none. R5 and earlier frozen artifacts/main preserved. Independent review `295ce7d7` returned `No issues found` / `OK with notes`; focused fixture and strict resolved extension typecheck passed. Final standard checkpoint remains. No live run after R5.
