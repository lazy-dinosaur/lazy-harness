# TDD — Layer completeness supplied-root path resolution

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - layer gate absolute path
  - cross-root matrix false positive
- Surface terms:
  - check_layer_completeness_helper
  - valid_matrix_roots
- Applies when:
  - validating tool-supplied TDD/regression paths or same-turn regression pairing
- Must:
  - inspect the supplied target root, never a same-named Parent-cwd shadow
  - preserve quoted JSON spaces/unicode, relative paths and canonical deduplication
  - warn for missing/non-file targets, missing or empty judgments, and regression data lacking a valid same-root matrix
  - leave independent semantic delta classification to the LLM
- Related records:
  - `.lazy-harness/spec/platform/layer-completeness-gate.md`
  - `.lazy-harness/decisions/0033-layer-completeness-gate.md`

## Reproduction and approved repair

An absolute foreign-root TDD path had all four judgments, yet warned from Parent cwd and passed from Target cwd. The old regex retained only the `.lazy-harness/...` suffix. User approved fixing path binding and regression protection, not copying Target records into Parent or changing the valid matrix.

`check_layer_completeness_helper` retains seven existing shape/pairing cases and adds ten protections: quoted foreign paths with spaces/unicode; valid/invalid Parent shadows; missing target; foreign-data/local-matrix denial; valid same-root pair; invalid same-root matrix; strategy XML exclusion; absolute/explicit-relative local references; canonical duplicate suppression. Existing payload-file transport and lifecycle registration stay intact.

## Implementation map

- `.lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh`: inline token decoding, canonical root/path identities, `is_tdd_markdown` and `valid_matrix_roots`.
- `.lazy-harness/scripts/self-test.py#check_layer_completeness_helper`: synthetic roots and matrix/pairing fixtures, through `run_layer_completeness_helper`.
- `.lazy-harness/hooks/lifecycle/on-response-completed.sh`: unchanged helper invocation.
- Flow: tool metadata → explicit root/path → actual record shape → same-root pairing → existing warning/no-output protocol. No user-text classifier or new hook.
- Fresh publication results: `.lazy-harness/planning/repository-publication-review.md`; historical source results are not publication proof.

## Layer completeness

- SDD: independent touched-path binding/pairing contract delta in `.lazy-harness/spec/platform/layer-completeness-gate.md`.
- BDD: no independent delta; intended workflow unchanged, mechanical warning corrected.
- SSOT: no independent delta; root ownership, storage and registration preserved.
- DDD: no independent delta; no domain/business rule change.
