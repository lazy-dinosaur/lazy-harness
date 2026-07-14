# Evidence: Cross-stack architecture core and skill pilot validation

## Scope

This capsule supports source validation of the implementation work unit that follows
baseline commit `71d6e11` for ADR 0054.

Validated surfaces:

- architecture profile catalog and both JSON schemas;
- `lazy architecture inspect|plan|apply` and the Host Architecture Map writer;
- Project Profile V2 candidate-only adapter and delegated promotion flow;
- Pi/OMP `lazy-architecture-refactor` package skill;
- Category A distribution and host-owned architecture-map preservation;
- canonical architecture records, graph links, and regression coverage.

Out of scope:

- application-source refactoring or architecture inference;
- policy/capability enforcement or warn/block promotion;
- npm publication;
- downstream canary sync before the separate W1.4 safety confirmation;
- the pending 37-row legacy graph migration;
- pre-existing Unicode replacement-character cleanup.

## Environment

- Date: 2026-07-14
- Project root: `/home/lazydino/dev/lazy-harness`
- Branch: `main`
- Base commit: `71d6e11`
- State: implementation worktree, not yet committed or pushed
- Bun: `1.3.14`
- Python: `3.14.4`
- Pi: `0.80.6`
- OMP: `16.2.2`

## Commands

Primary source gates:

```bash
npm run typecheck:node
python3 -m py_compile .lazy-harness/scripts/self-test.py
.lazy-harness/bin/lazy test --scope framework
.lazy-harness/bin/lazy doctor --profile=full
git diff --check
```

Record, graph, and implementation-map checks:

```bash
.lazy-harness/bin/lazy record-lint --format=json
.lazy-harness/bin/lazy record-structure-audit --format=json
.lazy-harness/bin/lazy graph-hygiene --format=json
.lazy-harness/bin/lazy impl-map --format=json
```

Schema checks used Python `jsonschema.Draft202012Validator` against the canonical catalog
and proposal. Negative copies added top-level and nested `enforcement`, a `..` traversal
reference, a planning semantic owner, and a nested unknown catalog property.

The architecture sandbox regression was also invoked directly through
`check_architecture_guidance_cli()` after Python compilation.

Current-runtime package checks:

```bash
.lazy-harness/bin/lazy pi smoke --format=json
.lazy-harness/bin/lazy omp smoke --format=json
pi  -e packages/lazy-harness-pi --mode rpc --no-session
omp -e packages/lazy-harness-pi --mode rpc --no-session
```

The RPC harness sent `{"type":"get_commands"}`. Pi returned the command through the
`get_commands` response; OMP exposed it through its initial
`available_commands_update` event.

Map-first discovery used the complete overview and targeted drill-downs for ADR 0054,
the architecture SDD, ADRs 0028/0030, graph hygiene, implementation-map contracts, and
the Pi package contract before source/test inspection.

## Results

- `npm run typecheck:node` passed.
- Python compilation passed.
- Focused architecture sandbox regression passed, including unknown-property rejection,
  path traversal, semantic-owner boundaries, catalog-content digest binding, root-relative
  proposals, scope-parent cycles, directional and explicit-cross-scope relations, lock/stale
  apply behavior, atomic cleanup, and full-tree side-effect snapshots.
- Full framework self-test passed: `ran=85`, `skipped=0`.
- Full doctor passed D01-D08. D08 reported three pre-existing Unicode replacement-character
  warnings; the doctor still completed successfully.
- `record-lint`: 169 inspected, 169 clean, 0 issues, 0 advisories.
- `record-structure-audit`: 169 canonical records, 0 orphan canonical records, and 0 graph
  parse errors. The existing corpus advisory remains 11 records without surface terms.
- `graph-hygiene`: 675 rows, 0 invalid rows, 0 duplicate IDs, and 2 existing command-string
  path warnings. The newly added architecture rows introduced no path issue.
- `impl-map`: 168 records `ok`, 1 pre-existing `needs-map`; all architecture records are
  `ok` with no drift.
- JSON, JSONL, and XML parsing passed, and `git diff --check` returned no output.
- Positive schema fixtures validated. All schema negative copies were rejected.
- Pi and OMP one-run smokes returned `ok=true`.
- Pi and OMP each discovered exactly one `skill:lazy-architecture-refactor` from the
  source-path package. Pi also reported the exact canonical `SKILL.md` path.
- The source checkout still has no `.lazy-harness/project/architecture-map.json`.
- Parallel final review found one additional scope-parent-cycle defect. The traversal was
  fixed, a two-node cycle regression was added, the full suite passed again, and the focused
  follow-up reviewer reported the seam clean with no blocker.
- The user confirmed `omp plugin link` as canonical over stale `plugin install` TDD prose,
  and confirmed `.lazy-harness/bin/lazy` as the canonical test/doctor entrypoint over missing
  Bun package scripts. The affected records/docs were reconciled.

## Interpretation

The evidence supports a high-confidence claim that the approved bounded architecture core,
Project Profile adapter, distribution contract, and Pi/OMP skill work in the framework source
checkout and reject the previously reproduced blocker cases.

This does not prove downstream deployment reach. Canary sync remains blocked until the
separate W1.4 `COMPLETE/SAFE` confirmation, and that canary must not modify application source.
It also does not resolve the 37 legacy graph rows, the two pre-existing command-string graph
warnings, the one unrelated implementation-map gap, or the three D08 Unicode advisories.

Pi-lens/LSP still reports repository-wide ambient Node typing and broad pre-existing scanner
findings for the large self-test module. The canonical Bun build, focused regression, full
framework self-test, and doctor gates passed; this capsule does not claim a clean project-wide
Pi-lens scan.

## Reproduce

1. Check out the implementation worktree on top of `71d6e11`.
2. Run the primary source gates above from the repository root.
3. Run record-lint, structure audit, graph hygiene, and implementation-map audit.
4. Validate the two JSON schemas with the positive fixtures and the negative mutations listed
   above.
5. Run Pi and OMP with the package through RPC mode and verify
   `skill:lazy-architecture-refactor` appears exactly once.
6. Confirm the source checkout has no host-owned architecture-map file.
7. Do not run downstream sync until W1.4 is explicitly reported `COMPLETE/SAFE`.

## Related records

- `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
- `.lazy-harness/domain/architecture-guidance.md`
- `.lazy-harness/spec/platform/architecture-guidance.md`
- `.lazy-harness/behavior/architecture-refactor-flow.md`
- `.lazy-harness/tests/architecture-guidance.md`
- `.lazy-harness/ssot/architecture-guidance-storage.md`
- `.lazy-harness/spec/platform/project-profile-v2.md`
- `.lazy-harness/spec/platform/pi-agent-package.md`
- `.lazy-harness/tests/pi-agent-package.md`
- `.lazy-harness/evidence/2026-07-13-cross-stack-architecture-planning-baseline.md`

## Retention / privacy

Retain this capsule with ADR 0054 and the eventual implementation commit. It contains
summarized commands and results only. No credentials, tokens, personal data, raw transcripts,
raw assistant responses, or unrelated product data are included. Reviewer session artifacts
under `.pi-subagents/` remain local and are not part of the implementation commit.
