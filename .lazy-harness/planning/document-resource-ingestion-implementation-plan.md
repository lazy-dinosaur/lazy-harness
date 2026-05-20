# Document Resource Ingestion + Project Profile implementation plan

Status: draft
Date: 2026-05-20
Related SDD:
- `.lazy-harness/spec/platform/document-resource-ingestion.md`
- `.lazy-harness/spec/platform/project-profile.md`
- `.lazy-harness/plans/project-init-interview-spec.md`

## Goal

Implement the next framework slice without collapsing two capabilities into one:

1. **Document Resource Ingestion**: scan host-root non-harness docs, score freshness/authority/duplication/contamination, and produce a reviewable intake report/ledger.
2. **Project Profile**: consume existing records and optional ingestion outputs, then run an interview-first architecture/profile flow.

The implementation must support the lazy-harness dogfooding loop:

```text
build framework here
→ sync to Medivance
→ run against Medivance normal project docs/records
→ observe gaps
→ improve framework here
```

## Non-goals for first slice

- Do not auto-promote external-doc claims into DDD/SDD/BDD/TDD/ADR/SSOT without review.
- Do not implement the full interview/apply engine immediately.
- Do not use sibling repositories as document sources unless explicitly requested.
- Do not treat stale/newer docs as authoritative by mtime alone.

## Slice 1 — Document Resource Ingestion inspect mode

Status: implemented in `.lazy-harness/scripts/document-resource-ingestion.ts` on 2026-05-20.

Create `.lazy-harness/scripts/document-resource-ingestion.ts`.

CLI shape:

```bash
bun .lazy-harness/scripts/document-resource-ingestion.ts --mode inspect [--format md|json] [--root <path>] [--include <glob>] [--max-files N]
```

Minimum behavior:

1. Resolve host root from `--root`, `LAZY_HOST_ROOT`, or cwd.
2. Scan root-bound non-harness docs:
   - `README.md`, `README.*`
   - `docs/**/*.{md,mdx,txt}`
   - `architecture/**/*.{md,mdx,txt}`
   - `notes/**/*.{md,mdx,txt}`
   - selected root docs such as `CHANGELOG.md`, `CONTRIBUTING.md`, `MIGRATION*.md`, `RELEASE*.md`
3. Exclude `.lazy-harness/**`, `.git/**`, `node_modules/**`, build/output dirs, binary files.
4. For each doc, emit:
   - path
   - size/mtime
   - heading summary
   - detected architecture/domain/test/config keywords
   - current-path references that exist vs are missing
   - status suggestion: `authoritative`, `candidate`, `historical`, `duplicate`, `conflicting`, or `rejected`
   - reasons
5. Detect duplicate/overlap clusters using normalized title + heading hashes + rough content fingerprint.
6. Output a review report without writing canonical records by default.

Validation:

- Add self-test fixture with fresh, stale, duplicate, and polluted docs.
- Confirm JSON output is parseable.
- Confirm `.lazy-harness` docs are excluded when root is a host project.

## Slice 2 — Document Resource Ingestion plan/apply dry-run

Status: implemented in `.lazy-harness/scripts/document-resource-ingestion.ts` on 2026-05-20. `plan` proposes ledger/candidate writes without applying; `apply` currently requires `--dry-run` and prints the same write preview.

After inspect works in Medivance, add:

```bash
--mode plan
--mode apply
--dry-run
```

Planned outputs:

- `.lazy-harness/project/document-intake.xml`
- `.lazy-harness/knowledge/candidates.jsonl`

Rules:

- `plan` proposes record writes but does not apply.
- `apply` only writes confirmed/candidate ledgers, not final DDD/SDD/BDD/TDD/ADR/SSOT promotions unless user-approved.
- Suspicious claims are quarantined, not promoted.

## Slice 3 — `/lazy-doc-ingest` framework skill

Status: implemented in `.lazy-harness/scripts/jcode-wiring.ts` and `.lazy-harness/manifests/skills.xml` on 2026-05-20.

Add generated skill wrapper via `.lazy-harness/scripts/jcode-wiring.ts`.

Skill behavior:

1. Read `.lazy-harness/spec/platform/document-resource-ingestion.md`.
2. Run inspect first.
3. Present summary and option gate:
   - A. create candidate ledger only
   - B. run deeper plan
   - C. skip docs and proceed to Project Profile
   - D. custom
4. Never auto-promote external facts.

## Slice 4 — Project Profile inspect/interview skeleton

Create `.lazy-harness/scripts/project-profile.ts` only after Slice 1/3 is usable.

First behavior:

```bash
bun .lazy-harness/scripts/project-profile.ts --mode inspect --format md|json
```

It checks for required profile outputs:

- `.lazy-harness/project/profile.xml`
- `.lazy-harness/project/stack.xml`
- `.lazy-harness/project/filesystem.xml`
- `.lazy-harness/project/feature-navigation.xml`
- `.lazy-harness/tests/test-strategy.xml`

It also reports whether Document Resource Ingestion outputs exist and whether Profile should consume them.

## Slice 5 — Medivance dogfood

After Slice 1 and `/lazy-doc-ingest` wrapper:

1. Sync framework to `/home/lazydino/dev/medivance`.
2. Run document ingestion inspect in Medivance.
3. Check if it correctly identifies:
   - authoritative docs
   - stale docs
   - duplicate docs
   - polluted/conflicting docs
4. Record findings back here under planning/TDD/SDD as needed.

Status: first document-only dogfood completed on 2026-05-20 after syncing source commit `b021451` to `/home/lazydino/dev/medivance`.

Important correction: this dogfood was CLI document inspection only. It did **not** validate a running Medivance app instance, DB connectivity, UI behavior, or runtime profile. Any Medivance runtime/UI dogfood must first follow the Medivance named test instance policy: stop stale/conflicting instance, launch with `--test`, and verify `bun dev:inspect <name>` shows the test environment before judging behavior. See `.lazy-harness/ssot/medivance-dogfood-runtime-policy.md`.

Observed Medivance inspect summary:

- `/lazy-doc-ingest` wrapper installed in `.jcode/skills/lazy-doc-ingest/SKILL.md`.
- `doctor --profile smoke --scope host` passed.
- `document-resource-ingestion.ts --mode inspect --format=json --max-files=200` found 77 non-harness docs.
- Status distribution: `authoritative=1`, `candidate=66`, `conflicting=6`, `historical=4`, `duplicate=0`, `rejected=0`.
- Examples: `docs/action-system.md` candidate with current path refs; `docs/ai-service-plan.md` conflicting due missing service/router refs; `docs/archive/action-model-refactoring-plan.md` historical; `README.md` authoritative.

Dogfood improvement candidates:

- Duplicate detection may be too strict for semantically overlapping docs because Medivance reported no duplicate groups despite multiple architecture/auth/system docs.
- Contamination scoring catches explicit deprecated/outdated wording but often leaves those docs as `candidate`; future plan mode should expose these as review warnings rather than auto-rejecting.
- Medivance has enough docs that `--max-files` and sorted report UX matter; default JSON full scan was okay, but Markdown examples should communicate when truncated.

## Recommended next action

Start with **Slice 1 + Slice 3 wrapper**.

Reason:

- It creates observable behavior quickly.
- It dogfoods against Medivance without making irreversible record changes.
- It gives Project Profile better evidence later without overloading Project Profile itself.

## Discovery capture

- DDD: candidate, ingested docs may seed domain vocabulary later.
- SDD: updated, inspect CLI, plan/apply dry-run, and `/lazy-doc-ingest` wrapper implemented.
- BDD: none for first inspect slice.
- TDD: updated, self-test fixture covers fresh/stale/duplicate/polluted docs, `.lazy-harness` exclusion, plan proposed writes, candidate confirmation requirements, and apply dry-run gate.
- ADR: none, current split follows existing accepted SDD contracts.
- SSOT: none for first inspect slice.
- Planning: updated, this plan defines implementation slices.
