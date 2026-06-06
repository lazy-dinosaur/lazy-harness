# SDD - Context Delivery Candidate Retrieval Contract

Status: accepted
Date: 2026-06-06
Layer: SDD
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
Related SDD: `.lazy-harness/spec/platform/relevant-record-query.md`
Related schema: `.lazy-harness/schemas/context-delivery-packet.schema.json`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - implementing or using `lazy context-delivery` / `context-delivery.ts`
  - producing candidate record/source/test hits from generated indexes, feature navigation, graph edges, or record-authored metadata
  - distinguishing generic search/read-debt from CLI-selected required reads
- Must:
  - return candidate evidence only: path, kind, matched fields, matched queries, optional layer/title/symbol hints, and fallback search commands
  - match structured record-authored fields such as aliases, surface terms, related records, implementation hints, graph links, and feature navigation pointers rather than generic `Applies when`/`Must`/`Must not` prose
  - keep generated packets non-canonical
  - preserve raw query text only in process output requested by the LLM/user; do not journal raw messages by default
  - allow `--handoff-prompt` to ask a read-only searcher for candidate hits only
  - keep default `message.received` as static search/read-debt transport, not an automatic context-delivery backend
  - keep generic search/read-debt enforcement in lifecycle hooks so the LLM/searcher must search/read before mutation
- Must not:
  - decide user intent, risk, importance, gate, required reads, record-write need, or next action
  - split output into `requiredRead` vs `optionalRead`
  - emit `confidence`, `instructionLevel`, `self-resolve-before-change`, `option-gate-needed`, or similar action labels from raw user text
  - journal context-delivery selected reads as read-debt; read-debt comes from generic static transport or LLM/searcher-confirmed evidence, not CLI importance judgment
  - hardcode host-specific semantic aliases in framework code
- Record completion:
  - changes to candidate fields, schema, CLI flags, or lifecycle integration update this SDD, `.lazy-harness/ssot/cli-tool-boundary.md`, and tests
- Related records:
  - `.lazy-harness/ssot/cli-tool-boundary.md`
  - `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - `.lazy-harness/spec/platform/context-tier-manifest.md`

## Purpose

`context-delivery.ts` is an explicit tool the LLM/searcher may call to list deterministic candidate hits.

It answers:

```text
For this literal query, which record-authored fields, feature navigation pointers, graph links, source files, tests, or schemas match?
```

It does not answer:

```text
What does the user intend?
Which file is important?
What must be read before action?
Should a record be written?
What is the next action?
```

Those judgments belong to the LLM/searcher after root-bound reads.

## Packet shape

Schema version: `2.0`
Mode: `candidate-retrieval`

Required top-level fields:

- `schemaVersion`
- `generatedAt`
- `mode`
- `queries[]`
- `candidateHits[]`
- `fallbackSearches[]`
- `notes[]`

Candidate hit fields:

- `path`
- `kind`: `record | project-profile | graph-edge | source-file | test | schema | generated-index`
- `matchedQueries[]`
- `matchedFields[]`
- optional `layer`
- optional `title`
- optional `symbols[]`

Forbidden packet fields:

- `requiredRead`
- `optionalRead`
- `confidence`
- `instructionLevel`
- `candidateMeanings`
- `instruction`
- `recordSearch`
- `recordCapture`
- `gate`
- `risk`
- `intent`

## Read-debt distinction

Read-debt is still required.

The default `message.received` hook creates generic search/read-debt so mutation/action is blocked until the turn shows root-bound harness-following search/read evidence. This is not removed.

What is removed is CLI-selected read-debt:

```text
context-delivery CLI sees raw user text
→ picks requiredRead
→ journals those paths
→ guard treats those paths as required
```

That is forbidden because it makes CLI output the semantic authority.

Allowed flow:

```text
message.received static search-debt
→ LLM/searcher reads inventory/records/source/tests
→ LLM may call context-delivery for candidate hits
→ LLM decides which candidates matter and reads evidence
→ action/mutation only after generic evidence guard is satisfied
```

## Static message.received transport

The default `message.received` hook is a bounded static transport. It emits the same instruction for any non-empty user message and does not branch on words such as `fix`, `test`, `고쳐`, or `확인`.

It must not call `context-delivery.ts`, `relevant-record-query.ts`, task-router-like classifiers, subagents, `jcode run`, or hosted RAG synchronously.

## `기능패널` example

Input:

```text
기능패널 고쳐줘
```

Allowed context-delivery behavior:

- include literal query terms such as `기능패널` if they match record-authored aliases or fields,
- return candidate hits if the current host has records/project navigation containing those terms,
- return fallback searches such as root-bound `rg` commands,
- avoid framework-authored semantic expansion to `FeaturePanel` unless that value was directly present in matched record-authored fields,
- avoid marking any hit as required or sufficient.

LLM/searcher behavior after receiving hits:

- read actual candidate records/source/tests,
- decide whether the term maps to a product surface,
- ask a 3-5 option gate if meanings still conflict,
- capture user-confirmed aliases in records later when appropriate.

## Privacy and fail-open requirements

- Do not persist raw `last_user_message`, full prompt, full transcript, or raw assistant response from this CLI by default.
- `--handoff-prompt` output is returned to the explicit caller only.
- Generated indexes and candidate packets are non-canonical.
- Missing generated index falls back to source scan.
- CLI failure must not weaken generic search/read-debt enforcement.

## Implementation map

- Primary files:
  - `.lazy-harness/spec/platform/context-delivery-contract.md` — this SDD.
  - `.lazy-harness/ssot/cli-tool-boundary.md` — CLI-as-tool boundary.
  - `.lazy-harness/scripts/context-delivery.ts` — explicit candidate retrieval helper.
  - `.lazy-harness/schemas/context-delivery-packet.schema.json` — candidate packet schema.
  - `.lazy-harness/scripts/context-index.ts` — deterministic generated index builder used as optional source.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — generic static search-debt transport.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — generic evidence guard, not a context-delivery requiredRead guard.
  - `.lazy-harness/scripts/self-test.py` — protects candidate-only contract and read-debt distinction.
- Key symbols:
  - `buildPacket` (`context-delivery.ts`) — returns candidate hits only.
  - `collectRecordHits` (`context-delivery.ts`) — matches record-authored fields.
  - `collectFeatureHits` (`context-delivery.ts`) — matches feature navigation pointers.
  - `check_context_delivery_candidate_retrieval_phase4` (`self-test.py`) — protects candidate-only output.
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `bun --check .lazy-harness/scripts/context-delivery.ts`

## Rule placement

- Rule: context-delivery is an explicit candidate retrieval tool; it must not decide required reads, importance, intent, risk, gates, record-write need, or next action.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/context-delivery-contract.md`
- Why not AGENTS.md: this is a detailed SDD/schema/implementation contract, not prompt grammar.
- Why not `.jcode`: this framework CLI contract must sync to all hosts, not local/private Jcode wiring.
- Confirmation: user-confirmed
