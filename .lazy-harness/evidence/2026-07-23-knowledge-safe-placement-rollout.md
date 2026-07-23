# Evidence: Knowledge-safe project-rule placement rollout

## Scope

This capsule covers the framework-source `lazy sync --skip-knowledge-seeds` implementation and its use to deploy the current-turn project-rule placement fix to the three approved dogfood hosts:

- `/home/lazydino/dev/medivance`
- `/home/lazydino/dev/medivance-pwa`
- `/home/lazydino/dev/medivance-homepage`

The protected rollout had to update normal Category A framework files and the sync marker while leaving every existing host `.lazy-harness/knowledge/*.jsonl` file byte-identical. It also had to preserve host-owned project identity, test strategy, registry-only rows, and pre-existing product working-tree state.

Out of scope: product source changes, product tests unrelated to framework wiring, database/release operations, legacy graph migration, dirty-primary-checkout reconciliation, and the separately planned implementation-map source/host ownership fix.

## Environment

- Work date: 2026-07-23.
- Clean integration worktree: `/tmp/lazy-code-org-rollout`.
- Branch: `integrate/code-org-host-adaptation-20260720`.
- Published placement commits already present before this work:
  - `daaa41a` — current-turn evidence scoping and semantic/action separation.
  - `daa56de37c48168a73a196d99170ecc118c17995` — distributed placement regression records.
- Published knowledge-safe sync commits:
  - `3fa6dd6` — `feat: add knowledge-safe sync opt-out`.
  - `30b1e4e424a27a6bc66d182b71b90103ea7f0ca8` — separate implementation-map ownership-drift handoff.
- All three hosts began at framework marker `52030c3cd052bdee219aa140ff03323a56675548`, with `sourceRoot=/tmp/lazy-code-org-rollout`.
- Pre-rollout product status: Medivance 0 lines, PWA 0 lines, Homepage 51 pre-existing lines. The Homepage status was treated as unrelated state and compared exactly before/after.
- Pre/post snapshots and raw command logs were stored under a transient `/tmp/lazy-skip-seeds-rollout.*` directory; only privacy-reviewed summaries are retained here.
- Untracked `.pi-subagents/` artifacts were excluded from commits and host-state comparisons.

## Commands

Working directory unless noted: `/tmp/lazy-code-org-rollout`.

```bash
# Focused implementation checks
python3 -m py_compile .lazy-harness/scripts/self-test.py
python3  # import self-test.py and call check_lazy_sync_prunes_stale_managed_files()
bun build .lazy-harness/scripts/lazy-sync.ts \
  --target=bun --outfile=/tmp/lazy-sync-skip-seeds-final.js
.lazy-harness/bin/lazy check --files <12 changed files> --format=json
.lazy-harness/bin/lazy record-lint --fail-on-issues --format=json
.lazy-harness/bin/lazy impl-map --format=json
git diff --check

# Final source regression
.lazy-harness/bin/lazy test --scope framework

# First protected rollout from each pre-flag host: invoke the updated source script directly
bun .lazy-harness/scripts/lazy-sync.ts \
  --from /tmp/lazy-code-org-rollout \
  --target <host> \
  --dry-run \
  --skip-knowledge-seeds
bun .lazy-harness/scripts/lazy-sync.ts \
  --from /tmp/lazy-code-org-rollout \
  --target <host> \
  --skip-knowledge-seeds

# Post-sync reach and regression on each host
cd <host>
.lazy-harness/bin/lazy sync --dry-run --skip-knowledge-seeds
.lazy-harness/bin/lazy test
```

A temporary verifier computed SHA-256 for every host `knowledge/*.jsonl`, compared product `git status`, project identity, and test strategy to the preflight snapshot, verified the marker commit/source root, and checked that host-only policy/capability rows remained JSON-equivalent while all framework seed ids remained present.

## Results

### Source implementation and review

- Focused knowledge-seed opt-out fixture: passed.
- Bun build: passed.
- Explicit static check: `ok=true`, 12 files, zero errors/warnings.
- Record lint: 171 inspected, 171 clean, zero issues/advisories.
- Source implementation-map audit: zero drift candidates.
- Final framework regression: `ran=86`, `skipped=0`, exit 0.
- Independent fresh-context reviewer: no blockers.
  - The reviewer identified the pre-flag-host bootstrap caveat; the skill and both READMEs now require direct invocation of the updated source-checkout script for the first protected rollout.
  - The reviewer requested direct marker coverage; the focused fixture now asserts `syncedFromCommit`, `sourceRoot`, and `syncedAt` after opt-out sync.
- TypeScript LSP still reported the repository's existing missing Node typings/module diagnostics. The Bun build passed; this capsule does not claim LSP/typecheck cleanliness.

### Downstream dry-run and live sync

Each host dry-run reported:

- drift: `behind`, from `52030c3cd052` to `30b1e4e424a2`;
- knowledge seeds: `SKIPPED (--skip-knowledge-seeds)`;
- Category A: `12 updated`, `288 unchanged`, `0 missing`;
- marker would advance to `30b1e4e424a2`.

Each live sync reported the same Category A counts and advanced the marker to `30b1e4e424a27a6bc66d182b71b90103ea7f0ca8`. Each installed host CLI then accepted the new flag, and its post-sync dry-run reported `equal: Already in sync`.

### Host-memory and host-state preservation

The complete filename-to-SHA-256 map for each host's existing knowledge JSONL corpus was identical before and after live sync and host regression:

- Medivance: 6 JSONL files; `candidates.jsonl=fa07cfe17c44…`, `graph.jsonl=b287098fcc87…`.
- PWA: 6 JSONL files; `candidates.jsonl=95ad7d92f899…`, `graph.jsonl=73a687c59264…`.
- Homepage: 7 JSONL files; `candidates.jsonl=8092da7f199c…`, `graph.jsonl=6f990604544c…`.

Existing conflict sidecars were included in those maps; no knowledge JSONL file or sidecar was added, removed, or changed. Host-owned `project-identity.md` and `test-strategy.xml` were byte-identical. Registry rows whose ids were absent from the framework source registry remained JSON-equivalent, and all framework capability/policy seed ids remained present.

Medivance and PWA product working-tree status remained empty. Homepage retained the same 51 pre-existing product-status lines exactly; no product file was created, deleted, staged, reverted, or rewritten by the rollout.

### Host regression

- Medivance: `lazy-harness self-test ok (scope=host, ran=59, skipped=27)`.
- PWA: `lazy-harness self-test ok (scope=host, ran=59, skipped=27)`; the existing doctor D07 package-health warning remained non-blocking.
- Homepage: `lazy-harness self-test ok (scope=host, ran=59, skipped=27)`.

## Interpretation

The evidence supports these bounded claims:

1. `--skip-knowledge-seeds` is opt-in; default sync still exercises the existing knowledge-seed merge path in the focused regression.
2. Opt-in mode bypasses only `knowledge/*.jsonl`. Other Category A copy/prune work, capability/policy seed merge behavior, and normal marker advancement remain active.
3. A pre-flag host cannot parse the option through its old installed dispatcher; direct invocation of the updated source-checkout script is the required first-rollout bootstrap. After that sync, the installed CLI accepts the flag.
4. The current placement fix reached all three named dogfood hosts, and their framework host suites passed.
5. The rollout did not modify host knowledge JSONL, host-owned identity/test strategy, host-only registry rows, or product working-tree state.

This evidence does not prove unknown-host rollout, product runtime behavior, TypeScript LSP cleanliness, or resolution of the framework implementation-map ownership drift. The source worktree path remains recorded in host markers and must stay available until the separately owned dirty primary checkout is reconciled. The 37-row legacy graph migration remains a separate user-approved guided task.

## Reproduce

```bash
# Inspect the published implementation
cd /tmp/lazy-code-org-rollout
git show 3fa6dd6 -- .lazy-harness/scripts/lazy-sync.ts .lazy-harness/scripts/self-test.py

# Re-run focused and full source checks
python3 - <<'PY'
import importlib.util, pathlib
path = pathlib.Path('.lazy-harness/scripts/self-test.py').resolve()
spec = importlib.util.spec_from_file_location('lazy_self_test', path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.check_lazy_sync_prunes_stale_managed_files()
PY
.lazy-harness/bin/lazy test --scope framework

# On a disposable host copy, hash knowledge before/after and run the protected sync
find <host>/.lazy-harness/knowledge -maxdepth 1 -name '*.jsonl' -print0 \
  | sort -z | xargs -0 sha256sum
bun .lazy-harness/scripts/lazy-sync.ts \
  --from /tmp/lazy-code-org-rollout \
  --target <host> \
  --dry-run \
  --skip-knowledge-seeds
```

Expected source regression line:

```text
lazy-harness self-test ok (scope=framework, ran=86, skipped=0)
```

Expected host regression line:

```text
lazy-harness self-test ok (scope=host, ran=59, skipped=27)
```

## Related records

- `.lazy-harness/spec/lazy-sync-drift-detection.md`
- `.lazy-harness/tests/lazy-sync-dirty-false-positive.md`
- `.lazy-harness/tests/project-rule-placement-gate-loop.md`
- `.lazy-harness/ssot/gate-fingerprint-state.md`
- `.lazy-harness/spec/platform/pi-agent-package.md`
- `.lazy-harness/tests/pi-agent-package.md`
- `.lazy-harness/planning/2026-07-23-framework-implementation-map-drift-handoff.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- Commits `daaa41a`, `daa56de37c48168a73a196d99170ecc118c17995`, `3fa6dd6`, and `30b1e4e424a27a6bc66d182b71b90103ea7f0ca8`.

## Retention / privacy

Retain with the framework change as the single summarized evidence capsule for this rollout. No credentials, secrets, personal data, product records, raw transcripts, raw assistant responses, or excessive command logs are included. The transient `/tmp` snapshots contain only local hashes/status summaries and may be removed after final review; they are not canonical evidence.
