# Medivance Homepage App Harness Comparison — 2026-06-04

Status: analysis-record
Layer: Planning
Scope: framework-source comparing downstream host evidence
Requested by: user asked to compare another developer's harness in `/home/lazydino/dev/medivance-homepage` with lazy-harness.

## Evidence read

Lazy-harness source records/files:

- `.lazy-harness/ssot/project-identity.md`
- `.lazy-harness/planning/lifecycle-compare-dogfood-handoff.md`
- `.lazy-harness/spec/lazy-sync-drift-detection.md`
- `.lazy-harness/AGENTS.md`
- `.lazy-harness/README.md`
- `.lazy-harness/bin/lazy`
- `.lazy-harness/framework/framework-contract.md`

Medivance homepage files/records:

- `/home/lazydino/dev/medivance-homepage/AGENTS.md`
- `/home/lazydino/dev/medivance-homepage/README.md`
- `/home/lazydino/dev/medivance-homepage/docs/PROJECT-MAP.md`
- `/home/lazydino/dev/medivance-homepage/docs/ssot/ssot-map.yaml`
- `/home/lazydino/dev/medivance-homepage/docs/ssot/adr/ADR-003-ai-development-principles.md`
- `/home/lazydino/dev/medivance-homepage/scripts/wt-cli.mjs`
- `/home/lazydino/dev/medivance-homepage/scripts/dev-cli.mjs`
- `/home/lazydino/dev/medivance-homepage/scripts/dev-instance-cli.mjs`
- `/home/lazydino/dev/medivance-homepage/.lazy-harness/ssot/project-identity.md`
- `/home/lazydino/dev/medivance-homepage/.lazy-harness/ssot/project-document-sources.md`
- `/home/lazydino/dev/medivance-homepage/.lazy-harness/domain/medivance-product.md`
- `/home/lazydino/dev/medivance-homepage/.lazy-harness/tests/test-strategy.md`
- `/home/lazydino/dev/medivance-homepage/.lazy-harness/tests/test-strategy.xml`

## Executive comparison

The homepage repo contains an app-specific harness, not a competing generic framework. It is mainly:

1. root `AGENTS.md` soft rules,
2. `docs/PROJECT-MAP.md` one-work-unit workflow and module map,
3. `docs/ssot/**` requirements/ADR/test/security documents,
4. `docs/evidence/**` persisted validation evidence,
5. app-local worktree/dev-instance scripts,
6. installed lazy-harness records that adapt those app docs for future agents.

Lazy-harness is a meta-harness/framework. It is:

1. record-first institutional memory under `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,...}`,
2. lifecycle/pre-action hooks and Jcode wiring,
3. portable sync/install/update system,
4. self-test/doctor/graph/audit tooling,
5. context delivery, capability registry, lifecycle compare/timing telemetry,
6. dogfood loop across Medivance/PWA/homepage.

## Rough footprint observed

Lazy-harness source at comparison time:

- record files across source layers: 181
- top-level scripts: 38
- hook files: 40
- self-test check functions: 78

Homepage non-lazy app harness at comparison time:

- `docs/ssot` files: 45
- `docs/evidence` files: 12
- app scripts: 4
- root `AGENTS.md`: 74 lines
- `docs/PROJECT-MAP.md`: 219 lines

## Strengths of homepage app harness

- Very concrete product guidance: Next.js 16, Bun, PGlite/Postgres, Drizzle, Server Actions, Vitest, Playwright, Zod.
- Strong app architecture doctrine: pragmatic hexagonal, mock-first, contract-first TDD, `Result<T>`, narrow ports, deep modules.
- Excellent work-unit closure rule: `PROJECT-MAP read -> Contract-First TDD -> gates -> log/evidence -> PROJECT-MAP update`.
- Good SSOT document structure: `docs/ssot/ssot-map.yaml` defines tiered source documents; domain PRDs are split under `docs/ssot/prd/**`.
- Evidence-first quality story: mutation/e2e/security/performance style evidence belongs under `docs/evidence/**`.
- Good local developer ergonomics: `scripts/wt-cli.mjs` creates branch worktrees and links `.jcode` / `.lazy-harness`; dev instance scripts allocate named Next dev instances and logs.

## Weaknesses / limits of homepage app harness

- Most rules are soft/document-driven. `AGENTS.md` itself says concrete hook/gate/skill mapping is platform-specific and not defined there.
- No tracked `.github`, `.husky`, `lint-staged`, gitleaks, semgrep, or CodeQL automation was found in the tracked files checked during this comparison.
- Source-of-truth ordering is split: root `AGENTS.md` says its rules are the single source for those rules, while installed `.lazy-harness/ssot/project-identity.md` says `.lazy-harness` records and `docs/PROJECT-MAP.md` / `docs/ssot/**` define host truth. This is manageable but should be made explicit for agents.
- The app harness is project-specific and not portable by itself. It relies on human/agent discipline unless paired with lazy-harness automation.
- It has strong app gates, but no framework-level memory mechanics like option gates, queue close, implementation-map graph, route/context delivery, read-debt guard, lifecycle compare, or self-test parity.

## Strengths of lazy-harness relative to homepage app harness

- Turns soft rules into executable surfaces: hooks, `lazy test`, `lazy doctor`, `lazy sync`, lifecycle helpers, graph hygiene, record audit, context delivery, capability registry, etc.
- Generic across hosts: source repo owns framework logic; homepage is a downstream evidence host.
- Strong anti-hallucination posture: default-unknown, record-first search, root-bound convergence, option gates, user-correction capture, and record-as-output.
- Durable multi-layer memory: DDD/SDD/BDD/TDD/ADR/SSOT plus graph.jsonl and generated indexes.
- Dogfood telemetry: route decisions, hook timings, lifecycle compare summaries, post-patch readiness records.
- Reproducible framework validation: `self-test.py` covers 78 check functions at comparison time.

## Weaknesses / risks of lazy-harness relative to homepage app harness

- Much heavier and more complex. It can produce overhead, stale graph conflicts, or sync churn if used for simple app tasks.
- Generic framework records can be stale or wrong inside a host if not superseded by host records. Homepage already records stale prior identity facts in graph and supersedes them via `.lazy-harness/ssot/project-identity.md`.
- It can over-record app-level facts if not carefully pointed back to `docs/PROJECT-MAP.md` and `docs/ssot/**` as source documents.
- Sync-based downstream updates need discipline: homepage app code is not the framework source of truth.

## Compatibility assessment

They are complementary:

- Homepage app harness answers: "What is this product, how should app code be structured, what docs/tests/evidence close an app work unit?"
- Lazy-harness answers: "How should AI discover/verify/remember host facts and avoid skipping gates across sessions/tools?"

Best combined rule for homepage:

```text
For app/product work in medivance-homepage: read `.lazy-harness/ssot/project-identity.md` and `.lazy-harness/ssot/project-document-sources.md` first, then `AGENTS.md`, `docs/PROJECT-MAP.md`, and relevant `docs/ssot/**`. Use lazy-harness records to point to and enforce those sources, not to replace them wholesale.
```

## Recommended integration improvements

1. Add a small explicit bridge section to homepage `AGENTS.md`: lazy-harness records are agent memory/enforcement; `docs/PROJECT-MAP.md` and `docs/ssot/**` remain product source docs.
2. Keep app validation evidence in `docs/evidence/**`; keep framework/dogfood evidence in `.lazy-harness/planning/**` or `.lazy-harness/logs/**`.
3. Convert only stable app soft rules into lazy-harness records/gates. Do not copy every PRD detail into `.lazy-harness` records.
4. Let `scripts/wt-cli.mjs` continue linking `.jcode` and `.lazy-harness`, but document that linked harness state is shared across sibling worktrees and should not be treated as per-worktree app state.
5. If homepage's app harness becomes a reusable pattern, extract only the generic pieces into lazy-harness source; keep Medivance-specific architecture and product rules in the homepage repo.

## Rule placement

- Rule: homepage's non-lazy app harness is complementary product/application governance, not a replacement for lazy-harness framework automation.
- Scope: transient-planning / dogfood analysis.
- Primary record: `.lazy-harness/planning/medivance-homepage-harness-comparison-20260604.md`.
- Why not AGENTS.md: this is a comparison/evaluation, not stable global grammar.
- Why not `.jcode`: this is shared framework dogfood evidence, not local private Jcode wiring.

## Discovery capture

- DDD: no new domain invariant; existing homepage domain record already captures product scope.
- SDD: possible bridge contract between homepage `AGENTS.md`/`docs/ssot/**` and lazy-harness record priority.
- BDD: no user-facing app flow change.
- TDD: no new test case yet; comparison suggests possible future doctor/audit check for host AGENTS/docs bridge clarity.
- ADR: no architecture decision yet.
- SSOT: homepage source-of-truth ordering is the main integration point.
- Planning: this record captures the comparison and recommended integration improvements.
