# Lazy-Harness Pi Package

Pi Coding Agent package for lazy-harness prompt/runtime lifecycle integration.

## Install locally into a project

```bash
pi install -l /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --approve
```

## One-run smoke

```bash
pi -e /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --help
```

## What it wires

- `before_agent_start` injects the lazy-harness record-first reminder by reusing `.lazy-harness/hooks/lifecycle/on-message-received.sh` when available.
- `tool_call` bridges Pi tool payloads into `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` and blocks only when the generic search/read evidence guard denies.
- `tool_result` records recent read/search/tool evidence for the next guard invocation.
- Commands: `/lazy-map`, `/lazy-doctor`, `/lazy-test`, `/lazy-sync`, `/lazy-update`.

## Trust boundary

Pi extensions run with project extension permissions. Install only in projects where you trust the checked-out lazy-harness source and the host `.lazy-harness` directory.
