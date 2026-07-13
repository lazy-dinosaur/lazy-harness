# Layer Completeness Gate

Status: accepted
Layer: SDD
Related ADR: `.lazy-harness/decisions/0033-layer-completeness-gate.md`
Related standard: `.lazy-harness/spec/platform/implementation-map-standard.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 완전성 게이트
  - completeness check
  - 교차 layer 검사
- Applies when:
  - a turn creates or updates a TDD/regression record (bug fix or regression protection)
  - judging whether a fix also touched contracts, behavior, source-of-truth, or domain rules
- Must:
  - identify the logical work unit's primary narrative record
  - require every TDD Markdown record to carry an explicit four-row SDD/BDD/SSOT/DDD judgement matrix, even when another layer record is updated
  - update another layer only for an independent semantic delta; otherwise mark that row `no independent delta`
  - stop with an option gate when the primary record or layer is ambiguous
- Must not:
  - complete a TDD/regression turn on regression evidence alone with no cross-layer check
- Record completion:
  - every TDD update records the four-layer matrix; independently changed layers also update their primary records
- Related records:
  - `.lazy-harness/spec/platform/sdd-component-contract-trigger.md`
  - `.lazy-harness/decisions/0033-layer-completeness-gate.md`
  - `.lazy-harness/spec/platform/implementation-map-standard.md`
  - `.lazy-harness/ssot/implementation-map-storage.md`

## Purpose

Prevent a bug-fix session from recording only TDD/regression evidence while omitting changed contracts, visible behavior, source-of-truth invariants, or domain rules.

## Trigger

The gate applies when a turn creates or updates any of:

- `.lazy-harness/tests/*.md`
- `.lazy-harness/regression/*.jsonl`
- `.lazy-harness/regression/*.md`

`test-strategy.xml` is excluded because it is the host test-strategy SSOT, not a per-bug regression note.

## Completion contract

A triggered TDD Markdown turn is complete only when all applicable conditions hold:

1. The TDD record includes a `Layer completeness` section with four explicit bullet rows: SDD, BDD, SSOT, DDD.
2. Each row records either the independently updated primary record/reason or `no independent delta` / not impacted.
3. Every layer with an independent semantic delta is updated/cross-linked in the same slice:
   - SDD: `.lazy-harness/spec/**`
   - BDD: `.lazy-harness/behavior/**`
   - SSOT: `.lazy-harness/ssot/**`
   - DDD: `.lazy-harness/domain/**`
4. The agent stops with an option gate when the primary narrative record or impacted layer is ambiguous.

A `.lazy-harness/regression/*.jsonl` data update cannot carry Markdown sections itself, so it must be paired in the same turn with a `.lazy-harness/tests/*.md` or `.lazy-harness/regression/*.md` record containing the matrix. A regression Markdown record may carry its own matrix.

One primary narrative record is the default, not a hard one-file cap. TDD regression protection may coexist with an independently changed contract/behavior/invariant record; relatedness alone is not an independent delta.

## Required judgement

Every TDD Markdown record uses this compact matrix. Example when no other layer is independently impacted:

```md
## Layer completeness

- SDD: no independent delta because no API/component/IPC/contract changed.
- BDD: no independent delta because no user-visible flow changed.
- SSOT: no independent delta because no routing/config/schema/source-of-truth invariant changed.
- DDD: no independent delta because no domain term/business rule changed.
```

If a layer is independently impacted, replace that row with the updated primary record and reason; the other rows remain explicit `no independent delta` judgements.

## Examples

### TDD-only is incomplete

A TDD regression record is incomplete if it documents reproduction/protection but does not also check:

- SDD: did the ChatWindow/open routing contract change?
- BDD: did reminder-click user flow change?
- SSOT: did reminder routing or scroll-target ownership become an invariant?
- DDD: was a new domain term/business rule introduced?

### Complete with cross-layer records

A fix is complete when it keeps one primary narrative record and updates only independently changed layers, for example:

- the TDD regression record captures reproduction/protection,
- the SDD record is also updated only if the component or route contract independently changed,
- the BDD record is also updated only if the visible user flow independently changed,
- the SSOT record is also updated only if routing or ownership became a new source-of-truth invariant.

Any layer without its own delta is explicitly marked `no independent delta` rather than receiving mirrored prose.

## Lifecycle helper behavior

`check-layer-completeness.sh` runs from `on-response-completed.sh`.

It emits a STOP message when:

- the payload indicates a TDD/regression record was written, and
- a touched TDD/regression Markdown record lacks `Layer completeness` plus explicit `- SDD:`, `- BDD:`, `- SSOT:`, and `- DDD:` judgement rows, or
- a regression JSON/JSONL update has no same-turn TDD/regression Markdown record that carries that matrix.
Touching another layer does not bypass the matrix. The helper validates only its mechanical shape and non-empty row values; it does not decide whether a semantic delta is real.

The helper can observe touched paths and explicit judgement text only. It must not guess whether two records contain an independent semantic delta; that decision remains LLM-owned after record/source/test reads.


The STOP options are:

- add the four-row judgement matrix to the TDD record (always required for TDD Markdown),
- update/cross-link another layer's primary record only for an independent semantic delta; otherwise write `no independent delta`,
- ask the user if layer ownership is ambiguous,
- or record an intentional skip in `.lazy-harness/logs/skipped.jsonl`.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh` — enforces the response-completed gate.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — invokes the helper before TDD cross-verify.
  - `.lazy-harness/AGENTS.md` — concise operational grammar.
  - `.lazy-harness/scripts/self-test.py` — regression coverage for helper behavior and AGENTS wording.
- Key symbols:
  - `check_layer_completeness_helper` (`.lazy-harness/scripts/self-test.py`) — asserts missing/label-only matrices block, explicit judgements pass, and regression JSON/JSONL requires a same-turn Markdown matrix.
  - `run_layer_completeness_helper` (`.lazy-harness/scripts/self-test.py`) — fixture runner.
- Flow:
  1. A turn writes TDD/regression records and chooses a primary narrative record.
  2. Lifecycle hook extracts touched `.lazy-harness` paths from recent tool calls.
  3. Helper requires a non-empty SDD/BDD/SSOT/DDD bullet matrix in each touched TDD/regression Markdown record, regardless of other layer touches; regression JSON/JSONL must be paired with such a Markdown record.
  4. The LLM confirms independent semantic deltas; the helper never infers them from paths or raw text.
  5. Missing matrix judgement injects STOP text whose default guidance is primary-record-first.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh`
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0033-layer-completeness-gate.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
- Machine index:
  - graph ids: `kg_primary_canonical_record_policy_20260713`, `kg_primary_canonical_record_broker_20260713`
  - generated index key: `pending until implementation-index generator exists`
