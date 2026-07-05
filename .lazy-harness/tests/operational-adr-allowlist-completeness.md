# TDD — Operational ADR Allowlist Completeness

Status: active
Layer: TDD
Date: 2026-06-25
Related SDD: `.lazy-harness/spec/platform/record-lint.md`
Related ADR: `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`
Related planning: `.lazy-harness/planning/framework-adr-host-distribution-drift-20260625.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - allowlist 회귀
  - operational adr 검사
- Applies when:
  - adding or removing a framework ADR that a synced canonical record references by a `decisions/NNNN-slug.md` path
  - changing the init-categories operational-adrs allowlist
- Must:
  - keep every framework ADR (>= 0026) path-referenced by a synced canonical record present in the init-categories operational-adrs allowlist, so the reference resolves on hosts
  - protect this with `check_operational_adr_allowlist_complete` at the commit/push gate (FRAMEWORK_ONLY)
- Must not:
  - rely on host record-lint to catch this (it skips Category-A framework records on hosts and only flags non-existent `.lazy-harness/...md` paths, so dangling agent references pass clean)
- Record completion:
  - allowlist or check changes update this TDD record, the check, and the drift planning record
- Related records:
  - `.lazy-harness/spec/platform/record-lint.md`
  - `.lazy-harness/planning/framework-adr-host-distribution-drift-20260625.md`

## Regression

Root cause: framework ADRs do not sync into host `decisions/` (host-owned institutional memory, ADR 0027); they reach hosts only via the explicit operational-adrs allowlist in `init-categories.json` (synced to `framework/operational-adrs/`). When ADR 0035/0038/0050/0051 were created, the allowlist was not updated, so synced files referencing them dangled on hosts — a medivance worktree agent searched host `decisions/` for `0050-pi-omp-only-runtime.md`, did not find it, and reported a broken reference.

A follow-up audit found nine more such gaps (0028, 0029, 0039, 0042, 0043, 0044, 0045, 0047, 0049) referenced by synced canonical records but absent from the allowlist. `record-lint` did not catch them: on hosts it skips Category-A framework records (ownership suppression) and only flags non-existent `.lazy-harness/...md` paths, so agent-facing path references to un-synced ADRs pass clean.

## Check

`check_operational_adr_allowlist_complete` (`.lazy-harness/scripts/self-test.py`, FRAMEWORK_ONLY):

1. parse the operational-adrs allowlist numbers from `init-categories.json` (targetPath under `framework/operational-adrs/NNNN-`),
2. scan every SYNCED canonical record (`domain|spec|behavior|tests|decisions|ssot`, README excluded) for path-form `decisions/NNNN-slug.md` references with fenced code blocks stripped,
3. fail when any referenced ADR (NNNN >= 0026) is absent from the allowlist.

Path-form only: bare `ADR NNNN` mentions and year-like numbers (e.g. 2026) are not resolvable file paths and are intentionally not flagged, mirroring `record-lint` reference semantics.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/scripts/self-test.py` — `check_operational_adr_allowlist_complete` (the check).
  - `.lazy-harness/manifests/init-categories.json` — operational-adrs allowlist (the data under test).
- Flow:
  1. A synced canonical record path-references a framework ADR.
  2. The check requires that ADR in the operational-adrs allowlist.
  3. The commit/push gate (`lazy test`) fails if a referenced ADR is not allowlisted.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/record-lint.md`
  - ADR: `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`
  - Planning: `.lazy-harness/planning/framework-adr-host-distribution-drift-20260625.md`

## Rule placement

- Rule: framework ADRs path-referenced by synced canonical records must be in the operational-adrs allowlist; enforced at the commit/push gate, FRAMEWORK_ONLY.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/operational-adr-allowlist-completeness.md`
- Why not AGENTS.md: this is a platform distribution-integrity test, not agent prompt grammar.
- Why not local notes: shared framework behavior for all hosts.
- Confirmation: user-confirmed

## Layer completeness

- SDD: 영향 없음 — no API/component/IPC/contract changed. The check is a framework commit-gate test that complements the existing `record-lint.md` validation SDD; no new or changed contract.
- BDD: 영향 없음 — no user-visible flow changed. This is a framework-internal commit/push-gate validation only.
- SSOT: 영향 있음 — the operational-adrs allowlist in `.lazy-harness/manifests/init-categories.json` is the source-of-truth for which framework ADRs reach hosts; it was updated (+9 ADRs: 0028,0029,0039,0042,0043,0044,0045,0047,0049) in the same commit. The governing rule is recorded in `.lazy-harness/planning/framework-adr-host-distribution-drift-20260625.md`. No separate `ssot/*.md` is created — the manifest is the canonical sync-surface config (ADR 0027/0050).
- DDD: 영향 없음 — no domain term or business rule changed.

## Discovery capture

- DDD: none.
- SDD: complements `record-lint.md`; record-lint does not cover host-side framework-ADR resolvability.
- BDD: none (no visible user flow).
- TDD: this record plus `check_operational_adr_allowlist_complete`.
- ADR: none new (distribution-config integrity, governed by ADR 0027/0050).
- SSOT: `init-categories.json` operational-adrs allowlist (manifest config) is the data under test.
- Planning: `framework-adr-host-distribution-drift-20260625.md` (follow-up 1 closed).
