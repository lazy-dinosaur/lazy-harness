---
name: harness-init
description: Initialize lazy-harness framework in current project — creates 30 containers per framework-contract Principle 0~18. Idempotent, supports --force, --dry-run, --tier.
allowed-tools: bash, read, write, edit, ls, grep
---

# harness-init

Use this skill when the user wants to initialize or refresh the lazy-harness framework in a project.

The goal is to create the `.lazy-harness/` directory structure (30 containers) defined by `framework-contract.md` so all 18 principles are immediately addressable.

> **Principle 0 reminder**: 사람도 AI 도 불완전하다. lazy-harness 는 이 둘의 한계 교집합에 안전망을 친다. init 은 그 안전망의 출발점.

## Default behavior

Run the bundled script:

```bash
.jcode/skills/harness-init/scripts/init-lazy-harness.sh <target-project>
```

If no target is provided, use the current working directory.

The script creates:

```text
.lazy-harness/
├── framework/                # framework-contract.md (single source of truth)
├── domain/                   # DDD aggregates, ubiquitous-language, bounded-contexts
├── spec/                     # SDD: frontend, backend, data, integration, infra, platform
├── behavior/                 # BDD scenarios
├── tests/                    # TDD plan and mapping
├── contracts/                # contract zone index
├── ssot/                     # SSOT registry
├── intent/                   # Intent Spec (active, archive, templates)
├── prd/                      # PRD (optional, large units)
├── questions/                # open questions
├── decisions/                # ADR + small decisions log
├── planning/                 # missions, plan, backlog
├── traceability/             # commit ↔ spec mapping
├── regression/               # regression registry + contract history
├── git/                      # commit-log, branch-events
├── retrospective/            # weekly auto + milestone manual
├── schemas/                  # result schema + xml schemas
├── scripts/                  # verification scripts (TS-heavy)
├── manifests/                # hook + verification + skill registration
├── visual/                   # HTML visualizations
├── generated/                # derived artifacts (json/md from xml)
├── logs/                     # actions/decisions/questions/validations (jsonl)
├── handoff/                  # session handoff
├── plans/                    # completion plans
├── trails/                   # long-term roadmap
├── progress/                 # daily progress
├── adapters/                 # input adapters (figma, requirement, bug, ...)
└── hooks/                    # lazy-harness lifecycle hooks
```

For Git repositories, it adds `.lazy-harness/` to `.git/info/exclude` by default and verifies `.git/hooks/pre-commit` blocks accidental staging.

## Options

```bash
init-lazy-harness.sh [TARGET_DIR] [--force] [--dry-run] [--tier <0|1|2|3>] [--gitignore]
```

- `--force`: overwrite existing files (default keeps existing)
- `--dry-run`: print what would be created without doing it
- `--tier`: adoption tier (default 2). reserved for future Graduated Adoption — currently creates same structure
- `--gitignore`: add to `.gitignore` instead of `.git/info/exclude` (not recommended for private use)
- `-h, --help`: show help

## Idempotent behavior

- Existing files are preserved unless `--force` is used (prints "keep existing")
- Directory creation is always safe (mkdir -p)
- Schema files are placed only on first init

## After running

Verify structure:

```bash
find <target>/.lazy-harness -maxdepth 2 -type d -print | sort
```

Verify safety (must return 0):

```bash
cd <target> && git ls-files | grep -c '^\.lazy-harness'
```

Verify pre-commit guard:

```bash
ls <target>/.git/hooks/pre-commit && grep -q "lazy-harness" <target>/.git/hooks/pre-commit
```

## Policy choices

Default private mode:

- `.lazy-harness/` is added to `.git/info/exclude` (NOT `.gitignore`) — keeps private without team awareness
- `.git/hooks/pre-commit` is installed/updated to block accidental staging
- Schema files ship as v1.1 (matching framework-contract Principle 0/17/18)

This skill never:

- modifies team-shared files (`.gitignore`, `package.json`, etc.) without explicit `--gitignore` flag
- pushes anything to git
- overwrites existing data files (only schema/structure)

## Related

- framework-contract: `.lazy-harness/framework/framework-contract.md`
- planning: `.lazy-harness/planning/phase-5-plan.xml` (5a success criteria)
- decisions: `.lazy-harness/decisions/0001-core-philosophy.md`
- companion skills: `harness-doctor` (validate), `harness-update` (sync schema)
