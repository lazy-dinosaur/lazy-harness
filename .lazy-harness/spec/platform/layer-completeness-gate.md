# Layer Completeness Gate

Status: accepted
Layer: SDD
Related ADR: `.lazy-harness/decisions/0033-layer-completeness-gate.md`
Related standard: `.lazy-harness/spec/platform/implementation-map-standard.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - a turn creates or updates a TDD/regression record (bug fix or regression protection)
  - judging whether a fix also touched contracts, behavior, source-of-truth, or domain rules
- Must:
  - in the same turn, update affected SDD/BDD/SSOT/DDD records, or
  - add a `Layer completeness` judgement explicitly naming SDD, BDD, SSOT, DDD, or
  - stop with an option gate when the primary layer is ambiguous
- Must not:
  - complete a TDD/regression turn on regression evidence alone with no cross-layer check
- Record completion:
  - when a fix touches a layer, update that layer's primary record instead of only noting it in TDD
- Related records:
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

A triggered turn is complete only if at least one condition is true:

1. The same turn also updates an affected cross-layer record:
   - SDD: `.lazy-harness/spec/**`
   - BDD: `.lazy-harness/behavior/**`
   - SSOT: `.lazy-harness/ssot/**`
   - DDD: `.lazy-harness/domain/**`
2. The TDD Markdown record includes a `Layer completeness` section that explicitly names all four: SDD, BDD, SSOT, DDD.
3. The agent stops with an option gate because the primary layer is ambiguous.

## Required judgement

Use this block when no other layer is impacted:

```md
## Layer completeness

- SDD: 영향 없음 because no API/component/IPC/contract changed.
- BDD: 영향 없음 because no user-visible flow changed.
- SSOT: 영향 없음 because no routing/config/schema/source-of-truth invariant changed.
- DDD: 영향 없음 because no domain term/business rule changed.
```

If any item is impacted, update that layer's primary record instead of only saying so in TDD.

## Examples

### TDD-only is incomplete

A TDD regression record is incomplete if it documents reproduction/protection but does not also check:

- SDD: did the ChatWindow/open routing contract change?
- BDD: did reminder-click user flow change?
- SSOT: did reminder routing or scroll-target ownership become an invariant?
- DDD: was a new domain term/business rule introduced?

### Complete with cross-layer records

A fix is complete when it updates, for example:

- the TDD regression record (reproduction/protection)
- the SDD contract for the affected component or route
- the BDD record for the affected user flow
- the SSOT record for the affected routing or ownership invariant

DDD may be explicitly marked as no impact if no new domain language exists.

## Lifecycle helper behavior

`check-layer-completeness.sh` runs from `on-response-completed.sh`.

It emits a STOP message when:

- the payload indicates a TDD/regression record was written,
- no SDD/BDD/SSOT/DDD record was also written,
- and the TDD Markdown record lacks an explicit `Layer completeness` block.

The STOP options are:

- update related SDD/BDD/SSOT/DDD records,
- add a local Layer completeness judgement,
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
  - `check_layer_completeness_helper` (`.lazy-harness/scripts/self-test.py`) — asserts TDD-only blocks and explicit judgement passes.
  - `run_layer_completeness_helper` (`.lazy-harness/scripts/self-test.py`) — fixture runner.
- Flow:
  1. A turn writes TDD/regression records.
  2. Lifecycle hook extracts touched `.lazy-harness` paths from recent tool calls.
  3. Helper detects whether cross-layer record updates or local completeness judgement exist.
  4. Missing judgement injects STOP text into the next assistant turn.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh`
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0033-layer-completeness-gate.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
- Machine index:
  - graph ids: `pending`
  - generated index key: `pending until implementation-index generator exists`
