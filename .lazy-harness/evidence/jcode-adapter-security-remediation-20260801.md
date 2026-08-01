# Evidence: Jcode adapter security remediation

## Scope

Security remediation for the official Jcode thin adapter in the Lazy-Harness source checkout. Covers trusted-root activation, privacy-safe evidence, canonical runtime isolation, lock ownership, bounded post-tool correlation, TOML-safe installation/removal, CLI/docs, and focused fake-runtime regressions. Fresh live Jcode session behavior and the unavailable Pi peer fixture are intentionally outside this capsule's completed claims.

## Environment

- Date: 2026-08-01
- Project: `/home/lazydino/dev/lazy-harness`
- Branch / base commit: `main` / `49691b9b76b3e2c45ea7eba9b56093155afc1614`
- Agent model: `gpt-5.6-sol`
- Jcode: `v0.64.114-dev (0ffe9f484, dirty)`, base `0.64.2`
- Runtime fixtures: temporary Jcode homes, lazy roots, canonical runtime roots, attacker-controlled relative-home registry, URI/path/symlink attacks, stale/live locks, and legal/invalid TOML variants.

## Commands

From the project root:

```bash
bun build .lazy-harness/scripts/jcode-adapter.ts --target=bun --outfile=/tmp/jcode-adapter.js
bun build .lazy-harness/scripts/jcode-package.ts --target=bun --outfile=/tmp/jcode-package.js
bun run typecheck:node
python3 - <<'PY'
import runpy
ns = runpy.run_path('.lazy-harness/scripts/self-test.py')
ns['check_jcode_agent_adapter']()
PY
.lazy-harness/bin/lazy check
.lazy-harness/bin/lazy jcode install --format=json
.lazy-harness/bin/lazy jcode doctor --format=json
.lazy-harness/bin/lazy jcode smoke --format=json
jcode run --no-update --json --tools read <trusted-read-smoke>
jcode run --no-update --json --tools bash <destructive-command-smoke>
jcode run --no-update --json --tool-profile none <ordinary-untrusted-root-smoke>
```

Independent read-only reviews:

- `.pi-subagents/artifacts/1a0cb4ec_reviewer_0_output.md`
- `.pi-subagents/artifacts/3fe69500_reviewer_0_output.md`
- `.pi-subagents/artifacts/167bac86_reviewer_0_output.md`

## Results

- Bun builds and `bun run typecheck:node` passed. Pi Lens standalone TypeScript diagnostics did not load this Bun script set's Node/Bun ambient types and reported 43 environment-level errors; those diagnostics are not treated as a green typecheck claim.
- Focused `check_jcode_agent_adapter` passed after expansion.
- `lazy check` passed on the changed worktree.
- The final narrow independent review reported no blocker, high, or medium findings for canonical path evidence or session-end lock ownership.
- Covered attacks/regressions include relative `JCODE_HOME`, marker-only roots across every hook, two exact trusted roots, URI variants, lexical and symlink escapes, raw command secrets, ambiguous/stale/failed post-tool events, explicit/default runtime roots, ownerless stale locks, live foreign locks, true deny cleanup failure, commented/quoted TOML, CRLF/trailing-byte round trips, dry-run/conflict/invalid TOML, and shell paths containing spaces.
- Global Jcode hooks installed successfully with backup `/home/lazydino/.jcode/config.toml.lazy-harness-backup-2026-08-01T05-07-48-535Z`; doctor reported valid TOML, all six managed hooks, exact current-root trust, no conflicts, and only the documented capability gaps.
- Fresh installed trusted-root sessions returned `JCODE_LIVE_SMOKE_OK` after a real read tool call and blocked `rm -rf /` with `Refusing rm -rf / (destructive root delete)`. Two trusted sessions used distinct mode-`0600` session hashes; bounded state contained only structural/path evidence.
- A fresh Jcode run in an ordinary untrusted directory returned normally while creating no project or trusted-root adapter state.
- The first final-standard attempt reached both bounded steps: `fast-static-check` passed and `full-self-test` exposed a Pi fake-runtime module-resolution defect. Pi was already installed globally; the direct Bun fixture could not resolve peer dependencies from the source checkout.
- The fixture now copies the current extension source beside bounded temporary `SessionManager` and TypeBox stubs. Focused `check_pi_package_layout_and_contract` passes without repository-local or machine-global peer lookup.
- Jcode remediation did not modify the Pi/OMP runtime adapter.

## Interpretation

The previously reported repository-execution, secret-persistence, runtime-path, TOML, lock, correlation, cleanup, and documentation blockers are closed at focused fake-runtime, independent source-review, installed-package, and live Jcode smoke scope. The Pi non-regression fixture is now hermetic and green. This does not establish full Jcode parity: Pi-style context reinjection, bounded turn-end continuation, and native selectable ask remain unsupported/unverified. Final standard validation remains pending.

## Reproduce

1. Run the commands above from `/home/lazydino/dev/lazy-harness`.
2. Inspect `.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter` for generated fixture details.
3. Inspect the three reviewer artifacts for finding progression and final narrow verification.
4. Run the focused Pi fixture, then `.lazy-harness/bin/lazy validate --plan standard` after the final mutation.
5. Re-run the three bounded `jcode run` smoke forms above for trusted read, confirmed pre-tool deny, and ordinary untrusted-root silence.

## Related records

- `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
- `.lazy-harness/spec/platform/jcode-agent-adapter.md`
- `.lazy-harness/tests/jcode-agent-adapter.md`
- `.lazy-harness/planning/jcode-runtime-adapter-pilot.md`
- `.lazy-harness/ssot/harness-enforcement-policy.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`

## Retention / privacy

Keep this capsule with the logical work unit. It contains summarized structural evidence only. Temporary fixture paths, credentials used as synthetic attack strings, raw tool payloads, and raw assistant/session transcripts are not retained here. Reviewer artifacts are local transient evidence and may be pruned after the work unit is committed or otherwise archived.
