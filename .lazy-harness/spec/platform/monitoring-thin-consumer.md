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
  - keep judgement.model in the lazy-harness Pi composition layer using the running Pi extension context's modelRegistry.classify on openrouter/typesafe/jev-1.14 only
  - use the module model router reservation gate and native request/decoding; disable retries
  - keep rule-steering and memory unavailable; use the module in-memory worker default
  - fence read records, capture and frame admission at lifecycle boundaries and changed catalog bytes
  - observe metadata only outside Git with bounded private logs; status and log failures must never call a model or block Pi
  - resume completed same-session fences with fresh scoped pipelines while preserving lifetime reservations and no-retry state
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

## Fabric compaction coexistence

User-approved 2026-11-14; confidence: code-evidence + offline SDK evidence, not live qualification.
The original private probe (Pi 1.5.0, pi-fabric 0.135.2; 18 isolated runs) proved identical
Fabric compaction with monitoring in both load orders, safe stale-result discard, and resume
through success/cancel/error. It also found three coverage/diagnostic gaps: a leading summary
was lost behind the newest 32 messages with Pi's default 20000-token kept tail; generic role
rendering clipped it to 1500 characters; attached masked a disposed window awaiting rebuild.

The monitoring pin fixes snapshot/material coverage. `OBSERVER_LIMITS` explicitly requests
32 recent native messages plus an 8192-byte maximum summary share, capped at one third of
the 65536-byte total snapshot ceiling. The summary is a separate provenance-labelled item,
not a duplicate native tail message. `summaryIncluded`, `summaryOmittedBytes` and
`truncatedHead` report inclusion, omitted original UTF-8 bytes, and first kept native index.
The total bound includes JSON escaping/metadata/hashes; full mode (tailMessages 0) is unchanged.

Material renders `[summary]` derived-summary context using deterministic Fabric-bracket/Markdown-header-first,
section-prefix truncation and `[summary omitted N bytes]`. It is outside newest-first region
trimming, never an own item or a region compaction unit. In the 16384-byte material window,
after catalog and own items, it reserves 512 bytes of headroom and takes at most
min(4096, floor(min(maxSourceBytes, remaining - 512) / 2)) text bytes; serialized JSON is checked
and shrunk further. With no viable room/source slots, context can be omitted rather than
cause material_limit. A 10000-byte catalog regression still reaches the fake judge.

Status semantics: `attached = !closed` means the composition is installed; `paused` means
pre-boundary fence; `rebuilding = needsPipeline || draining.size > 0` includes physical drain;
`ready = attached && !paused && !rebuilding`. Thus before_compact is attached/paused/rebuilding,
terminal compact is attached/not-paused/rebuilding, and next valid frame plus drain is ready.
Closed or unavailable/off status is not ready. Ready does not promise classifier budget or quality.
Event-budget `window.renewals` is not a count of lifecycle rebuilds. Metadata-only save/report
allowlists preserve these booleans without any body fields or model call.

### Coexistence Implementation map

- `vendor/lazy-harness-monitoring/hosts/pi/src/observer.ts`: `readObservationSnapshot`, separate bounded summary and hash; `ObservationLimits.maxSummaryBytes`.
- `vendor/lazy-harness-monitoring/packages/core/src/engine/compaction-summary.ts`: `boundedSummary`, byte-accurate deterministic section prefixes.
- `vendor/lazy-harness-monitoring/packages/core/src/engine/monitoring-core-realtime-material.ts`: `regionLines`, `RealtimeMaterialWindow.capture`, separate derived context with remaining-room admission.
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/index.ts`: `OBSERVER_LIMITS`, `composeObserve` status and unchanged generation/permitted fences; `load.ts` provides vendor-free not-ready status.
- `.lazy-harness/scripts/monitoring-report-data.ts`: `projectStatus` readiness allowlist.
- Protection: `packages/lazy-harness-pi/tests/monitoring-attach-phase1.test.ts`, `monitoring-report.test.ts`; vendor `hosts/pi/test/summary-coverage.test.ts`, `packages/core/test/summary-material.test.ts`.
- TDD: `.lazy-harness/tests/monitoring-attach-phase1.md`; evidence capsule: `.lazy-harness/evidence/monitoring-core/compaction-summary-coverage.md`; graph ids `kg_monitoring_compaction_summary`, `kg_monitoring_status_readiness`, `kg_monitoring_compaction_summary_tests`.

Remaining limits: derived summary is not authoritative instructions or fresh evidence; bounded
snapshots/material can omit older detail, headers if even headers cannot fit, or summary context
when the catalog/own item consumes the window. No changes to Fabric/Pi compactor ownership,
default token retention, classifier lifetime budget, abort guards, SDK pin or dependencies.
This is synthetic offline proof, not provider quality, hard termination, memory/RSS or restart proof.
ADR 0063 and module-composition SDD remain unchanged. Discovery capture / Rule placement:
this existing SDD is primary; TDD records protection, planning one line, no new global policy.

## Ownership and installation

`vendor/lazy-harness-monitoring` is a git submodule pinned to
`8ff4cdf` (PR #26 head; re-pin to the merged monitoring main commit before merge, or merge after PR #26 with a fast-forward pin). Module contracts remain there:
`lazy-harness.module.json`, `composition.ts`, `docs/design/attachment-contract.md`,
`docs/design/module-contract.md`, `docs/design/result-format-audit.md` and
`docs/design/host-input-ports.md` (the latter is historical design; exported contracts prevail).
No module source is copied into this repository. Relative imports intentionally consume the
checkout, not a published package. Deployment requires this checkout layout and initialized submodule.

Install: `git submodule update --init vendor/lazy-harness-monitoring`, `bun install --frozen-lockfile`
at this root, then `bun install --frozen-lockfile` inside the submodule. Both lockfiles are respected;
submodule files/lockfile are unchanged. No package-local SDK pin: the root development SDK remains
0.85.1, and bun.lock returns to the main baseline. The running Pi supplies ctx.modelRegistry; local
structural types describe getModelOfType/classify without importing a version-specific SDK runtime
or the module eval helper. The 1.5.0 SDK's core/extensions/types.d.ts and core/model-registry.d.ts
confirm this context shape. Older/missing registries fail closed only on explicit observe startup.
The unrelated before_agent_start prompt narrowing and all tsconfig changes are reverted.
Node capture tests retain --experimental-transform-types: importing the phase-1 composition reaches
packages/core/src/sdk/diagnostics.ts parameter properties. A direct strip-only Node probe fails with
ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX; the configured capture target passes. Production Pi transpiles
extensions. No npm publish/Fabric install.

Grounding used direct overview/drill/canonical reads because the user prohibited every real model
call, including a Reader worker. The original shared checkout is not edited or switched.
Draft PR #15 is reference only and is superseded by this implementation, not merged or closed.

## Fresh-install resilience (2026-11-14, user-approved option A)

The Mac fresh-install batch prepares the pinned monitoring checkout in every source-install/update
path before Pi/OMP registration: `install.sh` (including the persistent cache source), `lazy update`
and `lazy pi install` (global/local; shared OMP wrapper too) call `install-source-deps.sh`.
It runs `git submodule update --init --recursive vendor/lazy-harness-monitoring`, then frozen Bun
installs at root and submodule. Failures abort registration with a repair hint, never enable observe.
Repeated runs are safe and lockfiles/pin/dependencies are unchanged. Bash 3.2 and Linux are supported.
Dry-run performs no clone/fetch/checkout/submodule/dependency installation. Existing-source sync
preview describes the current checkout, not a fetched future revision. `lazy sync` itself only copies
files: it neither pulls source nor installs dependencies, so its drift/seed semantics stay unchanged.

Production bootstrap `installOptionalMonitoring` imports only the vendor-free config parser
(the module budget import is type-only/erased). Off/absent never resolves vendor files (including the new vendor-free config controls). Explicit
observe registers a read-only status command and loads composition dynamically at the real
`session_start`; registration replays that initiating event exactly once and forwards subsequent
session replacements to the existing lifecycle fences. A missing/uninitialized module or missing
transitive dependency yields `attached: false`, `stage: off`, reason `monitoring_module_unavailable`
and an install hint. A single warning is emitted per extension instance; no follow-up turn, hook
denial, retry or model call is introduced. Other startup failures use `monitoring_start_failed`.
All non-monitoring hook registration remains synchronous and independent of optional startup.
Healthy module composition and telemetry remain unchanged. No host-local activation file is created.

Discovery capture / Rule placement: this SDD is the primary approved installation/component contract;
TDD and the existing planning continuation hold protection/status only. No new global operating rule,
model invocation, dependency, submodule pin change, merge, shared-checkout edit or legacy graph
migration is authorized. Exact-intent policy/capability resolution has no matching rules; source
organization baseline is observe-only. macOS execution itself remains a user-side smoke check.

## Explicit enable/disable/config (2026-11-14, user-approved option A)

`lazy monitoring enable [--doc PATH]... [--no-default-docs] [--calls N] [--usd X]
[--read-format F] [--force] [--dry-run]`, `lazy monitoring disable [--dry-run]`, and
`lazy monitoring config` share the existing monitoring dispatcher with report. These are offline
file-management controls, not activation of the running extension, model calls or a reload.
Only `.lazy-harness/monitoring-attach.json` is persistently changed, in the selected host root.
No dependencies, lockfiles, submodule changes, automatic login or model/provider lookups.

Explicit enable defaults (distinct from the absent/manual parser's off/zero defaults):
- `references.stage: observe`.
- Catalog: `.lazy-harness/ssot/monitoring-records-ownership.md` as
  `ssot:monitoring-records-ownership`, and `.lazy-harness/decisions/0062-monitoring-core-own-repository.md`
  as `adr:0062-monitoring-core-own-repository`, only when present; missing defaults are skipped with a message.
- Extra `--doc` paths are root-relative, ids are `<layer>:<lowercase filename without extension>`
  (`decisions` maps to `adr`). Repeated identical paths are deduplicated; id collisions reject.
  No ambient scan or path normalization that would hide traversal. `--no-default-docs` omits defaults.
- Budget overrides the parser with maxCalls 100, maxConcurrent 1, maxQueued 2,
  maxReservedTokens 1000000, maxReservedUsd 0.05; other MonitoringModelLimits retain parser defaults.
  `--calls` is a nonnegative safe integer and `--usd` a finite nonnegative decimal.
- `readFormat`: `pi-hashline-edit-pro-v1` when the user's Pi settings packages list contains
  pi-hashline-edit-pro (npm/versioned string or source-object/local-path entry), else `pi-read-text-v1`.
  Settings live under `$PI_CODING_AGENT_DIR` or `~/.pi/agent`; an unreadable/unknown file uses plain read.
  Explicit `--read-format` overrides detection; all three parser formats are accepted.

Before any write, `parseMonitoringAttachConfig` and `admitCatalog` enforce the real bounded path,
symlink, byte, UTF-8 and aggregate limits below. Prints a whole-file removal/addition diff; an existing
file (even identical) refuses overwrite without `--force`. Publication uses a same-directory exclusive
temp file with fsync and atomic link (no-clobber) or rename (force); no secrets, mode 0644 subject to
umask. Symlinked config/directory, nonregular/over-64-KiB config and changed file content refuse.
`--dry-run` validates and previews but creates nothing. Disable shows the existing file before deleting
only it, preserves records/logs/status and is idempotent when absent. Config prints parsed effective
values and parser/catalog validation, effective off/zero when absent; invalid input reports failure
and exits nonzero without writing. No command turns on monitoring in the running Pi instance.

Next steps: conditional `/login openrouter` hint, `/reload` in Pi, `/monitoring status`. Authentication
is intentionally uncertain: no auth storage or secret values are read to suppress that hint.
`/monitoring enable` and `/monitoring disable` call the same helper for the extension's current project
root and notify reload, never invoke it. Bare slash controls use defaults (custom flags are CLI-only).
Production off/invalid config now retains this vendor-free control/status command, but still installs
no monitoring hooks and never imports the vendor. Existing observe status and `status --save` are
unchanged; a running observe instance stays active until the user reloads after disable.

### Enable/disable Implementation map

- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/manage.ts`: `manageMonitoring`,
  `detectReadFormat`, `handleMonitoringControl`; shared parser/catalog admission, offline preview,
  config-only atomic publication/removal and UI notifications.
- `.lazy-harness/scripts/monitoring.ts`: `monitoring`; report delegation and config-helper loading.
  Framework source uses its own package; synced hosts use recorded `state/synced-from-commit.sourceRoot`
  if no package exists locally. It imports code there but never changes cwd or writes that source root.
- `.lazy-harness/bin/lazy`: monitoring dispatcher; exports the resolved host root as before.
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/load.ts`: vendor-free controls in off,
  invalid, awaiting and unavailable modes; existing lazy observe lifecycle/status forwarding unchanged.
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/index.ts`: direct installed observe
  command controls; ordinary status/save path unchanged.
- `packages/lazy-harness-pi/tests/monitoring-manage.test.ts`: offline temp-root defaults, real parser/
  catalog, path/size/symlink/UTF-8/count refusal, overwrite/dry-run/disable/config, fake settings,
  Pi delegation/no-reload, dispatcher and synced-host source resolution. Registered in package.json's
  monitoring/capture/full test chain; Reader SDK regression and Pi typecheck remain required.
- TDD: `.lazy-harness/tests/monitoring-attach-phase1.md`; planning:
  `.lazy-harness/planning/monitoring-core-live-integration-plan.md`; graph rows `kg_monitoring_manage_*`.

Discovery capture / Rule placement: this SDD is primary; TDD protects the contract and planning holds
one continuation. Exact-intent monitoring-config policy/capability resolution returned no matches;
code organization is observe-only. Zero model calls including Reader workers; direct record reads.
One isolated enable worktree and one unmerged PR. No shared-checkout cwd or live activation file access.

## Configuration (manual file fallback)

Optional host-local `.lazy-harness/monitoring-attach.json`; absent means references off and zero
model budget. The later activation key is `references.stage: "observe"`. Only off/observe are accepted;
active/shadow and memory/rules keys reject. Installation never creates this file; explicit enable does.

The parser additionally accepts `catalog: [{id, path}]`, `readFormat`, `budget` and `observeLog`.
`observeLog: false` disables logging; a string selects an external state base directory.
Absent means on only in observe. No host-local activation file is created or modified.
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
Stored OpenRouter auth is resolved by the running Pi registry; no credentials belong in config/records.
Environment API-key fallback is suppressed. Attachment does not create an SDK runtime, refresh a
model catalog or import the host repository's installed SDK. Only exact classifier lookup is used.

## Long-session observation (fix 2026-11-13)

First live observe on this project's long main session stopped at its first frame with `scope_or_catalog_unavailable`: the monitoring Pi observer defaults to `maxMessages: 128` with `tailMessages: 0`, so a session with thousands of messages yields an unavailable snapshot on every frame. The host now passes `OBSERVER_LIMITS = { tailMessages: 32 }` (opt-in tail mode of `PiMonitoringObserver`, byte-bounded newest messages, snapshot stays available); U1 reads only recent history (`historyTurns` 4). An unavailable frame now stops with its own reason `frame_unavailable`, separate from scope/catalog changes. No module change.

## Material budget fix (2026-11-13)

After the long-session fix, live inputs were skipped with `selection_material_unavailable`. Reproduction with the real attach code, the live two-record catalog (9,832 bytes) and large messages showed the window note `material_limit`: the host passed BOTH `historyTurns: 4` (in since-last mode this adds one history blob up to `maxSourceBytes` 8,192 without checking the remaining window budget) and `historyMode: 'since-last'` (a budgeted region). Catalog + blob exceeded the 16,384-byte window, the window entered a gap and no judgement was dispatched. The host now passes only `historyMode: 'since-last'`; the region is the U1 history and is budgeted against what the catalog leaves. Diagnostics: selection skips append the window reason to `errorClass` (for example `selection_material_unavailable:material_limit`), and `/monitoring status` adds `window: {state, sources, bytes, lastReason}`. No module change.

## Classifier failure detail (2026-11-13)

After the material fix, the first live judgement failed with `classifier_uncertain` (1 call reserved, no usage), which stops the classifier for the session by design (no retry of uncertain outcomes). The binding swallowed the reason. An offline reproduction with the real attach code and the real Pi 1.5 `ModelRuntime.classify` (`openrouter/typesafe/jev-1.14`, 23 KB request, 12 questions) returned `stop` with usage, and two small direct probes also succeeded with and without the empty env override, so the live cause is not reproduced yet. The binding now records a bounded failure class and never the provider text: `aborted`, `field_mismatch`, `stop_<stopReason>_<kind>` or `threw_<kind>`, where kind is auth/timeout/rate/size/aborted/network/other plus an optional HTTP status. It appears as `budget.used.lastFailure` in `/monitoring status` and is appended to the observe `errorClass` (for example `classifier_uncertain:stop_error_auth_401`).

## Selection job deadline (fix 2026-11-13)

With the failure class in place, the live log showed `classifier_uncertain:aborted` after ~1,072 ms: `createRealtimeSelectionPipeline` defaults the realtime job deadline to `jobTimeoutMs` 1,000 ms, shorter than a real Jev judgement on the full U1 view, so the coordinator cancelled the call; an aborted call is uncertain and stops the classifier for the session (no retry, by design). The host now passes `realtimeLimits.jobTimeoutMs = budget.timeoutMs + JOB_TIMEOUT_MARGIN_MS` (10,000 + 2,000 ms by default), so the job deadline covers the model timeout. No module change.

## Window renewal for long sessions (fix 2026-11-13)

A live `/monitoring status` (old instance, before the job-deadline fix was reloaded) showed `window.state: stopped`, `lastReason: event_budget` after `framesSeen` 3,769: the module material window (and coordinator) stop permanently after `maxEvents` 2,048 frames, and every Pi event counts, including streaming deltas, so a long session silently stops judging. The host now renews the selection pipeline at the next `input` frame once the window has stopped or observed `WINDOW_RENEW_EVENTS` (1,024) frames: the old pipeline is retired like a fence (late results discarded) and a new one starts at that input; the session model budget and classifier state are NOT reset. `/monitoring status` reports `window.renewals`. No module change.

## Skip reasons and queued inputs (fix 2026-11-14)

Live: normal prompts were judged (3 skips) but a message typed while the agent was still answering produced no observe line. Offline reproduction with the real attach code: a queued `input` (`streamingBehavior: followUp` or `steer`) advances the coordinator intent mid-run, the earlier job is invalidated and the queued input's own job is either never admitted or not current (`material_or_permission_not_visible`/`deferred`, coordinator reasons such as `intent_changed`); none of these notes is in the module's traced selection set, so nothing reached the log. The host now records exactly one final outcome per input: an input without a final outcome after the job deadline plus `SWEEP_GRACE_MS` (1,000 ms) is logged as `skipped` with `errorClass` `queued_input_<followUp|steer>:<reason>` or `not_judged:<reason>` (last selection note, else last coordinator trace reason, else `no_selection_note`). The sweep runs on each new input and on `/monitoring status`; duplicate finals for a frame are suppressed. Phase-1 policy (user option B, 2026-11-14): queued follow-up/steer inputs are recorded, not specially judged; judging them at delivery time would be a module trigger change (for example `run.start`), not a host fix. `/monitoring status` `lastOutcomes` now include `errorClass`.

## Ports, stages and lifecycle

All nine majors are advertised as v1 because the module manifest inventories the full capability
surface. Version support is NOT availability or activation. The loader checks module support and
host majors before any factories/hooks. `memory.review-sink`, `memory.source`, `policy.registry`
and `rule.verifier` are unavailable; their purpose modules are not registered and cannot start.
`state.persistence` is unused (stateless/volatile composition), no durability claim.

- judgement.model: lazy-harness `createPiModelBinding`, not the monitoring hosts/pi eval transport.
  Local structural types and exact-model/Jev guards avoid version-specific SDK/eval imports; the module router generates native choice/bool requests,
  reserves lifetime calls/tokens/USD before invoke, and decodes answers. Pi classify has maxRetries 0;
  uncertain transport (including same-scope deadlines) permanently stops this backend, with no automatic retry or fallback. Explicit retired-scope cancellation discards the result without poisoning a new scope; it never retries the old frame.
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

Production off does not import vendor code or validate its manifest: no monitoring hooks, registry access, workers, sources or
provider calls. Direct `attachMonitoringPhase1` composition probes still validate the manifest. Observe installs module `hosts/pi` generation/observer/frame plumbing, preflights
U1 only, and uses the real-time selection/region-compaction pipeline. It executes no jobs, reports,
record-body writes or injection. Model reservations are shared for the session lifetime, including scope resumes.
Boundary notifications synchronously invalidate admission/attestation and retire the pipeline; physical
settlement drains asynchronously (including shutdown), never in a Pi lifecycle handler. Completed
`session_compact`, `session_compact_failed` and `session_tree` allow the next real valid frame to
start a fresh material window/coordinator/selection pipeline through public start ports (no synthetic
session_start). The shared classifier backend retains lifetime calls/tokens/USD and uncertainty state.
Old trace completions are recorded as stale skips, never accepted decisions or read exposure.
Before switch/fork remains paused until completion; native fork/switch replaces the session through
`session_start`. A replacement after startup remains permanently closed with
`session_replaced_reload_required`: clean native re-scope has not been proven, so /reload is required.
Shutdown, missing-frame, changed-catalog and unavailable-snapshot failures remain closed.

## OBSERVE telemetry contract (2026-11-13 option A)

`/monitoring` or `/monitoring status` is a read-only Pi command: attached/paused/rebuilding/ready/stage/stopped reason,
hashed scope and generation, catalog ids/versions and aggregate UTF-8 bytes, watch events (`input`
only), lifetime used/reserved and remaining calls/USD/tokens, reported usage totals, counters
(frames, judgements, run/skip/defer, region compaction notes, errors), last five outcomes (ids only),
log path/written/dropped/errors and classifier stop state. It never dispatches a model. Off installs
no monitoring hooks or log; the vendor-free control/status command remains available. No ambient catalog expansion.
`tail` is intentionally omitted (optional). Status is volatile, not restart-durable.

Log location: `$XDG_STATE_HOME/lazy-harness/monitoring/observe/<project-sha256>/<UTC-date>.jsonl`,
falling back to `~/.local/state`; the project hash is SHA-256 of the resolved project path. Custom
bases are rejected at write time if under the project, inside any Git checkout, or symlinked.
Owned base/project directories are 0700, regular no-follow files 0600. A bounded 64-entry async
queue drops on overflow, a strict 2 MiB daily cap drops new rows, and writes prune files older than
14 days. Log failures only increment counters; they never throw into Pi or trigger turns.

Host schema `lazy-harness-observe/v1` is an explicit metadata projection of the module's
`monitoring-trace/v1` callback, public selection notes (`region_within_budget`, `region_compacted`,
failures), and `judgementEntriesFromExchange`; the module file sink is deliberately NOT used because
it persists content bodies. Field allowlist: `schema`, `time`, `sessionIdHash`, `bindingGeneration`,
`frameId`, `eventId`, `trigger`, `outcome` (judged/skipped/refused/failed/compaction), `decisionMode`
(run/skip/defer/null), `confidence`, `selectedDocuments` (id/version), `candidateCount` (admitted
catalog documents), `compaction` (kept/dropped/withinBudget), `modelCalls`, `reportedUsd`,
`reportedTokens`, `latencyMs`, `budgetRemaining` (calls/usd/tokens), `errorClass`. Missing reported
usage/confidence or unexposed compaction counts are null, never invented zero. Calls on compaction
rows are separate from primary judgement calls. Remaining budget uses conservative reservations,
not reported cost; latency is end-to-end frame-to-outcome time. Selected ids come from native bool
selection, not proof of actual reading, delivery or execution. No conversation/record bodies,
prompts, arbitrary error messages or credentials are persisted. The core-decoded decision is
authoritative; raw late answers cannot increment run/skip/defer counts.

## Offline report collector (2026-11-14, user-approved A1)

`/monitoring status --save` notifies the same metadata JSON as plain status and explicitly saves
it as `status-latest.json` in the project's external observe state directory. The file is 0600,
its directory 0700; unsafe/Git/symlink locations fail with an advisory notice. Plain status remains
unchanged. Saving works in the optional loader's unavailable/awaiting status without loading vendor
code. `observeLog: false` still permits explicit snapshots at the default state location; custom
string bases are honored. Off retains the vendor-free control/status command. The state file is not restart-live status.

`lazy monitoring report [--lines N] [--out FILE] [--issue] [--repo OWNER/NAME] [--dry-run]` is
Bash-3.2-compatible dispatcher + Bun offline collection, with no model/client imports or new deps.
It collects OS/arch/hostname, host HEAD/dirty, pinned monitoring submodule status, bun/node/pi
versions (missing is noted), config existence and ONLY stage/catalog id/path/readFormat/numeric
budget fields, an allowlisted saved status with mtime age, and last N (default 20, range 1..1000)
physical lines across yesterday/today UTC. Unknown schema/malformed rows are omitted, nested v1
observe metadata is explicitly projected; unknown extra keys never escape. Summary counts are by
outcome/mode/errorClass, calls/reported USD (missing costs noted), nearest-rank latency p50/p95.
This is a sampled report, not lifetime billing evidence. Metadata reads are regular no-follow files,
max 2 MiB per daily log and 64 KiB config/status; oversized/unsafe files refuse collection.

Privacy boundary: no auth.json, environment dump, sessions, conversation text or record bodies
are read. Home paths become `~`; outbound credential patterns (sk-, ghp_, github_pat_, Bearer,
api_key= variants, private-key headers) refuse the artifact without echoing the match. Errors are
content-free. Explicit status save uses the existing trusted metadata object; collector reprojects
it, including nested objects, rather than trusting imported JSON. Hostnames/catalog metadata still
require human review. Experiment/raw result data is NEVER committed (ownership SSOT).

Default prints Markdown. `--out` is an atomic private external file, refusing every Git worktree,
symlink or unsafe file. Relative output paths use the invocation directory. `--dry-run` writes
nothing and runs no gh command. `--issue` prints the report and exact target before any GitHub
lookup/submission; default repo is lazy-dinosaur/lazy-harness, title `monitoring report: <host> <date>`.
It uses argv, never shell interpolation; adds monitoring-report only if the label exists. Lookup
failure omits the optional label. Dry-run displays command argv with a body placeholder referring
to the exact report above and explains conditional labeling; it does not create an issue.

### Report Implementation map

- `.lazy-harness/bin/lazy` delegates monitoring subcommands to `.lazy-harness/scripts/monitoring-report.ts` (`parseArgs`, `collectReport`, `monitoringReport`, `issueCommand`).
- `.lazy-harness/scripts/monitoring-report-data.ts`: `projectConfig`, `projectObserve`, `projectStatus`, `privacy`, `summarize`; recursive allowlist, outbound refusal and sampled statistics.
- `.lazy-harness/scripts/monitoring-private-state.ts`: `observeDirectory`, `assertOutsideGit`, `readMetadata`, `writePrivate`; state paths and bounded private file I/O. Distributed by the existing scripts/*.ts manifest glob.
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/status-save.ts`: `notifyMonitoringStatus`; shared by `index.ts` and vendor-free `load.ts`. Private I/O helper loads only on explicit save so ordinary startup stays independent of source helper availability.
- `packages/lazy-harness-pi/tests/monitoring-report.test.ts`: offline synthetic privacy, output, status permissions, projection, summary and dry-run tests; registered in the existing monitoring/capture/full regression chain.
- `.github/ISSUE_TEMPLATE/monitoring-report.md`, `README.md`, `packages/lazy-harness-pi/README.md`: reviewed handoff/checklist, never raw secrets or conversation.
- TDD: `.lazy-harness/tests/monitoring-attach-phase1.md`; ownership: `.lazy-harness/ssot/monitoring-records-ownership.md`; planning: `.lazy-harness/planning/monitoring-core-live-integration-plan.md`.

Discovery capture / Rule placement: this existing SDD is the primary A1 contract; TDD adds protection
only and planning one continuation. Exact-intent policy/capability resolution returned no matches;
organization is observe-only. One isolated report worktree, one unmerged PR, zero model calls,
no activation edits or lock/dependency/pin changes. Legacy graph migration remains separate.

## Implementation map

- Status: implemented
- Primary files:
  - `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/index.ts` — `attachMonitoringPhase1`, `installMonitoringPhase1`, `HOST_PORT_MAJORS`, `UNAVAILABLE_PORTS`; guarded startup, preflight, lifecycle and port assembly.
  - `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/model.ts` — `createPiModelBinding`; exact Pi classifier backend, pure module guard, module reservation/request/decoding integration.
  - `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/read-records.ts` — `createHostReadRecords`; host ledger ownership/fencing.
  - `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/catalog.ts` — `captureRecord`, `admitCatalog`; explicit byte admission/currentness.
  - `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/config.ts` — `readMonitoringAttachConfig`, `parseMonitoringAttachConfig`; off/observe and zero-budget defaults.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — default-off optional loader call; existing before_agent_start behavior unchanged.
  - `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/load.ts` — `installOptionalMonitoring`; vendor-free startup, guarded dynamic import, initiating-event replay and unavailable status.
  - `.lazy-harness/scripts/install-source-deps.sh` — shared recursive submodule and frozen-install preparation, used by `install.sh`, `.lazy-harness/scripts/lazy-update.ts` and `.lazy-harness/scripts/pi-package.ts`.
  - `packages/lazy-harness-pi/tests/monitoring-install.test.ts` — absent/empty/missing-dependency extension load, offline dry-run and bootstrap event replay protection.
  - `.lazy-harness/manifests/init-categories.json` — distributes the shared shell preparation helper with framework scripts.
  - `.gitmodules` — submodule wiring. Package SDK pin, tsconfig and bun.lock have no delta from main.
- Telemetry implementation: `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/observation.ts` — `createObservation`, metadata projection of public module trace/notes and judgement-log codec; `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/observe-log.ts` — `createObserveLog`, `observationHash`, bounded asynchronous private log. `createPiModelBinding` owns the shared lifetime reservation/uncertainty guard across pipeline replacements.
- Tests / protection: `packages/lazy-harness-pi/tests/monitoring-attach-phase1.test.ts`; registered in `package.json` and `.lazy-harness/tests/test-strategy.xml` via full regression's existing Pi-capture target.
- Cross-layer links: TDD `.lazy-harness/tests/monitoring-attach-phase1.md`; decisions ADR 0063/0064; common SDD `.lazy-harness/spec/platform/module-composition.md` remains LH-5-owned and unchanged.
- Machine graph ids: `kg_monitoring_attach_phase1_composition`, `kg_monitoring_attach_phase1_model`, `kg_monitoring_attach_phase1_reads`, `kg_monitoring_attach_phase1_tests`.
- Generated implementation index is derived; no new generator or canonical cache is introduced.

## Discovery capture / Rule placement

This primary SDD captures the confirmed phase-1 boundary and Parent correction: production model
transport belongs in lazy-harness, not monitoring hosts. No new global operating rule is created;
exact-intent policy/capability resolution returned no matches.
User correction (2026-11-13, PR #38): the full-suite Reader SDK failure was introduced by this PR,
not pre-existing. The package-local 1.5.0 pin mixed with the root 0.85.1 loader; remove that pin
and consume the running context registry. SDK upgrades are a separate future task. Work is confined
to lazy-harness.attach1 on feat/monitoring-attach-phase1; shared checkout and Parent verification
worktrees are excluded. No model calls or merge are authorized. Source organization baseline applied
observe-only. The planning continuation records both phase-2 backlogs; ADR 0063 and common SDD
are deliberately unchanged (LH-5 ownership). No graph legacy-row migration is folded into this PR.

2026-11-13 OBSERVE option A: implementation is confined to the isolated obs1 worktree, one
unmerged PR; the shared checkout and its live untracked activation file are excluded. Zero real
model/provider calls in development and validation (fake classifier only); submodule remains 659cdc7,
no dependencies or lockfile changes. This section supersedes the prior reload-only same-session
fence behavior, not the safe replacement-session closure. Discovery capture: this SDD is primary;
TDD contains protection and the four-row layer matrix; the existing plan gets one continuation line.
Rule placement: component contract here, not a new global policy (exact-intent resolvers had no matches).
