# Workflow Compression Plan — Read-only Router, Not Safety Reduction

Date: 2026-05-19
Status: planned
Source: user-confirmed planning discussion + Opus/Oracle cross-validation

## Summary

Implement **workflow compression** for lazy-harness: reduce agent confusion by routing requests through a read-only advisory decision summary, while preserving all safety invariants.

This is **not** a safety reduction and **not** a new canonical layer. It is a front-door compression/refactor over existing lazy-harness rules.

## Confirmed direction

User asked whether the harness should become less heavy and more effective. The agreed direction is:

- Keep safety invariants.
- Reduce repeated agent judgement and duplicated questions.
- Make the agent follow typed defaults instead of re-interpreting all AGENTS rules on every request.
- Start with a read-only `lazy route` CLI.
- Delay blocking/enforcement until fixtures prove the router is safe.

## Cross-validation summary

### Opus reviewer conclusion

Opus agreed with workflow compression if it is implemented as a **non-authoritative orchestration/UX layer**.

Key points:

- Do not weaken record-first or default-unknown.
- Do not weaken ambiguous force gates.
- Queue-close with `interview-loop --apply` remains non-negotiable.
- `response.completed` remains the primary completion audit.
- Task router must reuse existing framework-contract concepts.
- Record tiers must not create new canonical stores.
- Profiles are minimum-safe presets, not optimization shortcuts.
- UX compression is necessary but only as presentation/decision compression, not semantic weakening.

### Oracle conclusion

Oracle revised from conditional reject to **conditional approve as a compression refactor**.

Key points:

- Compression must not become a new workflow layer.
- Axes are better than a single task enum.
- Light vs full capture is high leverage, but `light` cannot mean chat-only.
- Option gates may be narrowed only by precision, dedupe, batching, or already-answered evidence.
- `lazy route` must start read-only/advisory.
- AGENTS compression should happen only after SDD + fixtures prove safety.

## Non-negotiables

1. Record-first search remains mandatory for host-dependent work.
2. Default-unknown remains the epistemic baseline.
3. Ambiguous means structured force gate.
4. User answers to queued questions must be closed with `interview-loop --mode answer ... --apply`.
5. `response.completed` remains a completion audit path.
6. No new canonical record layer.
7. Candidate/draft/generated data is not canonical truth.
8. Router is read-only and advisory first.
9. Router cannot write records, mutate queues, or auto-select Recommended options.
10. Commit-time `lazy test` remains blocking.

## Planned phases

### Phase 0 — Drift cleanup

Goal: align current docs/help/hook descriptions with actual behavior.

Tasks:

- Check `lazy help` / CLI usage for unsupported options such as `test --profile`.
- Align `hooks/README.md` with current advisory vs blocking policy.
- Align `AGENTS.md §4` with commit-time enforcement and edit/write non-blocking policy.
- Add/adjust self-test consistency checks where practical.

### Phase 1 — ADR 0037

Create:

```text
.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md
```

ADR content:

- Problem: agent confusion comes from too many judgement points.
- Decision: add workflow compression as read-only advisory routing.
- Invariants preserved: record-first, default-unknown, option gate, queue close, response audit, existing layer model.
- No new canonical layer.
- Profiles are minimum-safe presets, not bypasses.

### Phase 2 — SDD

Create:

```text
.lazy-harness/spec/platform/workflow-compression-router.md
```

Define finite axis values:

- `intent`: feature | fix | refactor | investigation | docs | release | unknown
- `scope`: trivial | code-local | behavior | contract | ownership | unknown
- `risk`: low | medium | high
- `confidence`: low | medium | high
- `affectedLayers`: ddd | sdd | bdd | tdd | adr | ssot
- `recordSearch.mode`: none | recommended | required
- `recordCapture.mode`: none | candidate | canonical
- `implementationMap.tier`: none | file-map | symbol-flow | full-graph
- `gate.mode`: none | narrow-confirm | option-gate
- `validation`: focused-test | lazy-test | doctor-smoke | explicit-confirmation, etc.

Also include default action table and compression rules.

### Phase 3 — Read-only CLI

Add:

```bash
.lazy-harness/bin/lazy route --message "..." --format=json
.lazy-harness/bin/lazy route --message "..." --format=md
```

Implement:

```text
.lazy-harness/scripts/task-router.ts
```

Constraints:

- read-only
- deterministic heuristic first
- no file writes
- no queue mutation
- no record mutation
- no Recommended auto-selection
- confidence low escalates gate/record search

### Phase 4 — Router self-test fixtures

Add fixture set for:

1. trivial copy/style
2. host-detail lookup
3. local refactor
4. behavior change
5. contract/API change
6. ownership/source-of-truth correction
7. ambiguous request
8. destructive/risk request
9. queued answer requiring `--apply`
10. candidate vs canonical distinction

Self-test checks:

- `check_task_router_fixtures`
- `check_task_router_read_only`
- `check_task_router_invariants`

### Phase 5 — Minimal docs alignment

After router fixtures pass:

- Add `route` to lazy help/docs.
- Update hooks README.
- Minimally update AGENTS to mention route as advisory front door.
- Do not perform major AGENTS compression yet.

### Phase 6 — Validation and sync

Run:

```bash
.lazy-harness/scripts/self-test.py
python3 .lazy-harness/scripts/doctor.py --profile smoke
```

Then commit/push source and sync medivance host:

```bash
cd /home/lazydino/dev/medivance
bun ~/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts --from ~/dev/lazy-harness --target ~/dev/medivance --force
.lazy-harness/bin/lazy test
python3 .lazy-harness/scripts/doctor.py --profile smoke
```

## 2nd-stage follow-up

Only after the read-only router is stable:

- Compress AGENTS.md into invariants + pointers.
- Add response.completed advisory comparison against router output.
- Add fast/normal/strict/audit-only profiles as minimum-safe presets.
- Collect UX/false-positive metrics.

Note: these fast/normal/strict/audit-only items are workflow execution presets. They are not the same as the Project Profile architecture contract in `.lazy-harness/spec/platform/project-profile.md`.

### 2026-05-19 telemetry update

Route-specific telemetry is now the prerequisite for judging the remaining 2nd-stage work. Normal Jcode dogfooding use is collected automatically by `response.completed` when `last_user_message` is present. Explicit route probes can also call:

```bash
.lazy-harness/bin/lazy route --message "..." --format=md --log
```

Then review accumulated evidence with:

```bash
.lazy-harness/bin/lazy route-summary --format=md
```

The telemetry is append-only and non-canonical. It stores route axes plus stable message/message-id hashes, not the raw user message. Duplicate lifecycle calls for the same message are deduped by `messageIdHash`. The goal is to make the next-session question "should we compress AGENTS / add profiles / adjust heuristics?" answerable from logs instead of memory.

User clarification on 2026-05-20: do not over-interpret telemetry immediately after implementation. First use it to confirm plumbing. Evaluate route quality and workflow-compression choices only after accumulated normal dogfooding use.

2026-05-20 deployment note: automatic telemetry collection was fixed in source commit `caa2a2b` after normal use showed `response.completed` hooks firing without `route-decisions.jsonl` growth. The fix was synced to the known dogfooding host `/home/lazydino/dev/medivance` with `lazy-sync --force`, and `/home/lazydino/dev/medivance/.lazy-harness/bin/lazy test` passed. Manual sync smoke telemetry was removed from the host log so subsequent `route-summary` reflects normal use.

2026-05-20 feedback-loop clarification: this source checkout is where the framework is built and improved. Downstream hosts such as Medivance are where the framework is applied and dogfooded. Workflow-compression decisions are made back in this source repo, using Medivance normal-use telemetry as practical evidence. Review with `cd /home/lazydino/dev/medivance && .lazy-harness/bin/lazy route-summary --format=md`, then implement framework improvements here.

## Acceptance criteria

1. Planning/ADR/SDD records exist and are internally consistent.
2. `lazy route` exists and is documented.
3. Router is read-only: no writes, no queue mutation, no record mutation.
4. Router output uses finite schema values from the SDD.
5. Fixtures prove trivial work does not require full graph.
6. Fixtures prove ambiguous/risk requests still gate.
7. Fixtures prove candidate does not satisfy canonical requirement.
8. Self-test passes.
9. Doctor smoke passes.
10. medivance host sync + host lazy test + doctor smoke pass.

## Implementation map

### Relevant records

- `.lazy-harness/framework/framework-contract.md` — core lazy-harness contract and lazy definition.
- `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md` — response/pre-commit/pre-push hook model.
- `.lazy-harness/decisions/0019-ambiguous-detection-force-gate.md` — ambiguity gate invariant.
- `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md` — implementation map storage and graph requirements.
- `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md` — planning/discovery capture requirement.
- `.lazy-harness/decisions/0035-interview-queue-close-mandate.md` — queued answer close invariant.
- `.lazy-harness/decisions/0036-record-search-trigger-by-intent-not-keyword.md` — record search by intent.

### Planned implementation files

- `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md` — new ADR.
- `.lazy-harness/spec/platform/workflow-compression-router.md` — router SDD.
- `.lazy-harness/scripts/task-router.ts` — read-only router CLI implementation.
- `.lazy-harness/bin/lazy` — add `route` command dispatch/help.
- `.lazy-harness/scripts/self-test.py` — route fixture/invariant checks.
- `.lazy-harness/fixtures/task-router/**` — route test fixtures.
- `.lazy-harness/hooks/README.md` — docs alignment.
- `.lazy-harness/AGENTS.md` — minimal truthfulness alignment first, full compression later.
