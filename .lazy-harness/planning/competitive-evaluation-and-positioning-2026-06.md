# Competitive Evaluation and Positioning — 2026-06

Status: accepted-reference
Layer: Planning
Created: 2026-06-26
Source: user-requested online research + harness-record synthesis (this session)
Related planning: `.lazy-harness/planning/external-agent-harness-reference.md`, `.lazy-harness/planning/practical-agent-harness-operating-patterns.md`
Related V2: `.lazy-harness/planning/lazy-harness-v2-direction-purpose.md`, `.lazy-harness/planning/lazy-harness-v2-evolution-context.md`, `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md`, `.lazy-harness/planning/lazy-harness-v2-roadmap-detailed-review.md`
Related ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
Related SSOT: `.lazy-harness/ssot/project-identity.md`

## Rule digest

- Status: advisory
- Layer: Planning
- Scope: framework-global
- Applies when:
  - user asks how lazy-harness compares to external agent harnesses or where it stands
  - planning V2 priorities, positioning, marketing, or adoption strategy
  - tempted to compare lazy-harness directly against execution runtimes (Claude Code/Cursor/Aider) as if same category
- Must:
  - position lazy-harness as a record-first governance/memory layer (L6), not an execution runtime
  - treat dimension grades here as session assessment/inference, not measured benchmark facts
  - prioritize measurement evidence and V2 update-loop shipping over adding more layers
- Must not:
  - present "foundation complete" as "V2 product complete"
  - claim independent benchmark/portability results that do not exist yet
- Record completion:
  - when real dogfooding measurement or cross-host portability evidence is produced, update this record and the V2 roadmap records
- Related records:
  - `.lazy-harness/planning/external-agent-harness-reference.md`
  - `.lazy-harness/planning/lazy-harness-v2-roadmap-detailed-review.md`

## Purpose

Preserve the competitive evaluation produced when the user asked to research well-known harnesses online and evaluate lazy-harness in detail. This record holds the consolidated assessment (positioning, dimension grades, strengths, weaknesses) and a prioritized recommendation backlog.

It is an assessment/reference, not an adoption decision or implementation approval. Grades are session inference grounded in records + online research, not measured benchmark results.

## Category framing — which layer is lazy-harness

Famous harnesses split into layers. Lazy-harness lives in the memory/spec/governance layer (L6), riding on top of execution runtimes — it is not a competitor to them.

| Layer | Examples | What they own |
|---|---|---|
| Execution runtime | Claude Code, Codex CLI, Gemini CLI, Aider, Goose, Crush, OpenCode | one agent session + tools |
| IDE pair agent | Cursor, Windsurf, Junie, Copilot | IDE plan/edit/test loop |
| Cloud autonomous | Devin, Factory Droid, Replit Agent | long-running VM task → PR/deploy |
| Orchestration | LangGraph, AutoGen, CrewAI, OMC | multi-agent coordination |
| Eval harness | SWE-bench, Inspect AI, HAL, DeepEval | datasets/solvers/scorers/traces |
| **Memory/spec/governance (lazy-harness)** | **lazy-harness**, spec-kit, Kiro, BMAD, Continue checks, Cursor Rules, CLAUDE.md/AGENTS.md | durable knowledge + project rules injected into a runtime |

The correct comparison ring is L6. Against execution runtimes the question "who is better" is malformed: lazy-harness governs them.

Identity basis: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md` (AI-first lifecycle enforcement, methodology pluralism, not an ESLint-style static tool) and `.lazy-harness/ssot/project-identity.md` (standalone framework source-of-truth repo).

## Landscape reference

Full external-harness landscape (≈40 tools across product, control-plane, adapter, runtime, eval) is already curated in `.lazy-harness/planning/external-agent-harness-reference.md`. Online research (2026-06) confirms the top tier and the market thesis: no single winner, workflow three-split (IDE / terminal / autonomous), power-user stack = Cursor + Claude Code. This record does not duplicate that table; it references it.

True L6 peers to benchmark against: CLAUDE.md/AGENTS.md conventions (shallowest), Cursor Rules + Memories (productized, unstructured), GitHub spec-kit / AWS Kiro (spec-driven, no accumulating memory/graph), BMAD-METHOD (role+doc workflow, no layer/graph), Continue source-controlled checks (validation only).

## Dimension assessment (L6 ring)

Scale ★1 (absent) – ★5 (best-in-class for this layer). Grades = session assessment/inference.

| Dimension | lazy-harness | Best L6 peer | Note |
|---|---|---|---|
| Structured memory depth | ★★★★★ | Cursor Memories ★★★ | 6-layer + Implementation map (3-layer storage, ADR 0030) + Rule digest |
| Knowledge graph | ★★★★☆ | (mostly absent) | 653 graph rows, ~21 edge kinds |
| Decision persistence (ADR) | ★★★★★ | (absent–weak) | 51 ADR with supersede chains |
| Lifecycle gates | ★★★★☆ | Claude Code hooks ★★★★ | response.completed gate, option-gate, layer-completeness gate; friction over ergonomics |
| Search / search discipline | ★★★☆☆ | Cursor indexing ★★★★ | AI-direct semantic search (ADR 0024) is portable but per-turn grep+read cost; graph CLI added then rolled back |
| Agent neutrality | ★★★☆☆ | LangGraph ★★★★ | V2 goal Pi-first agent-neutral; Jcode residue being decommissioned (ADR 0050/0051) |
| Verification / eval harness | ★★☆☆☆ | Inspect AI ★★★★★ | self-test + doctor smoke only; record/replay + benchmark matrix planning-only |
| Portability proof | ★★☆☆☆ | Aider ★★★★ | dogfood concentrated on Medivance; diversity unproven |
| Adoption / ecosystem | ★☆☆☆☆ | Claude Code ★★★★★ | internal-only, Korean-centric docs, not public |
| V2 implementation maturity | ★★☆☆☆ | — | core (project-map update loop) still "next"; many records draft/needs-review |

## Strengths (differentiators)

1. 6-layer × Implementation map × graph triad — depth no CLAUDE.md/Cursor Rules can match (ADR 0030, `searchable-record-memory.md`).
2. Accumulating-utility + user-correction convergence (ADR 0032): confirmed corrections persist to SSOT; next session does not repeat the mistake. Most harnesses lack this self-correction loop.
3. Methodology pluralism: DDD/SDD/BDD/TDD/ADR/SSOT equal, not TDD-centric.
4. Decision permanence: 51 ADR + supersede chains keep "why" in records, not buried in code.
5. Honest self-critique recorded (`lazy-harness-v2-evolution-context.md` L64–80) — rare for a framework to log its own failures.

## Weaknesses / risks (honest)

1. Friction vs utility unresolved — excessive prompt/gate burden, heavy rulebook surface, folder-first UX friction (evolution-context L112–118). The exact axis execution runtimes win on.
2. Architecture churn — graph CLI added→rolled back, route telemetry superseded (ADR 0037), Jcode wiring decommissioned (ADR 0050). Core model not yet stable; V2 = "recovery/simplification" of an overfit V1.
3. Verification gap is most critical — deterministic record/replay + reliability metrics (Inspect/HAL/DeepEval territory) are planning-only (`external-agent-harness-reference.md` L127, L153–161). ADR 0024 L226–232 promised dogfooding measurement (rule-violation rate, drift, search frequency, token cost) at 6 weeks–3 months; that measurement result record is not visible.
4. Single-host portability bias — `project-identity.md` 2026-06-04 correction forbids "Medivance-only optimization," evidence that work concentrates there; diverse stack/domain proof absent.
5. Adoption barrier — internal-only (README L206), Korean-centric docs, no public operation; OSS L6 peers (spec-kit, Continue) spread freely. [inference]
6. V2 unshipped — core product (project-map update loop) still "next" (`roadmap-detailed-review` L169); many records draft/needs-review. Self-docs warn to distinguish "foundation complete" from "V2 product complete" (L227).

## Prioritized recommendation backlog

| # | Priority | Recommendation | Status | Anchor |
|---|---|---|---|---|
| R1 | highest | Produce dogfooding measurement evidence (rule-violation, drift, search frequency, token cost) as a result record | open | ADR 0024; `.lazy-harness/spec/platform/retrieval-workflow-benchmark.md` |
| R2 | high | Ship Phase 1.5 Project Map Update Loop design→runtime; it gates all V2 follow-ups | open | `lazy-harness-v2-roadmap-detailed-review.md` L169 |
| R3 | high | Manage a friction budget explicitly via stage-aware policy levels (discover/recommend/warn/block) | open | ADR 0040; capability registry |
| R4 | medium | Add 1–2 heterogeneous-stack dogfood hosts beyond Medivance to prove portability | open | `project-identity.md` |
| R5 | medium | Fix HarnessAdapter boundary (Pi/Claude Code/Codex as adapters), natural consequence of Jcode decommission | open | ADR 0050; `external-agent-harness-reference.md` L152 |
| R6 | low/strategic | Evaluate public release (English entry doc + public install) since L6 peers occupy OSS space | open | README; ADR 0027 |

## Final grades

| Aspect | Grade |
|---|---|
| Concept / design depth | A |
| Current implementation maturity | C+ |
| Verification / evidence | C− |
| Adoption / ecosystem | D |
| Direction / self-awareness | A |

Verdict: in the L6 ring, frontier on ideas, early on proof. Fate hinges not on adding more layers but on (a) producing objective evidence that memory gain beats input friction, and (b) actually shipping the V2 update loop — a conclusion the harness's own records (ADR 0024, evolution-context, roadmap-review) already point to.

## Implementation map

- Status: `planned`
- Primary files:
  - `.lazy-harness/planning/competitive-evaluation-and-positioning-2026-06.md` — this consolidated assessment + recommendation backlog.
  - `.lazy-harness/planning/external-agent-harness-reference.md` — canonical external-harness landscape (referenced, not duplicated).
  - `.lazy-harness/planning/practical-agent-harness-operating-patterns.md` — operating-pattern reference.
  - `.lazy-harness/decisions/0024-ai-first-framework-redesign.md` — identity constraint underpinning positioning.
- Key symbols:
  - none; planning/assessment record, not an implemented code path.
- Flow:
  1. User requests external-harness research + lazy-harness evaluation.
  2. This record preserves the assessment, dimension grades, and recommendation backlog.
  3. Recommendation items graduate into ADR/spec/test records before any implementation.
- Tests / protection:
  - `.lazy-harness/bin/lazy record-lint --fail-on-issues` — digest/ref hygiene for this record.
  - `python3 .lazy-harness/scripts/self-test.py` — framework record/JSONL invariants.
- Ownership boundaries:
  - Owner/upstream: external projects remain upstream references only.
  - This host may change: lazy-harness planning/assessment records, V2 roadmap, recommendation backlog.
  - This host must not change without explicit confirmation: vendor-specific claims, benchmark assertions, or dependency adoption.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
  - Planning: `.lazy-harness/planning/lazy-harness-v2-roadmap-detailed-review.md`
  - SSOT: `.lazy-harness/ssot/project-identity.md`
- Machine index:
  - graph ids: `kg_competitive_evaluation_2026_06_doc`, `kg_competitive_evaluation_2026_06_references_landscape`, `kg_competitive_evaluation_2026_06_decided_by_adr0024`
  - generated index key: `pending until implementation-index generator exists`

## Rule placement

- Rule: lazy-harness should be positioned and evaluated as an L6 record-first governance/memory layer; competitive judgement must separate design depth (strong) from verification/adoption maturity (early), and prioritize evidence + V2 update-loop shipping over adding layers.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/competitive-evaluation-and-positioning-2026-06.md`
- Why not AGENTS.md: this is positioning/assessment planning, not immediate prompt grammar.
- Why not `.jcode`: framework-global assessment, not private local Jcode wiring.
- Confirmation: user-requested evaluation; user confirmed it should be recorded as a plan.

## Discovery capture

- DDD: none; reuses existing harness/project-map vocabulary.
- SDD: candidate only; R5 HarnessAdapter boundary would need a future SDD.
- BDD: none.
- TDD: candidate only; R1 measurement evidence may need a result/regression record.
- ADR: none yet; R2/R5 adoption would need future ADRs.
- SSOT: none; references existing project-identity SSOT.
- Planning: created by this record; recommendation backlog R1–R6 tracked here.

## Measured evidence — 2026-06-26 (R1 partial: cost side only)

Status: measured-evidence
Confirmation: ran framework measurement tools in source repo this session
Caveat: these measure lazy-harness's own overhead and retrieval cost, NOT a control A/B of rule-adherence with the layer on vs off. The decisive instruction-following delta (R1 net rule-violation rate vs control) is still unmeasured.

### Instruction-surface cost (`lazy prompt-budget`)

- `.lazy-harness/AGENTS.md`: 179 lines, 1761 est. tokens, enforced.
- Rendered `message.received` per-turn reminder: 19 lines, 551 est. tokens (hard max 1000).
- Interpretation: thin-grammar bet (ADR 0024) holds — static instruction surface is small and bounded vs thick monolithic system prompts.

### Per-turn latency cost (`lazy hook-timings`, 10268 turns, 2026-05-21→06-26)

- `hook-total`: avg 1317ms, p50 907ms, p90 2636ms, p99 4038ms, max 8009ms.
- Largest contributor: `check-response-rule-audit.py` avg 611ms (p90 1765ms).
- Trigger checks (DDD/SDD/SSOT/BDD/layer): ~25–136ms each.
- Interpretation: lazy-harness adds ~0.9–2.6s wall-clock per response turn; pure per-turn cost, no model task-resolution change.

### Retrieval token cost (`lazy retrieval-workflow-benchmark`, 4 feature queries)

- mandatory `lazy map --overview`: 8442 tokens/task.
- map-first path total: 339,294 tokens (3/4 layer coverage).
- naive grep fallback (`no_map`) total: 1,472,342 tokens (3/4 coverage).
- map-first saves ~77% retrieval tokens vs grep-everything; but adds the 8.4k/task overview vs a lean agent that retrieves nothing exhaustively.

### Enforcement firings (guard `emitted` counts, same sample)

- check-tdd-cross-verify 1645, check-option-gate-discipline 833, check-record-before-session-history 832, check-affected-tests 825, check-aftershock-reanalysis 830, check-policy-block-runtime 132 (hard blocks), check-project-rule-placement 67, check-analysis-discovery-capture 45, relevant-record-query 27.
- Interpretation: guards demonstrably fire thousands of times (the layer is active), but `emitted` counts reminders/nudges + post-hoc backstops, not proven prevented-violations. `model-quality-dogfood-findings.md` confirms response.completed reminders fire after the response, so net prevention requires action-boundary placement.

### Comparative bottom line

- Instruction-following: lazy-harness is a more rigorous implementation of the 2026 anti-drift best practice (distributed context files read before each step) than flat `.cursor/rules`/`CLAUDE.md`, with real firing evidence — but "how much better" is unquantified for lazy-harness and competitors alike (no published rule-adherence rate anywhere).
- Performance: lazy-harness is strictly a per-turn cost add (~+1.3s, ~+2.3k static tokens, +8.4k tokens/task overview) and does not change SWE-bench-style task resolution (a model+runtime property it sits above). Its only measured speed/cost win is ~77% token saving vs naive grep retrieval.
- Net: the layer trades measurable per-turn performance for asserted-but-unmeasured cross-session correctness/adherence. Closing R1 (a control A/B) is the only way to quantify the instruction-following gain.
