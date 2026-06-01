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
  - Korean or multilingual terms such as `예약시트` must bridge to English records, routes, symbols, or tests
- Must:
  - deliver required-read context with path, kind, reason, confidence, and matched query evidence
  - normalize raw hits before rendering; never inject raw grep chunks as the final broker output
  - keep canonical truth in `.lazy-harness` records and source files; generated packets are non-canonical context
  - fail open and stay bounded when used from `message.received`
  - allow lightweight self-resolution instructions when a full packet is unavailable but a request is implementation-likely
  - make optional search handoff prompts return the same packet-shaped contract and forbid mutations/raw chunks
  - ask an option gate when candidate meanings conflict and confidence is not high enough to proceed
- Must not:
  - make external vector DB, hosted RAG, or subagents mandatory for every turn
  - store raw user messages, full transcripts, or raw assistant responses in context-delivery runtime state
  - use Context Delivery Packet output as canonical record truth
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
  "path": ".lazy-harness/behavior/reservation-management.md",
  "matchedText": "예약관리페이지",
  "query": "예약시트"
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
  "id": "record:.lazy-harness/behavior/reservation-management.md",
  "kind": "record",
  "path": ".lazy-harness/behavior/reservation-management.md",
  "matchedBy": ["query-expansion", "record-digest"],
  "matchedQueries": ["예약시트", "예약표", "reservation sheet"],
  "whyMatched": "Korean surface term may map to reservation management behavior.",
  "confidence": 0.82,
  "layer": "BDD",
  "readPriority": "required"
}
```

Requirements:

- `path` must be root-bound and relative to the current host when possible.
- `confidence` is a number from 0 to 1.
- `whyMatched` explains the evidence in actionable language.
- `matchedQueries` records query expansion evidence without storing long raw messages.
- Rows can point to records, source files, tests, graph edges, or project-profile artifacts.

### Stage 3 - Context Delivery Packet

The packet is the only stage rendered into prompt context or returned by a searcher subagent.

Top-level shape:

```json
{
  "schemaVersion": "1.0",
  "generatedAt": "2026-06-01T00:00:00.000Z",
  "instructionLevel": "self-resolve-before-change",
  "resolvedPhrase": "예약시트",
  "candidateMeanings": [
    {
      "label": "reservation sheet / reservation management table",
      "confidence": 0.76,
      "why": "Korean phrase can refer to a reservation UI surface, but exact component is not yet confirmed."
    }
  ],
  "queries": [
    {
      "query": "예약시트 예약표 예약관리",
      "source": "llm-expansion",
      "purpose": "Korean user-facing aliases"
    },
    {
      "query": "reservation sheet booking table appointment schedule ReservationTable",
      "source": "llm-expansion",
      "purpose": "English/code aliases"
    }
  ],
  "requiredRead": [
    {
      "path": ".lazy-harness/behavior/reservation-management.md",
      "kind": "record",
      "reason": "Confirm the intended reservation UI behavior before editing.",
      "confidence": 0.82,
      "whyMatched": "Matched Korean reservation surface aliases and behavior record digest.",
      "matchedQueries": ["예약시트", "reservation sheet"]
    }
  ],
  "optionalRead": [],
  "confidence": 0.76,
  "fallbackSearches": [
    "rg -n \"예약|reservation|booking|appointment|schedule\" .lazy-harness src tests"
  ],
  "instruction": "Read requiredRead before answering or editing. If candidate meanings conflict, ask an option gate."
}
```

## Instruction levels

`instructionLevel` tells the recipient what to do with the packet.

| Level | Meaning | Expected behavior |
|---|---|---|
| `digest-only` | Normal relevant-record digest is enough. | Use compact digest guidance; no special search loop required. |
| `self-resolve-before-answer` | The request likely depends on host context before explaining. | Generate/refine queries, search root-bound records/files, read required items, then answer. |
| `self-resolve-before-change` | The request may lead to code/record changes. | Resolve candidate meanings and read required items before editing or planning changes. |
| `delegate-search` | Search is broad or high-risk enough to delegate. | Send the same contract to a searcher subagent and require a packet-shaped result. |

Selection guidance:

- Use `digest-only` when relevant records are direct and enough for the next response.
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

If more than one candidate has close confidence and the next action would change code/records, the agent must ask an option gate instead of silently choosing.

### `queries[]`

Queries record how the broker searched or wants the main LLM to search.

Each query contains:

- `query`: the actual query string or pattern.
- `source`: `user-phrase | llm-expansion | deterministic-expansion | record-link | profile-link | fallback`.
- `purpose`: why this query exists.
- optional `targets`: `records`, `project-profile`, `graph`, `source`, `tests`, `symbols`.

The broker should include multilingual and code-style expansions when user language differs from record/code language.

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

`requiredRead` means the agent must deliberately read or inspect the item before answering/changing, unless it can explain why the packet is stale or unsafe. `optionalRead` is useful context but not a prerequisite.

Framework-global records that merely contain a product-surface phrase as an example must not become `requiredRead` for a host product-surface request. They may remain candidate/optional evidence only when the request is not about lazy-harness, Context Delivery, retrieval, or framework behavior. If no host-local/project-specific record or code hint is found, emit fallback searches and ask/resolve before changing code.

### `fallbackSearches[]`

Fallback searches are explicit root-bound next steps when confidence is low, required items are missing, or candidates conflict.

Rules:

- They must stay inside the current host root.
- They should be copy-pasteable commands or tool-search descriptions.
- They should include multilingual/code aliases when relevant.
- They are instructions for the main LLM or searcher, not commands executed inside `message.received`.

## Rendering into `system_reminder`

When rendered by `message.received`, the packet must stay concise and actionable.

Example Markdown rendering:

```md
Context Delivery Packet
Instruction: self-resolve-before-change
Resolved phrase: 예약시트
Confidence: 0.76

Candidate meanings
- reservation sheet / reservation management table (0.76): Korean phrase can refer to a reservation UI surface.

Required read before answer/change
- `.lazy-harness/behavior/reservation-management.md` - record - 0.82
  - Reason: Confirm the intended reservation UI behavior before editing.
  - Matched: 예약시트, reservation sheet

Fallback searches
- `rg -n "예약|reservation|booking|appointment|schedule" .lazy-harness src tests`

Instruction: Read required items first. If candidates conflict, ask an option gate.
```

Rendering rules:

- Include path, kind, confidence, reason, and matched query evidence for each required item.
- Prefer required-read bullets over raw chunks.
- Keep normal output under 600 tokens and hard ceiling under 1,000 tokens for pre-response use.
- If output would exceed budget, keep highest-confidence required reads and move the rest to `fallbackSearches` or `optionalRead`.

## Lightweight self-resolution protocol

Phase 5 adds a bounded protocol-only rendering for `message.received` when the hook can identify a surface-like or implementation-likely request but should not run heavy model/subagent work inside the 800ms pre-turn budget.

This protocol is not a full `ContextDeliveryPacket`; it is an instruction to the main LLM to produce or approximate one by self-searching with root-bound tools before answering or changing code.

Allowed rendering:

```md
Context Delivery self-resolution
- Instruction: self-resolve-before-change
- Before answering or editing, generate 2-5 candidate meanings and multilingual/code query expansions.
- Run root-bound searches in `.lazy-harness`, source, and tests with available read/grep/bash tools.
- Read high-confidence records/files before acting; if candidate meanings conflict, ask an option gate.
- Use main-agent self-search first; delegate search only when broad, risky, or parallel search would reduce risk.
```

Rules:

- Simple digest matches stay `digest-only` and must not receive this extra protocol.
- Surface-like implementation/change requests may receive `self-resolve-before-change` even when no high-confidence required-read record is available yet.
- Explanation/question requests may receive `self-resolve-before-answer` only when the message is surface-like enough to need host context.
- The hook must not call a subagent, `jcode run`, hosted RAG, or other heavy model path synchronously for this protocol.
- Protocol-only injections are not enough evidence for response audit to claim a concrete surfaced record was ignored; audit must wait for packet/journal evidence.

## `예약시트` example

Input:

```text
예약시트 고쳐줘
```

The broker must not rely only on literal Korean keyword matches. It should expand candidates across Korean, English, and code-style names:

- Korean aliases: `예약시트`, `예약 시트`, `예약표`, `예약관리`, `예약관리페이지`
- English aliases: `reservation sheet`, `booking sheet`, `appointment schedule`, `reservation table`, `schedule grid`
- Code aliases: `ReservationSheet`, `ReservationTable`, `ReservationManagementPage`, `AppointmentPage`

Expected packet posture:

- `instructionLevel`: `self-resolve-before-change`
- `candidateMeanings`: at least one reservation UI/table/schedule candidate
- `queries`: include Korean, English, and code-style expansions
- `requiredRead`: project profile or BDD/SDD/SSOT records if found
- `fallbackSearches`: root-bound search across `.lazy-harness`, source, and tests
- If no canonical record/code candidate is found, ask the user which surface they mean and capture the confirmed alias later.
- Framework SDD/ADR examples containing `예약시트` are not themselves sufficient required-read evidence for a host product-surface change.

## Privacy and fail-open requirements

Context Delivery Packet runtime state is non-canonical context.

Privacy requirements:

- Do not persist raw `last_user_message`, full prompt, full transcript, or raw assistant response in generated packet journals.
- Short query strings and candidate labels may be stored only when they are derived from record-authored aliases or compact user-surface terms needed for debugging.
- Prefer short hashes for session/message identifiers if a future journal links packets to turns.
- Record paths, titles, digest bullets, schema names, and source file paths are allowed.
- Protocol-only self-resolution injections should not write raw user messages or synthetic candidate meanings to the surfaced digest journal.

Fail-open requirements:

- `message.received` must stay bounded by the existing Jcode hook timeout, currently 800ms.
- Timeout, malformed packet, missing generated index, or unavailable optional subagent must not block the turn.
- Failures may inject a small self-resolution instruction only if it is safe and within budget; otherwise emit nothing.
- Heavy query expansion, `jcode run`, or subagent work must not run synchronously inside `message.received` without a separate timeout/recursion guard design.

## Searcher subagent handoff

A searcher subagent receives the same contract, not a separate prose-only prompt.

Phase 6 implementation exposes a prompt renderer:

```bash
.lazy-harness/bin/lazy context-delivery --message "예약시트 고쳐줘" --handoff-prompt
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

The main LLM remains responsible for reading `requiredRead` items before acting.

## Relationship to existing SDDs

- `record-digest-format.md` defines compact record-authored retrieval metadata.
- `relevant-record-query.md` defines the current digest query contract.
- `pre-response-rule-context.md` defines the bounded lifecycle injection surface.
- This SDD defines the richer packet that future broker phases produce after query expansion and fusion.
- `response-rule-audit.md` may later consume packet evidence, but only after false-positive-safe fixtures exist.

## Implementation map

- Status: `partially-implemented through Phase 6`
- Primary files:
  - `.lazy-harness/spec/platform/context-delivery-contract.md` - this SDD and packet contract.
  - `.lazy-harness/schemas/context-delivery-packet.schema.json` - JSON Schema for packet-shaped outputs.
  - `.lazy-harness/schemas/context-index.schema.json` - JSON Schema for generated Context Delivery index cache.
  - `.lazy-harness/planning/native-context-broker-implementation-plan.md` - phase plan that schedules implementation after this contract.
  - `.lazy-harness/manifests/init-categories.json` - sync manifest entry for this SDD; schema directory syncs packet schema.
  - `.lazy-harness/scripts/context-index.ts` - deterministic generated context-index builder.
  - `.lazy-harness/scripts/context-delivery.ts` - dual-mode retrieval packet generator using query expansion and file/source hint fusion; Phase 6 `--handoff-prompt` renders optional searcher handoff prompt with packet seed.
  - `.lazy-harness/bin/lazy` - exposes `lazy context-delivery` including `--handoff-prompt` passthrough.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` - bounded pre-turn renderer for relevant-record digests plus Phase 5 lightweight self-resolution protocol.
  - `.lazy-harness/generated/README.md` - generated artifact policy for `context-index.json` as non-canonical cache.
  - `.lazy-harness/scripts/self-test.py` - contract/schema/document fixture validation.
  - `.lazy-harness/knowledge/graph.jsonl` - graph rows linking contract, schema, plan, and tests.
- Future implementation files:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` - future full-packet renderer once packet generation is safe for pre-turn use.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` - future packet-aware audit, after fixtures.
- Flow:
  1. Request enters `message.received`.
  2. Existing digest query may return `digest-only`.
  3. Surface-like implementation requests may receive lightweight self-resolution instructions without heavy hook latency.
  4. Future broker may emit a full Context Delivery Packet.
  5. Main LLM may call `lazy context-delivery --handoff-prompt` and delegate the rendered prompt when self-resolution is insufficient.
  6. Main LLM reads required items from the returned packet before acting.
  7. Response audit may later verify required-read usage only with strong evidence.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_context_delivery_contract_sdd` validates the SDD, schema enum, required fields, and `예약시트` example cues.
  - `.lazy-harness/scripts/self-test.py#check_message_received_hook_context_injection` validates digest-only output for simple record matches and `self-resolve-before-change` protocol for `예약시트 고쳐줘` without mandatory subagent latency.
  - `.lazy-harness/scripts/self-test.py#check_context_delivery_optional_handoff_phase6` validates the handoff prompt, delegate-search seed packet, no-mutation instructions, schema-return contract, and absence of hook-time `jcode run`/handoff execution.

## Validation plan

Minimum Phase 1 validation:

- JSON schema loads as valid JSON.
- Schema includes the four `instructionLevel` values.
- SDD includes `## Rule digest`.
- SDD includes raw hit, normalized evidence, and Context Delivery Packet stages.
- SDD includes `예약시트` example with Korean, English, and code-style expansion cues.
- SDD includes privacy, fail-open, rendering, and subagent handoff rules.

Future implementation validation:

- Fixture: direct digest request returns `digest-only`.
- Fixture: `예약시트 고쳐줘` returns `self-resolve-before-change` and multilingual queries.
- Fixture: `message.received` keeps simple digest requests digest-only but injects lightweight `self-resolve-before-change` protocol for ambiguous project-surface changes.
- Fixture: packet fuses record/profile/code/test hits into required-read items.
- Fixture: framework-global example-only matches do not become required-read host product-surface evidence.
- Fixture: missing index falls back to root-bound source scan.
- Fixture: searcher handoff prompt returns packet-shaped seed/return contract without executing mutations or adding hook-time `jcode run`/subagent latency.
- Fixture: response audit stays silent when required-read was respected or no packet was surfaced.

## Rule placement

- Rule: Native Context Broker outputs must use a stable Context Delivery Packet with required-read paths, reasons, confidence, query evidence, privacy, and fail-open semantics.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/context-delivery-contract.md`
- Why not AGENTS.md: this is a platform contract and output schema, not compact operational grammar.
- Why not `.jcode`: this must sync to hosts and be shared by lazy-harness scripts, hooks, records, and optional subagents.
- Confirmation: user-confirmed by approving Native Context Broker Phase 1 continuation.

## Discovery capture

- DDD: no domain entity added; `예약시트` is an example surface alias, not a canonical product-domain record in this framework repo.
- SDD: this record defines the Context Delivery Packet contract.
- BDD: future agent behavior should read required context before answering/changing ambiguous surfaces.
- TDD: self-test covers SDD/schema/example completeness; later packet generator fixtures required.
- ADR: ADR 0041 remains the architecture decision for organic hybrid rule guidance.
- SSOT: canonical truth remains records/source; packet and generated indexes are non-canonical context.
- Planning: Native Context Broker implementation plan Phase 1 is now specified by this SDD.
