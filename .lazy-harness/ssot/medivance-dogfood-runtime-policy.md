# SSOT — Medivance dogfooding runtime policy

Status: accepted
Date: 2026-05-20
Layer: SSOT
Scope: lazy-harness source repo dogfooding against `/home/lazydino/dev/medivance`
Source records in downstream host: the Medivance install (`/home/lazydino/dev/medivance`) owns its named dev instance workflow, dev runtime restart, and dev instance PR workaround policy records.

## Rule digest

- Status: active
- Layer: SSOT
- Scope: host-project
- Aliases:
  - dogfood 런타임
  - medivance 정책
  - dev instance
- Applies when:
  - dogfooding lazy-harness framework changes from this source repo against the Medivance downstream host
  - deciding whether a check is document-only or needs runtime/UI validation
  - judging Medivance UI persistence or runtime behavior as ready
- Must:
  - run document-only checks (e.g. ingestion `--mode inspect`) without launching the Electron app or a database
  - use the Medivance named `--test` instance workflow and confirm inspect shows the test environment before judging runtime/UI
  - run framework sync first, wait for success, then run host validation; never the same parallel batch
  - after framework sync or host-owned seed convergence changes validation capabilities, policies, generated rulebooks, or test-strategy records, require one serial host full regression to pass before deployment all-clear; a scoped `lazy check` alone is not sufficient
  - treat the Medivance product branch, product source, and in-progress working tree as protected user work during lazy-harness sync or deployment remediation
  - scope any sync rollback or repair explicitly to lazy-harness-managed framework/transport files; preserve product files and current product branch state
- Must not:
  - launch an unnamed/default dev app, reuse a running original instance, or use local/prod DB for runtime dogfood
  - parallelize source-to-Medivance sync with the command that validates the synced feature
  - run `git reset`, branch rollback, checkout/revert of product files, or any repository-wide rollback in Medivance to repair a lazy-harness deployment
- Record completion:
  - dogfood runtime-boundary changes update this SSOT and the downstream host's named-instance/restart policy records
- Related records:
  - `.lazy-harness/planning/document-resource-ingestion-implementation-plan.md`

## Rule

When this lazy-harness source repo dogfoods framework changes against Medivance, distinguish document-only checks from runtime/UI checks.

Document-only checks, such as `document-resource-ingestion.ts --mode inspect`, do not require launching the Medivance Electron app or connecting to a database.

Runtime/UI checks do require the Medivance named test instance workflow:

```bash
cd /home/lazydino/dev/medivance
bun dev:stop <instance-name> 2>/dev/null || true
PATH="$PWD/node_modules/.bin:$PATH" nohup bun scripts/dev-cli.ts --test --instance <instance-name> > /tmp/medivance-<instance-name>-test.log 2>&1 &
bun dev:inspect <instance-name>
```

The inspect output must show the test environment before behavior is judged or reported as ready.

Framework sync and host execution must be sequential. Do not run `lazy-sync` and the host validation command in the same parallel batch, because the validation can race the sync and execute stale or missing host files. First sync, wait for success, then run the host command.

When sync seed-merge semantics preserve host-owned validation registries or test-strategy records, deployment convergence must preserve source-exact protected actions/phrases while retaining host-specific content. After such convergence, run one serial host full regression before announcing all-clear. A scoped static check proves only the edited files parse; it does not prove the installed host satisfies framework self-test fixtures.

Medivance product work is outside the rollback boundary of lazy-harness deployment. If a synchronized harness snapshot fails validation, stop and preserve the current product branch and product working tree. Any proposed rollback must name only the lazy-harness-managed files or transport state it would restore; the word "Medivance rollback" must never imply a repository, branch, or product-code rollback.

## Do not

- Do not launch an unnamed/default Medivance dev app for runtime dogfood.
- Do not reuse an already-running original instance when UI/runtime validation matters.
- Do not use local/prod DB when the user expects test DB.
- Do not judge UI persistence/runtime behavior until stale instances have been stopped and the named `--test` instance is inspected.
- Do not parallelize source-to-Medivance sync with the command that validates the synced framework feature.
- Do not reset, switch, revert, clean, or otherwise roll back the Medivance product branch or product working tree as part of framework sync remediation.

## Implementation map

- Downstream Medivance install (`/home/lazydino/dev/medivance`) — host-owned canonical policy for named dev instances / `--test` launcher and runtime restart before judging backend/main-side behavior.
- Downstream protection boundary — only `.lazy-harness` managed framework files and explicitly managed runtime transport state may be considered for sync repair; Medivance product code, branch state, and unrelated working-tree changes are protected.
- `.lazy-harness/planning/document-resource-ingestion-implementation-plan.md`
  - Marks the first Medivance dogfood as document-only and not a runtime validation.

## Discovery capture

- DDD: none.
- SDD: none.
- BDD: candidate, future runtime/UI dogfood workflows should reference the named test instance flow.
- TDD: none.
- ADR: none.
- SSOT: updated, this record captures the dogfooding boundary in the source repo.
- Planning: updated, document ingestion dogfood note clarified as document-only.

## User correction — 2026-08-03

- The user corrected an ambiguous proposal to "roll back Medivance" while active product work was in progress.
- Confirmed boundary: never roll back the Medivance repository, branch, or product working tree for a lazy-harness deployment failure. Harness remediation must be narrowly scoped and explicitly named.

## 2026-08-18 host validation convergence correction

A post-deployment serial host pre-push exposed two seed-preserved drifts that the earlier scoped checks did not cover: paraphrased `bounded-validation-orchestration` action strings failed source-exact fixtures, and host-owned `tests/test-strategy.xml` lacked the protected `never after every micro-edit` guard. Deployment all-clear was therefore premature. Repair remains limited to host `.lazy-harness` capability/policy/rulebook and test-strategy records, followed by one serial full host regression; product files and branch state remain protected.

## Discovery capture — host validation convergence

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: none because the bounded-validation source contract already defines the protected actions and phrases.
- BDD: none because no product-visible workflow changed.
- TDD: existing bounded-validation self-test fixtures correctly detected both host drifts; no test-contract change is required.
- ADR: none because no architectural trade-off changed.
- SSOT: updated here because deployment readiness now requires source-exact host-owned convergence plus one serial full host regression before all-clear.
- Planning: updated in `.lazy-harness/planning/workflow-churn-reduction-plan.md` with the post-deployment repair status.
