# ADR 0037 — Workflow Compression, Not Safety Reduction

Status: accepted
Date: 2026-05-19

## Context

Lazy-harness has grown strong safety rules: record-first search, default-unknown epistemics, layer completeness, option gates, queued question closure, implementation maps, response lifecycle audits, and commit-time validation.

These rules reduce agent mistakes, but they also create many judgement points. An agent can hesitate over:

- whether the request is trivial or host-detail-dependent,
- which DDD/SDD/BDD/TDD/ADR/SSOT layers are affected,
- whether to ask an option gate or proceed,
- whether a discovery needs candidate or canonical capture,
- which implementation-map depth is required,
- which validation belongs now vs commit-time.

User feedback on 2026-05-19 confirmed the desired direction: make the harness less confusing and more effective without weakening its safety model. Opus and Oracle cross-validation converged on the same constraint: introduce workflow compression only as a read-only advisory front door over existing rules, not as a new canonical layer or safety bypass.

## Decision

Adopt **workflow compression** as a framework pattern.

Workflow compression means the framework may summarize existing lazy-harness obligations into a typed route recommendation. It does **not** reduce the underlying obligations.

The first implementation is a read-only `lazy route` command that classifies a request into finite axes and recommends record search, capture, gate, implementation-map, and validation actions.

## Invariants

The router and any future workflow profile must preserve these invariants:

1. Record-first search remains mandatory for host-dependent work.
2. Default-unknown remains the epistemic baseline.
3. Ambiguous decisions still require a structured force gate.
4. Queued answers must be closed with `interview-loop --mode answer ... --apply`.
5. `response.completed` remains a completion audit path.
6. DDD/SDD/BDD/TDD/ADR/SSOT remain the canonical layer model.
7. No new canonical workflow layer is introduced.
8. Candidate, draft, generated, and runtime data are not canonical truth.
9. Router output is advisory and read-only first.
10. Router may not write records, mutate queues, or auto-select Recommended options.
11. Commit-time `.lazy-harness/bin/lazy test` remains blocking.

## Telemetry amendment — 2026-05-19

Default `lazy route` remains read-only. For real dogfooding work, agents may call `lazy route --log`, and the Jcode `response.completed` lifecycle hook automatically records one append-only route telemetry sample per `message_id` when `last_user_message` is present. This makes telemetry collection usable without relying on agents to remember manual logging.

Telemetry is not canonical truth and does not close gates. It records only route axes plus stable message/message-id hashes, not the raw user message. It is append-only under `.lazy-harness/logs/route-decisions.jsonl`, ignored by git, and summarized by `lazy route-summary`.

This amendment preserves the read-only invariant by distinguishing:

- **route decision**: no write, advisory classification only;
- **route telemetry**: explicit `--log`, append-only metrics for later analysis;
- **automatic telemetry**: `response.completed` best-effort append keyed by `message_id` hash;
- **canonical record**: still only DDD/SDD/BDD/TDD/ADR/SSOT and their implementation maps.

## Router axes

The router may emit these finite axes:

- `intent`: feature | fix | refactor | investigation | docs | release | unknown
- `scope`: trivial | code-local | behavior | contract | ownership | unknown
- `risk`: low | medium | high
- `confidence`: low | medium | high
- `affectedLayers`: ddd | sdd | bdd | tdd | adr | ssot
- `recordSearch.mode`: none | recommended | required
- `recordCapture.mode`: none | candidate | canonical
- `implementationMap.tier`: none | file-map | symbol-flow | full-graph
- `gate.mode`: none | narrow-confirm | option-gate
- `validation`: focused-test | lazy-test | doctor-smoke | explicit-confirmation and related command hints

These axes are routing summaries. They do not replace records or hooks.

## Gate precision

Option gate reduction is forbidden if it means skipping real ambiguity. The allowed compression is:

- deduplicate repeated questions,
- batch related questions into one structured ask,
- avoid re-asking already answered questions,
- use narrow confirmation when there is one high-confidence candidate,
- provide evidence with a Recommended option without self-selecting it.

The forbidden compression is:

- treating low confidence as resolved,
- proceeding after an unresolved option gate,
- selecting Recommended without the user,
- closing a queue in chat only,
- hiding source-of-truth conflicts.

## Capture semantics

`recordCapture.mode` is a workflow state over existing storage, not a new store:

| Mode | Meaning | Storage |
|---|---|---|
| `none` | No durable capture needed for trivial/no-impact work | none |
| `candidate` | Durable non-canonical capture or planning note | `.lazy-harness/knowledge/candidates.jsonl` or `.lazy-harness/planning/**` |
| `canonical` | User-confirmed or contract/behavior/ownership truth | DDD/SDD/BDD/TDD/ADR/SSOT records plus required implementation map |

Candidate capture never satisfies canonical obligations.

## Implementation-map tiers

Implementation-map tiers refine ADR 0030. They are thresholds, not alternatives to ADR 0030 when a canonical implementation record is required.

| Tier | Use | Required detail |
|---|---|---|
| `none` | trivial/no implementation impact | no map |
| `file-map` | small local code or docs/tooling path | files, roles, validation |
| `symbol-flow` | behavior/contract implementation change | files, key symbols, flow, focused tests |
| `full-graph` | ownership/API/framework/risk/cross-layer change | MD map + graph.jsonl edges + generated index expectation |

## Consequences

Positive:

- Agents have fewer ad hoc judgement points.
- Small tasks avoid maximal record/graph overhead.
- Safety-critical ambiguity remains gated.
- Future profiles can be minimum-safe presets rather than bypass switches.

Negative / risks:

- A router can become a hidden decision-maker if allowed to mutate records or queues.
- Axis drift can create a shadow layer model if not fixture-tested.
- Advisory output may be ignored unless later measured.

Mitigations:

- Router starts read-only.
- Self-test fixtures protect invariants.
- SDD defines finite axis values.
- AGENTS compression waits until router fixtures are stable.

## Implementation map

### Records

- `.lazy-harness/planning/workflow-compression-router-plan.md` records the user-confirmed plan and Opus/Oracle cross-validation.
- `.lazy-harness/spec/platform/workflow-compression-router.md` defines the route contract.
- `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md` remains the hook enforcement decision.
- `.lazy-harness/decisions/0019-ambiguous-detection-force-gate.md` remains the ambiguity gate decision.
- `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md` remains canonical implementation-map storage.
- `.lazy-harness/decisions/0035-interview-queue-close-mandate.md` remains queued answer closure authority.
- `.lazy-harness/decisions/0036-record-search-trigger-by-intent-not-keyword.md` remains record-search trigger authority.

### Implementation files

- `.lazy-harness/scripts/task-router.ts` implements read-only routing.
- `.lazy-harness/bin/lazy` dispatches the `route` subcommand and documents truthful command usage.
- `.lazy-harness/scripts/self-test.py` protects route fixtures and read-only invariants.
- `.lazy-harness/fixtures/task-router/**` contains route fixture cases.

### Validation

- `.lazy-harness/scripts/self-test.py`
- `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Host sync validation in medivance after source commit.
