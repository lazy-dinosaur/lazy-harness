# logs

JSONL logs: actions, decisions, questions, validations, and historical/deprecated route telemetry. Append-only where still produced.

## Route telemetry (deprecated)

Route telemetry from the old task-router experiment is deprecated. Lifecycle hooks must not classify raw user text into route axes or append automatic route decisions. Historical `$LAZY_SHARED_ROOT/logs/route-decisions.jsonl` files may exist in old runtimes but are not current framework behavior.

## Hook timing telemetry

`response.completed` also appends measurement-only timing rows to:

```text
$LAZY_RUNTIME_ROOT/logs/hook-timings.jsonl
```

Timing rows contain component names, durations, exit codes, and emitted flags only. They do not store raw user messages or payload bodies. Use:

```bash
.lazy-harness/bin/lazy hook-timings --format=md
```

This is Phase 0 measurement data for performance optimization. It must not be used to skip gates until later conservative fast-path parity tests exist.

## Trigger to fill

Auto by hooks.

## Status

- Empty is valid (Principle #10 Empty-Container Tolerance)
- Will be filled when triggers fire (Principle #6 Trigger-Based Growth)
- Auto-audited on update (Principle #1.2 Drafting and Auditing)

## 2026-06-04 timing summary filters

`lazy hook-timings` supports reproducible dogfood review options:

```bash
.lazy-harness/bin/lazy hook-timings --format=md --since 2026-06-04T10:06:00Z
.lazy-harness/bin/lazy hook-timings --format=md --all-sessions --since 2026-06-04T10:06:00Z
```

`--since` filters rows by `ts` / `timestamp`. `--all-sessions` aggregates session-scoped runtime logs under `.git/lazy-harness/runtime/*/logs/hook-timings.jsonl` plus the selected/default log. Timing remains measurement-only and must not be used to skip gates.
