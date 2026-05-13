---
name: harness-doctor
description: Validate lazy-harness framework integrity — checks 30 containers, schemas, safety guards, link integrity, backup state. Emits Unified Result Schema (Principle #9). Read-only, idempotent.
allowed-tools: bash, read, grep, ls
---

# harness-doctor

Use this skill to verify the health of the `.lazy-harness/` framework in current project.

This is a **read-only** check tool. It never modifies files. It produces:

1. Pass/fail summary per check category
2. Detailed evidence with `file:line` references
3. Unified Result Schema JSON output (saved to `logs/validations.jsonl`)
4. Suggested fixes when failures detected

> **Principle 0 reminder**: 사람도 AI 도 불완전하다. doctor 는 양쪽 한계를 보완하는 자동 검진. 매 사이클마다 framework 가 살아있는지 확인.

## Default behavior

```bash
.jcode/skills/harness-doctor/scripts/doctor.sh [--json] [--verbose] [--target <dir>]
```

## Check categories

| ID | Category | What it verifies |
|----|----------|---------------|
| C1 | Structure | 30 containers per framework-contract exist |
| C2 | READMEs | All containers have README.md |
| C3 | Schemas | result.schema.json + decision.schema.json valid JSON |
| C4 | Safety | `.git/info/exclude` has `.lazy-harness/`, git tracked = 0 |
| C5 | Pre-commit | `.git/hooks/pre-commit` exists, contains lazy-harness guard, executable |
| C6 | Core docs | framework-contract.md exists, ≥ 18 principles referenced |
| C7 | Links | XML/MD referenced files actually exist |
| C8 | Backup | (placeholder for Principle #18 R3 backup verification) |

## Options

```bash
--target DIR     project root (default: cwd)
--json           emit JSON only (Unified Result Schema)
--verbose        show all check details
-h, --help       show help
```

## Output

Human-readable by default:

```text
╭───────────────────────────────────────╮
│ lazy-harness doctor · /home/.../medivance │
╰───────────────────────────────────────╯

[C1] Structure ............... ✓ pass (30/30 containers)
[C2] READMEs ................. ✓ pass (35/35)
[C3] Schemas ................. ✓ pass (2/2 valid JSON)
[C4] Safety .................. ✓ pass (0 git-tracked, exclude OK)
[C5] Pre-commit .............. ✓ pass (executable, contains guard)
[C6] Core docs ............... ✓ pass (461 lines, 18 principles)
[C7] Links ................... ⚠ warn (2 references unverified)
[C8] Backup .................. ○ skipped (deferred to M3)

Overall: 6 pass, 1 warn, 1 skipped, 0 fail
```

Or with `--json`, full Unified Result Schema array.

## Behavior contract

- **Read-only**: never modifies files
- **Logs to `logs/validations.jsonl`** (append-only, JSONL)
- **Exit codes**:
  - 0 = all pass (or only warns)
  - 1 = 1 + check failed
  - 2 = doctor itself errored
- **Idempotent**: safe to run anytime, anywhere

## Related

- Spec: `.lazy-harness/framework/framework-contract.md` (Principle #1.2, #9, #11)
- Companion: `harness-init` (creates structure), `harness-update` (sync schema)
- Result schema: `.lazy-harness/schemas/result.schema.json`
