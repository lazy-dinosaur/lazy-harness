# ADR 0041 — Organic Hybrid Rule Guidance for Stored Rule Recall

- Status: Accepted for design direction
- Date: 2026-06-01
- Trigger: Dogfooding showed that stored rules can be missed at action time, but a hard-gate/tool-attached restoration made the workflow too slow and brittle.

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Applies when:
  - user asks how lazy-harness should remember and apply stored rules
  - 사용자가 저장한 규칙, 기억, 인지, 따르기, 응답 전후 쿼리를 이야기한다
  - planning rule guidance, pre-response context, response audit, or tool-specific policy migration
  - deciding whether to add blocking hooks, tool guards, record query, or organic guidance
- Must:
  - use C+ v2 organic hybrid: pre-response record query plus response.completed audit
  - keep mandatory record completion separate from organic action guidance
  - avoid broad slow edit/write blocking as the primary solution
  - avoid project policy authored as bash, gh, dev-cli, or MCP-specific rules
- Record completion:
  - architecture changes to rule recall update this ADR or a successor ADR
- Related records:
  - `.lazy-harness/planning/record-query-context-loop-transition-plan.md`
  - `.lazy-harness/ssot/harness-enforcement-policy.md`
  - `.lazy-harness/spec/platform/pre-response-rule-context.md`

## Context

Lazy-harness has two truths that must both remain true:

1. `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/` records are canonical institutional memory, not optional notes.
2. The agent workflow must remain organic, fast, and flexible enough that agents do not feel forced to fight the harness.

Dogfooding exposed a recurring failure:

```text
A rule is stored correctly, but an agent later fails to recall/apply it at the moment it matters.
```

Examples include any stored rule or decision, not just PR:

- Project identity / ownership / source-of-truth records being ignored after they were captured.
- API/component contracts in SDD not being applied when implementation changes.
- UI/user-flow behavior in BDD not being applied when planning or editing.
- TDD/regression expectations not being applied during bug fixes.
- ADR decisions not being followed in later design work.
- Runtime/dogfood rules stored in host SSOT but missed while reasoning about test instances.
- PR description rules stored in host SSOT but missed during PR drafting.
- Confirmed project/team rules being treated as chat memory instead of canonical records.

A 2026-06-01 experiment restored hard enforcement by reintroducing edit/write/multiedit blocking hooks and adding tool-attached runtime/dev-instance guards. It passed technical validation, but the user rejected it because:

- normal iteration became too slow,
- the design felt attached to concrete tools (`bash`, `gh`, `dev-cli`, GitHub MCP, etc.),
- it did not feel like a framework-level, organic rule guidance system.

That experiment is retained as a reverted planning record, not the target architecture.

## Decision

Adopt **C+ v2 Organic Hybrid Rule Guidance** as a framework operating-model change, not a narrow PR/runtime feature.

The core framework loop should change from:

```text
agent manually remembers AGENTS + searches records when it thinks to do so
```

to:

```text
record creation/update
→ record indexing/digest
→ relevant context returned before response/plan
→ response audit verifies use/capture
→ records evolve again
```

The framework should improve stored-rule recall through a layered, organic guidance model:

```text
pre-response relevant rule query
→ compact ambient rule context
→ normal agent response
→ response.completed audit/backstop
→ graduated guidance / journal update
→ narrow hard stops only for irreversible or repeatedly failed boundaries
```

This architecture keeps one important hard line:

- **Mandatory record completion remains mandatory.** Confirmed rules, source-of-truth corrections, decisions, behavior scenarios, contracts, and regression cases must still be written to the appropriate DDD/SDD/BDD/TDD/ADR/SSOT/planning record.
- **Action guidance should be organic.** For non-record action guidance, prefer pre-response relevant-record query plus response-completed audit instead of tool-specific guides or broad blocking.


## Design principles

### 1. Response lifecycle hooks are the policy surface

Hooks are still important, but the important hooks are response lifecycle hooks, not tool-specific policy branches.

Target shape:

```text
message.received / pre-response context step
→ relevant-record query
→ compact rule digest
→ model response
→ response.completed audit/backstop
→ record completion feedback
```

Jcode commit `3eb71ddb Add pre-turn message received hooks` provides the required same-turn pre-response surface. Lazy-harness wires this through `on-message-received.sh` with bounded `blocking = true`, `timeout_ms = 800`, and fail-open behavior.

Tool hooks should be limited to transport/safety/logging, not project policy:

- allowed: destructive shell safety, telemetry, generic event forwarding;
- deprecated: PR body policy in `gh`/bash branches, runtime policy in `dev-cli` branches, release/DB policy tied to a specific command or MCP tool.


Rejected direction:

```text
bash-specific PR guard
+ GitHub MCP-specific PR guard
+ dev-cli-specific runtime guard
+ release-tool-specific guard
+ more adapters...
```

Preferred direction:

```text
current user message + recent context
→ framework-level record query
→ compact relevant rule context before response
→ response.completed audit after response
→ user-visible nudge/warn/ask or rare hard stop only when justified
```

Tool-specific guides are deprecated as the policy layer. A tool can still emit lifecycle events or safety metadata, but PR/runtime/release/DB rules should not be authored as `gh` rules, `bash` rules, `dev-cli` rules, or GitHub MCP rules.

## Phase 5 implementation note

Implemented on 2026-06-01:

- `check-rule-action-boundary.py` was reduced to a no-op legacy compatibility shim.
- generated `.jcode/hooks/check-bash.sh` keeps only generic destructive shell safety.
- the historical PR body hard block moved to `message.received` digest surfacing plus `response.completed` response-rule audit.
- ADR 0039 and `.lazy-harness/spec/platform/rule-binding-action-boundary.md` are now superseded for project-policy enforcement.

## Phase 6 implementation note

Implemented on 2026-06-01:

- `.lazy-harness/spec/platform/guidance-ladder.md` defines the L0-L5 guidance ladder.
- `.lazy-harness/scripts/hard-stop-promotion-audit.py` validates canonical `## Hard-stop promotion` sections.
- concrete hard stops remain rare and require user confirmation, miss/risk evidence, existing softer coverage analysis, fixture path, narrowness, and rollback.
- no new project-policy hard stop was added by Phase 6; it added promotion criteria and fixtures first.

## Phase 7 implementation note

Implemented on 2026-06-01:

- Context Delivery can append sanitized packet evidence with `lazy context-delivery --journal`.
- `response.completed` may consume correlated packet evidence as advisory-only required-read feedback.
- Phase 7 intentionally does not add new STOP/hard-stop behavior; it creates dogfood evidence needed before any later escalation or Record Decision Broker integration.

## Phase 8 implementation note

Implemented on 2026-06-01:

- Added the Post-turn Record Decision Broker contract as `.lazy-harness/spec/platform/record-decision-broker.md`.
- Added `.lazy-harness/schemas/record-decision-packet.schema.json` with explicit `record-updated`, `candidate-needed`, `no-record-needed`, `option-gate-needed`, and `deferred` dispositions.
- Phase 8 intentionally changes schema/tests/records only; runtime `response.completed` behavior remains unchanged until false-positive-safe generator/audit fixtures exist.

Generator follow-up implemented after user selected Option A:

- Added `.lazy-harness/scripts/record-decision-broker.ts` and `lazy record-decision` as explicit/offline packet generator.
- The generator emits packet-shaped decisions from supplied evidence flags and does not mutate records, write journals, or run from `response.completed`.

Dogfood collector follow-up implemented after user selected Option B:

- Added `.lazy-harness/scripts/context-broker-dogfood.ts` and `lazy context-dogfood` as explicit/offline dogfood collector.
- The collector gathers sanitized Context Delivery and Record Decision observations from hosts before any response.completed shadow/advisory integration.

Dogfood handoff clarification:

- Normal development can accumulate automatic Record Decision shadow rows via `response.completed`.
- Aggregate Medivance/PWA Context Broker dogfood still requires the agent to run `lazy context-dogfood` explicitly when the user asks to check dogfood.
- The user should not need to prepare inputs manually; the runbook lives in `.lazy-harness/spec/platform/context-broker-dogfood.md`.

Response shadow follow-up implemented after generator and dogfood collector evidence:

- Added `.lazy-harness/hooks/lifecycle/helpers/check-record-decision-shadow.py` to run the deterministic Record Decision generator from `response.completed` lifecycle evidence.
- The helper journals sanitized `.lazy-harness/state/record-decision-packets.jsonl` observations and stays silent by default.
- Optional advisory output requires `LAZY_RECORD_DECISION_SHADOW_ADVISORY=1`; this is not hard-stop promotion and does not change default runtime output.

### 2. Rule context is queried before the response

The preferred organic mechanism is a small relevant-record query before the agent commits to an answer or plan.

The query is not a broad blocking scan. It should:

- use the current user message and recent lightweight context,
- search only root-bound `.lazy-harness` records,
- return a compact ranked set of relevant rules/records,
- be cacheable/index-backed where possible,
- be safe to skip only when the request is clearly context-free.

This means a PR request naturally receives PR description records, a runtime/test-instance request naturally receives dogfood/runtime records, and a correction naturally receives rule-placement/SSOT capture obligations without binding that logic to a specific tool.

### 3. Response completion is the audit/backstop

`response.completed` should remain the place that checks whether the response ignored surfaced rules, missed rule placement, or failed to capture confirmed facts.

This is different from broad pre-tool blocking:

- pre-response query helps the model remember before answering,
- post-response audit catches misses and updates guidance/journal state,
- only promoted high-risk cases become hard stops.

### 4. The target should be faster than broad blocking

This architecture is expected to be faster than the reverted hard-gate experiment because it avoids blocking every edit/write/multiedit call.

Performance requirement:

- A normal turn should pay at most one small relevant-record query plus the existing response audit.
- The query must be measured and kept compact.
- Naive full-record grep on every turn is not acceptable as the final implementation.
- If indexes/caches are not ready, implementation should start in measurement/shadow mode before becoming user-visible.

Token budget requirement:

- Do not inject full records by default.
- Return at most a compact digest: record path, rule title, and 1–3 relevant bullets.
- Default target: 200–600 tokens per context injection.
- Hard ceiling for normal turns: 1,000 tokens.
- If more context is needed, surface paths and ask/read deliberately rather than dumping documents.
- `response.completed` audit should cost zero user-visible tokens when there is no issue.

Effectiveness hypothesis:

- This should be more effective than prompt-only AGENTS recall because the relevant rule is placed in the local working context immediately before the answer.
- This should be less disruptive than broad blocking because it does not interrupt every edit/write/tool call.
- This should be less brittle than tool-specific guards because the query is driven by records and conversational/action context, not a concrete tool name.

This hypothesis must be tested with dogfood fixtures and token/latency measurements before broad rollout.

### 5. Default posture is ambient, not blocking

The first line of defense should be small, ranked context that helps the model remember relevant records naturally.

Examples:

- User mentions PR: surface PR description/body SSOT if present.
- User mentions test instance/runtime/dev server: surface runtime/dogfood SSOT if present.
- User corrects source-of-truth ownership: surface rule-placement/SSOT capture obligation.

### 6. Guidance escalates by evidence

Rules should participate in a graduated ladder:

```text
ambient → nudge → warn → ask → hard stop
```

Promotion requires evidence, such as:

- explicit user mandate,
- high cost of missing the rule,
- repeated dogfood miss,
- irreversible/external mutation,
- stale approval or ignored user correction.

Demotion is allowed when a rule proves noisy or too broad.

### 7. Continuity is maintained by a soft action journal

Instead of rigid action tickets, lazy-harness should keep lightweight continuity metadata:

```text
current intent
relevant records surfaced/read
required artifact expectations
validation evidence
stale approval markers
```

The journal is normally guidance/context. It becomes enforcement input only near narrow hard-stop cases.

Subagent handoff benefit:

- The coordinator can pass the compact rule digest and journal state to subagents without copying full records.
- Subagents receive the same relevant constraints regardless of which tools they use.
- This reduces the chance that delegated work loses PR/runtime/release/domain rules during handoff.
- Handoff payload should stay small: current intent, top relevant records, required artifact expectations, and validation evidence.

### 8. Hard stops are narrow and framework-level

Hard stops remain valid, but must be justified by framework-level rule state, not by ad hoc tool branches.

Initial candidates:

- destructive/irreversible operations,
- stale requirements approval,
- explicit user correction ignored without record capture,
- repeated failure class promoted after dogfood evidence.

## Options considered

### A. Tool-specific guard sprawl

Attach policy checks directly to each tool surface.

- Pros: easy to add one case quickly.
- Cons: brittle, hard to generalize, misses alternate tools, makes framework feel like patchwork.
- Decision: rejected as primary architecture.

### B. 2026-05-19-style broad blocking

Use broad edit/write/multiedit blocking gates to force record-first behavior.

- Pros: strong safety net.
- Cons: slows normal iteration, encourages bypass, does not naturally solve non-edit intent recall.
- Decision: rejected as primary architecture.

### C. Rigid Action Gate / ticket model

Require explicit action tickets and policy validation before meaningful actions.

- Pros: precise, auditable.
- Cons: can feel bureaucratic and interrupt organic agent flow.
- Decision: not selected as first design. A lightweight journal may borrow useful concepts.

### D. Prompt-only / skill-only reminders

Rely on AGENTS, skills, and prompt overlays.

- Pros: organic and low overhead.
- Cons: dogfooding already showed prompt recall drift.
- Decision: insufficient alone.

### E. Ambient rule context only

Inject relevant records/context without escalation or hard stops.

- Pros: fast, natural.
- Cons: no protection for repeated/high-cost misses.
- Decision: useful base layer but incomplete.

### F. C+ v2 organic hybrid

Combine ambient context, graduated guidance, soft action journal, and narrow hard stops.

- Pros: preserves flow while creating a path to reliable rule recall.
- Cons: requires careful design and measurement before implementation.
- Decision: chosen.

## Consequences

Positive:

- Keeps lazy-harness framework-level instead of tool-adapter-level.
- Preserves fast iteration by avoiding broad edit/write blocking.
- Still allows mandatory rules to escalate when evidence justifies it.
- Gives performance work a clear target: optimize context/guidance, not remove safety.
- Makes subagent delegation cleaner because rule context is a portable digest/journal rather than tool-specific instructions.

Risks:

- Ambient guidance could be too weak if ranking is poor.
- Too much context injection could become noise.
- Promotion/demotion policy needs tests and dogfood telemetry.
- Existing tool-attached exemplars must be migrated carefully rather than abruptly removed.

## Migration policy

- Do not add new one-off tool-specific guards for PR/runtime/release/DB rules unless a separate emergency ADR justifies it.
- Existing rule-binding exemplars may remain temporarily, but future work should migrate them into the organic hybrid model.
- Start implementation with measurement and read-only/ambient context surfacing before any new hard stop.
- Hard-stop promotion requires a record, a fixture, and dogfood evidence.

## First-pass implementation scope

The first pass should not start with subagent handoff, swarm orchestration, or tool-specific guards.

The first pass should transform the existing harness loop around document completeness and relevant rule recall:

1. **Pre-response relevant record query**
   - Given the current user message and recent lightweight context, find a compact set of relevant `.lazy-harness` records.
   - Return a digest, not full documents.
2. **Compact rule digest injection**
   - Inject or surface only the path, rule title, and 1–3 bullets needed for the next response.
   - Keep the normal target at 200–600 tokens and ceiling at 1,000 tokens.
3. **Normal response/planning**
   - The agent uses the digest organically rather than following a tool-specific checklist.
4. **Response-completed audit/backstop**
   - Check whether surfaced rules were ignored, confirmed facts were not recorded, or rule placement was missing.
   - No user-visible output when there is no issue.
5. **Record-as-output completion**
   - When the user confirms a rule, decision, scenario, bug/regression, or source-of-truth correction, converge it into the correct DDD/SDD/BDD/TDD/ADR/SSOT/planning record.

Subagent handoff is a later beneficiary of the same digest/journal model, not the first implementation target.

## Implementation path

### Phase 0 — Measurement and baseline

- Measure current response lifecycle latency.
- Record where rule recall currently fails.
- Keep existing source and dogfood self-tests passing.

### Phase 1 — Ambient rule context resolver

- Given user message + recent tool/context metadata, resolve ranked relevant records.
- Output a compact context summary, not a block.
- Use root-bound `.lazy-harness` records only.
- Prefer an index/cache-backed query path; full grep is acceptable only as a measurement/prototype baseline.
- Treat the result as pre-response context, not tool-specific guidance.

### Phase 2 — Guidance ladder metadata

- Add a small schema for guidance levels: ambient, nudge, warn, ask, hard-stop.
- Let records opt into levels, but default conservatively.

### Phase 3 — Soft action journal

- Track current intent, surfaced records, read records, expected artifacts, and stale approval markers.
- Keep journal lightweight and inspectable.

### Phase 4 — Narrow hard-stop promotion

- Promote only repeated/high-cost cases with fixtures and user-confirmed policy.
- Hard stops must be framework-level and transport-independent.

## Validation

Any implementation of this ADR must validate:

- Source `.lazy-harness/scripts/self-test.py`.
- Source `python3 .lazy-harness/scripts/doctor.py --profile smoke`.
- Medivance dogfood sync + `.lazy-harness/bin/lazy test`.
- Medivance PWA dogfood sync + `.lazy-harness/bin/lazy test`.
- Latency before/after for relevant lifecycle paths.
- Fixtures proving relevant rules surface before action without broad blocking.
- Fixtures proving promoted high-risk cases still hard-stop.
- Fixture proving the relevant-record query returns PR/runtime/correction records without depending on a concrete tool name.

## Implementation map

- Status: `design-direction-accepted`
- Primary records:
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` — this ADR.
  - `.lazy-harness/planning/organic-hybrid-rule-guidance-plan.md` — active planning record.
  - `.lazy-harness/ssot/harness-enforcement-policy.md` — user-confirmed enforcement policy anchor.
  - `.lazy-harness/planning/harness-enforcement-restoration-plan.md` — reverted hard-gate experiment memory.
  - `.lazy-harness/planning/performance-optimization-plan.md` — performance plan that must preserve this direction.
  - `.lazy-harness/planning/record-query-context-loop-transition-plan.md` — comprehensive transition plan for record digest/query/audit migration.
  - `.lazy-harness/spec/platform/record-digest-format.md` — Phase 1 SDD for compact rule digest sections.
  - `.lazy-harness/spec/platform/record-write-update-policy.md` — Phase 1 SDD for update-vs-create and digest maintenance behavior.
  - `.lazy-harness/spec/platform/relevant-record-query.md` — Phase 2 SDD for natural-intent record lookup and compact digest output.
  - `.lazy-harness/schemas/relevant-record-index.schema.json` — Phase 2 schema for generated relevant-record cache.
  - `.lazy-harness/scripts/search-provider.ts` — fallback SearchProvider path model aligned to current canonical record dirs.
  - `.lazy-harness/spec/platform/pre-response-rule-context.md` — Phase 3 SDD for Jcode `message.received` pre-turn context injection.
  - `.lazy-harness/scripts/relevant-record-query.ts` — Phase 3 read-only query prototype and `lazy context` backend.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — Phase 3 Jcode hook that emits same-turn `system_reminder` injections.
  - `.lazy-harness/planning/native-context-broker-implementation-plan.md` — follow-on retrieval plan for self-resolving context delivery.
  - `.lazy-harness/spec/platform/context-delivery-contract.md` — Native Context Broker packet contract for raw hits, normalized evidence, required reads, rendering, privacy, and fail-open behavior.
  - `.lazy-harness/schemas/context-delivery-packet.schema.json` — schema for packet-shaped self-resolution or searcher handoff output.
- Candidate future files:
  - `.lazy-harness/spec/platform/organic-rule-context.md`
  - `.lazy-harness/spec/platform/soft-action-journal.md`
  - `.lazy-harness/tests/organic-rule-context-surfacing.md`
- Cross-layer links:
  - ADR 0037 — workflow compression, not safety reduction.
  - ADR 0038 — requirements-first change gate.
  - ADR 0039 — rule lifecycle bindings, now constrained by organic-hybrid migration policy.
  - ADR 0040 — capability registry kind/level separation, a possible input to ambient guidance, not the whole architecture.

## Rule placement

- Rule: use C+ v2 organic hybrid rule guidance as the target architecture for reliable stored-rule recall; avoid broad slow blocking and tool-specific adapter sprawl.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
- Why not AGENTS.md: this is an architecture decision; AGENTS should only change after implementation details are selected.
- Why not `.jcode`: this is shared lazy-harness framework design, not local/private Jcode-only workflow.
- Confirmation: user-confirmed
