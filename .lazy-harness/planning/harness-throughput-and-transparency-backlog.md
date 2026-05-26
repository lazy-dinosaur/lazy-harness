# Harness Throughput and Transparency Backlog

Status: proposed-backlog
Date: 2026-05-26
Confirmation: user-confirmed direction, implementation not started

## Purpose

Capture near-future framework workstreams discovered while planning Capability Registry Phase 1. These are backlog/planning items only and should not block the current Capability Registry implementation.

## Workstream A — Parallel initial record search

Problem:

- Lazy-harness requires record-first lookup before host-specific reasoning.
- Current searches are often sequential or manually batched.
- Initial intent classification could search DDD/SDD/BDD/TDD/ADR/SSOT/planning/knowledge in parallel and return a compact evidence bundle.

Goal:

```text
Given a user request, run root-bound parallel lookups across relevant record layers and present a concise set of candidate records before the agent reasons from memory.
```

Candidate implementation:

- `lazy search-intent --message <text> --format json|md`
- Parallel layer-specific search workers.
- Output grouped by layer, confidence, and action trigger.
- No semantic search implementation from scratch; use existing search provider/router constraints.

## Workstream B — Work transparency and resumable progress log

Problem:

- Long sessions can be interrupted.
- Subagents or later sessions need quick situational awareness without reading the whole transcript.
- Current planning/todo/records help, but progress snapshots are not consistently maintained as a first-class artifact.

Goal:

```text
During meaningful work, keep a compact, append-friendly progress/handoff log so another agent can resume quickly after session loss or delegation.
```

Candidate implementation:

- `.lazy-harness/state/work-progress.jsonl` for runtime progress events, ignored if runtime-only.
- `.lazy-harness/planning/<topic>.md` for durable plan/update summaries.
- `lazy progress checkpoint --task <id> --status <...> --summary <...>` helper.
- Automatic summary prompt for subagent handoff.
- Integration with todo list and `response.completed` audit, but no hard blocking at first.

## Workstream C — Parallel record writes with conflict boundaries

Problem:

- Lazy-harness records often require updates across SSOT/SDD/TDD/ADR/planning/knowledge.
- Some writes are independent and could be parallelized.
- Other writes target the same file and need serial merge discipline.

Goal:

```text
Make record-as-output faster while preserving canonical consistency by parallelizing independent writes and serializing same-file or same-index updates.
```

Parallel-safe examples:

- Create separate new files in different layers.
- Append independent JSONL rows with stable ids, if append-only and duplicate guarded.
- Generate derived index after canonical writes complete.

Serial-required examples:

- Multiple edits to the same MD record.
- Updating ADR count plus adding ADR freshness lines.
- Rewriting canonical JSON registry files such as `capabilities.json`.
- Deduplicating graph IDs.

Candidate implementation:

- `lazy record-plan --outputs ...` computes a write DAG.
- `lazy record-apply` applies independent nodes in parallel and serializes conflicts.
- `record-audit` checks duplicate IDs, stale indexes, and missing Implementation map.

## Rule placement

- Rule: Parallel initial search, resumable progress logging, and parallel-safe record writes are proposed framework backlog items for throughput and transparency, not active behavior rules yet.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/harness-throughput-and-transparency-backlog.md`
- Why not AGENTS.md: these are future implementation workstreams, not current universal agent requirements.
- Why not `.jcode`: these are shared lazy-harness framework capabilities, not local/private Jcode-only workflow.
- Confirmation: user-confirmed direction, implementation not started

## Discovery capture

- SDD: candidates for search-intent, progress checkpoint, and record write DAG contracts.
- TDD: candidates for parallel search coverage, checkpoint resume fixture, and record write conflict tests.
- ADR: candidate decision on runtime vs durable progress state and parallel record write safety model.
- SSOT: possible future state/storage records for progress and record-write DAG.
- Planning: this file is the active backlog capture.

## 2026-05-26 dogfood note — dry-run and mutating cleanup must not run in parallel

Status: observed during lifecycle Phase 3 readiness cleanup
Confirmation: validation evidence

Observation:

- Running `gate-state clear-stale --dry-run` and mutating `gate-state clear-stale` for the same roots in one parallel batch can reorder the dry-run/read and write operations.
- This confirms the existing parallel-write principle: read-only checks and writes against the same runtime/canonical file must be serialized if their output is used as evidence.

Implication:

- Future `lazy record-plan` / write DAG work should classify dry-run/read-after-write dependencies explicitly.
- For readiness cleanup, run dry-run first, inspect output, then run mutation, then run verification as separate serial phases.

## Rule placement

- Rule: Dry-run/read evidence and mutating cleanup for the same lazy-harness state files must be serialized; they are not parallel-safe even if one command is nominally read-only.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/harness-throughput-and-transparency-backlog.md`
- Why not AGENTS.md: this is a planning/dogfood finding for future parallel write orchestration, not a universal current rule yet.
- Why not `.jcode`: this is shared lazy-harness execution planning behavior, not local/private Jcode-only workflow.
- Confirmation: validation evidence
