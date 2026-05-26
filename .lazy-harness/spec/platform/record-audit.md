# SDD — Record Audit CLI

Status: accepted
Date: 2026-05-21
Layer: SDD
Related: `.lazy-harness/spec/platform/project-profile.md`, `.lazy-harness/spec/platform/progressive-knowledge-graph.md`, `.lazy-harness/planning/document-resource-ingestion-implementation-plan.md`

## Contract

`record-audit` is a read-only host record quality dashboard for lazy-harness dogfooding and normal host maintenance.

It answers one question:

```text
Did this host accumulate reusable lazy-harness project memory, and what needs cleanup next?
```

The command must not write records, mutate logs, resolve questions, fill Project Profile answers, or repair graph entries. It reports actionable signals only.

## CLI

```bash
bun .lazy-harness/scripts/record-audit.ts --format=json --root <host> --source <lazy-harness-source>
.lazy-harness/bin/lazy record-audit --format=md
```

Options:

- `--root` / `--host`: host root to inspect. Defaults to `LAZY_HOST_ROOT` or current working directory.
- `--source`: canonical lazy-harness source checkout or its `.lazy-harness` directory. When present, framework-synced records can be separated from host-owned or host-changed records. If it resolves to the inspected host's own `.lazy-harness`, `warnings` must explain that installed-host readiness checks need the canonical framework source instead.
- `--format md|json`: output format.
- `--recent N`: number of recent record files to show.

## Required output signals

The JSON output must include:

- `layers`: file and byte counts by DDD/SDD/BDD/TDD/ADR/SSOT/planning/knowledge/project/log layers.
- `totals.hostOwnedOrChanged`: records that are unique to the host or changed from framework source.
- `hostComparison`: per-layer `unique`, `changed`, `same`, and `totalOwnedOrChanged` counts.
- `jsonl`: line and invalid-line counts for knowledge/log JSONL files.
- `markers`: file counts for incomplete/risk markers such as `needs-interview`, `TODO`, `FIXME`, `stale`, `conflict`, `ambiguous`, and `needs-option-gate`.
- `projectProfile`: separate `artifactsComplete` from `answersComplete` and report `needsInterviewFields`.
- `graph`: implementation graph row count plus invalid, actionable missing path, source-only path, and comma-joined path hygiene signals.
- `recentFiles`: recent non-framework record files for quick dogfood review.
- `warnings` and `nextActions`: human/actionable summary.

## Non-goals

- Not a canonical decision engine.
- Not a log compactor.
- Not graph repair.
- Not Project Profile fill.
- Not a replacement for `.lazy-harness/bin/lazy test` or `doctor.py`.

## Implementation map

- `.lazy-harness/scripts/record-audit.ts`
  - Implements the read-only audit CLI and JSON/Markdown renderers.
  - Compares host `.lazy-harness` records against an optional canonical source checkout.
  - Splits Project Profile artifact completeness from answer completeness.
  - Reports graph hygiene and JSONL parseability without mutating files.
  - Separates `graph.sourceOnlyPaths` from actionable `graph.missingPaths` when `--source` is available.
  - Warns when `--source` points at the inspected host itself, because that misclassifies framework-source-only paths during installed-host readiness checks.
- `.lazy-harness/bin/lazy`
  - Adds `lazy record-audit` dispatcher entry.
- `.lazy-harness/scripts/self-test.py`
  - `check_record_audit_cli` protects host/source comparison, Project Profile answer split, graph hygiene reporting, JSONL invalid-line reporting, marker counting, and dispatcher pass-through.
  - `check_gate_state_cli_and_record_audit_source_guard` protects the self-source warning used by lifecycle Phase 3 readiness checks.
- `.lazy-harness/knowledge/graph.jsonl`
  - Stores confirmed implementation/test edges for this CLI.

## Discovery capture

- DDD: none.
- SDD: this contract is accepted for the record audit CLI.
- BDD: candidate, future host UX may render this as a compact dashboard.
- TDD: protected by self-test fixture.
- ADR: none for now; this is an incremental CLI under existing record-first and dogfood feedback rules.
- SSOT: none.
- Planning: dogfood improvement candidate promoted into this implementation slice.
