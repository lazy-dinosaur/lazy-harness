# ADR 0033 — Layer Completeness Gate for TDD and Regression Records

Status: accepted
Date: 2026-05-14

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Aliases:
  - layer 완전성
  - layer completeness
  - 영향도 판단
  - 교차 layer 영향
- Applies when:
  - creating or updating a TDD/regression record for a bug fix
  - judging whether a change also affects SDD/BDD/SSOT/DDD layers
  - a turn risks a "TDD-only done" false completion
- Must:
  - on every TDD/regression update, in the same turn either update affected SDD/BDD/SSOT/DDD records
  - or add a `Layer completeness` section marking SDD/BDD/SSOT/DDD each impacted or not, with reasons
  - prefer updating the impacted layer's primary record and cross-linking over burying facts in TDD prose
  - stop and ask an option-gated question when the impacted layer is ambiguous
- Must not:
  - complete a turn with a TDD/regression record only, leaving impacted layers unrecorded
- Record completion:
  - bug fixes add/update the TDD record plus impacted SDD/BDD/SSOT/DDD records or an explicit Layer completeness judgement
- Related records:
  - `.lazy-harness/spec/platform/layer-completeness-gate.md`
  - `.lazy-harness/spec/platform/implementation-map-standard.md`
  - `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`

## Context

A host session can correctly add a TDD/regression record for a bug fix, then stop before checking whether the same change also changed a contract, user-visible behavior, SSOT invariant, or domain rule.

That creates a false sense of completeness: future agents see the regression note but miss the SDD/BDD/SSOT facts needed to avoid reintroducing the bug.

## Decision

Adopt a **layer completeness gate** whenever an agent creates or updates TDD/regression records.

For every TDD/regression update, the same turn must do one of these:

1. update the affected SDD/BDD/SSOT/DDD records, or
2. add a `Layer completeness` section to the TDD record that explicitly mentions SDD, BDD, SSOT, and DDD and records each as impacted or not impacted, or
3. stop and ask an option-gated question when the impacted layer is ambiguous.

The gate is enforced in three places:

- `.lazy-harness/AGENTS.md` concise behavior grammar,
- `.lazy-harness/spec/platform/layer-completeness-gate.md` detailed operating standard,
- `.lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh` response-completed helper.

## Required judgement shape

A TDD record may satisfy the gate locally with:

```md
## Layer completeness

- SDD: updated `.lazy-harness/spec/...` / 영향 없음 because ...
- BDD: updated `.lazy-harness/behavior/...` / 영향 없음 because ...
- SSOT: updated `.lazy-harness/ssot/...` / 영향 없음 because ...
- DDD: updated `.lazy-harness/domain/...` / 영향 없음 because ...
```

If any layer is impacted, prefer updating that layer's primary record and cross-linking rather than burying the fact in TDD prose.

## Consequences

### Positive

- Prevents “TDD-only done” false completions.
- Makes bug fixes durable across contract, behavior, invariant, and domain records.
- Gives lifecycle hooks a concrete signal to stop incomplete turns.

### Negative

- TDD record writing requires a little more judgement.
- Some changes will need one extra record or a short `Layer completeness` section.

### Mitigation

- The helper passes if the same turn also touches SDD/BDD/SSOT/DDD records.
- If no other layer is impacted, a compact local judgement section is enough.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/AGENTS.md` — adds the concise Layer completeness gate rule and forbidden TDD-only completion.
  - `.lazy-harness/spec/platform/layer-completeness-gate.md` — detailed SDD operating contract.
  - `.lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh` — response-completed guard for TDD/regression-only record writes.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — includes the helper in the lifecycle chain.
  - `.lazy-harness/scripts/self-test.py` — protects AGENTS wording and helper behavior.
  - `.lazy-harness/manifests/init-categories.json` — syncs this ADR/standard/helper to hosts.
- Key symbols:
  - `check_layer_completeness_helper` (`.lazy-harness/scripts/self-test.py`) — fixture test for blocking TDD-only records and allowing explicit judgement.
  - `check_agents_md_invariants` (`.lazy-harness/scripts/self-test.py`) — asserts the concise AGENTS guard remains present.
- Flow:
  1. Agent writes `.lazy-harness/tests/*.md` or `.lazy-harness/regression/*`.
  2. `response.completed` calls `check-layer-completeness.sh`.
  3. Helper passes if SDD/BDD/SSOT/DDD record was also touched or the TDD record has explicit `Layer completeness` judgement.
  4. Otherwise helper injects a STOP message with options.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/layer-completeness-gate.md`
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
  - ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
- Machine index:
  - graph ids: `pending`
  - generated index key: `pending until implementation-index generator exists`
