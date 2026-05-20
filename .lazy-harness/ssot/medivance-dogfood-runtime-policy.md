# SSOT — Medivance dogfooding runtime policy

Status: accepted
Date: 2026-05-20
Layer: SSOT
Scope: lazy-harness source repo dogfooding against `/home/lazydino/dev/medivance`
Source records in downstream host:
- `/home/lazydino/dev/medivance/.lazy-harness/ssot/named-dev-instance-workflow.md`
- `/home/lazydino/dev/medivance/.lazy-harness/ssot/dev-runtime-restart-policy.md`
- `/home/lazydino/dev/medivance/.lazy-harness/ssot/dev-instance-pr-workaround.md`

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

## Do not

- Do not launch an unnamed/default Medivance dev app for runtime dogfood.
- Do not reuse an already-running original instance when UI/runtime validation matters.
- Do not use local/prod DB when the user expects test DB.
- Do not judge UI persistence/runtime behavior until stale instances have been stopped and the named `--test` instance is inspected.

## Implementation map

- `/home/lazydino/dev/medivance/.lazy-harness/ssot/named-dev-instance-workflow.md`
  - Downstream canonical policy for named dev instances and `--test` launcher.
- `/home/lazydino/dev/medivance/.lazy-harness/ssot/dev-runtime-restart-policy.md`
  - Downstream canonical policy for restart before judging backend/main-side runtime behavior.
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
