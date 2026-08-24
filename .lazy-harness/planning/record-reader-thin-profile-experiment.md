# Planning — Record Reader Evidence-Loading Pilot (Thin-Profile Experiment History)

Status: compact v2 static validation and one Luna High rule-recall canary are admitted with semantic fidelity retained and 3,143 characters below target; one hash-order deviation remains, and claim/main integration/further runs stay separately gated
Date: 2026-08-22
Updated: 2026-08-24
Layer: Planning
Primary ADR: `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md`

## Rule digest

- Status: advisory
- Layer: Planning
- Scope: transient-plan
- Aliases:
  - Record Reader evidence loader
  - records-only subagent
  - Work Packet
  - scoped retrieval child
- Applies when:
  - implementing or measuring the package-owned Lazy-Harness Record Reader
  - delegating Parent-selected canonical record loading without source or mutation authority
- Must:
  - preserve full Lazy-Harness grammar, complete overview discovery, governing reads, candidate-map approval/reopening, and semantic authority for Parent and every non-Record-Reader role
  - select the Reader only through its package-owned v2 system-prompt marker and require explicit packet `mode`, never user-text classification
  - require root/revision/canonical-snapshot/overview/epoch identity, Parent facets/inventory/concrete nodes, hard budgets, and keep the Reader records-only, read-only, non-recursive, and artifact-free
  - make candidate-map return unverified evidence questions plus input-relative coverage/overlap/cycle proposals; make claim-evidence load one Parent-approved bundle with path/hash/range provenance
  - return `needs-remap` for newly discovered questions/overlap/dependency changes and overflow for budget exhaustion; never false-complete or recursive fan-out
  - keep Parent responsible for map approval, packet inspection, freshness checks, decision-critical rereads, semantic decisions, and all mutation/validation
- Must not:
  - promote a model/runtime/default, delegated read-debt bridge, Source Verifier, Record Writer, merge, push, sync, or release from this pilot
  - treat historical v1/faithful profiles as current package roles or infer a production default from one benchmark task
- Record completion:
  - implementation results update this Planning record; contract and regression deltas update the linked SDD/TDD
- Related records:
  - `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md`
  - `.lazy-harness/spec/platform/pi-agent-package.md`
  - `.lazy-harness/tests/pi-agent-package.md`
  - `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`

## Confirmed scope

The 2026-08-22 thin/faithful prompt experiments remain historical evidence. On 2026-08-23 the user confirmed the architecture and selected **Reader only** for the next isolated implementation slice:

1. Parent owns operating/development rules, complete lean overview discovery, governing reads, options, candidate-map approval/reopening, decisions, durable writing, mutation, and validation;
2. one v2 Record Reader receives a mandatory mode and bounded root/revision/snapshot/overview/epoch/facet/concrete-node/budget packet, then reads canonical records only;
3. candidate-map proposes unverified evidence questions and bundles; claim-evidence loads one Parent-approved bundle and returns direct path/hash/range provenance or remap/overflow;
4. Parent waits for packets and selectively rereads governing, conflicting, high-risk, decision-critical, and sampled evidence;
5. this approval implements the guarded contract and regression boundary only. Automatic scheduling, a real parallel pilot, source verification, writing, delegated read-debt recognition, model defaults, merge, and production promotion remain out of scope.

Parent and ordinary subagents retain the full `.lazy-harness/AGENTS.md` path. The package exposes one Reader role rather than the historical v1 and faithful profile matrix.

## Current v2 guarded two-mode design

- runtime name: `lazy-harness.record-reader`; marker: `LAZY_HARNESS_ROLE: record-reader/v2`;
- compact v2 Parent envelope requires full identity/scope plus `contractDigest`, F/I/N/V catalogs, allowed layers, governing reads, risks/exclusions, operational budgets, 6k output target, and 12k hard cap;
- candidate-map returns compact Q questions, one F/I coverage map, one R/range table, N/V refs, normalized overlap/dependency/bundle fields, and non-authoritative routing; it never returns task-global `complete`;
- claim-evidence binds approved map/bundle/Q/F/N/D/owner scope in the envelope digest and returns compact claims, conflicts, remap fields, parentRead R ids, and verification V ids;
- new questions or changed overlap/dependencies force `needs-remap`; output above soft target warns, inability to fit hard cap forces `overflow` with split detail; recursive fan-out and evidence trimming are forbidden;
- runtime ceiling permits exact concrete-node map, canonical body read/hash, and bounded one-layer grep only; Reader overview, source, mutation, output artifact, external tools, user decisions, and recursion are blocked;
- Reader results never mutate or satisfy Parent work-unit evidence. Parent approves every bundle and selectively rereads before deciding or mutating.
- Contract/enforcement boundary: compact schema/digest/reference/coverage/soft-hard admission is machine-enforced; the extension still hard-enforces only trusted role, records-only tools, and Parent lifecycle isolation. Semantic correctness remains Parent-owned.

## Architecture review and approval

Three independent read-only reviews agreed that one Reader with two explicit modes is the least-drifting reversible design, but the original `scope-map` wording was unsafe because the same child could invent its own coverage universe and silently omit a claim. The approved correction therefore:

1. renames the first stage `candidate-map` and limits it to unverified evidence questions;
2. makes Parent-supplied facets/inventory entries the conserved input-relative coverage basis;
3. requires exact revision plus canonical working-set/overview/evidence-epoch identity and per-record working-tree content hashes;
4. reopens the map at a fixed point when claim-evidence discovers a new question, overlap, dependency, conflict, or overflow;
5. groups cyclic/overlapping evidence closure instead of equating record links or differently worded claims with independent DAG branches;
6. keeps Parent/direct or one-Reader handling as the fallback for small/high-overlap work; and
7. treats speed, token, cost, and admission thresholds as unproven until a separately approved frozen-root pilot.

Review verdict: guarded contract preconditions passed (`record-lint` 185/185, `lazy check`, `lazy validate --plan standard` with full regression, and no unresolved blocker/high/medium follow-up-review findings). On 2026-08-23 the user separately approved one conditional self-host real pilot; promotion remains `NO-GO`.

## Implementation review correction

Two independent implementation reviewers confirmed the concrete-map/canonical hash/read/grep runtime boundary and Reader-to-Parent lifecycle isolation, but found that the first draft overstated prompt clauses as runtime-enforced packet behavior and used weak phrase-only tests. The correction batch:

- explicitly distinguishes profile-contract semantics from extension hard enforcement and keeps machine packet parsing/counters/output validation deferred;
- replaces phrase-only checks with section-aware validation plus negative mutations for mode, snapshot, overview, exact tools, ceilings, false-complete, and remap clauses;
- parses the frontmatter tool list as exact `read, grep, bash`, closing the ineffective escaped-word-boundary check;
- exercises Reader `context` while Parent mutation context is pending;
- corrects stale SDD text that said reads/searches schedule context replay; and
- replaces the old project-rule-placement-only layer-completeness matrix with a package-wide matrix that links the Reader BDD/ADR and states actual LLM packet behavior is untested.

This correction does not add a raw-text packet parser or claim actual two-mode output fidelity.

## First guarded two-mode pilot — approved execution boundary

On 2026-08-23, after a read-only preflight and native option gate, the user approved **one conditional full pilot** in the isolated worktree. This approval is narrower than automatic fan-out or runtime promotion:

1. Target `/tmp/lazy-harness-record-reader-thin-profile` itself at exact revision and a freshly recomputed canonical working-set/overview fingerprint.
2. Ask for the current supported runtime/install/activation/rollback boundary after Jcode decommission, using six Parent-authored facets and six concrete canonical record nodes.
3. Run the same bounded `candidate-map` inputs twice in fresh sequential Readers: one per-run `openai-codex/gpt-5.6-luna:medium` and one per-run `openai-codex/gpt-5.6-luna:high`. Only `packetId` and `modelRoute` differ; there is no persistent model-default change. Both must conserve every supplied facet/inventory entry and propose exactly two sufficiently disjoint, dependency-safe bundles with no blocking gap, cycle, overflow, or unmapped item.
4. Parent compares protocol validity, coverage/question/facet conservation, provenance, overlap/dependency judgement, and decision-relevant omissions. Select Medium for both claim lanes only when it has no decision-relevant loss versus High and satisfies every admission criterion; select High only when it uniquely satisfies them. Material unresolved disagreement stops for a new user gate rather than merging packets.
5. If one route is selected, the Parent approves that route's exact question/facet/seed/dependency/shared-owner assignments, rechecks freshness, then runs exactly two `claim-evidence` Readers in parallel on the selected Luna level.
6. Stop without retry or automatic new wave on `invalid-packet`, `incomplete`, `overflow`, `needs-remap`, conflict, snapshot drift, prohibited tool attempt, child failure, one/single-reader routing, any bundle shape other than two safe lanes, or unresolved A/B disagreement.
7. Use an isolated `PI_CODING_AGENT_DIR` containing only the experiment package and Pi Subagents. Direct launch from the current parent environment is excluded because its global main package plus the worktree-local package can register duplicate extension tools.
8. Keep output files disabled for Readers, preserve the dirty worktree byte-for-byte, and have the Parent inspect final output, session/tool evidence, direct hashes/ranges, decision-critical/conflicting/sample records, and pre/post repository fingerprints.

This is a functional protocol/fidelity plus model-routing pilot. Candidate A/B timing, tools, tokens, cache, and cost are descriptive because sequential execution and cache state are not a controlled latency benchmark; there is no fresh Direct-Parent control arm, so no general speed, token, cost, or quality advantage may be claimed.

The initial Sol-medium transport attempt never launched a Reader. Its isolated launcher successfully listed the package agent, then intentionally returned `PRECHECK-FAILED` because the generated `get` management call used `id` instead of the required `agent` field. The repository was not inspected and this transport-only failure is not model evidence. Session: `/tmp/lh-record-reader-two-mode-pilot-20260823/sessions/--tmp--/2026-08-23T10-14-20-902Z_01a02e1d-33e6-7f2b-b165-6b744c05869c.jsonl`.

The earlier pre-approval fingerprint is navigation history only. The Parent recomputed and preserved revision `58fbcbf5e9d632bf9b0e7a87857ad8ed05f01f7b`, canonical working-set snapshot `sha256:d2080951954985b92832f50a0c86bacd6ca2a4a7dd6102dd4956c83a31c46b63`, overview fingerprint `sha256:83439053fc03d9e9f13b43821b2446f119f831e91cad8a1f0458d047b5a8d240`, and status fingerprint `sha256:c4da8bd806b824ae84226a229ebbcd9f2ef168ff9db390c2181058d12aca57ef` across both candidate runs.

### Luna candidate A/B result — stopped at admission

| Metric | Luna medium | Luna high |
|---|---:|---:|
| Run | `3514b52b-1c63-47e3-ba17-154717c7c9d6` | `76ff2068-0504-4920-b75a-ca7ae517ad3e` |
| Status / routing | `proposal-ready` / `single-reader` | `proposal-ready` / `single-reader` |
| Questions / bundles | 5 / 1 | 6 / 1 |
| Direct records / tools | 2 / 14 | 1 / 12 |
| Duration | 66.775s | 90.264s |
| Input / output / cache | 54,771 / 2,818 / 105,984 | 46,559 / 4,275 / 96,768 |
| Reported child cost | $0.01645548 | $0.01637716 |

Both arms echoed identity, conserved F1–F6 and I1–I6 with no unmapped input, kept questions unverified, map-drilled all six supplied nodes, returned matching direct content hashes, and performed no overview, source read, mutation, external call, artifact write, or recursive fan-out. Medium directly read ADR 0059 plus the Pi SDD and grouped five questions; High directly read ADR 0059, retained six finer questions, and made un-read/gap state more explicit.

Both independently rejected the requested two-lane split. Medium identified one strongly coupled ADR0059↔Pi-SDD closure; High identified two overlap groups still coupled through the shared runtime boundary. Parent honored the predeclared fallback instead of rewriting the map to manufacture parallelism. Therefore no Luna level was selected and no claim-evidence Reader ran.

Both first attempted the compound command `pwd && git rev-parse --show-toplevel && git rev-parse HEAD`; the runtime correctly blocked it, and each recovered with three exact allowed probes. This both verifies the hard guard and exposes a follow-up contract candidate: clarify three separate calls in the Reader prompt or separately approve a safe compound-probe allowance plus regression. No correction is included in this pilot result.

Evidence: `/tmp/record-reader-two-mode-pilot-20260823/comparison.md` SHA-256 `8c537283caa8704b4ce350074557bff58a013e9dc6cbe3d8183e5e3307e92dc3`; `/tmp/record-reader-two-mode-pilot-20260823/metrics.json` SHA-256 `6b30a1525c47c9a78be61166074a1a9e28d8e1b4f40dfcad3e3a36815db0179e`; raw packet/output/meta/transcript copies and `output-hashes.txt` are retained below that evidence root. Child-only candidate cost was $0.03283264. The isolated Sol transport launcher added $0.3784 and substantial elapsed overhead; this duplicate-package workaround is not representative of direct Parent routing. No Direct-Parent control arm exists, so no general efficiency or quality claim follows.

### Approved follow-up — separate probes plus single-bundle claim A/B

The user selected `Probe 수정 + Claim A/B` through a native option gate. This approval is limited to:

1. Change the Reader retrieval contract to require three separate shell calls—`pwd`, `git rev-parse --show-toplevel`, then `git rev-parse HEAD`—and explicitly forbid combining them with shell separators. Preserve the runtime denial of compound commands.
2. Strengthen section-aware profile mutation checks and fake-runtime checks so the separate-call instruction cannot silently regress and the exact three probes remain allowed while the compound probe remains blocked.
3. Update the Pi package SDD/TDD, this Planning record, ADR 0055, and graph for the confirmed correction; no new packet schema, tool allowance, or production policy is introduced.
4. Run focused package regression, record lint, `lazy check`, and one final standard/full validation before any new Reader launch.
5. Freeze a new root/revision/canonical-snapshot/overview/epoch identity after the correction.
6. Parent approves one normalized shared bundle with four questions: runtime/Jcode cutline (F1/F2), rollback/cleanup (F3), package/install/activation/root (F4/F5), and runtime/shared state isolation (F6). Seed nodes are ADR 0059, Pi package SDD, runtime/shared-state SSOT, and the Jcode decommission plan; one bundle owns all shared evidence.
7. Run identical fresh `claim-evidence` packets sequentially on `openai-codex/gpt-5.6-luna:medium` and `openai-codex/gpt-5.6-luna:high`; only packet id and model route differ. Budget: at most 3 direct records, 4 claims, 4 seed nodes, 14 tool calls, and 8,000 output characters.
8. Compare evidence fidelity, direct path/hash/range support, conflicts/supersession, new questions/remap, parentMustRead, gaps, tools, time, tokens, and cost. Stop on stale identity, blocked attempt, source/mutation/overview, overflow, or materially incomparable output. Do not infer a default or broader rollout from one bundle.

### Claim-evidence Luna A/B result — stopped

The Parent froze revision `58fbcbf5e9d632bf9b0e7a87857ad8ed05f01f7b`, canonical working-set snapshot `sha256:2b2b67f5b1624594239f3db6bce2812c0b687534579d541181f22a56d31987d3`, overview fingerprint `sha256:99721ba30d7adc9dded85f83244655c313d9225d0f0d4ec140f94358c51a7dff`, status fingerprint `sha256:c4da8bd806b824ae84226a229ebbcd9f2ef168ff9db390c2181058d12aca57ef`, and epoch `rr2pilot-20260823-e3`. The two packets differed only by packet id and Luna thinking route.

| Metric | Luna medium | Luna high |
|---|---:|---:|
| Run | `b28462eb-346d-48b2-84e4-505127f479b2` | `fd76b27b-3405-4cdd-b06f-e7d9c56a9c57` |
| Status | `incomplete` | `incomplete` |
| Direct bodies / claims | 2 / 2 (Q1–Q2) | 3 / 4 (Q1–Q4) |
| Returned content hashes / tools | 1 / 12 | 1 / 12 |
| Duration | 53.055s | 72.332s |
| Input / output / cache | 43,673 / 1,955 / 143,872 | 44,821 / 2,844 / 136,192 |
| Output characters / reported cost | 3,288 / $0.01395804 | 4,804 / $0.01510084 |

Both Readers attempted the prohibited `contact_supervisor` tool as their first call. The records-only runtime blocked both attempts before repository access. Each then followed the corrected probe contract exactly—`pwd`, git root, and HEAD as three ordered separate calls—and made no complete-overview, source, mutation, external-repository, recursive-subagent, or Reader-initiated output-file attempt. The predeclared blocked-attempt rule therefore stops this wave regardless of later evidence quality.

The launcher also supplied a runtime soft limit of 12 below the packet's declared 14-call ceiling. At call 12 both Readers were instructed to finalize before all directly read records were hashed. Medium returned Q1–Q2 after loading ADR 0059 and the Pi package SDD; High loaded ADR 0059, the Pi package SDD, and runtime/shared-state SSOT and returned Q1–Q4, but omitted multiple required common identity fields. Both correctly used a non-success status and disclosed missing provenance. High's broader evidence coverage is material descriptive evidence, but neither route uniquely passed; the approved selection rule therefore selects neither model and authorizes no retry or follow-on.

Post-run revision, canonical snapshot, status fingerprint, overview fingerprint, working-set file count, and dirty-entry count exactly matched the frozen pre-run values. Evidence: `/tmp/record-reader-two-mode-pilot-20260823/claim-ab/comparison.md` SHA-256 `0fab2e132135219f48a5bec962b87d3e3b35609bd640fc6d788d5046d5efd127`; `metrics.json` SHA-256 `b72e4b26ac9bc8986701b1a2e3ea571cd9b156e6e2c8dc8f2af41dc92da3bce3`. Full packets, outputs, metadata, transcripts, child sessions, launcher session, Parent overview, and pre/post snapshots are archived below that directory.

Residual candidates required another user gate: suppress the generic `contact_supervisor` surface/instruction for this records-only role rather than relying on denial, and align any runtime soft nudge with the packet's approved tool ceiling without increasing that ceiling.

### Approved controlled correction and one claim rerun

The user selected `Fix and rerun` through a native option gate. This new approval supersedes only the prior no-retry boundary for exactly one corrected repeat:

1. Disable Pi Subagents native supervisor/intercom coordination for each Record Reader child (`intercomBridge.mode=off`) so `contact_supervisor` is absent from prompt and effective tools; retain the Lazy-Harness role denial as defense in depth.
2. Set runtime `soft == hard == packet budget.toolCalls` (14 for this comparison). Do not increase the packet/role ceiling.
3. Update the Reader profile/reminder, package README, Pi SDD/TDD, ADR, Planning, graph, section-aware negative mutations, and fake-runtime leaked-supervisor denial. This is transport isolation, not a new Reader tool or model default.
4. Apply the Code Organization Profile observe-only: keep the reminder/test additions local to the existing Reader functions and package fixture; create no new architecture layer or shared helper.
5. Configure only the isolated pilot `PI_CODING_AGENT_DIR`, verify the effective bridge-off state without repository access, run one focused package regression, record lint, `lazy check`, graph/diff checks, and one final standard validation.
6. Freeze a fresh Parent revision/canonical-snapshot/overview/epoch identity, then rerun the same four questions, facets, three-record direct cap, four seeds, 14 tools, and 8,000 output characters sequentially on Luna medium and high. Only packet id/model route may differ.
7. Stop without retry or automatic follow-on on any stale identity, surfaced/blocked prohibited tool, overview/source/mutation access, overflow, incomplete result, missing required provenance, or materially incomparable output. A route is selectable only under the existing Medium-no-loss / High-unique-pass rule.

## Corrected claim-evidence rerun result — High uniquely passed

The Parent froze revision `58fbcbf5e9d632bf9b0e7a87857ad8ed05f01f7b`, canonical snapshot `sha256:96496509ab07605eadbbd339f49e8cd1317742c766fd39485a221409e8e1537f`, overview fingerprint `sha256:7a2ace0b04355647b69fc2a93513989824a17f8ec9373a47ec4febb43810f44b`, status fingerprint `sha256:c4da8bd806b824ae84226a229ebbcd9f2ef168ff9db390c2181058d12aca57ef`, and epoch `rr2pilot-20260823-e4`. The isolated Pi Subagents doctor reported bridge mode `off` and inactive. Each child also received `intercomBridge.mode=off` plus runtime `soft=hard=14`. The packets were identical after normalizing only packet id and model route.

| Metric | Luna medium | Luna high |
|---|---:|---:|
| Run | `9b3d3171-d5c9-4440-a88e-44b041321f14` | `ad1a328e-83e0-46ae-ac92-08c6d9b25bf3` |
| Status | `needs-remap` | `complete` |
| Direct bodies / claims / hashes | 3 / 4 / 3 | 3 / 4 / 3 |
| Tools / duration | 13 / 65.917s | 13 / 90.678s |
| Input / output / cache | 45,254 / 2,444 / 216,064 | 46,243 / 3,837 / 216,064 |
| Output bytes / reported cost | 5,554 / $0.01630488 | 5,978 / $0.01817428 |

Both children used exactly the same successful 13-call sequence: three ordered separate root/revision probes, four concrete-node maps, three canonical body reads, and one exact `git hash-object` immediately after each read. Neither received or attempted `contact_supervisor`; neither used overview, source/generated/session access, mutation, output files, recursion, broad search, compound probes, or external tools. All three record hashes matched, and post-run revision/snapshot/status/overview/working-set/dirty-entry identity matched the frozen pre-run values.

Medium opened `NEQ1-rollback-plan-detail` and returned `needs-remap`. Parent audit treats that as a conservative false-positive remap: the plan was already an approved concrete seed rather than a new out-of-bundle dependency, the three-record cap intentionally allowed one of four seeds under `notRead`, and primary ADR 0059 directly states the current rollback/cleanup boundary. Medium therefore remains a non-success route.

High returned all required identity/inventory fields, four directly supported Q1–Q4/F1–F6 claims, three path/hash/section records, valid not-read/conflict/gap/verification and `parentMustRead` lists, no new question/dependency/overlap/conflict/overflow, and a valid bundle-local `complete`. There is no unresolved factual disagreement between arms. Under the predeclared rule, High uniquely passed and `openai-codex/gpt-5.6-luna:high` is selected for any separately approved future Record Reader experiment. This is not a persistent default and launches no automatic follow-on.

Evidence: `/tmp/record-reader-two-mode-pilot-20260823/claim-ab-rerun/comparison.md` SHA-256 `4aa9aee1d807a7dd1283a1da22f033f3bb4cb42464ea3b02a4a30f91ab7d0cc7`; `metrics.json` SHA-256 `d9ae7b3b57b9ed8f6ac9093f0ac62acf77d2b6c0cc25a377315d4b6c743a7b4c`. Frozen packets, launcher, transport doctor/config, raw outputs/meta/transcripts/sessions, hashes, and pre/post snapshots are retained below that directory. Timing, tokens, cache, and cost remain descriptive only: execution was sequential, cache state was uncontrolled, and no Direct-Parent arm exists.

## Real-work High shadow result — NO-GO for main

The user approved `High 실전 검증`: use the selected Luna High route on one real self-host task, compare it with Parent ground truth, and present a main integration gate only if it passed. The Parent chose integration readiness for the current Record Reader v2 experiment, completed a fresh overview and governing/source/test baseline, froze revision `58fbcbf5e9d632bf9b0e7a87857ad8ed05f01f7b`, snapshot `sha256:6be5a4ab9c6d2c8f834421c0bc28213ac177cce3b3589b4a76b38cd6eef9761b`, overview `sha256:0de6e194bd3b3f13a6f5425a71a1db37121dcb07ccc278804645c35e07d58f07`, and epoch `rr2shadow-20260823-e5`, then launched one High `candidate-map`.

Run `ee79d90b-ee21-44ac-b5a8-6de717fc32d9` preserved every runtime boundary: bridge off, equal 14/14 tool limits, three ordered probes, all seven concrete maps, two canonical reads plus matching hashes, no prohibited attempt, and byte-identical pre/post repository identity. It conserved F1–F7 and I1–I8 into six useful unverified questions and correctly kept implementation truth with the Parent.

The packet is nevertheless inadmissible. It abbreviated both required freshness fingerprints and rendered the canonical snapshot prefix as `6be6e…` rather than the frozen `6be5a…`; exceeded the hard 6,000-character ceiling with 6,193 characters; reported `proposal-ready` and no overflow instead of a non-success outcome; and omitted the packet-required explicit `parentMustRead` inventory. Parent therefore rejects the candidate map, launches no claim-evidence follow-on, and returns **NO-GO for main integration** under the user's apply-then-merge-only-if-good criterion.

Evidence: `/tmp/record-reader-high-shadow-20260823/audit.md` SHA-256 `eef82ccc4719559f37fb092802c19268a1cecf71c05f60174ffc17fbcfea2fe3`; `metrics.json` SHA-256 `f8d90d1306df877cf6a7268a116b8f9c84289da4294f78a17b9519b404f85a2b`. Packets, launcher, raw artifacts/sessions, tool transcript, hashes, and pre/post snapshots remain below that directory. High remains the better experimental route from the A/B, but the component needs a separately approved correction for exact identity/output-budget/output-shape admission before another shadow or main gate.

## Approved machine-admission correction and exact shadow rerun

After the real High shadow exposed a false `proposal-ready`, the user selected **기계 검증 추가**. The approved bounded correction adds a strict per-packet Pi Subagents `outputSchema`, allows only its internal `structured_output` protocol tool while Pi Subagents' absolute schema/capture runtime paths are active, and adds `packages/lazy-harness-pi/scripts/record-reader-admission.ts` as a pure schema/admission helper.

The helper binds every frozen identity value with JSON Schema `const`, rejects packet budgets above the role ceilings, requires Parent-authored candidate coverage/exclusion inputs or claim question/facet inputs, builds a closed nested schema, independently revalidates the captured value, verifies exact coverage and authorized exclusions, binds question/claim/remap provenance and `parentMustRead` to `recordsRead`, counts compact `JSON.stringify` Unicode code points against the packet ceiling, and rejects success statuses inconsistent with gaps, overflow, unmapped coverage, missing facets/questions, or remap triggers. Its receipt validates packet shape and declared closure only; Parent semantic reads, source/test verification, integration, and merge authority do not move.

The correction remains limited to profile/reminder/README/manifest, extension internal-tool ownership, package SDD/TDD, deterministic candidate/claim/contract/adversarial/Unicode fixtures, ADR/BDD/Planning/graph, focused/final validation, and one rerun of the exact integration-readiness High candidate task with fresh identity. No automatic scheduler, retry beyond that one rerun, claim follow-on without an admitted candidate, persistent model default, merge, or production promotion is approved.

### Independent admission review and remediation

Fresh reviewer run `84f1e420-cc3b-4819-b6d5-89be5581ec9f` returned one blocker, two high findings, and three medium findings before any corrected live rerun. It found unenforced role ceilings (including a 10,000-character "valid" fixture), optional Parent coverage/claim inputs and unbound exclusions, no independent nested-schema validation in the Parent CLI, string-only remap questions without provenance, same-name `structured_output` allowance without Pi Subagents runtime evidence, and insufficient claim/adversarial/Unicode fixtures. The reviewer edited nothing.

The first remediation closed the blocker and most initial findings. Follow-up reviewer run `35e0b080-b680-49e7-b4e4-822d4c17ecd4` found no blocker but retained two High gaps: mandatory common Work Packet scope and claim map/bundle/seed/dependency/shared-owner identity were not bound, and provenance path/hash checks did not prove the cited range was directly read. It also found Parent exclusions were only authorized rather than preserved exactly and oversized basis arrays could create unsatisfiable schemas. The second remediation makes the full common/claim scope mandatory, echoes map/bundle identity as constants, preserves exclusions exactly, binds approved seeds/dependencies/owners, rejects impossible cardinality, and checks every provenance range against `recordsRead.ranges`.

Closure reviewer `e39d07ca-c3e2-4936-aeb2-fabe17cf6cf9` then reported **no blocker/high remaining** and confirmed closure of common scope, claim map/bundle/basis, exact exclusions, and path/hash/range binding. Its sole Medium was a satisfiability edge between admitted basis sizes and output-array capacities. The final correction caps candidate coverage at 32 total IDs and claim question/facet bases at 16 each, aligns output schema limits, and adds accepted-boundary and one-over rejection fixtures. Focused checks, exact TypeBox compilation, and final standard validation then passed.

### Machine-admitted High rerun result — invalid-packet / main NO-GO

Run `db834bed-fb07-4563-ab98-01a65736083d` completed the exact logical integration-readiness shadow through the real Pi Subagents structured-output path. Transport and repository safety passed: bridge off; no `contact_supervisor`; exactly 14 successful calls (three ordered probes, six concrete maps, two prescribed record reads, two matching hashes, final `structured_output`); no source/mutation/overview/grep/external/recursive attempt; and byte-identical pre/post revision, working-set manifest, status, overview, 617-file count, 302-record count, and 13 dirty entries.

The schema-captured value echoed exact identity, conserved F1–F7/I1–I8 into four unverified questions, supplied two direct records and `parentMustRead`, and again proposed one shared `single-reader` bundle. Independent Parent admission nevertheless returned `valid=false`, `success=false`, `admittedStatus=invalid-packet`: compact JSON was 14,108 characters against the 6,000 ceiling, and three question-provenance ranges were absent from their corresponding `recordsRead.ranges` inventories. High had self-reported `proposal-ready`, so machine admission correctly stopped the false success. No claim-evidence, retry, altered budget, or main gate follows.

Evidence: `/tmp/record-reader-high-shadow-20260823/rerun/audit.md` SHA-256 `6262cd74e47ed1330b6f495f989d6c0c337add2db78f7ebf025efa708d72dd32`; `metrics.json` SHA-256 `979967bdfa4f64d08dad7595a01ac146a70571f6518c833abf332f427b95e43a`; structured output SHA-256 `fb13b6b30df4348058918a8b51cba9b1c2ccf6f96520e9c60b564a9ba8d36bc8`; admission receipt SHA-256 `1113b2d354c517b15558f9e4dee2fbf1bab481bd7980cdcf4cf58e9e3cca3d48`. This proves the deterministic boundary catches the prior false-success class; it does not make the Reader integration-ready.

### Confirmed later rule-recall shadow

After showing a concrete failure where an agent correctly stored rules but misdiagnosed skipped rule retrieval as a generic L5/code-enforcement problem, the user selected **기존 구조로 사례 검증**. The Parent would directly read and interpret the governing rules; the unchanged Reader would return bounded canonical evidence and `parentMustRead`, with no full grammar, second resolver, delegated debt, new role, or `governingRuleCandidates` field.

### Rule-recall shadow result — semantic division supported, packet invalid

Run `a9c9bf32-7dd5-4a01-80c7-73acd90b2f33` obeyed the same 14-call records-only transport and preserved the repository exactly. Its two unverified questions identified skipped retrieval as the failure class, separated organic guidance/search-read evidence from a new tool-specific L5, preserved Parent rule authority, returned ADR 0041 and the enforcement SSOT in `parentMustRead`, warned not to promote L5 from the map, and used existing fields without requesting a new role/schema. Parent direct reads agree with that framing. This one case therefore supports the user's proposed responsibility split and demonstrates no semantic need for a rule-specific field.

The candidate was still not admissible: `8,310 / 6,000` compact characters and one enforcement-SSOT provenance range absent from `recordsRead.ranges`. Machine admission changed self-reported `proposal-ready` to `invalid-packet`; no claim or retry followed. The demonstrated remaining gap is output compactness/range discipline, not Parent-versus-Reader authority. Evidence: `/tmp/record-reader-rule-recall-shadow-20260824/audit.md` SHA-256 `1785d715b0e50d8c7083d7efab1a8bd141b7e35475a89a7164d77bea2bf89a4b`; `metrics.json` SHA-256 `950fc0a64dd598cd982938431870b5a51233ff3c133a2b49a1285695e7b46c71`.

## Compact output contract v2 — implementation approved, live run gated

The user selected **계약 압축 설계**, then questioned whether a fixed 6,000 hard ceiling could reduce accuracy. The confirmed implementation policy is accuracy-first **soft target 6,000 / hard cap 12,000**: over-target evidence remains structurally valid with a warning; evidence that cannot fit the hard cap returns `overflow` with split detail rather than trimming. Compact v2 implementation is approved; live Reader execution, ceiling benchmarking, merge, and main integration remain separate gates. The 37-row legacy graph migration remains deferred.

Measured compact JSON composition shows the design target is duplication, not semantic scope:

| Packet | Current | Largest duplicate-bearing sections | Repeated-string payload estimate | Normalized design estimate |
|---|---:|---|---:|---:|
| integration-readiness | 14,108 | questions 6,423; dispositions 2,877 | ~5,573 | 4,082 |
| rule-recall | 8,310 | questions 2,977; dispositions 1,363 | ~2,532 | 2,860 |

Implemented contract direction, preserving the single `record-reader/v2` role and changing only new-packet wire/admission semantics:

1. Keep full root/revision/snapshot/overview/epoch/objective/facet/node/risk identity in a Parent/transport envelope; model output echoes one schema-constant `contractDigest`, while run metadata, generated schema, ordered probes, and Parent fingerprints bind the captured payload to that envelope.
2. Give Parent contract entries compact `F*`/`I*`/`N*`/`V*` ids. Store each direct path/hash/range list once as payload-local `R*`; questions/claims, `parentRead`, seeds, and verification use ids/range indexes.
3. Make one coverage map the authority. Remove duplicated per-question facet/inventory lists and ordinary assigned-row prose reasons; retain bounded detail only for unmapped/other cases.
4. Remove derivable `cueOrigins`, per-question allowed layers, per-question overlap keys, repeated implementation paths, and full-path node dispositions. Top-level evidence, contract layer scope, overlap groups, verification table, and reason codes own those facts once.
5. Bound human text generously (`statusJustification`/question/claim <=600; risks and other reasons <=300) and retain aggregate 6,000 soft-target / 12,000 hard-cap accounting.
6. Use one admission CLI authority. Archived v1 validation remains explicit; compact v2 schemas are generated only for new packets. Unknown/duplicate ids, invalid range indexes, incomplete coverage/node disposition, remap, and success inconsistency reject admission.

The implementation keeps one CLI facade: archived `record-reader-admission/v1` schema/validation remains available, while v2 adds canonical digest generation, compact candidate/claim schemas, normalized reference/coverage/closure validation, soft-target warnings, and hard-cap rejection. Regression includes v1 compatibility, v2 candidate/claim/adversarial cases, and a 7-facet/8-inventory integration-scale payload below the 6,000 target. These are static/fixture results; no compact live model run is authorized.

### Compact v2 independent review and closure

Initial reviewer `b30d9bc5-812a-45ec-aef6-32af9e577899` found four High gaps: remap triggers did not force `needs-remap`; overlap/dependency bundle closure and aggregate seed/node closure were incomplete; and compact provenance accepted path traversal/impossible hash lengths. It also found open contract grammar, incomplete status/detail symmetry, and missing committed TypeBox evidence. The remediation closed contract/identity/catalog/budget grammar, canonical path + exact 40/64 hashes, unique node/seed/bundle ownership, remap/conflict/blocked/overflow status binding, and installed-peer TypeBox compile/check fixtures.

Follow-up reviewer `a364ce42-12ab-4ef5-bbfc-1c40de8ce2e9` reported no blocker/High and identified three Medium edges: blocked dependency ids were not Parent-approved, bundle ownership could duplicate, and records=1 could never satisfy success. Those were corrected by terminal-D id binding, exactly-one Q/overlap/cycle/dependency ownership, and compact `records >= 2`; an explicit 64-hash fixture and TypeBox Check parity were added.

Closure reviewer `acb68852-a98d-40ad-8ed7-cdff7644b2d6` reported **no blocker, High, or Medium findings remaining**. Residuals are limited to conditional peer discovery for TypeBox and the intentional Parent-owned run/transcript/content-truth audit. Review artifacts: `/tmp/record-reader-compact-v2-review-20260824/`.

### Compact v2 rule-recall canary — admitted / semantic fidelity retained

User-approved Luna High run `79dd9d1c-0ff8-4a62-b929-8e189e678d0c` completed one compact candidate-map with no retry or follow-on. Deterministic v2 admission returned `valid=true`, `success=true`, `proposal-ready`, `3,143 / 6,000 / 12,000`, `overTarget=false`, no violations, and no warnings. The prior equivalent packet was 8,310 characters, so normalized output saved 5,167 characters (`62.2%`) while retaining two questions, eight coverage inputs, two direct records, Parent rereads, risks, verification refs, overlap, one bundle, and single-reader routing.

Parent semantic comparison found no decision-relevant loss: the compact questions still identify skipped rule retrieval, distinguish organic guidance/search-read evidence from a new tool-specific L5, preserve Parent interpretation/read-debt authority, and reject a new role/schema authority. Runtime used only 14 allowed calls and preserved the repository. One protocol-quality deviation remains: calls 10–13 read both bodies before hashing both, instead of immediate read→hash interleaving; hashes matched before `structured_output`, so evidence remains valid but the prescribed sequence was not perfect.

Descriptive only: payload `8,310→3,143`, output tokens `4,319→1,988`, duration `118.700s→68.222s`, cost `$0.026013→$0.024904`; input rose `64,727→72,095`. Cache/execution were uncontrolled and there is no Direct-Parent arm. The live over-soft-target branch remains untested because this payload fit below target. No claim, integration canary, main gate, merge, or retry follows automatically. Evidence: `/tmp/record-reader-compact-rule-recall-canary-20260824/audit.md` SHA-256 `804ab112b4d82c3b3788878280b369f6f40bbcd5f04ec83798309dfc95240da8`; metrics SHA-256 `2a248192c6b4c46fef55f4f6f44186156aa2ee4c58c3ab3a96762bf4c347e9ea`.

User-confirmed evaluation priority: aggregate multi-agent token reduction is not an optimization target for this pilot because the selected per-run Luna route is economically acceptable even at high token volume. Optimize Parent-context footprint, Parent reread burden, elapsed time, semantic accuracy, and admission reliability instead. Aggregate token/cost remains a descriptive runaway guardrail, not a success or promotion gate; this does not change the per-run Luna-only experimental route or create a persistent model default.

Design artifact: `/tmp/record-reader-contract-compression-design-20260824.md`.

## Historical experiment design

### Package role

`packages/lazy-harness-pi/agents/record-reader.md` declares:

- runtime name `lazy-harness.record-reader`;
- `systemPromptMode: replace` and `inheritProjectContext: false`;
- strict `read, grep, bash` tool allowlist with no artifact output;
- `LAZY_HARNESS_ROLE: record-reader/v1` marker;
- one complete overview, one concrete drill, primary-body read, and one-hop canonical closure;
- explicit `complete|incomplete|conflict` output and 2–4 Parent verification records;
- no source read, mutation, subagent recursion, output file, user decision, or Parent read-debt claim.

### Adapter boundary

`packages/lazy-harness-pi/extensions/lazy-harness/index.ts` recognizes the role marker only in the resolved system prompt. It does not inspect task/user text. The role path:

- skips full `.lazy-harness/AGENTS.md` loading;
- injects one compact root/profile reminder;
- permits exact `lazy map`, bounded root identity/status probes, direct canonical record reads, and bounded grep within one canonical record layer;
- blocks source reads, mutation, broad shell search, file output, and external tools;
- skips Parent `agent_end` response-completion/canonicalization hooks.

All non-matching roles keep the existing full-grammar, hook, guard, continuation, and lifecycle behavior.

## Sequential A/B contract

Target: `/home/lazydino/dev/medivance`

Task: retrieve the canonical Lazy-Harness policy for reservation-management `예약 받기/예약 안받기` without reading product source.

Arms:

1. existing full-grammar `delegate`, Luna-low;
2. package-owned thin `lazy-harness.record-reader`, Luna-low.

Controls:

- same Medivance root, HEAD/status fingerprint, and task wording;
- fresh context, sequential launch, no fallback, no retry;
- no project mutation and no output file requested from either child;
- same outer timeout and comparable turn budget where runtime allows;
- Parent scores both against the previously established six core record groups and fifteen critical policy facts.

Metrics:

- protocol outcome;
- wall-clock;
- assistant turns and tools;
- input/output/cache tokens and reported cost;
- system prompt/full-grammar presence;
- core-record recall and critical policy coverage;
- irrelevant bodies, repeated reads, and Parent verification debt;
- Medivance status/fingerprint preservation.

## Acceptance

The thin profile is only a candidate for a later shadow task when:

1. Parent/ordinary full-grammar regression remains green;
2. the thin child demonstrably lacks Parent grammar;
3. tool ceiling blocks source/mutation/artifact paths;
4. retrieval fidelity is no worse than the previously observed Luna-low arm and closes its stale subset-rule defect;
5. it completes within the role turn envelope without output-edit loops;
6. Medivance state remains unchanged.

One A/B result is insufficient for production promotion even if all checks pass.

## Results

The earlier Luna-low delegate-vs-thin comparison is retained only as profile-diagnostic history. It is invalid for the user's requested Parent-alone vs Record-Reader question because neither arm was the Direct Parent.

The user corrected the benchmark contract and approved a fresh sequential replacement on Medivance `main@74315a091ae914e95114625467a067384d18abc5`: Direct Parent `openai-codex/gpt-5.6-sol:medium`, thin Record Reader `sol:medium`, and thin Record Reader `luna:xhigh`, with identical task text, fresh context, canonical-record-only evidence, normal response delivery, no fallback/retry/output artifact/source read/mutation, and mandatory Parent inspection of every final output plus transcript/tool evidence.

| Arm | Runtime | Turns/tools | Input/output | Cache read | Cost |
|---|---:|---:|---:|---:|---:|
| Direct Parent Sol-medium | 80.300s session-event span; 147s observed dispatch wall | 9/15 | 84,500/5,074 | 397,312 | $0.773376 |
| Thin Reader Sol-medium | 126.421s | 10/9 | 64,508/3,499 | 293,888 | $0.574454 |
| Thin Reader Luna-high | 139.628s | 13/17 | 101,791/4,574 | 357,888 | $0.033005 |
| Thin Reader Luna-xhigh | 207.827s | 15/22 | 98,953/8,974 | 741,376 | $0.045387 |

The eight-body set is a transparent verification-candidate list, not a mandatory core-body inventory. Complete discovery requires the complete overview, while body loading remains decision-relevant and JIT; mechanical candidate-body counts are retained only in `metrics.json`.

Direct inspection findings:

- the supervising Parent directly read all four final outputs, all child meta files, and every actual tool call/argument/result status; claimed read paths/ranges were cross-checked against completed reads;
- no arm invented an unread line range in the formal/follow-up runs; no source/mutation/output-artifact/subagent-recursion path occurred; all child transcripts carried the explicit `record-reader/v1` marker without Parent grammar;
- common skipped candidate bodies were not mandatory because their decision-relevant rules were recovered elsewhere or they were auxiliary to availability; candidate-body count is not used as a semantic score;
- Parent returned the fullest detail and a safe but arguably over-conservative `conflict`; it violated map-first ordering and read deprecated permission policy inefficiently;
- Reader Sol was the most concise Reader and omitted only the secondary control-row projection/capacity/dashboard exclusion detail;
- Reader Luna-high recovered the main user-facing policy plus staff filtering and projection/dashboard exclusion, but omitted mixed-range anchor/staff-change recalculation, global-vs-individual overlay/hover, awaited refresh, and room-capacity exclusion; it also read lifecycle SSOT without reporting that irrelevant body under `recordsRead`;
- Reader Luna-xhigh returned the richest Reader detail but was slowest/noisiest and finished on grace turn 15;
- Luna-high versus Sol: runtime `+10.4%`, tools `+88.9%`, input `+57.8%`, reported cost `-94.3%`; Luna-high versus Luna-xhigh: runtime `-32.8%`, tools `-22.7%`, output `-49.0%`, cache `-51.7%`, cost `-27.3%`;
- Parent dispatch wall and child model runtime are different envelopes, so runtime deltas are directional rather than strict end-to-end speed ratios.

Quality verdict: no general Subagent comprehension collapse was observed. Direct Parent provides the fullest detail; Reader Sol currently offers the strongest efficiency/detail balance; Luna-high is dramatically cheaper and substantially leaner than Luna-xhigh but drops more secondary display/snapshot detail; Luna-xhigh is the richest Reader at the highest latency/tool/cache cost. One sample per route cannot set a default.

State preservation: Medivance HEAD/status fingerprint remained unchanged with only pre-existing `?? 0.43.78`; `.pi/settings.json` and `.git/info/exclude` were restored byte-identically.

Evidence: `/tmp/medivance-record-reader-formal-ab-20260822/comparison.md` SHA-256 `ab2897b235ac2ec7aa9f2cbb22977540cda3b5e3f7c430b152263b06846fa821`; `/tmp/medivance-record-reader-formal-ab-20260822/metrics.json` SHA-256 `5d64e6131cf5730def2bf408d213926a3a1f56bfe4c8154131a0ffdf87c4c7c9`; output hashes are stored in `/tmp/medivance-record-reader-formal-ab-20260822/output-hashes.txt`.

The user rejected the original thin prompt as an unfair same-rules comparison and approved a two-stage replacement: first compare Direct Parent Sol-medium with a Reader Sol-medium receiving the full canonical AGENTS grammar; only after semantic equivalence, run exact canonical-section reductions that remove record accumulation, then approval+accumulation, then lifecycle/skip sections while preserving §0/§1/§2.1/§2.2/§2.5 retrieval semantics.

### Faithful quality-equivalence baseline

Fresh Direct Parent Sol-medium and `record-reader-faithful-full` Sol-medium ran sequentially on the same Medivance HEAD/task. Parent returned 8 policy groups with 10 tools; faithful-full returned all Parent decision-critical groups plus additional staff-filter, permission-supersession, control-row capacity/dashboard, and implementation-gap detail with 20 tools. Every reported `recordsRead` body matches an actual completed read; no source/mutation/output/subagent recursion occurred. The full Reader therefore passes the semantic/evidence equivalence gate for this task.

`record-reader-faithful-no-write` also passes the quality gate: it recovered all Parent decision-critical groups plus staff filtering and control-row exclusions, reported exact read ranges matching completed reads, and preserved unresolved implementation/cleanup gaps. It used 12 turns, 25 tools, 184.548s, and $0.712184; no source or mutation occurred. Removing canonical §2.4 record accumulation therefore caused no semantic regression on this read-only task.

`record-reader-faithful-no-approval` preserved the current policy claims and evidence fidelity, but changed the protocol verdict from the Parent/full/no-write `complete` interpretation to `conflict` solely because older contradicted paragraphs lacked explicit deprecated markers. The newer user-confirmed correction and current digest still determine the policy, so this is a conservative protocol-classification regression rather than a wrong current rule. Under the predeclared first-regression stop rule, the experiment stops here and the `faithful-core` arm is not run. The best validated reduction boundary for this sample is therefore **no-write**; removing §2.3 approval semantics is not accepted.

Evidence: `/tmp/medivance-record-reader-faithful-20260822/comparison.md` SHA-256 `29cfc1222b2ba1b1658108cf9c4593cb28c33388975053b193ec2563c9e14907`; `/tmp/medivance-record-reader-faithful-20260822/metrics.json` SHA-256 `143736d6276aa55de0703359b0555d2e8494f3f24c18ce678af59ffbe554625f`; raw outputs, metadata, transcripts, and hashes are retained below that evidence root.

## Correction implementation and residual candidates

Implemented in the approved correction batch: exact surface-term primary preference, primary-before-auxiliary ordering, `parentVerify ⊆ recordsRead`, unresolved→`incomplete` instruction, direct-link BDD/TDD/SSOT checklist, and bounded one-layer canonical grep with runtime denial outside the record boundary.

Approved execution boundary: identical Medivance HEAD/task/model, fresh sequential arms, normal response, no fallback/retry/source/mutation/output artifact, direct Parent inspection of all output/meta/transcript/tool evidence, and stop at the first semantic quality regression. Model comparison and production/default/shadow promotion remain out of scope.

## Implementation map

- `packages/lazy-harness-pi/package.json` — exposes `./agents` and the admission CLI script.
- `packages/lazy-harness-pi/agents/record-reader.md` — single v2 two-mode packet, coverage, freshness, fixed-point remap, strict structured output, hard budgets, and evidence-provenance contract.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts#lazyAgentRole/recordReaderReminder/recordReaderToolDenial` — v2 marker, two-mode/admission reminder, Pi Subagents schema/capture-gated `structured_output`, concrete-map/hash/read/grep allowance, steer preservation, and records-only runtime ceiling.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts#before_agent_start/tool_call/tool_result/context/agent_end handlers` — Reader prompt/tool delivery, Parent evidence isolation, and Parent lifecycle bypass.
- `packages/lazy-harness-pi/scripts/record-reader-admission.ts` — one facade for archived v1 plus compact v2 digest/closed-schema/canonical-provenance/reference/coverage/node/seed/bundle/dependency/remap/status closure, soft warnings, and hard rejection.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — v1 compatibility, compact candidate/claim/scale/adversarial/status/ownership/hash and installed-peer TypeBox Compile/Check fixtures, plus unchanged fake-runtime isolation.
- `.lazy-harness/spec/platform/pi-agent-package.md` — adapter, two-mode, and machine-admission package contract.
- `.lazy-harness/tests/pi-agent-package.md` — regression contract and layer-completeness judgement.
- Graph: compact implementation/review/validation plus the admitted rule-recall canary are indexed through `kg_record_reader_compact_rule_recall_canary_result_20260824`; legacy graph migration remains separately deferred.

## Layer completeness

- DDD: no independent delta; `candidate-map`/`claim-evidence` are internal packet modes, not project business vocabulary.
- SDD: updated for compact v2 Parent envelope/digest, normalized ids/tables, archived v1 compatibility, and separate 6k soft target/12k hard cap.
- BDD: compact rule-recall canary retained the correct rule family, Parent authority, two questions, and coverage with no decision-relevant loss; one tool-order deviation remains.
- TDD: updated with v1 compatibility plus compact digest/candidate/claim/scale/reference/coverage/remap and soft/hard budget fixtures; fake-runtime isolation is unchanged.
- ADR: ADR 0055 owns compact accuracy policy and the bounded admitted canary; claim/main rollout remains gated.
- SSOT: no permanent project memory/path/model-default delta; admission contracts and captured output are per-run artifacts.
- Planning: owns invalid v1 shadows, compact v2 implementation/reviews, admitted canary, protocol residual, Parent-context/latency-first evaluation priority, continued main NO-GO, and graph-migration defer state.

## Rule placement

- Rule: Parent owns complete overview/governing reads and approves a conserved candidate coverage map; the single package-owned v2 Reader uses explicit candidate-map or claim-evidence mode, and newly discovered evidence reopens the map instead of silently widening scope.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/record-reader-thin-profile-experiment.md`.
- Why not AGENTS.md: this is an opt-in Reader component experiment, not all-agent operating grammar.
- Why not local notes: the implementation affects shared framework package behavior and future runtime adapters.
- Confirmation: user approved compact v2 and exactly one rule-recall live canary, then confirmed that aggregate system-token reduction is not a pilot objective because per-run Luna economics are acceptable; Parent context, reread burden, latency, accuracy, and admission reliability are primary. The canary was admitted at 3,143 characters with no semantic loss on the bounded case, but had non-immediate hash ordering. No retry, claim, integration canary, automatic scheduling, Source Verifier, Writer, delegated debt, merge, default, or promotion is approved.
