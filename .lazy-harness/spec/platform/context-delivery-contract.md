# SDD - Context Delivery Contract

Status: accepted
Date: 2026-06-01
Layer: SDD
Related plan: `.lazy-harness/planning/native-context-broker-implementation-plan.md`
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
Related SDD: `.lazy-harness/spec/platform/relevant-record-query.md`
Related SDD: `.lazy-harness/spec/platform/record-digest-format.md`
Related schema: `.lazy-harness/schemas/context-delivery-packet.schema.json`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - implementing Native Context Broker, Context Delivery Packet, or required-read search output
  - user asks how ambiguous project-surface terms become actionable record/code context
  - designing self-resolving search, optional searcher subagent handoff, or pre-response context rendering
  - generating a searcher handoff prompt for optional delegation after main-agent self-resolution is insufficient
  - Korean or multilingual terms such as `기능패널` must bridge to English records, routes, symbols, or tests
- Must:
  - deliver required-read context with path, kind, reason, confidence, and matched query evidence
  - normalize raw hits before rendering; never inject raw grep chunks as the final broker output
  - keep canonical truth in `.lazy-harness` records and source files; generated packets are non-canonical context
  - fail open and stay bounded when explicitly used from lifecycle code; the default `message.received` hook must not run it automatically
  - allow lightweight self-resolution instructions when a full packet is unavailable but a request is implementation-likely
  - make optional search handoff prompts return the same packet-shaped contract and forbid mutations/raw chunks
  - when packet evidence is journaled, persist only sanitized required/optional read metadata and hashed identifiers
  - ask an option gate only after root-bound search/read evidence when candidate meanings still conflict and confidence is not high enough to proceed
  - treat low-confidence self-resolve packets or direct-search prompt rows with fallback searches as `search-debt` that must be satisfied by LLM/searcher root-bound search evidence before response/action
  - when concrete `requiredRead` or fallback search debt exists for a turn, journal the unresolved obligation, enforce generic pre-action search/read evidence before tools, and let response audit/backstop surface any unsatisfied debt at turn completion
  - keep the default `message.received` transport as harness-first inventory/search prompt + sanitized search-debt journal, not an automatic Context Delivery/relevant-record semantic backend
  - keep the default `message.received` transport static: shell/CLI hooks must not branch on raw user text to choose meaning-specific context or change-vs-answer instruction levels
  - require the default prompt to follow lazy-harness instructions first: inspect actual stored layer/file inventory, generated-index presence, graph/profile pointers, and canonical records/source before free-form alias/query expansion
  - treat tool names in prompts and fixtures as examples only; the guard checks for root-bound harness-following evidence, not a project/tool allowlist
- Must not:
  - make external vector DB, hosted RAG, or subagents mandatory for every turn
  - store raw user messages, full transcripts, or raw assistant responses in context-delivery runtime state
  - use Context Delivery Packet output as canonical record truth
  - treat deterministic Context Delivery/Relevant Record Query output as proof that the LLM/searcher performed direct search
- Record completion:
  - changes to packet fields, instruction levels, required-read semantics, rendering, privacy, or fail-open rules update this SDD and the packet schema
- Related records:
  - `.lazy-harness/planning/native-context-broker-implementation-plan.md`
  - `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - `.lazy-harness/spec/platform/relevant-record-query.md`
  - `.lazy-harness/spec/platform/response-rule-audit.md`

## Purpose

The Context Delivery Contract defines the stable handoff shape between user intent resolution, local search, optional delegation, and the main LLM's next action.

It answers:

```text
Given an ambiguous or implementation-likely user request,
which records/files must the agent read before answering, planning, or changing code?
```

The contract is intentionally independent of the worker. A packet may be produced by:

- the main LLM self-resolving with root-bound tools,
- a deterministic local broker implementation,
- a searcher subagent,
- a future index or optional RAG adapter.

All producers must return the same packet shape so the main agent can consume it uniformly.

## Non-goals

- Not a canonical record store.
- Not a replacement for full record reads after a required path is selected.
- Not a new hard-stop mechanism.
- Not a requirement to call a subagent or hosted model from every `message.received` hook.
- Not permission to search outside the current host root.

## Pipeline contract

Context delivery has three explicit stages.

```text
raw hit
→ normalized evidence
→ Context Delivery Packet
→ system_reminder rendering or searcher handoff result
→ required reads before answer/change
```

### Stage 1 - Raw hit

A raw hit is a direct result from a search backend. Raw hits are evidence only and must not be injected as the final user-facing context.

```json
{
  "source": "record-query",
  "path": ".lazy-harness/behavior/feature-surface.md",
  "matchedText": "기능관리페이지",
  "query": "기능패널"
}
```

Allowed raw hit sources:

- `record-query`
- `project-profile`
- `graph`
- `file-search`
- `symbol-search`
- `test-search`
- `manual`

### Stage 2 - Normalized evidence

Normalized evidence rows make heterogeneous hits comparable.

```json
{
  "id": "record:.lazy-harness/behavior/feature-surface.md",
  "kind": "record",
  "path": ".lazy-harness/behavior/feature-surface.md",
  "matchedBy": ["query-expansion", "record-digest"],
  "matchedQueries": ["기능패널", "기능화면", "feature panel"],
  "whyMatched": "Korean surface term may map to feature surface behavior.",
  "confidence": 0.82,
  "layer": "BDD",
  "readPriority": "required"
}
```

Requirements:

- `path` must be root-bound and relative to the current host when possible.
- `confidence` is a number from 0 to 1.
- `whyMatched` explains the evidence in actionable language.
- `matchedQueries` records packet query/evidence terms without storing long raw messages.
- Rows can point to records, source files, tests, graph edges, or project-profile artifacts.

### Stage 3 - Context Delivery Packet

The packet is the only stage rendered into prompt context or returned by a searcher subagent.

Top-level shape:

```json
{
  "schemaVersion": "1.0",
  "generatedAt": "2026-06-01T00:00:00.000Z",
  "instructionLevel": "self-resolve-before-change",
  "resolvedPhrase": "기능패널",
  "candidateMeanings": [
    {
      "label": "feature panel / FeaturePanel",
      "confidence": 0.76,
      "why": "Korean phrase can refer to a feature-surface UI surface, but exact component is not yet confirmed."
    }
  ],
  "queries": [
    {
      "query": "기능패널 기능화면 기능관리",
      "source": "llm-expansion",
      "purpose": "Korean user-facing aliases"
    },
    {
      "query": "feature panel feature panel feature schedule FeaturePanel",
      "source": "llm-expansion",
      "purpose": "English/code aliases"
    }
  ],
  "requiredRead": [
    {
      "path": ".lazy-harness/behavior/feature-surface.md",
      "kind": "record",
      "reason": "Confirm the intended feature-surface UI behavior before editing.",
      "confidence": 0.82,
      "whyMatched": "Matched Korean feature-surface aliases and behavior record digest.",
      "matchedQueries": ["기능패널", "feature panel"]
    }
  ],
  "optionalRead": [],
  "confidence": 0.76,
  "fallbackSearches": [
    "rg -n \"기능패널|feature panel|FeaturePanel\" .lazy-harness src tests"
  ],
  "instruction": "STOP before response: read requiredRead before answering, analyzing, planning, option-gating, or editing. Ask an option gate only after required reads/search if ambiguity remains."
}
```

## Instruction levels

`instructionLevel` tells the recipient what to do with the packet.

| Level | Meaning | Expected behavior |
|---|---|---|
| `digest-only` | Normal relevant-record digest is enough. | Use compact digest guidance; no special search loop required. |
| `harness-first-static` | Static `message.received` transport/search-debt row. | Do not infer user intent in shell/CLI; inject generic harness inventory/search instructions and let the LLM/searcher understand/search. |
| `self-resolve-before-answer` | The request likely depends on host context before explaining. | Generate/refine queries, search root-bound records/files, read required items, then answer/analyze/option-gate. |
| `self-resolve-before-change` | The request may lead to code/record changes. | Resolve candidate meanings and read required items before planning, option-gating, editing, or changing records. |
| `delegate-search` | Search is broad or high-risk enough to delegate. | Send the same contract to a searcher subagent and require a packet-shaped result. |

Selection guidance:

- Use `digest-only` when relevant records are direct and enough for the next response.
- Use `harness-first-static` only for default `message.received` transport/search-debt rows that intentionally avoid user-text semantic classification.
- Use `self-resolve-before-answer` for ambiguous questions that require host-specific grounding.
- Use `self-resolve-before-change` when the user asks to fix/change/build/debug an ambiguous project surface.
- Use `delegate-search` only when self-resolution would be too broad, parallel search would reduce risk, or a coordinator explicitly delegates.

## Field contract

### `candidateMeanings[]`

Each candidate meaning contains:

- `label`: concise meaning or alias group.
- `confidence`: 0 to 1.
- `why`: why this meaning is plausible.
- optional `language`: natural language or code style source, such as `ko`, `en`, or `symbol`.

If more than one candidate has close confidence, the agent must first perform root-bound search/read. Only after that evidence may it ask an option gate instead of silently choosing.

### `queries[]`

Queries record how the broker searched or wants the main LLM to search.

Each query contains:

- `query`: the actual query string or pattern.
- `source`: `user-phrase | llm-expansion | deterministic-expansion | record-link | profile-link | fallback`.
- `purpose`: why this query exists.
- optional `targets`: `records`, `project-profile`, `graph`, `source`, `tests`, `symbols`.

The broker should preserve user/token queries and record-authored metadata when user language differs from record/code language, but framework runtime code must not hardcode host/product aliases or generate semantic aliases by itself. Host-specific aliases must come from host records, Project Profile feature navigation, graph edges, implementation hints, source/test paths, or LLM/searcher root-bound search evidence.

Do not prematurely replace the LLM/searcher search loop with a CLI or backend. Context Delivery may produce compact packets, fallback commands, and candidate paths, but the main semantic work is still direct root-bound search/read by the LLM/searcher unless dogfood evidence proves a helper is reliably better.

### `requiredRead[]` and `optionalRead[]`

Read items contain:

- `path`: root-bound path or stable artifact path.
- `kind`: `record | project-profile | graph-edge | source-file | symbol | test | plan | schema | generated-index`.
- `reason`: what the reader should learn from this artifact.
- `confidence`: 0 to 1.
- `whyMatched`: match explanation.
- `matchedQueries`: compact query evidence.
- optional `layer`: DDD, SDD, BDD, TDD, ADR, SSOT, Planning.
- optional `symbols`: symbols/components/routes/tests worth inspecting.

`requiredRead` means the agent must deliberately read or inspect the item before answering/changing, unless it can explain why the packet is stale or unsafe. When a correlated packet has concrete required reads and sufficient confidence, those items are read-debt until evidence references the required paths. The default framework behavior journals and audits this debt instead of blocking concrete tools. `optionalRead` is useful context but not a prerequisite.

When the packet is low-confidence/self-resolve and has fallback searches but no concrete `requiredRead`, the packet records **search-debt** until the LLM or an explicit searcher handoff leaves root-bound search evidence. The harness does not claim to understand multilingual semantic intent by itself; it measures whether the LLM/searcher searched and audits misses after the response.

Framework-global records that merely contain a product-surface phrase as an example must not become `requiredRead` for a host product-surface request. They may remain candidate/optional evidence only when the request is not about lazy-harness, Context Delivery, retrieval, or framework behavior. If no host-local/project-specific record or code hint is found, emit fallback searches and ask/resolve before changing code.

### `fallbackSearches[]`

Fallback searches are explicit root-bound next steps when confidence is low, required items are missing, or candidates conflict.

Rules:

- They must stay inside the current host root.
- They should be copy-pasteable commands or tool-search descriptions.
- They should include multilingual/code aliases when relevant.
- They are instructions for the main LLM or searcher, not commands executed inside `message.received`.
- They remain visible so the LLM/searcher can inspect and adapt the search, instead of blindly trusting a hidden CLI/search backend.

## Rendering into `system_reminder`

When rendered by `message.received`, the packet must stay concise and actionable.

Example Markdown rendering:

```md
Context Delivery Packet
Instruction: self-resolve-before-change
Resolved phrase: 기능패널
Confidence: 0.76

Candidate meanings
- feature panel / FeaturePanel (0.76): Korean phrase can refer to a feature-surface UI surface.

Required read before answer/analyze/plan/option-gate/change
- `.lazy-harness/behavior/feature-surface.md` - record - 0.82
  - Reason: Confirm the intended feature-surface UI behavior before editing.
  - Matched: 기능패널, feature panel

Fallback searches
- `rg -n "기능패널|feature panel|FeaturePanel" .lazy-harness src tests`

Instruction: STOP before response: read required items first. If candidates still conflict after search/read evidence, ask an option gate.
```

Rendering rules:

- Include path, kind, confidence, reason, and matched query evidence for each required item.
- Prefer required-read bullets over raw chunks.
- Keep normal output under 600 tokens and hard ceiling under 1,000 tokens for pre-response use.
- If output would exceed budget, keep highest-confidence required reads and move the rest to `fallbackSearches` or `optionalRead`.

## Static message.received transport

The default `message.received` hook is a bounded static transport. It does not identify surface-like, implementation-likely, question-like, smalltalk-like, or change-like requests from raw user text. CLI/shell code cannot understand user intent; understanding belongs to the LLM/searcher or an explicitly delegated read-only searcher handoff.

This protocol is not a full `ContextDeliveryPacket`; it is a static instruction to the main LLM to inspect actual harness inventory/records and produce or approximate a packet by self-searching with root-bound tools before answering or changing code.

Allowed rendering:

```md
Harness-first static transport
- Instruction: harness-first-static
- This shell hook does not classify or interpret the user message. Do not branch on raw text such as `fix`, `test`, `고쳐`, or `확인`.
- Before answering, analyzing, planning, option-gating, or editing, the LLM/searcher inspects actual `.lazy-harness` inventory, generated index presence, graph/profile pointers, and canonical records/source.
- Use any root-bound read-only/search/query affordance; tool names in examples are not a policy allowlist.
- Only after inventory/content grounding should the LLM/searcher expand multilingual/code aliases or broader query terms.
- Use main-agent self-search first; delegate search only when broad, risky, or parallel search would reduce risk.
```

Rules:

- The default `message.received` hook emits the same static protocol for any non-empty user message after resolving host root.
- Simple digest, `self-resolve-before-answer`, and `self-resolve-before-change` remain packet-generator/subagent output levels, not shell-hook text-classifier outputs.
- Shell/CLI hooks must not choose `self-resolve-before-answer` vs `self-resolve-before-change` from raw user text.
- The hook must not call a subagent, `jcode run`, hosted RAG, or other heavy model path synchronously for this protocol.
- Protocol-only injections are not enough evidence for response audit to claim a concrete surfaced record was ignored; audit must wait for packet/journal evidence.

## `기능패널` example

Input:

```text
기능패널 고쳐줘
```

The broker must not pretend to understand host semantic aliases by itself. It may preserve the original/token query and provide fallback-search/searcher-handoff instructions; the LLM or searcher must expand candidates across Korean, English, and code-style names before answering, planning, option-gating, or acting:

- Korean aliases: `기능패널`, `기능 패널`, `기능화면`, `기능관리`, `기능관리페이지`
- English aliases: `feature panel`, `feature panel`, `feature schedule`, `feature panel`, `schedule grid`
- Code aliases: `FeatureSurface`, `FeaturePanel`, `FeatureSurfacePage`, `AppointmentPage`

Expected packet posture:

- `instructionLevel`: `self-resolve-before-change`
- `candidateMeanings`: literal/token candidates only unless record-authored aliases were directly matched
- `queries`: include the original/token request, not framework-authored semantic alias expansions
- `requiredRead`: project profile or BDD/SDD/SSOT records if found
- `fallbackSearches`: root-bound search across `.lazy-harness`, source, and tests; LLM/searcher performs semantic expansion before running those searches
- If no canonical record/code candidate is found, ask the user which surface they mean and capture the confirmed alias later.
- Framework SDD/ADR examples containing `기능패널` are not themselves sufficient required-read evidence for a host product-surface change.

## Privacy and fail-open requirements

Context Delivery Packet runtime state is non-canonical context.

Privacy requirements:

- Do not persist raw `last_user_message`, full prompt, full transcript, or raw assistant response in generated packet journals.
- Short query strings and candidate labels may be stored only when they are derived from record-authored aliases or compact user-surface terms needed for debugging.
- Prefer short hashes for session/message identifiers if a future journal links packets to turns.
- Record paths, titles, digest bullets, schema names, and source file paths are allowed.
- Protocol-only self-resolution injections should not write raw user messages or synthetic candidate meanings to the surfaced digest journal.
- Packet evidence journals may store required/optional read paths, kind/layer/confidence, symbol names, matched-query counts, packet hash, and message/session hashes, but not raw request text or raw record bullets.

Fail-open requirements:

- `message.received` must stay bounded by the existing Jcode hook timeout, currently 800ms.
- Timeout, malformed packet, missing generated index, or unavailable optional subagent must not block the turn.
- Failures may inject a small self-resolution instruction only if it is safe and within budget; otherwise emit nothing.
- Heavy query expansion, `jcode run`, or subagent work must not run synchronously inside `message.received` without a separate timeout/recursion guard design.

## Search/read debt journal and audit

The Context Delivery Packet is transport-agnostic, but the current Jcode default transport does not run the bounded local producer automatically. `message.received` emits a direct framework-structured search prompt and appends a sanitized direct-search debt row. `lazy context-delivery --journal` remains available for explicit/manual/dogfood packet evidence collection.

The response lifecycle uses that same packet journal as non-canonical search/read-debt state:

```text
message.received
→ direct-search prompt producer
→ sanitized direct-search debt row
→ if concrete requiredRead exists: read-debt
→ if requiredRead is unknown but fallback searches exist: search-debt
→ search/read tools and explicit searcher handoff allowed
→ generic action guard denies action until search/read evidence exists
```

Rules:

- The default producer emits a harness-first inventory/search protocol only; explicit Context Delivery helpers may surface literal/record-authored hints from existing indexes when invoked manually, but they must not implement semantic search or host-specific alias mapping.
- The LLM or a searcher subagent follows lazy-harness instructions first, inspects actual stored records/files, and only then performs semantic expansion and root-bound search for ambiguous terms such as Korean `기능패널`.
- The debt journal does not create project/tool policy. It records direct-search or packet-scoped `search-debt` and `read-debt`; the generic guard only checks whether the LLM/searcher left search/read evidence before response/action.
- Search-debt is satisfied when recent tool evidence shows root-bound harness-following inventory/search/read evidence, or explicit read-only searcher handoff evidence. Tool names such as `agentgrep`, `grep`/`rg`/`find`, `tree`, `git ls-files`, or future query tools are examples, not a closed allowlist. Deterministic `context-delivery`/`relevant-record-query` CLI output does not satisfy direct-search debt by itself.
- Read-debt is satisfied when recent tool evidence references every concrete required path in the correlated packet row.
- Packet selection itself must be strictly correlated: if `message_id` is available, the packet row must match the message hash and, when available, the session hash. Session-only matching is allowed only when message id is absent.
- Evidence sources include the current lifecycle payload's `recent_tool_calls` and the local `.jcode/hooks/tool-events.jsonl` after-tool journal for the same message/session. The journal fallback exists because some Jcode/provider paths may omit previous `Read` calls from later lifecycle payloads, which would otherwise create false-positive debt advisories.
- To avoid false positives in the opposite direction, the journal fallback is strict: if the current payload has a `message_id`, only the same `message_id` is accepted; same-session fallback is used only when message id is unavailable. Tool-events older than the correlated packet epoch are ignored.
- Mixed read+action batches do not satisfy the debt in the same tool call; reads must happen before the response/action evidence that claims the debt is satisfied.
- If the packet lacks concrete required paths or fallback searches, confidence is below threshold, no safe message/session correlation exists, or the producer times out, the guard fails open.
- This current transport uses lifecycle hooks, but the same packet/debt semantics are ACP-compatible and may be carried by a protocol layer later.

## Generic search/read evidence guard coverage

- Status: active; supersedes earlier audit-only wording
- Boundary: direct-search/read debt is journaled at turn start and the generic evidence guard denies action when search/read evidence is missing for the correlated turn.
- Scope: framework-global
- User confirmation: 2026-06-02 user corrected that the framework must not implement semantic search or attach tool-specific adapters; LLM/searcher performs root-bound search first, and the harness guards missing search/read evidence generically. 2026-06-03 user clarified that the important contract is following lazy-harness instructions and actual stored record/file inventory first, without restricting agents to a fixed tool allowlist.
- Evidence: repeated dogfood screenshots showed agents acting from wrong Figma node/runtime assumptions and skipping records/MCP context even after reminders; chat corrections included `기록을 지금 하나도 안보네??`, `검색을 먼저 하게 강제하고 그다음에 작업하는거로 하는거지`, and `검색을 했나 안했나를 측정하게하고 검색을 안했으면 먼저 하도록 강제`.
- Existing softer coverage: relevant-record digest injection, lightweight self-resolution, Context Delivery packet journal, `.jcode/hooks/tool-events.jsonl` evidence fallback, and response.completed advisory existed but were too late or too weak to prevent action drift.
- Fixture: `.lazy-harness/scripts/self-test.py`
- Narrowness: the guard activates only for correlated direct-search/read-debt rows or explicit Context Delivery packet rows with either concrete requiredRead paths or explicit fallback searches; search/read tools and explicit searcher handoff remain allowed; clean/no-debt turns remain silent; it is not a broad edit/write or tool-specific project-policy adapter.
- Rollback: disable the generated generic search/read evidence guard block or direct-search debt journaling; response.completed advisory remains as fallback.

## Searcher subagent handoff

A searcher subagent receives the same contract, not a separate prose-only prompt.

Phase 6 implementation exposes a prompt renderer:

```bash
.lazy-harness/bin/lazy context-delivery --message "기능패널 고쳐줘" --handoff-prompt
```

This command renders a handoff prompt only. It does not spawn a subagent, call `jcode run`, mutate files, or run inside `message.received`. The main LLM may explicitly pass the prompt to a searcher subagent when self-resolution is too broad, high-risk, or benefits from parallel search.

Handoff prompt must include:

- current user request,
- host root,
- root-bound constraint,
- candidate queries if already known,
- instruction to return a `ContextDeliveryPacket` shape,
- instruction not to mutate files.
- instruction not to return raw grep chunks or prose-only summaries.

Subagent result must include:

- `instructionLevel`,
- `candidateMeanings`,
- `queries`,
- `requiredRead`,
- `optionalRead`,
- `confidence`,
- `fallbackSearches`,
- concise `instruction`.

The main LLM remains responsible for reading `requiredRead` items before answering, planning, option-gating, or acting.

## Relationship to existing SDDs

- `record-digest-format.md` defines compact record-authored retrieval metadata.
- `relevant-record-query.md` defines the current digest query contract.
- `pre-response-rule-context.md` defines the bounded lifecycle injection surface.
- This SDD defines the richer packet that future broker phases produce after literal/token query collection and evidence fusion; semantic expansion remains LLM/searcher work.
- `response-rule-audit.md` consumes explicit packet evidence journal rows as advisory-only required-read audit after false-positive-safe fixtures exist.
- `record-decision-broker.md` mirrors this pre-turn packet with a post-turn Record Decision Packet for record-write decisions.

## Implementation map

- Status: `partially-implemented through Phase 7`
- Primary files:
  - `.lazy-harness/spec/platform/context-delivery-contract.md` - this SDD and packet contract.
  - `.lazy-harness/schemas/context-delivery-packet.schema.json` - JSON Schema for packet-shaped outputs.
  - `.lazy-harness/schemas/context-index.schema.json` - JSON Schema for generated Context Delivery index cache.
  - `.lazy-harness/planning/native-context-broker-implementation-plan.md` - phase plan that schedules implementation after this contract.
  - `.lazy-harness/manifests/init-categories.json` - sync manifest entry for this SDD; schema directory syncs packet schema.
  - `.lazy-harness/scripts/context-index.ts` - deterministic generated context-index builder.
  - `.lazy-harness/scripts/context-delivery.ts` - explicit/manual/dogfood dual-mode retrieval packet generator using original/token queries plus record-authored metadata; it does not implement semantic search or host-specific alias mapping and is not run automatically from `message.received`. Phase 6 `--handoff-prompt` renders optional searcher handoff prompt with packet seed; Phase 7 `--journal` writes sanitized packet evidence rows.
  - `.lazy-harness/bin/lazy` - exposes `lazy context-delivery` including `--handoff-prompt` and `--journal` passthrough.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` - bounded pre-turn renderer for harness-first inventory/search prompt plus sanitized search-debt journal; it injects compact real layer/file inventory and generated-index/graph/profile pointers without performing semantic search.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` - generic pre-action evidence guard that checks packet-scoped search/read debt against root-bound LLM/searcher evidence; it does not perform search and is not a concrete-tool adapter or allowlist.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` - consumes correlated packet evidence rows plus `recent_tool_calls` / `.jcode/hooks/tool-events.jsonl` evidence for advisory response backstop.
  - `.lazy-harness/spec/platform/record-decision-broker.md` - Phase 8 mirror contract for post-turn record actions.
  - `.lazy-harness/generated/README.md` - generated artifact policy for `context-index.json` as non-canonical cache.
  - `.lazy-harness/scripts/self-test.py` - contract/schema/document fixture validation.
  - `.lazy-harness/knowledge/graph.jsonl` - graph rows linking contract, schema, plan, and tests.
- Future implementation files:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` - future full-packet renderer once packet generation is safe for pre-turn use.
- Flow:
  1. Request enters `message.received`.
  2. Any non-empty user message receives the same compact actual `.lazy-harness` inventory/search protocol and sanitized search-debt journal row from `message.received`.
  3. The main LLM/searcher must start from actual record filenames/layers/index pointers before free-form alias expansion, without hook-time semantic classification.
  4. Future broker may emit a full Context Delivery Packet.
  5. Main LLM may call `lazy context-delivery --handoff-prompt` and delegate the rendered prompt when self-resolution is insufficient.
  6. Default `message.received` journals direct-search debt; main LLM or dogfood tooling may explicitly call `lazy context-delivery --journal` to record sanitized packet evidence when useful.
  7. Main LLM/searcher performs root-bound semantic expansion/search/read work before answering, planning, option-gating, or acting.
  8. Generic pre-action evidence guard denies action when correlated packet search/read debt lacks evidence.
  9. Response audit may advise when correlated packet evidence and mutation suggest required search/read evidence was skipped.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_context_delivery_contract_sdd` validates the SDD, schema enum, required fields, and `기능패널` example cues.
  - `.lazy-harness/scripts/self-test.py#check_message_received_hook_context_injection` validates static harness-first inventory/search prompt output, examples-not-allowlist wording, deterministic-helper non-authority, tree/directory inventory evidence, generic future query evidence, identical prompt body for different user text, and absence of user-text semantic classifier code.
  - `.lazy-harness/scripts/self-test.py#check_context_delivery_optional_handoff_phase6` validates the handoff prompt, delegate-search seed packet, no-mutation instructions, schema-return contract, and absence of hook-time `jcode run`/handoff execution.
  - `.lazy-harness/scripts/self-test.py#check_context_delivery_packet_journal_phase7` validates sanitized packet journaling and response audit behavior.
  - `.lazy-harness/scripts/self-test.py#check_read_debt_permit_generic_external_action` validates that unknown external MCP-like actions cannot bypass search-debt before root-bound search evidence exists.

## Validation plan

Minimum Phase 1 validation:

- JSON schema loads as valid JSON.
- Schema includes the five `instructionLevel` values.
- SDD includes `## Rule digest`.
- SDD includes raw hit, normalized evidence, and Context Delivery Packet stages.
- SDD includes `기능패널` example while explicitly assigning semantic expansion to the LLM/searcher, not deterministic framework code.
- SDD includes privacy, fail-open, rendering, and subagent handoff rules.

Future implementation validation:

- Fixture: direct digest request returns `digest-only`.
- Fixture: packet generator may return `self-resolve-before-change` with original/token queries and fallback-search/searcher instructions, not framework-authored multilingual aliases.
- Fixture: `message.received` injects the same static harness-first inventory/search prompt for different non-empty user messages, includes compact actual layer/file inventory and generated-index pointers, and keeps tool names as examples rather than a required allowlist.
- Fixture: packet uses literal/token queries plus record-authored metadata; semantic expansion is performed by LLM/searcher root-bound searches.
- Fixture: framework-global example-only matches do not become required-read host product-surface evidence.
- Fixture: missing index falls back to root-bound source scan.
- Fixture: searcher handoff prompt returns packet-shaped seed/return contract without executing mutations or adding hook-time `jcode run`/subagent latency.
- Fixture: packet evidence journal stores sanitized rows without raw request text or raw record bullets.
- Fixture: message.received injects STOP-before-response harness-first inventory/search instructions; generic evidence guard blocks missing harness-following evidence before tool action; response audit stays silent when evidence was respected, no mutation happened, or no packet was correlated.

## Rule placement

- Rule: Native Context Broker outputs must use a stable Context Delivery Packet with required-read paths, reasons, confidence, query evidence, privacy, and fail-open semantics.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/context-delivery-contract.md`
- Why not AGENTS.md: this is a platform contract and output schema, not compact operational grammar.
- Why not `.jcode`: this must sync to hosts and be shared by lazy-harness scripts, hooks, records, and optional subagents.
- Confirmation: user-confirmed by approving Native Context Broker Phase 1 continuation.

## Discovery capture

- DDD: no domain entity added; `기능패널` is an example surface alias, not a canonical product-domain record in this framework repo.
- SDD: this record defines the Context Delivery Packet contract.
- BDD: future agent behavior should read required context before answering/changing ambiguous surfaces.
- TDD: self-test covers SDD/schema/example completeness; later packet generator fixtures required.
- ADR: ADR 0041 remains the architecture decision for organic hybrid rule guidance.
- SSOT: canonical truth remains records/source; packet and generated indexes are non-canonical context.
- Planning: Native Context Broker implementation plan Phase 1 is now specified by this SDD.
