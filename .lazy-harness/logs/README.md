# logs

JSONL logs: actions, decisions, questions, validations, route telemetry. Append-only.

## Route telemetry

`lazy route --log` appends non-canonical workflow-compression telemetry to:

```text
.lazy-harness/logs/route-decisions.jsonl
```

`lazy route-summary --format=md` summarizes route counts, gate ratios, confidence ratios, and recommendations for deciding whether AGENTS compression, profiles, or heuristic adjustments are needed.

Telemetry stores a stable message hash and route axes, not raw user messages. It never closes gates and never satisfies canonical record obligations.

## Trigger to fill

Auto by hooks.

## Status

- Empty is valid (Principle #10 Empty-Container Tolerance)
- Will be filled when triggers fire (Principle #6 Trigger-Based Growth)
- Auto-audited on update (Principle #1.2 Drafting and Auditing)
