# Validation Graph + Hook Gates Plan

Date: 2026-05-13
Status: proposed
Purpose: keep `lazy test` fast as the framework grows by replacing always-full validation with DDD/SDD/BDD/TDD-aware validation planning, caching, and lifecycle hook enforcement.

## 1. Problem

`lazy test` currently works as a framework self-test suite. As DDD/SDD/BDD/TDD detectors, interview loop, affected tests, aftershock, host profile, and future report/export features grow, a single ever-expanding full test will become slow and will discourage frequent validation.

The goal is not to remove full tests. The goal is to make full tests an explicit escalation path, while the default path runs only the checks required by the changed files and impacted records.

## 2. Target model

```text
changed files
→ reference resolver
→ layer impact graph
→ validation planner
→ cache lookup
→ selected checks
→ hook gate result
→ missing record/test/question if needed
```

The framework should answer three questions before running checks:

1. What changed?
2. Which records/layers does that change affect?
3. Which validations protect those records/layers?

## 3. Layer policy

| Impact | Trigger examples | Required evidence |
|---|---|---|
| DDD | entity, domain term, business rule, invariant | domain record exists or updated, ubiquitous language/aggregate/bounded context linkage |
| SDD | API, schema, contract, component interface, data shape | spec record exists or updated, contract relation present |
| BDD | UI flow, user journey, behavior, acceptance condition | scenario exists or updated, flow relation present |
| TDD | bug fix, regression risk, changed source with matching tests | affected test run, regression entry for Fix commits, test map linkage |
| ADR | architecture, tradeoff, policy, irreversible design decision | ADR exists or structured question/decision log created |
| SSOT | config, env, schema, generated source, registry | ssot registry updated, source-of-truth relation present |

## 4. New command surface

```bash
.lazy-harness/bin/lazy validate --plan
.lazy-harness/bin/lazy validate --changed
.lazy-harness/bin/lazy validate --enforce
.lazy-harness/bin/lazy validate --full
.lazy-harness/bin/lazy validate --budget 15s
```

Later aliases:

```bash
lazy test             # default to validate --changed --budget default
lazy test --full      # existing full self-test behavior
lazy test --plan      # print selected checks and reasons
```

## 5. Validation planner

Add:

```text
.lazy-harness/scripts/validation-planner.ts
.lazy-harness/schemas/validation-plan.schema.json
.lazy-harness/generated/validation-cache.json
.lazy-harness/tests/validation-plan.xml
```

Planner input:

```json
{
  "changedFiles": ["src/main/services/referral.ts"],
  "mode": "plan|changed|enforce|full",
  "budgetSeconds": 15,
  "source": "cli|hook|pre-push|self-test"
}
```

Planner output:

```json
{
  "status": "pass|warn|fail",
  "mode": "changed",
  "changedFiles": [],
  "impactedLayers": {
    "ddd": { "impacted": true, "records": [], "missing": true },
    "sdd": { "impacted": false },
    "bdd": { "impacted": false },
    "tdd": { "impacted": true, "tests": [], "missing": true },
    "adr": { "impacted": false },
    "ssot": { "impacted": false }
  },
  "checks": [
    {
      "id": "tdd-affected-test",
      "reason": "source file changed and matching test exists",
      "command": "bun .lazy-harness/scripts/affected-test-runner.ts --files ...",
      "cacheKey": "sha256:...",
      "cache": "hit|miss|bypass",
      "required": true,
      "estimatedMs": 1200
    }
  ],
  "questions": [],
  "humanRequired": false
}
```

## 6. Check registry

Each validation check should declare metadata instead of being hardcoded only inside `self-test.py`.

Example registry record:

```json
{
  "id": "doctor-d03-adr-sequence",
  "layers": ["adr"],
  "protects": [".lazy-harness/decisions/**", ".lazy-harness/logs/decisions.jsonl"],
  "command": "python3 .lazy-harness/scripts/doctor.py --profile smoke --check D03",
  "tier": "smoke",
  "cacheable": true,
  "failStrategy": "closed",
  "budgetMs": 500
}
```

Initial registry can be embedded in `validation-planner.ts`; later promote to `.lazy-harness/manifests/validation-checks.json`.

## 7. Cache policy

Cache key must include:

- check id
- check implementation file hash
- changed file hash
- dependent record file hashes
- relevant package/config hash
- lazy-harness framework commit hash

Cache is safe only when all inputs match.

Cache file:

```text
.lazy-harness/generated/validation-cache.json
```

This remains derived and ignored/regenerated.

## 8. Hook integration

### 8.1 tool.execute.before

Fast gate only. It should not run heavy tests.

Responsibilities:

- ensure record search happened before code edit
- detect obviously forbidden edits
- optionally warn if edit target has no mapped record

Target budget: under 300ms.

### 8.2 response.completed

Main validation planning gate.

Responsibilities:

- inspect changed files
- run `validation-planner --mode plan`
- if required evidence is missing, emit structured ask or deny text
- if checks are cheap and required, run selected checks under budget
- if budget exceeded, tell agent exact command to run next

Target budget: under 5s by default.

### 8.3 pre-push / explicit full

Full escalation.

Responsibilities:

- run full self-test
- run doctor smoke/full as configured
- verify registry/cache/schema freshness
- no cache bypass unless explicitly allowed

## 9. Test tiers

| Tier | When | Expected time | Examples |
|---|---|---:|---|
| micro | every write/response | < 300ms | search gate, path policy, JSON parse of touched file |
| changed | default `lazy test` | < 15s | layer impact, affected tests, selected doctor checks |
| smoke | commit/pre-push | < 30s | doctor smoke, key lifecycle fixtures, schema parse |
| full | release/nightly/major refactor | no strict short budget | all fixtures, all E2E, host dogfood |

## 10. Implementation phases

### Phase A — Planner skeleton

- Add `validation-planner.ts` with `--plan`, `--changed`, `--full`, `--budget`.
- Reuse existing `layer-impact-gate.ts`, `reference-resolver.ts`, `affected-test-runner.ts`.
- Output JSON and human-readable summary.
- No enforcement yet.

Success:

```bash
bun .lazy-harness/scripts/validation-planner.ts --file src/foo.ts --plan
```

prints impacted layers and selected checks.

### Phase B — Check registry and cache

- Add internal check registry.
- Add cache key calculation.
- Cache only pure checks first: XML parse, JSONL parse, schema metadata, reference index freshness.
- Do not cache hook integration or tests with side effects yet.

Success:

- second run shows cache hits
- modifying a protected record invalidates cache

### Phase C — Hook connection

- Update `on-response-completed.sh` helper chain to call planner.
- Emit structured gate message when DDD/SDD/BDD/TDD evidence is missing.
- Keep fail-open/warn for early alpha, then promote selected gates to fail-closed.

Success:

- source edit without corresponding TDD/record produces exact required action
- docs-only edit does not run expensive tests

### Phase D — CLI unification

- Add `lazy validate` subcommand to `.lazy-harness/bin/lazy`.
- Make `lazy test` default to planner-driven changed mode.
- Keep `lazy test --full` as current self-test equivalent.

Success:

```bash
.lazy-harness/bin/lazy validate --plan
.lazy-harness/bin/lazy test --full
```

both work and are documented.

### Phase E — Host dogfooding

- Sync to Medivance.
- Run planner against real changed host feature files.
- Measure false positives/false negatives.
- Promote repeated gaps into project-profile outputs.

Success:

- host feature flow requires only relevant checks
- no silent skip of DDD/SDD/BDD/TDD evidence

## 11. Metrics

Track in `logs/validations.jsonl`:

- selected check count
- skipped by cache count
- total validation time
- budget exceeded count
- missing layer count
- human gate count
- false positive suppression decisions

Target:

- default changed validation < 15s
- tool gate < 300ms
- response hook < 5s unless explicitly escalated
- full self-test can grow, but not default path

## 12. Design principle

Do not make `lazy test` a single growing wall.

Make validation explainable:

```text
This changed file X.
It impacts layer Y.
Layer Y is protected by checks A/B.
Check A is cached, check B must run.
Record Z is missing, so completion is blocked or asks a structured question.
```

That is the lazy-harness advantage over a plain test suite.

## 13. Knowledge intake / registration gap

Observation from dogfooding: even when the framework has DDD/SDD/BDD/TDD folders, knowledge is not reliably injected or registered automatically during real work.

Current failure mode:

```text
user says important project knowledge
→ agent understands it in chat
→ maybe uses it once
→ no durable DDD/SDD/BDD/TDD/ADR/SSOT record is created
→ next turn/session/hook cannot retrieve it
→ same question repeats or AI guesses
```

This is a separate problem from validation speed. Validation can only check records that exist. If intake is weak, the validation graph becomes precise but empty.

## 14. Target: Knowledge Intake Pipeline

Every useful piece of knowledge should pass through this pipeline:

```text
conversation / code change / test failure / user correction
→ knowledge candidate detector
→ layer classifier
→ confidence score
→ structured ask when ambiguous
→ record writer / updater
→ reference index refresh
→ prompt/hook injection path
→ future validation can use it
```

## 15. Knowledge candidate types

| Candidate | Example | Target layer | Default action |
|---|---|---|---|
| Domain term | "Referral is not just a lead" | DDD | ask/record in domain |
| Business invariant | "A discharged patient cannot be re-opened without approval" | DDD/ADR | structured ask if policy vs term ambiguous |
| API/data contract | "Referral status comes from external EMR" | SDD/SSOT | record contract/source |
| User behavior | "Coordinator must see urgent referrals first" | BDD | scenario/update behavior map |
| Regression fact | "This bug happened before when status was null" | TDD/regression | registry + test mapping |
| Project convention | "Use shadcn, not MUI" | SDD/frontend or project profile | update project profile/spec |
| User correction | "No, message means Twilio SMS here" | DDD/SSOT | record immediately after confirmation |
| Decision/tradeoff | "Choose simple layered architecture for now" | ADR | ADR/decision log |

## 16. Intake command surface

Add:

```bash
.lazy-harness/bin/lazy intake --from-transcript <file>
.lazy-harness/bin/lazy intake --text "..."
.lazy-harness/bin/lazy intake --changed
.lazy-harness/bin/lazy intake --plan
.lazy-harness/bin/lazy intake --apply
```

Script:

```text
.lazy-harness/scripts/knowledge-intake.ts
.lazy-harness/schemas/knowledge-candidate.schema.json
.lazy-harness/questions/knowledge-intake.xml
```

Output example:

```json
{
  "candidates": [
    {
      "id": "ki-001",
      "text": "Referral is not just a lead",
      "candidateType": "domain-term",
      "recommendedLayer": "ddd",
      "confidence": "medium",
      "targetFile": ".lazy-harness/domain/ubiquitous-language.xml",
      "action": "ask",
      "question": {
        "prompt": "How should this knowledge be registered?",
        "options": [
          { "id": "A", "label": "DDD term", "recommended": true },
          { "id": "B", "label": "Business invariant" },
          { "id": "C", "label": "ADR policy" },
          { "id": "D", "label": "Skip/defer with reason" },
          { "id": "custom", "label": "Type your own" }
        ]
      }
    }
  ]
}
```

## 17. Automatic injection paths

There are two different meanings of injection:

### 17.0 Private instruction substrate, Jcode M45

This plan should prefer Jcode private instruction loading over noisy hook spam whenever possible.

M45-style private instruction behavior is the desired substrate:

- `.jcode/AGENTS.md`, `.jcode/harness/*.md`, future `.jcode/instructions.md`, and `.jcode/rules/*.md` are treated as user-private Jcode instructions, not team-shared project files.
- `/info` should show exactly which private instruction files were loaded or skipped, for example:
  - `loaded: /project/.jcode/AGENTS.md`
  - `loaded: /project/.jcode/harness/debug.md`
  - `skipped: /project/AGENTS.md because ignore_project_agents=true`
- `ignore_project_agents=true` should suppress shared project `AGENTS.md`, but must not suppress private `.jcode/*` instructions.
- Later stages can add private instruction globs such as `.jcode/rules/*.md` and nested `.jcode/AGENTS.md` lookup near edited files.

Implication for lazy-harness:

- Stable operating rules belong in private `.jcode/*` instructions.
- Hooks should stay short, conditional, and action-oriented.
- Knowledge graph context should be injected only when relevant, with citations.
- Forced hook messages remain as safety gates, not the primary instruction channel.

### 17.1 Prompt injection

Make the agent aware of relevant existing records before work.

```text
user request / changed file
→ reference-resolver
→ top DDD/SDD/BDD/TDD/ADR/SSOT records
→ compact summary injected by hook or shown as gate message
```

This should not inject the whole `.lazy-harness`. It should inject only the top relevant records with citations.

### 17.2 Record registration

Make new knowledge durable.

```text
new confirmed knowledge
→ layer classifier
→ record writer
→ index refresh
→ validation graph can use it later
```

Prompt injection without registration is temporary memory. Registration without injection is dead documentation. Both are required.

## 18. Lifecycle integration for intake

### 18.1 response.completed

Run lightweight intake detection on the last assistant/user exchange.

If a candidate is high confidence and low risk:

- suggest exact record update
- optionally apply if the user already explicitly confirmed it

If medium/ambiguous:

- create structured question in `.lazy-harness/questions/open.xml`
- block only if the next code change depends on the unresolved knowledge

### 18.2 tool.execute.before

Before editing code, check whether relevant records were loaded.

If no relevant record exists:

- do not immediately create records
- ask/intake first when the change appears to depend on unstored domain/spec/behavior/test knowledge

### 18.3 client.disconnect / session end

Summarize unregistered knowledge candidates:

```text
These 3 facts were used in chat but not recorded.
A) Record now
B) Carry as open questions
C) Discard as temporary
```

## 19. Record writer strategy

Start with conservative append/update only:

| Layer | v1 writer behavior |
|---|---|
| DDD | append term/invariant candidate to `domain/ubiquitous-language.xml` or bounded context file |
| SDD | append contract/source note to relevant `spec/**` file |
| BDD | append scenario candidate to `behavior/scenarios/*.xml` |
| TDD | append regression/test mapping to `tests/test-protection-matrix.xml` or `regression/registry.jsonl` |
| ADR | create decision log candidate first, ADR only after explicit confirmation |
| SSOT | update registry candidate, require confirmation for source-of-truth changes |

Do not let the agent silently decide the primary layer when more than one layer is plausible. Use structured ask.

## 20. Implementation order for intake

### Intake A — Detection only

- Add `knowledge-intake.ts --text --plan`.
- Detect explicit phrases: "X means Y", "always", "never", "must", "use X not Y", "this is domain", "bug happened because".
- Output candidates only. No writes.

### Intake B — Layer classifier

- Add rule-based classifier for DDD/SDD/BDD/TDD/ADR/SSOT.
- Use confidence: high / medium / low / ambiguous.
- Medium+ambiguous creates structured ask.

### Intake C — Record writer v1

- Implement append-only writers for safe destinations.
- Require explicit confirmation for ADR/SSOT or ambiguous layer.

### Intake D — Injection summary

- Add `reference-resolver --format context` or `knowledge-intake --inject-context`.
- Produce compact, cited context summary for hooks/agents.

### Intake E — Hook integration

- response.completed detects unregistered knowledge candidates.
- tool.execute.before checks whether edit depends on missing knowledge.
- client.disconnect/session end reports unregistered knowledge backlog.

## 21. Success criteria

A good implementation means:

1. User correction becomes durable record after confirmation.
2. Next session can retrieve that record automatically.
3. Code edit touching a domain/spec/behavior/test area sees relevant records before edit.
4. Missing DDD/SDD/BDD/TDD knowledge creates structured ask, not silent guessing.
5. `lazy test` uses registered knowledge to select validation, rather than blindly running everything.

## 22. Combined architecture

```text
Knowledge Intake Pipeline
  creates/updates records
        ↓
Reference Resolver
  finds relevant records
        ↓
Validation Graph
  maps records to checks
        ↓
Hook Gates
  enforce only what is required
```

Without intake, validation has no facts.
Without resolver, facts are not injected.
Without validation graph, facts do not protect behavior.
Without hooks, the agent can ignore the graph.

## 23. Concrete staged execution roadmap

This roadmap is the preferred implementation order. Do not start with validation-planner or full hook enforcement. Start by making knowledge registration observable and testable.

### Stage 0 — Hook output protocol hardening (done 2026-05-13)

Problem found during planning: Jcode lifecycle hooks require JSON hook decisions. Plain text helper output causes:

```text
invalid hook decision JSON from command: .lazy-harness/hooks/lifecycle/on-response-completed.sh
```

Required invariant:

- `tool.execute.before` deny output must be JSON: `{"action":"deny","reason":"..."}`.
- `response.completed` guidance output must be JSON injection: `{"inject":{"body":"...","format":"system_reminder"}}`.
- Helper scripts may still emit plain text internally, but wrapper hooks must convert it.

Evidence:

- `3c538e2 Fix: emit JSON decisions from Jcode lifecycle hooks`
- `9a3ea75 Chore: register Jcode hook JSON regression`
- Source validation: `.lazy-harness/scripts/self-test.py`, `doctor.py --profile smoke`, `jcode doctor --no-update`
- Host validation: synced to `/home/lazydino/dev/medivance`, `.lazy-harness/bin/lazy test` passed.

### Stage 1 — Knowledge intake detector, no writes

Deliverables:

- `.lazy-harness/scripts/knowledge-intake.ts`
- fixtures under `.lazy-harness/triggers/fixtures/knowledge-intake/`
- self-test check for detector fixtures

Command:

```bash
bun .lazy-harness/scripts/knowledge-intake.ts --text "Referral은 lead가 아니라 clinical intake record야" --plan
```

Supported candidate types in v1:

1. DDD term/invariant
2. SDD contract/source
3. BDD user behavior/scenario
4. TDD regression/test fact
5. ADR decision/tradeoff
6. SSOT config/source-of-truth
7. ambiguous layer

Exit policy:

- Always exit 0 in `--plan` mode.
- Output JSON by default plus `--format ask` for human-readable hook messages.
- No filesystem writes.

Validation:

```bash
bun .lazy-harness/scripts/knowledge-intake.ts --fixture all --plan
.lazy-harness/scripts/self-test.py
```

### Stage 2 — Structured ask generation

Deliverables:

- knowledge candidate schema
- A/B/C/D option generation
- integration with `.lazy-harness/questions/open.xml` in dry-run mode first

Policy:

- high confidence single-layer candidate can recommend a target file
- medium/low/ambiguous candidate must produce structured ask
- no silent primary layer selection when DDD/BDD/ADR or SDD/SSOT overlap

Validation fixtures:

- `Referral means clinical intake record` → DDD recommended
- `Coordinator must see urgent referral first` → BDD vs DDD ambiguous
- `Use shadcn not MUI` → SDD/frontend or project profile ambiguous
- `Bug happened when status was null` → TDD/regression recommended
- `API status comes from external EMR` → SDD vs SSOT ambiguous

### Stage 3 — Append-only record writer

Deliverables:

- `knowledge-intake.ts --apply --answer A|B|C|D`
- append-only writers for safe records
- dry-run diff output

Safety rules:

- ADR and SSOT require explicit confirmation.
- Existing XML must remain parseable.
- Writer must be append-only or narrowly scoped. No broad rewrite.
- Every write emits decisions/log evidence.

Initial write targets:

| Layer | Target |
|---|---|
| DDD | `.lazy-harness/domain/ubiquitous-language.xml` |
| SDD | `.lazy-harness/spec/spec-language.xml` or project profile spec file |
| BDD | `.lazy-harness/behavior/scenarios/*.xml` or scenario queue |
| TDD | `.lazy-harness/regression/registry.jsonl` / `tests/test-protection-matrix.xml` |
| ADR | `.lazy-harness/logs/decisions.jsonl` candidate, ADR later |
| SSOT | `.lazy-harness/ssot/registry.xml` candidate with confirmation |

### Stage 4 — response.completed intake injection

Deliverables:

- lifecycle helper: `.lazy-harness/hooks/lifecycle/helpers/check-knowledge-intake.sh`
- wrapper already emits JSON injection from helper text
- dedupe/cache so the same candidate is not repeated forever

Message budget:

- max 30 lines
- max 3 candidates
- must include exact next actions

Example injected body:

```text
[lazy-harness intake]
Unregistered knowledge candidates:
1. "Referral은 lead가 아니라 clinical intake record"
   Recommended: DDD → ubiquitous-language.xml
   Next: A) record B) ask C) defer with reason D) discard
```

Escalation:

- first occurrence: inject warning
- repeated candidate used before edit: block at tool.execute.before
- confirmed candidate not recorded: create question entry

### Stage 5 — Context injection before edit

Deliverables:

- `reference-resolver --format context` or `lazy context --file <path>`
- `tool.execute.before` hook can ask for context lookup when no relevant records were loaded

Policy:

- inject top 3 to 5 relevant records only
- include citations/path
- never dump whole DDD/SDD/BDD/TDD folders

Example:

```text
[lazy-harness context]
src/referral.ts relevant records:
- DDD: Referral = clinical intake record (.lazy-harness/domain/...)
- BDD: urgent referrals first (.lazy-harness/behavior/...)
- TDD: null status regression (.lazy-harness/regression/...)
```

### Stage 6 — Validation planner

Deliverables:

- `.lazy-harness/scripts/validation-planner.ts`
- `--plan`, `--changed`, `--enforce`, `--full`, `--budget`
- check registry and cache v1

Policy:

- default validates changed/risk impacted checks, not full suite
- full remains explicit
- cache only pure checks first
- output must explain why each check was selected or skipped

### Stage 7 — CLI unification

Deliverables:

```bash
.lazy-harness/bin/lazy intake --text "..." --plan
.lazy-harness/bin/lazy intake --apply
.lazy-harness/bin/lazy context --file <path>
.lazy-harness/bin/lazy validate --plan
.lazy-harness/bin/lazy validate --changed
.lazy-harness/bin/lazy test --full
```

Default policy:

- `lazy test` eventually becomes changed/risk validation.
- `lazy test --full` preserves current self-test.
- `pre-push` can run full or smoke+changed based on project profile.

### Stage 8 — Host dogfooding loop

Every framework change that affects hooks/intake/validation must be synced to Medivance:

```bash
cd /home/lazydino/dev/medivance
bun ~/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts \
  --from ~/dev/lazy-harness \
  --target ~/dev/medivance \
  --force
.lazy-harness/bin/lazy test
```

Record pilot findings back into this source repo. Do not edit framework source directly inside Medivance.

## 24. Non-negotiable implementation rules

1. Hook stdout must always be valid Jcode hook decision JSON when non-empty.
2. Hook messages must be short, conditional, and action-oriented.
3. Do not auto-write ambiguous knowledge.
4. Do not rely on chat memory as durable knowledge.
5. Every confirmed reusable fact must have a path into DDD/SDD/BDD/TDD/ADR/SSOT.
6. Every new `Fix:` commit must have a regression registry entry.
7. Every hook/intake/validation framework change must be dogfooded on Medivance after source validation.
