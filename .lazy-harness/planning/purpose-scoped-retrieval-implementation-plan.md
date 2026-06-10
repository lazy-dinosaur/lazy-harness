# Purpose-Scoped Retrieval Implementation Plan — 2026-06-10

Status: active-plan
Layer: Planning
Date: 2026-06-10
Confirmation: user-confirmed
Related planning: `.lazy-harness/planning/project-operating-rulebook-implementation-plan.md`
Related ADR: `.lazy-harness/decisions/0044-project-operating-rulebook.md`
Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
Related SDD: `.lazy-harness/spec/platform/project-operating-rulebook.md`
Related SDD: `.lazy-harness/spec/platform/capability-resolution.md`
Related SDD: `.lazy-harness/spec/platform/workflow-compression-router.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related SSOT: `.lazy-harness/ssot/capability-registry.md`
Related TDD: `.lazy-harness/tests/project-operating-rulebook.md`

## User-confirmed target

The user clarified that retrieval must distinguish **information/fact lookup** from **operating-rule/action lookup**:

```text
계약내용이나 실제 구현된 사실들 그리고 프로젝트에 대한 내용을 확인하기위해선 레코드를 찾는게 맞는데
그게 아닌거면 찾으면 토큰 낭비만 하는거잖아
내가 행동을 위한 규약이나 규칙을 찾는거랑 정보를위해찾는거랑 다르게봐야할것같아
```

Interpretation:

`record search` is not a universal synonym for context retrieval. Records are the right search space for project facts, contracts, implementation maps, decisions, and source-of-truth questions. They are not the right first search space when the agent is deciding what to do under project operating policy, or when the task is test/validation-only.

## Current verification snapshot

Verified on 2026-06-10 before writing this plan:

- Recent relevant commits:
  - `54e4b9f Implement project operating rulebook`
  - `ba59b00 Capture purpose scoped retrieval requirement`
- `lazy rules audit --strict --format=json` returns `{ ok: true, count: 1, issueCount: 0 }`.
- `lazy rules resolve --action '.jcode/harness/20-project-rules.md project policy body'` matches `discouraged-action` and points to the `project-operating-rulebook` capability.
- `lazy capability resolve --action '.jcode/harness/20-project-rules.md project policy body'` returns the preferred surfaces:
  - `.lazy-harness/rules/**`
  - `.lazy-harness/bin/lazy rules`
  - `.lazy-harness/ssot/capabilities.json`
- `lazy map '행동규약'` finds the project operating rulebook feature and records.
- `lazy graph-hygiene --fail-on-issues` passes.
- `.lazy-harness/bin/lazy test` passes: `ran=80, skipped=0`.
- Gap confirmed: `lazy map 'purpose scoped retrieval'` returns no record candidates because the requirement is currently only embedded in a long planning section.

## Problem

The current search/read debt language still nudges agents toward broad record/source/test sweeps:

```text
message.received
→ mandatory lazy map --overview
→ repeated query-map
→ root-bound record/source/test search/read
```

This is safe against guessing, but now over-broad for several common purposes:

| Purpose | Good first search space | Broad record sweep? |
|---|---|---|
| Project fact / contract / implementation fact | DDD/SDD/BDD/TDD/ADR/SSOT + source/tests/config | yes, often required |
| Operating rule / behavior policy | `.lazy-harness/rules/**` + `lazy rules resolve` + `lazy capability resolve` | no, unless rule points to missing facts |
| Test / validation | `.lazy-harness/tests/**`, source test files, validation capabilities | no, unless contract/behavior/config impact is needed |
| Command/tool selection | capability/rulebook action labels | no |
| Architecture/design change | record/source/test package + layer completeness gate | yes |
| Unknown/ambiguous host detail | overview + candidate records/source/tests + option gate | yes, but bounded |

## Decision candidate

Implement **purpose-scoped retrieval** as an explicit LLM/user-selected retrieval entrypoint, not a lifecycle semantic classifier.

Preferred CLI direction:

```bash
.lazy-harness/bin/lazy find --purpose <test|rulebook|capability|source|record|architecture|full> <query>
```

Why `lazy find`, not `lazy route`:

- `.lazy-harness/spec/platform/workflow-compression-router.md` explicitly supersedes the old route classifier and says not to reintroduce `lazy route` without a new LLM-first ADR/SDD.
- `find` describes cue retrieval, not action routing or semantic authority.
- The LLM/searcher chooses `--purpose`; the CLI does not infer purpose from raw user text.

## Purpose taxonomy

### `--purpose fact` / alias `record`

Question: “What is true about this project?”

Search spaces:

- `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/**`
- `.lazy-harness/knowledge/graph.jsonl`
- `.lazy-harness/generated/record-index.json`
- implementation maps/source/test/config docs as drill-down candidates

Default commands surfaced:

```bash
.lazy-harness/bin/lazy map '<query>' --format=md --limit=8
.lazy-harness/bin/lazy graph query '<query>' --format=md --limit=8
```

### `--purpose rulebook`

Question: “How should I act in this project?”

Search spaces:

- `.lazy-harness/rules/**`
- `.lazy-harness/ssot/capabilities.json`
- `lazy rules resolve --intent/--action`
- `lazy capability resolve --intent/--action`

Must not start with a broad DDD/SDD/ADR sweep unless the rulebook result says factual support is missing.

### `--purpose test`

Question: “What tests/validations matter?”

Search spaces:

- `.lazy-harness/tests/**`
- source test files under `tests`, `src`, `packages`, and common `*.test.*` / `*.spec.*` patterns
- validation/test capabilities in `.lazy-harness/ssot/capabilities.json`
- `lazy affected` or equivalent if present

Escalation to SDD/BDD/SSOT is allowed when:

- a test expectation references a contract/behavior/config record,
- the user asks why the behavior exists,
- mutation would affect API/component/schema/config boundaries.

### `--purpose capability`

Question: “Which registered affordance/tool/action applies?”

Search spaces:

- `.lazy-harness/ssot/capabilities.json`
- `lazy capability resolve`
- linked rulebook/source records only after a match

### `--purpose source`

Question: “Where is this implemented?”

Search spaces:

- source/test directories
- implementation-index/reference-index/graph paths as cues
- records only if implementation map or contract context is needed

### `--purpose architecture`

Question: “How should this be changed/designed?”

Search spaces:

- overview first
- ADR/SDD/BDD/TDD/SSOT/DDD as relevant
- source/tests/config
- layer completeness gate

This is the broad mode.

### `--purpose full`

Explicit broad retrieval mode for high-risk or ambiguous work.

## CLI contract candidate

Add a new read-only command:

```bash
lazy find --purpose <purpose> <query> [--format=md|json] [--limit=N]
```

Output shape:

```json
{
  "purpose": "test",
  "query": "worktree",
  "searchSpaces": ["tests", "source-tests", "validation-capabilities"],
  "commands": [
    ".lazy-harness/bin/lazy capability resolve --intent validating_changes --format=md",
    "grep -rli 'worktree' .lazy-harness/tests tests src packages"
  ],
  "candidates": {
    "records": [],
    "rules": [],
    "capabilities": [],
    "sourceFiles": [],
    "testFiles": []
  },
  "escalation": [
    "Run lazy map only if tests imply contract/behavior/config facts."
  ],
  "caveat": "cue-only; read actual files before relying on a match"
}
```

Hard boundaries:

- `lazy find` must not decide risk, gate, required reads, or next action from raw user text.
- `--purpose` is explicit input from the LLM/user.
- Results are cue-only.
- Missing/ambiguous results must provide fallback commands, not hallucinated facts.
- Lifecycle hooks may recommend purpose-scoped retrieval, but must not classify raw prompts into a purpose automatically.

## Implementation phases

### Phase 0 — promote requirement out of planning tail

Create dedicated record package:

- ADR: `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`
- DDD: `.lazy-harness/domain/purpose-scoped-retrieval.md`
- BDD: `.lazy-harness/behavior/purpose-scoped-retrieval.md`
- SDD: `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`
- TDD: `.lazy-harness/tests/purpose-scoped-retrieval.md`
- SSOT updates:
  - `.lazy-harness/ssot/cli-tool-boundary.md`
  - `.lazy-harness/ssot/capability-registry.md`
- Feature navigation update:
  - `.lazy-harness/project/feature-navigation.xml`
- Knowledge graph rows:
  - record/source/test/feature edges

Validation:

```bash
.lazy-harness/bin/lazy map 'purpose scoped retrieval' --format=md --limit=8
.lazy-harness/bin/lazy map '정보 검색 행동 규약 검색' --format=md --limit=8
.lazy-harness/bin/lazy test
```

Exit criteria:

- Current discoverability gap is closed.
- Record map returns the new feature/records for English and Korean queries.

### Phase 1 — read-only `lazy find` prototype

Add:

- `.lazy-harness/scripts/purpose-find.ts`
- `.lazy-harness/bin/lazy` dispatch for `find`
- self-test fixture for each purpose

Minimal behavior:

- `lazy find --purpose rulebook <query>` calls/uses the same data surfaces as `lazy rules` and capability action metadata.
- `lazy find --purpose test <query>` searches `.lazy-harness/tests/**` and source test file names/content before records.
- `lazy find --purpose fact <query>` wraps/points to `lazy map` and graph/source candidates.
- `lazy find --purpose architecture <query>` prints broad package commands and layer completeness reminders.

No hooks changed in Phase 1.

Validation examples:

```bash
.lazy-harness/bin/lazy find --purpose rulebook 'project policy storage' --format=json
.lazy-harness/bin/lazy find --purpose test 'worktree' --format=json
.lazy-harness/bin/lazy find --purpose fact 'capability resolution' --format=json
.lazy-harness/bin/lazy find --purpose architecture 'purpose scoped retrieval' --format=md
```

Expected:

- `rulebook` mode returns rule/capability surfaces and does not include broad DDD/ADR/SSOT records unless linked.
- `test` mode returns `.lazy-harness/tests/**` and source test candidates first, with no default broad record sweep.
- `fact` mode returns record/graph/source candidates.
- `architecture` mode returns broad layer package guidance.

### Phase 2 — capability-backed retrieval purposes

Register retrieval purpose capabilities so hosts can customize retrieval spaces:

- `retrieval-purpose-rulebook`
- `retrieval-purpose-test`
- `retrieval-purpose-fact`
- `retrieval-purpose-source`
- `retrieval-purpose-architecture`

Capabilities remain `discover` or `recommend` by default.

Validation:

```bash
.lazy-harness/bin/lazy capability resolve --intent retrieval_test --format=json
.lazy-harness/bin/lazy capability resolve --intent retrieval_rulebook --format=json
```

Expected:

- The resolver returns purpose-specific retrieval affordances.
- No warn/block is introduced.

### Phase 3 — audit and evidence integration

Update search/read debt and response audit to recognize purpose-scoped retrieval evidence without requiring irrelevant record reads.

Preferred mechanism:

- `lazy find` can emit a small evidence capsule to stdout or optional file.
- `check-read-debt-permit.py` recognizes explicit purpose-scoped retrieval evidence as satisfying search debt for matching non-mutating/low-risk tasks.
- Mutations and architecture changes still require actual file reads and layer completeness evidence.

Constraints:

- Do not change `message.received` into a semantic classifier.
- Do not generate required-read lists from raw user text.
- Do not reduce safety for ambiguous/high-risk tasks.

### Phase 4 — downstream dogfood fixtures

Phase 4 status: implemented in `check_purpose_scoped_retrieval_cli` on 2026-06-10.

Use dogfood cases:

- rulebook search for worktree/dev-instance policy should use rulebook/capability first.
- test search for a regression should use tests/test capabilities first.
- fact search for dev-worktree contract should use records/source.

## Validation matrix

| Case | Command | Expected |
|---|---|---|
| Current rulebook still works | `lazy rules audit --strict` | ok |
| Capability action routing still works | `lazy capability resolve --action '.jcode/harness/20-project-rules.md project policy body'` | returns `project-operating-rulebook` |
| Current gap captured | `lazy map 'purpose scoped retrieval'` before Phase 0 | no record candidates, motivating Phase 0 |
| Phase 0 discoverability | `lazy map 'purpose scoped retrieval'` after Phase 0 | returns feature/records |
| Korean discoverability | `lazy map '정보 검색 행동 규약 검색'` | returns purpose-scoped retrieval records |
| Rulebook purpose | `lazy find --purpose rulebook 'project policy storage'` | rule/capability candidates first |
| Test purpose | `lazy find --purpose test 'worktree'` | TDD/test/source-test candidates first, no broad records by default |
| Fact purpose | `lazy find --purpose fact 'capability resolution'` | records/graph/source candidates |
| No router regression | source grep | no raw prompt classifier or `lazy route` reintroduction |
| Full suite | `lazy test` | all green |

## Plan self-review

### Strengths

- Separates “what is true?” retrieval from “how should I act?” retrieval.
- Preserves rulebook/capability work already implemented.
- Explicitly avoids reintroducing the superseded workflow-compression route classifier.
- Uses explicit `--purpose`, so lifecycle hooks do not infer semantic intent from raw user text.
- Creates a dedicated record package so the requirement is discoverable by `lazy map`.

### Risks and mitigations

1. Risk: agents may skip needed records for fact-sensitive work.
   - Mitigation: `fact`, `architecture`, `full`, and escalation rules keep broad record/source/test retrieval available.

2. Risk: `test` mode may miss contract/behavior/config impacts.
   - Mitigation: TDD record must require escalation when tests reference SDD/BDD/SSOT or mutations cross boundaries.

3. Risk: `lazy find` becomes a semantic authority.
   - Mitigation: it is explicit-purpose and cue-only; it must not classify raw prompts or output confidence/gate/next-action fields.

4. Risk: too many modes confuse agents.
   - Mitigation: start with six stable purposes and aliases; keep `architecture/full` as broad fallback.

5. Risk: response audit still expects broad evidence.
   - Mitigation: Phase 3 updates audit only after Phase 1/2 prove stable evidence shape.

6. Risk: duplicate retrieval tools (`map`, `graph`, `rules`, `capability`, `find`).
   - Mitigation: `find` is an orchestration/cue entrypoint; existing commands remain canonical source-specific resolvers.

### Rejected alternatives

- `lazy route --purpose ...`: rejected for now because `workflow-compression-router.md` explicitly supersedes route-style classifier tooling.
- Lifecycle hook raw prompt classification: rejected by `cli-tool-boundary` and `search-read-debt-contract`.
- Replacing `lazy map`: rejected because records remain correct for fact/contract/architecture retrieval.
- Making test-purpose retrieval satisfy all mutation gates: rejected because test-only evidence is insufficient for architecture/contract mutations.

## Rule placement

- Rule: Lazy-harness retrieval must be purpose-scoped. Use project fact records for information/fact questions, rulebook/capability surfaces for operating-rule/action questions, and test surfaces for validation questions before widening to broader records only when needed.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/purpose-scoped-retrieval-implementation-plan.md`
- Why not AGENTS.md: this is an implementation plan and architecture transition; final prompt grammar can point to the accepted ADR/SDD after implementation.
- Why not `.jcode`: this changes shared framework retrieval behavior across hosts, not local/private Jcode wiring.
- Confirmation: user-confirmed

## Discovery capture

- DDD: create purpose-scoped retrieval vocabulary because “record search” and “context retrieval” are now distinct concepts.
- BDD: add agent behavior scenarios for choosing fact/rulebook/test retrieval spaces.
- SDD: define `lazy find --purpose` contract and update search/read debt evidence semantics later.
- TDD: protect no-broad-record default for rulebook/test purposes and no raw-text classifier reintroduction.
- ADR: decide explicit-purpose `lazy find` over `lazy route`.
- SSOT: update CLI boundary and capability registry with retrieval purpose constraints.
- Planning: this plan is the next implementation entrypoint.

## Implementation map

- Status: `planned`
- Existing implementation to build on:
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/record-map.ts`
  - `.lazy-harness/scripts/graph-query.ts`
  - `.lazy-harness/scripts/rulebook.ts`
  - `.lazy-harness/scripts/capability.ts`
  - `.lazy-harness/scripts/self-test.py`
  - `.lazy-harness/project/feature-navigation.xml`
- New implementation candidates:
  - `.lazy-harness/scripts/purpose-find.ts`
  - `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`
  - `.lazy-harness/domain/purpose-scoped-retrieval.md`
  - `.lazy-harness/behavior/purpose-scoped-retrieval.md`
  - `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`
  - `.lazy-harness/tests/purpose-scoped-retrieval.md`
- Protection:
  - `.lazy-harness/bin/lazy test`
  - focused `lazy find --purpose ...` fixtures
  - source grep proving no `lazy route` or raw prompt classifier reintroduction

## 2026-06-10 next candidate — Phase 5 prompt guidance alignment

Status: candidate-next
Confirmation: inferred-from-record

After Phase 4, purpose-scoped retrieval works in CLI, evidence guards, response audit, and downstream dogfood fixtures. The remaining mismatch is the default `message.received` reminder: it still reads as broad harness-first record/source/test retrieval guidance, while the implemented framework now supports purpose-scoped retrieval.

Candidate next phase:

```text
Phase 5 — prompt guidance alignment
```

Goal:

- Keep `message.received` static and non-semantic.
- Do not classify raw user text into purposes.
- Update the reminder wording to teach the LLM/searcher to choose an explicit retrieval purpose:
  - information/fact → `lazy find --purpose fact` / `lazy map`
  - action/rule → `lazy find --purpose rulebook` / `lazy rules` / `lazy capability`
  - validation/test → `lazy find --purpose test`
  - implementation/source → `lazy find --purpose source`
  - broad design/mutation → `lazy find --purpose architecture` or current overview/map flow
- Preserve broad overview requirement for architecture/ambiguous/high-risk work.
- Keep prompt budget and static equality tests green.

Likely files:

- `.lazy-harness/hooks/lifecycle/on-message-received.sh`
- `.lazy-harness/spec/platform/pre-response-rule-context.md`
- `.lazy-harness/tests/pre-response-rule-context.md`
- `.lazy-harness/tests/prompt-budget.md`
- `.lazy-harness/scripts/self-test.py`

Validation:

- `check_message_received_hook_context_injection` still proves no user-text semantic classifier and static output equality.
- prompt budget remains under threshold.
- reminder contains purpose-scoped retrieval examples without requiring broad record sweeps for every task.
- `.lazy-harness/bin/lazy test` all green.

## Rule placement

- Rule: After purpose-scoped retrieval exists, default prompt guidance should teach explicit purpose selection while staying static/non-semantic and preserving broad retrieval for architecture/ambiguous/high-risk work.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/purpose-scoped-retrieval-implementation-plan.md`
- Why not AGENTS.md: this is candidate implementation planning for prompt/runtime lifecycle, not final universal grammar yet.
- Why not `.jcode`: shared lazy-harness framework prompt behavior, not local/private Jcode wiring.
- Confirmation: inferred-from-record

## Discovery capture

- DDD: none.
- BDD: candidate update to agent-visible retrieval behavior in pre-response reminder.
- SDD: candidate update to pre-response context contract.
- TDD: candidate update to pre-response prompt and prompt-budget regression tests.
- ADR: no new ADR expected unless static prompt policy changes.
- SSOT: no new SSOT expected unless CLI boundary changes.
- Planning: this section is the active next-step candidate.
