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
  - identify one primary narrative record for the logical work unit by default
  - require every TDD Markdown record to carry explicit SDD/BDD/SSOT/DDD judgement rows
  - update another layer only for an independent semantic delta; otherwise mark its row `no independent delta` / not impacted
  - preserve regression protection in TDD without copying the primary record's full narrative
  - stop and ask an option-gated question when the impacted layer or primary record is ambiguous
- Must not:
  - complete a turn with a TDD/regression record only, leaving impacted layers unrecorded
- Record completion:
  - bug fixes add/update TDD with the four-layer matrix and update only independently impacted SDD/BDD/SSOT/DDD primary records
- Related records:
  - `.lazy-harness/spec/platform/layer-completeness-gate.md`
  - `.lazy-harness/spec/platform/implementation-map-standard.md`
  - `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`

## Context

A host session can correctly add a TDD/regression record for a bug fix, then stop before checking whether the same change also changed a contract, user-visible behavior, SSOT invariant, or domain rule.

That creates a false sense of completeness: future agents see the regression note but miss the SDD/BDD/SSOT facts needed to avoid reintroducing the bug.

## Decision

Adopt a **layer completeness gate** whenever an agent creates or updates TDD/regression records.

For every TDD/regression update, the same turn must:

1. identify the logical work unit's primary narrative record,
2. write an explicit SDD/BDD/SSOT/DDD judgement row in the TDD Markdown record even when another layer record is updated,
3. update an affected layer's primary record only when that layer owns an independent semantic delta; otherwise mark its row `no independent delta` / not impacted, and
4. stop and ask an option-gated question when the impacted layer or primary record is ambiguous.

A regression JSON/JSONL update satisfies the judgement shape through a same-turn TDD/regression Markdown record; regression data alone is incomplete because it cannot carry the Markdown matrix.

The primary-record default is not a hard one-file cap. A regression TDD plus an actually changed contract or behavior record is valid; copying the same invariant into several layers merely because they are related is not.

The gate is enforced in three places:

- `.lazy-harness/AGENTS.md` concise behavior grammar,
- `.lazy-harness/spec/platform/layer-completeness-gate.md` detailed operating standard,
- `.lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh` response-completed helper.

## Required judgement shape

Every TDD Markdown record satisfies the gate with a compact four-row matrix:

```md
## Layer completeness

- SDD: updated `.lazy-harness/spec/...` because this contract independently changed / no independent delta because ...
- BDD: updated `.lazy-harness/behavior/...` because this visible flow independently changed / no independent delta because ...
- SSOT: updated `.lazy-harness/ssot/...` because this ownership/config invariant independently changed / no independent delta because ...
- DDD: updated `.lazy-harness/domain/...` because this domain rule independently changed / no independent delta because ...
```

If any layer is impacted, its matrix row names the updated primary record and reason; every other row remains an explicit `no independent delta` judgement.

## Consequences

### Positive

- Prevents “TDD-only done” false completions.
- Makes bug fixes durable across contract, behavior, invariant, and domain records.
- Gives lifecycle hooks a concrete signal to stop incomplete turns.

### Negative

- TDD record writing requires a little more judgement.
- Some changes will need one extra record or a short `Layer completeness` section.
- Without a primary-record default, the gate can be misread as permission to mirror one invariant across every related layer.

### Mitigation

- The helper mechanically requires four non-empty `- SDD:` / BDD / SSOT / DDD rows even when another layer path was touched.
- The helper never decides whether a semantic delta is real; the LLM owns that judgement after reading records/source/tests.
- If no other layer is independently impacted, the compact four-row local judgement is enough.
- Repeated validation, review-round, commit, and staging detail belongs in one evidence capsule or transient output, not in every canonical record.

## Amendment — 2026-07-13: primary canonical record by default

A seven-day Medivance dogfood audit found useful durable records alongside repeated SDD/BDD/SSOT narratives, validation logs copied into canonical planning, and stale contradictions inside long records. The user selected the "guard → sample cleanup" rollout.

Decision amendment:

- one logical work unit chooses one primary narrative record by default;
- candidate enumeration and cross-layer inspection do not imply multi-record canonical promotion;
- every TDD Markdown record keeps the four-layer matrix; an additional layer record is promoted only for that layer's independent semantic delta;
- `no independent delta` is an explicit successful completeness judgement, not a skipped check;
- detailed repeated validation is consolidated into at most one evidence capsule when durable, otherwise it remains transient/no-record;
- enforcement starts as LLM-owned recommend guidance and fixture-protected wording, not a shell hook that guesses semantic meaning.

## Implementation map

- Status: `verified; 2026-07-13 primary-record amendment implemented`
- Primary files:
  - `.lazy-harness/AGENTS.md` — adds the concise Layer completeness gate rule and forbidden TDD-only completion.
  - `.lazy-harness/spec/platform/layer-completeness-gate.md` — detailed SDD operating contract.
  - `.lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh` — response-completed guard requiring the four-row TDD judgement matrix.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — includes the helper in the lifecycle chain.
  - `.lazy-harness/scripts/self-test.py` — protects AGENTS wording and helper behavior.
  - `.lazy-harness/manifests/init-categories.json` — syncs this ADR/standard/helper to hosts.
  - `.lazy-harness/spec/platform/record-write-update-policy.md` — canonical promotion and evidence-placement contract.
  - `.lazy-harness/spec/platform/record-decision-broker.md` — MultiCandidate review vs canonical promotion boundary.
  - `.lazy-harness/ssot/policies.json` — typed `primary-canonical-record` recommend policy.
- Key symbols:
  - `check_layer_completeness_helper` (`.lazy-harness/scripts/self-test.py`) — fixture test for blocking TDD-only records and allowing explicit judgement.
  - `check_agents_md_invariants` (`.lazy-harness/scripts/self-test.py`) — asserts the concise AGENTS guard remains present.
- Flow:
  1. Agent writes `.lazy-harness/tests/*.md` or `.lazy-harness/regression/*` and identifies the logical work unit's primary narrative record.
  2. `response.completed` calls `check-layer-completeness.sh`.
  3. Helper requires every touched TDD/regression Markdown record to contain non-empty SDD/BDD/SSOT/DDD rows; a regression JSON/JSONL path requires a same-turn Markdown record carrying the matrix.
  4. The LLM decides which rows have independent semantic deltas and updates only those layer primary records.
  5. Missing matrix judgement injects a STOP message whose default guidance is primary-record-first.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/layer-completeness-gate.md`
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
  - ADR: `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`
- Machine index:
  - graph ids: `kg_primary_canonical_record_policy_20260713`, `kg_primary_canonical_record_broker_20260713`
  - generated index key: `pending until implementation-index generator exists`
