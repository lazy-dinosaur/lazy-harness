# Planning — Jcode Multi-Project Unified Activation Rollout

Status: implementation-complete
Date: 2026-08-02
Layer: Planning
Primary ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
Related SDD: `.lazy-harness/spec/platform/jcode-agent-adapter.md`
Related TDD: `.lazy-harness/tests/jcode-agent-adapter.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: transient-plan
- Confidence: high
- Aliases:
  - 다른 프로젝트 Jcode 배포
  - 통합 agent activation
  - lazy init Pi OMP Jcode
  - multi-project lazy-patched rollout
- Surface terms:
  - lazy agent activate
  - lazy init
  - lazy sync
  - trusted roots
  - lazy-patched pointer
- Applies when:
  - implementing the user-confirmed option A for distributing Jcode activation to lazy-harness host projects
  - deciding whether init, sync, or activation may create Jcode trust
- Must:
  - use one explicit unified project activation path for Pi, OMP, and Jcode
  - allow explicit `lazy init --target` to activate the selected new project
  - keep `lazy sync` from silently trusting an untrusted project
  - reuse one machine-global lazy-patched Jcode candidate across projects
  - preserve reversible TOML-safe trust and local transport behavior
  - atomically make the normal `jcode` launcher use the dedicated lazy-patched pointer after validation
- Must not:
  - rebuild or copy the Jcode binary into every project
  - alter official stable/current while promoting the explicitly selected normal launcher
  - duplicate canonical project policy in `.jcode`, Pi, or OMP transport files
- Record completion:
  - update phase state after launcher selection, execution approval, implementation, and final validation
- Related records:
  - `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
  - `.lazy-harness/decisions/0057-jcode-lazy-patched-channel.md`
  - `.lazy-harness/spec/platform/jcode-agent-adapter.md`
  - `.lazy-harness/tests/jcode-agent-adapter.md`

## Confirmed requirements

User-confirmed option A on 2026-08-02:

1. Lazy-harness is the distribution and activation mechanism for other projects.
2. `lazy agent activate --target <root>` becomes the unified explicit activation/repair command for Pi, OMP, and Jcode.
3. `lazy init --target <root>` may perform unified activation for the explicitly selected new project.
4. `lazy sync` distributes framework updates and may check or repair an already trusted Jcode activation, but it must not create trust for an untrusted root.
5. One machine-global lazy-patched Jcode candidate is shared by all activated projects; projects keep only trust and reversible transport state.
6. Existing Pi/OMP behavior, unrelated user TOML, official Jcode stable/current pointers, and ordinary untrusted projects remain unaffected.
7. User-confirmed launcher option A: normal `jcode` resolves through `~/.jcode/builds/lazy-patched/jcode`; promotion is atomic, preserves the exact prior launcher target, and leaves official stable/current unchanged.

## Proposed implementation plan

Execution approved by the user on 2026-08-02. Source implementation, focused regression, independent review/remediation, current-root activation, real launcher promotion, and final standard validation are complete.

### Phase 1 — Unified activation transaction

1. Refactor the current Pi/OMP-only `agent-activate.ts` flow into a reusable activation transaction.
2. Reuse Jcode package/trust/local-config functions directly instead of duplicating TOML or trust logic.
3. Aggregate Pi, OMP, and Jcode results in Markdown and JSON output.
4. Preserve dry-run no-mutation, idempotency, user-owned content, and rollback on partial failure.

### Phase 2 — Init and sync integration

1. Make successful explicit `lazy init --target` call the unified activation flow unless an explicit skip flag is supplied.
2. Keep `lazy sync` non-authorizing: detect trust first, repair/check only trusted roots, and print the exact activation command for untrusted roots.
3. Keep framework copying and host institutional memory ownership unchanged.

### Phase 3 — Machine channel selection

1. Verify that the dedicated pointer resolves to the completed candidate and that candidate provenance, executable mode, version hash, and doctor output match the recorded build.
2. Capture the exact current type and target of `~/.local/bin/jcode` for rollback.
3. Atomically repoint only `~/.local/bin/jcode` to `~/.jcode/builds/lazy-patched/jcode`.
4. Verify `jcode version --json`, offline help, trusted-root doctor, and ordinary-root silence through the normal launcher.
5. On any failure, atomically restore the exact prior launcher state; never change official stable/current.

### Phase 4 — Regression and rollout

1. Add focused fixtures for unified activation, init activation, trusted sync repair, untrusted sync no-trust, dry-run, idempotency, rollback, TOML preservation, and Pi/OMP non-regression.
2. Exercise one temporary new host and one existing trusted host.
3. Run `.lazy-harness/bin/lazy check` during edits, focused tests, and one final `.lazy-harness/bin/lazy validate --plan standard` after the final mutation.
4. Publish an existing-project migration command and status report.

## Confirmed launcher decision

User-confirmed option A on 2026-08-02: promote the normal `jcode` launcher to the dedicated lazy-patched pointer while preserving official stable/current and exact rollback. Source implementation and machine mutation still require explicit execution approval of this complete plan.

## Stop conditions

- Stop if unified activation requires rewriting unrelated Jcode TOML or Pi/OMP user content.
- Stop if sync cannot distinguish trusted from untrusted roots without creating trust.
- Stop if launcher selection would silently replace official stable/current or remove rollback access.
- Stop if a per-project Jcode binary copy becomes necessary.

## Execution evidence — 2026-08-02

- `lazy agent activate` now installs/repairs global hooks against the stable synced framework source, manages exact-root trust/local transport, emits structural results only, and rolls Pi/OMP state back on Jcode conflict.
- `lazy init` auto-activates an explicit new target unless `--skip-agent-activation`; `lazy sync` repairs only trusted roots and leaves its prior marker intact on repair failure.
- Focused Pi/OMP/Jcode fixtures, Bun builds, Python compilation, diff checks, record lint, and two independent review rounds passed; the second review reported no remaining P1/P2 findings.
- `~/.local/bin/jcode` was atomically promoted from `~/.jcode/builds/current/jcode` to `~/.jcode/builds/lazy-patched/jcode` after exact candidate digest/provenance/version validation.
- The normal launcher reports git hash `04092f6de`; trusted-root doctor and offline help pass. Stable/current pointers remain unchanged and mode-0600 rollback state preserves the exact prior launcher target.
- No server reload, provider request, push, rebase, or per-project binary copy occurred.

## Existing-host activation evidence — 2026-08-03

- The normal launcher was confirmed promoted and running the later lazy-patched build `v0.64.141-dev (daf9d3d90)` with all eight managed hooks present.
- Medivance initially reported `targetTrusted: false` and `localPromptActive: false`; therefore the exact-trusted-root adapter intentionally no-op'd even though the machine-level launcher and hooks were installed. This explained the observed plain-text option output and ungoverned auto-poke continuation without treating it as a missing Jcode binary deployment.
- After explicit `lazy agent activate --target /home/lazydino/dev/medivance`, the user confirmed that Jcode now appears to behave normally.
- This is existing-host migration evidence for the intentional rule that `lazy sync` never creates trust: an existing untrusted host needs one explicit activation, while `lazy init` may activate its explicit new target automatically.

## Runtime-neutral progress deployment evidence — 2026-08-03

- The trusted-root registry contained the lazy-harness source root and one downstream activated project, `/home/lazydino/dev/medivance`; therefore Medivance was the complete downstream deployment set for this machine.
- Runtime-neutral progress commit `f08b1c92b901ae9c247218528ff5cfe222d04c71` was synchronized to Medivance from a clean detached source snapshot, with the marker restored to canonical source root `/home/lazydino/dev/lazy-harness`.
- Initial host standard validation exposed two missing harness coherence dependencies, not product failures: the committed host snapshot lacked the matching operating-rule catalog implementation and manifest entries for the already-present code-organization records/capability.
- A detached Medivance candidate worktree proved a two-file harness-only coherence overlay (`hooks/lifecycle/helpers/operating_rule_catalog.py`, `manifests/init-categories.json`) against the two failing checks plus the bounded-validation progress regression before active application.
- Active Medivance then passed capability registry, on-context catalog, bounded validation progress, Jcode doctor, and final `lazy validate --plan standard`: host self-test `ran=58`, `skipped=28`, exit 0.
- Medivance product state remained untouched throughout: branch `dev`, HEAD `5c4a1db225d2ed3b1b0edd56ce5ffd8672e3061f`, and clean product working tree were unchanged. No product reset, checkout, revert, branch move, runtime launch, or database action occurred.
- The shared machine Jcode launcher remained promoted to the lazy-patched channel and Medivance remained an exact trusted root with all eight hooks active.

## Implementation map

- Planned source seams verified from current source:
  - `.lazy-harness/scripts/agent-activate.ts` — current Pi/OMP project activation; planned unified transaction owner.
  - `.lazy-harness/scripts/lazy-init.ts` — current framework bootstrap; planned explicit post-init activation caller.
  - `.lazy-harness/scripts/lazy-sync.ts` — current framework synchronization; planned trust-aware repair/report caller.
  - `.lazy-harness/scripts/jcode-package.ts` — existing reversible install/trust/doctor operations to reuse.
  - `.lazy-harness/scripts/jcode-local-config.ts` — existing local transport preservation and rollback logic to reuse.
  - `.lazy-harness/scripts/jcode-trust.ts` — existing exact-root trust registry owner to reuse.
  - `.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter` — focused regression entrypoint to extend after approval.
- Flow: explicit init/activate → unified transaction → Pi/OMP transport + Jcode exact-root trust/local transport → trusted runtime auto-application; sync checks trust before any repair.
- Cross-layer links: ADR 0056, SDD Jcode adapter, TDD Jcode adapter.

## Rule placement

- Rule: distribute project activation through lazy-harness while sharing one machine-level Jcode candidate and preserving explicit trust.
- Scope: transient rollout plan derived from a framework-global ADR/SDD amendment.
- Primary durable decision: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`.
- Confirmation: user-confirmed 2026-08-02.

## Discovery capture

- ADR: independent delta recorded in ADR 0056 for unified activation and sync non-authorization.
- SDD: independent contract delta recorded in the Jcode adapter SDD.
- TDD: expected regression expansion identified; update alongside approved implementation.
- BDD: no independent product UI flow.
- DDD: no domain invariant change.
- SSOT: no ownership/config source-of-truth change; existing trust registry and runtime-state ownership remain authoritative.
- Planning: this record owns the pending launcher choice and implementation sequence.
