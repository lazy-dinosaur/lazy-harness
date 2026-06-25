# Planning — Regression registry data cleanup (host-owned)

Created: 2026-06-25
Status: open (host-owned, on host schedule)
Owner: each host project

## Context

The Fix-commit regression gate reader was fixed to JSON-parse the registry
(`456d5fa`), and a validated `lazy regression add` writer now prevents new
garbage. The remaining work is host-owned DATA cleanup of pre-existing garbage
entries already in each host's `.lazy-harness/regression/registry.jsonl`
(host runtime data, not framework Category A).

A safe mechanical migration was already applied this session: 13 truncated shas
in the medivance registry were expanded to full 40-hex via `git rev-parse`
(same commit, git-verified — not fabricated).

## Remaining backlog (per host, surfaced by `lazy regression lint`)

Post-migration `lazy regression lint --format=md` counts:

- medivance: 23 issues — `bad-repro` (7), `bad-sha` (6, `pending`/`PENDING-*`
  stubs + an `{"id":...}`-shaped row), `bad-description` (4),
  `missing-protected-by` (4), `placeholder-protected-by` (1), `pending-protected-by` (1)
- medivance-homepage: 1 (`bad-description`)
- medivance-pwa: 1 (`bad-repro`)
- medivance-homepage.admin-members: 1 (`bad-description`)

## Approach (no fabrication)

For each flagged entry:

1. Run `.lazy-harness/bin/lazy regression lint --format=md` to get exact line + code.
2. If the entry has a real 40-hex sha: derive the real `description`/`reproSteps`
   from the actual commit (`git show -s <sha>`) and `protectedBy` from the
   test file(s) the commit added (`git show --stat <sha>`). Re-register via
   `lazy regression add` (idempotent dedup updates are not supported — remove the
   old line first if replacing).
3. If the entry is a `pending`/`PENDING-*` stub with no real sha: find the real
   commit if it exists, else remove the unsalvageable line.
4. NEVER invent a `protectedBy` test path — a fake path protects nothing and is
   worse than an honest gap. If a Fix had no test, that is a separate test-debt
   item, not a registry-format fix.

## Acceptance

`lazy regression lint --fail-on-issues` exits 0 on the host (or only genuine
test-debt remains, explicitly acknowledged).

## Discovery capture

- DDD/BDD: none.
- SDD/TDD: `.lazy-harness/spec/platform/regression-registry.md` + `.lazy-harness/tests/regression-registry.md` capture the durable reader/writer contract.
- ADR: governed by ADR 0016/0041 (advisory gate); no new decision.
- SSOT: registry data is host-owned runtime; no source-of-truth change.
- Planning: this record.
