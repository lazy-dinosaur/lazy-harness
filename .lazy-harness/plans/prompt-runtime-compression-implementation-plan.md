# Prompt Runtime Compression Implementation Plan

Status: active-branch-plan
Branch: `feature/prompt-runtime-compression-plan`
Created: 2026-06-06
Base commit: `132c0ce` (`main` at branch creation)
Scope: lazy-harness source, framework-global prompt/context runtime evolution
User intent: keep lazy-harness's project-defined rule flexibility while reducing prompt-heavy operation by adapting useful homepage and timsquad patterns.

## 0. Executive decision

Lazy-harness should **not** replace its record-first/project-defined policy model with TimSquad's fixed phase process. The target is:

```text
project-defined records/capabilities/evidence
→ compact runtime/project navigation/context indexes
→ short pre-response operational guidance
→ response audit/backstop
→ rare hard stops only when promoted by evidence
```

The work must preserve these hard constraints:

1. Project/team policy remains configurable with capability levels: `discover`, `recommend`, `default`, `warn`, `block`.
2. `block` stays rare and must satisfy the guidance ladder's hard-stop promotion criteria.
3. Generated indexes and runtime state are never canonical truth.
4. Default `message.received` must not become a semantic user-text classifier in shell/CLI code.
5. Context helpers may assist, but direct record/source reads remain the baseline until dogfood proves otherwise.
6. Rollback must be one branch/commit revert away for every phase.

## 1. Grounding evidence already read

### Canonical lazy-harness records

- `.lazy-harness/planning/current-framework-roadmap-snapshot.md`
  - Framework supplies policy machinery, not one universal project policy.
  - Projects decide capability/rule levels.
  - New hard guards are paused unless repeated failures justify them.
- `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - Preferred loop: record indexing/digest → pre-response search prompt → direct root-bound search/read → response audit → records evolve.
  - Action guidance should be organic; hard stops are narrow/rare.
- `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - Current accepted behavior: default `message.received` emits the same static harness inventory/search prompt for every non-empty user message.
  - Target budget: 200-600 tokens, hard ceiling 1,000 tokens.
  - Implementation: `.lazy-harness/hooks/lifecycle/on-message-received.sh`.
- `.lazy-harness/spec/platform/context-delivery-contract.md`
  - Context Delivery Packet is non-canonical helper output.
  - Default `message.received` must not run deterministic semantic backend automatically yet.
- `.lazy-harness/ssot/capability-registry.md`
  - Kinds and enforcement levels are independent.
  - New capabilities default to `discover` or `recommend`.
  - `block` is reserved for high-risk or confirmed hard policy.
- `.lazy-harness/spec/platform/guidance-ladder.md`
  - L0-L3 are default guidance/audit.
  - L4 warning is case-by-case.
  - L5 hard stop is rare and requires promotion record, evidence, fixture, narrowness, rollback.
- `.lazy-harness/spec/platform/record-decision-broker.md`
  - Post-turn record decisions are advisory/non-canonical until explicitly applied.
  - Supports explicit `no-record-needed` for read-only/evaluation turns.
- `.lazy-harness/generated/README.md`
  - `context-index.json` is derived cache.
  - Canonical context inputs include `## Rule digest`, implementation maps, `.lazy-harness/project/feature-navigation.xml`, graph, source/tests.

### Source/test touchpoints inspected

- `.lazy-harness/hooks/lifecycle/on-message-received.sh`
  - Currently journals direct-search debt and emits static inventory/search prompt.
- `.lazy-harness/scripts/self-test.py`
  - `check_jcode_wiring_message_received_hook`
  - `check_context_index_generator`
  - `check_message_received_hook_context_injection`
  - Existing tests explicitly enforce static prompt equality for smalltalk and implementation-like messages.
- `.lazy-harness/scripts/context-index.ts`
  - Already parses records, graph, and `.lazy-harness/project/feature-navigation.xml` into derived context index.
- `.lazy-harness/scripts/relevant-record-query.ts`
  - Already supports `--token-budget`, compact relevant-record output, explicit/manual use.
- `.lazy-harness/bin/lazy`
  - Already dispatches `context-index`, `context-delivery`, `record-decision`, `capability`, etc.
- `.lazy-harness/schemas/context-index.schema.json`
  - Already models project profile feature navigation.

### External pattern synthesis

- medivance-homepage contributes:
  - evidence capsule markdown pattern,
  - project map / feature navigation pattern,
  - SSOT tier manifest pattern,
  - work-unit closure checklist.
- timsquad contributes:
  - prompt budget tests,
  - short root prompt + role/skill separation,
  - "LLM thinks, program handles repetition",
  - operational state runtime direction,
  - optional scoped capability token idea.

## 2. Current risk assessment

### Risk A: Prompt fatigue and duplicated grammar

Current prompt-ish surface includes:

- `.lazy-harness/AGENTS.md`
- `.jcode/harness/05-lazy-harness.md`
- `.jcode/harness/10-routing-policy.md`
- `.jcode/harness/20-project-rules.md`

Observed report count: roughly 386 lines across prompt-ish files. The same lazy-harness grammar can be loaded from both `.lazy-harness/AGENTS.md` and `.jcode/harness/05-lazy-harness.md`.

### Risk B: Static prompt tests intentionally block compression

`check_message_received_hook_context_injection` currently expects:

- hook output for smalltalk and implementation-like messages to be identical,
- STOP/search-debt phrase to always appear,
- full layer inventory phrases to appear.

Any prompt compression must update the SDD and tests first, not just modify the hook.

### Risk C: Semantic classifier prohibition

The existing accepted contract forbids shell/CLI user-text semantic branching in `message.received`. A tiered prompt cannot be implemented as shell regex classification of words like `fix`, `test`, `고쳐`, or `확인`.

Allowed alternatives:

1. static but shorter default prompt,
2. explicit user/agent invoked `lazy context` / `lazy route` / `lazy context-delivery`,
3. deterministic non-semantic inventory compaction,
4. capability/project-map-driven hints only after explicit command or dogfood-proven path,
5. later opt-in runtime mode with a clear feature flag and tests.

### Risk D: Over-importing TimSquad hard gates

TimSquad-like phase/capability gates can be useful, but lazy-harness must not add broad edit/write hard blocks by default. Any hard block needs L5 promotion evidence.

## 3. Target architecture

```text
Phase 0: planning branch and baseline measurement
Phase 1: prompt budget measurement and tests
Phase 2: compact static pre-response prompt, same semantics
Phase 3: project feature-navigation source file and context-index generation
Phase 4: context tier manifest as optional input/hint
Phase 5: evidence capsule standard and work-unit closure checklist
Phase 6: optional operational state packet / compact context helper
Phase 7: dogfood on source + medivance hosts, decide escalation or rollback
```

Key principle:

```text
First make prompt length measurable.
Then reduce static prompt without changing enforcement semantics.
Only after measurements pass, introduce optional runtime/context helpers.
```

## 4. Phase 0 — Branch and baseline

Status: started in this branch.

### Tasks

- [x] Create branch `feature/prompt-runtime-compression-plan` from `main`.
- [x] Confirm branch base commit: `132c0ce`.
- [x] Inspect current records/source/tests listed above.
- [ ] Capture baseline prompt/hook metrics before code changes.

### Commands

```bash
git status --short --branch
git log --oneline -6 --decorate
python3 .lazy-harness/scripts/self-test.py
.lazy-harness/bin/lazy doctor --profile=smoke
```

Optional baseline prompt measurement command to add in Phase 1:

```bash
python3 .lazy-harness/scripts/prompt-budget.py --root . --format=md
```

### Acceptance criteria

- Branch exists and worktree starts clean.
- Baseline `self-test.py` passes before implementation.
- Baseline line/token budgets are recorded as evidence.

### Rollback

```bash
git switch main
git branch -D feature/prompt-runtime-compression-plan
```

No source change has to be reverted if Phase 0 only creates planning commits.

## 5. Phase 1 — Prompt Budget Measurement and Tests

### Goal

Make prompt length and duplication measurable before reducing anything.

### New/changed files

- New SDD: `.lazy-harness/spec/platform/prompt-budget.md`
- New TDD: `.lazy-harness/tests/prompt-budget.md`
- New script: `.lazy-harness/scripts/prompt-budget.py`
- Update: `.lazy-harness/scripts/self-test.py`
- Optional CLI dispatch: `.lazy-harness/bin/lazy` → `lazy prompt-budget`

### Script responsibilities

`prompt-budget.py` should compute:

1. line counts for prompt-ish files:
   - `.lazy-harness/AGENTS.md`
   - `.jcode/harness/*.md` if present
   - `.lazy-harness/hooks/lifecycle/on-message-received.sh` rendered body from fixture payload
   - skill docs if present
2. approximate token count for rendered `message.received` injection.
3. duplicate section fingerprints between `.lazy-harness/AGENTS.md` and `.jcode/harness/05-lazy-harness.md`.
4. hard ceilings and soft target warnings.

### Proposed initial budgets

These are starting thresholds, not permanent ideals:

| Surface | Target | Hard ceiling | Initial mode |
|---|---:|---:|---|
| `message.received` injected body | 200-600 tokens | 1,000 tokens | warn in report, fail in self-test only if > 1,400 during transition |
| root `.lazy-harness/AGENTS.md` | <= 140 lines | <= 200 lines | warn initially |
| `.jcode/harness/05-lazy-harness.md` local copy | pointer-only target | <= 80 lines after migration | warn initially |
| skill/prompt template | <= 120 lines | <= 160 lines | fail for new fixtures later |

### Self-test additions

Add checks:

- `check_prompt_budget_script`
  - script exists,
  - JSON/MD output deterministic enough,
  - rendered fixture includes token estimate,
  - no raw user message storage.
- `check_prompt_budget_thresholds_initial`
  - allows current long state but emits measured values,
  - fails only on severe regression beyond hard transition ceiling.

### Acceptance criteria

- `python3 .lazy-harness/scripts/self-test.py` passes.
- `lazy prompt-budget --format=md` prints:
  - line counts,
  - rendered hook token estimate,
  - duplicate block hints,
  - pass/warn/fail status.
- No behavior change to `message.received` yet.

### Rollback

Revert the Phase 1 commit. Since it only adds measurement and tests, no runtime behavior changes should persist.

## 6. Phase 2 — Compact Static Pre-response Prompt

### Goal

Reduce static prompt size while preserving current semantics:

- still static,
- still no user-text classifier,
- still journals direct-search debt,
- still root-bound record/source search-first,
- still fail-open.

### Required record updates first

- Update `.lazy-harness/spec/platform/pre-response-rule-context.md`:
  - current contract says emit same static prompt with actual inventory.
  - revise wording to allow compact static prompt with pointers and bounded inventory summary.
  - preserve prohibition on semantic classification and automatic semantic backend.
- Update `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` only if the operating model changes materially. If semantics stay the same, add a short implementation note rather than a new ADR.
- Update `.lazy-harness/tests/pre-response-rule-context.md` if such TDD record exists or create one if missing.

### Source changes

- `.lazy-harness/hooks/lifecycle/on-message-received.sh`
  - Extract prompt rendering into a small function inside the Python block.
  - Collapse layer inventory from verbose sample list to compact counts + top pointers.
  - Move detailed examples to a single pointer line.
  - Keep essential instructions:
    - harness-first search-debt,
    - no semantic authority,
    - inspect actual records/files before answer/action,
    - root-bound search scope,
    - option gate only after search/read evidence.
- `.lazy-harness/scripts/self-test.py`
  - Update `check_message_received_hook_context_injection` expected phrases.
  - Keep equality test between smalltalk and implementation-like messages.
  - Add token budget assertion from Phase 1.

### Proposed compact prompt shape

```text
STOP. Harness-first search/read debt before response.
- Static transport; no user-text classification; CLI/index output is not semantic authority.
- Before answer/plan/edit: inspect real .lazy-harness records/source/tests in this host root.
- Actual inventory: DDD=7 SDD=42 BDD=5 TDD=24 ADR=42 SSOT=13 Planning=29 Plans=14 Project=0 Knowledge=5; context-index=missing; feature-navigation=missing.
- Search scope: .lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning,plans,project,knowledge}/ + src + tests.
- Protocol: choose candidate real records → read Rule digest/full body/Implementation map/graph links → then source/tests → then answer or option gate.
```

### Acceptance criteria

- Hook output remains identical for different user messages in the fixture.
- Hook still journals `message.received.direct-search-debt` rows.
- Hook output estimated tokens decrease by at least 30% from baseline.
- `self-test.py` passes.
- `lazy doctor --profile=smoke` passes.

### Rollback

Revert the Phase 2 commit to return to current static prompt. Since the journal schema remains unchanged, runtime state remains compatible.

## 7. Phase 3 — Feature Navigation / Project Map

Status: completed

### Goal

Fill the missing project-navigation input so context compression can rely on a compact map instead of large inventory dumps.

### New/changed files

- New canonical host/source file:
  - `.lazy-harness/project/feature-navigation.xml`
- New SDD or SSOT:
  - `.lazy-harness/ssot/project-navigation.md`
- Update:
  - `.lazy-harness/scripts/context-index.ts` unchanged; existing parser already supports the needed fields.
  - `.lazy-harness/schemas/context-index.schema.json` unchanged; no new output fields were added.
  - `.lazy-harness/scripts/self-test.py` adds a framework-only source feature-navigation completeness check.
  - `.lazy-harness/knowledge/graph.jsonl` links the SSOT, source map, context-index parser, and self-test protection.

### Minimal source feature-navigation content

The source repo map should stay high altitude:

- prompt/runtime lifecycle,
- capability registry,
- context delivery/indexing,
- record decision broker,
- implementation map/graph hygiene,
- lifecycle compare/parity,
- sync/install/update,
- test/doctor.

Implemented source feature ids:

- `prompt-runtime-lifecycle`
- `capability-registry`
- `context-delivery-indexing`
- `record-decision-broker`
- `implementation-map-graph-hygiene`
- `lifecycle-compare-parity`
- `sync-install-update`
- `test-doctor`

Each feature entry should include:

- `id`, `label`, `status`,
- aliases/surface terms,
- related records,
- key source files,
- key tests,
- risk.

### Acceptance criteria

- [x] `.lazy-harness/project/feature-navigation.xml` exists.
- [x] `lazy context-index --format=json` includes projectProfile features.
- [x] Existing `check_context_index_generator_phase3` still passes in focused validation.
- [x] New `check_source_feature_navigation_phase3` verifies source repo feature navigation contains at least the critical framework features above.
- [x] Generated `.lazy-harness/generated/context-index.json` remains optional/ignored unless explicitly written.
- [x] Full `python3 .lazy-harness/scripts/self-test.py` and `.lazy-harness/bin/lazy doctor --profile=smoke` pass after final validation.

Validation evidence:

- `git diff --check` passed.
- `python3 -m py_compile .lazy-harness/scripts/self-test.py .lazy-harness/scripts/prompt-budget.py` passed.
- `python3 .lazy-harness/scripts/self-test.py` passed with `ran=79, skipped=0`.
- `.lazy-harness/bin/lazy doctor --profile=smoke` passed.
- `.lazy-harness/bin/lazy prompt-budget --format=json` returned `status=warn` with `message.received` estimate `259` tokens.
- `.lazy-harness/bin/lazy context-index --format=json` returned 8 source feature ids.

### Rollback

Revert Phase 3 commit. Context index already tolerates missing feature navigation, so runtime should fall back cleanly.

## 8. Phase 4 — Context Tier Manifest

### Goal

Adopt homepage's SSOT tier-map idea as an optional, non-canonical hint for context delivery.

### New files

- New SDD: `.lazy-harness/spec/platform/context-tier-manifest.md`
- New schema: `.lazy-harness/schemas/context-tier-manifest.schema.json`
- Optional source manifest:
  - `.lazy-harness/project/context-tiers.yaml` or `.lazy-harness/ssot/context-tiers.yaml`

### Design constraints

- Manifest is a pointer/hint list, not canonical truth.
- It may define:
  - `always`,
  - `phase`,
  - `task`,
  - `optional`.
- Each entry must point to an existing canonical record/source path.
- Missing paths fail audit but should not block normal operation by default.
- Do not use manifest to bypass record reads.

### Implementation options

Option A: keep manifest as documentation + doctor audit only.

- Lowest risk.
- Good first step.

Option B: context-index ingests manifest into `source.canonicalInputs` and output metadata.

- Medium risk.
- Useful for context delivery later.

Recommended: start with Option A, then dogfood before Option B.

### Acceptance criteria

- Manifest schema validates sample fixture.
- `doctor.py --profile=smoke` or new self-test can detect broken pointers.
- No `message.received` behavior change.

### Rollback

Revert Phase 4 commit. Since manifest is optional and non-canonical, no runtime data migration.

## 9. Phase 5 — Evidence Capsule Standard + Work-unit Closure Checklist

### Goal

Import homepage's durable evidence pattern and make validation claims easier to audit.

### New files

- New SDD: `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- New TDD: `.lazy-harness/tests/evidence-capsule-standard.md`
- New directory: `.lazy-harness/evidence/README.md`
- Optional template: `.lazy-harness/templates/evidence-capsule.md`
- Optional CLI/checklist capability in `.lazy-harness/ssot/capabilities.json`:
  - `lazy-evidence-capsule`
  - kind: `checklist` or `validation`
  - level: `recommend`

### Evidence capsule template

```md
# Evidence: <topic>

## Scope

## Environment

## Commands

## Results

## Interpretation

## Reproduce

## Related records

## Retention / privacy
```

### Work-unit closure checklist

Add a checklist capability, not a hard gate:

```text
Before commit:
- Required records read?
- Validation run?
- Evidence capsule needed for non-trivial claims?
- Record/project map update needed?
- Commit message includes confidence/validation?
```

### Acceptance criteria

- Evidence standard record exists with Rule digest and Implementation map.
- `self-test.py` checks template headings and privacy note.
- Capability audit passes if adding registry entry.
- No automatic evidence writing is added.

### Rollback

Revert Phase 5 commit. Evidence directory/template is additive and non-runtime.

## 10. Phase 6 — Operational State Packet Prototype

### Goal

Prototype a compact runtime view that summarizes applicable context without becoming canonical truth or default semantic authority.

### New/changed files

- New SDD: `.lazy-harness/spec/platform/operational-state-packet.md`
- New schema: `.lazy-harness/schemas/operational-state-packet.schema.json`
- New script: `.lazy-harness/scripts/operational-state.ts`
- CLI dispatch: `.lazy-harness/bin/lazy operational-state`
- Self-test fixture.

### Packet should include

```json
{
  "schemaVersion": "1.0",
  "generatedAt": "...",
  "source": {
    "canonicalInputs": ["..."],
    "generatedInputs": ["..."]
  },
  "taskKind": "unknown|implementation|planning|validation|recording",
  "requiredReads": [],
  "recommendedReads": [],
  "capabilities": [],
  "evidence": [],
  "risk": "low|medium|high|unknown",
  "notes": []
}
```

### Constraints

- Explicit/manual command only in this phase.
- No default `message.received` use.
- No raw user transcript storage.
- No hard block output.
- If generated indexes are missing, it reports fallback-needed rather than failing.

### Acceptance criteria

- `lazy operational-state --message "..." --format=json` emits schema-valid packet.
- Packet references records by path and reason.
- `self-test.py` covers missing context-index fallback.
- No `message.received` default behavior changes.

### Rollback

Revert Phase 6 commit. CLI addition is isolated.

## 11. Phase 7 — Dogfood and Decision Gate

### Goal

Test whether compact prompt + project map + evidence/checklist actually improves behavior without losing safety.

### Dogfood hosts

- Source repo: `/home/lazydino/dev/lazy-harness`
- Medivance: `/home/lazydino/dev/medivance`
- Medivance PWA: `/home/lazydino/dev/medivance-pwa`
- Homepage: `/home/lazydino/dev/medivance-homepage`

### Validation commands

Source:

```bash
python3 .lazy-harness/scripts/self-test.py
.lazy-harness/bin/lazy doctor --profile=smoke
.lazy-harness/bin/lazy prompt-budget --format=md
.lazy-harness/bin/lazy context-index --format=json >/tmp/lazy-context-index.json
```

Dogfood hosts after sync/dry-run first:

```bash
bun .lazy-harness/scripts/lazy-sync.ts --from /home/lazydino/dev/lazy-harness --target <host> --dry-run
bun .lazy-harness/scripts/lazy-sync.ts --from /home/lazydino/dev/lazy-harness --target <host> --force
cd <host>
.lazy-harness/bin/lazy test
.lazy-harness/bin/lazy doctor --profile=smoke
.lazy-harness/bin/lazy prompt-budget --format=md
.lazy-harness/bin/lazy context-index --format=json >/tmp/<host>-context-index.json
```

### Metrics to compare

- Rendered `message.received` token estimate before/after.
- Hook latency remains under 800ms timeout in normal cases.
- Search/read debt guard still blocks action before evidence when debt exists.
- Response audit still catches unsatisfied debt.
- Agents still receive enough record/source search instruction to avoid silent skip.
- False positives: trivial turns that feel over-instructed.
- False negatives: host-specific records skipped when needed.

### Decision gate

Only after at least one dogfood pass:

- If prompt token count improves ≥30% and no safety regression appears:
  - keep compact prompt.
- If behavior gets worse:
  - revert Phase 2 only, keep measurement tooling if useful.
- If operational-state helper is useful:
  - keep explicit/manual capability at `recommend`, not default.
- If hard gate seems needed:
  - require L5 promotion record and user confirmation.

## 12. Commit and rollback strategy

### Commit slicing

Use small commits:

1. `Plan: detail prompt runtime compression rollout`
2. `Test: add prompt budget measurement`
3. `Spec: accept compact static prompt contract`
4. `Feat: compact message received prompt`
5. `Spec: add feature navigation map`
6. `Spec: add context tier manifest`
7. `Docs: add evidence capsule standard`
8. `Feat: add operational state packet prototype`
9. `Docs: record dogfood validation results`

### Rollback matrix

| Phase | Rollback command | Expected blast radius |
|---|---|---|
| 0/plan | `git revert <plan-commit>` | docs only |
| 1 prompt budget | `git revert <phase1>` | removes measurement/CLI only |
| 2 compact hook | `git revert <phase2>` | restores old static prompt; journal remains compatible |
| 3 feature navigation | `git revert <phase3>` | context-index falls back to no project profile |
| 4 tier manifest | `git revert <phase4>` | optional hints removed |
| 5 evidence/checklist | `git revert <phase5>` | docs/templates/capability removed |
| 6 operational state | `git revert <phase6>` | explicit CLI removed; no default hook dependency |
| 7 dogfood records | `git revert <phase7-docs>` | removes validation report only |

### Never do without explicit user approval

- Replace production `response.completed` hook.
- Promote any new broad hard stop.
- Make operational-state/context-delivery the default semantic authority in `message.received`.
- Sync experimental branch changes into dogfood hosts without dry-run and user-visible summary.

## 13. Detailed task backlog

### P0 — Planning and measurement

- [x] Create branch.
- [x] Write this plan.
- [ ] Run baseline `self-test.py` on branch.
- [ ] Add prompt budget SDD/TDD.
- [ ] Implement `prompt-budget.py`.
- [ ] Add `lazy prompt-budget` dispatch.
- [ ] Add self-test fixtures.

### P1 — Safe prompt compression

- [ ] Update pre-response SDD to permit compact static prompt.
- [ ] Update self-test expected phrases and token budget check.
- [ ] Refactor hook prompt rendering.
- [ ] Verify same output for different messages.
- [ ] Verify no semantic backend or user-text classifier.
- [ ] Measure token reduction.

### P1 — Feature navigation

- [ ] Draft `.lazy-harness/project/feature-navigation.xml` for source repo.
- [ ] Add/adjust spec for feature navigation.
- [ ] Verify `context-index.ts` consumes it.
- [ ] Add self-test for critical feature entries.

### P2 — Tier manifest and evidence standard

- [ ] Draft context tier manifest spec and schema.
- [ ] Add optional manifest pointer audit.
- [ ] Draft evidence capsule standard and template.
- [ ] Add recommended work-unit closure checklist capability.

### P3 — Operational-state prototype

- [ ] Draft packet spec/schema.
- [ ] Implement explicit CLI.
- [ ] Add fallback behavior for missing indexes.
- [ ] Keep command advisory and non-default.

### P4 — Dogfood

- [ ] Run source self-test/doctor/prompt-budget.
- [ ] Dry-run sync to dogfood hosts.
- [ ] Run host lazy test/doctor/prompt-budget.
- [ ] Capture evidence capsule for final comparison.
- [ ] Decide keep/revert/escalate.

## 14. Validation strategy

### Static validation

```bash
git diff --check
python3 .lazy-harness/scripts/self-test.py
.lazy-harness/bin/lazy doctor --profile=smoke
```

### Behavioral validation

Use existing fixtures and add new ones:

1. `message.received` emits compact prompt for non-empty message.
2. Empty user message stays silent.
3. Smalltalk and implementation-like messages produce identical prompt body until an explicit opt-in mode exists.
4. Journal row still written with `message.received.direct-search-debt`.
5. Pre-action read-debt guard still blocks action before search/read evidence.
6. Read-debt guard still allows action after evidence.
7. Context index includes feature-navigation entries.
8. Prompt budget CLI reports before/after metrics.

### Human/dogfood validation

Run at least 5 representative turns after Phase 2:

1. trivial greeting,
2. host-specific question,
3. implementation request,
4. ambiguous short request,
5. record/evidence update request.

Expected outcome:

- trivial turn feels less noisy,
- host-specific/implementation turn still triggers direct record/source search,
- ambiguity still leads to option gate after search evidence,
- no broad hard gate introduced.

## 15. Implementation map

- Records to update/create:
  - `.lazy-harness/spec/platform/prompt-budget.md`
  - `.lazy-harness/tests/prompt-budget.md`
  - `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - `.lazy-harness/project/feature-navigation.xml`
  - `.lazy-harness/spec/platform/context-tier-manifest.md`
  - `.lazy-harness/spec/platform/evidence-capsule-standard.md`
  - `.lazy-harness/tests/evidence-capsule-standard.md`
  - `.lazy-harness/spec/platform/operational-state-packet.md`
- Source files likely to change:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh`
  - `.lazy-harness/scripts/self-test.py`
  - `.lazy-harness/scripts/prompt-budget.py`
  - `.lazy-harness/scripts/context-index.ts`
  - `.lazy-harness/scripts/operational-state.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/schemas/context-tier-manifest.schema.json`
  - `.lazy-harness/schemas/operational-state-packet.schema.json`
- Existing protection tests:
  - `check_jcode_wiring_message_received_hook`
  - `check_context_index_generator`
  - `check_message_received_hook_context_injection`
  - context-delivery journal/read-debt checks around Phase 7 code in `self-test.py`
- New tests to add:
  - prompt budget check,
  - compact hook token threshold,
  - feature navigation source-map completeness,
  - evidence capsule template headings,
  - tier manifest pointer validation,
  - operational state packet schema/fallback.

## 16. Rule placement

- Rule: lazy-harness should reduce prompt-heavy operation by adding measurement, compact static prompts, project navigation, context tier hints, evidence capsules, and optional operational-state packets while preserving project-defined policy machinery and rare hard-stop discipline.
- Scope: framework-global implementation plan.
- Primary record: `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`.
- Why not AGENTS.md: this is not yet final operating grammar; it is a branch implementation plan.
- Why not `.jcode`: this is shared framework source planning, not local/private Jcode wiring.

## 17. Discovery capture

- DDD: no new domain/business invariant.
- SDD: prompt budget, context tier manifest, evidence capsule standard, operational state packet, and compact pre-response prompt need SDD records as implemented.
- BDD: agent behavior should become less noisy while retaining search/option-gate behavior; add dogfood scenarios if behavior changes.
- TDD: prompt budget, compact hook, feature navigation, tier manifest, evidence capsule, operational state packet all need self-test fixtures.
- ADR: no new ADR needed yet if implementing ADR 0041 direction; create ADR only if switching default `message.received` away from static direct-search transport or introducing new enforcement semantics.
- SSOT: capability registry levels remain unchanged; optional checklist/evidence capabilities may be added at `recommend`.
- Planning: this document is the active branch plan.
