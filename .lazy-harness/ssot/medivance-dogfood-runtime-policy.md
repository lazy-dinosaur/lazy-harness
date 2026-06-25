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
- Applies when:
  - dogfooding lazy-harness framework changes from this source repo against the Medivance downstream host
  - deciding whether a check is document-only or needs runtime/UI validation
  - judging Medivance UI persistence or runtime behavior as ready
- Must:
  - run document-only checks (e.g. ingestion `--mode inspect`) without launching the Electron app or a database
  - use the Medivance named `--test` instance workflow and confirm inspect shows the test environment before judging runtime/UI
  - run framework sync first, wait for success, then run host validation; never the same parallel batch
- Must not:
  - launch an unnamed/default dev app, reuse a running original instance, or use local/prod DB for runtime dogfood
  - parallelize source-to-Medivance sync with the command that validates the synced feature
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

## Do not

- Do not launch an unnamed/default Medivance dev app for runtime dogfood.
- Do not reuse an already-running original instance when UI/runtime validation matters.
- Do not use local/prod DB when the user expects test DB.
- Do not judge UI persistence/runtime behavior until stale instances have been stopped and the named `--test` instance is inspected.
- Do not parallelize source-to-Medivance sync with the command that validates the synced framework feature.

## Implementation map

- Downstream Medivance install (`/home/lazydino/dev/medivance`) — host-owned canonical policy for named dev instances / `--test` launcher and runtime restart before judging backend/main-side behavior.
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
