# Homepage File-Recording Pattern Import Review — 2026-06-04

Status: analysis-record
Layer: Planning
Scope: framework-source comparing downstream `medivance-homepage` file-recording patterns

## Trigger

User asked to inspect the other harness's file-internal and file-based recording methods and identify whether anything should be imported into lazy-harness.

## Lazy-harness grounding read

- `.lazy-harness/planning/medivance-homepage-harness-comparison-20260604.md`
- `.lazy-harness/ssot/implementation-map-storage.md`
- `.lazy-harness/spec/platform/implementation-map-standard.md`
- `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md` via filename search
- `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md`
- `.lazy-harness/spec/platform/context-delivery-contract.md`
- `.lazy-harness/spec/platform/record-decision-broker.md`
- `.lazy-harness/tests/record-decision-broker.md`
- `.lazy-harness/planning/dogfood-auto-recording-status-report.md`
- `.lazy-harness/generated/README.md`
- `.lazy-harness/logs/validations.jsonl`

## Homepage evidence read

- `/home/lazydino/dev/medivance-homepage/AGENTS.md`
- `/home/lazydino/dev/medivance-homepage/docs/PROJECT-MAP.md`
- `/home/lazydino/dev/medivance-homepage/docs/ssot/ssot-map.yaml`
- `/home/lazydino/dev/medivance-homepage/docs/ssot/adr/ADR-003-ai-development-principles.md`
- `/home/lazydino/dev/medivance-homepage/docs/evidence/stryker-2026-06-04.md`
- `/home/lazydino/dev/medivance-homepage/docs/evidence/dev-tooling-2026-06-04.md`
- `/home/lazydino/dev/medivance-homepage/docs/evidence/responsive-convention-2026-06-04.md`
- `/home/lazydino/dev/medivance-homepage/src/components/shared/brand/Logo.tsx`
- `/home/lazydino/dev/medivance-homepage/scripts/dev-instance-registry.mjs`
- `/home/lazydino/dev/medivance-homepage/scripts/wt-cli.mjs`

## Observed homepage recording patterns

### 1. Source file JSDoc header + update history

Shape:

```ts
/**
 * 제목: ...
 * 작성자: ...
 * 작성일: YYYY-MM-DD
 * 설명: ...
 *
 * 설계 이유:
 *   - ...
 *
 * @maintenance 이 파일 수정 시: 수정이력에 한 줄 추가, 설계가 바뀌면 설계 이유 갱신.
 *
 * 수정이력:
 *   - YYYY-MM-DD HH:mm author reason
 */
```

Example read: `src/components/shared/brand/Logo.tsx`.

Assessment for lazy-harness:

- Import value: medium, but not as-is.
- Good: embeds file purpose and design rationale at the exact file an agent edits.
- Risk: per-edit change history duplicates git, creates noisy maintenance debt, and can trigger meaningless edits.
- Recommended adaptation: optional concise module header for high-risk framework entrypoints/scripts with `Purpose`, `Record links`, `Design constraints`, `Generated/runtime/canonical?`, but **do not require per-edit history** in source files.

### 2. PROJECT-MAP frontmatter + bounded module/status map

Shape:

- YAML-like frontmatter with `updated`, `tests`, `stack`, cross-cutting `layers`, and `domains` status.
- Body has one-work-unit rule and high-level module map.
- Explicit rule: map records module/domain altitude only; method/implementation details are delegated to sub-docs/code.

Assessment for lazy-harness:

- Import value: high.
- Lazy-harness already has `.lazy-harness/project/feature-navigation.xml` planned/missing and context-index expects it.
- Homepage pattern can inform a Project Profile / feature navigation template:
  - compact snapshot,
  - status by feature/domain/layer,
  - no method-level detail,
  - links down to canonical records and implementation maps.
- Recommended adaptation: add a generic host `Project Map / Feature Navigation` template or generator, likely under `.lazy-harness/project/feature-navigation.xml` plus optional `.lazy-harness/project/project-map.md` rendering.

### 3. Evidence markdown capsules

Shape:

- `docs/evidence/<topic>-YYYY-MM-DD.md`
- Sections: Scope, Environment, Commands and results, Interpretation, Reproduction, Related records.
- Strong variant: mutation evidence preserves tabular score output and exact failure threshold.
- Responsive convention evidence includes proven before-breakage, implementation list, validation matrix, screenshots, addendum.

Assessment for lazy-harness:

- Import value: high.
- Lazy-harness has JSONL logs and runtime telemetry, but durable human-readable evidence capsules are not standardized.
- Recommended adaptation: introduce `.lazy-harness/evidence/` or `.lazy-harness/validations/evidence/` as a canonical optional artifact for non-trivial validation claims.
- Key rule to import: if README/roadmap/status/test-count/quality score claims a number, it should cite a durable evidence capsule, not terminal output only.
- Suggested capsule schema:
  - Scope
  - Environment
  - Commands and exact results
  - Interpretation
  - Reproduction
  - Related records / implementation map links
  - Retention/privacy note

### 4. SSOT tier injection map

Shape:

- `docs/ssot/ssot-map.yaml` has `tier-0-always`, `tier-1-phase`, `tier-2-sequence`, `tier-3-task`.
- Each tier lists compiled and source docs, optional flags, and injection owner (`hook` or `controller`).

Assessment for lazy-harness:

- Import value: high, but merge with existing context-delivery design.
- Lazy-harness context-delivery has packet shape and generated context index, but does not yet have a simple human-authored tier manifest for always/phase/task docs.
- Recommended adaptation: add `context tier manifest` as an optional source into `context-index` and Context Delivery:
  - always-read / phase / task / optional,
  - source record path,
  - compiled/generated path if any,
  - owner and privacy class.
- This should not become semantic authority. It is a deterministic hint over canonical records.

### 5. Dev-instance runtime registry

Shape:

- `.dev-instances/<name>.json` stored under main worktree.
- Fields: name, kind, worktree, branch, port, pid, url, logPath, startedAt, updatedAt, command.
- Includes prune-stale and inspect JSON helpers.

Assessment for lazy-harness:

- Import value: medium.
- Useful for app hosts that need many local dev servers.
- Lazy-harness should not make it core global memory. It is runtime state and should be ignored/non-canonical.
- Recommended adaptation: optional host capability `dev-instance-registry` or `lazy capability add dev-instance-registry`, not default core.

### 6. Worktree CLI harness symlink pattern

Shape:

- Sibling worktree creation links env files and symlinks `.jcode` / `.lazy-harness` from main worktree.
- Prints health summary: jcode/lazy/env/env.local/node_modules/bun.lock.

Assessment for lazy-harness:

- Import value: medium-low for core, medium for a skill/capability.
- Good ergonomics for branch worktrees.
- Risk: linked `.lazy-harness` means shared mutable runtime/records across sibling worktrees. Must be documented clearly.
- Recommended adaptation: optional `lazy worktree` helper or recipe, with explicit warning that canonical framework state is shared unless copied/synced deliberately.

### 7. Commit message as work log + map update as closure

Shape:

- One work unit: read map -> implement contract-first TDD -> gates -> log/evidence -> update map.
- Work log is structured commit message; milestone/status goes to PROJECT-MAP.

Assessment for lazy-harness:

- Import value: high conceptually.
- Lazy-harness already commits with confidence/internal-only trailers and has record-as-output.
- Recommended adaptation: add a lightweight `work-unit closure checklist` to framework docs/route output:
  - context read satisfied,
  - validation evidence captured if non-trivial,
  - record/project map updated if status changed,
  - commit message contains result/validation/confidence.

## Recommended import shortlist

1. **Evidence Capsule Standard** (highest ROI)
   - New SDD/TDD/backlog: durable markdown evidence for non-trivial validation claims.
   - Integrate with `.lazy-harness/logs/validations.jsonl` and record-decision evidence kind `validation`.

2. **Context Tier Manifest**
   - A human-authored tier manifest feeding context-index/context-delivery, similar to homepage `ssot-map.yaml`.
   - Must remain hints over records, not a replacement for record-first reads.

3. **Project Map / Feature Navigation Template**
   - Fill the currently missing `.lazy-harness/project/feature-navigation.xml` role using a bounded altitude map.
   - Optionally render markdown snapshot for humans.

4. **Work-unit Closure Checklist**
   - Formalize `read -> implement -> validate -> evidence -> record/map -> commit` as a compressed route/checklist.

5. **Optional Source Module Header Standard**
   - For new/high-risk framework scripts only.
   - Include purpose/record-links/design constraints, not per-edit history.

6. **Optional Runtime Dev Instance Registry Capability**
   - Useful for host apps, not core framework memory.

## Do not import as-is

- Mandatory per-edit `수정이력` in every source file: too noisy for lazy-harness and duplicates git.
- Homepage-specific `docs/ssot/**` product taxonomy: keep in homepage, not framework source.
- Worktree symlink behavior as default: useful but risky if users expect per-worktree records.
- Gitleaks/Semgrep/CodeQL claims from homepage ADR as accepted current implementation: tracked homepage files did not show automation; import only as future security capability if separately verified.

## Suggested implementation order if approved

1. Draft `.lazy-harness/spec/platform/evidence-capsule-standard.md` and `.lazy-harness/tests/evidence-capsule-standard.md`.
2. Add `.lazy-harness/evidence/README.md` and a sample template.
3. Extend `record-decision-broker` docs to treat evidence capsules as durable `validation` evidence references.
4. Draft context tier manifest spec and sample fixture.
5. Draft project feature-navigation template/generator plan.
6. Only later consider source module header and dev-instance registry as optional capabilities.

## Rule placement

- Rule: homepage file-recording patterns contain importable ideas, but lazy-harness should import only generic evidence/context/project-map/work-unit patterns, not app-specific product docs or noisy per-edit source histories.
- Scope: transient planning / import review.
- Primary record: `.lazy-harness/planning/homepage-file-recording-pattern-import-review-20260604.md`.
- Why not AGENTS.md: not yet user-approved global operating grammar.
- Why not ADR: no accepted design decision yet.
- Why not `.jcode`: shared framework design analysis, not local/private Jcode wiring.

## Discovery capture

- DDD: no new domain invariant.
- SDD: evidence capsule standard and context tier manifest are likely SDD candidates.
- BDD: work-unit closure checklist may affect agent-visible workflow behavior.
- TDD: evidence capsule and context tier manifest need self-test fixtures if accepted.
- ADR: importing tier/evidence/project-map patterns may need an ADR if adopted broadly.
- SSOT: project map / feature-navigation source-of-truth role should be clarified if implemented.
- Planning: this file records the import review and recommended order.
