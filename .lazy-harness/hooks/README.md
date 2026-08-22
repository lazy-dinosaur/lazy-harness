# hooks

Lazy-harness hook surface. Shell scripts are thin wrappers; durable logic lives in framework-owned scripts under `.lazy-harness/scripts/` and `.lazy-harness/triggers/`.

## Current hook groups

| Group | Entry point | Purpose |
|---|---|---|
| Git pre-commit | `.lazy-harness/hooks/pre-commit-guard.sh` | Prevent private framework files from leaking on host branches and run `.lazy-harness/bin/lazy test --light` as the commit-time blocking gate. |
| Git post-commit | `.lazy-harness/hooks/post-commit.sh` | Append action log metadata and regression hints. |
| Git pre-push | `.lazy-harness/hooks/pre-push.sh` | Run full `.lazy-harness/bin/lazy test` before push and enforce branch leak policy. |
| Scheduled/manual | `.lazy-harness/hooks/weekly-snapshot.sh` | Backup/snapshot support. |
| Runtime response lifecycle | `.lazy-harness/hooks/lifecycle/on-response-completed.sh` | Response-end audits and bounded continuation reminders transported by Pi/OMP. |

## Development-time vs commit-time enforcement

Edit/write/multiedit hooks are not registered as blocking gates by default.
Agents use `lazy check` during mutation loops, focused checks when behavior changes,
and one `lazy validate --plan standard` after the final mutation. Direct `lazy test`
is reserved for explicit fresh full regression or commit/push/release boundaries.
Git pre-commit runs `lazy test --light`; pre-push runs full `lazy test`. Audited
independent self-test checks use bounded process phases by default, while fixed-path
checks remain serial and `--jobs=1` provides the serial fallback.

CLI helpers are explicit tools only. Lifecycle hooks must not run static
user-text route classifiers, route telemetry, or context-delivery backends to
pre-decide intent, importance, required reads, gates, record-write need, risk,
or next action. Those judgments stay with the LLM/searcher after root-bound
record/source/test evidence (SSOT cli-tool-boundary; ADR 0041).

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

A helper should stay silent when clean. If it emits a force-gate message, the Pi/OMP adapter may deliver one bounded follow-up so the agent handles it.

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
- Current boundary: CLI helpers are explicit tools only; no automatic route telemetry.
- Pi is the stable primary adapter; OMP remains Experimental. Framework-owned checks live in `.lazy-harness` (ADR 0022/0059).
- Empty-container tolerance still applies to future hook registries, but this README is no longer intentionally empty.
