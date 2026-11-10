# TDD — Isolated native ready-material delivery to main-model input

Status: bounded native D1 ready/stale final-input consumption qualified; full native chain/live unqualified

## Rule digest
- Status: active
- Layer: TDD
- Scope: framework-global
- Confidence: medium
- Aliases:
  - native context delivery
  - D1 final input
  - 준비된 결과 메인 입력 전달
- Surface terms:
  - ready/stale material
  - actual provider payload
  - foreground non-wait
  - isolated SDK consumer
- Applies when:
  - qualifying delivery of prepared context into an isolated actual Pi model request
- Must:
  - use actual SDK-issued destination session identity and independently inspect actual model HTTP payload plus consumer reply
  - treat previous worker result files as explicit Host-owned NEW dependencies, never forge old scope/native IDs into a new lifetime
  - consume only ready/current context offers without waiting for pending work, preserve discard reasons and drain owned work
  - keep current real conversation injection, real-user data, business actions and default/shared activation off
  - distinguish this D1 handoff slice from full native source/judge/worker/Core/D semantic/lifecycle qualification

## Approved bounded work and capture judgement
User said `다음 진행해줘` after the two actual worker cases completed. The next bounded D1 execution is isolated ready/stale main-model input delivery, not a new proposal or real/live activation. Host-selected conservative new window:2 SDK dispatches/2 actual model HTTP requests/3 total HTTP incl normal auth/90s deadline(+5s physical stop grace); model remains existing openai-codex/gpt-6-luna OAuth, warming/retries/tools off. No unused prior requests transfer. Requested512 output tokens are not a claimed server hardcap; Codex previously omitted that field. Existing worker cases/green regression are not repeated. Full D rollout/manual-control gates remain.

Discovery capture: this record owns the new controlled D1 scenario and its verified actual outcome below. Rule placement: test scenario/evidence here, not a new operating policy; source-code policy resolve was advisory with no matches. Production API/Core/entrypoint remain unchanged. The operational probe composes existing Coordinator/public SDK hooks; no new ready material is a native observer/judge/worker pipeline claim.

## Acceptance ledger
1. Actual ready context offer reaches `context_with_system`, `before_provider_request`, and independently decoded final model HTTP input exactly once; response matches both actual worker values6/ALPHA BETA.
2. Changed source version excludes stale ready material from the ACTUAL HTTP input; independent model consumer returns empty items, with source_changed reason preserved.
3. A separate pending job is physically unresolved at both hooks and HTTP dispatch: foreground never awaits its outcome. Capture descriptive hook samples, not production p95 claims.
4. Actual target SDK session identity/current lease is checked at context/provider/HTTP boundary; raw owned work drains on cancellation/dispose. No native producer/semantic-judge accuracy or exhaustive revocation-window proof is inferred.

## Implementation map
- `.lazy-harness/scripts/monitoring-core-realtime.ts`: existing bounded `RealtimeMonitoringCoordinator`, context-channel `takeReady`, currentness and dependency invalidation, unchanged.
- `.lazy-harness/evidence/monitoring-core/pi-context-native-probe.ts`: isolated public DefaultResourceLoader extension factory/SessionManager, actual context/provider hooks, Host-owned fixture preparation and independent actual HTTP/consumer comparison. These are operational assertions, not a reusable/public delivery component.
- `.lazy-harness/evidence/monitoring-core/pi-context-native-result.json`: actual passed ready/stale SDK/HTTP/independent-consumer receipt, including physical pending-work drain and owned session disposal. Graph has source/test validation/call edges; `.lazy-harness/generated/implementation-index.json` receives only these verified incremental rows, not a full-corpus regeneration or new authority.
- `.lazy-harness/tests/monitoring-core-pi-worker.md`: previous actual worker results, not rerun or relabelled as the current source/judge pipeline.
- `.lazy-harness/spec/platform/pi-monitoring-observation.md`: current observer/realtime Host boundaries.
- `.lazy-harness/planning/monitoring-core-live-integration-plan.md`: task93/D broader qualification and rollout remain separate.

## Layer completeness judgement
| Layer | Independent delta | Judgement |
|---|---|---|
| SDD | no independent API delta | Existing SDK/Coordinator ports are composed only in an operational probe; thin evidence pointer only, no public/default injector. |
| BDD | no independent visible-flow delta | Actual user/main session and opt-in live controls remain unchanged. |
| SSOT | no independent config/schema/ownership delta | Prior worker files are explicit NEW Host-owned fixture dependencies, not reused native IDs; default settings/credential ownership unchanged. |
| DDD | no independent domain-rule delta | Prior synthetic feature values are consumer test data only. |

## Result
Actual D1 result: 2/2 PASS verified against terminal task, raw JSON, actual decoded provider HTTP input and independent main-model reply. Ready: actual first eligible context step1 offered1 material, actual wire copies1, reply items purpose.counter=6/purpose.labels=ALPHA BETA. Stale: changed Host dependency version offered0/wire copies0, reply items[], source_changed preserved. Each actual SDK target used its own SDK-issued SessionManager identity; context/provider/HTTP lease fences passed. Both cases had another physical preparation promise unresolved at hook AND actual HTTP dispatch, duplicate same-hook offers0, then owned raw work drained and session disposed. Hook samples0.363862ms/0.148718ms are just TWO observations, not production p50/p95/SLA. Total3.646s; actual SDK sessions2/dispatches2/modelHTTP2/totalHTTP2, all200; provider-reported input298/output40/total338tokens. Warm/retry/tool/worker calls0; prior worker/green suite not repeated; no production source/API/Core/shared entrypoint or current-user conversation/business changes. Requested512 output limit was absent on wire; no server-token/invoice/quota guarantee. Source is explicit Host fixture derived from previous actual worker files under fresh dependency identity, NOT a fresh same-run native observer→purpose-built judge→worker→Core→main chain. Full chain, independent wrong-scope/late-revocation/adversarial matrix, readiness-age/discard/speculative-waste statistics, production latency and real-session shadow/live remain unqualified. Record-only state/evidence updates do not repeat old green regression; this new operational probe's assertions are the focused behavior check. Final canonical/graph/cache/receipt readback and targeted record-lint decide task133 completion; this closure admits no further model calls.

## Late-result carry policy (task140)
User chose the recommended policy (read-only context only): deliver at a later request in the same turn if one exists; otherwise carry ONCE to the next turn's first request with an origin/age label, only with unchanged session/branch, unchanged source dependency versions and age <= 120s; otherwise drop with a reason; never twice; relevance left to the main model (no text classification in hooks).

Implementation: `.lazy-harness/scripts/monitoring-core-context-mailbox.ts` `ContextCarryMailbox` (`put`, `take(scope, now, firstRequestOfTurn)`, `traces`; reasons queued/delivered_same_turn/delivered_carried/scope_changed/expired_age/carry_exceeded/source_changed/duplicate/overflow/invalid). Source-local opt-in; the coordinator's intent_changed invalidation is unchanged. Protected by `tests/lazy-harness/monitoring-core-context-mailbox.test.ts` (9/9: same-turn, one carry with label, no mid-turn carry, two-turn drop, age expiry, stale source never injected, wrong scope never injected, no double delivery/duplicate refusal, bounds).

Offline simulation `.lazy-harness/scripts/monitoring-e2e-delivery-sim.ts` → `.lazy-harness/evidence/monitoring-core/e2e-v1/delivery-sim.json` (model calls 0): 137 actual a2 references readiness samples; request k at k·L, next input after G; the real mailbox decides. Delivered share, carry-once vs same-turn-only: L=3s 92.7% vs 0%; L=8s 96.4% vs 59.9% (same-turn 59.9 + carried 36.5); L=15s 96.4% vs 94.2%; independent of G in 10–60s (age p50 ≈ G+gap, below the 120s cap). Remaining drops are the sequence's last turn (no next request, 5–10). Simulated main latency is an assumption, not measured; stale/wrong-scope safety is from unit tests, not this replay.

Layer judgement for this delta:
- SDD: independent delta — new opt-in mailbox component; pointer in `.lazy-harness/spec/platform/pi-monitoring-observation.md`.
- BDD: no independent delta — not wired into the live host; no visible flow change.
- SSOT: no independent delta — no shared config/ownership change; 120s/one-turn are constructor options.
- DDD: no independent delta — policy wording recorded in Planning; no domain rule change.

Final validation after task140: `lazy validate --plan standard --max-seconds=900` exit0, full regression 91 ran/0 skipped, 468s (includes the worker instruction fix, `--probe-sequence`, `ContextCarryMailbox` with its tests and the delivery simulator).
