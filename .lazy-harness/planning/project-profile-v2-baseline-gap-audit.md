# Planning — Project Profile V2 Baseline / Gap Audit

Status: completed-audit-and-runtime-dry-run
Date: 2026-06-17
Layer: Planning
Related roadmap: `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md#phase-2--project-profile--interview-as-one-bootstrap-channel`
Related SDD: `.lazy-harness/spec/platform/project-profile-v2.md`
Related TDD: `.lazy-harness/tests/project-profile-v2.md`
Related fixture: `.lazy-harness/fixtures/project-profile-v2/interview-output.json`
Related update loop: `.lazy-harness/spec/platform/project-map-update-loop-v2.md`, `.lazy-harness/ssot/project-map-ingestion-sources.md`
Related source: `.lazy-harness/scripts/project-profile.ts`

## Rule digest

- Status: active audit result + first runtime dry-run slice implemented
- Layer: Planning
- Scope: framework-global
- Applies when:
  - starting Phase 2 Project Profile / Interview implementation
  - deciding whether V2 runtime work is ready
  - designing Project Profile V2 dry-run output
- Must:
  - preserve V1 `project-profile.ts` modes: `inspect`, `plan`, `apply`, `interview`, `fill`
  - keep `fill --confirm` confirmed-answer only
  - keep V2 runtime as read-only dry-run output first
  - align V2 profile refresh with Project Map update-loop `project-profile-refresh` semantics
  - keep Pi primary and Jcode compatibility in V2 packet metadata
  - keep unconfirmed Project Map seeds and policies as candidates/unresolved ambiguities
- Must not:
  - replace V1 semantics without a separate migration/ADR
  - write canonical Project Profile/Project Map/policy records from V2 dry-run output
  - turn Project Interview into a special authority path
  - introduce silent defaults or generated semantic-authority fields
- Record completion:
  - Phase 2 runtime work should update this audit, SDD, TDD, fixture, `project-profile.ts`, self-test, manifest, graph rows, and validation logs together.

## Audit purpose

The user selected Phase 2 option 1: baseline/gap audit before implementation. This record compares:

1. Phase 1.5 Project Map update-loop contract,
2. Phase 2 Project Profile V2 SDD/TDD/fixture,
3. current `project-profile.ts` V1 runtime behavior,
4. current self-test/validation baseline.

## Evidence read

Records and source inspected:

- `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md`
- `.lazy-harness/spec/platform/project-profile-v2.md`
- `.lazy-harness/tests/project-profile-v2.md`
- `.lazy-harness/fixtures/project-profile-v2/interview-output.json`
- `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
- `.lazy-harness/ssot/project-map-ingestion-sources.md`
- `.lazy-harness/fixtures/project-map-update-loop-v2/events.json`
- `.lazy-harness/scripts/project-profile.ts`
- `.lazy-harness/scripts/self-test.py`

Commands run:

```bash
bun .lazy-harness/scripts/project-profile.ts --mode inspect --format json
bun .lazy-harness/scripts/project-profile.ts --mode interview --dry-run --format json
python3 .lazy-harness/scripts/self-test.py --scope framework | grep -E 'project-profile|Project Profile|lazy-harness self-test ok'
```

## Current runtime baseline

`project-profile.ts` currently exposes V1 modes only:

```ts
type Mode = 'inspect' | 'plan' | 'apply' | 'interview' | 'fill'
```

Observed source behavior:

- `inspect` reports required artifact presence, document-ingestion handoff, answer completeness, option gate, and next actions.
- `plan` proposes missing `needs-interview` skeletons.
- `apply --confirm` writes skeletons only.
- `interview --dry-run` builds questions from existing `status="needs-interview"` fields.
- `interview --confirm` writes `.lazy-harness/project/profile-interview.xml`.
- `fill --dry-run/--confirm` updates only explicit matched answers.

Current host-root inspect summary:

```json
{
  "mode": "project-profile.inspect",
  "schemaVersion": "1.0",
  "requiredArtifacts": 5,
  "summary": {
    "present": 1,
    "missing": 4,
    "artifactsComplete": false,
    "needsInterviewFields": 0,
    "confirmedFields": 11,
    "answersComplete": false,
    "complete": false
  }
}
```

Current host-root interview dry-run summary:

```json
{
  "mode": "project-profile.interview",
  "schemaVersion": "1.0",
  "dryRun": true,
  "questions": 0,
  "warnings": [
    "Interview mode does not infer or fill profile values without confirmed answers.",
    "Use document-ingestion candidates only as evidence; Project Profile remains interview-first.",
    "Some Project Profile artifacts are missing; run plan/apply skeleton before completing the interview."
  ]
}
```

Interpretation: current host-root profile artifacts are incomplete, and V1 correctly refuses to infer profile content. This is not a bug. It is the safe baseline to preserve.

## Current design baseline

Project Profile V2 records already define a desired dry-run packet:

```json
{
  "schemaVersion": "project-profile-interview-v2/v1",
  "mode": "interview-v2",
  "adapterBoundary": { "primary": "pi", "compatibility": ["jcode"] },
  "projectMapSeeds": [],
  "policyCandidates": [],
  "questionGroups": [],
  "unresolvedAmbiguities": [],
  "writes": { "dryRun": true, "confirmedOnly": true }
}
```

The fixture includes:

- `adapterBoundary.primary == "pi"`, compatibility includes `jcode`.
- `questionGroups` for project purpose, source ownership, system design, domain vocabulary, validation policy, dependency policy, security/privacy, and human confirmation.
- `projectMapSeeds` with Project Map cluster metadata.
- `policyCandidates` with stage-aware `discover`/`recommend` levels.
- `unresolvedAmbiguities` including `policy-storage-target`.
- `proposedWrites` requiring confirmation.

Phase 1.5 update-loop records already define:

- event type `project-profile-refresh`,
- source `project-profile`,
- candidate/canonical transitions,
- adapter events as sources, not authorities.

## Gap matrix

| Area | Current baseline | V2 target | Gap | Next action |
|---|---|---|---|---|
| CLI mode | V1 `inspect/plan/apply/interview/fill` only | `interview-v2` or equivalent dry-run packet | V2 runtime mode absent | Add read-only `interview-v2` mode without writes. |
| Packet schema | V1 `schemaVersion: "1.0"`, mode `project-profile.interview` | `project-profile-interview-v2/v1`, mode `interview-v2` | V2 packet not emitted | Implement `ProjectProfileInterviewV2Packet` type and builder. |
| Question model | Questions derive from existing `needs-interview` XML fields | Structured question groups across project dimensions | V1 cannot seed missing-context groups before skeletons | Add grouped V2 questions independent of canonical writes. |
| Project Map seeds | No runtime output | `projectMapSeeds` with cluster/branch/edge metadata | Not emitted | Derive fixture-like seed candidates only. |
| Policy candidates | No runtime output | stage-aware `policyCandidates` | Not emitted | Include discover/recommend policy candidates, not defaults. |
| Ambiguity queue | V1 warnings/nextActions only | `unresolvedAmbiguities` objects | Not emitted | Carry unresolved storage/policy decisions as candidate questions. |
| Update-loop alignment | V1 profile output has no update event | `project-profile-refresh` event semantics | Bridge absent | Include update-loop-ready metadata or event candidates, but no canonical write. |
| Validation | Existing self-test protects V1 behavior; V2 fixture/TDD are design-only | runtime fixture self-test after implementation | Future test absent by design | Add focused runtime self-test with implementation. |
| Backward compatibility | Existing V1 tests green | V1 remains green | Must preserve | Add V2 mode without changing existing mode behavior. |

## Implemented runtime slice

Implemented the smallest runtime slice:

```text
project-profile.ts --mode interview-v2 --dry-run --format json
```

Scope:

1. Add mode parsing for `interview-v2`.
2. Add `ProjectProfileInterviewV2Packet` and helper types.
3. Build a read-only packet shaped like `.lazy-harness/fixtures/project-profile-v2/interview-output.json`.
4. Include current `inspect(args)` summary as evidence/context only.
5. Include Project Map seed candidates and policy candidates from fixture-compatible static definitions.
6. Include `project-profile-refresh` update-loop compatibility metadata as candidate/update-event-ready data.
7. Do not write files.
8. Do not promote candidates to canonical.
9. Preserve all existing V1 self-tests.
10. Add focused self-test assertions that compare V2 output shape to the fixture and recursively reject forbidden semantic-authority fields.

Implementation result on 2026-06-17:

- `project-profile.ts#Mode` includes `interview-v2`.
- `project-profile.ts#ProjectProfileInterviewV2Packet` defines the dry-run packet.
- `project-profile.ts#buildInterviewV2Result` emits Project Map seeds, policy candidates, unresolved ambiguities, and `project-profile-refresh` event-ready metadata.
- `project-profile.ts#renderInterviewV2Md` renders a markdown summary.
- `self-test.py#check_project_profile_v2_runtime` protects shape, adapter boundary, candidate-only semantics, no writes, and forbidden fields.

Out of scope for the next slice:

- `interview-v2 --confirm`
- automatic record writes
- automatic Project Map update event append
- policy promotion/demotion runtime
- V1 mode migration or replacement

## Open decisions before larger runtime

- Whether `policy-storage-target` resolves to project-map candidate first, rules record first, capability binding first, or per-policy decision.
- Whether V2 runtime should emit actual update-loop event packets immediately or only event-ready metadata in the first slice.
- Whether future V2 apply mode writes a profile queue file or only candidate rows after user confirmation.

These do not block the recommended first dry-run slice because it is read-only and can preserve the ambiguity explicitly.

## Confirmed apply/write decision 1 — policy storage target

User confirmation on 2026-06-17: use the recommended policy storage path.

Decision:

```text
policy candidate → confirmed rulebook record → optional capability binding
```

- `policy candidate`: draft suggestion card only; not a rule and not behavior-changing.
- `.lazy-harness/rules/**`: primary canonical location for confirmed human-readable operating policies.
- `.lazy-harness/ssot/capabilities.json`: optional machine-readable binding when the confirmed rule should steer concrete intents/actions or carry an explicit level such as `recommend`, `default`, `warn`, or `block`.

Remaining open decisions:

- Whether V2 runtime should emit actual update-loop event packets immediately or only event-ready metadata in the first apply slice.
- Whether future V2 apply mode writes a profile queue file or only candidate rows after user confirmation.

## Confirmed apply/write decisions 2-3 — event metadata and queue-first apply

User confirmation on 2026-06-17: use the recommended safer first implementation path.

Decision 2:

```text
confirmed Project Profile refresh → event-ready metadata first → later explicit update-loop event append/promote
```

- The first V2 apply/write slice must not append official update-loop history immediately.
- It should store enough event-ready metadata to later create a `project-profile-refresh` update-loop event.
- This avoids making noisy or premature official history while the apply/promote flow is still being introduced.

Decision 3:

```text
interview-v2 apply → profile queue file first → later promote to candidates/rules/capabilities/events
```

- The first V2 apply/write slice should write a profile queue file, not append directly to `.lazy-harness/knowledge/candidates.jsonl`.
- The queue is the safe holding area for confirmed answers, pending policy candidates, unresolved ambiguities, and event-ready metadata.
- Later promote logic can move accepted items to Project Map candidates, `.lazy-harness/rules/**`, optional capability bindings, canonical records, or update-loop events.

Policy candidate criteria:

- Create a policy candidate when evidence describes repeated or stage-specific operating behavior, not mere facts.
- Signals include: “always”, “normally”, “before push”, “must ask”, “must not”, “prefer/avoid”, approval gates, security/privacy constraints, dependency/tooling rules, validation gates, release gates, and ownership boundaries.
- Do not create one for one-off task commands, simple facts, API/component contracts, bug reports, or ambiguous questions with no proposed operating behavior.
- Ambiguous policy-like material stays `discover` or `unresolvedAmbiguities`; `warn`/`block` require explicit confirmation or canonical evidence.

No-silent-pass-through rule:

- Future `interview-v2 apply` must not silently drop policy candidates.
- Queue entries must keep a visible status such as `pending`, `accepted`, `rejected`, or `promoted`.
- Apply output should summarize pending items so humans/agents can revisit them.
- Promotion requires explicit user/team confirmation or accepted policy record evidence.

### Rule placement

- Rule: first V2 apply/write implementation should store event-ready metadata and a profile queue first, while keeping policy candidates visible until accepted/rejected/promoted.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/project-profile-v2-baseline-gap-audit.md`
- Why not AGENTS.md: this is Phase 2 Project Profile apply/write design, not prompt grammar.
- Why not `.jcode`: Project Profile V2 is Pi-primary and adapter-neutral; Jcode is compatibility only.
- Confirmation: user-confirmed on 2026-06-17.

### Discovery capture

- DDD: none.
- BDD: future apply behavior should expose pending candidates instead of silently dropping them.
- SDD: event-ready metadata first, profile queue first, and candidate criteria confirmed.
- TDD: future apply/write tests should protect queue visibility and no immediate update-loop append.
- ADR: candidate if queue-first vs direct-candidate-row trade-off changes.
- SSOT: aligns with Project Map ingestion source vocabulary and rulebook/capability records.
- Planning: updated here.

### Rule placement

- Rule: confirmed Project Profile V2 policy candidates should become `.lazy-harness/rules/**` records first, with optional capability bindings only when action steering is needed.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/project-profile-v2-baseline-gap-audit.md`
- Why not AGENTS.md: this is Phase 2 apply/write design, not prompt grammar.
- Why not `.jcode`: Project Profile V2 is Pi-primary and adapter-neutral; Jcode is compatibility only.
- Confirmation: user-confirmed on 2026-06-17.

### Discovery capture

- DDD: none.
- BDD: none.
- SDD: policy storage path confirmed for future V2 apply/write design.
- TDD: future apply/write tests should protect this path.
- ADR: candidate if the path later changes or conflicts with Phase 3 Policy Machinery.
- SSOT: aligns with Project Operating Rulebook and Capability Registry records.
- Planning: updated here.

## Implementation map

- Status: audit complete, first dry-run runtime slice implemented.
- Primary files:
  - `.lazy-harness/planning/project-profile-v2-baseline-gap-audit.md` — this audit.
  - `.lazy-harness/spec/platform/project-profile-v2.md` — V2 output contract.
  - `.lazy-harness/tests/project-profile-v2.md` — V2 acceptance contract.
  - `.lazy-harness/fixtures/project-profile-v2/interview-output.json` — desired packet fixture.
  - `.lazy-harness/spec/platform/project-map-update-loop-v2.md` — update-loop event contract.
  - `.lazy-harness/ssot/project-map-ingestion-sources.md` — source/event vocabulary.
  - `.lazy-harness/scripts/project-profile.ts` — current V1 runtime plus read-only V2 `interview-v2 --dry-run` runtime.
  - `.lazy-harness/scripts/self-test.py` — V1 checks plus `check_project_profile_v2_runtime`.
- Current symbols:
  - `project-profile.ts#Mode`
  - `project-profile.ts#ProjectProfileInspectResult`
  - `project-profile.ts#InterviewResult`
  - `project-profile.ts#buildInterviewResult`
  - `project-profile.ts#buildFillResult`
  - `self-test.py#check_project_profile_inspect`
- Implemented symbols:
  - `project-profile.ts#ProjectProfileInterviewV2Packet`
  - `project-profile.ts#buildInterviewV2Result`
  - `project-profile.ts#renderInterviewV2Md`
  - `self-test.py#check_project_profile_v2_runtime`
- Protection now:
  - `bun .lazy-harness/scripts/project-profile.ts --mode interview-v2 --dry-run --format json`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy test`
- Protection future:
  - additional V2 apply/write-mode checks after separate approval.
- Machine index:
  - graph id: `kg_project_profile_v2_baseline_gap_audit`
  - graph id: `kg_project_profile_v2_runtime_source`
  - graph id: `kg_project_profile_v2_runtime_test`
  - graph id: `kg_project_profile_v2_runtime_sdd`
  - graph id: `kg_project_profile_v2_runtime_tdd`

## Layer completeness impact

- DDD: V2 needs domain-vocabulary question groups and Project Map fact seed candidates.
- BDD: V2 needs workflow/human-confirmation behavior and expectation seed candidates.
- SDD: V2 output contract exists and read-only `interview-v2 --dry-run` runtime is implemented.
- TDD: V1 runtime checks exist and V2 runtime dry-run checks are implemented.
- ADR: ADR needed before replacing or migrating V1 mode semantics.
- SSOT: update-loop ingestion source `project-profile` already exists; policy storage target remains open.
- Planning: this audit now records the implemented first dry-run runtime slice and next apply/write decision slice.

## Rule placement

- Rule: Phase 2 should start with a read-only `interview-v2 --dry-run` packet that preserves V1 behavior and aligns with Project Map update-loop semantics before any writes or canonical promotions.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/project-profile-v2-baseline-gap-audit.md`
- Why not AGENTS.md: this is a Phase 2 implementation audit/plan, not prompt grammar.
- Why not `.jcode`: Project Profile V2 is Pi-primary and adapter-neutral; Jcode is compatibility only.
- Confirmation: user selected Phase 2 option 1 baseline/gap audit on 2026-06-17.

## Discovery capture

- DDD: domain vocabulary group gap identified for V2 runtime.
- BDD: workflow/human-confirmation group gap identified for V2 runtime.
- SDD: runtime mode gap closed for read-only dry-run packet.
- TDD: runtime fixture/self-test check implemented.
- ADR: no ADR yet; required only if replacing V1 semantics.
- SSOT: policy-storage-target remains unresolved.
- Planning: first dry-run runtime slice implemented; next slice is V2 apply/write decision design.
