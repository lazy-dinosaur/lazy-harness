# TDD — A Implementation Correctness Repairs

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - A implementation correctness repairs
  - graph sync typecheck capability regression
- Applies when:
  - changing graph projection, sync completion, package-health classification, or capability no-op behavior
- Must:
  - preserve SPO and legacy graph facts with explicit authored retirement state and historical exact-ID access
  - reject dirty-behind and incomplete sync inputs without publishing a successful marker
  - distinguish semantic TypeScript checking from bundling and report unexplained nonzero exits as failures
  - preserve policy links and graph/registry bytes on unchanged capability registration
- Must not:
  - infer unknown-marker or append-only capability update policy from these repairs
  - treat focused fixture success as project-wide or standard validation success
- Related records:
  - `.lazy-harness/planning/workflow-churn-reduction-plan.md`
  - `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
  - `.lazy-harness/spec/lazy-sync-drift-detection.md`
  - `.lazy-harness/spec/platform/package-health-generate-remediation.md`
  - `.lazy-harness/spec/platform/capability-resolution.md`

## Approved boundary and regression facts

The initial isolated A approval referenced the workflow-churn plan in the experiment; that experiment-only approval text is not imported from its dirty baseline. The main-based integration authorization below is the durable approval for this checkout. B/C semantic gates, record authoring, taxonomy, live sync and release remain excluded. This is the single primary repair record; detailed execution evidence is transient under `.a-repair/` in the isolated writer repository.

- Graph: shared `projectGraphHint` preserves SPO, legacy endpoints, object values, status and supersession pointers. Only explicitly superseded/rejected graph rows stop contributing current implementation hints. Historical rows remain in graph hints, exact-ID traversal and drill-down. Unknown/missing state remains compatible; Markdown/feature-navigation hints are not globally filtered. The projection marker invalidates older derived caches in memory. No graph corpus migration.
- Sync: dirty checking precedes equal/ancestry paths for known markers. Required Category A files/directories and registry JSON/array shape are preflighted before copy/prune. Parse/input failure exits 3, dirty refusal exits 2, success marker stays behind completed copy/activation. Host rows/metadata and explicit force/dry-run behavior remain protected. This is not transactional rollback after later I/O failure or full registry row-schema validation.
- Validation: `build:node` retains bundling; `typecheck:bun` invokes local `tsc --noEmit` for the Bun CLI. Historical D07 `typecheck:node` delegates to that command and is not a Node-runtime compatibility claim. D07 preserves the active generate/retry and recognized environment-warning contract but no longer calls an unexplained nonzero/empty command result an environment warning. Semantic invalid/valid fixtures execute the package command, not a mocked checker. Missing compiler is a failed prerequisite, never a skipped semantic success.
- Capability: CLI add has no policyIds input, so existing policyIds are retained. An unchanged add writes neither registry nor graph, including timestamps and same-ID historical rows. Changed graph updates still use the pre-existing upsert representation: choosing an append-only replacement/event scheme is pending, not silently implemented.

## Pending choices and prerequisites

- Unknown-marker SDD table says warn while prose says non-behind exit 2. Preserve current behavior; its fixture is observation-only.
- Capability SDD permits graph upsert while graph SDD requires append-only supersession. Changed-update history semantics require an owner decision; no event-ID or same-ID migration invented here.
- Automatic generate removal from the earlier experiment is not adopted: the active SDD requires remediation. Tests mock generate calls, never execute or download them.
- Initial A evidence had no compiler/type declarations and blocked standard on test-owned `/tmp` writes. The continuation authorization below supersedes those environment restrictions, not the original failed/not-run results.
- Prior Node 22/24 declarations expose four Bun 1.3.14 declaration mismatches. The finalization below resolves the Bun CLI target only; neither the earlier Node 26 empty-module probe nor Bun-target typechecking establishes Node 22 runtime compatibility or raises runtime support.

## A continuation — user-confirmed validation preparation

The user requested continuing A after the parent proposed repo-local reproducible type dependencies and test-owned temporary files under `/tmp`. This supersedes the previous no-install/root-only prerequisites for this isolated A continuation only:

- Resolve and install the minimum project-local compiler/type dependencies from normal package registry metadata, record chosen versions and a lockfile; keep package caches/config/install outputs inside this isolated repository and avoid arbitrary lifecycle install scripts. Do not use global installations or publish anything.
- Permit tests to create uniquely allocated temporary artifacts they own under `/tmp`, including the intentional missing-TMPDIR fallback, and clean up only artifacts demonstrably created by this run. No shared `/tmp` sweep, unrelated file access/mutation, original/prior-worktree writes or global settings changes.
- Repair the reviewed global-tsc-dependent fixture to resolve and invoke the same project compiler, with local-only compiler coverage. Classify remaining project diagnostics after provisioning; fix only bounded A-related type/integration defects, not unrelated repository-wide redesign or diagnostic suppression.
- Execute safe focused validation and final standard validation without weakening existing checks. Preserve failed results honestly. B/C policy changes, unknown-marker behavior and capability changed-update history remain outside this mechanical continuation.
- Rule placement: transient-plan approval in this isolated primary repair record; user-confirmed. No shared grammar change or live-host deployment authorized.
- Discovery capture: TDD/Planning updated for continuation; dependency declarations are an SSOT/config delta to document after selection; no new DDD/BDD/ADR decisions.

## Continuation implementation and compatibility boundary (prior checkpoint)

This checkpoint's provisional pin and PATH implementation were blocked by review; the finalization below supersedes them without overwriting their failed evidence.

- Registry metadata and installed manifests select TypeScript 6.0.3 (same compiler release as prior evidence, not an automatic latest-major upgrade), ts-morph 28.0.0 (existing imported source dependency), @types/bun 1.3.14 (Bun runtime release), provisional @types/node 24.13.3, @earendil-works/pi-coding-agent 0.85.1 (engine >=22.19.0), and typebox 1.3.7 (the Pi package's exact dependency, not @sinclair/typebox). Versions/integrities are locked; install uses --ignore-scripts and copyfile backend with local caches. Bootstrap: `bun install --frozen-lockfile --ignore-scripts --backend copyfile`.
- `typecheck:node` explicitly invokes the local TypeScript package through Bun and loads node/bun types. The semantic fixture resolves that same compiler from its package bin metadata, uses explicit project typeRoots and removes global compiler directories from PATH. Valid input must still fail if the project ambient dependencies are inconsistent; no skipLibCheck or error suppression is permitted.
- Five pre-existing source diagnostics surfaced by real checking receive supervisor-approved mechanical alignment only: document ingestion's appliedWrites union includes the existing conflict-recorded runtime result; detector filter callbacks capture a stable const alias; BDD/SSOT crossRef object spreads preserve the verified plain-object own fields. These are not newly introduced A runtime failures or B/C rule changes.
- Node 22 and Node 24 declarations do not satisfy four Bun 1.3.14 declaration references. The isolated Node 26 probe succeeds, but it is NOT adopted as the main pin or evidence of Node 22 support. No newer ambient API surface is silently used to redefine runtime compatibility. Exact diagnostics and the final standard result belong in the continuation evidence artifact, including failures.

## A finalization — user-confirmed two-blocker repair

The user requested continuing the same isolated A repair after the two reviewed blockers: uncontrolled compiler-fixture PATH and declaration compatibility. Preserve previous edits/evidence, actual invalid rejection and valid success, existing Node/Pi runtime support, and all original scope exclusions. No declaration suppression, handwritten ambient patches, global/runtime upgrade or policy expansion is authorized. New evidence lives under `.a-repair/finalization/`; no integration is implied.

- **Hermetic compiler fixture:** construct only test-owned `bun`/`sh` executable wrappers with absolute resolved runtimes, never their containing directories. Exercise the actual D07 alias and local compiler in both absent-tsc and first-on-PATH executable decoy-tsc cases. Demonstrate the decoy works, then assert it was not invoked by either invalid or valid checking. Keep all semantic assertions without skips.
- **Actual target:** `.lazy-harness/bin/lazy` invokes Bun for CLI TypeScript; `build:node` already targets Bun. The existing semantic source glob is `.lazy-harness/scripts/*.ts` plus its imported sources, not the Pi extension. Expose `typecheck:bun` as the exact local compiler command with explicit node/bun declarations; retain `typecheck:node` as the D07 compatibility alias (`bun run typecheck:bun`). It does not typecheck or promise execution of these Bun sources on standalone Node.
- **Pinned declaration resolution:** select `@types/node@26.5.0` solely as the compatible supporting declarations for `@types/bun@1.3.14` → exact `bun-types@1.3.14` → `@types/node:*`. Registry metadata, package declaration source and integrity-bearing lock back this resolution. This is not a Node runtime dependency upgrade. TypeScript 6.0.3, Bun declarations 1.3.14 and all other approved pins are unchanged; no `skipLibCheck` or weakening.
- **Runtime evidence boundary:** inspected compiler program comprises 50 non-declaration source files; its nine built-in module imports/used exports exist in actual Bun 1.3.14. Bun-specific uses are `Bun.argv` and `import.meta.main/url/dir`. The four vendor errors refer to node:util/node:tls declarations, not APIs imported by these sources. Source-derived inventory and existing Bun-executed CLI regressions provide runtime evidence separately from ambient checking.
- **Node/Pi is separate:** keep the existing Pi fixture unchanged and use an owned Git-less temp root. Independently execute the unchanged extension's emitted JS and real local Pi/SessionManager/Typebox packages with actual Node 22.23.2, matching the selected Pi engine `>=22.19.0`. Extension registration/session/schema smoke is limited evidence, not exhaustive Node compatibility. Do not infer Node support from the Bun compiler or use newer ambient APIs to expand supported runtime behavior.
- Supervisor confirmed this bounded target distinction after source/runtime-contract inspection. No new declaration version fishing is required beyond the already evidenced combination. Minimum local install remains `--ignore-scripts --backend copyfile`, with frozen-lock verification; test-owned `/tmp` is permitted, shared cleanup is not.
- Final acceptance requires focused semantic/project checks, unchanged Node/Pi coverage, record lint and normal standard validation against the last mutation. Preserve full top-level standard output; the governor retains only child-output tails, so missing raw child output is an explicit evidence limit, not grounds to instrument or rerun a successful full suite.

## A main integration — user-confirmed approval (2026-09-10)

The user approved preparing an A-only commit/PR against freshly fetched `origin/main`, followed by merge only after exact PR-state validation, independent review and required GitHub checks. This writer prepares the commit only: no push, PR creation or merge before the independent review handoff. B/C discussion starts only after merge; no B/C implementation, deployment or downstream sync is authorized.

- Base: `58fbcbf5e9d632bf9b0e7a87857ad8ed05f01f7b`. Import only the approved 19-file delta from experiment baseline `9c9d508fd3f1d63695c27981be4b86fec73f0871`, never the experiment's pre-existing dirty policy/record snapshot. The two A graph rows are appended without its unrelated context rows. Preserve the original checkout, source experiment and prior artifacts read-only.
- Keep the existing pins, local ignored-script frozen-lock install, actual Bun semantic checking with absent/decoy compiler coverage, separate actual Node22/Pi smoke, and normal checkpoint/standard/commit gates. No global settings, validation instrumentation, hook bypass, ambient declaration patches or runtime-support expansion.
- A tool-postprocessor incident before A import was recovered with explicit owner approval: repo-local formatting/autofix mutation controls only, diagnostics retained, and exactly the preserved 93 dirty paths restored from the verified base. This is transient recovery evidence, not 93 PR changes or a framework policy change. Local controls and raw evidence stay outside the commit.
- Fresh-main focused evidence (2026-09-10): checkpoint 19/19; real local `typecheck:bun` passed; D07 11/11 with absent/decoy TS2322 rejection and valid success; graph 8/8; sync 17 cases/84 assertions (unknown-marker remains observation-only); capability 3/3; unchanged trigger/ingestion/Pi fixtures passed. Separate Node 22.23.2 smoke initialized the extension with 6 events, 9 commands, 1 tool plus real Typebox and SessionManager. Record lint found 0 issues across 186 records. Pins/lock were installed locally with frozen-lock and ignored scripts; these are fresh-main results, not reused experiment green claims.
- Acceptance evidence belongs in the isolated integration evidence capsule: source/installed hashes, exact-state diff, focused command receipts and final `lazy validate --plan standard --format=json` output. Standard is required after this last canonical mutation; its outcome and subsequent commit/review receipts remain transient rather than recursively invalidating the tested record. Successful preparation is not publication/merge or runtime-support certification.
- Discovery capture: **TDD** owns these regressions and approval; **Planning** integration sequence is captured here, no duplicate plan; **SDD/SSOT** retain the check-target/dependency distinctions in the four-row matrix; **BDD/DDD/ADR** have no independent delta. Unknown-marker behavior, changed capability history, legacy graph migration and unrelated backlog/policies remain pending and excluded.

## Layer completeness

| Layer | Judgment |
| --- | --- |
| SDD | Check-target clarification: Bun CLI semantic command is explicit, historical D07 alias preserved; no Node-runtime/API support expansion. Existing retrieval, marker, failure and idempotence contracts repaired; unrelated policy conflicts remain pending. |
| BDD | No independent delta: no product flow, semantic approval or record-authoring behavior change. |
| SSOT | Independent dependency-config delta: package.json and bun.lock define repo-local compiler, Node26 supporting declarations for the Bun-only target, ts-morph and actual Pi/typebox peers. Standalone Node22/Pi runtime evidence is separate; host ownership/support is unchanged. |
| DDD | No independent delta: no domain vocabulary/business rule change. |

## Implementation map

- `.lazy-harness/scripts/record-index.ts`: `projectGraphHint`, `graphPathValues`, `graphRelatesTo`, `mergeGraph` project graph facts/state into the record index.
- `.lazy-harness/scripts/record-map.ts`: `graphMatch`, `loadRecordIndex`, overview and Markdown rendering consume the same projection.
- `.lazy-harness/schemas/record-index.schema.json`: derived SPO/state fields and projection marker schema.
- `.lazy-harness/scripts/lazy-sync.ts`: `detectDrift`, `readSeedRegistry`, `preflightCategoryA`, `syncCategoryA`, `main` enforce input/completion boundary.
- `.lazy-harness/scripts/doctor.py`: `check_package_health` reports unexplained failure while retaining existing remediation.
- `package.json`, `bun.lock`: separate build/semantic commands, `typecheck:bun` target and `typecheck:node` compatibility alias, and reproducible local dependency graph; runtime/type boundaries documented above.
- `.lazy-harness/scripts/document-resource-ingestion.ts`: `PlanResult.appliedWrites` matches `applyConfirmed` runtime action values.
- `.lazy-harness/triggers/code-change.ts`: stable detector alias in `runCodeChangeTrigger` filter callbacks.
- `.lazy-harness/triggers/detectors/bdd.ts`, `.lazy-harness/triggers/detectors/ssot.ts`: `buildBddAsk`/`buildSsotAsk` preserve crossRef own-data structure; protected by existing `check_triggers`.
- Existing `check_document_resource_ingestion_inspect` protects ingestion plan/apply behavior; the semantic fixture protects local compiler resolution with absent/decoy global compilers. Existing `check_pi_package_layout_and_contract` remains unchanged; `.a-repair/finalization/node-pi-smoke.py` separately captures actual Node22 execution without asserting exhaustive support.
- `.lazy-harness/scripts/capability.ts`: `addCapability` preserves policyIds and skips writes on unchanged status; changed `upsertGraphEntry` history remains pending.
- `.lazy-harness/scripts/self-test.py`: `check_implementation_correctness_repairs` registers the four real executable regression files in framework scope (serial until separately audited); host scope does not require source-only test files. Existing package-health checks are not weakened.
- Protection: `tests/lazy-harness/record-graph-projection.test.py`, `tests/lazy-harness/test_lazy_sync_integrity.py`, `tests/lazy-harness/doctor-package-health.test.py`, `tests/lazy-harness/capability-preservation.test.py`.
- Canonical graph id: `kg_a_implementation_correctness_repairs`; generated implementation index remains pending regeneration under the existing missing-index tolerance, not hand-migrated.

## Discovery capture and rule placement

TDD is the primary regression record. Pending contract/dependency choices are captured here; no additional operating rule or policy registry is authored. Source organization follows the resolved observe-only Code Organization Profile; no unrelated restructuring. Per-command results, source/test hashes, intermediate tooling failure and final review evidence belong once in `.a-repair/`, not repeated layer narratives.
