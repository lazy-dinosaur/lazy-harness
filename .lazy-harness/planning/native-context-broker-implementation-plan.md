# Native Context Broker / Retrieval Implementation Plan

Status: proposed
Date: 2026-06-01
Layer: Planning
Related SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
Related SDD: `.lazy-harness/spec/platform/relevant-record-query.md`
Related SDD: `.lazy-harness/spec/platform/record-digest-format.md`
Related SDD: `.lazy-harness/spec/platform/context-delivery-contract.md`
Related SDD: `.lazy-harness/spec/platform/project-profile.md`
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related candidates:
- `candidate_context_delivery_subagent_handoff_20260601`
- `candidate_llm_query_expansion_for_ambiguous_surface_terms_20260601`
- `candidate_dual_mode_retrieval_file_and_query_20260601`
- `candidate_lazy_harness_native_context_broker_rag_20260601`
- `candidate_context_delivery_self_resolving_agent_20260601`

## Goal

Build a lazy-harness native Context Broker that turns ambiguous user requests into actionable required-read context before the agent answers or edits.

This is not an external RAG-first plan. The first implementation should use canonical `.lazy-harness` records, Project Profile artifacts, graph/implementation map data, and source file search. Vector/hosted RAG can remain optional later.

## Problem statement

Current `message.received` relevant-record injection is useful but too shallow for short project-surface terms.

Example:

```text
예약시트 고쳐줘
```

A local token/digest query cannot reliably know whether this means:

- 예약시트 / 예약 시트 / 예약표
- 예약관리페이지
- reservation sheet
- booking sheet
- appointment sheet
- schedule grid
- reservation table
- route/component/test names such as `ReservationSheet`, `ReservationTable`, `AppointmentPage`

The missing layer is not just RAG. It is:

```text
user phrase
→ query expansion / surface resolution
→ record/profile/graph/code search
→ result fusion
→ required-read context delivery
→ main LLM reads first
→ response.completed audit
```

## Design principles

1. Canonical truth stays in `.lazy-harness` records and source files.
2. Generated indexes and broker results are caches/context, not sources of truth.
3. Do not make external vector DB or hosted RAG mandatory.
4. Do not run heavy model/subagent work for every message in the 800ms `message.received` hook.
5. Default agent can self-resolve by generating queries and searching with read/grep/bash/root-bound tools; subagents are optional escalation.
6. The first-class abstraction is the search protocol and result packet, not whether the worker is the main LLM or a subagent.
7. Context delivery output must contain required-read items with paths, reasons, confidence/uncertainty, and fallback instructions.
8. Response audit should later verify that required-read / record-completion obligations were respected.

## Agentic search protocol first

The Context Broker should not be framed as only a smarter keyword retriever. Its first useful form is an **agentic search protocol**:

```text
ambiguous user phrase
→ generate Korean / English / code-style candidate queries
→ search records, Project Profile, graph, routes, symbols, source files, and tests
→ inspect results
→ refine queries when needed
→ produce required-read context
→ read required files before answering or editing
```

For a phrase like `예약시트`, deterministic keyword search alone is insufficient when records/code may be English (`appointment schedule`, `ReservationTable`, `booking grid`). The LLM supplies the cross-language/query-planning step, while local tools verify actual files and records.

This protocol must be expressible as:

1. instructions injected to the main LLM for self-resolution, and
2. a task prompt for a searcher subagent when delegation is useful.

Therefore, the protocol's input/output schema should not depend on who performs the search.

## Subagent portability

Subagents should be an execution option, not a different architecture.

Default mode:

```text
message.received injects search protocol
→ main LLM performs query expansion + root-bound searches
→ main LLM produces required-read summary
```

Escalated mode:

```text
message.received injects search protocol
→ main LLM delegates the same protocol to a searcher subagent
→ subagent returns the same Context Delivery Packet
→ main LLM reads required files and continues
```

This keeps the system simple now while making later subagent delegation cheap: the handoff prompt is just the same protocol plus the user request and host root.

## Search result output pipeline

Search output must not be raw grep chunks or vague `Relevant: X` labels. The broker should normalize results in three stages:

### Stage 1 — Raw hit

Raw hits are direct outputs from search tools and are not injected as-is.

```json
{
  "source": "record-query | project-profile | graph | file-search | symbol-search",
  "path": ".lazy-harness/behavior/reservation-management.md",
  "matchedText": "예약관리페이지",
  "query": "예약관리"
}
```

### Stage 2 — Normalized evidence

Normalize raw hits into comparable evidence rows.

```json
{
  "id": "record:.lazy-harness/behavior/reservation-management.md",
  "kind": "record | project-profile | graph-edge | source-file | symbol | test",
  "path": ".lazy-harness/behavior/reservation-management.md",
  "matchedBy": ["query-expansion", "record-digest"],
  "matchedQueries": ["예약시트", "예약관리", "reservation sheet"],
  "reason": "예약시트가 예약관리 UI surface일 가능성이 있음",
  "confidence": 0.82,
  "layer": "BDD",
  "readPriority": "required | optional | candidate"
}
```

### Stage 3 — Context Delivery Packet

Only the fused packet should be rendered into `system_reminder` or returned by a searcher subagent.

```json
{
  "instructionLevel": "self-resolve-before-change",
  "resolvedPhrase": "예약시트",
  "candidateMeanings": ["예약관리페이지", "reservation sheet", "booking table"],
  "confidence": 0.76,
  "requiredRead": [
    {
      "path": ".lazy-harness/project/feature-navigation.xml",
      "kind": "project-profile",
      "reason": "예약시트가 어떤 project surface alias인지 확인",
      "confidence": 0.88
    },
    {
      "path": ".lazy-harness/behavior/reservation-management.md",
      "kind": "record",
      "reason": "예약 관리 UI behavior 후보",
      "confidence": 0.82
    }
  ],
  "optionalRead": [],
  "fallbackSearches": ["rg -n \"예약|reservation|booking|appointment|schedule\" ."],
  "instruction": "Read requiredRead before answering or editing. If candidates conflict, ask an option gate."
}
```

Scoring should begin deterministic and explainable:

```text
exact alias match             +40
project profile surface match +35
rule digest Applies when      +30
graph/implementation edge     +25
file/symbol/route match       +25
multi-query duplicate         +10
deprecated/stale penalty      -30
```

Thresholds for the first implementation:

- `score >= 70` → `requiredRead`
- `40 <= score < 70` → `optionalRead`
- `score < 40` → keep as raw/candidate evidence only

This output pipeline is the stable contract. Search backends can change later without changing what the main LLM receives.

## Proposed implementation phases

### Phase 1 — Context Delivery Contract SDD

Status: completed in `cec13a2 Add context delivery contract`; synced and validated in `/home/lazydino/dev/medivance` and `/home/lazydino/dev/medivance-pwa`.

Create `.lazy-harness/spec/platform/context-delivery-contract.md`.

Define:

- `instructionLevel`: `digest-only | self-resolve-before-answer | self-resolve-before-change | delegate-search`
- `resolvedPhrase`
- `candidateMeanings`
- `queries`
- `requiredRead[]`
- `optionalRead[]`
- `confidence`
- `whyMatched`
- `fallbackSearches[]`
- privacy/fail-open requirements
- rendering into `system_reminder`

Acceptance criteria:

- SDD includes `## Rule digest`.
- Example covers `예약시트` style ambiguous surface term.
- Output schema is testable with fixtures.

### Phase 2 — Record Digest / Project Profile retrieval metadata

Status: completed in this Phase 2 change; contracts updated in `.lazy-harness/spec/platform/record-digest-format.md`, `.lazy-harness/spec/platform/relevant-record-query.md`, `.lazy-harness/spec/platform/project-profile.md`, and `.lazy-harness/schemas/relevant-record-index.schema.json`; protected by `.lazy-harness/scripts/self-test.py#check_context_delivery_metadata_phase2`.

Extend record guidance so records can feed the broker.

Update or add examples for:

- aliases / surface terms,
- route/component/file hints,
- related records,
- implementation map references,
- Project Profile `feature-navigation.xml` as a first-class retrieval source.

Acceptance criteria:

- `record-digest-format.md` explains aliases/surface terms without making every record verbose.
- `project-profile.md` links feature navigation to context delivery.
- Fixtures show one host-project surface mapping.

### Phase 3 — Generated context index

Status: implemented in this Phase 3 change with `.lazy-harness/scripts/context-index.ts`, `.lazy-harness/schemas/context-index.schema.json`, and `.lazy-harness/bin/lazy context-index`; protected by `.lazy-harness/scripts/self-test.py#check_context_index_generator_phase3`.

Add a rebuildable generated index:

```text
.lazy-harness/generated/context-index.json
```

or a small SQLite/JSON index later.

Initial JSON index should include:

- record path/title/layer/status/scope,
- parsed rule digest,
- aliases/surface terms,
- related records,
- implementation map file hints,
- graph edge hints,
- project profile surface hints.

Acceptance criteria:

- index generation command is deterministic.
- generated output is ignored or documented as derived.
- query falls back to source scan when index missing/stale.

### Phase 4 — Dual-mode retrieval

Implement retrieval as two tracks:

1. Query track:
   - LLM/self-generated query expansion or deterministic expansion fixture,
   - multi-query record/profile/graph search.
2. File track:
   - file/path/symbol/route/component search,
   - implementation map and test lookup.

Result fusion should produce required-read candidates.

Acceptance criteria:

- fixture: `예약시트` expands to multiple candidate queries.
- fixture: matching record/profile/code paths are fused into required-read list.
- returned items include citation path, reason, source, and confidence.

### Phase 5 — Self-resolving agent instruction

Do not require subagents by default.

`message.received` should be able to inject:

```text
This request is ambiguous / implementation-likely.
Before answering or editing, generate multiple candidate meanings, run root-bound record/profile/code searches, then read required files.
```

Subagent/searcher escalation should be recommended only for high-depth, high-risk, or parallel search needs.

The injected protocol should make the main LLM do the first search loop itself: generate candidate meanings, run root-bound searches through available tools, read the resulting required files, and only delegate if the search becomes too broad or risky.

Acceptance criteria:

- simple questions still get `digest-only` output.
- ambiguous project-surface requests get `self-resolve-before-change` instruction.
- no mandatory subagent latency in the pre-turn hook.

### Phase 6 — Optional search handoff

Add optional handoff mode for cases where self-resolution is insufficient.

Possible modes:

- main LLM calls searcher subagent as first action,
- background index/cache refresh,
- later optional `jcode run` query-planner prototype with recursion guard.

The searcher subagent must return the same Context Delivery Contract shape as self-resolution. It should not return only prose or raw hits.

Acceptance criteria:

- no `jcode run` from hook without recursion guard and timeout plan.
- handoff result uses same Context Delivery Contract schema.
- response audit can cite whether required-read was provided.

### Phase 7 — Response audit integration

Extend response audit only after Context Delivery Contract is stable.

Audit should detect:

- required-read was surfaced but ignored,
- new alias/surface was discovered but not recorded,
- implementation touched mapped area but BDD/SDD/TDD/graph was not updated or record decision was not stated.

Acceptance criteria:

- avoid current false-positive problem by requiring concrete evidence.
- clean explanatory turns stay silent.
- fixtures cover record-needed and no-record-needed cases.

### Phase 8 — Post-turn Record Decision Broker

Add a structured post-turn broker after the pre-turn context delivery flow is stable.

Purpose:

```text
turn evidence
→ normalized record signals
→ record decision packet
→ record update / candidate capture / no-record-needed / option gate
```

The output should mirror pre-turn Context Delivery, but for record writes:

```json
{
  "recordDecision": {
    "disposition": "record-updated | candidate-needed | no-record-needed | option-gate-needed",
    "trigger": "new alias found / UI behavior changed / architecture decision made",
    "evidence": ["edited components/reservations/ReservationTable.tsx"],
    "recommendedRecords": [
      {
        "path": ".lazy-harness/behavior/reservation-management.md",
        "action": "update",
        "reason": "UI flow or alias changed"
      },
      {
        "path": ".lazy-harness/knowledge/graph.jsonl",
        "action": "append",
        "reason": "alias/surface/component relation should be indexed"
      }
    ]
  }
}
```

Acceptance criteria:

- no automatic blind record writes.
- explicit `no-record-needed` path for explanation/evaluation turns.
- concrete evidence required before STOP output.
- fixtures cover false-positive cases before enabling stricter audit.
- can consume Context Delivery Packet evidence such as `requiredRead`, resolved aliases, and files read/changed.

## Search system recommendation

Start with native lazy-harness retrieval, not external RAG:

```text
Phase A: generated JSON context index
Phase B: multi-query local record/profile/code search
Phase C: result fusion and required-read delivery
Phase D: optional SQLite FTS
Phase E: optional vector/GraphRAG adapter
```

Do not begin with hosted vector DB. The first value comes from better context delivery and file/profile/graph grounding.

## New record writing guidance

Records that should participate in retrieval should include:

```md
## Rule digest

- Applies when:
  - natural language aliases the user might say
  - project surface/action phrases
- Must:
  - what to do before changing this area
- Record completion:
  - when confirmed changes update this record
- Related records:
  - `.lazy-harness/...`
```

For UI/surface records, also include:

```md
## Surface aliases

- ko: 예약시트
- ko: 예약표
- en: reservation sheet
- route: `/reservations`
- component: `ReservationManagementPage`
```

For implemented areas, include `Implementation map` with source files, symbols, tests, and graph links.

## Validation plan

- Self-test for the three-stage output pipeline: raw hit → normalized evidence → Context Delivery Packet.
- Unit fixtures for query expansion/fusion output.
- Self-test for `예약시트` style ambiguous term.
- Self-test for digest-only simple request.
- Self-test for missing index fallback.
- Self-test for self-search protocol rendering.
- Self-test for searcher subagent handoff output shape, without requiring subagent execution.
- Self-test for post-turn Record Decision Packet false positives and no-record-needed cases.
- Medivance/PWA dogfood sync and smoke.
- Response audit false-positive regression tests before enabling stricter audit.

## Non-goals for first implementation

- No mandatory external RAG/vector DB.
- No mandatory subagent for every ambiguous request.
- No broad tool hard-blocks.
- No full-document prompt dumps.
- No generated index as canonical truth.

## Rule placement

- Rule: implement lazy-harness native context broker as a staged plan: context-delivery contract first, then retrieval metadata/index, then dual-mode search, then optional self-resolving/subagent handoff, then response audit integration.
- Scope: framework-global / transient-plan
- Primary record: `.lazy-harness/planning/native-context-broker-implementation-plan.md`
- Why not AGENTS.md: this is an implementation roadmap and architecture plan, not base agent grammar.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed direction; implementation still requires explicit approval after plan review.

## Discovery capture

- DDD: none yet; host-specific domain aliases come later via Project Profile/BDD records.
- SDD: candidate, new `context-delivery-contract.md` should be first implementation record.
- BDD: candidate, user-visible behavior is main agent reads required context before editing.
- TDD: candidate, fixtures listed above are required before enabling stricter audit.
- ADR: candidate, ADR 0041 successor or addendum may be needed if model-query planning becomes first-class.
- SSOT: candidate, rule lifecycle/search provider ownership may need update.
- Planning: updated in this file.
