# SDD — Monitoring Core v0 and module usage contract
> Pre-migration record: code/script/test/fixture paths below describe the layout of lazy-harness branch `work/monitoring-engine-v2` (221553d) before the monitoring implementation moved to `lazy-dinosaur/lazy-harness-monitoring`; evidence stays in lazy-harness (ADR 0062). Canonical monitoring records now live on lazy-harness main (see `.lazy-harness/ssot/monitoring-records-ownership.md`).

Status: experimental baseline retained; forward B stage0 mode criteria user-confirmed, not implemented in frozen pilot-v1
Layer: SDD

## Rule digest

- Status: advisory
- Layer: SDD
- Scope: host-project
- Confidence: medium
- Aliases:
  - 공통 모니터링 코어
  - 모듈 붙이는 법
  - monitoring core
  - processor registration
- Applies when:
  - explicitly using or extending the MonitoringCore v0 library and its reference modules
  - defining a future B knowledge/reference mode policy or evaluation revision after the user-confirmed stage0 criteria
- Must:
  - keep event transport and common execution separate from module-specific semantic questions
  - treat run/skip/defer as model judgement data, never a permission grant
  - validate context versions, declared evidence, host grants and proposal receipts
  - distinguish a recorded proposal from business-state application
  - measure functional examples, not only registration success; 100% model accuracy is not required
  - for future B revisions require input-visible approval evidence before knowledge run and defer admitted explicit requests with unresolved targets; never relabel/replay a frozen pilot by the new criterion
- Must not:
  - install live hooks, inject context, write a knowledge DB or remove the current record envelope implicitly
  - classify raw user text with keyword rules or execute generated text as code
  - claim hard cancellation of uncooperative adapters or cross-process exactly-once effects
- Record completion:
  - keep this contract, usage examples, tests and implementation graph aligned
- Related records:
  - `.lazy-harness/planning/jev-context-and-background-monitoring-research.md`
  - `.lazy-harness/ssot/cli-tool-boundary.md`
  - `.lazy-harness/tests/test-strategy.xml`

## Scope and approval

The user approved progressing toward a reusable core plus module contracts/examples with practical, not perfect, reliability. This v0 is an explicit library, not a decision to deploy inside Pi or as a daemon. Runtime placement and real event/injection adapters remain separate. Existing record-judgement stays enabled. No G16 source or business API is owned here.

## v0 contract

- `MonitoringCore`: registerProcessor, unregisterProcessor, setContext, start, stop, dispose, acceptEvent, getStatus.
- Context snapshots have host-issued scopeId/version, a goal and versioned references. Reusing a version with different data is invalid.
- Events have host-issued id/kind/scopeId/contextVersion/sequence and JSON payload. The source owns ordering; models do not invent identity.
- Processor declarations contain id, eventKinds, referenceKinds, allowedActions, optional run/skip/defer question and a trusted run handler. Registration supplies explicit host grants; declarations cannot widen them.
- JudgeBatchPort receives module-specific immutable views and questions. Missing/invalid judgement or evidence becomes defer, not skip or automatic execution. Evidence must refer to the actual event or visible references.
- Execution handlers receive the view, decision, AbortSignal and a checked readReference operation. They return proposals, not shell commands or final business facts.
- ProposalSink receives a core-issued request identity, currentness guard and signal. A recorded receipt requires matching requestId and a recordId. This is proposal acknowledgement, not final knowledge/task acceptance.

## Safety and limits

Limits bound events, judge batches, executions, concurrency, reference reads, proposals and stage time. Counters do not reset on stop/start. Duplicate events do not repeat judgement/effects; conflicting reuse of an id is rejected. New context versions, unregister and stop invalidate late results. One module failure does not convert another module's success into failure.

Adapters are trusted host code. They must honor AbortSignal; a JS library cannot forcibly terminate an ignored signal or roll back an already committed external operation. Logical timeouts return promptly, but an uncooperative operation retains its physical concurrency slot until it settles. Persistent idempotency, atomic conditional business commits, process supervision and network/dollar accounting belong to the corresponding host adapters. Core judge/execution counters are not a claim about provider HTTP request counts.

The host owns event-origin authenticity, payload redaction and permission to send data to a model. Core validates supplied identity/context/grants; it does not prove that caller-supplied text really came from a user or that external disclosure was authorized.

The v0 reference sink records proposals only in memory. No production DB, Pi session, prompt or injection is modified. No untrusted plugin-code sandbox is claimed.

## Module usage

1. Declare what events and reference kinds the module needs.
2. Write its semantic run/skip/defer question (or omit judgement for an explicitly unconditional observer).
3. Implement a handler returning evidence-linked proposals; validate its own payload semantics.
4. Register it with host-supplied action/reference grants.
5. Supply a context snapshot and event, then inspect outcomes/receipts rather than assuming success.
6. Test needed, unneeded, ambiguous and failed/stale cases. Model confidence alone is not a reliability measure.

Reference modules: knowledge.candidate quotes a confirmed user correction for review; context.references reads selected, version-checked sources and proposes them; audit.observation faithfully records event metadata. The third example is registered through the same public contract without core code changes. None is a production knowledge-storage or context-injection implementation.


## Forward B stage0 criteria — user-confirmed, implementation pending

The native stage0 questionnaire confirmed the following module semantics for a FUTURE B candidate/evaluation revision. This is not a retrofit to the frozen real pilot, a new model budget, an automatic worker/search trigger or permission to write canonical knowledge. Existing code/questions/corpus/gold and the9/12=75% result remain unchanged. In particular, original b04/b10 run expectations are retained as historical author labels; do not silently regrade them under this new contract.

### Knowledge candidate eligibility and evidence

- A potentially lasting project decision/rule/procedure may run only when original user approval or a trusted approved-record source is visible in the judgement input and attributable to the candidate. The host owns source authenticity and permissions; a model's confidence or text saying 'approved' does not establish that authority.
- An assistant/tool reporting 'the user approved this', without the original approval utterance or independent approved-record evidence in view, is defer until confirmation. Apply the same rule to all source roles/cases, not just b04; the analogous b10 tool report must also be reviewed in a future version.
- Purely transient status/one-off requests remain skip. Tentative/conflicting/partial potentially lasting decisions remain defer. A run is a checked candidate proposal, never final canonical knowledge acceptance.
- Required input meaning is traceable approval evidence and its association with the candidate/current source. No new field names, DTO, search algorithm or transport/schema implementation is selected by this criterion decision. Missing evidence does not authorize automatic retrieval or user questioning.

### Reference preparation eligibility and ambiguity

- An explicit request from any host-admitted user/assistant/tool source is an eligible request; no requester-role narrowing was selected.
- No present reference need/request -> skip. Present request with unknown/ambiguous product/document/version/target or unsupported required grounding -> defer. A clear current request with matching available permitted material -> run.
- This confirms the existing declared b06 defer interpretation; it does not retroactively change the pilot score or prove a model-internal cause. Defer does not itself grant search, worker/tool execution, transmission or effects. Technical malformed/missing judgement remains a distinct technical outcome, never a fabricated semantic defer.

### Stage0 Implementation map and placement

- Existing authorities: `.lazy-harness/scripts/monitoring-core.ts` validates module judgement/views/reads/receipts; `.lazy-harness/scripts/monitoring-core-realtime-selection.ts#RealtimeSelectionBridge` stages selected material with source/grant guards; `packages/lazy-harness-pi/monitoring/model-adapters.ts#monitoringJudgeRequest` constructs native questions.
- `.lazy-harness/scripts/monitoring-core-realtime-pilot.ts#pilotModules` and its frozen corpus/tests represent the OLD pilot-v1 criterion only, not enforcement of these forward choices. Implementing a revised contract/input schema/evaluator requires a separate plan/approval and source inspection; no new implemented_by graph claim is made now.
- Audit/result primary remains `.lazy-harness/tests/monitoring-core-reliability.md`; execution/sequence pointer remains `.lazy-harness/planning/monitoring-core-live-integration-plan.md`. Existing verified graph facts remain intact; generic derived-index ownership is unchanged.
- Rule placement: Scope=layer-fact; primary=this SDD, per `.lazy-harness/ssot/rule-sources.md` API/component contract routing. This clarifies module input/eligibility semantics, not the definition of lasting project knowledge, global agent operating policy, production source ownership, model/auth configuration or live UI. Do not duplicate it into policy registries, AGENTS or private memory.

## Implementation map

- Status: `verified` (source and strict API checked; experimental, not production acceptance).

- `.lazy-harness/scripts/monitoring-core.ts`: portable lifecycle, registry, immutable context, batching, bounded dispatch and receipt validation.
- Verified API: MonitoringCore.registerProcessor / unregisterProcessor / setContext / start / stop / dispose / acceptEvent / getStatus. Ports: JudgeBatchPort and ProposalSink; handlers and adapters remain trusted host code.
- `.lazy-harness/scripts/monitoring-core-examples.ts`: functional reference processors and an explicit memory proposal sink.
- Verified factories: createKnowledgeCandidate / createContextReferences / createAuditObserver / createMemorySink / createClassifierJudge / runCoreScenarios.
- `tests/lazy-harness/monitoring-core.test.ts`: contract and failure/uncertainty protection.
- `.lazy-harness/fixtures/monitoring-core/scenarios.json`: synthetic cases and pre-authored expected decisions.
- `.lazy-harness/scripts/monitoring-retrieval-poc.ts`: existing bounded SDK driver reused only for an explicitly selected core probe; existing retrieval behaviour remains protected.
- `.lazy-harness/tests/monitoring-core-reliability.md`: user-approved module acceptance and residual failures. The current reference questions distinguish actual committed/pending decisions from quoted text and require available source evidence before lookup. Frozen synthetic60×2 passed the selected thresholds; this is not a real Pi adapter or production accuracy claim. Shared createMeteredRequest/openMeteredClient checkpoints reservations/dispatch, forbids concurrent/additional/redirect requests, and preserves independent experiment ledgers.
- `packages/lazy-harness-pi/examples/monitoring-core/README.md`: how to attach a processor, explicit grants, actual adapter and lifecycle/receipt boundaries.
- `.lazy-harness/evidence/monitoring-core/model-probe-01.json`: actual typed-judge decisions and functional output evidence; not oracle replay.
- `.lazy-harness/knowledge/graph.jsonl`: append confirmed implementation edges after source inspection.
- Generated implementation index remains derived; the current SSOT has no implemented generator, so do not hand-author a truth cache.

## Layer completeness

| Layer | Independent delta |
|---|---|
| SDD | This primary owns the new component/adapter/module API contract. |
| BDD | No live UI, input handling or injection change. |
| SSOT | No production config/auth/ownership change; test bindings remain test-only. |
| DDD | No business rules; references and user statements are synthetic. |

TDD protection is mapped here rather than duplicating a second narrative. Practical semantic reliability is evaluated separately from deterministic core safety; numerical production acceptance thresholds remain unset.

## Evidence capsule — core v0

User-confirmed target: a reusable core plus module usage, with practical reliability rather than 100% perfection. Scope delivered: explicit portable library and reference processors; no live Pi hook, daemon, knowledge DB, real context injection or envelope removal.

- Local verification: initial focused suite 39 PASS / 0 FAIL / 770ms (19 core + 20 previous PoC protections); added capacity checks 3 PASS / 0 FAIL / 84ms. Total protected cases: 42 across checkpoints. Strict core/API/test typecheck passed after a type-only callback annotation; unchanged passing functional checks were not rerun for that annotation.
- Actual model probe: three independent synthetic episodes passed through the same MonitoringCore. The two questioned processors produced six decisions matching their pre-authored expectations: needed=run/run, unrelated=skip/skip, tentative=defer/skip. Criterion text is an adapter reason, not verified model reasoning.
- Functional results were checked separately: confirmed user text was quoted exactly as a candidate, the selected team-rule reference was actually read with matching id/version/content, unrelated/uncertain turns produced no domain proposal, and a third audit observer registered without core edits produced the expected event metadata. All three per-episode functional groups matched. No proposal was promoted to a business fact.
- New model HTTP requests: 3; cumulative original+core ledger: 20/20 (8 classifier + 12 chat), SDK estimate USD0.000983282 of the unchanged USD1 envelope. Incremental classifier cost estimate USD0.00015078. Billing invoices are not verified. No additional paid inference remains in this approved ledger.
- `.lazy-harness/evidence/monitoring-core/model-probe-01.json` preserves reports, expected/actual decisions, functional checks, actual proposed payloads, core counters and cumulative usage. Its core status is the snapshot before the runner calls dispose; the managed shell then exited. It is not a running service.
- Limits: three fixture-author-labelled episodes do not establish production accuracy or calibrated confidence. Oracle replay tests prove mechanics, not semantic reliability. Future held-out/real session tests, production module APIs and runtime placement need their own scope/criteria.
- Organization review: core owns lifecycle/registry/dispatch/receipt mechanics in one module; functional processors and typed-classifier conversion live in a separate example owner; SDK metering remains in the already bounded test driver. No line-count-driven extraction or untouched source rewrite.
- Final validation receipt: `.lazy-harness/evidence/monitoring-core/standard-after-ref-fix.json` (bounded standard report, fresh full regression passed). Incident closure/counts remain in the linked Planning; this is evidence-only closure, not a source/test/config mutation.


## Public SDK/configuration v1 — independent baseline

User-confirmed decision: ADR0061; public SDK + a single declarative schema/validator + generic conformance. Fabric is not a baseline dependency. Existing private package subpaths `@lazy-dinosaur/lazy-harness-pi/monitoring`, `/monitoring/pi`, `/monitoring/schema` expose portable contract/configuration/binding/conformance APIs. The package is not published or automatically installed by this work.

The SDK delegates to an explicit host `MonitoringCoreFactory`/`MonitoringObservationBridgeFactory`; it does not ship a second manually maintained engine. Source-only adapters in `packages/lazy-harness-pi/examples/monitoring-core/configured.ts` supply the same existing canonical constructors. Only the host adapter may depend on source-checkout paths. An isolated consumer with only SDK files, TypeBox and platform types imports/typechecks without Fabric, Pi SDK or a `.lazy-harness` subtree, then accepts an explicitly injected canonical host engine. This is portability of the SDK/composition boundary, not publication of a standalone engine binary.

`createConfiguredMonitoringCore` returns the same stopped engine after validated registration/context setup. `createConfiguredPiMonitoringModule` returns an idle/default-off component; handler installation still does not start collection. Host source/judge/delivery admission and the explicit start permit remain required. The Pi adapter forwards only user.input, assistant.message and tool.result; unsupported declared kinds reject before bridge creation. The existing Pi factory port requirements are retained (reports/getStatus/consume/dispose; no new required limits member).

Data contract/field ownership is `.lazy-harness/ssot/monitoring-configuration.md`; public usage is `packages/lazy-harness-pi/monitoring/README.md`. Native TypeBox is the single configuration authority. Root schema/defaults/static types/exported JSON derive from it; unknown fields, executable/nonplain data, wrong versions, unbound backends, unadmitted scopes and ungranted/excess limits reject. Module schemas retain native metadata for defaults. JSON data cannot self-grant permissions or encode callbacks/credentials; no config discovery, evaluation, fallback, hot reload or automatic start exists.

Public symbols verified in source: `defineMonitoringModule`, `parseMonitoringConfiguration`, `createConfiguredMonitoringCore`, `createConfiguredPiMonitoringModule`, `verifyMonitoringTrace`. The pure trace oracle requires independent expected payloads and actual source/view/read/receipt/observed-proposal-recording traces. A missing effect, unsupported capability or physically pending callback cannot count as a functional pass. Business-state acceptance, model accuracy, hostile-JS isolation and hard cancellation are not claimed.

### SDK Implementation map

- `packages/lazy-harness-pi/monitoring/index.ts`, `core.ts`, `pi.ts`: explicit public API/composition, host factories, no Fabric/source-root runtime dependency.
- `packages/lazy-harness-pi/monitoring/schema.ts`, `bindings.ts`, `diagnostics.ts`: authoritative native schema, immutable settings/grant snapshots, exact module versions, host ceilings, structural failure codes.
- `packages/lazy-harness-pi/scripts/generate-monitoring-contracts.ts`, `monitoring/contracts.generated.ts`, `monitoring/configuration.schema.json`: declared canonical AST/schema build and drift protection; generated artifacts are not authority.
- `packages/lazy-harness-pi/package.json`: public subpaths with existing resource/deep-import compatibility preserved; no dependency installation/Fabric requirement.
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring-module.ts`: existing assembly now consumes portable type-only contracts, keeping runtime behavior and original factory port shape.
- `packages/lazy-harness-pi/tests/fixtures/monitoring-consumers/modules.ts`: four public-import-only functions; harness owns the canonical host engine, scripted judges and independent observed-effect ledger.
- `packages/lazy-harness-pi/tests/monitoring-sdk-contracts.test.ts`, `monitoring-sdk-generic.test.ts`, `monitoring-sdk-schedules.test.ts`, `monitoring-sdk-pi.test.ts`, `monitoring-sdk-isolated.test.ts`: configuration, source/material integrity, arbitrary-function conformance,100 bounded schedules, actual SDK synthetic6 and isolated API proof. Current proof/limitations are primary in the existing TDD.
- Machine facts: `.lazy-harness/knowledge/graph.jsonl`, prefix `kg_monitoring_sdk_`. The recorded generic implementation-index generator is still pending; these new SDK cache entries are explicitly not regenerated/authoritative. Existing cache/legacy rows are not rewritten.


## Configurable model profiles v1 — explicit host adapters

Approved native choice: implementation plus free/deterministic/faux validation, not a new paid>=95% measurement. Model profiles use their own `modelConfigVersion:1`; the existing monitoring `contractVersion:1`, engine and old frozen questions/gold/ledger are unchanged. Public entry `@lazy-dinosaur/lazy-harness-pi/monitoring/models` (also re-exported from monitoring) exposes `createMonitoringModelRouter`, `MonitoringModelRouter`, schema/parser and normalized adapter contracts.

A profile explicitly selects a versioned admitted host backend/provider/model/role, supported native-TypeBox parameters, output/queue/time/call/token/cost reservation limits and optional native reference threshold. Host bindings own credentials/endpoints, exact parameter capabilities, pricing estimates, invocation and real HTTP/output accounting. No Fabric or automatic provider SDK install/discovery/fallback is added. Provider/model names in examples are symbolic, not a claim of qualified provider support.

`judgeBatch` groups already-scoped tasks by explicit per-processor route/default profile. Native typed classifier answers and structured JSON judgement answers normalize to the same core modes/evidence. Missing/invalid/technical results remain visibly missing with structural diagnostics; they are not fabricated semantically correct defer decisions. Unknown modes/processor IDs/references/actions and malformed scopes/refs reject. A shared backend receives only the union of its routed task views; neither prompts nor modules are hostile-code sandboxes.

`invokeWorker(profileId,{instructions,data,outputSchema},signal)` is an explicit trusted-module typed-data port; no automatic Luna runner/action execution is introduced. Every role must be host-admitted, and model results cannot grant source/action authority. `resolveProfile`, `getStatus`, `idle`, `dispose` expose admitted immutable identity, reservations/physical ownership, joining and lifetime invalidation. No hot reload or current Pi-agent model mutation. Profile/router fingerprints identify effective model/adapter/version/parameters/schema/limits/routes for provenance; they are not authentication or>=95% certificates.

Queue and input/output bounds apply before dispatch; host-estimated token/USD reservations are conservative lifetime ceilings with no refunds/reset. They bound driver calls, not proof of actual HTTP attempts/billing. Sum of profile physical concurrency caps is statically admitted against host.maxTotalConcurrent. Timeout/dispose invalidates results but retains the raw model promise/slot until actual settlement, preserving outer core physical ownership; never-settling groups can stall shared batch completion until the core's logical timeout. No hard kill/rollback guarantee.

### Model profile Implementation map

- `packages/lazy-harness-pi/monitoring/model-schema.ts`: schema/parser, `bindMonitoringModels`, native parameter/default validation, exact host identity/version/role/ceilings and fingerprints.
- `packages/lazy-harness-pi/monitoring/model-adapters.ts`: `validateMonitoringJudgeTasks`, `monitoringJudgeRequest`, `decodeMonitoringJudgements`, two model-protocol mappings and scoped evidence/output validation.
- `packages/lazy-harness-pi/monitoring/models.ts`: `MonitoringModelRouter`, `createMonitoringModelRouter`, default/module routing, typed worker invocation, conservative reservations, raw physical ownership/status/drain.
- `packages/lazy-harness-pi/monitoring/schema.ts`: existing bounded JSON parsing extracted as `parseMonitoringJsonData` without changing configuration v1 normalization.
- `packages/lazy-harness-pi/scripts/generate-monitoring-contracts.ts`: additionally derives `model-profiles.schema.json` from the single native model schema; original protocol/config artifacts unchanged.
- `packages/lazy-harness-pi/monitoring/models.md`, `example.model-profiles.json`: public data/host driver/SDK lifecycle/reservation/error/quality-boundary definition. `examples/monitoring-core/configured-models.ts` composes the same injected canonical core with explicit profile binding and no private engine import.
- `packages/lazy-harness-pi/tests/model-schema.test.ts`, `model-schema.contract.test.ts`, `model-adapters.test.ts`, `models.test.ts`, `schema.test.ts`, `models-sdk.test.ts`, and `examples/monitoring-core/configured-models.test.ts`: free model contract proof. Existing isolated public-consumer and generated-artifact tests also protect the new surface.
- Primary proof/limits: `.lazy-harness/tests/monitoring-core-reliability.md`, `.lazy-harness/evidence/monitoring-core/model-profiles-report.json`. Configuration ownership: existing monitoring configuration SSOT, explicit native gate B. Graph IDs prefix `kg_monitoring_models_`; generic generated implementation-index generation remains pending its recorded indexer, not hand-authored truth.

Discovery capture / Rule placement: this SDD is the primary for the new component API delta; the earlier Planning receives a pointer only. No global operating policy/capability or automatic hook is added. The existing graph legacy migration is not performed; only new verified component edges are appended.

## Current Pi judgement-input assembly — observed boundary

Clarification of existing implementation, not a new API or adopted selection pipeline. The overview phrase 'current context' must not be read as automatic reconstruction of the full conversation for each judgement.

1. `MonitoringObservationBridge.process` checks the observation cursor window and current settled snapshot. Eligible `message_end` sources are user.input/assistant.message/tool.result; the source message must still contribute unchanged to the canonical projection. The snapshot proves currentness/availability; the whole snapshot conversation is NOT automatically appended to the judge view.
2. The bridge sets core context to `{scopeId, version, goal: options.goal, references: this.references}`. `references` is the copied host-configured catalogue captured at bridge construction, not an automatically searched collection. Each message becomes a separate CoreEvent with payload `{text, message, source}`. Text is extracted from that message's text blocks; source is host-issued provenance.
3. Core matches processors by eventKinds. `MonitoringCore.view` includes the event and filters catalogue entries by BOTH processor.referenceKinds and granted referenceKinds. Matching reference entries retain their content. This is type/permission scoping, not semantic relevance scoring or passage extraction.
4. `monitoringJudgeRequest` for the native classifier serializes the already-scoped task views, including visible reference bodies, into `state.tasks`, and adds per-task run/skip/defer choice plus per-reference relevance bool questions. These reference decisions occur in the SAME judgement request; they do not shrink that request's input beforehand. Other injected judge ports may encode the supplied tasks differently.
5. Reference admission/observation limits reject or defer unsuitable input; there is no built-in instruction-aware source trimming to fit a model budget. No Luna preparation call is inserted here. A Jev-based pre-judgement selector remains a recorded candidate, not a semantic compaction pass in the current implementation.

Implementation map: `.lazy-harness/scripts/monitoring-core-observation.ts#MonitoringObservationBridge.process`, `.lazy-harness/scripts/monitoring-core.ts#MonitoringCore.view`, `packages/lazy-harness-pi/monitoring/model-adapters.ts#monitoringJudgeRequest`. Existing component graph links remain applicable; no new implementation or future-stage edge is asserted. Compaction reference study remains `.lazy-harness/planning/jev-context-and-background-monitoring-research.md`; role/input ownership remains `.lazy-harness/ssot/monitoring-configuration.md`.

## B stage2 model-input contract — draft for review

Status: **accepted for a separate controlled FREE prototype only; experimental field/layout contract, not a production SDK/schema adoption**. After reviewing this draft summary and its proposed free-fixture next step, the user said “좋아 다음 진행해봐”. Implement only source-local projection/eligibility helpers and bounded scripted fixtures, preserving the frozen Core/A/B/native codec/pilot path. No real model, auth, runtime registration or pilot score change is approved.

### 1. Purpose and recommended boundary

Close the audited gap between an admitted source body and a question that understands which source is current, which module purpose applies and which approval evidence is actually present. A body being visible is not semantic sufficiency. The24-view audit is `.lazy-harness/evidence/monitoring-core/realtime-B-pilot-v1/sequence-audit.json`; its missing explicit links/instructions are structural observations, not proven causes of every model error.

**Recommended draft:** retain the original grant-filtered Core view and each Reference's id/kind/version/content unchanged; attach bounded, per-module metadata in a MODEL-FACING projection alongside that view. Put the registered module contract into each task's state and explicitly bind both native choice and reference questions to that task. Keep the native output keys and existing Core decision/read/receipt authority. This avoids proposing an immediate rewrite of the common Core DTO/public generated contracts. Whether the existing adapter seams can safely provide all metadata must be proved in a separately approved prototype; this paragraph is not an implementation claim.

Flow: admitted source/material snapshot -> Core per-module grant-filtered view -> host-validated model projection -> native mode/ref questions -> existing judgement validation + checked reads -> module-specific proposal eligibility validation -> ready packet/internal receipt. Metadata must never be added through an unversioned hidden late patch.

### 2. Proposed per-task information (names are draft)

| Proposed field | Required meaning and producer | Consumer / constraint |
|---|---|---|
| `processorId`, `view` | existing registered ID and original immutable Core view | retain original source bodies/versions; do not replace them with model summaries |
| `moduleContract` | host registry's purpose/instructions, run/skip/defer criteria, required evidence roles and immutable contract revision | both choice and ref questions explicitly use the SAME task's contract; model cannot supply/change it |
| `current` | triggering host observation ID/event type and current logical reference IDs, from the material owner | current IDs must be a subset of this module's visible refs; event ID alone is not a reference association |
| `sourceMeta` | bounded map keyed only by visible reference ID: actual origin/actor, partial/final-hook/host-record stage, logical source revision and known observation associations | role comes from admitted source metadata, never text saying 'the user said'; host observation IDs are not native persisted entry IDs |
| `approvalEvidence` | input-visible potential original approval/approved-record reference IDs, provenance/association status, supplied by trusted host evidence owner | applies to knowledge eligibility; no private/ungranted IDs or record paths may leak through metadata |
| `projectionVersion` | host-issued binding of the actual per-task judgement input and its relevant dependencies | must participate in job/currentness/result acceptance, not be a decorative model label |

`moduleContract.requiredEvidenceRoles` remains module-owned, not a knowledge/reference special branch in Core. Proposed knowledge roles are current observation, applicable storage-policy context and approval evidence (the original current user statement may also be approval evidence). Proposed reference-preparation roles are current request and matching permitted task document(s). Exact role lists/payload schemas require review; no module input schema is silently adopted here.

### 3. Approval evidence is not a model-generated approved flag

Proposed statuses: `available`, `missing`, `unresolved`, `conflicting`. **Available means relevant source material is present with attributable origin; it does NOT mean the model or metadata automatically proves the decision was approved.** The model still interprets the original source under the module criteria. Unrelated user text is not approval of a candidate. An assistant quoting a user does not become the user. A tool may convey an approved record only when the host can tie the actual record/body/version to that source, not merely because the text claims an audit succeeded.

- Evidence owner supplies the actual original source/reference, its version and known candidate association. Structured approval workflow/canonical record provenance may substantiate that association. Model-inferred associations remain explicitly unverified; raw text is not statically keyword-classified by hooks.
- A path/record name without an admitted body is not input-visible proof. Missing required evidence is represented explicitly; it does not authorize retrieval, a broader grant, contacting a user or a worker run.
- If evidence is denied by module grants, omit its ID/path/title/body from the model projection. Use only a generic required-evidence-unavailable status; detailed permission diagnostics stay host-side.
- A valid semantic judgement may be defer because evidence is missing/unresolved. A malformed projection or missing native answer is a TECHNICAL failure, not a fabricated semantic defer.
- If the model nevertheless returns knowledge run without the required evidence linkage, a module-level eligibility validator may reject the proposal with a distinct reason. It must preserve the raw model decision/error and MUST NOT rewrite it as if the classifier returned defer. This is proposal validation, not a static raw-user-text classifier or a Core feature branch.
- A staged candidate/internal receipt remains separate from final canonical knowledge acceptance and business authorization.

### 4. Abbreviated proposed state example (not a runnable schema)

The classifier call remains the existing `{ state, questions }` shape. The following illustrates only the task projection; angle-bracket strings are placeholders, not actual runtime IDs.

```json
{
  "contractVersion": "monitoring-judge-input/v2-draft",
  "tasks": [{
    "processorId": "knowledge.candidate",
    "view": "<existing immutable per-module Core view, unchanged>",
    "moduleContract": {
      "revision": "<host registry revision>",
      "instructions": "<registered module purpose>",
      "criteria": {"run": "<rule>", "skip": "<rule>", "defer": "<rule>"},
      "requiredEvidenceRoles": ["current", "policy-context", "approval"]
    },
    "current": {
      "observationId": "<host observation ID>",
      "referenceIds": ["<visible current ref ID>"]
    },
    "sourceMeta": {
      "<visible current ref ID>": {
        "actor": "assistant",
        "stage": "final-hook",
        "observationIds": ["<actual known observation ID>"]
      }
    },
    "approvalEvidence": {"status": "missing", "referenceIds": []},
    "projectionVersion": "<host-computed relevant-input revision>"
  }]
}
```

No proposed field is currently exported/registered by the SDK. A production wire example/schema must be validated during an approved prototype rather than treating this abbreviated example as executable data.

### 5. Choice/ref question binding and output mapping

- For task index i, the choice question explicitly applies `state.tasks[i].moduleContract` to that task's current evidence. Its criteria come from the same registered immutable contract revision.
- Every `ref_i_j` question explicitly binds task i, visible ref j and that task's moduleContract/current/sourceMeta/approvalEvidence. Do not rely on instructions placed only in a neighbouring choice question being implicitly shared by the provider.
- Shared state contains the full relevant module contract once per task; a question's instruction points explicitly to it. Repeating all text per reference versus explicit shared-state binding is an encoding choice to review, not authority to split into two API calls.
- Reference necessity is not authority: an unverified report can be relevant to deciding defer. Do not hide such a source merely because it cannot establish approval. A run payload must contain the checked references required by its module input contract, including the actual approval evidence when knowledge run requires it.
- Keep native decision/ref question keys and decoding bound to the original visible reference IDs/order. No model-generated ID, approval flag, command, source-role upgrade or confidence value can widen permissions or manufacture evidence.

### 6. Scope, freshness and redaction

- Build metadata from an admitted, immutable job snapshot; then project it separately for EACH module AFTER existing grant filtering. Metadata key sets and all current/approval IDs must be subsets of that view's refs. Cross-module metadata must not leak denied evidence.
- Bind projection/module-contract/grant/approval-source revisions into the host context/job validity before dispatch. The Core context version or the existing realtime dependency/currentness seams must cover every decision-relevant input. If an adapter cannot bind this safely, it is a prototype blocker; never enrich only inside a late backend callback without a matching lease/version dependency.
- Approval/association, grants, source content, intent/session/branch or module criteria changes invalidate stale judgement/packets as appropriate. Ordinary context steps or a changing whole diagnostic hash do not blanket-cancel otherwise valid jobs.
- Identical hook/final copies may share a logical source/version. Preserve actual, bounded observation associations; do not require a fake one-to-one current-event/origin relation, invent native entry IDs, silently dedupe packets or mutate the original body/version to fit the model.
- Measure encoded projection bytes BEFORE token/cost reservation and dispatch; enforce the selected host/profile source/question/input/output caps. If metadata makes the payload too large, report technical-unavailable/limit rather than cropping required meaning or silently raising caps. No old call/dollar allowance is transferred.
- Do not attach whole history/system prompts, hidden provider data, unrelated records, thinking/images/details or all project policies. No new search algorithm, transcript authority, cross-epoch cache, automatic worker or live activation is proposed.

### 7. Controlled free-fixture acceptance ledger — prototype contract PASS, real-source/provider qualification pending

| Fixture/probe | Required observation |
|---|---|
| current + similar background refs | correct explicit current association; original bodies/IDs/versions preserved |
| original user approval is itself current source | evidence may reference that same visible ID; no fabricated second source |
| assistant/tool approval report without proof | explicit missing/unresolved evidence; scripted valid defer has no run packet |
| admitted actual approved-record body | traceable body/version/association visible; run references include required proof |
| denied approval record | no denied ID/path/title/body in ANY model metadata; no automatic grant expansion |
| explicit request with unclear target | semantic ambiguity remains visible; scripted defer is distinguishable from technical absence |
| two modules with different purposes/grants | task-local contract is visible to both question kinds; no cross-module leakage |
| relevant metadata changes but body does not | old projection/offer becomes stale; no budget reset |
| ordinary next context/identical final copy | still-valid captured source stays valid; no blanket diagnostic-hash invalidation |
| malformed/native-missing response or wrong evidence | existing validation rejects; no invented skip/defer or false receipt |
| wrong model run without approval/current proof | distinct module-level guarded rejection; raw mode retained as a failed useful outcome |
| packet missing vs packet exactness | report expected-packet availability AND conditional fidelity, not only successful packets |

Scripted fixture success would establish projection/guard/transport behavior only, NOT actual Jev semantic accuracy. Any instrumentation should measure actual boundaries (source/view freeze, native dispatch/settle, checked read, packet ready/offer). A single batched native call has one observed RPC duration; do not invent separate mode/ref CPU or wall times without provider evidence.

### 8. Review/implementation boundary and map

The user approved the next bounded FREE prototype after the draft summary: add `.lazy-harness/scripts/monitoring-core-input-projection.ts` and `tests/lazy-harness/monitoring-core-input-projection.test.ts` only, plus necessary SDD/TDD/verified graph evidence. Keep existing Core/A/B/codec/public generated contracts/pilot fixtures and ledgers frozen; no package/entrypoint/settings/auth/production metadata-source wiring. Use trusted synthetic evidence-owner ports, explicit evidence/catalog revision dependencies captured BEFORE dispatch through the existing RealtimeLease/currentness seam, and per-module projection after Core grant filtering. Preserve native choice/ref keys and decode through the existing authority. Scripted fixture transport only: real SDK/model/network/OAuth/business calls0. This is adoption of an experimental prototype representation, not stable production schema or real-model qualification; further adapter/provider wiring or real trials require separate review/budgets.

Verified FREE implementation map: `.lazy-harness/scripts/monitoring-core-input-projection.ts#buildInputProjection` builds immutable per-task `moduleContract` (actual Core question plus required roles), `current`, allowlisted visible `sourceMeta`, explicit `approvalEvidence`, `evidenceRoles` and content-bound `projectionVersion`; `InputProjectionError`/per-module rejections are technical, and returned `checkRunEvidence` is module-level eligibility, not a replacement for Core checked reads or semantic judgement. Native question keys and decoding reuse `packages/lazy-harness-pi/monitoring/model-adapters.ts`. `ProjectionBinding.capturedDependencies` MUST really be installed in existing A initial `dependencies` before dispatch; evidence/catalog tokens are required, all initial source dependencies remain host-side, and only the two opaque metadata/catalog bindings enter the model-facing projection fingerprint. `assertCurrent`/the module guard use the existing RealtimeLease. Core grants/view/version/read/receipt and existing B bridge/raw-work authorities are unchanged.

Experimental prototype fields/limits: approval `required` distinguishes other modules; approval origin is host-attested `kind/referenceVersion/originVerified/association`, never model-attested approval. `sourceMeta.roles`/`evidenceRoles` are visible host-declared role bindings; the fixture roles are current+policy-context+approval and current+task-document. Effective missing/unresolved/conflicting cannot supply a qualified approval role; a user approval may share current's ID. A source-local metadata-map encoding rejects reserved object keys technically rather than changing public Core reference IDs. Fixed ceilings are8tasks/32refs per task/64native questions/65536encoded bytes/64listed IDs/16observation associations, with tightening-only overrides and no silent truncation or extra RPC. Guarded rejection preserves the original run mode, not a fabricated defer.

Protection: `tests/lazy-harness/monitoring-core-input-projection.test.ts` now has26 distinct controlled cases, verified in an initial25-case run plus one new targeted independent-receiver oracle; outcomes/limits are in the existing Monitoring reliability TDD and `input-projection-checkpoint.json`. Main native probe has2/2 current/task contracts and2/2 choice+5/5ref question bindings; independent positive structural fixture supplies2/2 expected packets with2/2 conditional exactness over5 original refs. Scripted outputs do NOT establish semantic correctness. Both metadata dependency changes invalidate pending/ready work in the actual existing A seam, while normal context steps/equivalent-copy notifications leave unchanged pinned snapshots valid. The source is not a production assembler or a proof collector: authentic origin, revision discipline and real read evidence are trusted synthetic ports here; an arbitrary host can lie, and types/captured-dependency labels are not cryptographic registration proof. Actual observer/source metadata mapping, permission-owner integration, provider payload acceptance and noncooperative real raw-work lifetime need separately approved adapter qualification. No package/public schema/runtime hook is registered; actual SDK/model/HTTP/OAuth/live effects0, old pilot/gold/75% unchanged. Graph ids use `kg_monitoring_input_projection_*`; the existing derived implementation-index is explicitly stale for this addition (no regeneration tool discovered; standard §6.4 permits stale cache, never invented data). No production contract or new operating rule is implied.

### B stage2 step1 source-provider contract — controlled implementation only

`.lazy-harness/scripts/monitoring-core-source-projection.ts#captureWindowProjection` is the new source-local bridge from existing admitted Window output to the existing input-projection host; `MaterialSourceProjectionError` is a value-omitting technical failure. Inputs: a real Window instance, native-style frame header, admitted kind pool, immutable captured module question/required-role/reference bindings and two explicit caller-owned evidence/catalogue revisions. It reads Window.scope/snapshot, NOT filesystem/history/provider state or arbitrary frame payload. Output: ProjectionHost, full initial dependency list, binding(RealtimeLease), project(existing Core-filtered tasks,lease). No SDK/package registration or stable public ABI is added.

One owner each: Window retains admission/material/current association/body versions; Core retains grants and checked reads/receipts; source provider only maps a pinned admitted snapshot; existing projector retains native encoding/required-input guard; A retains invalidation/raw physical lifetime; existing router remains unmodified. Source header/event ID/kind/cursor and registered question must match the actual task; visible refs must match exact captured envelopes. Unknown origin is technical, never invented skip/defer or a changed actor.

Host-record in this experimental metadata means host-supplied reference container ONLY. Generic host docs, record kind/path labels or assistant/tool approval reports cannot set approved-record authority. Even a configured visible original-user-body candidate emits at most unresolved with originVerified=false and unresolved association. Genuine original-source authentication, record read evidence and candidate attribution need separately approved owners; no available/verified approval is fabricated here. The current user-confirmed all-admitted-user/assistant/tool R request policy is unchanged.

Freshness binding: all Window scope/source versions plus opaque host evidence/catalogue revision deps are returned before prepare (up to32+3). Caller must install them in actual A initial dependencies and provide live owner version resolution; the provider does not invent a watcher/currentness/approval registry. Pin known captured provenance instead of comparing latest diagnostic/provenance wholesale: actual equal-body hook/final copy may replace latest provenance without changing body version, while old pinned truth remains valid. Semantic metadata/catalogue changes need their explicit owner token; partial→final/source reset/gap/removal remain delegated to Window/A. The existing production selection factory's dependency/transport seam is NOT modified or qualified by this local provider.

Protection: new `tests/lazy-harness/monitoring-core-source-projection.test.ts`33controlled cases + strict PASS, with actual Window/Core/A code and synthetic Frames/scripted native results only. Exact outcomes/limits/terminal standard are in existing reliability TDD and linked source-projection evidence. Actual SDK/model/network/record lookup/effects0; old gold/75% unchanged; real provider acceptance, authenticity and semantic95% remain unqualified. Graph ids `kg_monitoring_source_projection_*`; generated index stays explicitly stale, using existing canonical/source fallback. Step2 pre-reservation/router/dependency seam and step3 SDK/real-model qualification require separate scope/approval; no backend.invoke late enrichment or private router access is introduced.

### B stage2 step2a public Router projection port — implemented opt-in, mock qualified

The existing public `monitoring/models` module now exports `PreparedJudgeGroup` (`tasks`, optional `request`) and `PrepareJudgeGroup` (trusted synchronous callback of immutable routed tasks and bound profile). `MonitoringModelRouter.judgeBatch(tasks,signal,prepare?)` adds an optional third argument; the original two-argument JudgeBatchPort remains assignable and uses the unchanged encoder/request bytes. Callback is a runtime host port, NOT JSON configuration, a Pi auth resolver, model worker, new route selection or a source/grant sandbox. Core DTO/generated contract/export map/model schema is unchanged.

Preparation follows existing profile grouping and precedes the existing perform path's final byte/estimate/reservation checks. Accepted tasks must be an original-order JSON-byte-exact subset of that group, retaining original question/view/ref envelopes. Nonempty accepted group needs a same-kind prepared request; empty group must omit request and produces no estimate/reservation/invoke. Missing/partial/invalid groups are technical absence with bounded diagnostics, not model skip/defer. Existing decoder uses accepted indices/identities so metadata failure of one module does not corrupt another's native answer map.

Native protected fields: state.tasks identities/views, question key set/type/criteria; instructions may be enriched but remain nonempty. Structured protected fields: exact tasks/outputSchema plus nonempty instructions. Extra metadata semantics remain the trusted host's explicit responsibility; no arbitrary secret/code/auth data becomes safe merely by passing JSON. Prepared result/request routing fields and unsafe getter/function/Promise data are rejected. Actual scopes/views cannot be rewritten or enlarged through the callback. Profile role/routing/limits, final input bytes, estimator/invoker request identity, reservations, output checks, cancellation/deadline and physical raw settlement remain in the existing router; no late backend.invoke enrichment or copied budget engine.

Source is `packages/lazy-harness-pi/monitoring/models.ts`; protected by new `packages/lazy-harness-pi/tests/model-projection-hook.test.ts` and affected existing router mocks (combined66PASS/225expect/441ms, strictPASS). Original98-line source is preserved in the linked baseline archive. Only this one previously frozen runtime source was explicitly approved to change for step2a; old experimental ledgers/questions/gold remain historical. Details/standard receipt are in existing reliability TDD and router-projection evidence. Public symbols verified by actual source and strict public-module imports; graph ids `kg_monitoring_router_projection_*`, generated cache explicitly stale.

Step2b actual SelectionBridge input capture/metadata-version resolution/required-read packet guard, actual SDK qualification and Luna Pi OAuth worker are NOT wired by this optional port. Host still uses OpenRouter for Jev only and Pi OAuth for Luna; generic router stays model/backend-independent. Actual external model/network/SDK/Luna calls0 in these tests; no claim of total session cost0 or actual semantic quality. No real-model budget or execution permission transfers from this interface addition.

## Stage3a draft-local evaluation API — CPU preparation, not production Stage0 enforcement

### Implementation map

`.lazy-harness/scripts/monitoring-core-input-v2-evaluation.ts` introduces draft-local `DraftInput`, `DraftCorpus`, `DraftObservation`, `PreparedDraftInput` plus `validateDraftInput`, `validateDraftCorpus`, `prepareDraftInput`, `scoreDraftRun`, `compareDraftModes`, `DraftEvaluationError`, `DRAFT_SCOPE` and `DRAFT_MODULES`. Existing Core/projector/source-provider/SDK/model config/public exports are unchanged. This is an isolated evaluation adapter, not live data-collection/authentication or automatic execution.

Only scope=synthetic-evaluation-only/status=draft/author-labelled-unreviewed is accepted. Corpus must contain24 distinct fictional cases with independent input and evaluator expected fields, per-module8run/8skip/8defer. Source-side body/version/case/actor/stage/authority and association declarations are consistency checked. Fixture-derived originVerified is explicitly NOT a real-host signature, consent judgement or an authenticated approved-record store. Production Forward B source-owner work above remains pending.

`prepareDraftInput(input,signal?)` accepts no gold/case wrapper; each permission-filtered snapshot is issued by the existing Core before the unchanged projector constructs native request metadata. Runtime identities depend only on visible current source, not case ordinal/gold/hidden-source hashes. No read, sink, search, SDK, transport, model, worker or real A lifecycle is implemented. Returned prepared scope and realHostAuthenticity=false prevent a production-readiness claim.

`scoreDraftRun(corpus,observations)` is offline arithmetic on caller-supplied raw decisions and checked-reference snapshots. Missing/error/timeout/malformed remain in all24/module denominators; wrong raw runs are not forgiven by a required-evidence guard. Mode/confusion/per-mode P/R/F1/useful packet and reference exactness/integrity metrics are separate. Checked snapshots are not proof that Core readReference actually occurred. Every score is marked semanticAccuracyMeasured=false and labelsIndependentlyAdjudicated=false; oracle correctness does not measure a model. `compareDraftModes` requires two valid modes before crediting agreement and keeps missing outcomes in denominator24.

Protection: `tests/lazy-harness/monitoring-core-input-v2-evaluation.test.ts`; draft `.lazy-harness/fixtures/monitoring-core/realtime-B-input-v2-draft.json`; primary proof `.lazy-harness/tests/monitoring-core-reliability.md`; review/evidence capsules under `.lazy-harness/evidence/monitoring-core/`. Graph kg_monitoring_input_v2_* maps verified helpers/corpus/protection. Derived index remains explicitly stale. Human review, freeze, real Jev budget/execution, actual source/approval authenticity and OAuth worker remain separate and unapproved by this preparation contract.

## Step3b controlled Jev qualifier — evaluation-only contract

### Implementation map

NEW `.lazy-harness/scripts/monitoring-core-input-v2-pilot.ts` and profile `.lazy-harness/fixtures/monitoring-core/realtime-B-input-v2-pilot-profile.json` bind the explicitly selected24HTTP/USD0.10 SDK-est/600s OpenRouter-Jev native experiment. Tests: `tests/lazy-harness/monitoring-core-input-v2-pilot.test.ts`. Primary proof remains `.lazy-harness/tests/monitoring-core-reliability.md`; real outcomes live in the NEW input-v2-jev24-v1 evidence directory, not this API narrative.

`runInputV2Case(input,invoke,signal?)` accepts input only, obtains existing Core-issued/projected views, calls the existing Router once and applies the decoded decisions to byte-identical actual Core views. Its read callbacks capture actual source snapshots; guarded handlers and in-memory sink stage only those read bodies. `rawDecisions` preserve the automatic eventRef; material scorer rows remove only that context eventRef, not modes/wrong semantic references. Returned trial distinguishes operational integrity, semantic match and recorded staged receipts; it does not authenticate a live source or claim a business effect.

`InputV2Budget` narrows the reused Budget's input envelope only; `createMeteredRequest` remains the sole cross-case paid accounting/transport authority. `exactInputV2Model` and `inputV2RouteFetch` restrict exact classifier/API/pricing and actual OpenRouter destination/model without auth export or fallback. Native output generation is not a chat maxTokens guarantee; native question/byte bounds apply.

`inputV2Identity`/`prepareInputV2Pilot`/`assertInputV2Identity` bind exact local files, all prepared requests/questions and installed SDK entry/package. `claimInputV2Start` is exclusive; `runApprovedInputV2Pilot` has no implicit resume/retry and journals pending before each request. Model-free checks and final standard precede freeze/real dispatch; after dispatch only evidence changes. Provisional user acceptance of author labels is not independent adjudication; original draft bytes/gold remain unchanged. No public SDK/Core/source/credential/settings change or real-worker/live source-authenticity claim is implied.

The experiment profile, not runtime source, owns endpointOrigin/endpointPathPrefix. `validateInputV2Profile` checks bounded HTTPS origin/path data alongside exact approved request/cost/model limits; the independently tested and frozen profile pins the intended destination. This follows C17 external-dependency separation without changing doctor/allowlists or hiding URL text. No production endpoint/config is altered.

## Step3d CPU host-evidence adapter — controlled implementation, not native authentication

User-approved scope is one NEW source-local helper and one NEW CPU test, plus existing maps/evidence; Core/Window/A/projector/source/router/public configuration/gold/auth/settings remain unchanged. `.lazy-harness/scripts/monitoring-core-input-trust.ts` exports `buildTrustedInputProjection`/`InputTrustError` and private experimental types `InputTrustAuthority`/`InputTrustCandidate`. Default import performs no collection, source callbacks, SDK/model/worker invocation or effect. This is not an adopted public SDK ABI or actual Pi/record authentication.

### Contract and authority

Callers supply Core-issued grant-filtered JudgeTasks, existing ProjectionHost/ProjectionBinding, expected namespace and an explicit trusted synchronous authority port. `readRevision` supplies its dependency; `admission` supplies namespace/scope/issuer plus separate admitted/disclosure/inference booleans; `attest` reads only already-admitted snapshots and returns proof rows for visible refs. Ports are trusted host CODE; arbitrary source JSON/actor/hash/originVerified flags are not proof. A hostile/misconfigured host callback can lie; this adapter is neither a plugin sandbox nor a cryptographic attestation/key registry. Real SDK/approved-record read provenance requires a later separately approved owner/binding.

The authority dependency must ALREADY be installed in initial captured dependencies; missing capture fails UNBOUND_AUTHORITY. Admission rejects before projection/source/proof/model work if collection, disclosure or inference is not admitted. Scope/namespace are explicit fences, not inferred from text. The composed existing lease keeps authority revision, scope/issuer and permissions live at assertCurrent/required-read guard boundaries. Hosts must bump relevant revisions on proof/grant changes and check currentness before dispatch/use/handoff. Returning a prepared request cannot constrain callers that bypass the adapter; it does not own HTTP accounting or enforce grants outside that path.

### Narrowing flow and required-input semantics

1. Reuse buildInputProjection with approval SUPPRESSED. Never access `host.approval`: its caller-supplied flags cannot create authority. All other visible source/contract/role data is captured through the existing validator and frozen snapshot. Invalid/malformed tasks remain technical, not invented defer.
2. For approval-requiring modules ONLY, obtain an explicit host attestation over a candidate link fence and Core-visible refs. The digest binds expected namespace, scope, processor, goal, module contract/criteria and exact current refs; it excludes unrelated event/context diagnostics so unchanged pinned truth survives copies. The digest is not authentication. Strict plain-data proof rows bind issuer/namespace/authority version, original-user or admitted-approved-record kind, exact ref ID/kind/version/content, origin status and candidate association. A wrong candidate link is conflicting, not re-attributed by a model.
3. Ignore out-of-view rows BEFORE accessing private proof fields/getters; none of their IDs/path/body/hash enters model state/version hashes. Proof list size is bounded by the visible reference count; malformed/duplicate/accessor/unknown fields fail technically. Present but unresolved origin/link and partial sources stay unresolved. Original-user versus host-record source compatibility remains the existing projector's authority.
4. Replay ONLY immutable safe source/contract/current/role snapshots and qualified approval metadata through the SAME projector. Preserve first-pass technical rejections and module independence. Existing native questions, task/input limits and runEligibility remain the one encoding/required-input implementation. Available is not an approval fact; LLM semantics and all-admitted user/assistant/tool R policy remain unchanged. Missing knowledge approval neither stops an otherwise admitted R request nor suppresses the reference module.
5. Preserve raw run and selected materials. Existing checked-read/required-evidence guards deny an ineligible knowledge proposal without relabelling it correct defer. Core/A retain physical-slot ownership, relevant-dependency invalidation, source read fences and review-only receipt behavior. No canonical write/Main injection or real business effect is enabled.

### Implementation map and qualification boundary

- NEW helper owns only the scoped host-evidence validation adapter; buildInputProjection/ProjectionHost in `.lazy-harness/scripts/monitoring-core-input-projection.ts` remain snapshot/encoding/required-input owners.
- Existing `captureWindowProjection` in `.lazy-harness/scripts/monitoring-core-source-projection.ts` still emits originVerified:false/unresolved; no false production upgrade was applied.
- NEW `tests/lazy-harness/monitoring-core-input-trust.test.ts` exercises synthetic owner/ports, actual MonitoringCore checked reads and actual RealtimeMonitoringCoordinator lifetime/independent receiver paths. Thirty distinct passing CPU cases across bounded checkpoints, not a fresh single30 run; final strict and default-import/export/no-network probe pass. Cases/initial failures/observations/terminal standard are owned by the existing reliability TDD and input-trust checkpoint/receipt.
- Canonical graph kg_monitoring_input_trust_* maps verified source/symbol/call/protection/evidence facts. Generated implementation index was not regenerated and is explicitly stale for these additions; use canonical MD/graph/exact source rather than inventing cache data.
- Cross-layer ownership: existing monitoring configuration SSOT owns admission/grants/config; existing reliability TDD owns CPU proof and its4-row judgement matrix. Real native-event/record owner mapping, data-disclosure grant, independent semantic accuracy and worker-Pi-OAuth integration are NOT qualified here.

## Step3e Pi original-input owner — controlled actual SDK profile, default off

Native option selection explicitly approved NEW `.lazy-harness/scripts/monitoring-core-pi-input-trust.ts` + NEW `tests/lazy-harness/monitoring-core-pi-input-trust.test.ts` and a fresh controlled SDK envelope4 AgentSession creation attempts/12 prompts/600s. Existing active extension loader/package/observer/Window/source/projector/Core/router/gold/auth/settings remain unchanged. No automatic package registration, live conversation collection, real model/worker call or canonical/business effect is enabled.

### Source and permission contract

Verified private exports: `createPiInputTrustBinding`, `PiInputTrustError`; structural `PiInputApi`/`PiInputContext` target actual1.4.0 input/session_start/session_shutdown semantics without upgrading development dependencies. Default off registers nothing and does not call the permissions/context ports. Enabled factory registers ONLY input and session lifecycle handlers and returns input continue; it does not transform/consume input or classify text. SDK callback capture, not serialized role/body/flag, is the source route.

The HOST must explicitly admit the namespace/scope/issuer, context root/session and **owned passive/non-transforming prefix**. Pi input handlers compose in registration order, before skill/template expansion. Source tag interactive/rpc alone is not proof, and generic user-role/model-visible messages may be transformed/converted content. An unqualified/unknown handler prefix produces NO original-source evidence. The owner does not automatically detect a lying host or an earlier transformer; it trusts admitted host code and qualified registration order. It is not a hostile-extension sandbox or human-identity certificate. The controlled SDK fixture's known earlier callbacks are passive observers; this is not activation in the current live loader.

Only admitted interactive/rpc text is copied; extension-source input is ignored before body access. Images/non-text/accessors/oversize inputs do not become approval evidence. No history/branch/system-prompt/credential APIs are read by this binding. It reads minimal cwd/sessionId from admitted native context, issues labelled source-local observation/reference IDs (NEVER native persisted entry IDs), retains one immutable text snapshot up to65536 UTF-8 bytes, and uses source-local body version/counters. This is not a transcript store.

Collection/disclosure/inference remain separate explicit host permissions with a relevant grant version. Source revision changes on admitted new input, grant change, session lifecycle, rebind, explicit invalidate or dispose; old/late generation callbacks cannot repopulate new state. Hosts must signal relevant outside policy/root/work-unit changes through grant version/invalidate; no new watcher/authority registry is invented. Ordinary context/model messages and other worktrees do not replace native truth. Disposal is idempotent, removes listeners and prevents reactivation of that owner instance.

### Narrow current-source association and existing adapter composition

The authority port implements the existing InputTrustAuthority readRevision/admission/attest contract. It attests only an exact visible ref matching the captured native input ID/kind/version/body. Association is attributed ONLY when that exact ref is the candidate's sole current reference; another candidate stays unresolved even when source origin is genuine. It does not authenticate anaphoric replies to older proposals or approved-record sources. Those require separately reviewed evidence owners. Available remains not approved: Jev/LLM meaning is not replaced by a static hook check.

The existing buildTrustedInputProjection/ProjectionHost/checked-read/Core guards remain the engine. Hosts include the owner's dependency in initial A capture and check currentness at prepare/dispatch/use. Generic host.approval flags remain suppressed. Missing approval does not change the all-admitted R policy or suppress the reference module; an invalid raw run remains invalid rather than being regraded as defer. In-memory review receipts are not canonical knowledge acceptance.

### Implementation map and actual qualification

- New source owns the SDK raw-input callback binding, one bounded current source, local identity/revision and explicit authority callbacks only; import probe exports function/class with external calls0/SDK creations0.
- New tests reuse existing `.lazy-harness/scripts/monitoring-core-input-trust.ts`, MonitoringCore and the unchanged `packages/lazy-harness-pi/tests/support/monitoring-sdk-fixture.ts`. The fixture uses isolated roots, actual installed1.4.0 services/runtime, official faux provider and in-memory credentials. Its independent observer reads ONLY its own synthetic context for reconciliation; that is distinct from this binding's no-history/no-system access contract. It never reads the current real conversation.
- Actual SDK tests verify interactive/rpc original text before a later transform, rejection of extension injection, grant revocation/session rebind and unqualified prior-transform behavior. The strengthened negative receiver oracle carries the actual transformed SDK user body through Core checked reads to the reference receiver while denying knowledge approval. No production role=user authenticity, real human intent, independent semantic accuracy or OAuth-worker route is claimed.
- Existing reliability TDD plus `pi-input-checkpoint.json`, `pi-input-sdk-ledger.json`, controlled SDK reports and `pi-input-standard.json` own counts/terminal evidence. The cumulative SDK cap is exhausted at4 creations/7 prompts, active1228.146428ms; no further SDK attempt/resume/reset is authorized. External HTTP/Jev/Luna/worker calls0; old semantic24/24 untouched.
- Canonical graph kg_monitoring_pi_input_trust_* maps verified file/symbol/protection/evidence facts. Generated implementation index is explicitly stale for additions; canonical/source fallback applies. No public SDK/config/schema or runtime activation entry was added.

## Step3f explicit question/review link — CPU-only, presentation owner unqualified

User selected option1: additive readonly lookup in existing interview-loop plus NEW `.lazy-harness/scripts/monitoring-core-review-link.ts` and NEW `tests/lazy-harness/monitoring-core-review-link.test.ts`, with existing records/maps/evidence. No SDK/model/worker call, real queue/decision-log write, current conversation collection, UI interaction, public SDK/schema/config or active loader change is enabled.

### Existing identity owner and readonly API

`.lazy-harness/scripts/interview-loop.ts` now exports `readInterviewQuestion(queue, questionId)`. It explicitly delegates to the SAME private readQuestions/parseQuestion owner, returns a fresh matching parsed snapshot, missingundefined, and rejects duplicate matching IDs. It never writes/closes a queue, appends a decision or grants a read/presentation authority. Existing collect/answer/CLI/fingerprint/ID/effect semantics are unchanged. Current collect remains a writer and is not a readonly API. ADR0035 still owns same-turn answer --apply closure for actual queued answers; this helper does not replace it.

### Private review contract and authority boundaries

New exports `captureReviewQuestion`, `createReviewLinkBinding`, `ReviewLinkError`; experimental `ReviewLinkReceipt`/`ReviewLinkHost`. Caller explicitly admits a queue/question, native-input authority, candidate ref, namespace/scope/issuer/evidence dependency and trusted Host review port. The port supplies actual relevant revision, question-read permission and a purported presentation/reply link receipt. Synthetic ports qualify validation plumbing only: neither a linked flag, Q-id, answered state, digest nor tool success establishes actual UI delivery or human approval. The real review/presentation owner still needs separate qualification; hostile/misconfigured Host code can lie.

Q-id is queue identity, not full reviewed semantic version (legacy fingerprint does not guarantee all options/effects). `captureReviewQuestion` separates PRIVATE Host version over normalized question/options/effects/crossRef/candidate context from the granted displayed question reference (text/recommended/option IDs/labels/descriptions only). Public ref/version never incorporates hidden effects/context or their hashes. Operational answeredAt/decisionId and open→answered bookkeeping are excluded from reviewed meaning; superseded/deferred or changed relevant content revokes. Read scope is exact explicit queue/id, not filesystem discovery. No second XML parser/approval registry/watcher is added.

A link requires a matching trusted receipt/question version/candidate exact ref/native reply exact ref/namespace/scope/contract revision in linked state. Actual source origin is delegated to the existing native-input owner; it is not fabricated by receipt data. Another candidate, missing/ambiguous/cancelled/pending link, wrong scope/session/revision or unqualified native origin remains unresolved/missing. Jev/LLM still interprets the reply; no hook parses “1/좋아” as approval. Available is not approved.

`createReviewLinkBinding.authority` composes native/review/question currentness into a Host-only dependency and a bounded observed-change sequence (no revival on observed ABA); callers install it in initial captured dependencies/lease. Relevant underlying owners must retain honest version discipline; there is no automatic filesystem watcher or guarantee about unobserved transient changes. Normal closure or unrelated questions/worktrees do not invalidate unchanged pinned review truth.

### Projection/read privacy and lifecycle

`project` delegates to existing buildTrustedInputProjection, not another judge engine. It refuses installation of private review revision as a public evidence/contract revision, never reads/spreads base.approval, and rejects cached now-ungranted question material before forwarding that module; otherwise missing question material remains uncertainty without suppressing another valid module. Approval-requiring modules must explicitly declare review-context and bind it only to the exact visible question. Grant-denied/private question IDs/bodies/effects/hashes are not inserted by role metadata. Existing required-evidence/checked-read guards require the selected question actually be read; forced raw run remains raw and can be denied, never relabelled correct defer.

All-admitted R policy and Core/Window/A/raw physical lifetime/router/native source ownership remain unchanged. Prepared request admission cannot protect bypassing callers or a dishonest Host. Only review proposals are produced; question effects/canonical/business writes/Main injection are never executed by the link adapter.

### Implementation map and qualification

- Existing interview-loop readonly API → parser-owned question source only. New `captureReviewQuestion` directly calls it and builds private/public snapshots; no change to other writer exports.
- New `createReviewLinkBinding` owns only explicit-link validation/currentness/public review projection; existing `.lazy-harness/scripts/monitoring-core-input-trust.ts`/input-projection/Core and native-input binding remain their original authorities.
- New test exercises only temp fixture queues/decision logs, synthetic Host review/native callbacks and actual MonitoringCore checked reads/independent receivers.34 distinct CPU cases pass across bounded checkpoints; not one fresh34 run. Final strict/no-operation import/export probes pass. No new SDK/real UI presentation/semantic model acceptance is qualified, and exhausted old SDK caps are untouched.
- Existing reliability TDD and review-link checkpoint/standard capsules own full proof/limits/layer matrix. Canonical graph kg_monitoring_review_link_* records verified existing/new symbols, direct readonly-parser call and protections. Derived implementation index remains explicitly stale for additions; MD/graph/exact source fallback applies.

## Trigger points and independent module pipelines (task154, user-confirmed, model calls 0)

Contract: a module declares WHEN it checks by naming trigger points in `watch.events` (`MONITORING_TRIGGER_POINTS`: Pi hook + deterministic payload condition; raw hook names remain valid; `model.before-call` is delivery-only; unknown names fail with `MODULE_DECLARATION`). Configuration data may only select a declared subset (`modules[].watch.events`; widening fails with `WATCH_WIDENED`, missing declaration with `WATCH_OVERRIDE_WITHOUT_DECLARATION`). The engine resolves the names into hook events plus a per-module `trigger` predicate (`watchModuleFromDeclaration(..., { events })`). Independence (user-confirmed requirement): each module triggers and decides on its own — `createIndependentSelectionPipelines` builds one pipeline per module (own material window/budget, coordinator admission, selection bridge and judge request) over the shared observer, so one module's size, failure or timing cannot change another's input or outcome; a batched multi-module bridge refuses conditional modules (batching stays an optional transport optimisation for unconditional modules). The observer payload now also carries `messageType`, `command`, `outcome` for these conditions. Not yet done: the per-module between-region input (everything since the module's last judged point, tool calls summarised, origin-tagged), live wiring (S8), and the evaluator switch to independent pipelines.

**Between-region input (task154, user-confirmed rules, memo option A).** Material window `historyMode: 'since-last'`: on every watched frame the window renders everything since THIS module's last judged point (`regionLines`: user/assistant text verbatim and clipped, tool calls as `name → target`, tool results as `ok`/`error: …`, harness `<system-reminder>` blocks removed and marked, extension messages tagged `[extension:<type>]`, summaries tagged by role). Newest items are kept within the window budget and an `[omitted N earlier items of this region]` marker is added; the first judgement starts at the session head. Memo (A): up to 4 short originals the judge selected in earlier run decisions (`[memo]`) plus deterministic state (`[state] files touched: …` from tool-call paths), placed first. The selection bridge calls `window.markJudged(frameId, selected)` after a completed judgement of any decision; a failed judgement does not, so that span is seen again. `session_compact`/`session_tree` restart the region from the projection head (compaction summary first). Region items are context only unless the frame has no own item (for example `turn_end`), where the region is the judged current material. The judge's own per-item selection is the compaction step (selected originals become the memo); a separate Jev pre-pass that compacts an over-budget region before judgement is NOT implemented yet — over budget falls back to newest-first with the omitted marker. Not wired yet into declarations (`watch.history`) or the evaluators. Protected by `tests/lazy-harness/monitoring-core-region.test.ts` (6 cases).

Region size and judgement count on real sessions (task154 free check, `monitoring-region-stats.ts`, model calls 0; 57 sessions, 4025 user turns, 100014 messages, 260 compactions; regions rendered by `regionLines`): **input** schedule (once per user turn) region p50 2.3 KB / p90 8.9 KB / p99 33 KB, over 8 KB 11.0%, over 12 KB 6.1%, over 16 KB 3.8%, over 32 items (the default `maxSources`) 13.5% — the only schedule where an over-budget pre-pass (Jev compaction) matters, and the item cap binds more often than bytes; **turn_end** 11.7 judgements per user turn, region p99 2.1 KB, never over 8 KB; **tool_call** 12.1 per user turn, p99 3.3 KB, over 8 KB 0.11%. Cost reading (Jev ≈ USD 0.0003–0.0004 per call measured): a turn-end or tool-call module costs ≈ 12× an input module per user turn.

Fix (task154, found by the real-prefix oracle check: 6/31 run turns lost although the judge answered `run`, coordinator reason `source_changed`): in `since-last` mode the finalized user `message_end` re-added the same intent's user words (often longer: skill expansion, harness reminders) while the input judgement was still in flight; the late item could exceed the budget (`material_limit` → window gap) and changed the window version, so the ready offer was discarded silently. The window now admits the user words once per intent (input hook) and skips the finalized user message in that mode; protected by `tests/lazy-harness/monitoring-core-region.test.ts` (“finalized user message does not … invalidate an in-flight judgement”). Worktree cleanup in the same batch: the untracked test helper `packages/lazy-harness-pi/tests/support/model-fixture.ts` (needed by committed monitoring tests) is added; the public contract artifacts were regenerated for `modules[].watch` and `observationLimits.tailMessages`; the S7 policy-adapter test now names a committed policy. All 44 monitoring test files: 743 pass before these two fixes, then the affected 5 files 26/26.

Purpose-scoped region compaction (task154, user-confirmed option A): `RealtimeWatchModule.compactRegion` (declaration need adapter `region.compact`, set by `watchModuleFromDeclaration`; U1 declares it). In a single-module pipeline the selection bridge first sends one compaction task (question: the module's purpose; per-item reference question “needed to judge this module purpose on the current event?”, event id `<frame>:compact`) over the region items (head lines [memo]/[state]/[omitted] excluded and always kept), keeps only the selected items verbatim for the judgement view, and adds them to the memo via `markJudged`. A failed compaction keeps the window's newest-first region. Protected by `tests/lazy-harness/monitoring-core-region.test.ts` (“Jev keeps only the region items the module purpose needs before the judgement”).

Use-time tuning loop, step 1 (task154, user-confirmed; Fabric-independent per ADR 0061 — plain host ports, no Fabric runtime): **run stages** — declaration `maxStage` (`observe|shadow|active`, default active), configuration `modules[].stage` (`off|observe|shadow|active`) may only lower it (`STAGE_RAISED`), `prepareMonitoringBindings` returns the effective `stage`; `MonitoringModuleRuntime` with `RegisteredModule.stage`: off/observe never run jobs (`stage:<stage>`), shadow runs only read-only jobs and withholds reports (`stage:shadow-report-withheld`, text kept as `withheldReport`) and skips effectful jobs (`stage:shadow-effects-withheld`). **Judgement trace** `monitoring-trace/v1` through host sink ports: selection bridge `options.trace` emits `judgement` rows (frame, source event, module ids, material ids/kinds/bytes, region items, omitted flag, compaction counts, outcomes with modes, evidence ids, bodies) and terminal `selection` rows; the coordinator `onTrace` emits `delivery` rows (ready, offered, source_changed, no_result, …); the runtime `trace` emits one `job` row per outcome with the stage. `createFileTraceSink(dir)` (`.lazy-harness/scripts/monitoring-trace.ts`) stores rows per module per day under `.lazy-harness/state/monitoring-private/<module-id>/` (now git-ignored), bodies in a hash-keyed content store, size cap per module-day and `pruneTraces` age cap (default 14 days). Protected by `tests/lazy-harness/monitoring-trace-stage.test.ts` (5 cases); all monitoring tests 751 pass / 0 fail.

TypeScript core cost (task154 micro-measure, model calls 0, synthetic conversation): observer `record` per event incl. snapshot read 0.26 ms at 32 messages / 0.41 ms at 128; region rendering 0.007–0.018 ms — negligible next to a Jev call (~400–500 ms). Watch item for S8: handlers are awaited on every hook, so `message_update` streaming deltas (possibly thousands per response) could add up (e.g. 2,000 × 0.4 ms ≈ 0.8 s); candidate fix is to skip snapshot reads for event kinds no module watches. This is structural, not language-bound.

Implementation map: `packages/lazy-harness-pi/monitoring/trigger-points.ts` (`MONITORING_TRIGGER_POINTS`, `MONITORING_DELIVERY_POINTS`, `resolveMonitoringWatch`); `packages/lazy-harness-pi/monitoring/declaration.ts` (point validation, `effectiveMonitoringWatch`); `schema.ts` (`modules[].watch`); `bindings.ts` (effective `watch`); `diagnostics.ts` (new codes); `.lazy-harness/scripts/monitoring-engine-runtime.ts#watchModuleFromDeclaration`; `.lazy-harness/scripts/monitoring-core-realtime-selection.ts` (`RealtimeWatchModule.trigger`, batched refusal, `createIndependentSelectionPipelines`); `packages/lazy-harness-pi/extensions/lazy-harness/monitoring-observer.ts#payload`. Protected by `tests/lazy-harness/monitoring-trigger-points.test.ts` (8 cases: point→observed hook, deterministic conditions, declaration validation, configuration narrowing, engine resolution, batched refusal, per-module triggering with separate judge requests, failure isolation).

## U1 references module — gap-filler purpose (task154, user-confirmed)

Binding 2.1.1 (pre-registered dev revision): the instructions ask the judge to select every visible record the answer relies on, and `skip` names general tool/model knowledge and plain commands that need no project facts.

**Operating role — assistive reminder (user-chosen after the real-session results, task154).** U1 is a non-blocking, read-only aid; the parent's own record-reading rules stay the primary path and cover what U1 misses. It is judged by an assistive tier instead of the read-only tier (recall ≥ 95% / false trigger ≤ 3% / references ≥ 97%), which U1 cannot meet on real turns with the Jev judge: per round, job-level false trigger (a reminder is sent on a turn whose gold needs no unread record) ≤ 5%; useful-reminder rate (a sent reminder contains ≥ 1 needed unread record) ≥ 80%; integrity 0; recall and reference precision are reported, not gated. Provisional: these numbers were set after the task154 holdout was seen (holdout 4.9% false trigger, 83.3% useful reminders, 71.4% recall, record precision 71–74%), so they count only as a hypothesis until a fresh real-session window (S8 shadow or a new holdout) confirms them; the gates in `monitoring-e2e-evaluate.ts` stay unchanged for other modules.

After the real-session measurement (synthetic 100% recall vs real ~57%, definition gap on short follow-ups), U1 (`context.references`, binding 2.1.0) is a gap filler: it hands the parent project records the current turn needs and the parent does not already have. Split: the judge gets the broad question `referencesQuestion` (does handling the current turn well need project records now, short follow-ups included; each text ≤ 200 chars); the `deliver` job (template, read-only) takes a host port `AlreadyRead` (declaration `needs` adapter `session.read-records`: record ids the parent already read in this session from observed tool calls, reset on compaction), drops those, and reminds only when something remains (`output.deliveredIds`, `output.droppedAlreadyRead`; nothing left = rejected). Without the port the job is the plain template. The earlier narrow question is kept as `referencesQuestionNarrow` for comparison with the synthetic measurements. Implementation map: `.lazy-harness/scripts/monitoring-module-references.ts` (`referencesQuestion`, `createReferencesHandlers`, `AlreadyRead`), test `tests/lazy-harness/monitoring-u6-question.test.ts` (U1 gap-filler cases); evidence `.lazy-harness/tests/monitoring-core-e2e-acceptance.md` (real-session check), `.lazy-harness/planning/monitoring-core-live-integration-plan.md` (filter impact).

## Engine v2 opt-in judgement and long-session contract (task149–150)

Status: implemented, all **opt-in with unchanged defaults** (user-confirmed: keep them opt-in now; choose defaults together with rolling budgets at live wiring). Evidence: `.lazy-harness/tests/monitoring-engine-v2-contract.md` (U6 measurement, real-session replay).

Judgement contract additions:
- `JudgeQuestion.reference?` — a module-owned per-item question (`instructions` with `{id}`, `criteria.true/false`); the native-classifier adapter uses it instead of the generic "needed evidence?" question. Core validates every question text ≤ 200 chars.
- `JudgeQuestion.selectReferences?: false` — ask no per-item selection questions; decoded evidence is the event only (verification stages).
- Follow-up verification lives in the MODULE JOB, not the engine (Stage 2 decisions ②/③; plan conformance fix, user-approved): the engine judges at most once per module per trigger. A module that needs the exact judge view declares `needs` adapter `judge.view` → bridge `RealtimeWatchModule.includeJudgeView` → the selection packet carries `view`, and the runtime `Trigger.view`. U6 `remind` (form `jev-select`, declared cost `judgeCalls` ≤ 8 per run, so the runtime requires an approved budget) re-judges each selected rule alone via an injected `RuleVerifier` (`ruleVerificationTask`: current event + context + that one rule, `selectReferences: false`) in parallel and reminds only rules confirmed `run`; a failed or non-run verification drops the rule (fail closed); none confirmed = rejected. Request bodies are identical to the earlier engine-level build after normalizing per-run ids. Serial transports must queue calls (runner `serialized`).
- Selection option `currentInPayload` — the judged event payload lists the frame's own item ids (`currentReferenceIds`, metadata only).
- Selection option `frameBoundedMaterial` — `RealtimeMaterialWindow.snapshot(frameId, kinds, { boundToFrame, dedupe, tailItems })`: only material up to the judged frame cursor (host references stay), repeated identical items dropped (the frame's own kept); `frameTailItems` keeps only the newest N other observation items in the judge view.

Long-session contract additions:
- `PiMonitoringObserver` limit `tailMessages` (0 = off): the snapshot keeps the newest N messages within `maxSnapshotBytes` (system prompt dropped first, then N halved), stays `available`, records `truncatedHead`. Without it, a session beyond `maxMessages`/`maxSnapshotBytes` yields unavailable snapshots and the coordinator drops every frame.
- `RealtimeMaterialWindow` option `clipOversize`: an oversize item is clipped with a marker instead of failing the window into a per-turn gap.
- Known blockers before live wiring (not fixed): lifetime counters (coordinator `maxEvents`/`maxJobs`, selection `maxRequests`, material `maxEvents`) stop or skip long sessions and need rolling budgets; the coordinator validates frames with the shared `parseMonitoringJsonData` bound (16384 nodes), so full snapshots must stay bounded; a live `module` channel consumer must drain offers promptly or long turns overflow the mailbox.

Implementation map: `.lazy-harness/scripts/monitoring-core.ts` (`JudgeQuestion`), `packages/lazy-harness-pi/monitoring/model-adapters.ts` (`monitoringJudgeRequest`, `decodeMonitoringJudgements`), `.lazy-harness/scripts/monitoring-module-rule-steering.ts` (`createRuleSteeringHandlers`, `ruleVerificationTask`, `RuleVerifier`), `.lazy-harness/scripts/monitoring-engine-runtime.ts` (`watchModuleFromDeclaration`), `.lazy-harness/scripts/monitoring-core-realtime-selection.ts` (`RealtimeWatchModule.includeJudgeView`, packet `view`, `currentInPayload`, `frameBoundedMaterial`, `frameTailItems`), `.lazy-harness/scripts/monitoring-core-realtime-material.ts` (`snapshot` options, `clipOversize`), `packages/lazy-harness-pi/extensions/lazy-harness/monitoring-observer.ts` (`tailMessages`); tests `tests/lazy-harness/monitoring-u6-question.test.ts`, `tests/lazy-harness/monitoring-core-realtime-frame-bound.test.ts`, `tests/lazy-harness/monitoring-core-observation.test.ts` (tail case); runners `.lazy-harness/scripts/monitoring-u6-evaluate.ts` (`LONG_SESSION_TAIL_LIMITS`; `LONG_SESSION_LIMITS` kept only to compare the rejected raise-the-bounds approach), `.lazy-harness/scripts/monitoring-session-replay.ts`, `.lazy-harness/scripts/monitoring-session-label.ts`.

## Rule placement

- Rule: The current Pi-to-core judge-input boundary consists of per-message events plus a host-configured reference catalogue scoped by module/reference grants; observing a full snapshot does not mean forwarding or semantically compacting that whole conversation.
- Scope: layer-fact
- Primary record: `.lazy-harness/spec/platform/monitoring-core.md`
- Why not AGENTS.md: this describes one component's observed data-flow/API boundary, not universal agent behavior or a new workflow policy.
- Why not local notes: module/adapter authors need the shared component contract; this is not private Pi/OMP wiring or a local preference.
- Confirmation: inferred-from-record

Discovery capture: this existing SDD is the single primary for the observed input-assembly clarification. Code and current governing records were read; no new role choice, API, compaction adoption, model call or execution approval is introduced.
