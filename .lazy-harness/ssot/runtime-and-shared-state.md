# Runtime and Shared State Roots

Status: accepted
Layer: SSOT
Date: 2026-06-03
Related SDD: `.lazy-harness/spec/platform/runtime-and-shared-state.md`
Related TDD: `.lazy-harness/tests/parallel-runtime-state-isolation.md`

## Rule digest

- Status: active
- Layer: SSOT
- Scope: framework-global
- Aliases:
  - 상태 저장소
  - state 위치
- Applies when:
  - choosing where to write runtime, shared, or canonical lazy-harness state
  - deciding LAZY_HOST_ROOT / LAZY_RUNTIME_ROOT / LAZY_SHARED_ROOT placement for hooks or session state
- Source of truth:
  - `LAZY_HOST_ROOT`: caller workspace/worktree root
  - `LAZY_RUNTIME_ROOT`: runtime-only per worktree/session mutable state
  - `LAZY_SHARED_ROOT`: cross-session durable event bus
- Must:
  - use `LAZY_RUNTIME_ROOT` for lifecycle packet journals, open-gate cache, hook timing, compare logs, disconnect snapshots, and other ephemeral state
  - keep opt-in Pi `agent_end` structural traces under `LAZY_RUNTIME_ROOT`; never store raw conversation, tool arguments, or tool results in the trace
  - use `LAZY_SHARED_ROOT` for shared non-canonical event telemetry that should be visible across sessions/worktrees
  - keep human-facing records and knowledge files in `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning,plans,knowledge}` as canonical or durable host memory
  - use lock + canonical-payload dedupe + stable-id conflict-visible helpers for shared JSONL writes
- Must not:
  - use a symlink target's `.lazy-harness/state` as the default runtime state for a caller worktree
  - silently drop a same-id/different-payload durable row

## Paths

| Class | Default path | Ownership |
|---|---|---|
| Runtime root | `$(git rev-parse --absolute-git-dir)/lazy-harness/runtime/<session-key>` | current worktree/session |
| Shared root | `$(git rev-parse --git-common-dir)/lazy-harness/shared` | repository/worktree set |
| Runtime packet journal | `$LAZY_RUNTIME_ROOT/state/search-read-debt.jsonl` | current session |
| Runtime record-decision shadow | `$LAZY_RUNTIME_ROOT/state/record-decision-packets.jsonl` | current session |
| Runtime gate cache | `$LAZY_RUNTIME_ROOT/state/open-gates.json` | current session |
| Runtime timing log | `$LAZY_RUNTIME_ROOT/logs/hook-timings.jsonl` | current session |
| Opt-in Pi agent-end trace | `$LAZY_RUNTIME_ROOT/logs/pi-agent-end-trace.jsonl` | current session; structural fingerprints only |
| Historical route telemetry | `$LAZY_SHARED_ROOT/logs/route-decisions.jsonl` | deprecated old task-router experiment; current hooks must not append |
| Durable knowledge | `.lazy-harness/knowledge/*.jsonl` | host institutional memory |

## Implementation map

- `.lazy-harness/scripts/runtime-paths.ts` and `.lazy-harness/hooks/lifecycle/helpers/runtime_paths.py` implement the root derivation.
- `.lazy-harness/hooks/lifecycle/helpers/runtime-paths.sh` exports the env vars for shell hooks.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` resolves `pi-agent-end-trace.jsonl` through `runtime_paths.py` (or an explicit `LAZY_RUNTIME_ROOT`) and writes content-free rows only when `LAZY_PI_AGENT_END_TRACE=1`.
- `.lazy-harness/spec/platform/runtime-and-shared-state.md` defines behavior and no-silent-drop invariant, including idless identical-payload dedupe.
- `.lazy-harness/tests/parallel-runtime-state-isolation.md` protects the storage split and stable JSONL append contract.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` protects trace default-off behavior, explicit and canonical-fallback placement, bounded 50-row/content-shape retention, no-raw-content output, and fail-open continuation when the trace path is unwritable.
- Machine graph rows: `kg_sdd_runtime_shared_state`, `kg_ssot_runtime_shared_roots`,
  `kg_pi_agent_end_structural_trace_impl_20260714`,
  `kg_pi_agent_end_structural_trace_test_20260714`.

## Discovery capture — Pi agent-end trace

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: updated in `.lazy-harness/spec/platform/runtime-and-shared-state.md`.
- BDD: none because trace collection is disabled by default and non-user-facing.
- TDD: updated in the runtime-isolation and Pi-package regression records.
- ADR: none because runtime/shared ownership is unchanged.
- SSOT: updated because this record owns the new runtime-only log path and content boundary.
- Planning: updated in the analysis-discovery capture backlog.
