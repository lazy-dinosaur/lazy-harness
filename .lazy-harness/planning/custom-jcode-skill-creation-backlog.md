# Custom Jcode Skill Creation Backlog

Status: cancelled-by-ADR-0059
Date: 2026-05-15
Related SDD: `.lazy-harness/spec/platform/jcode-skill-creation.md`

## Goal

Add a first-class lazy-harness command for host projects to create custom Jcode skills while keeping framework logic and project/team rules in canonical records.

## Scope

1. Add `lazy skill create <name>` dispatcher.
2. Add `.lazy-harness/scripts/skill-create.ts`.
3. Generate `.jcode/skills/<name>/SKILL.md`.
4. Optionally generate `.jcode/skills/<name>/scripts/<script>`.
5. Append metadata to `.lazy-harness/knowledge/skills.jsonl`.
6. Add self-test coverage.
7. Add sync manifest entries.
8. Sync to medivance and medivance-pwa after validation.

## Non-goals

- Do not invent project team policies inside generated skills.
- Do not overwrite user-owned skills by default.
- Do not promote every custom skill to framework-owned `manifests/skills.xml`.

## Discovery capture

- DDD: none, no domain model change.
- SDD: updated via `.lazy-harness/spec/platform/jcode-skill-creation.md`.
- BDD: none, CLI developer workflow only.
- TDD: planned self-test coverage.
- ADR: none, this is an additive implementation of existing `.jcode` wrapper architecture.
- SSOT: candidate `.lazy-harness/knowledge/skills.jsonl` storage behavior included in SDD.
- Planning: updated via this backlog.

## Rule placement

- Rule: Project custom skill creation must generate host-local `.jcode/skills/<name>/SKILL.md` while canonical policies/logic stay in `.lazy-harness` records/scripts.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/jcode-skill-creation.md`
- Why not AGENTS.md: This is detailed CLI/file contract, not thin grammar.
- Why not `.jcode`: `.jcode` is the generated target location, not the source of truth for generator rules.
- Confirmation: user-confirmed
