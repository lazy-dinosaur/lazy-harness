# Evidence — Jcode Integration Decommission (2026-08-22)

Status: implementation-complete; final standard validation pending
Primary ADR: `.lazy-harness/decisions/0059-pi-primary-jcode-decommission.md`
Primary TDD: `.lazy-harness/tests/jcode-decommission.md`

## Scope

User confirmed complete removal of active Lazy-Harness Jcode integration while preserving all runtime-neutral improvements, Pi stable support, OMP Experimental support, Jcode build/source rollback artifacts, and rescue commit `129e90c`.

## Private rollback capture

- Private backup root: `/home/lazydino/.jcode/decommission-backups/20260822T050600Z`
- Permissions: backup root `0700`; manifest/config copies `0600` or original protected mode.
- Captured surfaces: global config, trusted-root registry, source/Medivance local prompt configs, source/Medivance Git excludes, launcher symlink, stable/current/lazy-patched pointers, launcher rollback state, Jcode swarm/prompt mirrors, modes, targets, and SHA-256 values.
- Raw config contents and user secrets are not copied into this evidence record.

## Machine decommission receipt

- Exact rollback dry-run passed before mutation.
- Normal launcher restored from the lazy-patched channel to its recorded prior target: `/home/lazydino/.jcode/builds/current/jcode`.
- Stable and current pointers remained byte/target-equivalent to the private backup.
- Eight managed Lazy-Harness hook assignments were removed from the global Jcode TOML through the byte-preserving package remover.
- Existing trusted roots `/home/lazydino/dev/lazy-harness` and `/home/lazydino/dev/medivance` were untrusted and their marker-owned local prompt state was removed.
- Stale missing `/tmp/lazy-agent-activate-*` registry entries were removed by deleting the now-unneeded Lazy-Harness trusted-root registry after exact backup.
- The remaining shared Jcode server process was stopped with TERM.
- Fresh launcher verification resolved to official/current build `v0.64.131-dev (dcc8ed100)`. Lazy-Harness-specific Jcode swarm/prompt mirror files were backed up and removed; unrelated personal Jcode TOML remained preserved.
- The lazy-patched candidate, official stable/current builds, Jcode source checkout, provenance, generated backups, and private decommission backup remain intact as inert rollback assets.

## Preserved framework behavior

- Pi/OMP work-unit grounding and governing-record hash reuse.
- Explicit-steer evidence invalidation.
- Canonical lifecycle `agent_end` payload and bounded follow-up behavior.
- OMP native ask activation.
- Runtime-neutral `LAZY_PROGRESS`.
- No-micro-edit validation cadence and one final standard boundary.
- Runtime-neutral project command boundary.
- Distribution-aware implementation-map audit.
- Host product branch/dirty-state protection.
- ADR 0055 agent-neutral orchestration direction.

## Focused checkpoint

- Relevant TypeScript Bun builds passed.
- `bun run typecheck:node` passed.
- `lazy check` passed; expected missing-path warnings correspond to intentional active Jcode file deletion.
- JSON/TOML-independent registry/manifest parsing, shell syntax, Python compilation, and `git diff --check` passed after manifest correction.
- Pi package, decommission, project command-boundary, and policy machinery focused fixtures passed.
- The first focused batch found two closure issues: ADR 0055 missing from the operational ADR distribution set and historical records citing the removed integration guide. Both were corrected.
- Independent review found one high-risk installed-host transition gap: retained source history was removed from the manifest but could not be pruned while source files existed. The repair now distributes visibly retired historical Jcode records so stale active host copies are overwritten, and an isolated installed-host fixture proves retired overwrite plus active adapter pruning without `JCODE_HOME` mutation.
- Independent review reported no blocker after inspecting the exact diff; its medium validation/status items are covered by the pending final standard gate.

## Pending closure

- Sync downstream hosts sequentially only after source green; preserve product branches and dirty files.
- Keep the separate 37-row graph migration deferred and user-approved; do not fold it into this work unit.
