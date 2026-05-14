# ADR 0032 — User Correction and Ownership SSOT Convergence

- Status: Accepted
- Date: 2026-05-14
- Trigger: User observed an agent trying to perform Supabase DB correction work from a PWA host and clarified that the upstream app/DB work belongs in `dev/medivance`, while `dev/medivance-pwa` should maintain compatibility.

## Context

Lazy-harness already required record-first search and root-bound convergence, but a practical gap remained: when the user corrected an agent's host understanding, the correction could be acknowledged in chat without being converted into a durable host record.

That failure mode is dangerous for project-role and ownership facts. If a host is a downstream compatibility client, an agent must not infer that it owns shared DB migrations just because a `supabase/` folder or a query exists locally.

## Decision

Adopt **user-correction ownership convergence**:

1. Treat explicit user correction about host role, source-of-truth, ownership, or forbidden work as a confirmed override.
2. Search/read current `.lazy-harness` records first, then update or create the appropriate record in the current host.
3. Default layer is SSOT for:
   - project identity and role
   - upstream/downstream host relationships
   - DB/API/schema/env ownership
   - source-of-truth location
   - areas this host must not mutate without explicit confirmation
4. If the correction is about behavior, contract, domain term, regression, or architectural trade-off, use BDD, SDD, DDD, TDD, or ADR respectively and cross-link to the SSOT instead of duplicating.
5. The record must include an `Implementation map` even when the fact is an ownership boundary rather than a function implementation.
6. Root `AGENTS.md` may carry a short bridge rule for generic agents, but canonical truth remains in `.lazy-harness`.
7. If the primary layer is ambiguous, ask using the standard option gate before writing.

## Required record shape for ownership facts

A host ownership SSOT record should include:

- Status and date.
- User-confirmed statement.
- Scope: current host, upstream host/service, downstream consumers if known.
- Allowed work in this host.
- Forbidden work in this host without explicit user confirmation.
- Exception process.
- Implementation map:
  - primary files/directories that expose the boundary
  - key configs/routes/functions if verified
  - tests/protection or validation command
  - cross-layer links
  - machine index / graph ids

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/AGENTS.md` — adds the user-correction convergence rule and SSOT ownership default.
  - `.lazy-harness/decisions/0032-user-correction-ownership-ssot-convergence.md` — this ADR.
  - `.lazy-harness/spec/platform/implementation-map-standard.md` — extends implementation maps with ownership boundaries.
  - `.lazy-harness/manifests/init-categories.json` — syncs operational ADR 0030~0032 to hosts under `framework/operational-adrs/`.
  - `.lazy-harness/scripts/lazy-init.ts` — supports manifest `targetPath` so source files can install into host-safe reference paths.
  - `.lazy-harness/scripts/lazy-sync.ts` — supports manifest `targetPath` during host updates.
  - `.lazy-harness/knowledge/graph.jsonl` — stores confirmed machine-readable edges for this decision.
- Key symbols / config:
  - `§2.5 Missing record 수렴 규칙` (`.lazy-harness/AGENTS.md`) — operational prompt section that forces missing/incorrect host knowledge to converge into records.
  - `Implementation map` template (`.lazy-harness/spec/platform/implementation-map-standard.md`) — now includes ownership boundary fields.
- Flow:
  1. User corrects host role/source-of-truth/ownership.
  2. Agent searches existing `.lazy-harness` records inside current host.
  3. Agent updates or creates the primary SSOT/layer record with implementation map.
  4. Future agents read that record before touching DB/API/schema/project-boundary work.
  5. `lazy-sync` copies operational ADR 0030~0032 into `framework/operational-adrs/` so host agents can read the detailed rule without polluting host ADR numbering.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
  - host dogfooding sync + `.lazy-harness/bin/lazy test`
- Ownership boundaries:
  - Owner/upstream: current host `.lazy-harness` record for confirmed host facts.
  - This framework may change: prompt grammar, ADRs, standards, seed/sync assets, manifest target-path routing.
  - This framework must not change: host-specific DB/schema ownership without writing the host-local SSOT record and obtaining confirmation when ambiguous.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0031-root-bound-record-convergence.md`
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
- Machine index:
  - graph ids: `kg_adr0032_decides_user_correction_convergence`, `kg_agents_implements_adr0032`, `kg_implmap_standard_implements_ownership_boundaries`
  - generated index key: `pending until implementation-index generator exists`

## Consequences

### Positive

- User corrections become durable host memory instead of one-off chat acknowledgements.
- Prevents downstream clients from accidentally owning upstream DB/API/schema changes.
- Gives future agents a concrete place to record host relationships and forbidden mutation boundaries.

### Negative

- Agents must write a small SSOT record more often after corrections.
- Some corrections can span multiple layers, requiring option-gate discipline.

### Mitigation

- Default ownership/source-of-truth corrections to SSOT.
- Use cross-links instead of duplicating facts in many layers.
- Use implementation maps to make boundary facts searchable even without a concrete function symbol.
