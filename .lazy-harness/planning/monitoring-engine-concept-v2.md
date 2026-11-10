# Planning — Monitoring engine concept v2 (declared purpose → fast Jev hand-off → routed action)

Status: concept (stages 1–5 drafted); implementation slices S0–S7 executed one by one under per-slice user approvals; execution log lives in `.lazy-harness/planning/monitoring-core-live-integration-plan.md`

## Rule digest
- Status: draft
- Layer: Planning
- Scope: framework-global
- Aliases:
  - monitoring engine v2
  - 모니터링 엔진 구상
  - 목적 선언 라우팅
- Applies when:
  - designing how monitoring modules declare purpose, information scope, target and action
  - planning routing of Jev-selected information to the parent or to background actions
- Must:
  - extend the existing monitoring configuration contract v1 (`packages/lazy-harness-pi/monitoring/schema.ts`, `defineMonitoringModule`) instead of creating a second contract
  - keep routing separate from permission: risk tier and grants are part of every declaration
  - keep measured evidence in `.lazy-harness/planning/monitoring-core-live-integration-plan.md` and the TDD records; this document holds the concept only
- Must not:
  - start implementation or model calls from this draft without explicit approval

## Confirmed requirement
Through Jev, all information matching a registered monitoring goal is handed off quickly and directly. The target is the parent (main-agent context) or a background/external path that does not need the parent. The engine therefore knows each module's purpose and the action it must trigger, and routes by that declaration (recorded in the live-integration plan, 2026-11-03).

User correction (2026-11-03, confirmed override, refined): the thing being MONITORED is the agent itself — its conversation and its tool calls/results. Every monitoring module has its OWN purpose; watching the agent against that purpose is what fires its trigger, and the trigger runs that module's declared actions so the agent ends up behaving the way we want. There is no separate engine-level "reference context" layer: things like a todo list or rule text are just inputs that a particular module's purpose needs (e.g. a todo-sync module needs the current todo list to judge and to update it). Earlier wording that treated the todo list as a monitoring source or as general reference context is superseded.

## Method (proposed by Parent, accepted for planning)
1. Use cases → 2. module declaration contract v2 (extend v1) → 3. engine flow and mapping of existing parts (reuse/change/new) → 4. safety and latency budgets → 5. staged implementation plan with acceptance per slice. Option gates at each decision; code only after plan approval.

## Stage 1 — use cases (draft)
These are representative EXAMPLES chosen to test whether the contract and engine design cover enough variety (targets, input forms, risk tiers, sources). They are not a committed feature list or build order; only U1/U2 have measured evidence.
| # | Use case | Purpose (what to watch) | Information | Target | Input form | Risk tier | Depends on |
|---|---|---|---|---|---|---|---|
| U1 | Reference delivery | user needs current project evidence now | current input, recent turns, knowledge docs | parent context injection | selected originals | read-only | measured (judge + mailbox) |
| U2 | Knowledge candidate | user firmly adopts/confirms/corrects an enduring decision | current input, recent turns | background record | worker-composed sentence or verbatim quote + evidence | proposal/record (user confirms) | measured (judge + Luna) |
| U3 | Work assistant (비서) | a tracked work item/task reaches its completion condition, or the next goal becomes due | current turn events incl. tool calls/results (tests, commits), harness work records (goal, completion condition, progress) | parent context ("X completed at T; next goal Y") and user-visible notification; background progress record | selected originals + worker summary of next goal | proposal (suggest; completion is confirmed, not inferred from agent_end) | work-management module not implemented (`.lazy-harness/domain/work-management.md`, schema proposal advisory) |
| U4 | Todo auto-update | a todo item is started/finished/blocked by observed work | current turn events, current todo list | background action on the todo tool | structured {id, status, evidence} | automatic execution if unconfirmed (≤0.5% false-trigger gate) or proposal if confirmed | todo tool exists (`@juicesharp/rpiv-todo`); action adapter not built |
| U5 | Risk alert / automatic action | dangerous command, secret exposure, destructive operation | tool calls/arguments | external notification / block request | selected originals | automatic execution | permission model, consent for tool arguments |
| U6 | Behaviour steering | the agent deviates from how we want it to work (skips grounding/reading records, edits without tests, ignores a stated rule, loops on the same failure) | agent conversation, tool calls/arguments/results, applicable rule records | parent context reminder/steer; background violation record; external block request for dangerous cases | selected originals (+ rule excerpt) | proposal for reminders; automatic only for blocking | rule records exist; steering action adapter not built |

U6 clarified with the user: when the agent breaks one of its working rules, Jev picks WHICH rule (rules are candidate items, e.g. from `.lazy-harness/ssot/policies.json` pre-filtered by appliesTo) plus the evidence, and a template job injects that rule's text and the offending action into the parent (report: always) via the carry mailbox. This is post-action steering; preventing the action before it runs needs a synchronous pre-tool path. Needs per-rule/per-turn dedup against nagging and its own false-trigger acceptance set.

Notes:
- U3/U4 add a new source of truth: harness work records and the todo list are read as references; completion must be evidenced (tool results, user confirmation), never assumed from a run ending.
- U3 shows one judgement can fan out to several targets (parent + notification + record); the contract must allow multiple targets per module or separate modules sharing a question.
- U4/U5 are the first automatic-execution cases; they need their own acceptance sets sized for ≤0.5% false-trigger.

## Stage 1 decisions (user-confirmed, native option gate 2026-11-03)
1. Declaration shape: **one module = one purpose (one Jev question) + several declared actions**. The judgement runs once; each action has its own target (parent context / background / external), input form (selected originals / worker-composed), risk tier and grants. No duplicated judgement cost, no diverging decisions between targets.
2. U3 start: **start U3 and U4 together with the existing todo list as the interim work record**. Triggers come from watching the agent's conversation and tool calls against each module's purpose; the todo list is an input those modules' purposes need (which work exists, status/dependencies) and the target they update. It sits behind a replaceable adapter so the work-management module can replace it later.
3. Next goal: **recorded order and dependencies first** (blockedBy, pending order), chosen deterministically; worker inference only when records are insufficient, labelled as a suggestion.

## Stage 2 — module declaration contract v2 (DRAFT, not approved)

Grounding (source read): v1 separates DATA configuration (`MonitoringConfigurationSchema`: contractVersion, source, goal, receiver, judge, modules[{id, version, settings}], references, limits) from HOST CODE bindings (`defineMonitoringModule({version, settingsSchema, grants, destination, create → Processor{id, eventKinds, referenceKinds, allowedActions, question, run}})`, `prepareMonitoringBindings` with host ceilings). v2 keeps that split: the module author declares purpose and actions in code; the host grants ceilings; data configuration can only select, disable or tighten.

### Module binding v2 (author-declared, code)
```
defineMonitoringModule({
  version, settingsSchema,
  purpose: { question: JudgeQuestion },                 // ONE Jev question per module
  watch: {
    events: [...],                                      // e.g. input, tool_result
    info: {
      kinds: [...],                                     // user-text, assistant-text, tool-call, tool-result, knowledge, ...
      history: { turns: 0..8, granularity: 'message' },  // per-message items so Jev can pick only what is needed
      needs: [{ id, adapter }]                          // extra inputs THIS module's purpose requires (e.g. current todo list, rule text); not the monitored source
    }
  },
  actions: [{
    id, target: 'parent-context' | 'background' | 'external',
    on: ['run'],                                        // decision modes that fire this action
    inputForm: 'selected' | 'composed',
    inputSchema?, compose?: { workerProfile, instructions },   // only when composed; selected bodies are inlined (one dispatch)
    riskTier: 'read-only' | 'proposal' | 'automatic',
    grants: { referenceKinds, actions },
    idempotency: 'per-event' | 'per-subject',          // dedupe key = module.action.event|subject
    delivery?: { carryTurns: 0..1, maxAgeMs }          // parent-context only (ContextCarryMailbox)
  }],
  acceptance: { setRef, targets }                       // per-module gold + tier targets
})
```

### Data configuration v2 (user/host data)
`modules[{ id, version, settings, actions?: [{ id, enabled?, riskTier? }] }]` — may disable an action or make its tier STRICTER, never looser; never adds targets or grants.

### Host bindings v2
Per-action grant ceilings, allowed targets, worker profiles, source adapters, carry limits. Missing binding = fail closed (as v1).

### Engine invariants (draft)
- One Jev call per event batches all watching modules (decision + per-item selection); split when >64 answers or >64KiB.
- User-confirmed requirement (task154): modules decide and trigger INDEPENDENTLY — each module has its own trigger points, its own last-judged cursor and between-region input, its own material budget and its own decision; one module's size, failure or timing must never change another module's input or outcome. Physically sending several modules' judgements in one Jev request is only an optional transport optimisation when they trigger on the same event, and is allowed only while it keeps those guarantees (separate budgets, isolated failure). Measured basis: Jev bills input tokens only and a batched request already repeats shared items per module (t43), so batching saves HTTP requests, not tokens.
- Selection is per module and shared by its actions; an action may further restrict by kind.
- Redaction and size bounds apply to every item BEFORE Jev; only declared/consented kinds are visible.
- Loop guard: events produced by monitor actions carry origin metadata and are not re-judged by the module that produced them; bounded depth for others.
- Idempotency key per action; receipts via existing C1 consumer; automatic actions keep the ≤0.5% gate and confirmation policy.
- Latency budget: selection-only paths target hand-off within ~1s p95 (judge measured ≈0.4s); composed paths ≈3s target (one worker dispatch).

### Coverage check against the examples
| Example | purpose | actions (target / form / tier) |
|---|---|---|
| U1 references | needs project evidence now | parent-context / selected / read-only, carry 1 |
| U2 knowledge | firm enduring decision | background record / composed or selected quote / proposal |
| U3 work assistant | tracked item reached completion or next goal due | parent-context / selected+composed summary / proposal; external notification / selected / proposal; background progress record / composed / proposal |
| U4 todo update | todo status change evidenced | background todo.update / composed {id,status,evidence} / automatic or proposal (data config may tighten) |
| U5 risk alert | dangerous command or secret exposure | external alert / selected / automatic |

### Run model and parent reporting (user direction 2026-11-03)
A triggered module runs its job in the background and can simply finish there, or also tell the parent agent. Whether to tell the parent is chosen by the USER (data configuration per module/action), not by the worker at runtime and not fixed by the author: `report: never | always | on-result`. The module author only declares which report modes it supports and a default; on-result means the job reports only when its result is meaningful to the parent, with a reason. Reports go through the late-result carry policy (same turn, else next turn once, 120s, unchanged sources). Exception: actions that must act BEFORE a tool runs (e.g. blocking a dangerous command) are synchronous hook paths, not background jobs.
Examples confirmed with the user: a knowledge ABSORPTION module receives the selected content, runs its absorption sequence in the background and just finishes (report: never). A rule-violation module or a "what to do in this situation" module runs its worker and delivers the result to the parent (report: always or on-result). Same engine path; only the module purpose, its background job and the user-chosen report mode differ.

### Stage 2 decision ① — no engine-level defer handling (user-confirmed 2026-11-03)
The engine only judges whether the agent's activity matches a module's purpose (trigger or not) and selects the information. How an ambiguous or pending situation is handled is decided by each module inside its own purpose and job (e.g. a knowledge-absorption module may also list pending decisions). Every judgement is recorded in detail — module, event/source refs, the input seen, selected items, decision, confidence and reason — so ambiguous cases can be reviewed later and used to evaluate and tune modules. That judgement log contains conversation content and therefore needs bounded retention and the same consent scope as the monitored data.

### Stage 2 decision ② — select once per module (user-confirmed 2026-11-03)
Amendment (user-confirmed option A, task154): purpose-scoped region compaction is an INPUT PREPARATION step, not a second judgement. A module that declares the need `region.compact` gets one extra Jev call per trigger in which Jev keeps only the between-region items its purpose needs (verbatim); decision ① “judge at most once per module per trigger” applies to the match + evidence judgement that follows. Reason (user correction): Jev compaction must bring only the information that fits the module's monitoring purpose, not a code-side generic cut.
A module has one purpose, so the ENGINE runs Jev at most once per trigger for that module (match + evidence selection); each external job takes only what it needs from that shared selection. What the module does internally afterwards (e.g. many per-unit Jev/Luna calls in its own role chain) is the module's business, not engine selection. If two EXTERNAL jobs would need entirely different evidence, the module has two purposes and should be split; internal roles are not split into modules.

### Feedback from the knowledge-module session (LH-2, 2026-11-03)
Their module (v2 knowledge-digest runner: source → atomic units → Jev placement → Luna write → SDK review → grounding check → knowledge DB ingest) would need: user turns, assistant final answers, record-judgement confirmed facts, tool results that changed `.lazy-harness` records (path, revision/sha); evidence = verbatim spans + session entry id + file sha, never inferred from tool args alone. Background only, report on-result, never a sync tool block. Output is a CANDIDATE (agents read first, humans review); Luna sentences must each be grounded in verbatim quotes + provenance. Contract changes requested: (a) engine selection once per trigger; internal Jev calls are module-owned; (b) module-defined idempotency (ledger/epoch/checkpoint) and a terminal "uncertain effect = stop, never retry" state; (c) cost/egress declaration with per-run caps (sdk/jev/embedding/cash) and a user-approved budget gate BEFORE a paid job starts; (d) internal role chains inside one module. Also: define canonical JSON serialization explicitly across JS/Python for every hash.

### Stage 2 decision ③ — how a job builds its output (user-agreed for now, 2026-11-03)
Cheapest sufficient method first: (1) fixed template filled by code, (2) Jev selection/matching (e.g. "which todo item does this evidence complete?"), (3) Luna only when the job must reason across evidence, summarise a long span or write advice. When Luna is used, the Jev-selected originals are inlined into ONE call (no read_material round trips), and every generated sentence stays grounded in verbatim quotes + provenance (quote bundle is the source of truth; sentences are derived and re-checkable). Records produced by monitoring are candidates by default; final canonical wording can be written at user confirmation. Internal role chains (as in the knowledge-digest runner) are allowed inside one job.

### Stage 2 decision ④ — module options vs engine rules (user-agreed for now, 2026-11-03)
Module-declared OPTIONS: job form (template / Jev selection / Luna / internal role chain), report mode never|always|on-result (author default, user may change), idempotency key (per-event / per-subject / module-defined ledger·epoch·checkpoint), extra inputs (`needs`), output nature (candidate default / final), cost & egress declaration with per-run caps (sdk/jev/embedding/cash).
ENGINE RULES (always enforced, not optional): user-approved budget gate before any job that declares cost; terminal "uncertain effect = stop, never retry"; risk tier and grant ceilings (user configuration may only disable or tighten; automatic execution keeps the ≤0.5% false-trigger gate); loop guard; one canonical JSON serialization for every hash across JS/Python; judgement log with bounded retention and consent scope; redaction and size bounds before Jev.

## Stage 3 — engine flow and mapping of existing parts (DRAFT, not approved)

### Flow per observed agent event
1. **Observe** — SDK hook frame (conversation message, tool call, tool result).
2. **Prepare items** — current items + recent history as per-message items + tool calls/results; redaction and size bounds; only kinds declared by watching modules.
3. **Admit** — bounded job per event with lifetime/currentness (session, branch, intent, source versions).
4. **Judge + select (one batched Jev call)** — for every module watching this event: matches purpose? + which items are evidence; split when >64 answers/64KiB. Every judgement goes to the judgement log.
5. **Route by declaration** — for each triggered module: loop guard → idempotency key → budget gate (if the job declares cost) → background job (template / Jev matching / inline worker / internal role chain) with receipts; uncertain effect = stop.
6. **Report** — per the user's report mode: carry mailbox → parent context hook injection (same turn, else next turn once), or an external notification adapter, or nothing.
- Separate synchronous path: modules that must act BEFORE a tool runs (block/confirm) use a pre-tool hook, not steps 3–6.

### Mapping
| Step | Existing part (path) | Verdict | Change needed |
|---|---|---|---|
| 1 Observe | `PiMonitoringObserver`, `createPiObservationExtension` (`packages/lazy-harness-pi/extensions/lazy-harness/monitoring-observer.ts`) | reuse | none known |
| 2 Prepare | `RealtimeMaterialWindow` (`.lazy-harness/scripts/monitoring-core-realtime-material.ts`, opt-in `historyTurns`) | change | per-message history items instead of one blob; tool-call/argument items per declared kinds; redaction hook before judge |
| 3 Admit | `RealtimeMonitoringCoordinator` (`monitoring-core-realtime.ts`) | reuse | none known (intent/step/source lifetimes, bounded queue) |
| 4 Judge+select | `RealtimeSelectionBridge` / `createRealtimeSelectionPipeline` (`monitoring-core-realtime-selection.ts`), `MonitoringCore`, model router (`packages/lazy-harness-pi/monitoring/`) | change | consume v2 declarations; one batched call across modules per event (verify current batching); emit judgement log rows; keep `includeCurrentMaterial` |
| 4 Log | — | NEW | judgement log store with bounded retention and consent scope |
| 5 Route | — (evaluator-only wiring today) | NEW | module runtime/router reading v2 declarations; loop guard (origin tag); idempotency registry |
| 5 Budget | `Budget`/`createMeteredRequest` (`monitoring-retrieval-poc.ts`, evaluation only) | NEW (production) | user-approved per-module/per-run budget gate before paid jobs |
| 5 Jobs | `RealtimeExecutionConsumer` (C1, `monitoring-core-realtime-execution.ts`) | reuse | confirm no-retry on unknown; module-defined idempotency key |
| 5 Worker | `createPiWorkerExecutionPorts` (`monitoring-core-pi-worker.ts`) | change | inline mode: selected bodies in the prompt, one dispatch (keep fail-closed reads) |
| 6 Parent report | `ContextCarryMailbox` (`monitoring-core-context-mailbox.ts`) | reuse + wire | context-hook injection wiring in the live host (D1 proved the wire path in isolation) |
| 6 External | — | NEW | notification adapter(s) |
| Contract | config schema v1 + `defineMonitoringModule` (`packages/lazy-harness-pi/monitoring/schema.ts`, `bindings.ts`) | change | v2 declaration fields and validation; data config may only disable/tighten/choose report mode |
| Hashing | ad-hoc `sha256(JSON.stringify(...))` in several scripts | NEW | one canonical JSON serialization shared by JS and Python |
| Sync path | — | NEW (later) | pre-tool hook for blocking modules |
| Activation | manual pilot controls (`monitoring-core-pilot.ts`) | reuse | opt-in start/stop per module |
| needs adapters | — | NEW | todo adapter (interim work record), rule source adapter (`policies.json`) |

### Observations
- Most of the pipeline already exists and is measured in isolation; the main missing piece is the **module runtime/router** that turns v2 declarations into steps 4–6, plus the engine-rule components (judgement log, budget gate, loop guard, canonical hashing).
- Two existing parts need behavioural changes (per-message history, inline worker); both were motivated by measurements (context misses, 7.5s worker latency).

## Stage 3b — trigger points: WHEN a module may act (DRAFT, task154, not approved for code)

User direction (task154): fix the monitored events first and define as many “when to act” points as possible; a module's input is then everything since its last judged point. Grounded in the Pi 1.5.0 inventory (`.lazy-harness/spec/platform/pi-monitoring-observation.md` § Pi 1.5.0 observable-channel inventory). Each point = source event + deterministic condition; what is known there; what a module may do there.

| Point | Source + condition | Known at that moment | Possible action there |
|---|---|---|---|
| `user.prompt` | `input`, no `streamingBehavior`, source interactive/rpc | raw user text | inject at `run.start`, background |
| `user.steer` | `input` with `streamingBehavior: steer` | mid-run user correction | steer, next-context inject |
| `user.follow-up` | `input` with `streamingBehavior: followUp` | queued request | inject at its run start |
| `user.shell` | `user_bash` | user `!`/`!!` command | intercept (blocking module only), record |
| `run.start` | `before_agent_start` (`messageType` user/custom) | expanded prompt, system prompt options | inject one message, patch prompt sections |
| `model.before-call` | `context` (every model call) | messages about to be sent | inject pending reports (carry mailbox) |
| `assistant.stream` | `message_update` | partial text/tool-call deltas (speculative) | early background preparation only |
| `assistant.message` | `message_end` role assistant | final assistant text + tool-call list | next-context reminder |
| `tool.before` | `tool_call` | tool name + final args (incl. file paths) | block / mutate (blocking tier), pre-action steer |
| `tool.after` | `tool_result` / `tool_execution_end` | result, isError, duration | next-context reminder, background |
| `tool.failed` | `tool_execution_end` with `isError` (also blocked/invalid calls) | error result | reminder |
| `tool.nested` | any tool event with `parentToolCallId` | calls hidden from the transcript | observe/record |
| `turn.end` | `turn_end` | the persisted assistant message + all its tool results | append `custom_message`, request one continuation — the default **between-region boundary** |
| `run.end` | `agent_end` | one low-level run (more work may follow) | observe |
| `run.before-settle` | `agent_before_settle` | whole run, last actionable moment | append a final reminder + continue once (end-of-work checks) |
| `run.settled` / `run.aborted` | `agent_settled` (`aborted`) | final state | background record, external notification |
| `session.start` | `session_start` (`reason` startup/reload/new/resume/fork) | session identity | reset module cursors/state |
| `session.compact` | `session_compact` | compaction summary | reset already-read lists; summary as module state |
| `session.tree` / `session.switch` / `session.end` | `session_tree`, `session_before_switch/fork`, `session_shutdown` | branch/session change | reset or rebind |
| `model.changed` | `model_select`, `thinking_level_select` | new model/level | observe |
| `ui.waiting-user` | `ui_prompt_start/end` | agent waiting for the user | defer delivery |
| `extension.message` | `message_end` role custom, or user-role content authored by an extension (incl. lazy-harness `<system-reminder>`) | non-human input | origin tagging; never treated as the user |
| derived | deterministic counters over the points above: repeated same failure, N tool calls without a test, file touched (from `tool.before` args) → implementation-map records | — | input for the modules above |

Not observable as a point: extension commands (`/name`, no `input`); provider transport stages are registered but debug-only. Between-region input (user proposal): per module, everything since its last judged point, with tool calls compressed to name + target + outcome, origin-tagged, plus short module state (goal/todo/already-read), within the material window budget. Open decisions before code: whether `watch.events` names these points (contract change) or stays raw event names with conditions; the default boundary per module; summary rules for the between-region.

Stage 3b decision (user-confirmed option A, task154): modules declare WHEN they check using these point names in `watch.events` (raw hook names stay accepted for compatibility); configuration data may only SELECT a subset of the declared points (narrowing, consistent with “data may only disable/tighten”), never add points. Reason: adding a point changes what the module sees, its cost and its accuracy, which would need re-acceptance. Code plan pending execution approval.
Stage 3b implemented (execution-approved, task154, model calls 0): trigger-point catalogue, declaration validation, configuration narrowing, engine resolution and independent per-module pipelines — contract in `.lazy-harness/spec/platform/monitoring-core.md` § Trigger points and independent module pipelines. Pending: per-module between-region input, evaluator switch, live wiring.
Between-region rules (user-confirmed, task154): input = everything since the module's own last judged point; first judgement from the session head within budget; long regions keep originals for user/assistant text and summarise tool calls (name + target + ok/error), newest first, omitted items marked, Jev used to compact an over-budget region (user proposal; current code uses the judge's own per-item selection as compaction and a deterministic newest-first fallback; the Jev pre-pass is pending); context outside the region = module memo, option A (judge-selected originals + deterministic state, no generated summary); compaction restarts from the summary head; every item origin-tagged; the start moves after any completed judgement and stays after a failure. Implemented in the material window (`historyMode: 'since-last'`, `markJudged`) — contract in `.lazy-harness/spec/platform/monitoring-core.md`.

## Stage 3c — use-time tuning loop (user-confirmed, task154)

Requirement (user): the core must let us tune, judge accuracy, debug, test and dogfood WHILE it is in use. Three layers (user-confirmed recommendation): (1) **core** = the engine plus its inspection ports; (2) **one shared evaluation tool** that every module plugs into (not re-implemented per module); (3) **modules** own purpose, trigger points, inputs, jobs and their own gold set. Data is kept per module: traces, feedback marks and gold sets are separated by module id; only the observed session source is shared.

Loop: run a module in observe/shadow → every judgement leaves a trace → the user marks wrong/missed/ok with an explicit command → marks become gold candidates (user-confirmed) → a new module version is replayed on those traces by the shared tool and compared → when the shadow results meet the module tier the user may promote it to active.

Step 1 design (core, next to implement):
- **Run stage per module**: `off | observe | shadow | active`. The declaration states the highest stage the author allows; configuration data may only lower it (narrowing rule). observe = judge + trace, no job; shadow = judge + job with effects and reports withheld (output kept in the trace); active = normal delivery.
- **Judgement trace** (`monitoring-trace/v1`, one JSONL line per judgement): module id/version/declaration hash, stage, session/binding, frame id + trigger point/source event, time; input summary (material ids, kinds, bytes, region items, omitted count, compaction kept ids) with bodies in a separate private content file keyed by hash; decision (mode, confidence); selected evidence ids; job id/status/output summary; delivery status (delivered | withheld-by-stage | dropped) with the drop reason (`source_changed`, budget, material limit, …); judge/compaction call counts. Written through a host-provided trace sink port under `.lazy-harness/state/monitoring-private/<module-id>/` (git-ignored), bounded retention (age and size caps).
- Later steps keep the user-confirmed order: memory-module monitoring in observe/shadow → explicit feedback command (`/monitor-mark <trace> wrong|missed|ok`; no user-text classification) → shared evaluation tool (replay → judge → score → version compare, oracle check, budgets, holdout) replacing the four per-module runners → promotion. Settings change at use time (on/off, lower stage, trigger subset, report mode, cost caps, judge profile); question/trigger additions/inputs/job form change by a new module version measured before promotion.

Implementation language (user-confirmed option A, task154): keep the core in TypeScript inside the Pi package (Fabric-independent per ADR 0061) and keep its boundaries language-neutral — configuration schema, `monitoring-trace/v1`, canonical JSON hashing (Python twin exists). Reason: the bottleneck is Jev latency and judgement quality, not core CPU; Pi extension hooks run in-process TypeScript, so Rust would add IPC/native binding and per-platform distribution. Revisit only when a non-JS agent runtime needs the same core (ADR 0056) or S8 dogfooding measures hook overhead (per-event snapshot reads) as a problem; then port only that part.

## Stage 4 — safety invariants and latency budgets (DRAFT, not approved)
| Invariant | Acceptance (must hold in tests and every measured run) |
|---|---|
| Delivery integrity | wrong-scope, stale-source, restricted-body and gold-leak violations = 0 |
| Budget gate | a job that declares cost never starts without a user-approved budget; spend never exceeds the approved caps |
| Uncertain effect | unknown/unverified results end terminal, retries = 0 |
| Idempotency | same key never executes twice (incl. restart/replay) |
| Loop guard | a module never re-triggers on events produced by its own jobs; bounded depth for others |
| Redaction | secret-shaped values never reach Jev/Luna (synthetic secret corpus) |
| Canonical hashing | identical JSON produces identical hash in JS and Python (parity corpus incl. integer-like keys) |
| Judgement log | every judgement logged; retention bound enforced; no logging outside consented scope |
| Risk tiers | per-module accuracy targets by tier (read-only R≥95%/FP≤3%, proposal R≥95%/FP≤2%, automatic FP≤0.5%/R≥90%) on its own acceptance set |

Latency budgets (input event → hand-off): judge+select p95 ≤ 1s; template/Jev-matching jobs add ≤ 0.2s; inline worker job p95 ≤ 4s (target ≈3s); parent report follows the carry policy. Measured baselines: judge ≈0.4s/call, current worker ≈7.5s.

## Stage 5 — staged implementation plan (DRAFT, not approved)
| Slice | Content | Acceptance | Model calls |
|---|---|---|---|
| S0 | canonical JSON serialization (JS + Python) | parity tests incl. integer-like keys, unicode, nesting | 0 |
| S1 | contract v2: schema + `defineMonitoringModule` v2 (purpose, watch, needs, jobs, report, cost, idempotency), data config rules (disable/tighten/report only), v1 compatibility | schema/validation unit tests, v1 configs still load | 0 |
| S2 | items: per-message history, tool-call items, redaction hook in the material window | unit tests; existing suites green | 0 |
| S3 | judge: selection bridge reads v2, one batched Jev call per event across modules, judgement log store | unit tests; dev measurement of accuracy/latency | Jev ≈ 70 |
| S4 | module runtime/router: loop guard, idempotency registry, budget gate, uncertain-stop, template and Jev-matching jobs via C1 | CPU tests for every engine rule above | 0 |
| S5 | inline worker mode (one dispatch) | dev latency + input accuracy vs current mode | Luna ≈ 100 |
| S6 | report wiring: carry mailbox → context hook in an isolated SDK session; external notification adapter stub | wire test like D1 (actual final request) | main model ≈ 2–4 |
| S7 | first modules on the new contract: U1 references (port), U6 rule steering (new, with its own acceptance set); U2 knowledge absorption as a hand-off to the knowledge-digest runner later | per-module tier targets on fresh holdouts | new budget per module |
| S8 | opt-in live shadow on real sessions (observe + log only, no injection) | human review of the judgement log | needs consent beyond current P5 |

Order rationale: contract and hashing first (everything depends on them), then the core path (S2–S4) with zero model calls, then the two measured performance changes (S3, S5), then wiring and real modules, live last.

Execution progress, measured results and execution decisions: `.lazy-harness/planning/monitoring-core-live-integration-plan.md` § Monitoring engine v2 execution log (moved there to follow this document's rule).



### Remaining open items
- Stage 3: engine flow and mapping of existing parts (observer, material window/history, coordinator, selection bridge, C1 consumer, worker adapter, carry mailbox, judgement log, budget gate).
- The two-step report idea (fast alert first, worker analysis appended later) for modules like repeated-failure detection.
