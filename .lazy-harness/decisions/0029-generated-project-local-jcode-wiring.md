# ADR 0029 — Generated Project-Local Jcode Wiring

- **Status**: superseded
- **Superseded on**: 2026-06-24
- **Superseded by**: .lazy-harness/decisions/0050-pi-omp-only-runtime.md
- **Date**: 2026-05-13
- **Related**: ADR 0024 (AI-first framework redesign), ADR 0027 (standalone source-of-truth repository), ADR 0028 (progressive knowledge graph backbone)
- **Docs**: `.lazy-harness/JCODE-INTEGRATION.md`, root `README.md`

## Rule digest

- Status: deprecated
- Layer: ADR
- Scope: framework-global
- Applies when:
  - bootstrapping or syncing a host's `.jcode` / Jcode wiring
  - deciding whether a generated config file may be refreshed or is user-owned
  - ensuring `.lazy-harness/AGENTS.md` loads early without duplicate grammar
- Must:
  - generate project-local Jcode wiring from generic public templates during lazy-init/lazy-sync
  - mark generated files; refresh marked files and preserve markerless user-owned files
  - keep `.jcode/harness/05-lazy-harness.md` pointer-only so grammar is not loaded twice
  - generate Jcode wiring by default; `--skip-jcode` is the opt-out
- Must not:
  - ship Lazydino's private `.jcode/` verbatim or overwrite user-owned host customization
- Record completion:
  - Jcode template/marker or sync-repair changes update this ADR and the Jcode wiring self-test
- Related records:
  - `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`
  - `.lazy-harness/decisions/0025-portability-single-entry-point.md`
  - `.lazy-harness/JCODE-INTEGRATION.md`

## Context

> Superseded by ADR 0050 (Pi/OMP-only runtime, 2026-06-24): jcode wiring is decommissioned. This record is preserved as decision history.

Dogfooding showed that relying on a public framework body without project-local Jcode wiring leaves important behavior dormant:

1. `.lazy-harness/AGENTS.md` may exist but not be loaded early enough by Jcode.
2. `.jcode/config.toml`, hooks, harness instructions, and lazy-* skills were missing on newly installed hosts.
3. Public source cannot ship Lazydino's private `.jcode/` directory verbatim, but hosts still need a complete generic Jcode setup.
4. Existing hosts such as Medivance may already have customized `.jcode/*`, so updates must not blindly overwrite user-owned files.

## Decision

`lazy-init` and `lazy-sync` must generate project-local Jcode wiring from public, generic templates by default.

Generated default surface:

- `.jcode/config.toml`
- `.jcode/AGENTS.md`
- root `AGENTS.md` pointing at `.lazy-harness/AGENTS.md`
- `.jcode/harness/05-lazy-harness.md` as pointer-only generated reminder
- `.jcode/harness/10-routing-policy.md`
- `.jcode/harness/20-project-rules.md`
- `.jcode/hooks/check-bash.sh`
- `.jcode/hooks/log-tool.sh`
- `.jcode/skills/lazy-{init,sync,update,doctor,test}/SKILL.md`
- `.jcode/rules/` and `.jcode/monorepo/` directories for M45 private instruction globs

Update policy:

1. `.lazy-harness/*` remains framework-owned and is synced from source.
2. root `AGENTS.md` is the symlink/full-body loader for `.lazy-harness/AGENTS.md`.
3. `.jcode/harness/05-lazy-harness.md` must stay pointer-only when managed, so project-local Jcode harness loading does not duplicate the full lazy-harness grammar already loaded through root `AGENTS.md`.
4. Generated `.jcode/*` files include a generated marker.
5. Files with the marker may be refreshed by future template updates.
6. Files without the marker are treated as user-owned and preserved.
7. `install.sh` generates Jcode wiring by default. `--skip-jcode` is the opt-out.
8. `lazy-update` must invoke the source checkout's latest `lazy-sync.ts` so newly introduced sync behavior applies even to outdated hosts on the first update run.

## Consequences

### Positive

- Fresh hosts receive complete harness behavior without requiring a separate private bootstrap step.
- Public install remains secret-free and generic.
- Existing private host customization is preserved.
- Missing skills/hooks can be repaired by `lazy update --force`.
- M45 private instruction loading becomes the primary behavior path instead of brittle prompt-injection hooks.
- The same lazy-harness grammar is not loaded twice through both root `AGENTS.md` and generated `.jcode/harness/05-lazy-harness.md`.

### Negative / Trade-offs

- The framework now owns a small generic `.jcode` template surface.
- Template refresh must distinguish generated files from user-owned files.
- Existing hosts with old `lazy-update` may require one source-backed update to receive the newest update behavior, but `lazy-sync` can repair them directly.

## Validation

- Fresh temp host install generated `.lazy-harness/` and full `.jcode/` surface.
- Temp host installed with `--skip-jcode` was repaired by `lazy-sync`.
- `medivance-pwa` updated to `9d4d47b` and generated full `.jcode/` surface.
- `dev/medivance` updated to `9d4d47b`, preserved user-owned `.jcode/*`, and added missing `lazy-update` skill.
- Framework `doctor --profile smoke` and `self-test --scope framework` passed after implementation commits.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/scripts/jcode-wiring.ts` — generated project-local Jcode config/hooks/harness/skills templates and repair logic.
  - `.lazy-harness/scripts/lazy-init.ts` — calls `installJcodeWiring` during host bootstrap unless `--skip-jcode`.
  - `.lazy-harness/scripts/lazy-sync.ts` — refreshes/repairs Jcode wiring during sync, including equal-drift fast path.
  - `.lazy-harness/scripts/self-test.py` — Jcode wiring regression tests.
- Key symbols:
  - `installJcodeWiring` (`jcode-wiring.ts`) — main project-local wiring generator/repair entrypoint.
  - `postInitJcodeWiring` (`lazy-init.ts`) — bootstrap integration.
  - `main` (`lazy-sync.ts`) — sync integration and equal-state Jcode wiring check.
  - `check_jcode_wiring_pointer_only`, `check_jcode_wiring_repairs_stale_defaults`, `check_jcode_wiring_message_received_hook`, `check_jcode_dev_hooks_are_nonblocking`, `check_jcode_wiring_bash_safety_only_hook` (`self-test.py`) — executable coverage.
- Flow:
  1. `lazy-init` lays down `.lazy-harness` and then installs generated `.jcode` wiring unless skipped.
  2. `lazy-sync` repairs generated `.jcode` files on sync or even equal-drift no-op.
  3. Generated files with markers may refresh; markerless/user-owned files are preserved or archived according to repair rules.
  4. Private/project rules stay pointer-only and durable rules belong in `.lazy-harness` records.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` protects pointer-only templates, stale markerless repair, message.received hook wiring, bash safety-only hook, non-blocking dev hook policy, and skill wrappers.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`, `.lazy-harness/decisions/0025-portability-single-entry-point.md`
  - Docs: `.lazy-harness/JCODE-INTEGRATION.md`
- Machine index:
  - graph ids: `kg_adr0029_jcode_wiring_source`, `kg_adr0029_jcode_wiring_tests`
  - generated index key: `pending`
