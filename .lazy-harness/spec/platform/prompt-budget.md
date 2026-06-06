# SDD — Prompt Budget Measurement

Status: accepted
Date: 2026-06-06
Layer: SDD
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
Related TDD: `.lazy-harness/tests/prompt-budget.md`
Related plan: `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - reducing lazy-harness prompt-heavy operation
  - changing `.lazy-harness/AGENTS.md`, `.jcode/harness/**`, or `message.received` injection text
  - evaluating whether context delivery, project navigation, or evidence helpers can replace repeated prompt text
- Must:
  - measure prompt-ish line counts and rendered `message.received` injection size before compression
  - keep measurement read-only and deterministic enough for self-test fixtures
  - render the current `message.received` hook with an isolated runtime state so measurements do not write raw user text or pollute host journals
  - report duplicate grammar risk between `.lazy-harness/AGENTS.md` and `.jcode/harness/05-lazy-harness.md` when both exist
  - distinguish target, hard ceiling, and transition hard ceiling so Phase 1 can measure current over-budget prompts without changing runtime behavior
  - keep generated measurement output non-canonical; canonical truth remains records/source/tests
- Must not:
  - shorten or rewrite prompts as part of the measurement phase
  - classify raw user text or run semantic context selection inside `message.received`
  - treat prompt-budget output as proof that required records were read
  - store raw user messages, transcripts, or assistant responses
- Record completion:
  - changes to prompt surfaces, budget thresholds, rendered-hook measurement, duplicate detection, or self-test enforcement update this SDD and `.lazy-harness/tests/prompt-budget.md`
- Related records:
  - `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - `.lazy-harness/spec/platform/context-delivery-contract.md`
  - `.lazy-harness/spec/platform/guidance-ladder.md`

## Purpose

Prompt Budget Measurement makes lazy-harness's prompt/runtime compression work measurable before any behavior-changing prompt edits.

It answers:

```text
How large are the prompt surfaces that the harness currently injects or asks agents to load?
```

The first implementation is intentionally observational. It provides a CLI/report and self-test fixture, but it does not change `message.received` behavior.

## Measured surfaces

The Phase 1 script measures these surfaces when present:

1. `.lazy-harness/AGENTS.md`
2. root `AGENTS.md`
3. `.jcode/harness/*.md`
4. rendered `.lazy-harness/hooks/lifecycle/on-message-received.sh` system reminder body
5. project-local skill `SKILL.md` files under `.jcode/skills/**` and `.lazy-harness/skills/**` when present

Missing optional surfaces are valid and should be reported as absent, not failure.

## Token estimate policy

Exact tokenizer parity is not required in Phase 1. The script uses a deterministic approximation that is good enough to detect regressions and compare before/after changes:

```text
estimatedTokens = max(whitespace token count, ceil(non_space_character_count / 6))
```

This intentionally avoids external tokenizer dependencies.

## Initial budgets

| Surface | Target | Hard ceiling | Transition hard ceiling | Phase 1 behavior |
|---|---:|---:|---:|---|
| Rendered `message.received` body | 200-600 tokens | 1,000 tokens | 1,400 tokens | warn above hard; fail above transition hard |
| `.lazy-harness/AGENTS.md` | <= 140 lines | <= 200 lines | 220 lines | warn above hard; fail above transition hard |
| `.jcode/harness/05-lazy-harness.md` | pointer-only | <= 80 lines | 220 lines | warn above hard; fail above transition hard |
| `SKILL.md` prompt files | <= 120 lines | <= 160 lines | 200 lines | warn above hard; fail above transition hard |

The transition hard ceilings are deliberately looser so Phase 1 can be merged before Phase 2 compacting work. Later phases may lower transition ceilings after dogfood evidence.

## CLI contract

Command:

```bash
.lazy-harness/bin/lazy prompt-budget --format=md
python3 .lazy-harness/scripts/prompt-budget.py --root . --format=json
```

Supported options:

- `--root DIR` — host root, default `LAZY_HOST_ROOT` or cwd
- `--format json|md` — output format, default `md`
- `--transition-message-tokens N` — override rendered message transition hard ceiling

JSON output shape is intentionally compact:

```json
{
  "schemaVersion": "1.0",
  "generatedAt": "2026-06-06T00:00:00Z",
  "root": "/host/root",
  "status": "pass|warn|fail",
  "budgets": {...},
  "surfaces": [...],
  "duplicates": [...],
  "renderedMessageReceived": {...},
  "notes": [...]
}
```

## Privacy and runtime isolation

When rendering the hook, the script must:

1. use a fixed synthetic fixture message,
2. set `LAZY_RUNTIME_ROOT` to a temporary directory,
3. set `LAZY_HOST_ROOT` to the measured root,
4. avoid emitting the synthetic message in output,
5. delete temporary runtime state after measurement.

## Implementation map

- Primary files:
  - `.lazy-harness/spec/platform/prompt-budget.md` — this SDD contract.
  - `.lazy-harness/tests/prompt-budget.md` — regression/fixture record.
  - `.lazy-harness/scripts/prompt-budget.py` — read-only measurement CLI.
  - `.lazy-harness/bin/lazy` — dispatches `lazy prompt-budget`.
  - `.lazy-harness/scripts/self-test.py` — protects script output shape, privacy, and transition thresholds.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — rendered by the measurement script but not changed in Phase 1.
- Flow:
  1. CLI resolves host root.
  2. CLI counts prompt-ish files.
  3. CLI renders `message.received` with isolated runtime state.
  4. CLI estimates tokens and status against budgets.
  5. CLI reports duplicate grammar fingerprints where applicable.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy prompt-budget --format=md`
  - `python3 .lazy-harness/scripts/prompt-budget.py --root . --format=json`

## Rule placement

- Rule: prompt/runtime compression must start with deterministic prompt-budget measurement before behavior-changing prompt edits.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/prompt-budget.md`
- Why not AGENTS.md: this is a platform measurement contract, not final always-loaded grammar.
- Why not `.jcode`: this is shared framework source behavior, not local/private wiring.

## Discovery capture

- DDD: none.
- SDD: this contract defines prompt budget measurement.
- BDD: future agent behavior should become less noisy after later phases, but Phase 1 has no behavior change.
- TDD: `.lazy-harness/tests/prompt-budget.md` covers regression criteria.
- ADR: implements ADR 0041 direction without changing the architecture decision.
- SSOT: budgets are canonical in this SDD until superseded.
- Planning: Phase 1 of `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`.
