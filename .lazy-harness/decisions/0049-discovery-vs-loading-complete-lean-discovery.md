# ADR 0049 — Discovery vs Loading: Mandatory Complete Lean Discovery, JIT Targeted Loading

- Status: Accepted
- Date: 2026-06-24
- Trigger: Token-efficiency review of the retrieval workflow. User clarified the binding constraint: "늘 모르는게 기본이어야하는데 오히려 레코드를 강제로 읽게 시키지 않는다면 나중에 이미 저장된건데 모르고 넘어가는 경우가 많아서 문제거든?" — i.e. `default=모름` makes discovery non-optional; a Karpathy-style "just load what this step needs" (conditional/JIT-as-skip) reintroduces silent-skip of already-stored records. Cross-checked against Andrej Karpathy's context-engineering methodology.

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Applies when:
  - deciding how much project knowledge to surface or read before answering/acting
  - changing `lazy map --overview`, the message.received discovery prompt, or record-read expectations
  - evaluating retrieval token cost vs the `default=모름` completeness invariant
- Must:
  - keep discovery (which records EXIST) mandatory and complete: every record discoverable, never truncated away
  - keep the discovery surface lean: paths + titles + status only, no bodies, no graph dumps, no candidate-list dumps
  - keep loading (reading full record BODIES) just-in-time and targeted: read the records the task implicates, not a read-until-all-layers sweep
  - preserve `default=모름`: the agent may not self-certify "no relevant record exists" and skip discovery
- Must not:
  - make discovery optional or task-conditional (that is the silent-skip failure this framework exists to prevent)
  - treat "keep context lean / JIT" as license to skip discovery; lean/JIT governs loading, not discovery
  - ship a discovery surface that is both heavy and incomplete (the current truncated overview)
- Record completion:
  - changes to discovery completeness/leanness, the loading expectation, or the `--complete` discovery mode update this ADR plus `spec/platform/purpose-scoped-retrieval.md`, `spec/platform/record-index-header.md`, and self-test
- Related records:
  - `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`
  - `.lazy-harness/spec/platform/record-index-header.md`
  - `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md`
  - `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - `.lazy-harness/ssot/cli-tool-boundary.md`

## Context

A token-efficiency review measured the retrieval workflow with `lazy retrieval-workflow-benchmark` (extended in this work to add a `no_map` grep-fallback surface, the otherwise-excluded `overview` cost, and a `mapInclusive` accounting). Findings, default limit=8, 4 framework queries, token proxy `ceil(bytes/4)`:

- The mandatory `lazy map --overview` costs ~8,320 tokens (JSON) per task and is excluded from the older benchmark's helper comparison.
- Per-task harness overhead over a no-harness baseline is ~87k tokens (map+overview), of which record-body reads are ~80%.
- `map` vs `no_map`: `no_map` helper is cheaper (grep returns paths only) but its unranked, over-broad candidate pile makes the read-to-cover-all-layers simulation ~4x more expensive in total. `map`'s value is candidate ranking/curation, not the cue verbosity.

Cross-checked against Karpathy's methodology:

- "Context engineering" = fill the context window with just the right information for the next step; context window = RAM (expensive, volatile); avoid eager stuffing and "context rot."
- His "LLM Wiki / compilation" idea (LLM synthesizes raw source into a persistent, interlinked knowledge base the agent maintains and queries, so knowledge compounds instead of being re-derived) is exactly what `.lazy-harness` records are. So the record corpus is an asset, not waste, and record reads are not pure overhead.
- His "keep context lean / just-in-time" guidance assumes the scheduler knows what to load. It governs LOADING.

The binding correction from the user: `default=모름` (AGENTS.md §0/§2.5) means the agent does not know what it does not know, so it cannot be trusted to decide "this task needs no record." Discovery therefore cannot be optional; otherwise already-stored decisions/contracts are silently skipped — the exact failure the framework exists to prevent.

Measured flaw that proves discovery and loading are conflated today: the mandated `lazy map --overview --limit=20` is both heavy and INCOMPLETE.

| Layer | total records | listed in overview (limit=20) | hidden |
|---|---:|---:|---:|
| ADR | 49 | 20 | 29 |
| SDD | 50 | 20 | 30 |
| Planning | 44 | 20 | 24 |
| TDD | 39 | 20 | 19 |
| DDD/BDD/SSOT | 8/6/18 | all | 0 |

An agent following only the mandated overview cannot discover 102 records — silent-skip is already happening. The measured fix `lazy map --overview --complete --format=md` lists all 214 records at ~6.7k tokens (26,706 bytes): leaner than the mandated `--format=json` overview (~8.3k) and with the drill-down/graph-sample noise removed, but ~+2.1k over the truncated `--format=md --limit=20` (~4.6k, only 112 of 214 shown). So completeness costs ~+2.1k over the truncated md to eliminate the 102-record silent-skip; a paths-only variant would be ~2.3k if titles are dropped. Neither existing surface fills the gap: overview is heavy-and-truncated; `lazy record-index --format=md` lists only records that carry retrieval metadata (a curated subset, not the full catalog).

## Decision

Separate the two concerns and govern each by the principle that fits it.

1. **Discovery (which records exist) — mandatory, complete, lean.** Provide a complete lean discovery index: every record's path, title, and status across all layers, untruncated, with no bodies, no graph sample-row dumps, and no drill-down candidate dumps (compact graph relation counts are retained). This is the surface that satisfies `default=모름`: nothing stored is hidden, and it is cheap enough to run every task.
2. **Loading (reading full record bodies) — just-in-time, targeted.** After discovery, read the specific record bodies the task implicates (Rule digest / full body / Implementation map / linked source-tests). Do not read-to-cover-all-layers as a default; cover the layers the task actually touches.
3. **Epistemic boundary.** `default=모름` governs discovery (complete, non-skippable). Karpathy's lean/JIT governs loading (targeted, not eager). They do not conflict; they apply to different steps.

This work implements the discovery half: a `lazy map --overview --complete` complete lean discovery mode (untruncated inventory, paths/titles/status only). Making it the mandated discovery surface in `on-message-received.sh` and tightening the loading expectation are follow-ups gated on dogfood, captured in planning; this ADR does not change the message.received prompt or option-gate/read-debt policy.

## Consequences

- A complete discovery surface exists (`lazy map --overview --complete`): all 214 records at ~6.7k tokens in md, leaner than the mandated JSON overview (~8.3k) and free of the truncation silent-skip, with drill-down/graph-sample noise dropped. Completeness costs ~+2.1k over the truncated md (4.6k); the `--format=json` complete variant is heavier (~14.8k) due to pretty-print verbosity over 214 records, so the lean discovery surface is the md form.
- The retrieval token problem is correctly named: the waste is fat-and-incomplete discovery plus untargeted loading, not "reading records" (necessary) nor "discovering" (necessary).
- No epistemic regression: discovery stays mandatory and becomes more complete, so `default=모름` is better served, not weakened.
- The earlier "make small-task reads conditional" idea is explicitly rejected: it would skip discovery and silently miss stored records.
- Follow-up (not in this ADR): wire the complete mode into the mandated discovery prompt and tighten loading guidance, after dogfood evidence.

## Implementation map

- Status: `implemented` (discovery mode); message.received wiring is a flagged follow-up
- Source files:
  - `.lazy-harness/scripts/record-map.ts` — `--complete` overview mode: untruncated inventory (path/title/status), lean features (id/label/status), omits graph sample-row and drill-down candidate dumps (relation counts kept).
  - `.lazy-harness/bin/lazy` — help text for `--complete`.
  - `.lazy-harness/scripts/retrieval-workflow-benchmark.ts` — `no_map` + `overview` + `mapInclusive` axes that produced the evidence.
- Key symbols:
  - overview builder in `.lazy-harness/scripts/record-map.ts` (complete-mode branch).
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_purpose_scoped_retrieval_cli` (complete-mode completeness + leanness)
  - `.lazy-harness/scripts/self-test.py#check_retrieval_workflow_benchmark_cli`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`, `.lazy-harness/spec/platform/record-index-header.md`, `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md`
  - ADR: `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`, `0041`
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
- Machine index:
  - graph ids: `kg_adr0049_discovery_vs_loading`, `kg_adr0049_complete_discovery_mode`

## Rule placement

- Rule: discovery is mandatory + complete + lean; loading is JIT + targeted; `default=모름` governs discovery, Karpathy lean/JIT governs loading.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0049-discovery-vs-loading-complete-lean-discovery.md`
- Why not AGENTS.md: AGENTS.md carries only a compact pointer (180-line cap); the rationale, measurements, and trade-off belong in an ADR.
- Why not `.jcode`: shared framework retrieval behavior for all hosts, not local/private wiring.
- Confirmation: user-confirmed

## Discovery capture

- DDD: no new domain vocabulary; reuses Map-First Retrieval / Searchable Record Memory.
- SDD: `purpose-scoped-retrieval.md` and `record-index-header.md` gain the complete lean discovery mode contract.
- BDD: agent discovery behavior should run a complete lean index; loading should be targeted (behavior tightening is a flagged follow-up).
- TDD: self-test covers `--complete` completeness (all records, untruncated) and leanness (no bodies/graph/candidate dumps).
- ADR: this ADR; ADR 0045 (map-first) and 0041 (organic) remain governing.
- SSOT: CLI boundary remains `.lazy-harness/ssot/cli-tool-boundary.md`; the complete mode stays cue-only and non-canonical.
- Planning: message.received discovery-surface rewire + loading-guidance tightening captured as follow-up.
