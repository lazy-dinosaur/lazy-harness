---
name: lazy-skill-create
description: "RETIRED (ADR 0050): the jcode skill-create generator is gone. Framework skills are authored in this package's skills/; host-local custom skills use a host-attached Pi/OMP package. No lazy skill create generator."
allowed-tools: read
---
# lazy-skill-create — RETIRED (ADR 0050)

The jcode runtime was decommissioned (ADR 0050 — Pi/OMP-only runtime). The
`lazy skill create` CLI and `skill-create.ts` (which generated `.jcode/skills/`
wrappers) are removed; this wrapper no longer functions.

Pi/OMP load skills from any attached package's `skills/` dir
(`package.json#pi.skills` / `#omp.skills`). There is no generator CLI:

- **Framework skills** — author by hand in this source package:
  `packages/lazy-harness-pi/skills/<name>/SKILL.md`. Framework-owned (ADR 0027);
  edited only in the lazy-harness source repo, never on a downstream host.
- **Host-local custom skills** — a host creates its own package and attaches it
  via `.pi/settings.json` `packages: [...]` (Pi) or `omp plugin install <path>`
  (OMP). Authored directly; there is no host-side `lazy skill create` scaffolder.

Durable team/project policy belongs in `.lazy-harness` records (AGENTS §2.4,
`ssot/rule-sources.md`); a skill may point to the canonical record.

See `.lazy-harness/decisions/0050-pi-omp-only-runtime.md` (Phase 2 skill-authoring
decision) and `.lazy-harness/manifests/skills.xml` (status="retired").
