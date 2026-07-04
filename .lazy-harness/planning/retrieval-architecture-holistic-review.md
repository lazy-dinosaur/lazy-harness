# Retrieval Architecture Holistic Review

Status: active
Date: 2026-06-08
Layer: Planning
Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/record-index-header.md`
Related SDD: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
Related Planning: `.lazy-harness/planning/graph-index-migration-considerations.md`
Related Planning: `.lazy-harness/planning/jcode-graph-memory-tool-integration.md`
Related SSOT: `.lazy-harness/ssot/implementation-map-storage.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: framework-global
- Applies when:
  - evaluating whether `lazy map --overview` should be a hard sequential gate, soft guidance, or prompt/reminder context
  - Graphify adoption evaluation: vendoring Graphify code vs porting Graphify principles
  - prototype-sized implementation vs big-change boundary for graph query rollout
  - comparing current `record-map` shallow candidate retrieval with Graphify-style graph query/path/explain traversal
  - deciding whether to adopt Graphify by vendoring code or porting its principles
  - deciding whether batching is safe for overview/query/read workflows
  - deciding whether overview text should be injected into reminders instead of forcing another tool call
- Must:
  - preserve canonical record/source/test reads before semantic reliance
  - treat generated indexes and Graphify-style outputs as cue-only/non-canonical
  - distinguish local CLI latency from LLM token/context savings
  - evaluate dogfood friction, not only theoretical correctness
  - consider a soft/depth-aware workflow before keeping a hard batch block
  - prefer porting Graphify principles into TypeScript/Bun before considering wholesale Python vendoring
  - keep the first `lazy graph query` slice additive/read-only before changing lifecycle or batch policy
- Must not:
  - forget the user concern that hard-blocking batch may be low value if the workflow is still shallow
  - inject full graphs or full overview into every prompt without measuring token cost
  - make Graphify or generated index canonical truth
  - block useful parallel reads chosen after enough context is available
- Record completion:
  - final decision updates BDD, SDD, TDD, SSOT/ADR if needed, helper source, self-test, sync manifest if downstream behavior changes.

## User-confirmed concerns to preserve

The user asked not to forget these points:

1. The current approach may be too shallow: it shows an index/overview and then asks the agent to manually choose tokens, rather than letting the system traverse deeply.
2. Hard-blocking `batch` around overview may not help much if agents can still do suboptimal sequential searches afterward.
3. It may be better to include a compact overview/reminder in the prompt rather than forcing a separate overview tool call every time.
4. Graphify should be considered as a reference for how to solve this: persistent generated graph, query/path/explain/MCP tools, compact subgraph output, cache/watch behavior.
5. The goal is not just rule compliance; the flow must be practically faster, lower-token, and less annoying while still safe.

## Current state assessment

### Graphify adoption note

- Graphify clone verification already read source at commit `8a04560bf5d5eaeef8e466bce084270b7f68faae`.
- License is MIT, so copying/adapting is legally permissive if copyright/license notice is preserved.
- Package is Python (`graphifyy`, CLI entrypoint `graphify = graphify.__main__:main`, `requires-python >=3.10`), while lazy-harness core tooling is TypeScript/Bun.
- Therefore the preferred first implementation is **port the principles and data flow**, not wholesale vendoring:
  - persistent generated graph/cache,
  - query/path/explain commands,
  - compact cited subgraph/context output,
  - stale/missing fallback to canonical records/source/tests,
  - generated/non-canonical boundary.
- Direct vendoring remains possible later, but should be a separate ADR because it introduces Python runtime/dependency/package maintenance into lazy-harness.

### What is working

- `record-index` builds a deterministic, rebuildable cache over record metadata and graph hints.
- `lazy map --overview` gives whole-structure inventory.
- `lazy map <term>` gives 1-hop matches plus drill-down candidates.
- `retrieval-audit` exposes structural gaps and related layer candidates.
- Cross-layer related records now surface DDD/BDD/SDD/TDD/SSOT candidates.
- Downstream sync currently carries retrieval/index foundation records and the overview batch guard.

### What is weak

- `record-map` is mostly **1-hop cue aggregation**:
  - matched records,
  - related records,
  - source/test hints,
  - graph row fields.
- It does not yet implement Graphify-style deep traversal:
  - no `path A B`,
  - no `explain node`,
  - no BFS/DFS subgraph expansion from seed nodes,
  - no scored context packet with citations,
  - no persistent query service/MCP tool.
- The overview-first hard guard protects order, but may be over-strict if a better architecture provides enough context up front or a query tool can expand from seed terms safely.
- Reminder injection of full overview would cost tokens; a compact inventory digest or dynamic packet may be better than full overview text.

## Options under consideration

### Option A — Keep hard sequential overview guard

Pros:

- Strictly preserves current record-first protocol.
- Prevents obviously premature dependent queries.

Cons:

- Dogfood friction is high.
- Does not solve shallow traversal.
- Agent may still perform inefficient sequential calls.

### Option B — Replace hard block with soft warning / post-turn lint

Pros:

- Allows practical parallelism.
- Still records misuse through response.completed or doctor/self-test.

Cons:

- Allows mistakes during the active turn.
- Requires strong final verification to catch missed layers.

### Option C — Compact overview packet in reminder + allow batching

Pros:

- Agent has initial inventory without a tool call.
- Reduces need for hard block.
- Could allow dependent query planning in one batch because the overview is already available.

Cons:

- Adds prompt tokens every turn.
- Needs token budget/quality measurement.
- Must stay cue-only and avoid semantic authority.

### Option D — Graphify-style query/path/explain tool first, then relax overview guard

Pros:

- Addresses the real weakness: shallow traversal.
- Tool returns compact cited subgraph/context from a persistent generated memory.
- Can support `query`, `path`, `explain`, `neighbors`, and stale-safe fallback.

Cons:

- More implementation work.
- Needs schema/version/stale tests.
- Must preserve generated/non-canonical boundary.

## Recommended direction

Recommended: **D + C, then reassess B**.

1. Build a Graphify-inspired internal query tool over existing record-index/graph/generated implementation index:
   - `lazy graph query <text>` or `lazy index query <text>`
   - `lazy graph explain <node-or-path>`
   - `lazy graph path <from> <to>`
   - output compact cited subgraph/context packet
2. Add a compact overview digest to reminder or lifecycle packet, not full overview.
3. Completed follow-up on 2026-06-09 after user-confirmed policy audit: the hard overview-batch denial was retired into a compatibility no-op, while mutation safety remains in the generic search/read evidence guard.

## Scope sizing

The next step should be treated as a **prototype-sized implementation**, not the full architecture migration.

### Prototype-sized / safe first slice

- Add a TS/Bun CLI over existing generated/canonical inputs, e.g. `.lazy-harness/scripts/graph-query.ts`.
- Add `lazy graph query <text>` first.
- Use existing inputs only:
  - `.lazy-harness/knowledge/graph.jsonl`,
  - `.lazy-harness/generated/record-index.json` or fresh `record-index.ts` rebuild,
  - `.lazy-harness/generated/implementation-index.json` when present.
- Output a compact cue-only cited context packet.
- Do not change lifecycle policy yet.
- Do not remove `lazy map` or `retrieval-audit`.
- Do not vendor Graphify/Python.

This first slice is **medium-small** because it is additive, read-only, and can be guarded by self-test without changing agent policy.

### Big-change boundary

It becomes a large architectural change only when one of these happens:

- Replace overview-first policy with graph-query-first policy.
- Reintroduce any hard block for read-only overview batching.
- Inject compact overview/graph packets into every reminder/prompt.
- Add a persistent daemon/MCP server.
- Vendor Graphify or introduce Python/Go/Rust runtime dependencies.
- Make generated graph output influence semantic authority instead of remaining cue-only.

Therefore: implement `lazy graph query` as an additive TS/Bun prototype first, benchmark it, then decide whether the larger policy/runtime change is justified.

## Evaluation plan

1. Measure prompt overhead of a compact overview packet vs full `lazy map --overview`.
2. Prototype a `lazy graph query` over existing `knowledge/graph.jsonl`, record-index, and generated indexes.
3. Compare three flows on real tasks:
   - current hard overview-first flow,
   - compact reminder overview + batched follow-up,
   - graph query/path/explain + minimal reads.
4. Metrics:
   - input tokens,
   - tool call count,
   - local latency,
   - missed DDD/BDD/SDD/TDD/SSOT layers,
   - user-visible friction,
   - false block rate.

## Implementation map

- Status: planned
- Primary files:
  - `.lazy-harness/scripts/record-map.ts` — current 1-hop overview/drill-down CLI.
  - `.lazy-harness/scripts/record-index.ts` — generated record/source cache.
  - `.lazy-harness/scripts/retrieval-coverage-audit.ts` — structural coverage audit.
  - `.lazy-harness/hooks/lifecycle/helpers/check-overview-batch-order.py` — retired compatibility no-op for the old hard batch guard.
  - `.lazy-harness/planning/graph-index-migration-considerations.md` — Graphify source-verified constraints.
  - `.lazy-harness/planning/jcode-graph-memory-tool-integration.md` — graph memory tool concept.
  - future `.lazy-harness/scripts/graph-query.ts` or `.lazy-harness/scripts/index-query.ts` — deep query/path/explain prototype.
- Key observations:
  - `record-map.ts#buildDrilldown` collects 1-hop related/source/test/graph ids only.
  - Graphify source implements persistent graph outputs, cache, MCP query tools, BFS/DFS-like context rendering, and advisory assistant hooks.
- Tests / protection:
  - current `check_tool_execute_before_hook` protects hard overview guard.
  - future tests should cover compact overview packet token budget, graph query citations, path/explain output, stale index fallback, and false block rate.
- Machine index:
  - graph ids: pending until prototype/decision.

## Discovery capture

- DDD: none yet; existing `searchable-record-memory` terms apply.
- SDD: candidate deep graph query/path/explain contract needed.
- BDD: candidate revised retrieval behavior needed for compact overview / graph query / parallel-safe workflow.
- TDD: candidate tests for false block rate, compact overview token budget, graph query citation/path/explain, and stale fallback.
- ADR: likely required if changing from hard overview guard to soft/depth-aware policy.
- SSOT: generated/non-canonical boundary remains `implementation-map-storage`; may need a new SSOT for reminder packet contents.
- Planning: this file captures the current open design review and user concerns.

## Rule placement

- Rule: The open question is not whether to ignore record-first behavior; it is whether record-first should be implemented as hard sequential overview, compact reminder context, or Graphify-style query/path/explain traversal.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/retrieval-architecture-holistic-review.md`
- Why not final BDD/SDD yet: user has not chosen the policy; current content is a planning review and design option set.
- Confirmation: user-requested holistic review, pending final option decision.

## Measured evidence — 2026-07-04 storage/retrieval economics spike (user-approved)

Status: measured-evidence
Method: `lazy retrieval-workflow-benchmark --format=json` (4 feature queries) + digest/body token census over all 160 canonical records + fresh overview size. Rough token estimate = chars/4. Read-only.

### Findings

1. Cost concentration: map-first total 345,325 est tokens for 4 tasks; helper (map) calls are only 34,487 (10%) — **90% of retrieval cost is the 129 follow-up full-body record reads (310,838 tokens)**. The storage format is not the bottleneck; full-body loading is.
2. Digest tier is ready and unused: 160/160 canonical records now carry `## Rule digest` (100% coverage); digest averages 312 est tokens vs 1,957 full-body — **digest = 16% of body**.
3. Projected saving from digest-first JIT loading (read digest, load body only when the task needs it): upper bound followups 310,838 → ~49,700 (digest-only); realistic (~1/3 of records still need full body) ≈ 180k total ≈ **~48% further reduction on top of the existing 77% vs grep**. No storage format change required.
4. Overview surface: 8,454 est tokens per `--complete` call (28,194 chars, 276ms). ADR 0049 keeps it complete+lean; prompt injection vs tool call changes latency/compliance, not tokens.
5. `map_plus_retrieval_audit` adds ~13k tokens over plain map for the same coverage — the audit surface is not the lever.
6. no_map (grep-everything) control: 1,532,064 tokens — map-first stays 77% cheaper, consistent with the 2026-06-26 measurement.

### Conclusion (proposed, pending user direction)

- Canonical MD storage stays (ADR 0013/0024/0027/0030 rationale intact); the economic lever is **digest-tier JIT loading** — a workflow/CLI change (e.g. drill-down returning digests before bodies), which is precisely what record-digest-format designed digests for and what ADR 0049 calls targeted loading.
- Graphify-style query/path/explain remains the deeper second step (compresses which records to touch); FTS/vector storage experiments are not justified by these numbers.

### Discovery capture

- DDD/BDD/SSOT: none.
- SDD: candidate — digest-tier loading would extend `purpose-scoped-retrieval.md`/`record-index-header.md` contracts when approved.
- TDD: candidate — digest-first flow needs a benchmark regression once implemented.
- ADR: none new; operates within ADR 0049.
- Planning: updated — this section.

## User-confirmed requirement — 2026-07-04 (LLM-as-middle-layer memory device)

Confirmation: user-confirmed (ADR 0032 same-turn convergence). This REORDERS the evaluation criteria for all retrieval/storage options in this record:

1. Records are a MEMORY DEVICE attached to the LLM; the LLM is the middle layer. Human readability of the storage format is NOT a requirement (a human asks the LLM to search and report; verification happens on the report, not the raw file).
2. Priority 1 = accurate, lossless storage. Priority 2 = complete recall — when retrieving, NOTHING relevant may be missed ("놓치는 것 없이").
3. Economy (token cost) remains a factor but is subordinate to (1) and (2).

Implications recorded:

- Canonical MD stays, but its justification shifts from human readability to: lossless text, git history, deterministic lint/validation (record-lint), and zero-dependency portability (ADR 0013/0027). Format migration remains possible if (1)/(2) ever demand it.
- Digest-tier JIT loading (2026-07-04 spike conclusion) gains a design constraint: digest-first must not cause body-miss — need an escalation rule for when digest is insufficient.
- Derived FTS/embedding indexes are re-scoped: rejected as economy measures, but OPEN as recall safety nets (lexical FTS is not a custom semantic algorithm; semantic recall would still go through SearchProvider delegation, ADR 0024 §2).
- Known recall-failure evidence: 2026-07-04 TimSquad first-pass summary miss — cause was scattered same-topic knowledge (plans/, candidates.jsonl, ADR mentions) + synthesis skip, NOT storage format. Countermeasures ranked: alias/surface-term digest metadata (contract exists, unused), same-topic graph edges, synthesis-completeness check.

### Discovery capture

- DDD: candidate — "memory device / LLM middle layer" framing may deserve a domain concept entry if it recurs.
- SDD: candidate — recall-completeness acceptance criteria for retrieval surfaces (purpose-scoped-retrieval.md) when a track is approved.
- BDD/TDD/ADR/SSOT: none yet.
- Planning: updated — this section.

## Discussion synthesis — 2026-07-04 recall-completeness decomposition (in progress)

Status: discussion-in-progress (no execution decision; user explicitly held this at discussion stage)

"놓침 없는 recall" decomposes into three distinct failure points:

1. Discovery miss — record absent from the inventory list. Structurally solved: ADR 0049 mandates complete, untruncated overview (all 229 records always listed).
2. Bridging miss — record listed but not CONNECTED to the question (user vocabulary vs record naming, Korean↔English, aliases). Weak point #1; the digest Aliases/surface-terms contract exists but is unused in practice.
3. Synthesis miss — some related records read, partial set reported as complete. Weak point #2; live specimen = 2026-07-04 TimSquad first-pass summary miss (topic scattered across plans/, candidates.jsonl, ADR mentions). No mechanism tells the LLM "this topic has N pieces total".

Guarantee strategies discussed (maps 1:1 to the two open development tracks):

- Structural guarantee — same-topic graph edges so finding one piece pulls the rest (deterministic; depends on edge diligence at write time) → graph/record infrastructure track.
- Loop guarantee — recall failures captured as feedback and reinforced against recurrence (probabilistic; self-improving) → retro-loop track.
- Likely answer is the combination: structure for storage-time linkage, loop for residual failures.

LLM-middle-layer tension noted: recall passes through probabilistic LLM judgment each query, so storage alone cannot guarantee "no miss"; structural aids and/or verification loops are required.

Open question to user (discussion resumes here): which miss scenario drives the concern — ② bridging, ③ synthesis, or an unlisted class?

### Discovery capture

- DDD: candidate — miss-class taxonomy (discovery/bridging/synthesis) may become domain vocabulary if adopted.
- SDD/BDD/TDD/ADR/SSOT: none yet (discussion stage).
- Planning: updated — this section.

### 2026-07-04 recall measurement methodology (discussion, user leaning ② or both)

User intuition: bridging (②) primary, possibly both; asked how to verify/prove/measure. Proposed design (not approved for execution):

- Gold sets exist already: past-session real queries ↔ eventually-read/corrected records (② pairs); 2026-07-04 TimSquad miss = confirmed ③ specimen #1 (gold = 4 pieces across plans/retrospective/candidates/ADR mentions; first report = 2).
- Stage 1 — deterministic structural-readiness audit (no LLM, cheap): alias coverage over 160 canonical records (likely ~0%, contract unused), Korean surface-term presence, orphan-topic rate (Related-records text links lacking graph edges), piece-scatter degree per feature. Measurable today read-only.
- Stage 2 — gold-set replay eval (LLM-in-the-loop, Inspect/DeepEval Task/Dataset/Scorer shape): 10–20 user-vetted query↔record-set pairs; fresh-context subagent runs map-first retrieval; score piece-recall (③), bridge-rate (②), and completeness self-awareness (did it claim "all" while partial — the real harm of ③ is not-knowing-what-was-missed). Re-run same set before/after improvements to prove effect (e.g. alias seeding → bridge-rate delta).
- Side effects: building the ③ gold set IS the repair (confirming "all pieces of topic X" = graph edge backfill); replay-discovered misses feed the retro loop as its first data source.

### Discovery capture

- TDD: candidate — gold-set replay becomes a regression corpus once built.
- SDD: candidate — scorer/metrics contract if approved.
- DDD/BDD/ADR/SSOT: none yet.
- Planning: updated — this section.

### 2026-07-04 measurement-unit correction (user): no query layer exists — the LLM is the searcher

User correction to the measurement design above: lazy-harness has no "query" as a first-class thing; the LLM translates the user's want (expressed many ways) into search behavior. Consistent with ADR 0024/0045 (no query-helper authority; LLM-owned retrieval).

- Measurement unit corrected: NOT query-string → results, BUT user-utterance + conversational context → the LLM's whole retrieval behavior → evidence set reached.
- Gold set shape corrected: situation SCENARIOS (real utterance + context), each with 2–3 paraphrase variants — adds a new metric dimension: paraphrase robustness (same intent, different wording, same evidence set?). This is the true measurement of bridging (②).
- Structural aids (aliases, graph edges) are cues FOR THE LLM, so their value is measured as LLM behavior change (before/after seeding), not index ranking.
- Eval structure: scenario replay by fresh-context subagents; score evidence-set recall (③), cross-phrasing consistency (②), completeness self-awareness.
- First gold specimen stands: 2026-07-04 "다른 하네스 조사 확인" scenario, expected 4-piece set, observed 2.

### Discovery capture

- DDD: candidate — "scenario/paraphrase robustness" may join the miss-class taxonomy vocabulary.
- SDD/BDD/TDD/ADR/SSOT: none yet (discussion stage).
- Planning: updated — this section.

### 2026-07-04 convergence (user-confirmed): storage discipline IS the retrieval infrastructure

User: the LLM-searcher may use tree/bash/grep/fuzzy-finder — any tool; what makes retrieval possible is storing things well BY RULE. Tools can only find what is written in the files.

Storage-rule → retrieval-affordance mapping (discussion consensus):

1. Location rules (layer folders, predictable names) → tree/ls discovery → prevents ① discovery miss.
2. Surface-term rules (user vocabulary / Korean aliases PRESENT IN FILE TEXT) → grep/fuzzy bridging → prevents ② bridging miss. Alias metadata's essence = grep bait, not index optimization; if no record contains "메세지", no tool can bridge it.
3. Cross-link rules (same-topic pieces reference each other: Related records + graph edges) → one hit pulls the rest regardless of tool → prevents ③ synthesis miss.
4. Format rules (uniform digest) → cheap skim + targeted deep read → economy.
5. Lint enforces 1–4 → discipline survives time (record-lint already enforces format; surface-term/cross-link rules are the same enforceable class).

Consequence: "did we store well" becomes a DETERMINISTIC audit (surface-term coverage, cross-link rate, location conformance) — sharper definition of the Stage-1 structural audit above.

Honest residual: storage discipline is necessary, not sufficient — a perfectly stored corpus still misses if the LLM doesn't search (trigger) or partially synthesizes (2026-07-04 TimSquad case: fully stored, partially reported). Residual failures belong to the loop (retro). Final frame: storage discipline = structural guarantee; loop = residual recovery.

### Discovery capture

- SDD: candidate — surface-term/cross-link storage rules could become record-write-update-policy or record-lint extensions when the discussion concludes.
- DDD: candidate — miss-class taxonomy keeps stabilizing (discovery/bridging/synthesis; bait; structural vs loop guarantee).
- BDD/TDD/ADR/SSOT: none yet.
- Planning: updated — this section.

### 2026-07-04 user vision (confirmed): traversal-based retrieval — walk the links like a human

User's target retrieval model: NOT bulk multi-fetch; documents are interlinked (graph-like, backlinks, related docs). Flow = tree for structure (cheap) → read one entry document → find related links INSIDE it → follow deeper → repeat — like a human browsing folders and following references. Pay-per-hop token economics: load only what the path demands; unrelated documents never appear on the path.

- Alignment: this is the concrete execution shape of ADR 0049 (complete+lean discovery = tree role; JIT targeted loading = per-hop reads). Obsidian/wiki backlink-navigation pattern.
- Gap analysis against current corpus:
  - whole-structure view: EXISTS (lazy map --overview / tree);
  - outgoing links: EXIST (Related records, Implementation map, cross-layer links) but uneven density;
  - BACKLINKS: MISSING in files — graph.jsonl knows some reverse edges but records do not surface "who links here", so entering a topic via a downstream piece cannot walk upstream (2026-07-04 TimSquad case: entry via ADR mention could not reach plans/);
  - link completeness: partial (same-topic unlinked pieces exist).
- Measurement consequence (sharpest yet): REACHABILITY AUDIT — from any piece of topic X, following only in-file links, what % of the topic's pieces are reachable? Deterministic (connected-component analysis over in-file links), no LLM needed. This becomes the final acceptance criterion for "stored well".

### Discovery capture

- DDD: candidate — traversal/backlink/reachability joining the taxonomy.
- SDD: candidate — backlink materialization rule (in-file "referenced by" or generated backlink index) if the vision is adopted as requirement.
- BDD/TDD/ADR/SSOT: none yet.
- Planning: updated — this section.

### 2026-07-04 refinement (user-confirmed): surface terms are authored by the LLM

User correction: surface terms ARE decided by the LLM. This resolves an earlier overstatement in this discussion (that LLM-invented aliases would be fabrication): aliases are retrieval AFFORDANCES, not factual claims about the host — and under the memory-device frame, records are written BY the LLM FOR the LLM, so the LLM is best placed to predict what its future self would grep for.

- Two supply sources for surface terms:
  1. observed user vocabulary — real utterances harvested from conversation (highest-value bait; capture as they occur);
  2. LLM-generated variants — synonyms, Korean↔English, abbreviations, predicted future-grep terms (legitimate LLM authorship; no per-item user confirmation needed).
- record-digest-format's "confirmed aliases" caution applies to source 1 (do not misattribute user vocabulary), not a prohibition on source 2.
- Consequence: write-time quality varies by model/session → lint can enforce PRESENCE (coverage) only; QUALITY is validated by actual use (replay eval / loop — whether the bait actually gets bitten).

### Discovery capture

- SDD: candidate — surface-term authorship rule (two sources, coverage-lint, quality-by-use) folds into the eventual storage-rules contract.
- DDD/BDD/TDD/ADR/SSOT: none yet.
- Planning: updated — this section.

### 2026-07-04 external convergence: Karpathy's LLM Wiki pattern (user-raised, web-verified)

User asked whether this discussion's direction matches Andrej Karpathy's LLM Wiki idea. Web-verified (2026-07-04): Karpathy's pattern = LLM compiles raw sources into a persistent, interlinked markdown wiki and NAVIGATES it by following links, explicitly bypassing embedding/similarity RAG (VentureBeat + multiple ecosystem implementations: karpathy-llm-wiki repos, Obsidian frameworks, hermes-agent llm-wiki skill).

- Convergence points with this discussion / lazy-harness records: markdown substrate; LLM-authored-LLM-read (memory device frame); traversal over retrieval (tree → doc → follow in-file links); no-embeddings bet (ADR 0024's LLM-direct-search decision = same bet as "bypasses RAG"). Independent convergence by a high-signal external source = strong validation of the architecture direction chosen in 2026-05.
- Where lazy-harness goes further than the wiki pattern: typed layers (DDD/SDD/BDD/TDD/ADR/SSOT) vs untyped pages; lint-enforced storage discipline (no validator exists in the wiki pattern); confirmation provenance (user-confirmed vs candidate); lifecycle gates that FORCE lookup (wiki pattern has no trigger mechanism).
- Where the wiki pattern is ahead: bidirectional links — Obsidian-family implementations get backlinks for free; lazy-harness records lack in-file backlinks (gap already identified in the traversal-vision section above).
- Ecosystem note: multiple open-source implementations exist (karpathy-llm-wiki variants, obsidian-wiki, OpenKB, BrainDB) — candidate study references if backlink materialization is pursued; study only, no adoption implied (ADR 0052 boundary applies).

### Discovery capture

- ADR: none new — strengthens ADR 0024's bet with external validation.
- SDD: candidate unchanged (backlink materialization rule).
- Planning: updated — this section.
- DDD/BDD/TDD/SSOT: none.

### 2026-07-04 differentiation (user insight): typed layers fit development knowledge — generic wikis cannot

User point: other implementations (Karpathy-wiki ecosystem) lack project/DDD/TDD/BDD/SSOT concepts, so their storage schema is not fitted to development; since our purpose is a DEVELOPMENT harness, typed layers should yield extra advantage. Discussion sharpened this into three concrete mechanisms:

1. Directed traversal — generic wiki links mean only "related"; lazy-harness edges are TYPED (implemented_by/protected_by/decided_by), enabling purposeful walks ("go to this contract's protecting tests"), and the layer↔question mapping (§1 grammar) points to the right folder BEFORE any search — structurally reducing bridging (②) misses because developer question classes are finite and map to layers.
2. Absence detection (biggest) — an untyped wiki cannot know a page is missing; a typed schema has EXPECTED SHAPES, so gaps are detectable at write time ("bug fix without TDD record", "implementation without Implementation map") — layer completeness gate (ADR 0033) is exactly this. Typed schema is the only write-time mechanism supporting the "nothing missed" requirement; principled impossibility for the untyped wiki ecosystem.
3. Write routing — the layer table (§2.4) decides placement for new knowledge, preventing the untyped-wiki failure mode of arbitrary placement → duplication/drift.

Honest cost: typing brings layer-ambiguity friction (mitigated by option gates) and non-dev-shaped knowledge (absorbed by planning/knowledge folders). For a development harness the benefit dominates: development knowledge has recurring canonical shapes (decision/contract/flow/regression/source-of-truth/term).

Positioning consequence: vs the emerging Karpathy-wiki ecosystem (OpenKB, BrainDB, obsidian-wiki...), lazy-harness is the same architectural bet PLUS the discipline stack they lack (typed layers, lint, provenance, forced lookup, absence detection) — the borrowable piece from them remains backlink materialization.

### Discovery capture

- DDD: candidate — "typed layer advantage / absence detection" vocabulary stabilizing.
- ADR: none new; strengthens ADR 0024/0033 rationale.
- Planning: updated — this section.
- SDD/BDD/TDD/SSOT: none.

### 2026-07-04 backlink format question (user): is MD the wrong format for backlinks?

User asked whether backlinks might warrant a different format than MD. Discussion answer: backlinks are DERIVED data — computable from forward links — so this is not a canonical-format question at all.

- Key fact: with MD + forward links, backlinks are already grep-recoverable with zero infrastructure (`grep -rl <target-path>` = all referencers). Storage discipline already encodes them implicitly.
- Options weighed: (A) hand-maintained in-file "Referenced by" = anti-pattern (write amplification, stale risk, derived-data-by-hand); (B) derived backlink index in generated/ (rebuildable, always fresh, zero amplification — matches "rebuild over migration" philosophy) but needs a surface; (C) DB/graph store = overkill for computable data, conflicts with generic-tool walking; (D) walking-protocol grep ("on entering a record, grep its path for upstream") = zero infra, works today, per-hop cost.
- Proposed resolution (discussion, not approved): B + D combo — canonical MD keeps forward links only (store truth one direction; never store the derivable); backlinks materialize as a generated index surfaced through `lazy map <record>` drill-down (which already shows graph links — extend with referencing docs); D as protocol fallback that works even with stale/absent index.
- Consequence for C1 (backlink materialization change item): the in-file vs generated decision leans generated + drill-down surface + grep protocol; format inside generated/ is free (JSON etc., no lock-in since rebuildable).

### Discovery capture

- SDD: candidate — backlink derivation/surface contract folds into C1 when approved.
- SSOT: none (generated/ boundary already covers derived data).
- DDD/BDD/TDD/ADR: none yet.
- Planning: updated — this section.

### 2026-07-04 honest risk registry (user asked: "is this really the best way?")

Agent's critical self-assessment of the converged design, recorded for future falsification:

- Confident: derived backlinks (computable data must not be hand-stored); typed-layer absence detection (principled advantage for a dev harness); measure→rules→loop ordering (our own graph-CLI-rollback lesson); storage-discipline-as-infra (tool-neutral, no lock-in).
- Open risk 1 — traversal scale ceiling: walking works at 229 records; unknown at ~2,000 (per-hop token/attention cost, long chains eat context; Karpathy's wiki is personal-scale). STEP 1/4 measurements only answer for today's corpus size. Honest state: unknown.
- Open risk 2 — no-embedding bet accepts first-miss: grep only bites seeded strings; a NEVER-seen phrasing misses first time, loop fixes the next. Design = first-miss + loop-recovery, prioritizing verifiability/determinism over first-time recall. Conditional position: if replay eval shows persistent bridging (②) failures, a DELEGATED semantic safety net (SearchProvider, per ADR 0024 which bans self-built not delegated) alongside — not replacing — walking deserves reconsideration.
- Open risk 3 — weakest link is LLM compliance, not architecture (2026-07-04 injection≠compliance specimens): walk protocol/grep-on-entry/synthesis completeness all require per-turn LLM adherence; structure reduces, loop recovers post-hoc; the advisory philosophy consciously accepts this residual, with TimSquad-style action-boundary hard gates deferred as an evidence-conditional counter-position.
- Verdict recorded: best available under current constraints (verifiability, portability, no lock-in, dev-harness purpose); NOT beyond doubt. The design's actual merit: all three risks are wired to produce their own falsifying evidence (replay vs corpus growth; ② metrics; loop-collected compliance failures) instead of being answered by taste.

### Discovery capture

- Planning: updated — this section (risk registry).
- ADR: candidate — risk 2's conditional (delegated semantic safety net) may need an ADR 0024 clarifying amendment IF evidence triggers it.
- DDD/SDD/BDD/TDD/SSOT: none.

### 2026-07-04 Karpathy pattern verified at source (user-requested deep check)

Sources read: VentureBeat coverage of Karpathy's X post (x.com/karpathy/status/2039805659525644595, gist 442a6bf...), Nous Research hermes-agent llm-wiki SKILL.md v2.1 (most faithful implementation).

- Exact structure: ① Data Ingest (immutable raw/, web clipper, local images) ② Compilation (LLM authors wiki: summaries, concept pages, BACKLINKS) ③ Active Maintenance (periodic lint/health passes — self-healing). Principles: MD = source of truth; file-over-app; "wiki is the LLM's domain".
- Structural isomorphism with lazy-harness confirmed: SCHEMA.md≈AGENTS+digest-format; index.md("read first")≈lazy map overview (ADR 0049); log.md≈graph/validations jsonl; 13-check lint≈record-lint (theirs broader: orphan pages, broken wikilinks, index completeness, contradiction, stale, sha256 source drift, tag taxonomy, page size); session orientation mandate≈§2.1; raw→page promotion thresholds≈candidates→record.
- Shared limitation check (user question): ALL THREE of our risk-registry items exist there too. (1) Scale: Karpathy himself scopes it to ~100 articles/400k words, ideal 100–10,000 docs; mitigations = hierarchy (index section split at 50, topic-map at 200 entries, page split at 200 lines, ephemeral task-scoped mini-KBs per Lex Fridman). (2) Miss: hermes explicitly warns index-only lookup misses at 100+ pages → mandates parallel search_files; structural counters = orphan-page lint (same idea as our reachability audit), contradiction/contested/confidence frontmatter, sha256 drift detection; swarm variants add a Quality Gate (independent model scores drafts before promotion — isomorphic to our option-gate promotion). (3) LLM compliance: identical exposure, weaker remedies than ours — their "CRITICAL orient-first" and Pitfalls are pure advisory prompt text (injection≠compliance applies fully); no enforcement layer, no loop.
- Verdict on superiority (user Q): on the MEMORY axis this design extends lazy-harness's only 5★ dimension and none of the three compared harnesses has an equivalent (flat SSOT / external optional binary / none) — moat-strengthening yes; but overall harness superiority still requires the loop + proof tracks (enforcement/productization axes untouched by this design).
- Worth borrowing (3): confidence/contested markers on weak claims (absent from our digest contract); orphan/reachability lint (already planned as C4 — external precedent strengthens); index scale thresholds (50/200 split rules) as scaling playbook.

### Discovery capture

- SDD: candidate — confidence/contested marker fields for record-digest-format (borrow item 1).
- TDD: none. DDD/BDD/SSOT: none.
- ADR: none new — external validation of ADR 0024/0049 deepened to source level.
- Planning: updated — this section.
