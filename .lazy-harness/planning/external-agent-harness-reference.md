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

## Evaluation harnesses and benchmarks

| Harness | Strengths to study | Lazy-harness relevance |
|---|---|---|
| SWE-bench harness | Docker reproducibility, patch apply, tests, grading, metrics, cache levels, parallel workers | model for deterministic framework eval: setup → apply → run → grade → report |
| SWE-bench Verified | human-filtered subset and leaderboard discipline | reference for curated regression/eval corpus quality |
| OpenHands benchmarks | multi-benchmark infra: SWE-bench, SWE-bench Pro, GAIA, Commit0, OpenAgentSafety, ProgramBench | reference for framework-wide evaluation matrix and safety benchmark integration |

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

## Implementation map

- Status: `planned`
- Primary files:
  - `.lazy-harness/planning/external-agent-harness-reference.md` — canonical reference landscape for external harness ideas.
  - `.lazy-harness/knowledge/candidates.jsonl` — discovery/candidate trail that first captured the online research summary.
  - `.lazy-harness/decisions/0024-ai-first-framework-redesign.md` — identity constraint: AI-first lifecycle enforcement and SearchProvider delegation.
  - `.lazy-harness/README.md` — high-level lazy-harness identity and source-of-truth entry points.
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
  - generated index key: `pending until implementation-index generator exists`
