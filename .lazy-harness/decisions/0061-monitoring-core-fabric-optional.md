# ADR 0061 — Monitoring core is Fabric-independent; integration is optional

Status: accepted; SDK/configuration/generic conformance and corrected final standard qualified within the explicit source-local/synthetic scope; publication/live activation remain off
Layer: ADR

## Rule digest

- Status: advisory
- Layer: ADR
- Scope: host-project
- Confidence: high
- Aliases:
  - monitoring Fabric dependency
  - 독립 코어 선택 연동
- Applies when:
  - defining the reusable monitoring SDK, its configuration and its Pi/Fabric host bindings
- Must:
  - keep the common core/public SDK/configuration usable without Fabric
  - use explicit host-owned ports and separately qualified optional integration
  - preserve one canonical engine implementation and one configuration schema authority
  - distinguish source-local composition, declared host dependencies and independently importable SDK contracts
- Must not:
  - import Fabric internals, require Fabric for the baseline, or silently select another backend
  - treat configuration data as data-disclosure permission or automatic start approval
- Related records:
  - `.lazy-harness/spec/platform/monitoring-core.md`
  - `.lazy-harness/spec/platform/pi-monitoring-observation.md`
  - `.lazy-harness/planning/monitoring-core-live-integration-plan.md`
  - `.lazy-harness/decisions/0043-pi-native-package-in-source-repo.md`

## Decision and reason

After choosing public SDK + declarative schema/validator + generic conformance work, the user explicitly selected “독립 기본＋선택 연동 (Recommended)”. The baseline targets authors of functions beyond our reference modules, including users without Fabric. Keep core semantics and contracts independent; use Pi for its host observation integration and explicit ports for judgement/delivery. Fabric may later provide tool/task/model orchestration through a separately validated connector, not a required import or a new transcript authority.

Using Fabric to develop/test this repository does not make Fabric a product dependency. The actual existing core has no imports; the measured classifier path uses the native SDK. Installed Fabric0.127.1 also imposes its own runtime/compatibility conditions (currently Node>=24). A Fabric-required frontend can be reconsidered for a deliberately Fabric-only audience, but is not selected now.

The initial implementation remains in the current package/source repository. This decision does not publish npm artifacts, create several new repositories/packages, activate collection, install dependencies or increase the paid model budget. Generic SDK host factories remain explicit dependencies; configuration never serializes executable callbacks or credentials. Unsupported/missing bindings fail explicitly without fallback.

## Implementation map

- `.lazy-harness/scripts/monitoring-core.ts`: canonical portable execution/registry/context/proposal contracts and engine; no Fabric import.
- `.lazy-harness/scripts/monitoring-core-observation.ts`: existing SDK frame-to-core/material bridge; host adapter, not a second core.
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring-module.ts`: existing default-off explicit Pi lifetime; a portable public protocol must remove its source-checkout type coupling without rewriting the engine.
- `packages/lazy-harness-pi/package.json`: existing source-local private Pi package; future public subpaths must preserve existing resource/deep-import compatibility. No Fabric dependency is added.
- `packages/lazy-harness-pi/scripts/generate-monitoring-contracts.ts`: declared AST build step for a derived portable protocol, retaining canonical source ownership and a drift check. SDK/schema/test maps and proof are updated after implementation, not invented here.
- `.lazy-harness/tests/monitoring-core-reliability.md`: deterministic core protection versus module semantic quality remain separate. The closed experiment/corpus/unused requests are preserved.

### Connector boundary (corrected 2026-11-09, task154; supersedes the same-day 'Connector selected' entry)

The same-day entry placed a Fabric connector package `hosts/pi-fabric` inside `lazy-dinosaur/lazy-harness-monitoring`. That conflicted with the user's earlier cross-module decision (2026-11-07, option A, recorded in the main checkout `.lazy-harness/ssot/project-identity.md` "2026-11-07 correction"): modules are independent and define contracts (model call, judgement, execution) without Fabric; the lazy-harness composition layer is the only place that depends on `pi-fabric` and attaches modules through Fabric adapters. At the user's direction the two sessions confirmed the meaning with each other (2026-11-09): option (1). Corrected boundary:

- `lazy-harness-monitoring` has NO `pi-fabric` dependency in any package. It defines a module-owned worker execution port (spawn/run/stop/wait, timeout, cancellation, concurrency/lifetime limits) plus conformance tests run against fake implementations. The port shape is owned by the module and must not mirror Fabric's API, so Fabric changes are absorbed by the implementation, not the contract.
- `lazy-harness` implements that port with `pi-fabric` public exports (`pi-fabric/agents`, `pi-fabric/runners`; optionally `pi-fabric/jev` as a judgement backend), owns the exact version pin and the bun/Node >= 24 compatibility check.
- `packages/core` stays Fabric-free (unchanged). Session persistence is not Fabric's role (tmux leaning). Fabric's resident host does not observe the parent session and Jev observation is lossy: neither is an event source or delivery guarantee.
- The knowledge module follows the same rule; its nearest current port shape is `experiments/v2-knowledge-module-runner-01/scale-04/place_write.py` `Ports` (model, embed, choose, ask) in the knowledge worktree, and it will align with the monitoring port shape once defined.

## Rule placement

Component architecture decision, not an agent operating rule. Do not add it to project policy/capability registries as an automatic action. No global Pi/OMP runtime ownership is changed; ADR0055's Reader orchestration and superseded runtime ADR0056 are different scopes.

Rule placement for the 2026-11-09 connector correction:

- Rule: modules (monitoring, knowledge, later ones) never depend on `pi-fabric`; each defines module-owned ports (model call, judgement, worker execution) with fake-backed conformance tests; only the `lazy-harness` composition layer depends on `pi-fabric` (exact pin, bun/Node >= 24 check) and implements those ports.
- Scope: host-project (ownership/dependency boundary across this host's module repositories); monitoring-specific consequences are layer facts of this ADR.
- Primary record: the cross-module boundary lives in the main checkout `.lazy-harness/ssot/project-identity.md` section "2026-11-07 correction — modules live in separate repositories" (owned and corrected by the knowledge-module session). This ADR records only its application to the monitoring core (why the same-day `hosts/pi-fabric` entry was superseded); `.lazy-harness/planning/monitoring-core-live-integration-plan.md` records the work consequences (P1/P3/P7, PR #2 to correct).
- Why not AGENTS.md: not framework-global agent behaviour; it is a dependency/ownership boundary of this host's modules.
- Why not local notes: it is shared project ownership that other sessions and repositories must follow, not a private Pi/OMP preference; nothing was written to `.pi/` or memory.
- Confirmation: user-confirmed — option A on 2026-11-07; on 2026-11-09 the user directed this session to confirm its meaning with the knowledge-module session, which answered option (1) and withdrew its own inferred `hosts/pi-fabric` line.
