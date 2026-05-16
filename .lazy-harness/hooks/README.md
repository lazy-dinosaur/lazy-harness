# hooks

Lazy-harness hook surface. Shell scripts are thin wrappers; durable logic lives in framework-owned scripts under `.lazy-harness/scripts/` and `.lazy-harness/triggers/`.

## Current hook groups

| Group | Entry point | Purpose |
|---|---|---|
| Git pre-commit | `.lazy-harness/hooks/pre-commit-guard.sh` | Prevent private framework files from leaking on non-framework branches. |
| Git post-commit | `.lazy-harness/hooks/post-commit.sh` | Append action log metadata and regression hints. |
| Git pre-push | `.lazy-harness/hooks/pre-push.sh` | Run `.lazy-harness/bin/lazy test` before push and enforce branch leak policy. |
| Scheduled/manual | `.lazy-harness/hooks/weekly-snapshot.sh` | Backup/snapshot support. |
| Jcode response lifecycle | `.lazy-harness/hooks/lifecycle/on-response-completed.sh` | Response-end force gates and continuation reminders. |
| Jcode disconnect lifecycle | `.lazy-harness/hooks/lifecycle/on-client-disconnect.sh` | Session cleanup/snapshot hook. |

## `response.completed` helper chain

`on-response-completed.sh` currently runs these helpers in order:

1. `check-handoff-stale.sh`
2. `check-ddd-trigger.sh`
3. `check-sdd-trigger.sh`
4. `check-bdd-trigger.sh`
5. `check-ssot-trigger.sh`
6. `check-tdd-cross-verify.sh`
7. `check-affected-tests.sh`
8. `check-aftershock-reanalysis.sh`
9. `check-fix-regression.sh`
10. `check-adr-sync.sh`

A helper should stay silent when clean. If it emits a force-gate message, jcode injects that reason into a later continuation turn and the agent must handle it.

## Audit/read-only mode

Read-only audits should avoid lifecycle side effects:

```bash
touch .lazy-harness/.hooks-disabled
# run read-only audit commands
rm -f .lazy-harness/.hooks-disabled
```

or run helpers with dry-run semantics when available. This prevents response lifecycle hooks from mutating documentation during nominally read-only audits.

## Status

- Current operational gate: `.lazy-harness/bin/lazy test` and `.lazy-harness/bin/lazy doctor --profile smoke`.
- Jcode is a wrapper/tooling layer; framework-owned checks live in `.lazy-harness` (ADR 0022).
- Empty-container tolerance still applies to future hook registries, but this README is no longer intentionally empty.
