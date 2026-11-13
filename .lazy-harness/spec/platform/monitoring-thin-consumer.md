# SDD — Monitoring phase-1 thin consumer

User-confirmed: 2026-11-13, option A. Phase 1 only; no live activation or paid calls approved here.

## Rule digest

- Status: active
- Layer: SDD
- Scope: host-project
- Aliases:
  - monitoring phase 1 attach
  - monitoring thin consumer
  - Fabric-free monitoring attachment
- Applies when:
  - composing the pinned monitoring module in the lazy-harness Pi package
  - configuring U1 references observation or updating the submodule pin
- Must:
  - validate the module-owned root manifest and all required integer majors before composition
  - default references to off and paid-call budgets to zero; require separate approval for observe and budget admission
  - keep judgement.model in the lazy-harness Pi composition layer using Pi ModelRuntime.classify on openrouter/typesafe/jev-1.14 only
  - use the module model router reservation gate and native request/decoding; disable retries
  - keep rule-steering and memory unavailable; use the module in-memory worker default
  - fence read records, capture and frame admission at lifecycle boundaries and changed catalog bytes
- Must not:
  - add a pi-fabric dependency or call the monitoring eval transport as production transport
  - infer read exposure from selection, preparation, enqueue or hook delivery
  - activate stages or spend a model budget as part of installation or offline tests
- Related records:
  - `.lazy-harness/decisions/0063-module-composition-contract.md`
  - `.lazy-harness/decisions/0064-v1-enforcement-retired-v2-direction.md`
  - `.lazy-harness/spec/platform/module-composition.md`
  - `.lazy-harness/tests/monitoring-attach-phase1.md`
  - `.lazy-harness/tests/test-strategy.xml`

## Ownership and installation

`vendor/lazy-harness-monitoring` is a git submodule pinned to
`659cdc782bef43fd77a79bbc5e77a16ad61d22ab`. Module contracts remain there:
`lazy-harness.module.json`, `composition.ts`, `docs/design/attachment-contract.md`,
`docs/design/module-contract.md`, `docs/design/result-format-audit.md` and
`docs/design/host-input-ports.md` (the latter is historical design; exported contracts prevail).
No module source is copied into this repository. Relative imports intentionally consume the
checkout, not a published package. Deployment requires this checkout layout and initialized submodule.

Install: `git submodule update --init vendor/lazy-harness-monitoring`, `bun install --frozen-lockfile`
at this root, then `bun install --frozen-lockfile` inside the submodule. Both lockfiles are respected;
submodule files/lockfile are unchanged. The Pi package's development SDK is pinned to 1.5.0,
because the root CLI development SDK 0.85.1 has no classify API. The root CLI pin is unchanged.
A minimal prompt-field narrowing accommodates Pi 1.5 custom-start events; no v1 behavior is restored.
Node/Bun types cover the module's existing native-classifier helper; skipLibCheck applies only to third-party declaration conflicts (Bun fetch.preconnect versus SDK fetch declarations). Node capture tests use --experimental-transform-types because the module contains TypeScript parameter properties; production Pi transpiles extensions. No npm publish/Fabric install.

Grounding used direct overview/drill/canonical reads because the user prohibited every real model
call, including a Reader worker. The original shared checkout is not edited or switched.
Draft PR #15 is reference only and is superseded by this implementation, not merged or closed.

## Configuration (nothing enabled by this PR)

Optional host-local `.lazy-harness/monitoring-attach.json`; absent means references off and zero
model budget. The later activation key is `references.stage: "observe"`. Only off/observe are accepted;
active/shadow and memory/rules keys reject. No config file is created by this change.

The parser additionally accepts `catalog: [{id, path}]`, `readFormat` and `budget`.
Catalog admission is explicit, never an ambient scan: at most 16 distinct record paths under
`.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning}`, each at most 8192 bytes,
aggregate at most 12288 bytes. Paths are contained, no symlink components, stable file identity/stat
and UTF-8 bytes; versions are SHA-256 of freshly captured bytes. Changes revoke the composition.
`readFormat` is owner-selected `unknown` (default), `pi-read-text-v1` or `pi-hashline-edit-pro-v1`.
Unknown/truncated/partial tool output cannot suppress a whole document.

Budget fields are the module's MonitoringModelLimits: calls, concurrency/queue, timeout,
input/output byte bounds, output tokens and lifetime reserved tokens/USD. Defaults are zero calls,
zero reserved tokens/USD, concurrency 1 and queue 0. Observe does not itself grant paid calls;
a separately approved nonzero budget is necessary before the module router can dispatch.
Stored OpenRouter auth is resolved by ModelRuntime; no credentials belong in config/records.
Environment API-key fallback is suppressed. SDK creation has catalog network refresh disabled.

## Ports, stages and lifecycle

All nine majors are advertised as v1 because the module manifest inventories the full capability
surface. Version support is NOT availability or activation. The loader checks module support and
host majors before any factories/hooks. `memory.review-sink`, `memory.source`, `policy.registry`
and `rule.verifier` are unavailable; their purpose modules are not registered and cannot start.
`state.persistence` is unused (stateless/volatile composition), no durability claim.

- judgement.model: lazy-harness `createPiModelBinding`, not the monitoring hosts/pi eval transport.
  Imports only its pure exact-model/Jev guard; module router generates native choice/bool requests,
  reserves lifetime calls/tokens/USD before invoke, and decodes answers. Pi classify has maxRetries 0;
  uncertain transport permanently stops this backend, with no automatic retry or fallback.
- worker.execution: module `createHandlerWorkerPort`, built on its in-memory default, owned by the
  runtime. Logical wait is not physical settlement. Observe starts no jobs.
- session.read-records: host `createHostReadRecords`, bounded volatile immutable snapshots,
  exact version/source/grant/cursor scope, replay/mutation/overflow protections, single-flight
  snapshots and generation fencing. Module expose/bind adapters preserve common result semantics.
  Module `createReadResultAttestor` gets only actual main-session Pi read hooks, explicit successful
  paired results, owner-selected format and freshly captured catalog bytes. No Reader summaries.
- report.enqueue: module expose/bind result adapters and `hosts/pi` parent delivery/mailbox mechanics.
  Phase-1 observe returns matching failed receipts and never installs delivery/injection hooks.
  Enqueue and hook-boundary delivery are separate from provider input/read evidence. Active delivery
  and capture-before-dispatch origin/dependencies remain a later approved extension, not this PR.

Off loads/validates the manifest only: no monitoring hooks, model runtime, workers, sources or
provider calls. Observe installs module `hosts/pi` generation/observer/frame plumbing, preflights
U1 only, and uses the real-time selection/region-compaction pipeline. It executes no jobs, reports,
writes or injection. Model reservations are shared for the pipeline lifetime. Boundary notifications
close admission, attestor, ledger, observer, pipeline and worker runtime; raw idle is awaited at close.
Before/failed compaction, navigation, session replacement and shutdown never relabel old records.
After such a fence a reload/new extension instance is required; there is no automatic restart.

## Implementation map

- Status: implemented
- Primary files:
  - `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/index.ts` — `attachMonitoringPhase1`, `installMonitoringPhase1`, `HOST_PORT_MAJORS`, `UNAVAILABLE_PORTS`; guarded startup, preflight, lifecycle and port assembly.
  - `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/model.ts` — `createPiModelBinding`; exact Pi classifier backend, pure module guard, module reservation/request/decoding integration.
  - `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/read-records.ts` — `createHostReadRecords`; host ledger ownership/fencing.
  - `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/catalog.ts` — `captureRecord`, `admitCatalog`; explicit byte admission/currentness.
  - `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/config.ts` — `readMonitoringAttachConfig`, `parseMonitoringAttachConfig`; off/observe and zero-budget defaults.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — default-off startup call and Pi 1.5 prompt narrowing.
  - `packages/lazy-harness-pi/package.json`, `packages/lazy-harness-pi/tsconfig.json`, `bun.lock`, `.gitmodules` — SDK/type/submodule wiring.
- Tests / protection: `packages/lazy-harness-pi/tests/monitoring-attach-phase1.test.ts`; registered in `package.json` and `.lazy-harness/tests/test-strategy.xml` via full regression's existing Pi-capture target.
- Cross-layer links: TDD `.lazy-harness/tests/monitoring-attach-phase1.md`; decisions ADR 0063/0064; common SDD `.lazy-harness/spec/platform/module-composition.md` remains LH-5-owned and unchanged.
- Machine graph ids: `kg_monitoring_attach_phase1_composition`, `kg_monitoring_attach_phase1_model`, `kg_monitoring_attach_phase1_reads`, `kg_monitoring_attach_phase1_tests`.
- Generated implementation index is derived; no new generator or canonical cache is introduced.

## Discovery capture / Rule placement

This primary SDD captures the confirmed phase-1 boundary and Parent correction: production model
transport belongs in lazy-harness, not monitoring hosts. No new global operating rule is created;
exact-intent policy/capability resolution returned no matches. Source organization baseline applied
observe-only. The planning continuation records both phase-2 backlogs; ADR 0063 and common SDD
are deliberately unchanged (LH-5 ownership). No graph legacy-row migration is folded into this PR.
