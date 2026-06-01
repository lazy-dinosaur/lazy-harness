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
6. Keep development edit/write/multiedit hooks scoped and fast, but registered as blocking Layer 2 force-gates so record-first misses are caught before file mutation.
7. Enforce runtime/dev-server/test-instance commands when relevant runtime/dogfood records exist in the host and have not been read or searched in recent tool-call history.

## Exemplar 1: PR body format

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

## Exemplar 2: runtime/dev-instance record-first lookup

If a host contains policy-bearing canonical records under `.lazy-harness/{domain,spec,behavior,decisions,ssot}/` whose path names indicate runtime, dogfood, dev-server, dev-instance, test-instance, or instance policy, lazy-harness treats dev/runtime start commands as an enforced action boundary.

Examples of matched commands include:

- `bun run dev`
- `bun dev:*`
- `bun scripts/dev-cli.ts ...`
- `npm run dev`, `pnpm dev`, `yarn dev`
- `next dev`, `vite`

Before allowing those commands, the helper checks recent tool-call history for a read/search of the relevant policy record. TDD regression records are intentionally excluded from default policy-source detection so framework tests do not make every host dev command block. If no lookup is visible, it emits STOP text listing the matching records and a grep command to run first.

## Non-goals

- These exemplars do not intercept every MCP mutation surface.
- This does not replace prompt/record-first instructions.
- This does not make `.jcode` a policy store; generated `.jcode` only wires the generic helper.

## Implementation map

- Status: `implemented-pr-and-runtime-exemplars`
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
  - `runtime_policy_records` — finds host runtime/dogfood policy records in canonical layers.
  - `check_runtime_record_binding` — denies dev/runtime commands until relevant records are looked up.
  - `main` — emits STOP text on violations and exits 0 for hook compatibility.
- Flow:
  1. Jcode fires `tool.execute.before` for `bash`.
  2. `.jcode/hooks/check-bash.sh` captures payload and invokes `check-rule-action-boundary.py`.
  3. The helper loads host bindings/defaults, matches PR/runtime command boundaries, and validates the required record/body evidence.
  4. If output is non-empty, the bash hook returns a deny JSON to Jcode.
- Tests / protection:
  - `check_rule_action_boundary_pr_body_guard` in `.lazy-harness/scripts/self-test.py`.
  - `check_rule_action_boundary_runtime_record_guard` in `.lazy-harness/scripts/self-test.py`.
  - `check_jcode_wiring_rule_action_boundary_hook` in `.lazy-harness/scripts/self-test.py`.
