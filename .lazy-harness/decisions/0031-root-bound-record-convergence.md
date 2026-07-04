# ADR 0031 — Root-bound record convergence

- Status: Accepted
- Date: 2026-05-14
- Trigger: User confirmed option A for keeping host knowledge inside `.lazy-harness` / `.jcode` and asked whether missing `.lazy-harness` content should be pulled from current host evidence and mapped.

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Aliases:
  - 루트 바운드
  - root bound
  - 현재 root 만
  - sibling 금지
  - 지식 반입 금지
- Applies when:
  - searching or discovering host knowledge, or a `.lazy-harness` record is missing
  - an agent considers parent/sibling-directory discovery
  - a test-strategy / validation-gate / "Vitest required?" question arises
- Must:
  - keep search and discovery inside the current host root
  - when a record is missing, gather current-host evidence only and converge it into `.lazy-harness/<layer>` with an implementation map
  - read `.lazy-harness/tests/test-strategy.xml` first for any test-strategy or validation-gate question
  - store Jcode-local workflow notes only in `.jcode/harness/20-project-rules.md`
- Must not:
  - use parent/sibling discovery (`find ..`, `grep ../`, sibling-repo references) for host knowledge
- Record completion:
  - confirmed host facts converge into the appropriate `.lazy-harness/<layer>` record with an implementation map
- Related records:
  - `.lazy-harness/spec/platform/implementation-map-standard.md`
  - `.lazy-harness/ssot/implementation-map-storage.md`
  - `.lazy-harness/tests/test-strategy.xml`

## Context

Agents were discovering `AGENTS.md` and docs with parent-directory commands such as `find ..`, which leaks sibling repositories into the current host's knowledge search. This breaks lazy-harness's record-as-SSOT model because host knowledge should converge into the current host's `.lazy-harness` records, not drift into parent or sibling directories.

The user clarified the intended direction: when `.lazy-harness` has no record, gather evidence from the current host and map it back into `.lazy-harness` so source-of-truth gradually converges.

## Decision

Adopt **root-bound record convergence**:

1. Search and discovery must stay inside the current host root.
2. Parent/sibling discovery (`find ..`, `grep ../`, sibling repo references) is forbidden for host knowledge.
3. If `.lazy-harness` lacks a needed record, inspect current host evidence only:
   - `package.json`
   - framework/config files
   - `src/**`
   - `tests/**`
   - current host `docs/**`
   - current host root `AGENTS.md`
4. Create or update the appropriate `.lazy-harness/<layer>/...` record.
5. Add an `Implementation map` linking source files, key symbols/config, flow, tests, and cross-layer references.
6. Store Jcode-local workflow notes only in `.jcode/harness/20-project-rules.md`.
7. Root `AGENTS.md` may remain a bridge for generic tools, but canonical framework/host knowledge remains in `.lazy-harness` records.

## Test strategy special case

Test strategy is canonical at:

```text
.lazy-harness/tests/test-strategy.xml
```

If it is missing or stale, agents must derive it from current host evidence such as package scripts, test configs, and existing tests. Human-facing `docs/test-strategy.md` is optional and secondary.

For any test strategy / validation gate / "Vitest required?" question, agents must read `.lazy-harness/tests/test-strategy.xml` first. Reading `docs/test-strategy.md` or package scripts first is the wrong order unless the XML is missing or empty.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/AGENTS.md` — adds root-bound search and missing-record convergence rules.
  - `.lazy-harness/manifests/init-categories.json` — seeds the canonical host test-strategy record during init.
  - `.lazy-harness/scripts/lazy-init.ts` — renders the `test-strategy.xml` seed template.
  - `.lazy-harness/tests/README.md` — documents canonical test strategy storage.
  - `.lazy-harness/decisions/0031-root-bound-record-convergence.md` — this ADR.
- Key symbols / config:
  - `makeSeedFile` (`.lazy-harness/scripts/lazy-init.ts`) — returns specialized XML for `test-strategy.xml`.
  - Category B `tests/` seed (`.lazy-harness/manifests/init-categories.json`) — ensures new hosts get the canonical test strategy file.
- Flow:
  1. Agent searches `.lazy-harness` inside host root.
  2. If record is missing, agent reads current host evidence only.
  3. Agent creates the canonical layer record with implementation map.
  4. Future agents reuse that record instead of rediscovering from scattered docs.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
  - host dogfooding sync + `.lazy-harness/bin/lazy test`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
  - TDD: `tests/test-strategy.xml` (host-seeded by init; not a source-repo file).
- Machine index:
  - graph ids: `pending`
  - generated index key: `pending until implementation-index generator exists`

## Consequences

### Positive

- Prevents sibling-repo contamination.
- Makes missing knowledge converge into `.lazy-harness` instead of scattered docs.
- Gives every new host a canonical test strategy record location from init.

### Negative

- Agents must do a little more local evidence gathering before answering.
- Existing hosts may need a one-time `test-strategy.xml` migration.

### Mitigation

- `lazy-init` seeds new hosts automatically.
- Existing hosts can receive the file via sync plus a small migration or manual record creation.
