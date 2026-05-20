# Project Init Interview Spec

Date: 2026-05-12
Status: planned as a skill-first Project Profile flow; full standalone CLI comes later
Related SDD: `.lazy-harness/spec/platform/project-profile.md`
Purpose: create a new project's lazy-harness SSOT through structured interview, not silent defaults

> 상위 목표 (north-star): [`./north-star-accuracy-and-no-regression.md`](./north-star-accuracy-and-no-regression.md)
> 이 spec 은 north-star 의 "Map-aware Reference Resolver" + "Project Profile Skill" 토대를 만드는 하위 plan.

## 1. Core idea

Project Init / Project Profile must not only create folders. It must interview the user and generate a durable project profile that defines how this project should be built, tested, designed, and evolved.

2026-05-20 clarification: Project Profile means the host architecture/structure/goal/pattern profile. It is not the same as workflow execution presets such as fast/normal/strict/audit-only. The profile should decide or create the host's architectural records when missing, then guide subsequent development.

The output is a project-local SSOT that future agents can read before touching code.

Before implementing any feature, the agent must use the project profile to find the correct map path first. A feature should not start from a guessed file edit. It should start from the relevant DDD / SDD / BDD / TDD / ADR / SSOT maps, then follow those maps into code, tests, and records.

```text
feature request or code change
→ project profile
→ relevant maps
→ existing records/specs/tests
→ gap/conflict/missing/unclear check
→ side-effect / regression / domain-invariant check
→ structured question if needed
→ implementation + record updates
→ validation
```

The map structure is therefore part of the project contract, not just documentation.

Correct development also requires every code change to be checked against:

1. **Side effects** — which nearby flows, components, APIs, data paths, or user journeys can be affected?
2. **Regression risk** — which past bugs, tests, BDD scenarios, or ADR constraints can be broken again?
3. **Domain invariants** — does the change violate DDD vocabulary, bounded-context rules, business policies, or protected assumptions?

If the framework cannot confidently answer these from maps/records/tests, it must create a structured question or block completion. Silent "looks fine" is not acceptable.

```text
project purpose
→ optional document-resource ingestion outputs
→ stack choices
→ test strategy
→ architecture style
→ filesystem/folder layout
→ frontend design system
→ backend boundaries
→ domain/spec/behavior/test seed files
→ validation commands
```

## 2. Interview sections

### 0. Optional document-resource ingestion handoff

Project Profile creation and Document Resource Ingestion are separate capabilities.

If `.lazy-harness/project/document-intake.xml` or equivalent ingestion outputs already exist, the Project Profile flow may use them as evidence. If important outside docs exist but have not been ingested, Project Profile should offer to run the separate Document Resource Ingestion flow first, or proceed with interview-only profile creation.

Ask:

1. Should Project Profile use existing document-ingestion outputs?
2. If outside docs have not been ingested, run the separate document ingestion flow first, or continue with interview-only setup?
3. Are any ingestion outputs authoritative enough to seed project profile decisions, or should they remain candidates?

Outputs:

- references from Project Profile records to ingestion output IDs when used
- option-gate answer if document ingestion is deferred
- no direct document scanning/reproduction inside Project Profile itself

### A. Project purpose and constraints

Ask:

1. What is the project trying to achieve?
2. Who are the target users?
3. Is this a prototype, internal tool, production SaaS, library, CLI, desktop app, mobile app, or mixed system?
4. What must not be compromised? speed, correctness, UX, cost, privacy, portability, accessibility, etc.
5. Are there compliance/security constraints?

Outputs:

- `.lazy-harness/project/profile.xml`
- `.lazy-harness/intent/active/project-init.xml`
- initial risk tier and confidence policy

### B. Stack selection

Ask current stack if known, otherwise recommend options.

Frontend options examples:

- React + Vite
- Next.js
- Electron + React
- React Native
- SvelteKit
- none/backend-only

Backend options examples:

- Node/Bun + Hono/Fastify/Express
- NestJS
- tRPC
- Python FastAPI
- Go
- none/frontend-only

Database/data options:

- PostgreSQL + Prisma/Drizzle
- SQLite
- Supabase/Firebase as external integration
- file-based/local-first
- none

Outputs:

- `.lazy-harness/project/stack.xml`
- `.lazy-harness/spec/platform/stack-decisions.xml`
- decision log entry for stack choices

### C. Test strategy

Ask:

1. Which test runner exists now?
2. If no tests exist, should lazy-harness recommend Vitest for unit/integration?
3. Should UI/e2e use Playwright?
4. What command proves correctness before commit/push?
5. What is allowed to skip, and what requires explicit defer decision?

Recommended default:

```text
unit/component: Vitest
browser/e2e: Playwright when UI exists
typecheck: project native typecheck command
lint: project native lint command
lazy harness gate: lazy:test + project test command
```

Outputs:

- `.lazy-harness/tests/test-strategy.xml`
- package script recommendations
- affected test routing config, for example `<affectedTestRouting command="bun run test:run {tests}" />`
- initial `lazy:test:affected` policy

### D. Filesystem and folder structure

Ask:

1. Monorepo or single package?
2. Source root candidates: `src/`, `apps/*`, `packages/*`, `src/renderer/src`, etc.
3. Where do tests live?
4. Where do generated files live?
5. What directories are forbidden for agents to edit?

Outputs:

- `.lazy-harness/project/filesystem.xml`
- detector include/exclude path config
- generated/runtime artifact policy

### D2. Map-first feature navigation

Ask:

1. Which map is the entry point for a feature request?
2. How do DDD terms map to SDD contracts and BDD scenarios?
3. How do BDD scenarios map to TDD/affected tests?
4. How do ADRs link to long-lived architecture or policy decisions?
5. Which map gaps should block implementation vs create follow-up questions?
6. Which records define side-effect boundaries for a feature area?
7. Which regression history or protected BDD/TDD cases must be checked before editing this area?
8. Which domain invariants must never be violated without an ADR/decision?

Outputs:

- `.lazy-harness/project/feature-navigation.xml`
- map lookup order for future agents
- cross-layer relation policy
- missing-map force gate policy
- side-effect and regression lookup policy
- domain-invariant validation policy

### E. Frontend design system and system design

Ask:

1. Existing design system? Tailwind, shadcn/ui, MUI, custom tokens, Figma, none?
2. Component policy: atomic, feature-local, shared components, design tokens?
3. Accessibility baseline?
4. Theme strategy: light/dark, density, typography, spacing scale?
5. State management: local state, Zustand, Redux, React Query, TanStack Query, URL state?
6. Routing/layout conventions?

Outputs:

- `.lazy-harness/spec/frontend/design-system.xml`
- `.lazy-harness/spec/frontend/component-policy.xml`
- `.lazy-harness/behavior/ui-accessibility-baseline.xml`

### F. Backend architecture

Ask:

1. Architecture style: layered, hexagonal/ports-adapters, clean architecture, vertical slice, simple CRUD?
2. Domain boundaries and bounded contexts?
3. API style: REST, RPC, GraphQL, tRPC, events?
4. Validation policy: Zod/class-validator/manual?
5. Persistence boundary: repositories, direct ORM, service layer?
6. Error handling and logging policy?
7. Auth/authz model?

Recommended decision rule:

- Small CRUD/internal tool: simple layered or vertical slice.
- Domain-heavy system: hexagonal/ports-adapters.
- UI-heavy product: vertical slice with shared domain vocabulary.
- Library/CLI: module boundary + contract tests.

Outputs:

- `.lazy-harness/domain/bounded-contexts.xml`
- `.lazy-harness/spec/backend/architecture.xml`
- `.lazy-harness/spec/backend/api-contract-policy.xml`
- `.lazy-harness/spec/backend/persistence-policy.xml`

### G. Agent operating rules

Ask:

1. Can agents auto-refactor?
2. Can agents add dependencies?
3. What requires human confirmation?
4. What files are high-risk?
5. What validation must run before commit/push?

Outputs:

- `.lazy-harness/project/agent-policy.xml`
- `.lazy-harness/hooks/policy.xml`
- `.jcode/AGENTS.md` or equivalent wrapper instructions only if host allows it

## 3. CLI shape

Long-term standalone repo target command:

```bash
lazy-harness init
lazy-harness init --profile web-app
lazy-harness init --non-interactive --answers answers.json
lazy-harness init --dry-run
lazy-harness init --apply
```

Inside this incubating repo, implementation should start as a skill-first flow before a full CLI:

```bash
bun .lazy-harness/scripts/project-profile.ts --mode inspect
bun .lazy-harness/scripts/project-profile.ts --mode interview --dry-run
bun .lazy-harness/scripts/project-profile.ts --mode interview --apply

# later CLI-compatible implementation shape
bun .lazy-harness/scripts/project-init-interview.ts --mode interview
bun .lazy-harness/scripts/project-init-interview.ts --answers answers.json --dry-run
bun .lazy-harness/scripts/project-init-interview.ts --answers answers.json --apply
```

## 4. Output contract

Every init run must produce:

1. Structured question transcript.
2. Decision log entries for non-default choices.
3. Optional references to Document Resource Ingestion outputs when used.
4. Project profile XML.
5. Test strategy XML.
6. Filesystem policy XML.
7. Architecture policy XML.
8. Design-system policy XML when frontend exists.
9. Validation command registry.
10. Handoff entry summarizing how future agents should work.

## 5. No silent defaults

If a project has no tests, no design system, or no backend architecture, lazy-harness may recommend defaults but must ask:

- Accept recommended default.
- Specify existing/custom approach.
- Skip/defer with explicit reason.
- Provide custom answer.

This mirrors the affected-test gate's A/B/C/D strategy. Affected test execution must use this project-owned strategy or repo-native package scripts, never a hardcoded framework runner command.

## 6. Relationship to standalone extraction

This feature should first be exercised as a framework skill in the host-project incubation branch. The full CLI belongs in the standalone `lazy-harness` repository after the skill/profile workflow is proven by real host-project pilots.

## 7. Dogfooding deployment note

2026-05-20: `/lazy-project-profile` was promoted to a framework-owned Jcode wrapper skill generated by `.lazy-harness/scripts/jcode-wiring.ts` and declared beta in `.lazy-harness/manifests/skills.xml`.

The wrapper was synced to `/home/lazydino/dev/medivance` with `lazy-sync --force`; `.jcode/skills/lazy-project-profile/SKILL.md` was created and host `doctor --profile smoke --scope host` passed. Full host `lazy test` is blocked by existing Medivance health issues unrelated to the wrapper: missing `VITE_DIRECT_URL` for Prisma generate and existing Unicode replacement-character findings.
