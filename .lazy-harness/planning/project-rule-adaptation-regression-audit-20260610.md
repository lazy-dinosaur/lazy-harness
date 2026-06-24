# Project Rule Adaptation Regression Audit — 2026-06-10

Status: superseded-by-20260624-repair (diagnosis retained as history)
Layer: Planning
Date: 2026-06-10
Superseded-by: `.lazy-harness/planning/operating-rule-storage-apply-repair-20260624.md`
Supersession note: the 6-phase repair direction below pre-dates ADR 0044/0046. The current-structure repair (apply-audit default-level firing + storage-correctness helper, no hard gate, R3 excluded) lives in the 2026-06-24 plan. This record is kept for its diagnosis and history.
Related SSOT: `.lazy-harness/ssot/rule-lifecycle.md`
Related SSOT: `.lazy-harness/ssot/rule-sources.md`
Related SDD: `.lazy-harness/spec/platform/project-rule-router.md`
Related SDD: `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
Related SDD: `.lazy-harness/spec/platform/guidance-ladder.md`
Related SDD: `.lazy-harness/spec/platform/capability-resolution.md`
Related ADR: `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md`
Related ADR: `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md`
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related TDD: `.lazy-harness/tests/project-rule-memory-routing.md`
Related TDD: `.lazy-harness/tests/rule-binding-pr-body-guard.md`
Related TDD: `.lazy-harness/tests/guidance-ladder-hard-stop-promotion.md`

## Trigger

User correction on 2026-06-10:

```text
우리의 목표가 정보저장만이 아니야 프로젝트마다 다른 규칙들이 생기면 거기에 유연하게 변형될수 있는게 목표인데 왜이렇게됬지?
```

The correction was made after downstream dogfood showed that a host-specific worktree/dev-instance rule could be stored or documented yet still not shape agent behavior strongly enough at action time.

## Finding summary

The regression is not simply that project rules cannot be stored. Project rule placement/storage still exists.

The lost or weakened behavior is the **adaptation path**:

```text
confirmed project rule
→ canonical record
→ machine-understandable applicability/action metadata
→ pre-action/pre-response retrieval
→ agent behavior changes
→ audit/escalation/hard-stop when misses repeat
```

Current lazy-harness protects the first and last-adjacent parts better than the middle:

- project rule placement is gated,
- Jcode memory misuse is blocked,
- broad hard stops are discouraged,
- capability registry can store/resolve capabilities,
- but normal turns mostly receive a static “search records” reminder, not selected project-specific rules/capabilities,
- capability warning/default/block integration is intentionally not implemented yet,
- old rule-binding enforcement was demoted to a no-op shim,
- runtime/dev-instance action-boundary lookup was removed during hard-gate revert.

## Historical evidence

### 1. `.jcode` project notes became pointer-only

Commit: `3fb22a1 Make Jcode project rules pointer-only`

Changed `jcode-wiring.ts` so `.jcode/harness/20-project-rules.md` is generated as pointer-only and any user-owned content is archived to:

```text
.jcode/archive/20-project-rules.pre-pointer-only-migration.md
```

Reasonable part: `.jcode` should not be the canonical team/project rule store.

Side effect: the old obvious local place where agents looked for project workflow rules became intentionally empty/pointer-only, increasing reliance on `.lazy-harness` record discovery and lifecycle surfacing.

### 2. Executable rule lifecycle was originally stronger

Commit: `684b390 Add rule lifecycle action-boundary guard`

Original SSOT stated:

```text
A lazy-harness rule is not fully installed just because it is written in a record.
```

Original lifecycle states included:

- `captured`
- `bound`
- `enforced`
- `advisory-only`
- `retired`

Original contract also defined `.lazy-harness/ssot/rule-bindings.json` as canonical machine-readable binding metadata for host/framework rules.

Original action-boundary helper:

- loaded `.lazy-harness/ssot/rule-bindings.json` and `.lazy-harness/generated/rule-bindings.json`,
- created a default PR body binding if `.lazy-harness/ssot/pr-description-format.md` existed,
- was called from generated `.jcode/hooks/check-bash.sh`,
- denied malformed `gh pr create/edit` commands before mutation.

### 3. Runtime/dev-instance lookup guard briefly existed and was removed

Commit: `9411cbd Revert hard gates and plan organic hybrid guidance`

The reverted helper had runtime command detection for commands like:

- `bun run dev*`
- `npm run dev*`
- `pnpm run dev*`
- `yarn dev*`
- `next dev`
- `vite`

It also searched runtime/dogfood/dev-instance records and required recent record lookup before starting or inspecting dev/test instances.

This is directly relevant to the downstream worktree/dev-instance miss: the exact class of action-time guard was removed.

### 4. Tool-attached project policy was fully deprecated

Commit: `4ab9a5f Deprecate tool-attached rule policy`

`check-rule-action-boundary.py` became a no-op compatibility shim. The generated bash hook became destructive shell safety only.

Current `.jcode/hooks/check-bash.sh` blocks only generic destructive shell patterns such as `rm -rf /`, `dd of=/dev/...`, `mkfs /dev/...`.

### 5. Organic replacement did not fully replace adaptation

ADR 0041 adopted:

```text
record creation/update
→ record indexing/digest metadata
→ framework-structured direct-search prompt before response/plan
→ LLM/searcher root-bound search/read evidence
→ response audit verifies use/capture
→ records evolve again
```

But current `on-message-received.sh` is deliberately static transport:

- no semantic backend,
- no user-text classification,
- no relevant-record query,
- no concrete project rule/capability injection,
- only an inventory/search protocol reminder and search-debt journal.

That means the replacement system often tells the model “go search” instead of directly surfacing “this host has this worktree/dev-instance rule”.

### 6. Capability Registry was the likely flexible adaptation path, but it stopped at non-blocking phases

ADR 0040 and `.lazy-harness/ssot/capability-registry.md` introduced project-specific capabilities with independent `kind` and `level`:

- `discover`
- `recommend`
- `default`
- `warn`
- `block`

This is closer to the user’s intended model: project-specific scripts/skills/prompts/hooks/commands/validations can adapt agent behavior without forcing every rule into a hook.

However Phase 1/2 explicitly says:

```text
No hook is added by Phase 1/2. Warn/block boundary enforcement is a later phase.
```

The plan later records a user-confirmed target for automatic accumulation/confirmation/promotion, but that follow-up has not become an active integrated behavior path.

## Current gaps / wrong turns

1. **Storage and adaptation were split but not reconnected.**
   - Project Rule Router handles “where do we store this?”
   - Capability Registry handles “what project-specific affordance exists?”
   - Guidance Ladder handles “when can we hard-stop?”
   - No complete bridge currently turns host rules/capabilities into action-time defaults/warnings.

2. **The old `captured → bound → enforced` path was deprecated without an equivalent `captured → surfaced/resolved → adapted` path.**
   - ADR 0041 kept the problem statement but weakened the mechanism to static search reminders plus audits.

3. **`.jcode` pointer-only migration removed local rule bodies before record retrieval had enough precision.**
   - This was correct for canonical storage, but it increased the need for strong record discovery, aliases, and capability resolution.

4. **`rule-bindings.json` disappeared as an active canonical binding store.**
   - Current rule-lifecycle says old machine-readable bindings are historical/compatibility metadata.
   - There is no replacement action-binding schema that maps host rules to commands/tool intents at the same fidelity.

5. **Capability Registry is host-owned and allowed to be empty.**
   - This is correct for portability, but downstream hosts may have no registered project capabilities even when records contain operational rules.

6. **Capability candidate accumulation/promotion is still planning, not active default.**
   - The 2026-05-26 plan records that automatic evidence accumulation and promotion is the target, but current implementation is read-only/non-blocking.

7. **Response audit mostly catches record/search debt, not semantic rule application.**
   - It can audit surfaced PR digest examples and generic search/read evidence.
   - It does not generally know that `git worktree add` should have been replaced by `bun run wt new` unless a surfaced digest/capability/action binding exists.

8. **Hard-stop policy is too binary for operational rules.**
   - The framework avoids broad hard stops, correctly.
   - But there is no middle layer that says “warn/default this command based on host capability/rule” before hard-stop promotion.

9. **DevOps/Ops workflow rules have no first-class category.**
   - They are currently forced into SSOT/SDD/TDD/Capability records.
   - For now this can be modeled as SSOT rule + command capability, but the taxonomy gap contributed to rules landing in `spec` only.

10. **Downstream discoverability gaps become framework adaptation gaps.**
    - Korean aliases, graph-row-to-record promotion, missing/freshness of generated indexes, and empty capability registries can all prevent the framework from adapting behavior in real host use.

## Recommended repair direction

Do not revert to broad tool-attached hard gates.

Instead restore the missing adaptation path as a narrow, record-driven bridge:

```text
Host rule SSOT / SDD / ADR
→ optional capability entry or binding metadata
→ lazy map / graph / capability resolver can surface it
→ message.received injects selected project-relevant rules/capabilities or asks LLM to resolve them with a concrete command
→ pre-action guard can warn/default/block based on level
→ response audit records misses and promotes only repeated/high-risk boundaries
```

Concrete phases:

1. **Define `Project Rule Application` SDD**
   - Inputs: rule records, `Rule digest`, capabilities, optional bindings.
   - Outputs: discover/recommend/default/warn/block behavior.
   - Must keep storage separate from action adaptation, but connect them.

2. **Revive machine-readable applicability without reviving tool sprawl**
   - Either extend `capabilities.json` or introduce a successor to `rule-bindings.json`.
   - Prefer capability registry because it already supports kind/level/action labels.

3. **Register downstream operational rules as capabilities**
   - Example: worktree/dev-instance standard commands.
   - Level could start as `default` or `warn`, not necessarily `block`.

4. **Improve pre-response surfacing**
   - Static reminder alone is insufficient.
   - Add a safe resolver step that surfaces compact candidate capabilities/rules by exact command/action labels, record aliases, and graph paths, without treating it as semantic authority.

5. **Add middle-rung pre-action warning/default behavior**
   - For a command with a known host default capability, emit guidance before running raw alternatives.
   - Promote to hard-stop only through Guidance Ladder criteria.

6. **Add tests from the downstream failure**
   - Korean `워크트리`/`인스턴스` discoverability.
   - graph row hit promotes source record candidate.
   - missing/stale generated indexes are detected by doctor/lazy test.
   - raw `git worktree add` when a host declares `bun run wt new` as default/warn capability.
   - raw `bun run dev` when a host declares `bun run dev:instance` as default/warn capability.

## Rule placement

- Rule: Lazy-harness project rules are not complete when merely stored; framework-global behavior must support project-specific adaptation through canonical records plus capability/binding/resolution/audit layers.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/project-rule-adaptation-regression-audit-20260610.md`
- Why not AGENTS.md: this is an architecture/regression audit and repair direction, not a short universal prompt grammar rule yet.
- Why not `.jcode`: the issue is shared framework behavior for all hosts, not local/private Jcode wiring.
- Confirmation: user-confirmed

## Discovery capture

- DDD: no domain/business vocabulary impact.
- SDD: candidate `Project Rule Application` SDD; update `capability-resolution`, `project-rule-router`, and possibly `guidance-ladder`.
- BDD: agent-visible behavior should change from passive search reminder to project-specific default/warn guidance.
- TDD: add regressions for worktree/dev-instance command substitution and multilingual discovery.
- ADR: likely successor or amendment to ADR 0041 is needed because the current organic replacement under-specifies adaptive application.
- SSOT: `rule-lifecycle`, `rule-sources`, and `capability-registry` need alignment.
- Planning: this audit is the current entrypoint.

## Implementation map

- Status: `audit-created`
- Evidence files:
  - `.lazy-harness/ssot/rule-lifecycle.md`
  - `.lazy-harness/spec/platform/project-rule-router.md`
  - `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
  - `.lazy-harness/spec/platform/guidance-ladder.md`
  - `.lazy-harness/spec/platform/capability-resolution.md`
  - `.lazy-harness/ssot/capability-registry.md`
  - `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md`
  - `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md`
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh`
  - `.lazy-harness/hooks/lifecycle/helpers/check-rule-action-boundary.py`
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py`
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh`
  - `.lazy-harness/scripts/capability.ts`
  - `.lazy-harness/scripts/jcode-wiring.ts`
  - `.lazy-harness/scripts/self-test.py`
- Key historical commits:
  - `3fb22a1` — `.jcode/harness/20-project-rules.md` pointer-only migration.
  - `684b390` — executable rule lifecycle/action-boundary guard introduced.
  - `9411cbd` — hard gates and runtime/dev-instance lookup guard reverted.
  - `4ab9a5f` — tool-attached rule policy deprecated into no-op shim.
  - `98c979c` — lazy harness instruction pointer-only.
- Protection gap:
  - no current fixture proves a host operational rule changes later command choice via capability/default/warn/block behavior.

## 2026-06-10 correction — separate project facts from operating rulebook

Status: user-confirmed-requirement
Confirmation: user-confirmed

User correction:

```text
규칙을 저장하는 방식도 만들도록 하는게 좋겠지?? 이게 레코드는 프로젝트에대한사실이고 이 프로젝트를 개발하면서의 행동규약은 따로있어야하잖아
```

Interpretation:

Lazy-harness currently uses `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/**` records for project facts, contracts, behavior, decisions, regressions, and source-of-truth knowledge. That is necessary but not sufficient for project-specific development behavior.

The framework also needs a distinct **project operating rulebook** concept for rules that tell agents how to work inside a host project:

- which commands are canonical/default,
- which commands are discouraged or require justification,
- which workflow steps must happen before mutation,
- which project-specific tools, scripts, skills, or validations should be preferred,
- which actions warn or block,
- how those rules are surfaced to agents at planning/action time.

This rulebook must not be stored only in `.jcode` or Jcode memory. It should be canonical under `.lazy-harness`, but semantically separate from factual records.

## Proposed storage split

| Knowledge type | Meaning | Canonical storage |
|---|---|---|
| Project fact record | What the project is / has / guarantees | `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/**` |
| Operating rulebook entry | How agents should work while developing this project | proposed `.lazy-harness/rules/**` or `.lazy-harness/ssot/project-operating-rules.*` |
| Capability/action registry | Machine-readable command/tool/prompt/validation mapping and level | `.lazy-harness/ssot/capabilities.json` or successor registry |
| Runtime evidence/journal | What happened in a session | `.lazy-harness/state/**` or `.lazy-harness/logs/**`, non-canonical |
| Local/private Jcode wiring | User/private harness execution preference | `.jcode/**`, pointer/local-only only |

## Design implication

The next design should not only improve record discovery. It should define a first-class project operating rule storage path and connect it to Capability Registry / Guidance Ladder so that rules can become:

```text
discover → recommend → default → warn → block
```

without turning every rule into a brittle tool-specific hook.

## Open design options

A. Add `.lazy-harness/rules/` as a new first-class layer for project operating rules.
B. Keep all canonical rule bodies under `.lazy-harness/ssot/`, but define a dedicated `project-operating-rules.md/json` schema.
C. Use Capability Registry as the canonical rulebook and require every operating rule to map to a capability entry.
D. Hybrid: human-readable rulebook under `.lazy-harness/rules/**`, machine-readable action mapping in `.lazy-harness/ssot/capabilities.json`. Recommended candidate.
E. Other user-specified structure.

## Rule placement

- Rule: Project facts and project development operating rules must be modeled separately; storing facts in records is not enough because agents also need a project operating rulebook that changes development behavior.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/project-rule-adaptation-regression-audit-20260610.md`
- Why not AGENTS.md: this is a framework architecture requirement pending design/implementation, not a short universal prompt rule yet.
- Why not `.jcode`: `.jcode` is local/private wiring and must not become the canonical shared project rulebook.
- Confirmation: user-confirmed

## Discovery capture

- DDD: no business/domain vocabulary change.
- SDD: candidate contract for project operating rulebook storage and resolution.
- BDD: agent behavior should distinguish fact lookup from operating-rule application.
- TDD: future regression should prove host worktree/dev-instance rules are stored separately from facts and influence command selection.
- ADR: likely required to choose `.lazy-harness/rules/**` vs SSOT-only vs Capability-only storage.
- SSOT: existing rule-sources and capability-registry records need alignment with the chosen storage model.
- Planning: this section extends the active regression audit.
