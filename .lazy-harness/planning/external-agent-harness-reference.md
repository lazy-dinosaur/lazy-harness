# External Agent Harness Reference Landscape

Status: accepted-reference
Layer: Planning
Created: 2026-05-18
Source: online research requested by user
Related ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
Related SSOT: `.lazy-harness/ssot/project-identity.md`

## Purpose

This record preserves well-known external agent/coding harnesses and agent orchestration frameworks that lazy-harness should consider when evolving its own lifecycle, adapter, evaluation, and verification design.

It is a reference landscape, not an adoption decision. Any future adoption still needs a separate ADR or implementation plan.

## Local identity baseline

Lazy-harness is an AI-first lifecycle enforcement framework. Its distinctive axis is not just running an agent loop, but enforcing record-first development across DDD, SDD, BDD, TDD, ADR, and SSOT with hooks and institutional memory.

External harnesses are therefore references for mechanisms, not replacements for lazy-harness identity.

## Coding agent and deep-agent harnesses

| Harness | Public positioning | Strengths to study | Lazy-harness relevance |
|---|---|---|---|
| OpenHands | Open-source AI software developer platform with SDK, CLI, local GUI, cloud, enterprise, and benchmark infra | sandbox/runtime, Docker isolation, SDK/CLI separation, evaluation infra, model-agnostic routing | reference for runtime boundary, remote execution, benchmark harness, cloud/self-host split |
| SWE-agent / mini-SWE-agent | Research coding agent for GitHub issue fixing and SWE-bench; mini-swe-agent supersedes with much smaller core | Agent-Computer Interface, benchmark-proven loop, YAML configurability, simple/hackable design | keep lazy-harness core small; make prompts/interfaces/evals explicit and configurable |
| Aider | Terminal pair-programming agent | repo map, git integration, auto-commit, lint/test auto-fix, broad language support | reference for codebase map, git-safe undo path, automatic validation after edits |
| Cline | IDE agent with file/terminal/browser tools and human approval | human-in-loop approvals, command/browser actions, diff view, checkpoints, MCP tool extension | reference for permission UX, checkpoint/restore, browser verification, user-visible trace |
| Roo Code | IDE agent/team style fork lineage with modes, checkpoints, MCP, subtask communication | custom modes, shadow-git checkpoints, multi-window/subtask flows | reference for mode-specific behavior, reversible experimentation, agent role UX |
| Codex CLI | OpenAI terminal coding agent, Rust CLI/TUI/exec, local workspace operations | headless exec mode, MCP client/server, zero-dependency binary path | reference for noninteractive automation and harness-as-tool composition |
| Claude Code | Proprietary terminal coding harness with hooks, skills, subagents, agent teams, MCP | lifecycle hooks, filesystem skills/rules, isolated subagents, agent-based hook verification | reference for hook surfaces and scoped subagent policies |
| OpenCode | Open-source terminal/TUI coding agent with provider flexibility | multi-provider/local model support, TUI, LSP, session management, custom commands | reference for provider abstraction, local privacy, LSP-backed context |
| Continue | Source-controlled AI checks in CI | repo-local markdown checks, PR status integration, suggested diffs | reference for `.lazy-harness` source-controlled AI validation specs |
| Open Harness | Harness-agnostic framework for deep agents | typed state, conditional activation, signal coordination, deterministic record/replay, cross-harness adapters | closest direct reference for future lazy-harness adapter/eval layer |

## Agent orchestration frameworks

| Framework | Strengths to study | Lazy-harness relevance |
|---|---|---|
| LangGraph | durable execution, stateful graphs, interrupts, memory, checkpoints, observability via LangSmith | possible model for long-running lifecycle state machine and resumable gates |
| AutoGen / AG2 | multi-agent conversation, group chat, nested/sequential chats, human-in-loop | reference for agent critique/review/coordination patterns |
| CrewAI | role-based crews and rapid multi-agent prototyping | reference for named lifecycle roles and reusable task teams |
| smolagents | lightweight code-first agents, minimal abstraction | reminder to avoid overbuilding and preserve small-core paths |
| OpenAI Agents SDK / Anthropic Agent SDK / Google ADK | provider-native orchestration, handoffs, guardrails, ecosystem integration | references for vendor-specific adapter capability surfaces, not canonical dependencies |
| Pydantic AI / Semantic Kernel / Mastra / Strands Agents | type-safe app agents, enterprise orchestration, TS-first or AWS-centered integrations | compare only when lazy-harness needs production app-agent embedding |

## Governance / workflow-enforcement frameworks (direct identity overlap)

Unlike the references above (mechanisms to study), this category overlaps lazy-harness's own identity: deterministic process enforcement, human-in-the-loop gates, and a recorded decision trail. Treat these as competitors to study, not runtimes to install inside the lazy-harness source repo.

| Framework | Public positioning | Strengths to study | Lazy-harness relevance |
|---|---|---|---|
| Babysitter (`@a5c-ai/babysitter-pi`, Pi integration Experimental v0.1.4, MIT) | Workflow orchestration/enforcement: event-sourced state, code- or NL-markdown-defined processes, quality gates before progression, human-in-the-loop approval at breakpoints, immutable decision journal, deterministic "hallucination-free self-orchestration"; thin Pi wrapper exposes `/babysit /call /plan /resume /doctor /yolo` slash aliases forwarding to `/skill:` (no custom tools/loop driver; orchestration lives in `@a5c-ai/babysitter-sdk`) | deterministic step-enforcement (block progression until a gate passes), event-sourced/replayable decision journal, explicit coded workflow definition, HITL breakpoints | closest direct competitor to lazy-harness enforcement; study its hard determinism but do not run it as a second governance layer in this source repo |
| gentle-pi (`gentle-pi`, MIT v0.10.2, Gentleman Programming; 24.2 MB extension+skill+theme+prompt) | Full "controlled development harness": el Gentleman senior-architect persona, Spec-Driven Development via OpenSpec (init/explore/proposal/spec/design/tasks/apply/verify/sync/archive; canonical `openspec/specs/` + change deltas with ADDED/MODIFIED/REMOVED), Strict TDD evidence (RED->GREEN->TRIANGULATE->REFACTOR), subagent orchestration (scout/context-builder/worker/reviewer + delegation triggers), skill-discovery registry (`.atl/skill-registry.md`), runtime safety guards, per-agent model/effort routing, memory via `gentle-engram` (Engram Go binary, SQLite+FTS5) | OpenSpec delta-spec model (ADDED/MODIFIED/REMOVED vs canonical), RED->GREEN->TRIANGULATE->REFACTOR evidence shape, delegation triggers (4+ files->scout, 2+ code files->worker, commit->fresh reviewer), skill registry, per-agent model routing | closest PARALLEL of lazy-harness's own thesis (requirements-first, artifacts-over-chat, TDD, review); NON-INSTALLABLE here: bundles `@heyhuynhgiabuu/pi-pretty` which registers `read` -> hard conflict with `pi-hashline-edit-pro` (pi fails to start); study only |

### lazy-harness vs Babysitter contrast

- Same goal (govern an agent), opposite trade-off:
  - lazy-harness = advisory/organic enforcement + LLM-as-semantic-authority + layered human-readable records; hard gate reserved for git pre-commit/pre-push `lazy test` (ADR 0016). Optimizes adaptability for open-ended development.
  - Babysitter = deterministic step/gate enforcement + code-defined process + event-sourced journal. Optimizes guaranteed compliance for repeatable, high-stakes workflows.
- What lazy-harness can learn (aligns with design ideas #2 deterministic record/replay, #3 typed lifecycle state, #10 observability): deterministic gate enforcement for the narrow set of already-hard gates (commit/push, irreversible ops), an event-sourced replayable decision journal, and explicit typed workflow state — without converting dev-time advisory hooks into rigid blocking gates.
- What to NOT adopt: a second governance grammar inside this repo; `/yolo` auto-approve (antithetical to the requirements-first/option-gate discipline, ADR 0019/0038); and slash-command collisions (`/resume` is Pi-native, `/plan` and `/doctor` are generic).
- Verdict: non-adopt as a runtime in the lazy-harness source repo; keep as a reference competitor. Any experiment belongs on a non-lazy-harness project. Best primary model: hybrid — lazy-harness flexible core, Babysitter-style determinism only on the narrow already-hard gates.

### lazy-harness vs gentle-pi contrast

- Closest parallel yet: gentle-pi independently implements lazy-harness's exact thesis (requirements-first, decisions-as-artifacts, TDD evidence, review discipline, skill discovery).
- Where gentle-pi is ahead (study targets): turnkey SDD/OpenSpec phase workflow with file-backed artifacts; RED->GREEN->TRIANGULATE->REFACTOR strict TDD evidence; ACTIVE runtime safety guards (blocks destructive shell, sensitive-path read/write); deterministic delegation triggers; per-agent model/effort routing; polished onboarding (preflight, status/doctor, persona).
- Where lazy-harness is ahead: depth of layered institutional memory (DDD/SDD/BDD/TDD/ADR/SSOT + knowledge graph + implementation maps) as git-tracked canonical SSOT; LLM-as-semantic-authority + map-first evidence retrieval; ownership/identity convergence and root-bound discipline; dogfood feedback loop.
- Honest read: gentle-pi is the stronger turnkey workflow PRODUCT (more enforced, more polished); lazy-harness is the deeper institutional-memory SUBSTRATE with more flexible LLM-judgment enforcement but weaker active runtime blocking. lazy-harness's real weakness vs gentle-pi = enforcement is advisory until git boundaries (ADR 0016).
- What to NOT adopt: full competing harness in this repo; the bundled-pi-pretty `read` conflict; persona/AGENTS-grammar injection. Verdict: non-adopt as a runtime; mine OpenSpec deltas, strict-TDD evidence, delegation triggers, and active safety guards as design references.

## Evaluation harnesses and benchmarks

| Harness | Strengths to study | Lazy-harness relevance |
|---|---|---|
| SWE-bench harness | Docker reproducibility, patch apply, tests, grading, metrics, cache levels, parallel workers | model for deterministic framework eval: setup → apply → run → grade → report |
| SWE-bench Verified | human-filtered subset and leaderboard discipline | reference for curated regression/eval corpus quality |
| OpenHands benchmarks | multi-benchmark infra: SWE-bench, SWE-bench Pro, GAIA, Commit0, OpenAgentSafety, ProgramBench | reference for framework-wide evaluation matrix and safety benchmark integration |

## Second-pass additions: product, control-plane, adapter, runtime, and eval harnesses

This section records additional well-known harnesses and products discovered after the initial landscape pass. These are especially relevant because they show how the market is separating into execution agents, local fleet supervisors, cloud autonomous agents, universal adapters, sandbox runtimes, and evaluation harnesses.

### Product / hosted coding agents

| Harness / product | Public positioning | Strengths to study | Lazy-harness relevance |
|---|---|---|---|
| Cursor Agent / Cursor CLI | AI-native IDE plus terminal agent, background/cloud agents, rules, memories, checkpoints, worktree mode, headless CLI | `.cursor/rules`, AGENTS.md compatibility, plan/ask modes, queued messages, automatic checkpoints, cloud handoff, `--worktree` isolation | reference for scoped rules, checkpoint UX, cloud handoff, and noninteractive CI use |
| Windsurf Cascade | IDE coding agent that tracks edits, terminal commands, browser/web context, rulebooks, deployment and PR review workflows | ambient workflow context, browser-to-IDE loop, saved rulebooks, team-scale curated knowledge | reference for passive context capture and team rule distribution |
| GitHub Copilot coding agent | GitHub-native async agent assignable from Issues, IDE, CLI, Slack/Teams, Jira/Linear; produces plans/PRs and uses security checks | issue-to-PR flow, unified agent mission control, context traveling from issue/chat, code/security/supply-chain checks before PR | reference for async task ownership, PR-first output, and security scan integration |
| Devin / Devin for Terminal | cloud autonomous software engineer plus local terminal agent; supports Ask/Agent modes, managed Devins, Playbooks, Secrets, Knowledge, Skills, Review/Auto-Fix | clear task suitability guidance, managed parallel sessions, cloud VM execution, review/auto-fix loop, repo-committed `SKILL.md` procedures | reference for task triage, cloud/local handoff, skills-as-reusable-procedures, review auto-fix loops |
| Replit Agent | browser/cloud app builder from prompt to deployed app; sets up project, tests, fixes, previews, publishes | integrated build-test-reflection loop, browser verification, one-click deploy, non-coder product flow | reference for end-to-end preview/deploy validation and agent self-test reports |
| Factory Droid | enterprise development agent CLI/TUI with spec mode, approvals, organizational knowledge, Jira/Notion/Slack/MCP context, review workflow | transparent proposed changes, spec mode for complex work, org knowledge and ticket integration, enterprise approvals | reference for spec-before-code and organizational context connectors |
| JetBrains Junie | JetBrains IDE/CLI/headless coding agent; BYOK, MCP, planning mode, custom subagents, skills/guidelines, live prompting | IDE semantic checks, live steering while running, `.junie/AGENTS.md`, plan mode, custom subagents | reference for IDE-backed validation and mid-run prompt steering |
| Amazon Q Developer / Kiro CLI lineage | AWS-focused agentic coding CLI and IDE agent; custom agent JSON format with prompt, MCP servers, tools, allowedTools, resources, hooks, model | first-class custom agent config schema and lifecycle hooks | reference for typed profile/config schema for lazy-harness agents |
| Amp | frontier coding agent focused on long responsive threads, plugins/hooks/tools/policy, polished agent UX | event-hook plugins, policy standardization, thread responsiveness | reference for plugin/event surfaces and UX responsiveness during long runs |

### Open-source / terminal coding agents not in first pass

| Harness | Public positioning | Strengths to study | Lazy-harness relevance |
|---|---|---|---|
| Gemini CLI | open-source terminal agent with Google Search grounding, file/shell/web tools, MCP, checkpointing, GEMINI.md context, headless JSON/stream modes, GitHub Action | massive open-source adoption, checkpoint/resume, structured output for automation, GitHub PR review/issue triage workflows | reference for open terminal agent automation and structured stream integration |
| Qwen Code | open-source terminal agent optimized for Qwen Coder but multi-provider; Skills, SubAgents, headless, IDE integrations, SDKs | Claude-Code-like open stack, local/custom provider support, subagent/skill primitives | reference for vendor-neutral skills/subagents and SDK embedding |
| Goose | open-source local general agent by Block/AAIF; desktop, CLI, API, MCP extensions, recipes, subagents, sandbox/security, ACP server | recipes as YAML workflows, 70+ MCP extensions, subagents to keep main context clean, ACP compatibility, adversary reviewer | reference for recipes, standards-based interoperability, security reviewer, and ACP/MCP duality |
| Crush | Charm terminal coding agent; multi-model, sessions, LSP context, MCP, hooks, skills, permissions, project initialization to AGENTS.md, logs | LSP-enhanced context, permission policy, hook support, agent skills standard, local/project config, attribution trailers | reference for LSP-backed context, config trust boundaries, permission prompts, and logs |
| Kilo Code / Codebuff / Auggie / Mistral Vibe / Kimi Code / Pi / Rovo Dev / Open Interpreter | ecosystem of provider- or vendor-specific coding CLIs referenced by orchestration tools | CLI diversity and fast-changing provider surface | reason to design lazy-harness adapter boundary without hardcoding one agent |

### Agent fleet / macro-orchestration harnesses

| Harness | Public positioning | Strengths to study | Lazy-harness relevance |
|---|---|---|---|
| Daintree | local desktop control plane for supervising 3-10 concurrent CLI agents in isolated git worktrees | worktree lifecycle, dev server management, context injection, agent state detection, review-first dashboard, resource profiles, MCP server exposing orchestration actions | very strong reference for local agent fleet supervision and worktree/resource governance |
| Emdash | open-source Agentic Development Environment; runs multiple coding agents in parallel locally or over SSH, each in its own worktree; supports 27 CLI providers and ticket/PR/CI workflows | provider-agnostic worktree isolation, remote SSH execution, ticket-to-agent dispatch, diff review, CI status, PR creation/merge | reference for ADE category and remote/local fleet workflow |
| AgentPipe | CLI/TUI multi-agent room that lets different CLI agents communicate with shared rooms, metrics, cost tracking, user participation | agent-to-agent room protocol, cost tracking, live participation | reference for swarm communication and telemetry design |
| AgentAPI | HTTP API wrapper for Claude Code, Goose, Aider, Gemini, Amp, Codex, Copilot, Cursor CLI, etc. | normalizes terminal agents behind `/messages`, `/message`, `/status`, `/events`; in-memory terminal emulator; SSE event stream; OpenAPI | strong reference for a universal adapter layer when native SDKs are missing |

### Sandbox / runtime infrastructure

| Runtime | Public positioning | Strengths to study | Lazy-harness relevance |
|---|---|---|---|
| E2B | secure Firecracker microVM sandboxes for coding agents, code execution, desktop/computer use, long sessions | isolated untrusted code execution, real tools, internet, templates, enterprise BYOC/on-prem | reference for safe test/eval execution outside the developer machine |
| Daytona | open-source secure elastic sandbox runtime for AI-generated code and agent workflows; full composable computers, snapshots, persistence, APIs/SDKs | fast sandbox startup, stateful snapshots, preview links, full filesystem/process control, self-host/hybrid | reference for reproducible eval environments and snapshot-based checkpoints |
| Morph Cloud / Infinibranch | cloud computers/devboxes with snapshot/replicate/autoscale/debug/deploy for agents | fast branching runtime snapshots and parallel code execution | reference for scalable parallel eval and branch-per-agent runtime design |

### Evaluation / reliability harnesses beyond SWE-bench

| Harness | Public positioning | Strengths to study | Lazy-harness relevance |
|---|---|---|---|
| Inspect AI | UK AISI frontier AI eval framework with 200+ evals, agent evals, multi-agent primitives, external agent execution, sandboxing, logs/viewer | Task/Dataset/Solver/Scorer model, sandbox providers, agent bridge, log viewer, compaction, concurrency, limits | strongest reference for lazy-harness eval architecture and trace/log viewer design |
| HAL: Holistic Agent Leaderboard | Princeton framework-agnostic agent evaluation harness and cost-aware leaderboard across multiple benchmarks | cost-performance frontier, reliability dashboard, trace logging, benchmark/agent modularity | reference for evaluating reliability beyond raw pass rate: consistency, robustness, safety, self-awareness |
| DeepEval | pytest-native LLM/agent eval framework with traces, CI integration, LLM-as-judge metrics, synthetic goldens | agent trace scoring, local test runner, regression loop, span-level reasons | reference for lazy-harness source-controlled AI checks and agent regression tests |
| Ragas | systematic eval loops for LLM applications with experiments, metrics, datasets, RAG metrics | experiments-first eval loop and custom metrics | reference mainly if lazy-harness evaluates knowledge/RAG/context retrieval quality |
| DSPy | programming-not-prompting framework with optimizers for prompts/weights and modular LM programs | measurable optimization of prompts/agent modules | reference for future prompt/hook optimization, not direct harness replacement |
| AgentBench / WebArena / OSWorld / Mind2Web / tau-bench / Terminal-Bench / BFCL / AppWorld | benchmark families for tool-use, browser, OS, terminal, workflow, and function-calling agents | environment-specific eval tasks | candidate benchmark inputs for lazy-harness adapter/replay validation |

### Updated ecosystem taxonomy

| Layer | Examples | What they own | What lazy-harness should learn |
|---|---|---|---|
| Execution agent | Claude Code, Codex CLI, Gemini CLI, Qwen Code, Crush, Goose, Amp, Aider, OpenCode | one agent session and its tools | adapter protocol, permissions, logs, context files |
| IDE pair agent | Cursor, Windsurf, Junie, Amazon Q, GitHub Copilot | IDE-integrated planning/edit/test loop | checkpoints, rules, semantic validation, PR/review loop |
| Cloud autonomous engineer | Devin, Factory Droid cloud, GitHub Copilot coding agent, Replit Agent | long-running VM/cloud task and PR/deploy outcome | async ownership, skills/playbooks, review/fix, deploy validation |
| Agent fleet control plane | Daintree, Emdash, AgentPipe | many agent sessions, worktrees, status, review/merge | worktree isolation, dashboard, resource governance, swarm telemetry |
| Universal adapter | AgentAPI, ACP/A2A-style protocols | common API over heterogeneous CLIs | future HarnessAdapter implementation |
| Runtime/sandbox | E2B, Daytona, Morph Cloud | isolated compute and snapshots | reproducible eval, safe execution, parallel runs |
| Eval harness | Inspect, HAL, DeepEval, SWE-bench, Ragas | datasets, solvers, scorers, traces, metrics | lazy-harness self-eval and record/replay grading |

## Candidate design ideas for lazy-harness

1. **Harness adapter boundary**: model Claude Code, Codex, Jcode, OpenCode, and future harnesses as adapters. Lazy-harness owns lifecycle/records; adapters provide tool execution semantics.
2. **Deterministic record/replay evals**: record agent runs, hook decisions, tool calls, record mutations, and final outcomes; replay against changed prompts/hooks where possible.
3. **Typed lifecycle workflow state**: represent DDD/SDD/BDD/TDD/ADR/SSOT gate state, option gates, and discovery captures as explicit state objects.
4. **Shadow checkpoints**: use git or shadow-git snapshots to support reversible agent experimentation without polluting user history.
5. **Source-controlled AI checks**: define repo-local AI review/check specs that can run in CI or pre-merge, similar to Continue checks but using lazy-harness layers.
6. **Sandboxed self-eval**: use Docker/containerized fixtures for reproducible framework validation beyond current self-test/doctor smoke checks.
7. **Benchmark matrix**: separate harness correctness, agent behavior compliance, record quality, eval cost, latency, and user-interruption count.
8. **Mode/role templates**: learn from Cline/Roo/CrewAI/Claude subagents but keep roles grounded in lazy-harness lifecycle layers.
9. **Small-core discipline**: preserve mini-SWE-agent/smolagents lesson that a minimal core plus strong records/evals can outperform a large rigid framework.
10. **Observability first**: log hook events, gates, skipped steps, option gates, and replayable traces as first-class artifacts.
11. **Agent fleet supervision**: Daintree/Emdash show that worktree isolation, resource governance, and review dashboards become first-class when supervising several agents.
12. **Universal terminal adapter**: AgentAPI shows a pragmatic bridge over heterogeneous CLIs before standards or SDKs converge.
13. **Sandbox-first eval**: E2B/Daytona/Morph show that runtime snapshotting and safe execution can become part of the harness, not an afterthought.
14. **Reliability metrics beyond pass/fail**: Inspect/HAL/DeepEval show the need for cost, trace, consistency, robustness, and span-level failure reasons.
15. **Skills/rules convergence**: Devin, Cursor, Crush, Goose, Qwen Code, Gemini CLI, and Junie all converge on repo-local context/rules/skills files, validating lazy-harness's record-first direction while warning against one giant instruction file.

## Non-goals and cautions

- Do not copy a general agent framework identity. Lazy-harness remains record-first lifecycle enforcement.
- Do not add custom semantic search algorithms merely because other tools have indexing. ADR 0024 keeps SearchProvider delegation as the path.
- Do not introduce vendor lock-in at the framework layer.
- Do not treat benchmark score as the only quality measure. Lazy-harness quality also includes institutional memory, user correction convergence, and regression prevention.
- Do not adopt external dependencies without an ADR covering cost, portability, local/offline behavior, security, and host impact.

## Follow-up backlog

- Draft an ADR for a `HarnessAdapter` interface only if/when multiple harness backends become active targets.
- Create a replay/eval spike that records one lazy-harness turn and replays gate decisions deterministically.
- Compare shadow-git checkpoints versus normal git worktree commits for lazy-harness task safety.
- Prototype a source-controlled AI check spec under `.lazy-harness/spec` or `.lazy-harness/tests` after layer ownership is decided.
- Extend doctor/self-test metrics to include trace quality and record/replay readiness.
- Study Daintree/Emdash for a local worktree/fleet supervision model before expanding lazy-harness swarm workflows.
- Study AgentAPI/ACP/A2A-style protocol boundaries before implementing a universal adapter.
- Study Inspect AI's Task/Dataset/Solver/Scorer and log viewer model before designing lazy-harness record/replay evals.
- Study DeepEval's pytest-native agent trace scoring before adding source-controlled AI checks.
- Study E2B/Daytona snapshot semantics before adding sandbox-backed framework tests.

## Implementation map

- Status: `planned`
- Primary files:
  - `.lazy-harness/planning/external-agent-harness-reference.md` — canonical reference landscape for external harness ideas.
  - `.lazy-harness/knowledge/candidates.jsonl` — discovery/candidate trail that first captured the online research summary.
  - `.lazy-harness/decisions/0024-ai-first-framework-redesign.md` — identity constraint: AI-first lifecycle enforcement and SearchProvider delegation.
  - `.lazy-harness/README.md` — high-level lazy-harness identity and source-of-truth entry points.
  - second-pass external references: Daintree, Emdash, AgentAPI, Gemini CLI, Qwen Code, Goose, Crush, Cursor, Devin, Replit Agent, Factory Droid, Junie, Amazon Q/Kiro, E2B, Daytona, Morph Cloud, Inspect AI, HAL, DeepEval, Ragas, DSPy, Babysitter (`@a5c-ai/babysitter-pi`), gentle-pi (`gentle-pi`).
- Key symbols:
  - none; this is a planning/reference record, not an implemented code path.
- Flow:
  1. Online research identifies external harness mechanisms.
  2. This planning record preserves mechanisms as references and cautions.
  3. Future concrete adoption must graduate into ADR/spec/test records before implementation.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` — validates framework records and JSONL after this reference is added.
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke` — smoke-validates framework health.
- Ownership boundaries:
  - Owner/upstream: external projects remain upstream references only.
  - This host may change: lazy-harness records, plans, adapters, eval tooling, and hooks after explicit ADR/spec work.
  - This host must not change without explicit confirmation: vendor-specific assumptions, external benchmark claims, or dependency adoption.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
  - SSOT: `.lazy-harness/ssot/project-identity.md`
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
- Machine index:
  - graph ids: `kg_external_agent_harness_reference_doc`, `kg_external_agent_harness_reference_decided_by_adr0024`, `kg_external_agent_harness_reference_candidate_source`
  - second-pass graph ids: `kg_external_agent_harness_reference_second_pass`, `kg_external_agent_harness_reference_eval_runtime_axis`
  - generated index key: `pending until implementation-index generator exists`
