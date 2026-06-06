# SDD — Project Profile architecture contract

Status: accepted
Date: 2026-05-20
Layer: SDD
Related: `.lazy-harness/plans/project-init-interview-spec.md`, `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`, `.lazy-harness/ssot/project-identity.md`
Related: `.lazy-harness/spec/platform/search-read-debt-contract.md`
Related skill: `/lazy-project-profile`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - implementing or using Project Profile, feature navigation, or host project architecture maps
  - LLM/searcher direct retrieval needs feature aliases, routes, components, source roots, tests, or project-surface mappings
  - user-facing terms differ from source code names or English record names
- Must:
  - treat Project Profile as durable host architecture context, not chat memory
  - use `feature-navigation.xml` as a first-class retrieval source for direct record/source/test discovery
  - keep surface aliases compact, confirmed, and linked to records/code/tests when known
- Record completion:
  - changes to Project Profile retrieval fields or feature-navigation semantics update this SDD and search/read-debt/index-header records when retrieval behavior changes
- Related records:
  - `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - `.lazy-harness/spec/platform/record-digest-format.md`

## Contract

`Project Profile` means the host project's durable architecture and operating profile, not a runtime strictness preset.

It is the framework-owned mechanism that decides, creates, and maintains the project-level architecture records that future development must follow.

When a host lacks this profile, lazy-harness should create it through structured inspection and interview instead of silently defaulting.

Before asking the user to restate known facts, the Project Profile flow may use outputs from the separate Document Resource Ingestion feature when they exist. It should not own the full document ingestion/reproduction pipeline itself.

## Scope

The Project Profile covers:

- project goal and product constraints
- imported document-resource summaries produced by the separate Document Resource Ingestion feature, when available
- expected users and quality priorities
- stack and platform choices
- target folder structure and source roots
- architecture style and system design theory
- frontend design system and component policy
- backend boundaries, API style, persistence boundary, validation, error/logging policy
- domain boundaries and bounded contexts
- test strategy and validation commands
- agent operating policy, risk tier, confirmation boundaries, and forbidden edit areas
- map-first feature navigation across DDD/SDD/BDD/TDD/ADR/SSOT

## Required outputs

At minimum, a host Project Profile must materialize as records, not just chat memory:

- `.lazy-harness/project/profile.xml` or equivalent project profile root record
- `.lazy-harness/project/stack.xml`
- `.lazy-harness/project/filesystem.xml`
- `.lazy-harness/project/feature-navigation.xml`
- `.lazy-harness/tests/test-strategy.xml`
- architecture records under `.lazy-harness/spec/**` and `.lazy-harness/decisions/**`
- domain records under `.lazy-harness/domain/**` when bounded contexts or vocabulary exist
- behavior/test records when UI flows or regression protections are known

The exact format may evolve, but the profile must remain durable, inspectable, and sync-safe for downstream host use.

## Development rule

Before implementing a feature in a host project, agents should route through the Project Profile:

```text
request
→ project profile
→ relevant DDD/SDD/BDD/TDD/ADR/SSOT maps
→ existing code/tests
→ gap/conflict/risk check
→ implementation + record updates
→ validation
```

If the Project Profile is missing or incomplete for the requested area, the framework should create/update the profile or ask a structured option gate before implementation.

## Feature navigation as retrieval source

`feature-navigation.xml` is a first-class retrieval source for LLM/searcher direct reads. It should help map user-facing surfaces to records, code, routes, tests, and validation commands.

Minimum feature-navigation fields for retrieval-friendly hosts:

```xml
<feature id="example-feature" status="confirmed">
  <label>Reservation management</label>
  <aliases>
    <alias lang="ko">기능패널</alias>
    <alias lang="ko">기능화면</alias>
    <alias lang="en">feature panel</alias>
  </aliases>
  <routes>
    <route>/example-feature</route>
  </routes>
  <components>
    <component>FeaturePanel</component>
  </components>
  <records>
    <record layer="BDD">.lazy-harness/behavior/feature-surface.md</record>
    <record layer="SDD">.lazy-harness/spec/feature-surface.md</record>
  </records>
  <sourceFiles>
    <path>src/features/example-feature/FeaturePanel.tsx</path>
  </sourceFiles>
  <tests>
    <path>tests/example-feature/feature-panel.test.tsx</path>
  </tests>
</feature>
```

Direct retrieval mapping:

- `aliases/alias` give the LLM/searcher stable terms to use during root-bound search/read.
- `records/record` point to likely canonical records that the LLM/searcher must actually read before relying on them.
- `routes`, `components`, and `sourceFiles` become implementation hints for file/symbol search.
- `tests/path` becomes optional or required read depending on whether the request is a bug/regression/change.

Rules:

1. Do not invent feature-navigation aliases from a single ambiguous user phrase; ask or store as candidate until confirmed.
2. Keep host-specific feature maps in the host `.lazy-harness/project/` records, not in shared `.jcode` wiring.
3. Feature navigation is retrieval evidence, not canonical domain truth by itself. Link to DDD/SDD/BDD/TDD/ADR/SSOT records when stable.

## Non-goals

- Not the same as `fast / normal / strict / audit-only` execution presets.
- Not a place to hide host-specific rules in shared `AGENTS.md`.
- Not a one-time init wizard only; normal use can discover profile gaps and fill them.
- Not the document ingestion/reproduction engine. External document assimilation is a separate capability that Project Profile may consume.

## Implementation map

- `.lazy-harness/plans/project-init-interview-spec.md`
  - Existing plan defining the interview sections and output contract for Project Profile creation.
- `.lazy-harness/spec/platform/document-resource-ingestion.md`
  - Separate contract for reading non-harness documents, scoring staleness/duplication/contamination, and reproducing trusted knowledge into records/resources.
- `.jcode/skills/lazy-project-profile/SKILL.md`
  - Framework-owned Jcode wrapper generated by `.lazy-harness/scripts/jcode-wiring.ts`; invokes the interview-first Project Profile process in host projects.
- `.lazy-harness/scripts/jcode-wiring.ts`
  - Installs the `/lazy-project-profile` wrapper into host `.jcode/skills/` alongside other lazy-harness framework skills.
- `.lazy-harness/scripts/project-profile.ts`
  - Entry point that reports missing Project Profile artifacts, plans missing skeletons, applies only `status="needs-interview"` skeleton records after confirmation, and emits structured questions for open needs-interview fields.
  - CLI: `bun .lazy-harness/scripts/project-profile.ts --mode inspect [--format md|json] [--root <path>]`.
  - `inspect` splits artifact presence from answer completeness: `summary.artifactsComplete` means required files exist; `summary.answersComplete` means required files exist and no `status="needs-interview"` fields remain. Legacy `summary.complete` is retained as an alias for answer completeness to avoid the previous misleading `present=5 complete=true` state.
  - CLI: `bun .lazy-harness/scripts/project-profile.ts --mode plan [--format md|json] [--root <path>]`.
  - CLI: `bun .lazy-harness/scripts/project-profile.ts --mode apply --confirm [--format md|json] [--root <path>]`.
  - CLI: `bun .lazy-harness/scripts/project-profile.ts --mode interview [--dry-run|--confirm] [--format md|json] [--root <path>]`.
  - CLI: `bun .lazy-harness/scripts/project-profile.ts --mode fill --answers answers.json [--dry-run|--confirm] [--format md|json] [--root <path>]`.
  - `interview --confirm` writes only `.lazy-harness/project/profile-interview.xml`, an open-question transcript. It does not fill stack, filesystem, architecture, or validation decisions without confirmed answers.
  - `fill --confirm` updates only `status="needs-interview"` self-closing fields that match explicit answer targets from the answers file. Unmatched answers are reported and not written.
- Future host records: `.lazy-harness/project/*.xml`
  - Host-local durable profile outputs consumed before feature implementation.
  - `.lazy-harness/project/feature-navigation.xml` is the first-class Project Profile retrieval source for LLM/searcher direct reads.
- `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - Defines the static search/read-debt evidence loop that keeps Project Profile retrieval LLM-owned.
- `.lazy-harness/project/feature-navigation.xml`
  - Source project feature map fixture used by self-test and direct retrieval checks.
- `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
  - Defines Project Profile as the `config.json`/host profile part of the grammar+vocabulary model.

## Discovery capture

- DDD: candidate, Project Profile may seed bounded-context/domain vocabulary records per host.
- SDD: updated, this contract defines Project Profile semantics.
- BDD: candidate, UI/product flows can be generated as profile outputs.
- TDD: self-test protects feature-navigation parsing through inline fixtures; test strategy remains a required profile output.
- ADR: none, existing ADR 0024 already establishes the grammar/vocabulary model.
- SSOT: none, project identity remains unchanged.
- Planning: updated by linking to the existing project init interview plan.
