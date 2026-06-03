# logs

JSONL logs: actions, decisions, questions, validations, route telemetry. Append-only.

## Route telemetry

`response.completed` automatically appends one non-canonical workflow-compression telemetry entry per Jcode message when `last_user_message` is present. `lazy route --log` can also append explicit route probes. Both write to:

```text
$LAZY_SHARED_ROOT/logs/route-decisions.jsonl
```

`lazy route-summary --format=md` summarizes route counts, gate ratios, confidence ratios, and recommendations for deciding whether AGENTS compression, profiles, or heuristic adjustments are needed.

Telemetry stores stable message/message-id hashes and route axes, not raw user messages. It never closes gates and never satisfies canonical record obligations. Duplicate lifecycle calls for the same `message_id` are deduped by `messageIdHash`.

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
