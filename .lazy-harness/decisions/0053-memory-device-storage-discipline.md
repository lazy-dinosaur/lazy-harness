# ADR 0053 — Memory-Device Storage Discipline (walk-first retrieval)

Status: accepted
Date: 2026-07-04
Layer: ADR
Related plan: `.lazy-harness/planning/memory-device-implementation-plan.md`
Related discussion: `.lazy-harness/planning/retrieval-architecture-holistic-review.md`
Related ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`, `.lazy-harness/decisions/0049-discovery-vs-loading-complete-lean-discovery.md`

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Applies when:
  - writing or updating a canonical record (surface terms, cross-links, backlinks)
  - deciding how retrieval should reach records (walking, grep, map drill-down)
  - considering embedding/RAG/index machinery for record retrieval
  - user vocabulary appears in conversation that records do not yet contain
  - backfilling existing records to these rules (full-corpus re-review, 2026-07-04 amendment)
- Aliases:
  - 메모리 장치
  - memory device
  - 백링크
  - backlink
  - 표면어
  - surface terms
  - grep bait
  - 걷기 검색
  - traversal retrieval
- Must:
  - treat records as an LLM-authored, LLM-read memory device; retrieval = link-walking (tree/map → entry doc → in-file links), not bulk fetch or similarity search
  - seed surface terms at write time from two sources: observed user vocabulary (harvest as it occurs) and LLM-generated variants (Korean↔English, synonyms, predicted future greps)
  - backfill the FULL existing corpus to these rules via the guided backfill skill — batched, user-checkpointed, never one unreviewable bulk diff (2026-07-04 amendment; supersedes the original walk-frequency-only organic policy)
  - keep same-topic pieces cross-linked so any entry point reaches the rest (acceptance: reachability; audited by `lazy record-structure-audit`)
  - keep backlinks DERIVED (`lazy backlink-index` → `generated/backlink-index.json`, surfaced by `lazy map` drill-down); fallback protocol `grep -rl <record-path> .lazy-harness/`
  - mark weak or conflicting claims with optional `Confidence:`/`Contested:` digest fields instead of letting them harden into accepted fact
- Must not:
  - hand-maintain backlinks or any derivable data inside canonical records
  - introduce embedding/vector retrieval as primary record search (delegated safety net remains an evidence-conditional option per ADR 0024)
  - make surface-term/link checks commit-blocking in HOST context before that host's backfill completes (framework source became blocking 2026-07-04 after W8 zero-advisory completion — see second Amendment)
- Record completion:
  - changes to storage-discipline rules update this ADR, `.lazy-harness/spec/platform/record-digest-format.md`, `.lazy-harness/spec/platform/record-write-update-policy.md`, and the audit/index tooling together
- Related records:
  - `.lazy-harness/spec/platform/record-digest-format.md`
  - `.lazy-harness/spec/platform/record-write-update-policy.md`
  - `.lazy-harness/planning/memory-device-implementation-plan.md`

## Context

2026-07-04 discussion (user-confirmed, full trail in `retrieval-architecture-holistic-review.md`) converged on: records are a memory device attached to the LLM (human readability non-essential); priority 1 accurate lossless storage, priority 2 complete recall ("nothing missed"); retrieval is hop-by-hop link-walking with generic tools (tree/grep/fuzzy), so STORAGE DISCIPLINE — not a search engine — is the retrieval infrastructure. Independently validated by Karpathy's LLM Knowledge Bases pattern (compile→interlink→lint, navigate-not-search, bypasses RAG); lazy-harness adds what that ecosystem lacks: typed layers (absence detection), lint enforcement, provenance grades, forced lookup.

Recall decomposes into three miss classes: ① discovery (solved by ADR 0049 complete overview), ② bridging (user vocabulary absent from file text — no tool can connect what is not written), ③ synthesis (partial set reported as complete; live specimen: 2026-07-04 TimSquad first-pass miss). W1 baseline (2026-07-04): surface terms 0/160, true orphans 4, one 216/227 connected component, avg 4.8 outbound links.

## Decision

1. **Surface-term rule (counters ②)**: reusable records SHOULD carry `Aliases`/`Surface terms` seeded from observed user vocabulary + LLM-generated variants. Coverage is lintable (advisory); quality is validated by use (replay/loop), not review.
2. **Cross-link/reachability rule (counters ③)**: same-topic pieces must link (directly or via a hub); acceptance criterion is reachability, measured by `lazy record-structure-audit` connected components/orphans.
3. **Backlinks are derived**: computed from forward links + graph.jsonl by `lazy backlink-index` into `generated/backlink-index.json` (rebuildable, cue-only), surfaced as `referenced by` in `lazy map` drill-down; grep fallback works with stale/absent index. Never hand-stored.
4. **Weak-claim markers**: optional `Confidence: high|medium|low` / `Contested: <record>` digest fields (borrowed from the hermes llm-wiki implementation) so uncertain claims are visible to future retrieval.
5. **Enforcement level**: advisory checks in `record-lint` (reported, not exit-affecting) until dogfood evidence justifies promotion — consistent with ADR 0016 and the roadmap hard-guard pause.

## Consequences

- Positive: ②/③ miss classes get structural countermeasures; the corpus becomes walkable from any entry; audits make "stored well" deterministic; retroactive backlinks are free (forward links already exist).
- Negative / cost: write-time obligation grows (surface terms, links) — mitigated by LLM authorship and advisory-first enforcement; generated index adds one more derived artifact to rebuild.
- Neutral: canonical MD, typed layers, map-first discovery, and no-embedding stance unchanged.

## Amendment — 2026-07-04: full-corpus re-review backfill (user decision)

Original decision limited backfill to organic, walk-frequency-priority updates ("do not make every historical record verbose retroactively"). The user overrode this the same day via option gate ("전면 재검토로 정책 변경"): ALL existing canonical records are to be re-reviewed and reworked to the new rules (surface terms, cross-links/reachability, Confidence/Contested where warranted).

Preserved safeguards (unchanged by the amendment):

- execution is batched and user-checkpointed via the guided backfill skill (`lazy-memory-backfill`, lazy-record-quality precedent) — "full corpus" defines COVERAGE, not a single unreviewed diff;
- observed user vocabulary remains the preferred surface-term source where available; LLM-generated variants are legitimate authorship (user-confirmed 2026-07-04) but should be marked by usage evidence over time (replay/loop validates quality);
- derived-backlink and advisory-lint principles are untouched;
- risk accepted knowingly: LLM-authored aliases without usage evidence may be weak bait — the retro loop + W5 replay measure and correct this.

## Amendment — 2026-07-04 (2): framework-source commit-gate promotion after W8

W8 completed same-day (advisories 160→0, orphans 0). User then approved promoting the surface-term check to a blocking commit-gate issue (`missing-surface-terms`) in the FRAMEWORK SOURCE context only. Rationale: deterministic check with ~zero false positives, trivial compliance cost, digest-format precedent (already blocking), ADR 0016-compatible (commit boundary, not dev-time), and same-session injection≠compliance evidence showed advisory+habit decays. HOST context remains advisory until each host's own backfill completes (host-owned pace, record-lint ownership-suppression principle).

## Implementation map

- Status: `partially-verified (W1/W2 verified; W3 contracts landed; full-corpus backfill W8 in progress via lazy-memory-backfill skill)`
- Primary files:
  - `.lazy-harness/scripts/record-structure-audit.ts` — W1 read-only baseline audit (`lazy record-structure-audit`).
  - `.lazy-harness/scripts/backlink-index.ts` — W2 derived backlink generator (`lazy backlink-index`); exports `refreshBacklinkIndex` for auto-regen.
  - `.lazy-harness/scripts/record-index.ts` — `--write` path auto-refreshes the backlink index (small-automation #1, 2026-07-05).
  - `.lazy-harness/generated/backlink-index.json` — derived, rebuildable backlink index.
  - `.lazy-harness/scripts/record-map.ts` — drill-down `referenced by` surface (loadBacklinkEntries).
  - `.lazy-harness/scripts/record-lint.ts` — advisory surface-term check.
  - `.lazy-harness/bin/lazy` — dispatchers for the two new commands.
- Key symbols:
  - `loadBacklinkEntries` (`record-map.ts`) — reads generated index into drill-down.
  - `refreshBacklinkIndex` / `main` (`backlink-index.ts`) — forward-link + graph scan, all schema generations; exported for record-index `--write` auto-regen.
- Tests / protection:
  - determinism: two identical consecutive audit runs (verified 2026-07-04); W1↔W2 orphan parity (4/4, verified).
  - self-test checks: candidate, to be added with the next slice (batching commit-gate changes).
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/record-digest-format.md`, `.lazy-harness/spec/platform/record-write-update-policy.md`
  - Planning: `.lazy-harness/planning/memory-device-implementation-plan.md`
- Machine index:
  - graph ids: `kg_adr0053_memory_device_discipline`

## Rule placement

- Rule: storage discipline (surface terms, cross-links, derived backlinks, weak-claim markers) is the retrieval infrastructure for walk-first record memory; enforcement starts advisory.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0053-memory-device-storage-discipline.md`
- Why not AGENTS.md: platform decision; AGENTS carries only the walking-grammar pointer.
- Walking-grammar pointer: DEFERRAL LIFTED 2026-07-05 (user-approved option gate) — one line added under AGENTS.md §2.2 pointing at Rule digest Aliases/Surface terms + backlink-index/grep-on-entry fallback.
- Confirmation: user-approved plan execution 2026-07-04 ("좋아 진행해봐") over the user-confirmed requirement set; small-automation slice (backlink auto-regen in record-index --write + AGENTS pointer) user-approved 2026-07-05.

## Discovery capture

- DDD: none new (taxonomy recorded in holistic review).
- SDD: updated — digest-format + write-update-policy gain surface-term/backlink/marker rules (same slice).
- BDD: none.
- TDD: candidate — self-test checks for audit/backlink CLIs (next slice).
- ADR: this record.
- SSOT: none (generated/ boundary already covers derived data).
- Planning: memory-device-implementation-plan W2/W3 sections updated with results.
