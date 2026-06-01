# Rule Binding Action Boundary

Status: accepted
Layer: SDD
Related SSOT: `.lazy-harness/ssot/rule-lifecycle.md`
Related ADR: `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md`
Related TDD: `.lazy-harness/tests/rule-binding-pr-body-guard.md`

## Purpose

Agents can store host/team rules correctly and still fail to apply them later. This SDD defines the action-boundary enforcement surface that turns stored rules into executable policies.

## Contract

Action-boundary helpers must:

1. Run before irreversible or external mutations when a supported tool surface is available.
2. Read canonical `.lazy-harness` records or rule bindings from the current host root.
3. Avoid hardcoding project-specific content in `.jcode` or Jcode memory.
4. Emit a clear denial/reminder before the mutation happens when severity is `block`.
5. Allow hosts to override defaults through canonical binding metadata.
6. Keep development edit/write/multiedit hooks fast and non-blocking; action-boundary guards target external mutations such as PR creation, not every file edit.

## First exemplar: PR body format

If `.lazy-harness/ssot/pr-description-format.md` exists in the host, `gh pr create` and `gh pr edit` commands must provide a PR body that contains the required headings:

- `## Why`
- `## What`
- `## Task`

The helper accepts bodies supplied through:

- `--body <text>`
- `--body=<text>`
- `-b <text>`
- `--body-file <path>`
- `--body-file=<path>`

When the command mutates a PR and the body is missing or lacks required sections, the helper emits STOP text explaining the source record and required sections.

## Non-goals

- This first exemplar does not intercept every GitHub MCP PR mutation surface.
- This does not replace prompt/record-first instructions.
- This does not make `.jcode` a policy store; generated `.jcode` only wires the generic helper.

## Implementation map

- Status: `implemented-first-exemplar`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-rule-action-boundary.py` — action-boundary helper.
  - `.jcode/hooks/check-bash.sh` — active local bash hook wrapper.
  - `.lazy-harness/scripts/jcode-wiring.ts` — generated bash hook template.
  - `.lazy-harness/ssot/rule-lifecycle.md` — lifecycle and binding SSOT.
  - `.lazy-harness/scripts/self-test.py` — regression fixtures.
- Key symbols:
  - `extract_bash_command` — pulls command text from Jcode payload shapes.
  - `default_pr_body_binding` — host-sensitive default binding activated by `pr-description-format.md`.
  - `extract_body` — reads body text from CLI args/body files.
  - `main` — emits STOP text on violations and exits 0 for hook compatibility.
- Flow:
  1. Jcode fires `tool.execute.before` for `bash`.
  2. `.jcode/hooks/check-bash.sh` captures payload and invokes `check-rule-action-boundary.py`.
  3. The helper loads host bindings/defaults, matches `gh pr create/edit`, and validates body headings.
  4. If output is non-empty, the bash hook returns a deny JSON to Jcode.
- Tests / protection:
  - `check_rule_action_boundary_pr_body_guard` in `.lazy-harness/scripts/self-test.py`.
  - `check_jcode_wiring_rule_action_boundary_hook` in `.lazy-harness/scripts/self-test.py`.
