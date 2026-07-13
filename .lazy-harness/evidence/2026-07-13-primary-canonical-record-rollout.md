# Evidence: Primary canonical record rollout + Medivance samples

## Scope

This capsule covers the user-approved `guard → two-sample cleanup → deploy → 7-day dogfood` work unit:

- framework-global `primary-canonical-record` recommend policy and four-row TDD completeness protection;
- current-rule reconciliation of Medivance `sheet-treatment-document-option`;
- consolidation of the Medivance reservation time-step SDD/BDD/SSOT triplicate to one SSOT primary narrative;
- scoped framework source commit/push and Category A rollout to all known dogfood hosts: Medivance, Medivance PWA, and Medivance Homepage.

Out of scope: application behavior changes, database work, product releases, bulk host-record rewrites, conflict-journal dedupe, and guided legacy graph migration.

## Environment

- Date: 2026-07-13
- Framework source: `/home/lazydino/dev/lazy-harness`, branch `main`, HEAD `81afe2f3fbb9d0cc517b4bca876908586c781345`
- Dogfood hosts: `/home/lazydino/dev/medivance`, `/home/lazydino/dev/medivance-pwa`, `/home/lazydino/dev/medivance-homepage`
- Medivance `.lazy-harness/` is host-local/ignored; sync and current-size evidence is not a product git diff.
- Sync source was an isolated detached worktree carrying only this rollout's framework diff. Host knowledge seeds were rebased to the current Medivance graph/candidate stores so the user-selected conflict-free sync did not append known stable conflicts.

## Commands

Framework source:

```bash
.lazy-harness/bin/lazy policy audit --format=json
.lazy-harness/bin/lazy rules audit --strict --format=json
.lazy-harness/bin/lazy record-lint --format=json
.lazy-harness/bin/lazy graph-hygiene --format=json
.lazy-harness/bin/lazy test --scope framework --light
.lazy-harness/bin/lazy test --scope framework
```

Downstream sync/dogfood:

```bash
bun <isolated-source>/.lazy-harness/scripts/lazy-sync.ts \
  --from <isolated-source> \
  --target /home/lazydino/dev/medivance \
  --force --dry-run

bun <isolated-source>/.lazy-harness/scripts/lazy-sync.ts \
  --from <isolated-source> \
  --target /home/lazydino/dev/medivance \
  --force

cd /home/lazydino/dev/medivance
bun run test:run \
  tests/integration/COMMIT-sheet-modal-treatment-document-disabled.test.ts \
  tests/integration/COMMIT-appointment-reservation-time-step-10min.test.ts
.lazy-harness/bin/lazy record-lint --format=json
.lazy-harness/bin/lazy policy audit --format=json
.lazy-harness/bin/lazy graph-hygiene --format=json
.lazy-harness/bin/lazy graph-hygiene --migration-plan --format=json
.lazy-harness/bin/lazy test --scope host
```

Manual/source inspection included the current SheetModal/SheetEditForm always-true payloads, the backend sheet/template gates, reservation time constants, both focused Vitest guards, map overview, and concrete record drill-downs.

## Results

- Framework full self-test: `ran=84, skipped=0`, pass.
- Framework policy/rules/record audits: clean; generated rulebook matched the registry.
- First Medivance sync: 16 managed updates, 0 missing.
  - graph rows: `1294 → 1296` (the two new rollout ids exactly once);
  - graph conflict journal: stayed `20,984` lines;
  - candidates: stayed `90` lines.
- A normal seed simulation would have added the same 59 known graph conflicts again; the user selected conflict-free selective seed sync instead.
- Sheet sample: code/test/ADR-backed 2026-07-08 rule became the single current SSOT; stale 2026-05-21 active-toggle prose was retained only as decision history.
- Reservation time-step sample: SSOT remains active/full; SDD and BDD are deprecated superseded pointers. The four edited sample files are net 25 lines smaller; no source/test/runtime edge changed.
- Focused Vitest: 2 files passed, 7 tests passed.
- Initial host full test exposed a nested-sync fixture bug: a preserved Medivance-only policy cited a host-owned source outside the framework manifest. The user selected a portable framework-policy subset audit. The fixture now preserves that host-only policy but audits only framework seed + fixture policies.
- Framework full self-test after that fix: `ran=84, skipped=0`, pass.
- Resync: 5 managed updates, no knowledge-store delta.
- Final Medivance host self-test: `ran=57, skipped=27`, pass.
- Final Medivance record lint: 0 issues, 0 advisories.
- Final Medivance policy audit: pass.
- Final Medivance graph hygiene: `ok=true`, 1,296 rows; 5 pre-existing missing artifact-path warnings.
- Medivance migration probe remains read-only/out of scope: 123 legacy-schema rows, 0 removed-framework refs, 97 record-body Jcode mentions.
- Deployment extension: user clarified that dirty/local dogfood state is not completion; source commit/push plus all-known-host sync/validation is required. Final deployment results are appended after those gates complete.

## Interpretation

The rollout is mechanically active at recommend/advisory level and the two samples now demonstrate one primary current narrative without changing product behavior. The sync avoided known conflict-journal write amplification while still installing both new graph ids and all managed framework assets.

This proves framework and immediate Medivance host consistency for the slice. It does not yet prove the 7-day success targets. Dogfood measurement begins from this 2026-07-13 baseline; median primary records per logical work unit, extra-layer reasons, repeated validation transcript, and touched-record contradictions must be re-audited after seven days.

Confidence: high for the validated framework/host slice; pending for the seven-day behavioral outcome.

## Reproduce

1. Read `.lazy-harness/planning/workflow-churn-reduction-plan.md` and the related policy/record contracts below.
2. Run the framework audit and full test commands above.
3. In Medivance, drill down the sheet-option and reservation time-step records with `lazy map`.
4. Run the two focused Vitest files and `.lazy-harness/bin/lazy test --scope host`.
5. Confirm the time-step SDD/BDD map as deprecated pointers and SSOT as active.
6. Confirm Medivance graph ids `kg_primary_canonical_record_policy_20260713` and `kg_primary_canonical_record_broker_20260713` occur exactly once.
7. Do not run graph migration without the guided, batch-scoped user approval flow.

## Related records

- `.lazy-harness/planning/workflow-churn-reduction-plan.md`
- `.lazy-harness/decisions/0033-layer-completeness-gate.md`
- `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md`
- `.lazy-harness/spec/platform/record-write-update-policy.md`
- `.lazy-harness/spec/platform/layer-completeness-gate.md`
- `.lazy-harness/spec/platform/record-decision-broker.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- `/home/lazydino/dev/medivance/.lazy-harness/ssot/sheet-treatment-document-option.md`
- `/home/lazydino/dev/medivance/.lazy-harness/ssot/appointment-reservation-time-step.md`

## Retention / privacy

Keep this summarized capsule while the 7-day dogfood measurement is active and for later rollout comparison. It contains no credentials, tokens, patient data, raw transcripts, raw assistant responses, or product database contents. Temporary sync worktrees and simulation targets were removed after validation; large command logs remain transient under `/tmp`.
