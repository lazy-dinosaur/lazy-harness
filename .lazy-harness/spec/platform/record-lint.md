# SDD — Record Lint

Status: accepted
Date: 2026-06-24
Layer: SDD
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related SDD: `.lazy-harness/spec/platform/record-digest-format.md`, `.lazy-harness/spec/platform/record-write-update-policy.md`
Related TDD: `.lazy-harness/tests/record-lint.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - validating that canonical records carry a well-formed `## Rule digest` and no broken record references
  - wiring record-quality enforcement into the commit/push gate
  - debugging why `lazy test`/self-test rejects a malformed record
- Must:
  - validate every canonical record (domain/spec/behavior/tests/decisions/ssot, excluding README) for digest presence, valid Status/Layer/Scope enums, Layer-matches-path, Applies-when/Must bullets, and broken `.lazy-harness/...md` references outside code fences
  - stay read-only and deterministic; `--fail-on-issues` exits non-zero for the commit/push gate
  - be enforced via `lazy test`/self-test on the framework source (commit/push blocking, FRAMEWORK_ONLY scope); on hosts it is advisory (`lazy record-lint`) since host-authored records are host-owned and may not yet carry digests
- Must not:
  - add a dev-time blocking hook (ADR 0016/0041/0048: dev edits stay non-blocking)
  - mutate records, indexes, graph, or runtime state
  - flag example paths inside fenced code blocks as broken references
- Record completion:
  - changes to checks, enums, or enforcement update this SDD, `.lazy-harness/tests/record-lint.md`, the script, dispatcher, self-test, and manifest together
- Related records:
  - `.lazy-harness/spec/platform/record-digest-format.md`
  - `.lazy-harness/spec/platform/record-write-update-policy.md`

## Purpose

`record-lint` is the deterministic, commit-gate validator that keeps the record corpus from decaying: every reusable canonical record must carry a well-formed `## Rule digest` (so the digest retrieval tier stays usable) and must not cite missing `.lazy-harness` records (so cross-layer navigation stays sound). `record-audit` remains the advisory dashboard; `record-lint` is the strict, fail-on-issues check.

## Checks (per canonical record)

Canonical layers: `domain` (DDD), `spec` (SDD), `behavior` (BDD), `tests` (TDD), `decisions` (ADR), `ssot` (SSOT). `README.md` excluded.

1. `missing-rule-digest` — no `## Rule digest` section.
2. `digest-missing-status` / `digest-bad-status` — Status absent or not one of `active|advisory|deprecated|reverted|needs-review`.
3. `digest-missing-layer` / `digest-bad-layer` / `digest-layer-path-mismatch` — Layer absent, invalid, or not matching the path's layer.
4. `digest-missing-scope` / `digest-bad-scope` — Scope absent or not one of `framework-global|host-project|team-policy|layer-fact|transient-plan|local-only`.
5. `digest-missing-applies-when` / `digest-missing-must` — required digest bullets absent.
6. `broken-record-ref` — cites a `.lazy-harness/...md` path that does not exist, scanning the record body with fenced code blocks stripped (so template examples are not flagged).

## CLI contract

```bash
.lazy-harness/bin/lazy record-lint [--format=json|md] [--fail-on-issues]
```

- `--fail-on-issues` exits `2` when any issue is found (commit/push gate). Default is report-only.
- JSON shape: `schemaVersion`, `mode: "record-lint"`, `root`, `inspected`, `cleanRecords`, `issueCount`, `counts`, `issues[]` (`recordPath`, `code`, `detail`), `note`.

## Enforcement boundary

- Enforced at the commit/push gate through `lazy test`/self-test (blocking). A malformed record fails commit, forcing the author to add/fix the digest or reference.
- NOT a dev-time `tool.execute.before` hard gate: per ADR 0016/0041/0048, dev edits stay non-blocking for iteration speed; the commit/push gate is the blocking layer.
- Downstream hosts run the same `lazy record-lint` after `lazy sync` (runtime-agnostic CLI). The `lazy-record-quality` skill installed with `lazy pi install` / `lazy omp install` (`packages/lazy-harness-pi/skills/`) guides host-record digest backfill and reference cleanup. This is not wired through Jcode.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/record-lint.md` — this contract.
  - `.lazy-harness/tests/record-lint.md` — regression contract.
  - `.lazy-harness/scripts/record-lint.ts` — read-only validator CLI.
  - `.lazy-harness/bin/lazy` — dispatches `lazy record-lint`.
  - `.lazy-harness/scripts/self-test.py` — runs `record-lint --fail-on-issues` as a commit-gate check.
- Key symbols:
  - `lint` (`.lazy-harness/scripts/record-lint.ts`) — per-record digest + reference validation.
  - `digestField` — `- Name: value` extraction for Status/Layer/Scope.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_record_lint_cli`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/record-digest-format.md`, `.lazy-harness/spec/platform/record-write-update-policy.md`
  - ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
- Machine index:
  - graph ids: `kg_record_lint_cli_20260624`, `kg_record_lint_self_test_20260624`

## Rule placement

- Rule: canonical records are validated for digest format + reference integrity by a read-only `record-lint`, enforced at the commit/push gate, not a dev-time hard gate.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/record-lint.md`
- Why not AGENTS.md: this is a platform validation contract; AGENTS.md carries only the digest authoring pointer.
- Why not local notes: shared framework behavior for all hosts.
- Confirmation: user-confirmed

## Discovery capture

- DDD: none.
- SDD: this contract; complements record-digest-format and record-write-update-policy.
- BDD: authors get a commit-time failure when a canonical record lacks a well-formed digest or cites a missing record.
- TDD: `.lazy-harness/tests/record-lint.md` + self-test protect checks and enforcement.
- ADR: ADR 0041 governs (organic; commit-gate blocking, no new dev-time hard gate).
- SSOT: digest format remains record-digest-format.md.
- Planning: `.lazy-harness/planning/discovery-vs-loading-followups-20260624.md` (record quality enforcement section).
