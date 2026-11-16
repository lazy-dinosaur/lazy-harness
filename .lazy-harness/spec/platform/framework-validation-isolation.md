# Framework validation ownership and observation isolation

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - runtime ownership inventory
  - isolated benchmark self-test
  - framework validation isolation
- Applies when: running source/host runtime hardcoding checks or benchmark validation
- Must: reuse authoritative manifest path matching, fail when host ownership cannot be established, keep source-authoring checks broad, and compare exact state only inside owned test fixtures.

## Runtime inventory

`framework-runtime-ownership.ts --root <harness-root> --scope framework|host` returns `{schemaVersion:1,scope,paths}` with sorted harness-relative runtime-file paths. It reads only. The runtime directories and suffixes preserve the previous scan coverage. Framework source includes all candidates, including undeclared files. Installed hosts include only Category A file/directory paths selected using existing `shouldIncludeManifestPath` glob/exclude behavior. A name like local has no intrinsic exemption: a declared nested file remains managed. Missing/invalid ownership metadata fails instead of returning a success-shaped empty inventory. The hardcoding token policy is unchanged; Python self-test validates inventory before reading the selected files.

## Benchmark observation

The registered `check_retrieval_workflow_benchmark_cli` allocates a canonical temporary host and enters ownership before copying input. It reuses copy_harness_fixture; only the established .cache/state ignore tuple and root runtime tmp are excluded; canonical evidence remains input, nested canonical tmp and canonical failure semantics stay intact. Only the fixture's dispatcher/cwd/root/env are used. Shape, numeric metrics, helper counts, no semantic-authority fields, measurement-only boundary and actual no-mutation assertions are retained. Graph/cache presence and bytes must be identical; creation/deletion/write are failures. An external writer to real host knowledge is never restored or attributed to the fixture.

A failed setup releases its allocation and preserves the original error. No shared-host graph snapshot restoration, global ignore regex, paid model or monitoring activation is introduced. BOTH registration and public benchmark CLI/result contracts remain unchanged.

## Implementation map

- framework-runtime-ownership.ts exports the typed manifest selection/read-only inventory and internal CLI.
- manifest-path-matcher.ts remains the glob/exclude semantic authority.
- self-test.py retains the two registered callers and isolates benchmark assertions in `_check_retrieval_workflow_benchmark_fixture`.
- tests/lazy-harness/host-validation-isolation.test.ts provides controlled negative cases and unmocked integration.
- Primary TDD: .lazy-harness/tests/host-validation-isolation.md; copy-helper contract: .lazy-harness/tests/harness-fixture-runtime-isolation.md; benchmark contract: .lazy-harness/spec/platform/retrieval-workflow-benchmark.md.
