# Planning — Memory-Device Implementation Plan (walk-first retrieval, storage discipline, loop)

Status: proposed-plan (authored at user request 2026-07-04; per-step execution approval still required — ADR 0038)
Date: 2026-07-04
Layer: Planning
Source: user approved moving from discussion to planning ("이 방식으로 lazy-harness 현 구조를 분석하고 어떻게 구현할지 계획을 세우자")
Supersedes/absorbs: `.lazy-harness/planning/retro-loop-first-development-path-proposal.md` (its Phase 1 becomes W4 here)
Related discussion (requirements, canonical): `.lazy-harness/planning/retrieval-architecture-holistic-review.md` (2026-07-04 sections: memory-device requirement, traversal vision, storage-discipline convergence, surface-term authorship, Karpathy verification, risk registry)
Related report (derived view): /tmp/harness-analysis/retrieval-memory-final-report.html
Related ADR: `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`, `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`, `.lazy-harness/decisions/0049-discovery-vs-loading-complete-lean-discovery.md`

## Baseline facts (measured 2026-07-04, current structure)

- Corpus: 229 records total; 160 canonical (6 layers), digest coverage 160/160 (100%), digest = 16% of body tokens (312 vs 1,957 avg).
- Forward links: healthy — avg 4.8 outbound/canonical record, only 2 records with zero outbound.
- Orphans: 13 canonical records with ZERO inbound links from other canonical records (reachability gap, measured via in-file `.lazy-harness/...md` reference scan).
- Aliases: record-index parser ALREADY extracts `aliases[]`/`surfaceTerms[]` (440 fields in generated/record-index.json) — fields empty; C2 is content work, no parser work.
- Backlinks: no inbound-link concept anywhere (record-map.ts, record-index.ts — grep confirmed).
- graph.jsonl schema drift: 3 generations coexist — `relation/source/target` (356 rows incl status variant), `confidence/…/subject/target` (179), `subject/predicate/object` (29). Any graph consumer must normalize all three; graph-hygiene issue.
- Retrieval economics: map-first 345k tokens/4 tasks, 90% of cost = 129 follow-up full-body reads; overview 8.4k tokens.
- Tooling ground: scripts/ has record-lint.ts (6 checks), record-index.ts, record-map.ts, retrieval-workflow-benchmark.ts, graph-hygiene.ts — audit/backlink generators have clear attachment points.

## Work items

### W1 — Structural audit CLI (STEP 1; read-only; first execution candidate)

- New `lazy record-structure-audit` (script `record-structure-audit.ts`), read-only, deterministic:
  - surface-term coverage (aliases/surfaceTerms non-empty rate; Korean surface-term presence),
  - reachability: connected components over in-file links (canonical + planning/plans/knowledge scopes), orphan list (baseline: 13 canonical),
  - link density distribution; same-topic scatter (feature membership vs link presence),
  - graph.jsonl schema-generation census (drift quantification).
- Output: JSON + md, becomes the BEFORE baseline for every later step.
- Validation: self-test check for schema/exit codes; numbers reproduced twice.

### W2 — Backlink derivation + surface (C1; decision converged: derived, not in-file)

- Generator: `generated/backlink-index.json` derived from (a) in-file forward links, (b) graph.jsonl edges (normalize all 3 schema generations).
- Surface: record-map drill-down gains "Referenced by" section reading the generated index; stale/missing → fallback note.
- Protocol: walking grammar addition — "on entering a record, `grep -rl <its-path>` when index absent/stale" (AGENTS pointer + purpose-scoped-retrieval SDD).
- Retroactive for free: forward links already exist → one generation covers all 229 records.
- Validation: orphan count from W1 reproduced by generator; drill-down shows inbound for known cases (e.g. TimSquad plan record).

### W3 — Storage rules codification (C2+C3 + Karpathy borrowings; requires 1 new ADR)

- New ADR: memory-device storage discipline — (1) surface-term rule (two sources: observed user vocabulary harvested as it occurs + LLM-generated variants; coverage lintable, quality validated by use), (2) cross-link/reachability rule (same-topic pieces must link so any entry reaches all; acceptance = reachability), (3) backlinks stay derived (never hand-stored), (4) optional `confidence/contested` markers for weak claims (borrowed from hermes implementation), (5) index scale thresholds precedent (50/200 split rules) noted for future.
- Contract updates: record-digest-format (activate Aliases/Surface terms; add optional confidence/contested), record-write-update-policy (write-time surface-term + cross-link obligations), record-lint (ADVISORY-level checks first: missing surface terms on new/updated records, orphan warning — NOT commit-blocking until dogfood evidence, per ADR 0016 philosophy and roadmap hard-guard pause).
- Backfill policy: not bulk — priority by walk frequency (features with most drill-downs first), using W1 numbers.

### W4 — Retro loop MVP (C6; absorbs retro-loop-first proposal Phase 1)

- As previously specified (`lazy retro feedback` L1/L2/L3 → feedback.jsonl; `lazy retro report` KPT + 3-repeat deterministic pattern detection; option-gate promotion) PLUS two roles from this discussion: recall-failure capture (misses/partial syntheses as feedback class) and user-vocabulary harvest (feeding W3 surface terms).
- Data sources exist: validations.jsonl, hook-timings, logs/skipped.jsonl; storage `.lazy-harness/retrospective/`.

### W5 — Scenario replay eval (C5; needs user-vetted gold set)

- Gold set: 10–20 situation scenarios (real utterance + context) × 2–3 paraphrase variants; user vets expected evidence sets. Specimen #1: 2026-07-04 TimSquad miss (4-piece set).
- Runner: fresh-context subagents replay; score evidence-set recall (③), cross-phrasing consistency (②), completeness self-awareness.
- Before/after: re-run over W2/W3 changes to prove effect; doubles as R1-class evidence.

### W6 — Digest-tier JIT loading (C7; conditional, after W5 baseline)

- Drill-down returns digest tier before bodies; body escalation rule mandatory (recall > economy). Projected ~48% additional saving. Only after W5 confirms no recall regression path.

### W7 — Evidence-gated follow-ups (unchanged from final report)

- Stop-deny narrow gate, contradiction lint, conditional review triggers, heterogeneous-host expansion, FTS-as-recall-net reconsideration — each behind its own option gate, triggered by W4/W5 evidence.

## Sequencing and rationale

W1 (audit, days) → W3-ADR + W2 (rules + backlinks, ~1wk) → W4 (loop MVP, 1–2wk) → W5 (replay, after gold set) → W6/W7 conditional.
Rationale: measure before rules (graph-CLI-rollback lesson); backlinks are free retroactively so early; loop starts feeding surface terms before backfill scales; replay proves the whole chain. Each step produces the next step's input.

## Invariants (unchanged)

Canonical MD; typed layers; no self-built semantic search (ADR 0024 — delegated safety net only as W7 evidence-conditional); dev-time advisory (ADR 0016); discovery complete+lean (ADR 0049); every promotion user-gated; no new external deps (ADR 0013).

## Open decisions (option gates due at execution time)

1. W2 surface detail: extend record-map.ts vs separate `lazy backlinks` CLI.
2. W3 lint level: advisory-only start (recommended) vs immediate commit-gate for new records.
3. W5 gold-set sourcing: past sessions (retroactive judgment) vs user-authored now vs 2-week live collection (= W4 overlap).
4. graph.jsonl schema drift: normalize-in-consumers only vs one-time migration (graph-hygiene decision).

## Validation criteria (plan-level)

- W1 numbers published and reproducible; W2 orphan parity with W1; W3 ADR + contracts lint-clean and self-test green; W4 E2E one pattern promoted via option gate; W5 baseline scored on ≥10 scenarios; every step closes with an evidence capsule.

## Discovery capture

- DDD: none new (taxonomy already recorded in holistic review).
- SDD: candidates listed in W3 (digest-format/write-policy/record-lint changes) — created only on W3 approval.
- BDD: none.
- TDD: candidate — W1/W2 self-test checks; W5 gold set becomes regression corpus.
- ADR: candidate — W3's memory-device storage discipline ADR (single new ADR for the whole plan).
- SSOT: none.
- Planning: this record; absorbs retro-loop-first proposal (marked below).

## Rule placement

- Rule: implementation of the memory-device design proceeds measure-first (W1) with per-step option gates; storage rules land as one ADR + contract updates; backlinks remain derived data.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/memory-device-implementation-plan.md`
- Why not AGENTS.md: implementation plan, not per-turn grammar.
- Confirmation: plan authoring user-approved 2026-07-04; per-step execution approval pending.

## W1 result — baseline published (2026-07-04)

Status: W1 implemented and measured. CLI: `lazy record-structure-audit [--format=json|md]` (`.lazy-harness/scripts/record-structure-audit.ts`, read-only; dispatcher wired in `bin/lazy`). Determinism verified: two consecutive JSON runs byte-identical (modulo generatedAt).

Baseline numbers (canonical=160, extended docs=67):

- Surface terms: aliases 0/160 (0%), surface-terms 0/160 — contract fully unused, as suspected; 59 records contain Korean text incidentally (not as deliberate bait). → W3's main content gap confirmed and quantified.
- Reachability: TRUE orphans = 4 (earlier rough count of 13 shrank once planning/plans/knowledge inbound links counted — scatter helps reachability): 0038-requirements-first-change-gate.md, spec/platform/graph-hygiene.md, spec/platform/sdd-component-contract-trigger.md, tests/todo-reminder-loop-and-stream-utf8-invalid.md. Zero-outbound = 1. Connected components = 9 (largest 216/227; 6 isolated docs).
- Link density: avg 4.22 outbound, p50=4, p90=7, max=15 — healthy forward-link core confirmed.
- graph.jsonl census: 658 rows, 4 generations — source-relation-target 376, subject-relation-target 186, subject-predicate-object 54, UNKNOWN 42 (rows matching no known generation — worse than the 3-generation estimate; W2 normalizer must handle 4 shapes + unknowns, and graph-hygiene owns the cleanup decision).

Interpretation: corpus is one big walkable component (216/227) with a small repair list (4 orphans, 6 isolated docs) — W2 backlinks + a handful of link edits close reachability; the dominant gap is surface-term content (0%), confirming W3 as the heavy-lift item.

### Discovery capture (W1)

- TDD: candidate — self-test check for audit schema/exit code (add with W2 or W3 slice to batch commit-gate changes).
- SDD: none yet (CLI contract documented here; formal SDD when W3 lands).
- Planning: updated — this section.
- DDD/BDD/ADR/SSOT: none.

## W2+W3 result — implemented (2026-07-04)

Status: W2 and W3 landed in one slice, user-approved ("좋아 진행해봐"). Reserved option gates resolved from record evidence without re-asking (§2.3): W2 surface = map drill-down extension (holistic-review convergence), W3 lint level = advisory-first (this plan + roadmap hard-guard pause).

Delivered:

- ADR 0053 `memory-device-storage-discipline` — surface-term rule (2 sources), reachability acceptance, derived-backlink principle, optional Confidence/Contested markers, advisory-first enforcement. Added to init-categories operational-adrs allowlist (self-test D-gate caught the dangling-ref risk; README/handoff ADR counts bumped to 53).
- W2: `lazy backlink-index` (`scripts/backlink-index.ts`) → `generated/backlink-index.json` (derived, rebuildable; forward links + graph.jsonl all schema generations). `lazy map <record>` drill-down now renders `referenced by:` (record-map.ts `loadBacklinkEntries`). Verified: W1 orphan parity 4/4; TimSquad plan shows correct inbound.
- W3 contracts: record-digest-format (+Confidence/Contested optional fields; aliases activated as default expectation for new/updated records with backfill-by-walk-frequency note), record-write-update-policy (+grep-bait and cross-link write obligations), record-lint.ts (+`advisory-missing-surface-terms`, new `advisories[]`/`advisoryCount` — never exit-affecting), record-lint SDD (+advisory tier §7, JSON shape) and TDD record (+assertion 8).
- Validation evidence: `record-lint --fail-on-issues` exit 0, issues 0, advisories 160/161 (only ADR 0053 carries Aliases — the backfill baseline); `record-structure-audit` aliases=1, orphans=4 unchanged; framework self-test GREEN 84/84 (incl record-lint cli + operational-adrs allowlist).

Next: W4 retro loop MVP (per plan; approval pending) — backfill of surface terms proceeds organically via W4's vocabulary harvest plus walk-frequency priority, not bulk edits.

## W4 result — implemented (2026-07-04)

Status: W4 landed, user-approved. Loop is live with real data.

Delivered:

- `lazy retro feedback|report|resolve` (`scripts/retro.ts`, dispatcher wired): L1/L2/L3 classified feedback with deterministic `kind` signatures → `retrospective/feedback.jsonl`; KPT report + 3-repeat pattern candidates → `retrospective/retro-<date>.md`; resolve closes entries after user-gated promotion. CLI never promotes (cli-tool-boundary); no semantic matching (ADR 0024 §2); no auto-apply (TimSquad improve principle).
- SDD contract: `.lazy-harness/spec/platform/retro-loop.md` — first record authored under the new ADR 0053 surface-term rule (carries Aliases: 회고 루프/retro loop/실패 패턴/KPT/...). Graph ids: kg_retro_loop_cli_20260704, kg_retro_loop_contract_20260704.
- Real seed data (this session's documented failures, honest counts): premature-execution ×2 (L2), recall-miss-synthesis ×1 (L2, vocab harvest: 팀스쿼드/하네스 비교/timsquad). First report generated; threshold honest (2<3 → no pattern candidate yet — premature-execution promotes at its 3rd occurrence via option gate).
- Validation: lint 0 issues / 160 advisories / 162 inspected; framework self-test 84/84 GREEN; backlink index rebuilt.
- Evidence capsule: `.lazy-harness/evidence/2026-07-04-memory-device-w1-w4.md` (W1–W4 commands/results/interpretation/reproduce).

Deferred (recorded): self-test checks for the three new CLIs (audit/backlink/retro) — batch as one commit-gate slice; W5 replay eval next (needs user-vetted gold set); surface-term backfill proceeds organically (vocab harvest + walk-frequency priority).

## W8 — Full-corpus re-review backfill (policy changed 2026-07-04, user decision)

Status: approved-direction; execution via guided skill, batch-by-batch user checkpoints.

- Policy change: supersedes W3's "not bulk — walk-frequency priority" line. User chose full re-review over organic-only backfill at the 2026-07-04 option gate; ADR 0053 amended accordingly (see its Amendment section for preserved safeguards and accepted risk).
- Scope: all canonical records (161 at amendment time; advisory queue = `lazy record-lint` advisories, currently 160) get surface terms; reachability repairs target the audit's orphan/isolated lists; Confidence/Contested markers added where claims are weak/conflicting.
- Vehicle: `lazy-memory-backfill` skill (`packages/lazy-harness-pi/skills/lazy-memory-backfill/`), lazy-record-quality precedent: read-only evidence in (record-lint advisories + record-structure-audit + vocab harvest queue) → batch proposal (5–10 records) → user review → apply → re-run audits → progress via advisory count decrease.
- Ordering inside the full sweep: walk-frequency/importance still orders BATCHES (map-frequent and feature-core records first); the change is that coverage no longer stops there.
- Done when: advisory-missing-surface-terms count reaches 0 for canonical records and reachability audit shows no orphans; then (separate option gate) consider promoting the advisory to a commit-gate check for NEW records.

### W8 batch log

- Batch 1 (2026-07-04, user-approved proposal): core-6 aliases (ADR 0016/0024/0049, digest-format, write-update-policy, record-lint SDD) + orphan repairs (0038←0019, graph-hygiene←progressive-knowledge-graph, sdd-component-contract-trigger←layer-completeness-gate, todo-reminder-loop←bdd-trigger reciprocal + full-path ref fix; jcode-era TDD already needs-review, left demoted). Results: advisories 160→151, orphans 4→0, aliases coverage 1→11, lint 0 issues.
- Batch 2 (2026-07-04, user-approved): retrieval/rule-recall cluster aliases — 0045 + purpose-scoped-retrieval SDD/BDD/DDD/TDD, cli-tool-boundary, 0041, search-read-debt-contract, project-rule-router, llm-owned-record-retrieval. Results: advisories 151→141, coverage 11→21, orphans 0 maintained, lint 0 issues.
- Batch queue (next candidates, proposal pending user review per batch): Batch 3 = capability/policy cluster (0040, 0046, 0048, capability-resolution, policy-registry, rule-sources, project-operating-rulebook spec/tests, capability-registry ssot/tests). Batch 4+ = implementation-map/graph cluster (0028/0030, implementation-map-standard/migration, knowledge-graph-storage, graph records), then lifecycle/gate cluster (0016-adjacent: 0019/0033/0035/0038 remainder, layer-completeness, interview-loop records), then long tail by remaining advisory list. Progress tracking = advisory count (141 remaining ≈ 14 batches).
- Batch 3 (2026-07-04, user-approved): capability/policy operating-rule cluster aliases — 0040/0046/0048, capability-resolution, policy-registry, rule-sources, project-operating-rulebook spec+tests, capability-registry ssot+tests. Results: advisories 141→131, coverage 21→31, orphans 0, lint 0.
