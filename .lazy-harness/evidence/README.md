# Evidence Capsules

Status: container
Layer: SDD/TDD support

This directory stores optional, durable, privacy-reviewed evidence capsules for non-trivial claims.

Use `.lazy-harness/templates/evidence-capsule.md` when a validation, visual comparison, benchmark, migration dry-run, dogfood finding, or phase closure needs reproducible evidence beyond a commit message.

Rules:

- Capsules are manually authored. Hooks must not write them automatically.
- Capsules are supporting evidence, not canonical truth over records or source code.
- Redact secrets, credentials, personal data, raw transcripts, and unrelated product data.
- Prefer summaries, command outputs, file paths, and reproducible steps over raw logs.
- Link related records, plans, commits, screenshots, or generated artifacts when relevant.

Small edits with focused validation usually do not need a capsule.
