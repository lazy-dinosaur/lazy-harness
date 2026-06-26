---
name: lazy-skill-create
description: "RETIRED (ADR 0050): jcode runtime removed; this wrapper no longer functions. Pi/OMP custom skills are authored directly in packages/lazy-harness-pi/skills/."
allowed-tools: read
---
# lazy-skill-create — RETIRED (ADR 0050)

The jcode runtime was decommissioned (ADR 0050 — Pi/OMP-only runtime), so this
skill no longer generates `.jcode/skills/` wrappers and the legacy
`lazy skill create` wrapper command no longer applies under Pi/OMP.

**Replacement:** Pi/OMP custom skills are authored by hand directly in the
framework package source at `packages/lazy-harness-pi/skills/<name>/SKILL.md`.
There is no host-side skill-creation skill or CLI under Pi/OMP — by design.

See `.lazy-harness/decisions/0050-pi-omp-only-runtime.md` and
`.lazy-harness/manifests/skills.xml` (status="retired", replacedBy="pi-omp-package-skill").
