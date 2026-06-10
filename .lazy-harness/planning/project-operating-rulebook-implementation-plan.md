# Project Operating Rulebook Implementation Plan — 2026-06-10

Status: active-plan
Layer: Planning
Date: 2026-06-10
Confirmation: user-confirmed
Related audit: `.lazy-harness/planning/project-rule-adaptation-regression-audit-20260610.md`
Related SSOT: `.lazy-harness/ssot/rule-sources.md`
Related SSOT: `.lazy-harness/ssot/rule-lifecycle.md`
Related SSOT: `.lazy-harness/ssot/capability-registry.md`
Related SDD: `.lazy-harness/spec/platform/project-rule-router.md`
Related SDD: `.lazy-harness/spec/platform/capability-resolution.md`
Related SDD: `.lazy-harness/spec/platform/guidance-ladder.md`
Related ADR: `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md`
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related TDD: `.lazy-harness/tests/capability-registry.md`
Related TDD: `.lazy-harness/tests/project-rule-memory-routing.md`

## User-confirmed target

The user confirmed that lazy-harness needs more than project fact records:

```text
규칙을 저장하는 방식도 만들도록 하는게 좋겠지??
이게 레코드는 프로젝트에대한사실이고
이 프로젝트를 개발하면서의 행동규약은 따로있어야하잖아
```

Target model:

```text
project facts/knowledge records
  !=
project development operating rulebook
```

The rulebook must be canonical, discoverable, and able to change agent behavior through capability/default/warn/block levels without reviving broad tool-specific hard gates.

## Proposed architecture: Hybrid rulebook + capability registry

Use two connected stores:

1. Human canonical operating rules:

```text
.lazy-harness/rules/**
```

2. Machine-readable action/capability mapping:

```text
.lazy-harness/ssot/capabilities.json
```

Flow:

```text
.lazy-harness/rules/<rule>.md
  -> sourceRecord for one or more capabilities
  -> lazy rules / lazy capability resolve
  -> message/action-time surfacing
  -> response audit / guidance ladder escalation
```

Why hybrid:

- Markdown rulebook preserves explainable project operating policy.
- Capability registry already has `discover/recommend/default/warn/block` levels.
- Existing `capability.ts` resolver can be extended instead of introducing a brittle hook per tool.
- `.jcode` remains local/private pointer-only wiring.
- Project facts remain in DDD/SDD/BDD/TDD/ADR/SSOT records.

## Storage contract

### New directory

```text
.lazy-harness/rules/
  README.md
  <topic>.md
```

`rules/README.md` explains:

- rulebook purpose,
- difference from project fact records,
- required sections,
- relationship to capabilities,
- level semantics,
- examples.

### Rulebook entry required sections

Each `.lazy-harness/rules/<id>.md` should include:

```md
# <Title>

Status: active | draft | retired
Layer: Rulebook
Scope: framework-global | host-project | team-policy | jcode-local
Owner: <owner>
Level: discover | recommend | default | warn | block
Related capability: <capability-id>
Related records:
- <fact/contract/decision/ssot paths>

## Rule digest

- Applies when:
  - <intent/action cue>
- Prefer:
  - <canonical command/tool/workflow>
- Avoid:
  - <discouraged command/tool/workflow>
- Requires:
  - <required precondition/check>
- Bypass:
  - <when/how bypass is allowed>
- Record completion:
  - <what must be updated if rule changes>

## Operating rule

Human explanation.

## Examples

Good and bad command/workflow examples.

## Capability binding

- Capability id: ...
- Preferred actions: ...
- Discouraged actions: ...
- Intent labels: ...
- Enforcement level: ...

## Implementation map

- Source records:
- Capabilities:
- Validation:
- Tests:
```

### Capability extensions

Current capabilities schema supports:

- `actions`
- `entrypoint`
- `fallback`
- additional properties

For operating rules, add explicit optional fields:

```json
{
  "preferredActions": ["bun run wt new"],
  "discouragedActions": ["git worktree add"],
  "requiresReasonForBypass": true,
  "rulebookRecord": ".lazy-harness/rules/dev-worktree.md"
}
```

Resolution rule:

- `--action` matches `actions`, `preferredActions`, or `discouragedActions`.
- If matched by `discouragedActions`, output must show the preferred replacement and level.
- `entrypoint` remains the canonical command/path to use when present.

## CLI design

Add a new command group:

```bash
.lazy-harness/bin/lazy rules <subcommand>
```

Subcommands:

```bash
lazy rules list [--format=json|md]
lazy rules resolve --intent <intent> [--format=json|md]
lazy rules resolve --action <command-or-tool-label> [--format=json|md]
lazy rules audit [--format=json|md] [--strict]
lazy rules candidates [--format=json|md]
```

Implementation file:

```text
.lazy-harness/scripts/rulebook.ts
```

Resolver behavior:

1. Load `.lazy-harness/rules/**/*.md`.
2. Load `.lazy-harness/ssot/capabilities.json`.
3. Link capabilities to rulebook entries by:
   - `sourceRecord`, or
   - `rulebookRecord`, or
   - `Related capability` section in Markdown.
4. Match by exact intent/action labels, not semantic inference.
5. Sort by `block`, `warn`, `default`, `recommend`, `discover`.
6. Print concise guidance:
   - matched rule,
   - level,
   - prefer/avoid commands,
   - source rulebook path,
   - related fact records.

Audit behavior:

- Every active rulebook entry must have a valid `Status`, `Scope`, `Level`, and `## Rule digest`.
- Every active rulebook entry at `default|warn|block` must be linked to a capability.
- Capability `sourceRecord`/`rulebookRecord` must exist.
- `warn|block` capabilities must declare an action surface: `actions`, `preferredActions`, `discouragedActions`, or `entrypoint`.
- If a rulebook entry has `Avoid`, the linked capability must include `discouragedActions`.
- If a capability has `discouragedActions`, its rulebook entry must document bypass behavior.
- `.jcode/**` and Jcode memory must not be canonical rulebook stores.

Candidate behavior:

- If `.lazy-harness/rules/**` contains active entries without capabilities, suggest missing capability entries.
- If capabilities contain `host-project` entries with no rulebook record, suggest adding a rulebook entry.
- If package scripts reveal likely canonical commands but no rulebook/capability exists, suggest `recommend` candidates only.
- Never auto-promote to `warn` or `block`.

## Lifecycle integration plan

### Phase 0 — contract and records

Files:

- `.lazy-harness/decisions/0044-project-operating-rulebook.md`
- `.lazy-harness/spec/platform/project-operating-rulebook.md`
- `.lazy-harness/tests/project-operating-rulebook.md`
- `.lazy-harness/ssot/rule-sources.md` update
- `.lazy-harness/ssot/capability-registry.md` update
- `.lazy-harness/project/feature-navigation.xml` update

Validation:

- `lazy map 'operating rulebook'` finds ADR/SDD/TDD/SSOT.
- `lazy map '행동규약'` finds the same path.
- `python3 .lazy-harness/scripts/self-test.py` passes.

Exit criteria:

- The framework has a recorded distinction between fact records and operating rules.
- Placement matrix routes operating policy to `.lazy-harness/rules/**` plus capability bindings.

### Phase 1 — storage skeleton and audit-only CLI

Files:

- `.lazy-harness/rules/README.md`
- `.lazy-harness/rules/dev-worktree.example.md` or test fixture equivalent
- `.lazy-harness/scripts/rulebook.ts`
- `.lazy-harness/bin/lazy` dispatch for `rules`
- `.lazy-harness/scripts/self-test.py` fixtures

Behavior:

- `lazy rules list` reads rulebook entries.
- `lazy rules audit --strict` validates required sections and capability links.
- No lifecycle hook enforcement yet.

Validation:

```bash
.lazy-harness/bin/lazy rules list --format=json
.lazy-harness/bin/lazy rules audit --format=json --strict
python3 .lazy-harness/scripts/self-test.py
.lazy-harness/bin/lazy test
```

Exit criteria:

- A fixture rulebook entry is parsed and audited.
- Missing `Rule digest`, invalid level, missing capability link, and missing source file produce deterministic audit failures.

### Phase 2 — capability binding and resolver

Files:

- `.lazy-harness/schemas/capabilities.schema.json` extend optional fields.
- `.lazy-harness/scripts/capability.ts` extend matching to `preferredActions` and `discouragedActions`.
- `.lazy-harness/scripts/rulebook.ts` add `resolve`.
- `.lazy-harness/tests/capability-registry.md` update.
- `.lazy-harness/tests/project-operating-rulebook.md` update.

Behavior:

Example fixture:

```json
{
  "id": "dev-worktree-standard-command",
  "kind": "command",
  "level": "warn",
  "sourceRecord": ".lazy-harness/rules/dev-worktree.md",
  "rulebookRecord": ".lazy-harness/rules/dev-worktree.md",
  "appliesWhen": ["creating_worktree", "starting_dev_instance"],
  "preferredActions": ["bun run wt new", "bun run dev:instance"],
  "discouragedActions": ["git worktree add", "bun run dev"],
  "entrypoint": "bun run wt new / bun run dev:instance",
  "description": "Use the project worktree/dev-instance wrappers instead of raw git worktree or raw dev server commands.",
  "owner": "host-project"
}
```

Validation:

```bash
.lazy-harness/bin/lazy capability resolve --action 'git worktree add feature/foo' --format=json
.lazy-harness/bin/lazy rules resolve --action 'git worktree add feature/foo' --format=md
.lazy-harness/bin/lazy rules resolve --intent creating_worktree --format=json
```

Expected:

- Returns the rulebook entry.
- Shows level `warn`.
- Shows preferred action `bun run wt new`.
- Shows source `.lazy-harness/rules/dev-worktree.md`.

Exit criteria:

- Exact action matching handles discouraged raw command aliases.
- Resolver remains deterministic and does not perform semantic classification.

### Phase 3 — message/action surfacing without broad hard gates

Files:

- `.lazy-harness/hooks/lifecycle/on-message-received.sh`
- `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py`
- possibly `.lazy-harness/hooks/lifecycle/helpers/check-operating-rulebook.py`
- `.lazy-harness/spec/platform/pre-response-rule-context.md`
- `.lazy-harness/spec/platform/guidance-ladder.md`

Behavior constraints:

- Do not add project-specific string branches.
- Do not interpret arbitrary user text as semantic authority.
- Only use exact action/intent labels from registered rulebook/capability metadata.
- Keep hard blocks rare and gated by Guidance Ladder L5.

Suggested first integration:

1. Pre-response reminder mentions `lazy rules resolve --intent/--action` when operating-rule cues are relevant through existing record-first obligation.
2. Generic response audit detects when a mutation command appears in tool-events and a matching `warn|block` operating rule existed but was not read/resolved.
3. Emit advisory first, not block.
4. Store misses in a bounded runtime journal.
5. Promote only through `## Hard-stop promotion` evidence.

Validation:

- Fixture with `git worktree add` and registered `warn` rule emits advisory.
- Fixture with prior `lazy rules resolve --action 'git worktree add'` evidence stays silent.
- Fixture with no matching rule stays silent.
- Fixture with `block` requires existing hard-stop promotion record and self-test fixture.

Exit criteria:

- The framework can nudge a missed operating rule without hardcoded command branches.
- No tool adapter sprawl is introduced.

### Phase 4 — downstream dogfood repair cases

Use the user-observed downstream failures as acceptance fixtures:

1. Korean discoverability:

```bash
.lazy-harness/bin/lazy map '행동규약' --format=md --limit=8
.lazy-harness/bin/lazy map '워크트리' --format=md --limit=8
.lazy-harness/bin/lazy map '인스턴스' --format=md --limit=8
```

2. Worktree rule:

- Raw `git worktree add` resolves to `bun run wt new` guidance.

3. Dev server rule:

- Raw `bun run dev` resolves to `bun run dev:instance` guidance.

4. Index freshness:

- `lazy doctor` detects missing/stale generated indexes or rulebook/capability mismatch.

Exit criteria:

- Downstream host can register worktree/dev-instance operating rules once and future agents receive deterministic guidance.

## Validation matrix

| Area | Command / fixture | Expected |
|---|---|---|
| Record discoverability | `lazy map 'project operating rulebook'` | finds plan/SDD/ADR/TDD |
| Korean discoverability | `lazy map '행동규약'` | finds rulebook records |
| Rulebook audit | `lazy rules audit --strict` | valid fixtures pass, invalid fixtures fail |
| Capability audit | `lazy capability audit --format=json` | accepts rulebook-backed capabilities |
| Action resolve | `lazy rules resolve --action 'git worktree add x'` | recommends preferred command |
| Intent resolve | `lazy rules resolve --intent creating_worktree` | returns relevant rule |
| No semantic backend | source scan | no user-text classifier branches added |
| Response audit | fixture payload | missed warn/block rule emits advisory only |
| Hard-stop promotion | `hard-stop-promotion-audit.py --strict` | block requires promotion section/fixture |
| Full validation | `.lazy-harness/bin/lazy test` | all green |

## Risk controls

- Keep Phase 1/2 non-blocking.
- New rulebook entries default to `discover` or `recommend` unless user/team confirms stronger level.
- `warn` is allowed for repeated dogfood misses or explicit project policy, but should be bypassable with reason.
- `block` requires Guidance Ladder L5 promotion.
- Avoid broad regex filters over full user text.
- Prefer exact action labels and registry metadata.
- Keep `.jcode/**` pointer/local-only.

## Open implementation questions

1. Command name: `lazy rules` vs `lazy rulebook`.
   - Recommended: `lazy rules` for short CLI, while records use “Project Operating Rulebook”.
2. Rule entry format: strict Markdown sections vs optional JSON sidecar.
   - Recommended: Markdown sections first, JSON only in capabilities.
3. Whether `.lazy-harness/rules/dev-worktree.example.md` should ship in source repo.
   - Recommended: keep examples under tests/fixtures or README, not active source policy.
4. Whether Phase 3 advisory should inspect tool-events or only response text.
   - Recommended: inspect structured tool-events only, never full freeform blobs where avoidable.
5. Whether rulebook is a new layer.
   - Recommended: treat it as a new canonical category with `Layer: Rulebook`, but keep DDD/SDD/BDD/TDD/ADR/SSOT intact for facts.

## Work breakdown

### Step 1: Design record patch

- Create ADR 0042.
- Create SDD `project-operating-rulebook.md`.
- Create TDD `project-operating-rulebook.md`.
- Update SSOT `rule-sources.md`.
- Update SSOT `capability-registry.md`.
- Update feature navigation.

### Step 2: CLI storage/audit

- Add `.lazy-harness/rules/README.md`.
- Add `scripts/rulebook.ts` with list/audit parser.
- Wire `bin/lazy rules`.
- Add self-test fixtures.

### Step 3: Capability resolver extension

- Extend schema with `preferredActions`, `discouragedActions`, `rulebookRecord`, `requiresReasonForBypass`.
- Extend `capability.ts` matching and audit.
- Add tests for action matching.

### Step 4: Rule resolver

- Add `lazy rules resolve --intent/--action`.
- Link capability matches back to rulebook entries.
- Add MD/JSON outputs.

### Step 5: Advisory lifecycle

- Add conservative response audit advisory for registered warn/block missed actions.
- Journal misses.
- Keep fail-open behavior.
- Add fixtures proving silent/noise boundaries.

### Step 6: Dogfood fixture

- Add worktree/dev-instance fixture rulebook entry under self-test temp host.
- Assert raw commands resolve to standard wrappers.
- Assert Korean aliases discover records.

## Implementation map

- Status: `planned`
- Existing source to modify:
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/capability.ts`
  - `.lazy-harness/schemas/capabilities.schema.json`
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh`
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py`
  - `.lazy-harness/scripts/self-test.py`
  - `.lazy-harness/project/feature-navigation.xml`
- Existing records to update:
  - `.lazy-harness/ssot/rule-sources.md`
  - `.lazy-harness/ssot/capability-registry.md`
  - `.lazy-harness/spec/platform/capability-resolution.md`
  - `.lazy-harness/spec/platform/guidance-ladder.md`
- New records/files:
  - `.lazy-harness/decisions/0044-project-operating-rulebook.md`
  - `.lazy-harness/spec/platform/project-operating-rulebook.md`
  - `.lazy-harness/tests/project-operating-rulebook.md`
  - `.lazy-harness/rules/README.md`
  - `.lazy-harness/scripts/rulebook.ts`
- Validation:
  - `.lazy-harness/bin/lazy rules audit --strict`
  - `.lazy-harness/bin/lazy capability audit --format=json`
  - `.lazy-harness/bin/lazy map '행동규약' --format=md --limit=8`
  - `.lazy-harness/bin/lazy test`

## Rule placement

- Rule: Lazy-harness must implement a project operating rulebook storage and resolution path separate from project fact records, with machine-readable capability bindings that can steer agent behavior by discover/recommend/default/warn/block levels.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/project-operating-rulebook-implementation-plan.md`
- Why not AGENTS.md: this is an implementation plan and architecture contract candidate, not a final universal prompt rule.
- Why not `.jcode`: the rulebook is shared framework/host behavior, while `.jcode` remains local/private wiring.
- Confirmation: user-confirmed

## Discovery capture

- DDD: no domain/business vocabulary change.
- SDD: create project operating rulebook contract and update capability resolution.
- BDD: agent behavior must distinguish fact lookup from operating-rule application.
- TDD: add regressions for rulebook audit/resolve, worktree/dev-instance guidance, and Korean discoverability.
- ADR: add ADR 0042 for the storage split and hybrid architecture.
- SSOT: update rule-sources and capability-registry.
- Planning: this plan is the execution entrypoint.

## 2026-06-10 correction — purpose-scoped retrieval, not universal record sweep

Status: user-confirmed-requirement
Confirmation: user-confirmed

User correction:

```text
중요한건 llm이 목적에따라 검색할때 영역을 선택할수 있는게 좋을꺼거든
test 를 위햇 test 관련 된걸 찾는다고 record 를 검색할필욘없잔아 그지??
...
레코드를 뒤질 필요가 없는거아냐
```

Interpretation:

The framework goal is not “always search every record layer first.” The goal is **purpose-scoped retrieval**: the agent should select the smallest relevant search space for the task.

Examples:

- Test/validation intent should start in TDD/test surfaces: `.lazy-harness/tests/**`, test capabilities, `lazy affected`, `lazy test`, source test files, and only read factual records if a contract/behavior/domain question is actually needed.
- Operating-policy intent should start in `.lazy-harness/rules/**` and capability action bindings, not the full DDD/SDD/BDD/ADR/SSOT corpus.
- Command/tool-selection intent should start with `lazy capability resolve` / `lazy rules resolve` by exact intent/action labels.
- Architecture/contract changes still need the full record/source/test package and layer completeness gate.

Current problem:

`message.received` and generic search/read debt language still nudges agents toward broad record-first retrieval. That is safer than guessing, but it is too expensive/noisy after the framework has separate rulebook, capability, test, feature-navigation, graph, and source-index spaces.

Target:

Add a retrieval routing layer that is deterministic and explicit, not a raw semantic classifier:

```text
purpose / mode / explicit CLI option
  -> chosen search spaces
  -> cue-only candidates
  -> required reads limited to those spaces
  -> escalation to broader records only when needed
```

The router should be tool/user controlled, for example through explicit modes such as:

- `test`
- `rulebook`
- `capability`
- `source`
- `record`
- `architecture`
- `full`

Potential CLI surfaces:

- `lazy find --purpose test <query>`
- `lazy map --scope tests <query>`
- `lazy route --purpose test <query>`
- `lazy rules resolve --intent ...` and `lazy capability resolve --intent ...` for operating rules/tool choices

## Design constraints

- Do not infer high-stakes intent from raw user text inside lifecycle hooks.
- Prefer explicit user/LLM-selected purpose flags or command-specific resolver calls.
- Keep outputs cue-only unless real files are read.
- Preserve root-bound search.
- Allow escalation: test-scoped search can widen to SDD/BDD/SSOT when tests imply contract/behavior/config impact.
- Update response audit so it does not punish purpose-scoped retrieval for not reading irrelevant records.

## Candidate implementation options

A. Add `lazy map --scope <records|tests|rules|capabilities|source|feature|graph|full>`.
   - Minimal change to existing retrieval surface.
   - Needs record-map source-space filtering.

B. Add new `lazy find --purpose <test|rulebook|capability|source|record|architecture|full>`.
   - Clearer product model: purpose first, sources second.
   - Can orchestrate `lazy map`, `lazy rules`, `lazy capability`, grep/source search, and test files.

C. Add `lazy route --purpose ...` that only prints the recommended commands/search spaces.
   - Safer first step because it does not pretend to retrieve evidence.
   - Requires the LLM to execute selected commands.

D. Extend capability registry with retrieval capabilities and let `lazy capability resolve --intent testing_changes` return test search/validation actions.
   - Reuses existing capability mechanism.
   - May be too indirect for normal search UX unless combined with A or B.

Recommended candidate: **B + D later**.

Start with `lazy find --purpose ...` as a user/LLM explicit retrieval entrypoint. Then register common purpose routes as capabilities so project-specific hosts can override/add routes.

## Rule placement

- Rule: Lazy-harness retrieval should become purpose-scoped; agents should not perform broad record sweeps when a task only needs test/rulebook/capability/source surfaces, and should escalate to broader records only when needed.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/project-operating-rulebook-implementation-plan.md`
- Why not AGENTS.md: this is a retrieval architecture requirement and implementation option set, not yet a final prompt grammar rule.
- Why not `.jcode`: it changes shared framework retrieval behavior across hosts, not local/private Jcode wiring.
- Confirmation: user-confirmed

## Discovery capture

- DDD: retrieval vocabulary now includes “purpose-scoped retrieval”; candidate DDD update may be needed.
- SDD: search/read debt and record-map contracts need a purpose-scoped successor or extension.
- BDD: LLM retrieval behavior should route by task purpose before reading broad record sets.
- TDD: add regression proving test-purpose search does not require reading unrelated fact records before test/source surfaces.
- ADR: likely needed if replacing record-first static debt language with purpose-first routing.
- SSOT: CLI boundary must still forbid raw-text semantic authority in lifecycle hooks.
- Planning: this section is the active requirement entrypoint.

### Information retrieval vs operating-rule retrieval

The retrieval router must distinguish two fundamentally different questions:

1. **Information / fact retrieval**
   - Question: “What is true about this project?”
   - Search spaces:
     - DDD/SDD/BDD/TDD/ADR/SSOT records
     - implementation maps
     - source/tests/config/docs
   - Examples:
     - contract details
     - actual implementation facts
     - project identity
     - schema/config/source-of-truth
     - why a design decision exists
   - Records are appropriate and often required.

2. **Operating-rule / behavior retrieval**
   - Question: “How should I act in this project?”
   - Search spaces:
     - `.lazy-harness/rules/**`
     - `.lazy-harness/ssot/capabilities.json`
     - `lazy rules resolve`
     - `lazy capability resolve`
     - validation/test capabilities when the action is testing
   - Examples:
     - preferred command
     - discouraged command
     - required validation workflow
     - bypass policy
     - default/warn/block level
   - Broad fact-record retrieval is token waste unless the rule points to missing factual support or the user asks for project facts.

The framework should therefore avoid treating “record search” as a universal synonym for “context retrieval.” Records are one retrieval space among several. The selected space should follow the task purpose.

Operational rule:

```text
If the user/LLM is deciding what to do, start from rulebook/capability/action surfaces.
If the user/LLM is deciding what is true, start from project fact records and implementation evidence.
If the task is test/validation-only, start from tests/test capabilities/source test files and widen only when contract/behavior/config facts are needed.
```

This requirement should be promoted from planning into a dedicated SDD/BDD/TDD package before changing lifecycle hooks, because current `search-read-debt` still assumes broad record/source/test evidence as the generic safety baseline.
