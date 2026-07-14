# Evidence: Cross-stack architecture planning and ADR baseline

## Scope

This capsule supports closure of the Lazy-Harness three-layer architecture
research, planning, and ADR decision work unit.

Validated artifacts:

- `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`;
- `.lazy-harness/planning/cross-stack-architecture-guidance.md`;
- `.lazy-harness/planning/cross-stack-architecture-profiles.md`;
- `.lazy-harness/planning/cross-stack-architecture-host-mapping.md`;
- the architecture-direction additions in
  `.lazy-harness/planning/lazy-harness-v2-direction-purpose.md`.

The work is record-only. Schemas, writers, validators, policy/capability changes,
source scaffolding, runtime behavior, and deployment reach are out of scope.

## Environment

- Date: 2026-07-13
- Project root: `/home/lazydino/dev/lazy-harness`
- Branch: `main`
- Baseline commit: `81afe2f`
- State: ADR/planning records are uncommitted and coexist with unrelated edits
- Research inputs: Goedamjip, official FSD material, and cross-stack backend,
  CLI/worker, monorepo, and multi-service evidence summaries

## Commands

Map-first inventory and representative drill-downs:

```bash
.lazy-harness/bin/lazy map --overview --complete --format=md
.lazy-harness/bin/lazy map \
  .lazy-harness/planning/cross-stack-architecture-guidance.md \
  --format=md --limit=8
.lazy-harness/bin/lazy map \
  .lazy-harness/planning/cross-stack-architecture-profiles.md \
  --format=md --limit=8
.lazy-harness/bin/lazy map \
  .lazy-harness/planning/cross-stack-architecture-host-mapping.md \
  --format=md --limit=8
.lazy-harness/bin/lazy map \
  .lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md \
  --format=md --limit=8
```

Record and Markdown checks:

```bash
.lazy-harness/bin/lazy record-lint --format=json
.lazy-harness/bin/lazy record-structure-audit --format=json

git diff --check -- \
  .lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md \
  .lazy-harness/planning/cross-stack-architecture-guidance.md \
  .lazy-harness/planning/cross-stack-architecture-profiles.md \
  .lazy-harness/planning/cross-stack-architecture-host-mapping.md \
  .lazy-harness/evidence/2026-07-13-cross-stack-architecture-planning-baseline.md

awk 'length($0) > 100 { print FILENAME ":" FNR ":" length($0) }' \
  .lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md \
  .lazy-harness/planning/cross-stack-architecture-guidance.md \
  .lazy-harness/planning/cross-stack-architecture-profiles.md \
  .lazy-harness/planning/cross-stack-architecture-host-mapping.md \
  .lazy-harness/evidence/2026-07-13-cross-stack-architecture-planning-baseline.md
```

Manual review included complete reads of the ADR, the three planning records, a
recent ADR precedent, and the relevant Project Profile V2, Policy Machinery V2,
record-write, rule-source, and evidence-capsule contracts.

## Results

- Complete map overview found 239 records, including 54 ADRs and ADR 0054.
- `record-lint` inspected 164 eligible records: 164 clean, zero issues, and zero
  advisories.
- `record-structure-audit` reported zero orphan canonical records and zero graph
  parse errors. Its corpus-wide cue-only baseline still reports 11 records without
  surface terms; ADR 0054 itself includes both Aliases and Surface terms.
- `git diff --check` returned no output.
- The line-length check returned no output for the ADR, planning records, and
  evidence capsule.
- The user confirmed the planning baseline and then explicitly selected formal ADR
  progress. ADR 0054 records that decision without approving implementation.
- No framework test suite or runtime/deployment check was claimed because no
  implementation or deployed artifact changed.

## Interpretation

The results show that ADR 0054 and its three supporting planning records are
recorded, cross-linked, format-clean, and free of current record-lint issues.

They do not prove that a schema, Project Profile writer, profile resolver, evidence
adapter, validator, policy, or enforcement path exists or works. Those remain
explicitly unapproved follow-up slices. Confidence remains medium until mixed-host
pilots exercise the values, relations, scope model, and waiver flow.

## Reproduce

1. Change to `/home/lazydino/dev/lazy-harness`.
2. Run the map overview and the four drill-down commands above.
3. Read ADR 0054 and the three planning records completely.
4. Run `record-lint`, `record-structure-audit`, `git diff --check`, and the
   line-length command above.
5. Confirm that all records preserve the explicit no-implementation boundary.

## Related records

- `.lazy-harness/planning/cross-stack-architecture-guidance.md`
- `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
- `.lazy-harness/planning/cross-stack-architecture-profiles.md`
- `.lazy-harness/planning/cross-stack-architecture-host-mapping.md`
- `.lazy-harness/planning/lazy-harness-v2-direction-purpose.md`
- `.lazy-harness/spec/platform/project-profile-v2.md`
- `.lazy-harness/spec/platform/policy-machinery-v2.md`
- `.lazy-harness/spec/platform/project-operating-rulebook.md`
- `.lazy-harness/ssot/rule-sources.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`

## Retention / privacy

Retain this capsule with ADR 0054 until it is superseded by an ADR amendment,
superseding ADR, or implementation-phase evidence capsule. It contains summarized
results only. No credentials, tokens, personal data, raw transcripts, raw
assistant responses, or unrelated product data are included.
