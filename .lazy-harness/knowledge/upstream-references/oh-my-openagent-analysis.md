# Upstream reference — oh-my-openagent (omo) analysis

Status: snapshot
Source: https://github.com/code-yeongyu/oh-my-openagent (clone at /tmp/oh-my-openagent, branch=dev)
Captured: 2026-05-17
Purpose: ground truth reference for lazy-harness integration work. Not a record; a captured analysis of an external system we are mirroring.

## Why this file exists

We are integrating the oh-my-openagent (formerly oh-my-opencode, abbreviated omo) agent harness into lazy-harness so any host using lazy-harness benefits from the same multi-agent orchestration model.

The integration plan, decisions, and authoritative definitions live in:

- `.lazy-harness/decisions/0035-oh-my-opencode-personas-integration.md` (ADR)
- `.lazy-harness/ssot/agent-profiles.md` (SSOT — profile / category / model truth)
- `.lazy-harness/domain/agent-orchestration.md` (DDD — ubiquitous language for personas + 3-layer architecture)
- `.lazy-harness/spec/jcode-agent-profile-contract.md` (SDD — jcode profile merge contract we depend on)
- `.lazy-harness/planning/oh-my-opencode-integration-plan.md` (planning — phased rollout)

This file is the **raw extracted facts** so future sessions can resume without re-cloning and re-reading 11k lines of omo source.

## Agent inventory (11 built-ins)

omo registers 11 builtin agents, split by `mode`:

| Agent | Mode | Source file | Role |
|---|---|---|---|
| sisyphus | primary | src/agents/sisyphus/{default,claude-opus-4-7,gpt-5-4,gpt-5-5,gemini,kimi-k2-6}.ts | Main orchestrator. Plans, delegates, drives to completion. Never works alone when specialists available. |
| hephaestus | primary | src/agents/hephaestus/{agent,gpt,gpt-5-4,gpt-5-5,gpt-5-3-codex}.ts | Autonomous GPT-native deep worker. Goal-not-recipe execution. |
| prometheus | primary | src/agents/prometheus/{system-prompt,gpt,gemini,interview-mode,identity-constraints,plan-generation,plan-template,high-accuracy-mode,behavioral-summary}.ts | Strategic planner. Interview mode. READ-ONLY except `.omo/*.md`. |
| atlas | primary | src/agents/atlas/{agent,default,gpt,gemini,opus-4-7,kimi,*-prompt-sections,shared-prompt}.ts | Conductor. Reads plans. Distributes tasks. Verifies. Cannot write code. |
| oracle | subagent | src/agents/oracle.ts (591 lines, 4 model variants) | Read-only strategic technical advisor. Architecture / security / complex debugging. |
| librarian | subagent | src/agents/librarian.ts | Open-source codebase understanding. github, context7, websearch. Returns GitHub permalinks. |
| explore | subagent | src/agents/explore.ts | Contextual grep. Parallel fan-out. Returns absolute paths + intent analysis + next steps. |
| multimodal-looker | subagent | src/agents/multimodal-looker.ts | PDF/image/diagram extraction. Returns interpreted data, not raw bytes. |
| metis | subagent | src/agents/metis.ts (335 lines) | Pre-planning consultant. Catches gaps before Prometheus writes the plan. READ-ONLY. |
| momus | subagent | src/agents/momus.ts (449 lines, GPT/GPT-5.2/default variants) | Ruthless plan reviewer. OKAY/REJECT against clarity, verification, context, big-picture. |
| sisyphus-junior | subagent | src/agents/sisyphus-junior/ | The task executor. Cannot delegate. Disciplined todo tracking. lsp_diagnostics required before completion. |

Canonical assembly order for primary agents: `Sisyphus → Hephaestus → Prometheus → Atlas`.

## 3-layer orchestration architecture

```
Planning Layer (Human + Prometheus + Metis + Momus)
  User describes work
  → Prometheus interviews
  → Metis gap-analyzes (mandatory before plan write)
  → Prometheus writes .omo/plans/<name>.md
  → (optional high-accuracy) Momus loops until OKAY

Execution Layer (Atlas)
  /start-work
  → Atlas reads plan
  → Atlas analyzes tasks
  → Atlas accumulates wisdom (notepad)
  → Atlas delegates to workers
  → Atlas verifies results
  → Atlas final report

Worker Layer (specialists)
  Sisyphus-Junior (code writing, cannot delegate)
  Oracle (architecture consult)
  Explore (codebase grep)
  Librarian (docs/OSS)
  Category-routed (visual-engineering, deep, ultrabrain, ...)
```

## Category-based delegation (key innovation)

omo's most novel idea: subagent delegation does NOT take a model name. It takes a **category**, and the category maps to a model.

User-facing categories: `visual-engineering`, `artistry`, `ultrabrain`, `deep`, `quick`, `unspecified-low`, `unspecified-high`, `writing`, `quick-rust`, `quick-zig`, `git`.

Defaults defined in `src/tools/delegate-task/*-categories.ts` and `src/shared/model-requirements.ts`. Hosts can extend.

Regardless of category, dispatch goes through Sisyphus-Junior (the worker).

Two delegation calls in omo's tool API:

- `task(category="...")` → routes to Sisyphus-Junior with category-optimized model + skill stack
- `task(subagent_type="...")` → invokes that specific agent directly (oracle, explore, librarian, ...)
- These two inputs are mutually exclusive in one call.

## Working modes

| Mode | Trigger | Description |
|---|---|---|
| Simple prompt | normal chat | Sisyphus handles directly |
| Ultrawork / `ulw` | type `ultrawork` or `ulw` | Full automatic. Sisyphus explores, researches, implements, verifies until done. |
| Prometheus mode | Tab → select Prometheus, or `@plan "task"` | Interview-mode planning, no code touched |
| `/start-work` | after plan written | Atlas takes over and executes plan |

## Persona prompt construction pattern

Each persona is implemented as a TypeScript file (or directory) that:

1. Exports `create<Name>Agent(model, ...)` factory returning `AgentConfig`.
2. Exports `<NAME>_PROMPT_METADATA` with category/cost/promptAlias/triggers/useWhen/avoidWhen.
3. Branches on model family — for major personas (sisyphus, hephaestus, prometheus, atlas, oracle, momus) there are 4–6 model-specific prompt variants under the persona directory.
4. Uses `createAgentToolRestrictions([disallowed], [allowed])` or `createAgentToolAllowlist([...])` to fence what the persona can do.
5. Composes the system prompt from shared section builders in `src/agents/dynamic-agent-prompt-builder.ts` (keyTriggers, toolSelection, delegationTable, hardBlocks, antiPatterns, parallelDelegation, ...).

Prompt style:

- XML tags throughout: `<Role>`, `<context>`, `<expertise>`, `<decision_framework>`, `<output_verbosity_spec>`, `<response_structure>`, `<scope_discipline>`, `<tool_usage_rules>`, `<high_risk_self_check>`, `<delivery>`, `<formatting>`, `<uncertainty_and_ambiguity>`, `<long_context_handling>`.
- Hard constraints repeated as MUST / MUST NOT / NEVER.
- Explicit opener blacklist (no "Great question!", "Sure thing", "Got it", "Done -", "Happy to help").
- Anti-pattern sections list forbidden behaviors that the model is prone to.
- Sisyphus prompts in particular are long (443–545 lines per variant) and include a Phase 0 Intent Gate, intent verbalization map, todo discipline, parallel delegation guidance, anti-duplication block.

## Wisdom accumulation system

After each subagent task, Atlas extracts learnings into per-plan notepad:

```
.omo/notepads/{plan-name}/
├── learnings.md      Conventions, successful patterns
├── decisions.md      Architectural choices and rationales
├── issues.md         Problems, blockers, gotchas encountered
├── verification.md   Test results, validation outcomes
└── problems.md       Unresolved issues, technical debt
```

These are passed forward to every subsequent subagent so mistakes are not repeated.

## Hooks (selected)

omo ships ~60 lifecycle hooks. Key ones we should mirror in lazy-harness:

| Hook | Function |
|---|---|
| todo-continuation-enforcer | If todos incomplete, system reminder forces continuation |
| task-resume-info | Persist resume info across sessions |
| ralph-loop | Self-referential loop until done |
| keyword-detector | `ultrawork`, `ulw`, etc. trigger detection |
| intent-gate | Pre-classify intent before action |
| prometheus-md-only | Restrict Prometheus writes to `.omo/*.md` |
| no-sisyphus-gpt | Prevent assignment of weak models to sisyphus |
| no-hephaestus-non-gpt | Prevent assignment of non-GPT models to hephaestus |
| compaction-todo-preserver | Keep todos through context compaction |
| compaction-context-injector | Re-inject context after compaction |
| directory-agents-injector | Auto-inject AGENTS.md by directory |
| directory-readme-injector | Auto-inject README.md by directory |
| start-work | Bootstraps Atlas with selected plan |

## Team Mode (v4.0, optional, off by default)

Lead agent + up to 8 parallel members. tmux visualization. Dedicated `team_*` tools (`team_create`, `team_send_message`, `team_task_create`, `team_status`).

Team-eligible: sisyphus, atlas, sisyphus-junior.
Conditional: hephaestus.
Hard-rejected as team members: oracle, librarian, explore, multimodal-looker, metis, momus, prometheus (they are read-only / scoped tools).

## Files we have read in detail

- README.md — top-level
- docs/guide/overview.md — first 200 lines (architecture, agent list, model matching)
- docs/guide/orchestration.md — first 400 lines (full 3-layer architecture, planning loop, atlas conductor, category system, team mode)
- src/agents/builtin-agents.ts — agent registry / factory dispatch
- src/agents/oracle.ts — prompt patterns (default, GPT, GPT-5.2, GPT-5.5 variants)
- src/agents/sisyphus/index.ts + default.ts (partial) — sisyphus prompt builder pattern
- src/agents/metis.ts (head) — Metis pre-planning consultant identity
- src/agents/multimodal-looker.ts (full) — minimal persona example
- src/agents/explore.ts (head) — parallel-grep specialist with mandatory <analysis>/<results>/<next_steps> output structure
- src/agents/librarian.ts (head) — OSS lookup specialist with PHASE 0 classification
- src/agents/momus.ts (head) — plan reviewer with approval-bias
- src/agents/hephaestus/agent.ts — model-source dispatch for variant selection
- src/tools/delegate-task/constants.ts — plan-agent system prepend (mandatory context gathering + dependency graph + parallel execution + category/skill recommendation)

## Files referenced but not yet read

- src/agents/sisyphus/{claude-opus-4-7,gpt-5-5,kimi-k2-6}.ts — sisyphus per-model prompts (~440–545 lines each)
- src/agents/prometheus/{interview-mode,plan-template,plan-generation,system-prompt}.ts — Prometheus internals
- src/agents/atlas/* — Atlas conductor prompts
- src/agents/sisyphus-junior/ — junior worker
- src/agents/dynamic-agent-prompt-builder.ts — shared section composer (referenced from sisyphus/default.ts)
- src/shared/model-requirements.ts — fallback chains per category
- src/tools/delegate-task/*-categories.ts — category default definitions
- src/hooks/* — 60+ lifecycle hooks
- docs/reference/configuration.md, docs/reference/features.md — full config schema

These will be read per-phase as needed by the integration plan.

## Differences vs lazy-harness/jcode context

| Concern | omo | lazy-harness/jcode |
|---|---|---|
| Host runtime | opencode plugin | jcode binary |
| Plan files | `.omo/plans/*.md` | `.lazy-harness/planning/*` already exists |
| Notepad | `.omo/notepads/<plan>/` | new — propose `.lazy-harness/notepads/<plan>/` |
| Delegation tool | `task(...)` / `call_omo_agent(...)` | `Agent(subagent_type=...)` |
| Profile config | `oh-my-opencode.jsonc` per project | `~/.jcode/config.toml` + `<host>/.jcode/config.toml` with deep-merge (jcode commit 539c8f47, confirmed) |
| Hot reload | opencode plugin reload | jcode M19 hot-reload via force_reload_config |
| Category routing | first-class delegate-task tool with category arg | jcode `[agents.routing]` / `[agents.routes]` (existing structure per jcode answer #3) |
| Team Mode | opt-in v4.0 with team_* tools | jcode has no team_* tools; out of scope for initial integration |

## Discovery capture

- DDD: candidate — `domain/agent-orchestration.md` to be authored with persona definitions and 3-layer ubiquitous language.
- SDD: candidate — `spec/jcode-agent-profile-contract.md` documenting deep-merge contract we depend on; future spec for delegation tool surface.
- BDD: none — no UI flow yet; `ultrawork` / `/start-work` scenarios are planning candidates for later phases.
- TDD: none — no regression bug being fixed in this turn.
- ADR: candidate — `0035-oh-my-opencode-personas-integration.md` for the integration decision and trade-offs.
- SSOT: candidate �� `ssot/agent-profiles.md` as the single source of truth for personas, categories, model mappings.
- Planning: candidate — `planning/oh-my-opencode-integration-plan.md` for phased rollout.
