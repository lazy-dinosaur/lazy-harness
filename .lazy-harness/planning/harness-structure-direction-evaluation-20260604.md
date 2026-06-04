# Harness Structure and Direction Evaluation — 2026-06-04

Status: current-evaluation
Date: 2026-06-04
Layer: Planning
Trigger: user asked for full evaluation of current lazy-harness structure, direction, and completeness

## Executive summary

Lazy-harness is no longer an idea-stage harness. It is a working, self-tested, installable AI-first development framework with a clear architecture:

```text
canonical records
→ generated/index/helper metadata
→ pre-turn harness-first search prompt and search/read debt
→ LLM/searcher root-bound record/source/test inspection
→ generic pre-action evidence guard
→ response.completed audit/backstop
→ record/candidate/graph update
→ commit/push lazy test gate
```

Overall assessment as of this evaluation:

| Area | Maturity | Assessment |
|---|---:|---|
| Core philosophy / direction | 90% | Very strong. ADR 0024, ADR 0041, SSOT enforcement, and north-star are coherent. |
| Framework-owned validation | 90% | Strong. `lazy test --scope framework` passed 77/77 checks and smoke doctor passed. |
| Install / sync portability | 80% | Strong and now public-install dogfooded in `medivance-homepage`; host-specific D07 package-health policy needs tuning. |
| Jcode integration / hooks | 80% | Working and deeply protected, but response lifecycle is still partly legacy/backstop and compare replacement is not approved. |
| Record-first memory model | 75% | Strong mandatory policy and many guards, but canonical promotion still depends on agent workflow, not a fully productized broker. |
| Context Delivery / search guidance | 65% | Direction is correct. Current static search-debt is useful; native context broker is planned/partial, not fully implemented. |
| Project Profile | 55% | CLI and skill exist, but source Project Profile artifacts are missing and dogfood hosts have had needs-interview gaps. |
| Capability Registry | 55% | CLI/registry works, but source registry has only the phase-one capability and auto-promotion remains dogfood/planning. |
| Knowledge graph | 65% | Canonical graph exists with 348 rows and JSONL health; graph query/projection/conflict workflow is still incomplete. |
| Product UX / operator ergonomics | 60% | Powerful but still heavy. Needs better dashboards, profile fill UX, and fewer ambiguous command paths. |

Practical headline:

```text
MVP/framework-infra: mostly complete and green.
Productized multi-host operating system: mid-stage, needs dogfood/evaluation before more hard guards.
```

## Evidence read

Records and code consulted in this evaluation:

- `README.md` — public install/update/sync and status overview.
- `.lazy-harness/framework/framework-contract.md` — Principle 0, directory split, validation ownership.
- `.lazy-harness/plans/north-star-accuracy-and-no-regression.md` — failure classes and ideal loop.
- `.lazy-harness/decisions/0024-ai-first-framework-redesign.md` — AI-first lifecycle enforcement, AGENTS grammar/records vocabulary.
- `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` — C+ v2 organic hybrid rule guidance.
- `.lazy-harness/ssot/harness-enforcement-policy.md` — mandatory records vs organic action guidance.
- `.lazy-harness/spec/platform/pre-response-rule-context.md` — message.received static harness-first prompt contract.
- `.lazy-harness/spec/platform/context-delivery-contract.md` — partial Context Delivery Phase 7 status.
- `.lazy-harness/spec/platform/response-rule-audit.md` — response.completed audit criteria.
- `.lazy-harness/spec/platform/project-profile.md` — durable Project Profile contract.
- `.lazy-harness/spec/platform/record-decision-broker.md` and `.lazy-harness/tests/record-decision-broker.md` — post-turn record decision packet and shadow behavior.
- `.lazy-harness/planning/current-framework-roadmap-snapshot.md` — active tracks and do-next policy.
- `.lazy-harness/planning/native-context-broker-implementation-plan.md` — planned native context broker.
- `.lazy-harness/planning/model-quality-dogfood-findings.md` — guard placement and model-quality risks.
- `.lazy-harness/planning/dogfood-auto-recording-status-report.md` — auto-recording and production hook replacement status.
- `.lazy-harness/planning/dogfood-record-audit-improvement-plan.md` — record-audit/graph hygiene dogfood status.
- `.lazy-harness/knowledge/candidates.jsonl` — recent dogfood observations including medivance-homepage install and D07 gap.

Validation run during this evaluation:

```bash
.lazy-harness/bin/lazy doctor --profile smoke --scope framework
.lazy-harness/bin/lazy test --scope framework
.lazy-harness/bin/lazy lifecycle-parity --format=md --fail-on-mismatch
.lazy-harness/bin/lazy record-audit --format=md --source /home/lazydino/dev/lazy-harness
.lazy-harness/bin/lazy graph-hygiene --format=md --source /home/lazydino/dev/lazy-harness
.lazy-harness/bin/lazy hook-timings --format=md --limit=500
.lazy-harness/bin/lazy capability audit --format=json
```

Key results:

- Framework smoke doctor passed.
- Framework self-test passed: `ran=77, skipped=0`.
- Lifecycle parity passed: `12/12` fixtures.
- Capability audit passed: `count=1, issues=[]`.
- Hook timing recent 500 rows: `hook-total avg=720.3ms`, `p90=863ms`, `p99=1341ms`, max `1341ms`.
- Record audit source: `195` files, graph rows `348`, JSONL invalid rows `0`.
- Graph hygiene source: OK yes, but `Issues=1` warning for missing path `.lazy-harness/planning/native-context-broker-implementation-plan.md#inventory-first-correction`.
- Generated indexes present: `implementation-index.json`, `reference-index.json`.
- Generated indexes missing: `relevant-record-index.json`, `context-index.json`.
- Source `.lazy-harness/project/` has no artifacts; Project Profile incomplete in the source repo context.

## Strengths

### 1. Direction is coherent and differentiated

The framework has a clear identity:

- AI-first, not static ESLint-like automation.
- AGENTS.md is grammar, records are host vocabulary.
- Canonical memory is record/graph backed, not chat memory.
- Hooks are safety and evidence transport, not the primary semantic authority.
- Non-record action guidance stays organic; record completion stays mandatory.

This is the right direction. It avoids two bad extremes:

1. A brittle hard-rule trap where every preference blocks workflow.
2. A weak note-taking system where agents keep forgetting records.

### 2. Validation depth is unusually strong

`self-test.py` now protects many real surfaces:

- Jcode wiring and managed blocks.
- message.received search-debt injection.
- generic search/read evidence guard.
- response.completed helper chain.
- lifecycle parity runner.
- record decision broker.
- Context Delivery packet journal.
- Project Profile inspect/plan/apply.
- document ingestion.
- affected test runner and TDD cross-verify.
- graph hygiene and record audit.
- install/sync drift behavior.

A green 77-check framework gate means the framework is structurally reliable enough for real dogfood.

### 3. Public install and host dogfood are real now

The public installer works and was dogfooded in `/home/lazydino/dev/medivance-homepage`:

- official `curl | bash` install succeeded,
- `.lazy-harness/` and `.jcode/` wiring were generated,
- host smoke doctor passed,
- full host self-test surfaced a real D07 package-health policy gap instead of install failure.

This is a strong portability proof, even though full host validation policy needs tuning.

### 4. Hook philosophy matured

The current design is more mature than the earlier hard-block-heavy direction:

- `message.received` injects bounded inventory/search protocol.
- generic evidence guard can deny mutation when search/read evidence is absent.
- `response.completed` stays as audit/backstop.
- record-completion obligations remain mandatory.
- tool-specific project policy is being removed/migrated.

This is a good balance between correctness and workflow speed.

### 5. The system is accumulating useful dogfood evidence

Recent candidates and planning records show the harness is learning from real use:

- D07 missing `typecheck:node` in generic host.
- official install vs local dogfood distinction.
- medivance-homepage official install milestone.
- context broker/search handoff candidates.
- ambiguous Korean surface-term retrieval gaps.
- graph path hygiene and source-only classification.
- lifecycle compare dogfood handoff.

This is exactly the intended "improves as it is used" loop.

## Weaknesses and gaps

### 1. Project Profile is the biggest product gap

The Project Profile contract is central:

```text
request → project profile → maps → records/code/tests → implementation → validation
```

But current source record audit reports:

- `artifactsComplete=false`
- `.lazy-harness/project/` is empty in the source repo context
- `feature-navigation.xml` missing
- `tests/test-strategy.xml` missing in source context

For installed hosts, prior dogfood also showed profile skeletons could exist while many fields remain `needs-interview`.

Impact:

- Agents still rely too much on layer inventory and ad hoc search instead of first-class project navigation.
- Ambiguous surface terms like `예약시트` remain hard without profile aliases/routes/components/tests.
- Cross-project onboarding works structurally but does not yet guarantee useful project understanding.

Recommended next improvement:

1. Run `/lazy-project-profile` or direct `project-profile.ts` on `medivance-homepage`.
2. Make profile fill UX easier than raw answers JSON.
3. Use `feature-navigation.xml` as the first real context broker input.

### 2. Context Delivery is partially implemented, not yet productized

Current state:

- Static harness-first search-debt prompt works.
- `context-delivery.ts`, packet schema, handoff prompt, journal, and audit exist.
- `context-index.ts` exists, but `context-index.json` is currently missing.
- Native Context Broker plan is still `proposed`.

The missing product layer is:

```text
ambiguous phrase
→ query expansion / feature-navigation / graph / source fusion
→ ranked requiredRead packet
→ main agent reads exact records/files
```

Until this exists, the system depends on the LLM manually following the search protocol well. The search/read guard measures evidence, but it does not yet provide high-quality semantic resolution.

Recommended next improvement:

- Promote `native-context-broker-implementation-plan.md` into an approved slice after an option gate.
- Start with `Project Profile + feature-navigation + generated context-index` rather than external RAG.
- Keep `message.received` static and use task-start/self-resolve or optional searcher handoff for heavier resolution.

### 3. Record Decision Broker is shadow-only

The post-turn Record Decision Broker is well specified and tested, but it is intentionally conservative:

- shadow bridge journals sanitized packets,
- silent by default,
- advisory only behind env flag,
- no automatic blind record writes.

This is correct for safety, but it means canonical record promotion still depends on the active agent workflow. The framework is not yet a fully automatic record-completion product.

Recommended next improvement:

- Collect dogfood packet rows.
- Add a review dashboard for `record-decision-packets.jsonl`.
- Promote only low-FP cases to advisory, not block.

### 4. Capability Registry is under-populated in source

Source registry has one capability:

```text
capability-registry-phase1, kind=command, level=discover
```

The registry CLI works, but the intended capability model is not yet broadly populated in the source repo. Host-specific capabilities have existed in Medivance/PWA dogfood, but the source global registry is still minimal.

Impact:

- Capability Registry is structurally implemented, but not yet delivering much automated guidance in the source repo itself.
- Auto-promotion is still a roadmap/dogfood target.

Recommended next improvement:

- Evaluate host capability evidence from Medivance/PWA/homepage.
- Add source-level framework capabilities only when they are general.
- Keep most host capabilities host-local.

### 5. Graph is useful but not yet the retrieval backbone

Graph state is healthy enough:

- 348 rows,
- JSONL valid,
- no duplicate IDs,
- no comma-joined paths,
- one missing-path warning.

But graph is not yet a complete backbone because:

- candidate → draft → confirmed flow is still partly manual,
- graph query/projection is not the default agent retrieval surface,
- human docs and graph can still drift,
- the context broker does not yet fully fuse graph edges into requiredRead.

Recommended next improvement:

- Fix the one graph missing-path warning.
- Add graph query/context output only as derived helper, not canonical truth.
- Tie graph edges into Context Delivery once Project Profile aliases exist.

### 6. Logs and telemetry are noisy

Record audit shows large log volumes:

- hook-timings: 38139 lines,
- route-telemetry-debug: 2879 lines,
- validations: 909 lines.

This is useful during dogfood but can become hard to reason about. There is already a log compaction/summary backlog. It should become a product UX slice after the current dogfood/evaluation period.

### 7. Host full-test policy needs generic-host tuning

`medivance-homepage` full host self-test found:

```text
D07 package health expected bun run typecheck:node, but script was missing.
```

This is not an install failure. It is a policy calibration issue:

- For framework/Medivance-specific hosts, `typecheck:node` may be expected.
- For generic public installs, missing `typecheck:node` should probably be warn, discover, or Project Profile question rather than a hard fail.

Recommended next improvement:

- Decide whether D07 missing `typecheck:node` is:
  A. warning for generic hosts,
  B. required only after Project Profile declares it,
  C. mapped to existing `typecheck` / `build` package scripts,
  D. custom host rule.

### 8. Response lifecycle replacement is intentionally not complete

Lifecycle parity is green, and compare dogfood exists, but production default replacement is not approved.

This is good caution. Current state:

- legacy helper loop is still production default,
- lifecycle-check/orchestrator path has parity fixtures,
- compare dogfood is active in selected hosts through local wiring,
- replacement requires explicit approval.

Recommended next improvement:

- Do not replace production hook yet.
- First inspect accumulated compare logs and readiness checklist.
- Only then decide an opt-in default switch with rollback.

## Completeness score by layer

| Layer / subsystem | Score | Why |
|---|---:|---|
| DDD/SDD/BDD/TDD/ADR/SSOT record structure | 85% | Directories, records, rule digests, implementation maps broadly exist. Project-specific content depends on host profile. |
| AGENTS grammar and private Jcode wiring | 90% | Strong and installed. Self-test protects invariants. |
| Hook/event lifecycle | 80% | Working, measured, parity-tested. Production replacement still pending. |
| Search/read enforcement | 75% | Search-debt and generic guard work. Semantic resolution remains LLM/manual protocol. |
| Validation/test gates | 90% | Strong self-test/doctor/lifecycle parity. Generic-host D07 needs policy tuning. |
| Install/update/sync | 85% | Public install works. Sync marker policy clear. Host copy/source boundary good. |
| Project Profile/bootstrap | 55% | Contract and CLI exist; product flow and real host fill remain incomplete. |
| Knowledge graph | 65% | Healthy JSONL backbone, but query/projection/conflict automation still maturing. |
| Capability Registry | 55% | CLI exists and audited; registry is under-populated and auto-promotion unproven. |
| UX/observability | 65% | record-audit, graph-hygiene, hook-timings exist; log/decision dashboards still needed. |

## Overall judgment

### What is complete

- The core framework architecture is sound.
- The source repo is installable and validated.
- The Jcode integration is real, not just docs.
- Hooks and validation are protected by strong self-tests.
- The active-memory-loop direction is correct.
- Dogfood is producing real findings and the framework is capturing them.

### What is not complete

- Project Profile is not yet a smooth, unavoidable onboarding layer.
- Context Broker is not yet a full native retrieval product.
- Record Decision Broker is still shadow/advisory, not an automated promotion system.
- Capability Registry has not reached broad real-use auto-promotion.
- Some host validation policies are too specific for generic public hosts.
- Telemetry/log UX needs compaction and dashboards.

### Recommended next order

1. **Calibrate generic host validation**
   - Fix or decide the D07 `typecheck:node` policy for `medivance-homepage` style hosts.
   - This directly improves public install confidence.

2. **Run Project Profile on `medivance-homepage`**
   - It is the newest clean official-install host.
   - Use it to test profile skeleton/interview/fill UX without the complexity of full Medivance.

3. **Build the smallest Context Broker slice**
   - Use `feature-navigation.xml`, generated context-index, graph edges, and source/test search.
   - Do not add external RAG yet.
   - Output requiredRead, not answers.

4. **Inspect lifecycle compare dogfood before replacement**
   - Keep production legacy loop until logs prove safe.

5. **Add observability dashboard / compaction**
   - Summarize hook timings, route decisions, record-decision packets, graph hygiene, profile completeness.

6. **Capability Registry evaluation**
   - Evaluate real host capability evidence, then add/promote only justified capabilities.

## Rule placement

- Rule: This is a point-in-time framework evaluation and next-step recommendation, not permanent operating grammar.
- Scope: transient-planning / evaluation.
- Primary record: `.lazy-harness/planning/harness-structure-direction-evaluation-20260604.md`.
- Why not AGENTS.md: the evaluation includes mutable completeness scores and roadmap priorities.
- Why not `.jcode`: it concerns shared lazy-harness framework state, not local/private Jcode-only execution.

## Discovery capture

- DDD: none. No domain model change.
- SDD: candidate, Context Broker and D07 package health policy need follow-up contract decisions.
- BDD: candidate, Project Profile onboarding UX needs real host behavior coverage.
- TDD: candidate, generic-host D07 and context broker required-read behavior need regression fixtures.
- ADR: no immediate new architecture decision; future D07 policy and Context Broker promotion may require ADR/SDD option gates.
- SSOT: candidate, generic host validation/source-of-truth policy may need SSOT update.
- Planning: updated, this evaluation records current completeness, risks, and recommended next order.
