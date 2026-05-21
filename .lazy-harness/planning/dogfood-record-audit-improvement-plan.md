# Dogfood Record Audit Improvement Plan

Status: active
Date: 2026-05-21
Source: Medivance dogfood record audit

## Context

Medivance dogfooding showed that lazy-harness records are accumulating, but the quality signals were spread across manual shell snippets:

- host-owned/changed record counts
- layer file distribution
- Project Profile `needs-interview` fields
- JSONL line/parse counts
- graph hygiene signals
- log volume
- recent record files

The user approved turning these dogfood improvement candidates into framework improvements and keeping the source plus Medivance host updated.

## Plan

1. Implement `record-audit` read-only CLI.
2. Split Project Profile artifact completeness from answer completeness in audit output.
3. Surface graph hygiene warnings for missing and comma-joined paths.
4. Keep log compaction as a later improvement; the first slice reports log volume only.
5. Sync to Medivance and dogfood with real host records.

## Current slice

- `.lazy-harness/scripts/record-audit.ts`
- `.lazy-harness/bin/lazy record-audit`
- `.lazy-harness/spec/platform/record-audit.md`
- self-test coverage in `.lazy-harness/scripts/self-test.py`
- Medivance dogfood after sync

## Acceptance criteria

- Source self-test and smoke doctor pass.
- `lazy record-audit --format=json` works through the dispatcher.
- Medivance audit reports host-owned/changed records and Project Profile answer completeness without mutating Medivance records.
- Implementation graph records the new CLI and self-test protection.

## Follow-up backlog

- Add explicit graph repair or graph lint command.
- Add log summary/rollup or compaction view.
- Consider a quality score once enough audits are available.
