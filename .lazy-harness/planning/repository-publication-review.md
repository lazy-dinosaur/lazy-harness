# Planning — Repository Publication Review and Cleanup

Status: active — Phase1 source published on review branch; Phase2 V2 source closure reconciled for gated publication; Phase3 pending
Layer: Planning

## Rule digest

- Status: active
- Layer: Planning
- Scope: transient-plan
- Aliases:
  - 전체 커밋 푸시 정리
  - 다른 세션 변경도 검토
  - publication dependency closure
- Applies when:
  - integrating and publishing the user-approved Main framework changes before separate V2/G16 phases
- Must:
  - judge necessity, completeness, dependencies and public suitability, not authoring session
  - preserve original dirty/private/frozen work, all newer upstream fixes and normal validation hooks
  - publish only reviewed public-safe allowlisted source/canonical records and verify actual remote hash
- Must not:
  - bulk-add runtime evidence, credentials, real ledgers, vectors, model output or dependency trees
  - claim unfinished SDK/native compatibility or Phase2/3 code promotion complete
  - force-push, push origin/main, reset/stash originals or infer product model/DB/cash approval
- Record completion:
  - retain dispositions/reasons, exact scope, checks, commit/remote evidence and remaining compatibility facts here
- Related records:
  - `.lazy-harness/ssot/project-identity.md`
  - `.lazy-harness/ssot/rule-sources.md`
  - `.lazy-harness/behavior/agent-owned-target-context-transition.md`

## User-confirmed scope, correction and execution approval

The user repeatedly approved inspect **all** cross-session needed changes → necessary public-safe changes → normal commit/push → continue. Earlier author-scoped “our files only” exclusion is superseded: authorship is provenance, not necessity. Do not ask a new general approval or make the user classify hundreds of files. Preserve original dirty worktrees and private/frozen prototypes; cleanup does not mean deleting originals.

User selected an isolated publication worktree and explicit review branch `work/publication-main`, based on `origin/main`. The private ignored input manifest retains the exact approved local paths and handoff. Original Main, design/V2 and G16 worktrees are approved read-only inputs, not active host rules or mutation targets. Current target CLI is the sole writer. No stash/reset/checkout/write of originals, global installs/SDK-major upgrade, release, financial/product model, DB, embedding, or policy-activation effects are authorized.

Phase1 is framework Main only: all necessary local Main code, canonical contracts/corrections and Pi/OMP/runtime-usage public-safe groups. Phase2/3 publish G16 dependency closure and V2 differences separately, without switching a branch checked out elsewhere. Normal hooks are mandatory; the only authorized push is `git push -u origin work/publication-main`, never a plain push using inherited origin/main tracking.

## Grounding and context-transition workflow evidence

Parent direct session switching was unavailable. Under the existing agent-owned-target-context-transition contract, Parent launched this approved target-root CLI, remains in its original root and supervises. `-ne` avoids duplicate project/global startup and hashline tools are explicitly loaded. This is a task-specific fallback, not bypassed approval or a new global policy.

Actual startup showed target pwd, `work/publication-main...origin/main`, HEAD `2ec5d2f89f215ad83b02c3e46151be011a149cd8` and only this transferred primary untracked. Dedicated Reader/Fabric tools are unavailable here. Before mutation: direct complete overview → exact primary drill → current local `.lazy-harness/AGENTS.md`, primary, test strategy and relevant canonical/source reads. Original source paths/snapshots were explicitly authorized inputs; arbitrary sibling discovery is excluded.

## Accepted review evidence and integration decisions

Parent's three static source audits were already completed/consumed, not tests or publication. Old Main `5d86e820534ec78ad2c86f6b1a95277112745307` is 0 ahead/22 behind the integration base. V2/G16 diverge from the older `88cd3c0` baseline; publishing a feature review branch is not integration into main. Preserve all 22 newer Main fixes; do not replace shared files wholesale with old Main versions. The earlier 87-candidate comparison found 33 exact-upstream blobs; fresh per-file metadata/dispositions live in ignored publication scratch.

Integrated groups and reasons:
1. Supplied-root layer-completeness repair and 17 shape/root/pairing protections; NUL-delimited changed-file collection excluding **only untracked** exact node_modules plus four isolated cases. Shared self-test keeps upstream strengths.
2. Pi/OMP instance isolation/status/shared transport is already partly upstream. Add the six-module OMP thin adapter, create-only activation and synthetic/default plus opt-in native fixtures; port only remaining native output/steer/session/receive hooks into the current Fabric core. Keep Fabric request/policy/spawn/wait and removed legacy manifest removal. Dynamic SessionManager loading addresses OMP-only source startup; prompt-less Reader startup fails closed. No major dependency alignment.
3. Read-only runtime usage collector and synthetic regression/CLI interface. No real usage/session report is a public fixture; caller inventory and runtime cost do not attest complete attempts, task success or billing.
4. Complete the existing target-context BDD's missing typed policy/capability binding and regression/distribution links, retaining schema/upstream catalog semantics. Preserve the user correction: recoverable transition is agent-owned; process running is insufficient; root/current-context grounding and one writer remain required. No static hook classifies user text or selects scope.
5. Public canonical documentation retains necessary reasons, scope/ownership and compatibility findings. Minimize personal installation paths, backups and live-session ids. Personal runtime settings are not framework defaults; “update our harness” means source work, not merely extension inventory. Duplicate global/project attachments can cause startup conflicts; an approved global rebind must account for explicit project pins, not leave different copies active.

Preserved upstream behavior: Fabric Reader/policy and legacy-manifest removal; invalid-TMPDIR fallback and message-temp/@file transport; partial lifecycle sandbox cleanup; runtime scratch isolation; same-repository worktree fixture routing; honest partial-sync. Unchanged upstream source/tests are not republished as local implementation.

## Public/private and deferred dispositions

Ignore local publication scratch, dependency trees/backups, private directories, runtime state/evidence and generated doctor-negative fixture instances. Explicitly exclude the original generated doctor negative Python file; do not delete it. Keep logs/queue state, real model/session/usage/benchmark artifacts, raw record copies, ledgers, cached vectors and auth bodies out of the allowlist. Original graph rows remain untouched: append only inspected Phase1 source/record/test links, no 37/40 legacy graph migration or experimental/private references. Generated indexes are derived, not proof.

Long cross-session experimental/benchmark narratives are not blanket Main publication inputs. Retain needed framework corrections/contracts in their existing primary records and this capsule; preserve detailed private source evidence in originals. V2/G16 source, SQL, private experiment dependencies and frozen14 are excluded from Phase1 rather than discarded or declared unnecessary.

Known compatibility fact: development SDK/lock remain Pi **0.85.1**, independently of managed Pi **1.3**. Historical mapped-type investigation found the newer user/custom `before_agent_start` prompt union and integration-fixture ABI gap. Normal source checks are not that external probe. The bounded prompt guard/OMP-only loader fix do not implement SDK1.3 dependency/fixture migration. No installed-version or build-only claim is a compatibility pass. OMP remains Experimental; native opt-in skips and untested fork/resume/root/async/artifact cases are not green certification. These limit compatibility claims; a failing current gate still blocks publication.

User-confirmed harness philosophy remains: LLM owns semantic scope/relevance/approval judgments; records are institutional memory, generated indexes cue-only; shape/runtime observers do not become semantic authority. Coding-agent models are distinct from product/embedding/financial authority. The selected future matched Pi/OMP comparison uses GPT-6 Sol medium/common blocking Reader scope, not model substitution or paid execution here. Existing Reader model intent stays unchanged.

## Implementation map / evidence capsule

- `.gitignore`: private/runtime/dependency publication boundary.
- `.lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh` and `scripts/self-test.py#check_layer_completeness_helper`: root/path and same-root matrix pairing; TDD `.lazy-harness/tests/layer-completeness-path-resolution.md`.
- `.lazy-harness/scripts/lazy-check.py#git_paths/default_changed_files` and `tests/lazy-harness/lazy-check-collection.test.py`: untracked dependency/NUL collector; SDD/TDD fast-validation-tier.
- `packages/lazy-harness-pi/omp/`, shared extension, activation, package manifest/tsconfig and default/opt-in tests: `.lazy-harness/tests/omp-runtime-parity.md`; SDD `.lazy-harness/spec/platform/pi-agent-package.md`.
- `packages/lazy-harness-pi/scripts/collect-runtime-usage.ts#collectRuntimeUsage/decodeUsage` and adjacent synthetic tests: `.lazy-harness/tests/runtime-session-usage.md`.
- `.lazy-harness/ssot/policies.json`, `capabilities.json`, manifests and `self-test.py#check_project_operating_rulebook_cli`: existing target-context BDD binding; rulebook SDD/TDD.
- `.lazy-harness/ssot/project-identity.md`: minimized cross-session ownership/SDK evidence, not personal installation publication.
- Private `.local/publication-phase1/`: exact approved inputs, per-file manifest, exclusions, validation/publication evidence. Never stage it.
- Phase1 implementation commit: `d99299f288a0490b00251ad74965f82f627b42d9`; normal pre-commit and canonical pre-push passed, exact review-branch push succeeded and remote equality was independently verified. Publication receipt follows; Phase2/3 and SDK1.3 certification remain incomplete.
- Initial coherent checkpoint: fast static passed 52 changed files, zero errors/warnings; normal Pi/Node/Bun-test typechecks passed against frozen 0.85.1 dependencies. Package-wide Bun invocation produced 271 passes, 10 native OMP opt-in skips and 8 setup failures in the unchanged legacy native Subagents CLI matrix (5.14s): it requires explicit external LAZY_READER_NATIVE_SYNC/ASYNC package paths, which are unavailable and are not restored under Fabric. All newly integrated default source/loader/transport/accounting cases passed in that invocation. This is not an all-green package-wide or native compatibility claim. Canonical record-lint passed 196/196. Normal current full framework/SDK integration gates remain required; no failing fixture is deleted, weakened or supplied invented native paths.
- Final standard after the source/contract/index batch passed once: ok=true, fullRegression=true, evidenceReused=false, 404.876s total; fast-static 52 files/0 issues in 0.352s; full framework self-test 92 checks, 0 skipped, jobs=4 in 404.379s. It includes current real SDK capture integration, Fabric policy/transport, existing cleanup/routing/sync cases and newly registered offline OMP/accounting suites. This does not erase the separate unconfigured legacy native CLI matrix or certify managed SDK1.3/native OMP. No unchanged focused suite/standard rerun after green; further updates are publication receipts only.
- The standard gate regenerated the tracked policy-rulebook explain view from the merged catalogs (9 policies); reviewed public-safe and included as derived output, not copied private evidence. Git discovery found the existing shared pre-commit delegate active and no installed pre-push hook. Preserve originals/config: use the normal pre-commit hook and explicitly run the unchanged canonical `.lazy-harness/hooks/pre-push.sh` gate before the exact approved branch push; no hook-disable, no-verify or shared hook/config mutation.

### Phase1 publication receipt

- Implementation/source commit `d99299f288a0490b00251ad74965f82f627b42d9` contains the reviewed 53-file allowlist: 2,503 insertions/175 deletions across all necessary Phase1 groups. Six verified graph rows appended; existing 758 rows preserved. All private/runtime/dependency data and V2/G16 experimental promotion excluded, not deleted.
- Actual normal Git pre-commit delegate ran `lazy test --light` and passed (204.961s wall). The unchanged canonical pre-push script ran full `lazy test` and passed (404.908s wall). No no-verify, disabled hook, altered source gate, shared hook installation or global config change.
- Exact `git push -u origin work/publication-main` succeeded. Independent `git ls-remote` returned `d99299f288a0490b00251ad74965f82f627b42d9` for the review branch, equal to local HEAD; remote main remained `2ec5d2f89f215ad83b02c3e46151be011a149cd8`. Branch now tracks `origin/work/publication-main`; working tree was clean after that push.
- This subsequent amendment is the publication receipt in the same primary, not another source batch, global policy or Phase2/3 completion. It records the verified implementation commit/remote pair; its own final branch HEAD is verified/reported separately after normal commit/pre-push gates. Do not rerun the already passing focused suite/standard merely for this evidence capsule.
- The separate broad Bun invocation remains 271 pass/10 native OMP skips/8 legacy-native setup failures, not all-green. Source SDK0.85.1 normal gates passed; SDK1.3 event/fixture migration and broader native OMP scenarios are still unimplemented/unverified. These do not block this bounded Main-source publication, but do block universal latest-SDK/native-parity claims.

## Phase2/3 next steps (not completed)

G16's Native/caller seven files are not a public dependency closure: account for inherited tests, scale-04 sources and helper dependencies; replace frozen real-source/plan/before.json couplings with synthetic public fixtures. Both reviewed portable allowlists omit new dependencies. Preserve frozen14/private originals. Review V2's distinct model route, maintenance signature and ownership/routing contracts; do not blanket-replace it with G16. Separate source/SQL/privacy inventory and normal fresh gates precede their separate review branches; Phase1 does not authorize live product/DB/model work.

## Discovery capture / Rule placement

### Approved Phase2/3 continuation and source-closure capsule

The user confirmed this same publication workspace as the sole writer after the prior writer exited, and authorized new `work/publication-v2` then stacked `work/publication-g16` branches. Normal exact new-branch pushes only; the Phase1-only push restriction above is extended to those two branches, not origin/main. Startup verified clean Main HEAD and tracking ref `690f433846365b89e1350f4fe5e2c98677c080ef`; live remote returned the same hash and unchanged main `2ec5d2f89f215ad83b02c3e46151be011a149cd8`. Direct overview, exact-node drill, current records and the explicitly authorized narrow handoffs were consumed before mutation. No Reader/Fabric is available here.

Source-review candidates retained for implementation (not fresh test results): the runtime SQL closure is the ordered 23 numbered migrations through `0023_validation_receipt.sql`; `templates._seed` also reads `0001_knowledge_init.sql`. Alternative apply-form SQL is not an additional migration. Catalog APIs retain plan/home/hash/approval and conflicting-existing-catalog guards; actual business catalog values are excluded in favor of explicitly synthetic offline inputs. Portable-source inventories must cover conditional Python dependencies, dynamic JS hosts and SQL assets, not just AST imports. Native relocation must preserve bounded repository containment and use fresh unrelated-cwd/HOME denial probes. Private prepare fingerprints and inherited source/plan fixtures require synthetic public adapters, never copied payloads.

The conditional `jev_failure.{uncharged,capture,resolve}` dependency remains unresolved in the supplied review. Only actual approved source or explicit fail-closed unavailability is permitted; no fabricated financial accounting, zero price or release behavior. Source publication does not validate PostgreSQL semantics, managed SDK1.3/core compatibility, native live execution or financial/model/DB effects. Preserve the original acceptance evidence and frozen originals; fresh public relocation evidence is a separate obligation.

### Phase2 initial source checkpoint — not publication completion

The current target branch is `work/publication-v2`, created from verified Main `690f433846365b89e1350f4fe5e2c98677c080ef`. The initial public candidate now contains the V2 runtime Python modules, inactive knowledge extension source, 18 numbered V2 SQL assets, empty configuration example, portable source requirements/docs and a new synthetic relocation suite. Original source worktrees were read-only inputs; no source/private/frozen data was deleted or overwritten. Main runtime/package/Fabric files are unchanged.

Public-copy changes beyond literal source transfer: the portable inventory includes the previously omitted CURRENT V1/semantic/lineage modules and runtime SQL assets; the diagnostic rejects absent explicit config before config-backed imports and requires a caller-supplied vector query instead of a business query; personal-path SQL comments and per-case private lineage diagnostic queries/identifiers are omitted. No financial policy, schema application or runtime activation is inferred.

Initial focused checkpoint: direct `test_public_relocation.py` passed **13 tests in 0.837s**; `lazy check` passed **78 changed files**. This proves only the enumerated synthetic/import/asset/boundary cases in `.lazy-harness/tests/v2-source-review.md`, not full public relocation, PostgreSQL correctness, Pi SDK/native compatibility, original frozen-file byte equality or actual trial success. Two verified implementation/protection graph rows were appended; prior 764 rows were preserved and no generated implementation cache was rebuilt.

**Still incomplete:** final all-necessary V2 file/maintenance/record reconciliation, inherited map/reduce test/helper publication, stronger clean-extraction/JS/private-HOME-open denial evidence, final standard and normal commit/pre-push gates; then the separately stacked G16 source/SQL/native/test-fixture closure and publication. No V2 implementation commit or remote branch exists from this checkpoint, and G16 has not been created. Do not mistake an import-safe core inventory for the whole approved scope. SDK0.85.1 versus managed1.3, unconfigured legacy-native setup failures and native OMP skips retain the Phase1 limitations above.

Record judgment: retain this bounded public source/contract checkpoint in the existing primary plus the necessary existing V2 SDD/TDD paths and four-row matrix. Detailed per-file transfer/operational notes belong only in ignored scratch. No new general approval is needed; this is an unfinished approved work unit, not an authority contradiction or a root-guard denial.

### Phase2 final V2 closure and terminal publication judgment

This continuation is bounded to V2 only; G16 is the next worker, not created or started here. Current-root pwd/status/HEAD, actual AGENTS, complete overview → exact current primary → SDD/TDD/test strategy grounded the work once using direct fallback (dedicated Reader unavailable). Existing edits and the 53-file Main publication/upstream fixes remain intact. Exact source-work policy/capability resolve returned no match; code organization baseline was observe-only, with no architecture/profile inference or unrelated rewrite.

The initial 78-path candidate is extended by the four distinct V2 maintenance modules, conditional fragment parser, two code-only synthetic measurement adapters, eight inherited offline suites and clean-extraction/JS acceptance fixtures. `portable_source.ALLOWLIST` is the exact experiment file manifest; `PORTABLE.md` classifies content safety/exclusions. The V2 SDD/TDD own the independent diagnostic/query/explicit-namespace, fixture adapter and package boundaries and four-row matrix. Four verified graph links in total extend the prior 764 rows; no old graph row migration or generated implementation-index replacement occurs.

Public-copy adapter decisions: original `judge_measure` performed private/config/paid work at top level, so import safety alone was inadequate. Public measurement and judging entry points are synthetic-only and fail closed without explicit fixtures; no HTTP/auth/live-data code or automatic estimated charge/release reconciliation is provided. Unknown/nonfinite/negative costs and ambiguous failures stop without replay. Real V2 runtime brief/model routing and authority rules stay unchanged. Private lineage IDs/aliases were replaced in offline tests; the provider requires an explicit namespace instead of a deployment default. Maintenance signatures and exact host/revision/preview/guard semantics are retained. No G16 financial helper is imported or invented.

Reconciliation judgment: the selected closure includes generic runtime/schema/seed/loader/helper source and public synthetic protections, not original private corpus, service-starting legacy pytest infrastructure or old experiment narratives. Extra prototype/pilot paid scripts and raw business fixtures are excluded by content/scope, not because they were ignored/untracked. Original source/prototypes/frozen14 are read-only inputs, never reset/stashed/rewritten; no frozen-byte-equality certification is asserted. Stable protocol namespace constants/schema IDs and pinned model/image metadata remain code, not operational receipts. No model/DB/financial/policy/extension activation or global SDK action is authorized or performed.

Terminal acceptance requires the coherent-batch `lazy check`, one fresh clean-extraction acceptance batch, final standard, normal commit hook and the unchanged canonical pre-push gate (manual if no installed hook), then **only** `git push -u origin work/publication-v2`, live remote/local hash equality and clean target status. A checkpoint is not terminal success. Exact counts/durations/commit/remote proof belong in terminal stdout and ignored scratch, avoiding a self-referential evidence-commit loop. The source/record closure is accepted for this gated publication; any real failing gate must be fixed before that terminal receipt. SDK0.85.1 versus managed1.3, unconfigured legacy-native setup failures, native OMP skips, live PostgreSQL/financial execution and G16 completion retain their existing limitations.

Discovery capture: completed V2 source/contract/protection deltas converge in this primary and existing V2 SDD/TDD with verified Implementation maps; no new backlog outside the already approved next G16 phase. Rule placement: no new global/host operating policy or team-memory store. Terminal record judgment is complete for the V2 durable delta when the enumerated publication gates succeed; remote hashes are execution evidence, not another semantic delta requiring a receipt-only commit.

One existing primary owns publication scope, correction reasons, bounded compatibility findings and deferred phase backlog. Scope=transient-plan, confirmation=user-confirmed. Necessary API/fixture/ownership deltas are captured once in existing SDD/TDD/SSOT records with four-row regression matrices. No new AGENTS grammar, duplicate global policy, personal-memory rule or standalone publication narrative. Operating bindings implement the already accepted BDD after exact resolver found them absent; source organization remains thin-adapter/shared-authority, observe-only, no line-count split or untouched rewrite.
