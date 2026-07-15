# Runtime and Shared State Isolation

Status: accepted
Layer: SDD
Date: 2026-06-03
Related SDD: `.lazy-harness/spec/platform/host-root-resolution.md`
Related ADR: `.lazy-harness/decisions/0002-conflict-resolution-protocol.md`
Related SSOT: `.lazy-harness/ssot/runtime-and-shared-state.md`
Related TDD: `.lazy-harness/tests/parallel-runtime-state-isolation.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 런타임 상태
  - shared state
- Applies when:
  - `.lazy-harness` is symlinked across git worktrees
  - multiple agents/sessions operate in the same branch or worktree
  - lifecycle hooks write packet, gate, timing, or progress state
  - framework helpers append durable knowledge/candidate/event rows
- Must:
  - resolve `LAZY_HOST_ROOT` as the caller workspace root, not the physical symlink target
  - keep ephemeral runtime state under `LAZY_RUNTIME_ROOT`
  - default `LAZY_RUNTIME_ROOT` to the caller worktree git-dir plus `lazy-harness/runtime/<session-key>`
  - keep cross-session durable event/knowledge visibility under `LAZY_SHARED_ROOT` or canonical `.lazy-harness` records
  - default `LAZY_SHARED_ROOT` to the git common-dir plus `lazy-harness/shared`
  - preserve the invariant that a shared write result is one of `appended`, `deduped-identical`, `conflict-recorded`, or `blocked/needs-human-resolution`
  - dedupe rows when the canonical JSON payload is identical, including rows without a stable id
  - record same-id/different-payload writes in `*.conflicts.jsonl` instead of silently overwriting or dropping them
  - serialize same-file durable writes with a lock
  - guard commit/push validation with a worktree-local git-action lock
- Must not:
  - write runtime packets, open gate state, hook timings, or disconnect snapshots into a symlink target shared `.lazy-harness/state` by default
  - treat generated summaries/indexes as canonical truth
  - silently discard conflicting durable rows

## Purpose

Parallel agents need two properties at the same time:

1. isolated runtime state so one session/worktree does not poison another session's hook packets, open-gate cache, timing log, or last-session snapshot;
2. shared durable visibility so records, candidates, and confirmed knowledge from another session are discoverable.

The failure mode observed in dogfooding was a worktree whose `.lazy-harness` was a symlink to the primary checkout. Runtime files such as `state/search-read-debt.jsonl`, `state/record-decision-packets.jsonl`, `questions/open.xml`, and `knowledge/*.jsonl` therefore appeared shared. Product git indexes were still worktree-local, but harness runtime/evidence streams were not isolated.

## Contract

### Roots

```text
LAZY_HOST_ROOT     = caller product workspace/worktree root
LAZY_HARNESS_ROOT  = physical or copied framework code root, usually $LAZY_HOST_ROOT/.lazy-harness
LAZY_RUNTIME_ROOT  = per-worktree/per-session mutable runtime root
LAZY_SHARED_ROOT   = cross-session durable event bus root
```

Defaults:

```text
LAZY_RUNTIME_ROOT = $(git rev-parse --absolute-git-dir)/lazy-harness/runtime/<session-key>
LAZY_SHARED_ROOT  = $(git rev-parse --git-common-dir)/lazy-harness/shared
```

`<session-key>` is derived from `session_id`/`JCODE_SESSION_ID` when available, otherwise `default`.

### Runtime-only files

These are non-canonical and default to `LAZY_RUNTIME_ROOT`:

- `state/search-read-debt.jsonl`
- `state/record-decision-packets.jsonl`
- `state/open-gates.json`
- `state/last-session.json`
- `logs/hook-timings.jsonl`
- `logs/lifecycle-compare.jsonl`
- `logs/pi-agent-end-trace.jsonl` — opt-in, content-free Pi `agent_end` structural diagnostics; newest 50 rows only, with bounded message/content-kind/tool metadata per row and atomic temp-file replacement
- `logs/actions.jsonl` entries created by disconnect/runtime hooks

Runtime-only state may be pruned without losing durable project knowledge.

### Shared durable/event files

These remain host-visible across sessions/worktrees:

- human-facing records under `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning,plans}`
- knowledge JSONL under `.lazy-harness/knowledge/`
- historical route telemetry files may exist from the removed task-router experiment, but current hooks must not append them
- future shared question/event queues that carry explicit scope metadata

Shared writes must use lock + canonical-payload dedupe + stable-id conflict-visible recording.

### No silent drop invariant

For a shared stable JSONL write, the implementation returns exactly one status:

| Status | Meaning |
|---|---|
| `appended` | row was new and appended |
| `deduped-identical` | the same canonical JSON payload already existed, even when the row has no stable id |
| `conflict-recorded` | same stable id but different payload; conflict row written |
| `blocked/needs-human-resolution` | merge would rewrite a canonical document or ambiguous conflict requires a human gate |

Only `deduped-identical` may skip writing. Idless rows may only dedupe by identical canonical payload; different idless payloads append as new rows. Meaningful same-id conflicts must remain visible.

## Implementation map

- Primary files:
  - `.lazy-harness/scripts/runtime-paths.ts` — TypeScript resolver, shared lock helper, and stable JSONL append helper.
  - `.lazy-harness/hooks/lifecycle/helpers/runtime_paths.py` — Python resolver and stable JSONL append helper for lifecycle code.
  - `.lazy-harness/hooks/lifecycle/helpers/runtime-paths.sh` — shell adapter that exports `LAZY_RUNTIME_ROOT` and `LAZY_SHARED_ROOT`.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — writes static search-debt packet journal to runtime state.
  - `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` — reads the matching runtime packet journal for the same session/worktree.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — writes timing/compare logs to runtime logs.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — resolves the canonical runtime log path and writes opt-in structural `agent_end` trace rows.
  - `.lazy-harness/hooks/lifecycle/helpers/check-record-decision-shadow.py` — writes record-decision shadow journal to runtime state.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — reads runtime packet journal.
  - `.lazy-harness/hooks/lifecycle/helpers/gate-fingerprint.sh` and `.lazy-harness/scripts/gate-state.ts` — use runtime `open-gates.json`.
  - `.lazy-harness/hooks/pre-commit-guard.sh` and `.lazy-harness/hooks/pre-push.sh` — use worktree-local git-action lock.
  - `.lazy-harness/scripts/lazy-sync.ts`, `.lazy-harness/scripts/document-resource-ingestion.ts`, `.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh` — use stable JSONL append helpers for knowledge JSONL writes.
- Key symbols:
  - `LAZY_RUNTIME_ROOT`
  - `LAZY_SHARED_ROOT`
  - `runtimeRoot`, `sharedRoot`, `appendJsonlStable`
  - `runtime_state_path`, `append_jsonl_stable`
  - `agentEndTracePath`, `writeAgentEndTrace`
  - `git-action.lockdir`
- Tests / protection:
  - `.lazy-harness/tests/parallel-runtime-state-isolation.md`
  - `check_parallel_runtime_state_isolation`
  - `check_shared_jsonl_conflict_visible`
  - `check_pi_package_layout_and_contract` — verifies trace default-off behavior, runtime-root placement, structural-only fields, and queued follow-up preservation.
- Machine index:
  - `kg_pi_agent_end_structural_trace_impl_20260714`
  - `kg_pi_agent_end_structural_trace_test_20260714`
  - `check_pre_commit_runs_lazy_test`

## Layer completeness

- DDD: no domain/business terminology impact.
- SDD: this file defines runtime/shared state contracts.
- BDD: user-visible behavior is fewer false blocks/contamination reports in parallel sessions.
- TDD: `.lazy-harness/tests/parallel-runtime-state-isolation.md` protects symlink and same-worktree parallel cases, plus stable JSONL identical-payload dedupe and same-id conflict visibility.
- ADR: ADR 0002 conflict protocol already mandates no silent conflict resolution; no new trade-off beyond applying it to runtime/shared storage.
- SSOT: `.lazy-harness/ssot/runtime-and-shared-state.md` defines canonical root/path ownership.

## Discovery capture

- Planning: previous backlog item "Parallel record writes with conflict boundaries" is now partly implemented for runtime isolation, JSONL stable append, and git-action lock.
- Remaining work: scoped XML question queues and full MD write DAG remain future work unless later dogfood shows blocking failures.

## Discovery capture — Pi agent-end trace

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: updated because the runtime-state contract now includes the opt-in structural trace.
- BDD: none because tracing is disabled by default and does not change visible agent flow.
- TDD: updated in `.lazy-harness/tests/parallel-runtime-state-isolation.md` and `.lazy-harness/tests/pi-agent-package.md`.
- ADR: none because the trace preserves ADR 0051 runtime behavior and adds no enforcement.
- SSOT: updated in `.lazy-harness/ssot/runtime-and-shared-state.md` with the canonical runtime path.
- Planning: updated in `.lazy-harness/planning/analysis-discovery-capture-backlog.md`.
