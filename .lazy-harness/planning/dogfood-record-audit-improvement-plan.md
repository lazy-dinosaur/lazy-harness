# Dogfood Record Audit Improvement Plan

Status: active
Date: 2026-05-21
Source: Medivance dogfood record audit

## Context

Medivance dogfooding showed that lazy-harness records are accumulating, but the quality signals were spread across manual shell snippets:

- host-owned/changed record counts
- layer file distribution
- Project Profile `needs-interview` fields
- JSONL line/parse counts
- graph hygiene signals
- log volume
- recent record files

The user approved turning these dogfood improvement candidates into framework improvements and keeping the source plus Medivance host updated.

## Plan

1. Implement `record-audit` read-only CLI.
2. Split Project Profile artifact completeness from answer completeness in audit output.
3. Surface graph hygiene warnings for missing and comma-joined paths.
4. Keep log compaction as a later improvement; the first slice reports log volume only.
5. Sync to Medivance and dogfood with real host records.

## Current slice

- `.lazy-harness/scripts/record-audit.ts`
- `.lazy-harness/bin/lazy record-audit`
- `.lazy-harness/spec/platform/record-audit.md`
- self-test coverage in `.lazy-harness/scripts/self-test.py`
- Medivance dogfood after sync

## Acceptance criteria

- Source self-test and smoke doctor pass.
- `lazy record-audit --format=json` works through the dispatcher.
- Medivance audit reports host-owned/changed records and Project Profile answer completeness without mutating Medivance records.
- Implementation graph records the new CLI and self-test protection.

## Follow-up backlog

- Add explicit graph repair or graph lint command.
- Add log summary/rollup or compaction view.
- Consider a quality score once enough audits are available.

## 2026-05-21 Medivance dogfood result

After source commit `8585136`, synced framework to `/home/lazydino/dev/medivance` with `lazy-sync --force`.

Validation:

- `python3 .lazy-harness/scripts/doctor.py --profile smoke --scope host` passed in Medivance.
- `.lazy-harness/bin/lazy record-audit --format=json --source ~/dev/lazy-harness --recent=8` passed in Medivance.

Observed audit summary:

- Total `.lazy-harness` files: 145.
- Host-owned/changed records: 116 (`unique=99`, `changed=17`, `same_as_source=21`).
- Project Profile: `artifactsComplete=true`, `answersComplete=false`, `needsInterviewFields=26`.
- Graph: `rows=138`, `invalidRows=0`, `missingPaths=22`, `commaJoinedPaths=1`.
- JSONL parseability: all inspected knowledge/log JSONL files had `invalid=0`.
- Log volume: `actions=719`, `validations=955`, `route-decisions=100`, `route-telemetry-debug=144`, `skipped=5`.

Dogfood conclusion:

- The new CLI replaces the previous manual shell audit with a single reproducible dashboard.
- It also confirms the next two improvement slices: Project Profile answer fill UX and graph hygiene/lint.

## 2026-05-21 follow-up implementation results

Project Profile completeness split:

- Implemented `summary.artifactsComplete`, `summary.answersComplete`, `summary.needsInterviewFields`, and `summary.confirmedFields` in `project-profile inspect`.
- Legacy `summary.complete` now follows answer completeness, so `present=5` no longer implies the profile is complete when `status="needs-interview"` fields remain.
- Source self-test and smoke doctor passed before commit `fabc35a`.

Graph hygiene lint:

- Implemented `.lazy-harness/scripts/graph-hygiene.ts` and `.lazy-harness/bin/lazy graph-hygiene`.
- Added `--fail-on-issues` for optional non-zero lint enforcement while keeping default mode report-only.
- Fixed one source graph comma-joined path by converting it to a path array.
- Source `lazy graph-hygiene --format=json` reported `issues=0` before commit `5c8fca2`.
- Source self-test and smoke doctor passed.

Host sync after push:

- Pushed source through `5c8fca2` to origin `main`.
- Synced `/home/lazydino/dev/medivance` to `5c8fca2`; host smoke doctor passed.
  - `record-audit`: `hostOwnedOrChanged=120`, `answersComplete=false`, `needsInterviewFields=26`, `graphMissingPaths=22`, `commaJoinedPaths=0`.
  - `graph-hygiene`: `rows=141`, `invalidRows=0`, `duplicateIds=0`, `commaJoinedPaths=0`, `missingPaths=32`.
- Synced `/home/lazydino/dev/medivance-pwa` to `5c8fca2`; host smoke doctor passed.
  - `record-audit`: `hostOwnedOrChanged=28`, `answersComplete=false`, `needsInterviewFields=0`, `graphMissingPaths=22`, `commaJoinedPaths=0`.
  - `graph-hygiene`: `rows=141`, `invalidRows=0`, `duplicateIds=0`, `commaJoinedPaths=0`, `missingPaths=31`.

Next dogfood insight:

- Graph syntax/id/path-shape hygiene is now clean in source, but host copies still report missing paths because framework graph records reference source-only files not installed into hosts. The next graph improvement should distinguish framework-source paths from host-owned paths or add an ownership/scope field before treating host missing paths as actionable errors.
