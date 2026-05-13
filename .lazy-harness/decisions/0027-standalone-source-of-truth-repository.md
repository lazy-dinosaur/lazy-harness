# ADR 0027 — Standalone Source-of-Truth Repository

- **Status**: Accepted
- **Date**: 2026-05-13
- **Related**: ADR 0021 (experimental branch and extract strategy), ADR 0024 (AI-first redesign), ADR 0025 (portability single entry point), ADR 0026 (doctor/self-test scope separation)

## Context

`lazy-harness` started inside the Medivance repository as `.lazy-harness/` on the `experimental/lazy-harness` worktree. That worked for dogfooding, but it created a structural conflict:

1. The Medivance host must keep `.lazy-harness/` untracked and ignored so private framework files never leak into the Medivance origin.
2. The framework body itself must track `.lazy-harness/` files as first-class source.
3. Git worktrees share the same common `.git/info/exclude`, so the host ignore rule also affected the framework worktree. `git add .lazy-harness/...` staged tracked files but emitted ignore warnings / non-zero exit behavior.
4. `lazy-harness` is not only an installed folder. It is itself a project and installation system, so it must run its own doctor/self-test in the same host-shaped layout that consumers receive.

During extraction, stripping the `.lazy-harness/` path prefix was rejected: it broke the established contract used by `doctor.py`, `self-test.py`, hooks, and CLI commands. The correct standalone shape is a host-shaped repository:

```text
~/dev/lazy-harness/
  package.json
  tests/lazy-harness/...
  .lazy-harness/
    scripts/
    hooks/
    decisions/
    manifests/
    AGENTS.md
```

## Decision

`~/dev/lazy-harness` is now the **canonical framework source of truth**.

- Framework development happens in `~/dev/lazy-harness`.
- The actual installed framework body remains under `.lazy-harness/` inside that repository.
- Dogfooding hosts, including Medivance, receive an installed copy via `lazy-sync` / `lazy-init`.
- Direct framework edits in `~/dev/medivance/.lazy-harness` are not source-of-truth changes. They must be promoted back to `~/dev/lazy-harness` or discarded.
- `~/dev/medivance.experimental-lazy-harness` is legacy extraction scaffolding, not the development base.

The source extraction must preserve these paths:

```text
.lazy-harness/
tests/lazy-harness/
package.json
```

The first two are framework-owned; `package.json` is the minimal standalone dev/test harness for the framework repository.

## Consequences

### Positive

- Git ignore conflict is removed. In `~/dev/lazy-harness`, `.lazy-harness/` is tracked normally and `git add .lazy-harness/...` exits cleanly.
- The framework can self-host its checks:

```bash
cd ~/dev/lazy-harness
python3 .lazy-harness/scripts/doctor.py --profile smoke
.lazy-harness/scripts/self-test.py
```

- Host sync becomes explicit:

```bash
cd ~/dev/medivance
bun ~/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts \
  --from ~/dev/lazy-harness \
  --target ~/dev/medivance \
  --force
.lazy-harness/bin/lazy test
```

### Negative / Trade-offs

- Existing commit SHAs were rewritten by extraction. Historical framework commits are preserved semantically, but SHAs differ from the Medivance worktree branch.
- `state/synced-from-commit` in existing hosts will show divergent history once, requiring `lazy-sync --force` for the first transition.
- User-level `~/.local/bin/lazy` launcher remains deferred to packaging. The source-of-truth repository only owns the per-host `.lazy-harness/bin/lazy` dispatcher.

## Validation

Completed on 2026-05-13:

```text
~/dev/lazy-harness:
  lazy-harness self-test ok (scope=framework, ran=20, skipped=0)

~/dev/medivance after sync from ~/dev/lazy-harness:
  lazy-harness self-test ok (scope=host, ran=10, skipped=10)
```

Medivance `.lazy-harness/` remained git-clean after sync because it is excluded from the host repository.
