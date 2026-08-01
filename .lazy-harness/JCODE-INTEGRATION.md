# Jcode Integration Guide — Historical Directory-Bridge Design

Status: superseded by `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md` and `.lazy-harness/spec/platform/jcode-agent-adapter.md`.

The generated `.jcode` wiring described below is retained only as decision history and must not be restored. Current Jcode uses official lifecycle hooks through:

```bash
.lazy-harness/bin/lazy jcode install      # install hooks + trust current root
.lazy-harness/bin/lazy jcode trust        # trust another lazy root once
.lazy-harness/bin/lazy jcode untrust      # revoke one root
.lazy-harness/bin/lazy jcode trusted-roots
.lazy-harness/bin/lazy jcode doctor
.lazy-harness/bin/lazy jcode smoke
.lazy-harness/bin/lazy jcode remove
```

The adapter is installed explicitly once and executes repository lifecycle scripts only for exact roots in the user-owned trusted-root registry. `install` trusts the current root; each new lazy root needs one `lazy jcode trust`. Marker-only and ordinary projects no-op. Canonical policy remains in `.lazy-harness` records.

## Archived design note (non-actionable)

Before ADR 0050, Lazy-Harness generated project-local `.jcode/**` policy, prompt, skill, and hook files. ADR 0050 removed that directory bridge; ADR 0056 later restored Jcode support only through official global lifecycle hooks plus explicit trusted-root registration.

Do not follow or reconstruct the former setup from repository history. In particular, do not generate `.jcode/hooks`, `.jcode/harness`, `.jcode/skills`, or project-owned policy copies. Use the current commands above and the canonical contracts:

- `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
- `.lazy-harness/spec/platform/jcode-agent-adapter.md`
- `.lazy-harness/tests/jcode-agent-adapter.md`
