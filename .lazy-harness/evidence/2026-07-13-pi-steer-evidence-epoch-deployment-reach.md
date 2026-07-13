# Evidence: Pi/OMP steer evidence epoch deployment reach

## Scope

This capsule records commit, push, sync, and deployment-reach verification for SCR-702 Pi/OMP mid-turn steer evidence epochs.

- Source commit: `1bfcae8665c892c535de9d500ab534a499777d25` (`Harden steer read-debt evidence epochs`).
- User authorization: commit, push, and sync to all initialized downstream projects on 2026-07-13.
- Corrected deployment topology after user review: 60 logical initialized host/worktree paths resolve to 6 physical `.lazy-harness` installations across 5 git repository/worktree families; 54 of the 60 logical paths use a `.lazy-harness` symlink.
- Verification unit selected by the user: all 6 physical installations, plus logical reach through all 60 entrypoints.

This capsule does not describe 60 independent framework installations. Repeated sync calls through symlinked worktrees reached the same physical harness targets and are reported as redundant logical-path invocations.

## Environment

- Date: 2026-07-13
- Source root: `/home/lazydino/dev/lazy-harness`
- Source branch: `main`
- Remote: `origin/main`
- Physical harness targets:
  - `/home/lazydino/dev/beloaclinic/.lazy-harness`
  - `/home/lazydino/dev/goedamjip-pipeline/.lazy-harness`
  - `/home/lazydino/dev/medivance/.lazy-harness`
  - `/home/lazydino/dev/medivance-homepage/.lazy-harness`
  - `/home/lazydino/dev/medivance-homepage.admin-members/.lazy-harness`
  - `/home/lazydino/dev/medivance-pwa/.lazy-harness`
- Logical grouping by physical target: 35 Medivance paths, 20 Medivance Homepage paths, 2 Medivance PWA paths, and three single-path targets.
- Transient detailed logs (not retained in Git): `/tmp/lazy_steer_sync_results.jsonl`, `/tmp/lazy_steer_host_topology.json`, `/tmp/lazy_steer_deployment_verify.json`, `/tmp/lazy_steer_host_tests.json`.

## Commands

Source commit and remote verification:

```bash
git commit -m "Harden steer read-debt evidence epochs" ...
git push origin main
git ls-remote origin refs/heads/main
```

Initialized logical host enumeration followed the previously validated rollout definition: first-level `/home/lazydino/dev/*` directories, excluding the source checkout and path-only backups, with both `.lazy-harness/bin/lazy` and `.lazy-harness/state/synced-from-commit` present.

Each logical path was initially synchronized with:

```bash
<host>/.lazy-harness/bin/lazy sync --force
```

After the user noted symlink prevalence, topology was recomputed using:

```text
Path("<host>/.lazy-harness").is_symlink()
Path("<host>/.lazy-harness").resolve(strict=True)
git -C <host> rev-parse --path-format=absolute --git-common-dir
```

Deployment reach was then checked on each unique physical target:

- `state/synced-from-commit.syncedFromCommit == 1bfcae8665c892c535de9d500ab534a499777d25`
- `spec/platform/pi-agent-package.md` contains `toolCallEpochsByRoot`
- `spec/platform/search-read-debt-contract.md` contains older-epoch result exclusion
- `behavior/llm-owned-record-retrieval.md` contains `toolResultBelongsToCurrentEvidenceEpoch`
- `scripts/self-test.py` contains the late pre-steer result regression
- `knowledge/graph.jsonl` contains both SCR-702 implementation/test graph ids

Logical reach checked the resolved physical harness, marker, and regression content through all 60 worktree entrypoints.

Host/runtime checks:

```bash
<physical-host>/.lazy-harness/bin/lazy test --light
.lazy-harness/bin/lazy pi list --format=json
.lazy-harness/bin/lazy pi smoke --format=json
LAZY_AGENT_RUNTIME=omp .lazy-harness/bin/lazy omp list --format=json
LAZY_AGENT_RUNTIME=omp .lazy-harness/bin/lazy omp smoke --format=json
```

## Results

- Source commit created: `1bfcae8`.
- Push succeeded: remote `refs/heads/main` resolved to full commit `1bfcae8665c892c535de9d500ab534a499777d25`.
- Initial logical-path sync calls: `60/60` succeeded, `0` failed.
- Initial sync-call summed duration: `277.532s`; this was redundant because symlinked worktrees repeatedly targeted the same physical harness directories.
- Topology:
  - logical initialized paths: `60`
  - `.lazy-harness` symlink paths: `54`
  - physical harness installations: `6`
  - git repository/worktree families: `5`
- Physical deployment verification: `6/6` passed with the expected marker and all checked content/graph facts.
- Logical reach verification: `60/60` entrypoints resolved to the expected physical target and exposed the expected marker/regression content.
- Physical-host light self-test: `6/6` passed.
- Pi package list: the user and project package surfaces resolve to `/home/lazydino/dev/lazy-harness/packages/lazy-harness-pi`.
- OMP plugin list: `@lazy-dinosaur/lazy-harness-pi@0.1.0` is installed.
- Pi one-run package smoke: exit `0`.
- OMP one-run package smoke: exit `0`.
- Verification failures: `0`.

## Interpretation

SCR-702 is committed, pushed, and reachable from every currently initialized logical host entrypoint. The correct independent-installation claim is **6 physical harness deployments**, not 60. The 60 logical paths are mostly symlinked git worktrees that share those installations.

The user correction exposed avoidable rollout churn: enumerating logical worktrees before realpath deduplication caused 60 sync commands where 6 physical syncs were sufficient. Future all-host rollouts should:

1. enumerate logical initialized entrypoints;
2. group them by resolved physical `.lazy-harness` target;
3. sync each physical target once;
4. verify each physical target once;
5. separately verify that all logical entrypoints resolve to a verified target.

This preserves deployment-reach confidence while eliminating redundant worktree sync calls and avoiding inflated “project count” claims.

## Reproduce

```bash
cd /home/lazydino/dev/lazy-harness
git ls-remote origin refs/heads/main
.lazy-harness/bin/lazy pi list --format=json
.lazy-harness/bin/lazy pi smoke --format=json
LAZY_AGENT_RUNTIME=omp .lazy-harness/bin/lazy omp list --format=json
LAZY_AGENT_RUNTIME=omp .lazy-harness/bin/lazy omp smoke --format=json
```

Re-enumerate initialized logical paths, group by `Path(<host>/.lazy-harness).resolve(strict=True)`, then run the marker/content checks above on each unique physical target. Verify each logical path resolves to one of those verified targets.

## Related records

- `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- `.lazy-harness/spec/lazy-sync-drift-detection.md`
- `.lazy-harness/spec/platform/host-root-resolution.md`
- `.lazy-harness/spec/platform/pi-agent-package.md`
- `.lazy-harness/spec/platform/search-read-debt-contract.md`
- `.lazy-harness/tests/pi-agent-package.md`
- `.lazy-harness/tests/pre-action-search-evidence-guard.md`
- `.lazy-harness/planning/pi-agent-plugin-adapter.md`
- `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`
- `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- `.lazy-harness/evidence/2026-07-13-pi-steer-evidence-epoch-source-validation.md`
- Source commit: `1bfcae8665c892c535de9d500ab534a499777d25`

## Retention / privacy

Retain this summarized capsule with the framework source. Detailed `/tmp` logs are transient and may be deleted. No credentials, tokens, raw transcripts, personal data, or downstream product data are included. Local checkout names are retained only to identify deployment topology and reproduce physical-target grouping.
