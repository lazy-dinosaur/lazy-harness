# TDD — Lifecycle Compare Fidelity

Status: accepted
Layer: TDD
Date: 2026-06-04
Related SDD: `.lazy-harness/spec/platform/hook-performance-measurement.md`
Related Planning: `.lazy-harness/planning/lifecycle-compare-mismatch-triage-20260604.md`
Related SSOT: `.lazy-harness/ssot/project-identity.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - 라이프사이클 비교 회귀
  - compare fidelity
- Applies when:
  - comparing legacy vs orchestrator lifecycle hooks (`response.completed.compare`) or diagnosing compare mismatches
  - running sandbox-mode lifecycle checks or deciding production orchestrator replacement
- Must:
  - distinguish real lifecycle mismatches from sandbox/instrumentation fidelity gaps before any production orchestrator replacement
  - normalize compare hashes with trailing-newline equivalence (keeping raw byte lengths); run sandbox in isolated runtime/shared roots with minimal read-only git facts and bounded state mirror
- Must not:
  - store `legacyBody`/`orchestratorBody`, raw payload, user messages, or raw hook bodies in compare logs
- Record completion:
  - changes to compare fidelity or summary tooling update this TDD plus the hook-performance-measurement SDD
- Related records:
  - `.lazy-harness/spec/platform/hook-performance-measurement.md`
  - `.lazy-harness/planning/lifecycle-compare-mismatch-triage-20260604.md`
  - `.lazy-harness/ssot/project-identity.md`

## Regression

Dogfood compare logs showed non-zero `response.completed.compare` mismatches after enough real rows accumulated:

- Medivance: `159/671` mismatches at triage time
- Medivance PWA: `2/19` mismatches at triage time
- Unclassified rows: `0`

The root causes were framework-general compare/sandbox fidelity gaps, not Medivance-only behavior:

1. **Trailing newline normalization**: legacy bash command substitution strips trailing newlines from helper stdout, while `lifecycle-check.py` stores subprocess stdout as-is.
2. **Missing git context**: sandbox used `git init` only, so git-dependent `check-fix-regression.sh` could not see real host last commit facts.
3. **Missing runtime/Jcode state**: sandbox copied only `.lazy-harness` and omitted duplicate-suppression `open-gates.json`, surfaced digest/packet journals, and correlated `.jcode/hooks/tool-events.jsonl` rows.

## Protected behavior

`check_response_completed_auto_route_telemetry` in `.lazy-harness/scripts/self-test.py` must protect:

- `lazy lifecycle-compare-summary --format=json --log <path>` reports compare rows without raw hook bodies,
- compare-mode body hashing uses legacy-equivalent trailing-newline normalization while preserving raw byte lengths for diagnostics,
- sandbox mode uses an isolated `LAZY_RUNTIME_ROOT` / `LAZY_SHARED_ROOT` rather than writing to the source host runtime,
- sandbox mode receives safe read-only git facts for git-dependent helpers,
- sandbox mode mirrors bounded runtime state tails for `open-gates.json`, `surfaced-rule-digests.jsonl`, and `search-read-debt.jsonl`,
- sandbox mode mirrors only message/session-correlated `.jcode/hooks/tool-events.jsonl` rows, not wholesale raw tool-event history,
- duplicate open-gate suppression matches legacy behavior in compare mode,
- `check-fix-regression.sh` matches legacy behavior in compare mode when the real host last commit is `Fix: ...`,
- compare logs still store hashes/lengths/helper names only and must not include `legacyBody`, `orchestratorBody`, raw payload, or raw message fields.

## Layer completeness

- DDD: no domain/business rule changed.
- SDD: impacted. `.lazy-harness/spec/platform/hook-performance-measurement.md` now defines Phase 3A compare fidelity: compare summary CLI, newline normalization, isolated sandbox runtime, minimal git facts, bounded state mirror, and message/session-filtered tool-event mirror.
- BDD: no app/user-facing flow changed. Agent-visible effect is better compare readiness telemetry.
- SSOT: impacted only through framework-vs-host boundary. Medivance evidence remains dogfood evidence, not framework target.
- ADR: no new ADR. Production replacement remains explicitly deferred and requires user approval.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — compare log writer; normalizes compare hashes with `rstrip("\n")` while keeping raw byte lengths.
  - `.lazy-harness/scripts/lifecycle-check.py` — sandbox root creation; isolated runtime/shared root; read-only git facts; bounded state/journal mirror.
  - `.lazy-harness/hooks/lifecycle/helpers/check-fix-regression.sh` — consumes sandbox-provided read-only git facts before falling back to real git.
  - `.lazy-harness/scripts/lifecycle-compare-summary.py` — read-only compare log summary CLI.
  - `.lazy-harness/bin/lazy` — dispatcher for `lifecycle-compare-summary`.
  - `.lazy-harness/scripts/self-test.py` — Phase 3A regression fixtures.
  - `.lazy-harness/manifests/init-categories.json` — syncs the summary CLI and this TDD record to hosts.
- Flow:
  1. Compare mode runs `lifecycle-check.py --sandbox` first.
  2. Sandbox copies framework files into a temp host and sets sandbox-only runtime/shared roots.
  3. Sandbox mirrors only bounded/minimal state needed to reproduce helper behavior.
  4. Legacy loop runs as user-visible truth.
  5. Compare log stores normalized hashes, byte lengths, helper names, sandbox flag, and mismatch booleans.
  6. `lazy lifecycle-compare-summary` summarizes mismatch classes for dogfood review.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy lifecycle-parity --format=md --fail-on-mismatch`
  - direct `lifecycle-check --sandbox --format=json` smoke
  - `lazy lifecycle-compare-summary --format=json --log <fixture>`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/hook-performance-measurement.md`
  - Planning: `.lazy-harness/planning/lifecycle-compare-mismatch-triage-20260604.md`
  - SSOT: `.lazy-harness/ssot/project-identity.md`
- Machine index:
  - graph ids: `kg_tdd_lifecycle_compare_fidelity`, `kg_impl_lifecycle_compare_summary_cli`, `kg_impl_lifecycle_sandbox_context_mirror`, `kg_impl_lifecycle_compare_newline_normalization`
  - generated index key: pending regeneration; generated indexes are derived and non-canonical.

## Rule placement

- Rule: compare-mode dogfood must distinguish real lifecycle mismatches from instrumentation/sandbox fidelity gaps before any production orchestrator replacement decision.
- Scope: framework-global TDD/regression.
- Primary record: `.lazy-harness/tests/lifecycle-compare-fidelity.md`.
- Why not AGENTS.md: this is lifecycle implementation/test protection, not compact operating grammar.
- Why not `.jcode`: it must ship with the framework to every host.
- Confirmation: user selected Phase 3A implementation option after triage.

## Discovery capture

- DDD: none.
- SDD: hook performance/compare contract updated.
- BDD: none.
- TDD: this record is the regression protection.
- ADR: none.
- SSOT: existing framework-vs-Medivance boundary remains applicable.
- Planning: Phase 3A source implementation is complete; host sync/re-dogfood is pending.

## 2026-06-04 compare/timing evaluation tooling protection

Status: accepted

Phase 3A post-patch evidence evaluation required repeatable timestamp filtering and session-aware timing aggregation. The regression protection now includes:

- `lazy lifecycle-compare-summary --since <ISO>` reports only compare rows at or after the given row `timestamp` and includes `sourceRows` / `filteredRows` counts.
- `lazy hook-timings --all-sessions --since <ISO>` aggregates timing rows across session runtime logs and filters old rows by `ts` / `timestamp`.
- The summary tools remain read-only and do not expose raw payload, user messages, or hook bodies.

Layer completeness:

- DDD: no domain/business rule changed.
- SDD: impacted. `.lazy-harness/spec/platform/hook-performance-measurement.md` now defines timestamp filtering and session timing aggregation contracts.
- BDD: no app/user-facing flow changed. Agent-visible effect is easier/reproducible dogfood evidence review.
- SSOT: no config/schema ownership change.
- ADR: no production replacement decision.

Implementation map update:

- `.lazy-harness/scripts/lifecycle-compare-summary.py` — `--since` compare row filter.
- `.lazy-harness/scripts/hook-timing-summary.py` — `--since` and `--all-sessions` timing aggregation.
- `.lazy-harness/scripts/self-test.py` — `check_response_completed_auto_route_telemetry` fixture verifies both new CLI paths.
- `.lazy-harness/bin/lazy` — help surface for new flags.
- Protected by: `python3 .lazy-harness/scripts/self-test.py --scope framework`.
