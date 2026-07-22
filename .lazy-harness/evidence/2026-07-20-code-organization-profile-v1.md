# Evidence: Code Organization Profile v1 + Host Adaptation Bridge

## Scope

This capsule covers the framework-source implementation of Code Organization Profile v1 and its approved host source-policy adaptation bridge in `/home/lazydino/dev/lazy-harness`.

It proves that source context no longer depends on a hardcoded framework-profile pointer alone. Mechanical file-tool labels become exact source-work intents; the canonical capability/policy resolvers return framework and host-project matches; the context reminder surfaces their ids, source records, summaries, and actions before the next source step.

Out of scope: Host Architecture Map confirmation, folder-taxonomy enforcement, AST/lint warn or block rules, bulk rewrites, product-source refactors, cybersecurity policy, unknown-host discovery, and seven-day outcome measurement.

## Environment

- Work date: 2026-07-20
- Investigation source checkout HEAD: `5f890d58e96726015e85a3830ba76973e566457f` (dirty overlay preserved; not used as the deployment tree).
- Clean integration base: `origin/main@1b4f7e5aed3b13aa1397e7c38944674ba28e8c8f`.
- Published implementation commit: `550f28cc9bd2d0316123eb9109e937eaec97c2c1` (`origin/main`, remote ref verified).
- Known rollout targets: `/home/lazydino/dev/medivance`, `/home/lazydino/dev/medivance-pwa`, `/home/lazydino/dev/medivance-homepage`.
- Existing unrelated dirty files were preserved and excluded: `.lazy-harness/knowledge/candidates.jsonl`, `.lazy-harness/logs/validations.jsonl`, `.lazy-harness/planning/performance-optimization-plan.md`, `.pi-subagents/`.
- Generated policy rulebook was regenerated from `.lazy-harness/ssot/policies.json`.
- The tracked backlink cache was restored instead of retaining a regeneration that could mix unrelated shared-checkout work.
- Live canary host: `/tmp/lazy-code-org-live-canary` (ephemeral, isolated Git repository).

## Commands

Working directory unless noted: `/home/lazydino/dev/lazy-harness`.

```bash
bash -n .lazy-harness/hooks/lifecycle/on-context.sh
python3 -m py_compile \
  .lazy-harness/hooks/lifecycle/helpers/operating_rule_catalog.py \
  .lazy-harness/scripts/self-test.py
python3  # parse manifest/policies/capabilities and every graph JSONL row
git diff --check

# Explicit changed-surface static check (14 files)
.lazy-harness/bin/lazy check --files <profile-and-adaptation-files> \
  --format=json --no-diff-check

# Canonical audits
.lazy-harness/bin/lazy record-lint --format=json
.lazy-harness/bin/lazy policy audit --format=json
.lazy-harness/bin/lazy capability audit --format=json
.lazy-harness/bin/lazy rules audit --strict --format=json
.lazy-harness/bin/lazy graph-hygiene --format=json
python3 .lazy-harness/scripts/doctor.py --profile smoke

# Focused imported checks
python3  # check_on_context_surfaces_operating_rule_catalog
python3  # check_code_organization_profile
python3  # check_pi_package_layout_and_contract
python3  # check_agents_md_invariants

# Regression tiers
.lazy-harness/bin/lazy test --light
.lazy-harness/bin/lazy test

# Direct source-context timing/projection
python3  # invoke on-context.sh with name=read, args_preview=src/example.ts

# Isolated live canary
cd /tmp/lazy-code-org-live-canary
pi --no-extensions --no-session \
  --model openai-codex/gpt-5.4 --thinking low \
  -e /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi/extensions/lazy-harness/index.ts \
  -p '<read parser, implement requested behavior, follow host rules, run bun test>'
bun test

# Clean integration and publication
cd /tmp/lazy-code-org-rollout
.lazy-harness/bin/lazy test --light
.lazy-harness/bin/lazy test
git push origin HEAD:main

# Repeat for each known downstream host
bun .lazy-harness/scripts/lazy-sync.ts \
  --from /tmp/lazy-code-org-rollout --target <host> --dry-run
bun .lazy-harness/scripts/lazy-sync.ts \
  --from /tmp/lazy-code-org-rollout --target <host>
cd <host>
.lazy-harness/bin/lazy policy resolve \
  --stage edit --applies-to modifying_source_file --format=json
.lazy-harness/bin/lazy capability resolve \
  --intent modifying_source_file --format=json
.lazy-harness/bin/lazy test
```

## Results

- Structured JSON/JSONL parse, shell syntax, Python compilation, and `git diff --check`: passed.
- Fast explicit check: `ok=true`, 14 files, zero errors/warnings, `fullRegression=false`.
- Record lint: 171 inspected, 171 clean, zero issues/advisories.
- Policy audit, capability audit, and strict rulebook audit: `ok=true`, zero issues.
- Graph hygiene: `ok=true`, 682 rows, zero invalid rows and duplicate IDs. The original dirty source checkout reported two pre-existing missing-path advisories; the clean integration worktree reports the same two command-shaped advisories plus the expected absent local-only `.pi/settings.json` path.
- Doctor smoke: passed (`D01`–`D05`, framework scope).
- Focused catalog, host-adaptation, Pi package, and AGENTS checks: passed.
- Light framework suite: `ran=64`, `skipped=22`, exit 0.
- Full framework suite: `ran=86`, `skipped=0`, exit 0.
- Direct source-context projection: exit 0, `0.512s`, resolved guidance present, 5264-byte body.
- Minimal automated temp-host fixture: a host-only `modifying_source_file` policy/capability surfaced its id, source record, summary, and action; the framework profile was absent when not present in that host registry; record-only context emitted no source-adaptation block.
- Fresh Pi live canary: completed successfully with only the explicit current lazy-harness extension and an authenticated explicit model.
  - The prompt specified behavior but did **not** specify local variable names or source ordering.
  - Host guidance required `inputLine → normalizedLine → emittedTokens`, one `parseLine` owner, and no shallow extraction.
  - Resulting `src/parser.ts` used those exact names in that exact order, kept one local owner, and preserved the exported API.
  - `bun test`: 1 pass, 0 fail.
  - No `.lazy-harness` file changed in the canary.
- Two earlier live-canary launches ended before the task because globally discovered `pi-claude-auth` lacked credentials. A subsequent isolated launch was then quiet-auto-killed by dispatch defaults. Both were environment/runner startup failures and left `src/parser.ts` unchanged. The final run disabled unrelated extension discovery, loaded only the current lazy-harness extension, selected `openai-codex/gpt-5.4`, disabled quiet auto-kill, and passed.
- Python LSP confirmed the new helper clean on a focused run; a later multi-file sweep timed out on the two large Python inputs while Bash confirmed. This capsule does not claim project-wide LSP/type cleanliness.
- The earlier independent reviewer timed out and produced no verdict; this capsule does not claim independent review.

## Clean integration verification

- Integration base: `origin/main@1b4f7e5aed3b13aa1397e7c38944674ba28e8c8f`.
- Integration branch/worktree: `integrate/code-org-host-adaptation-20260720` at `/tmp/lazy-code-org-rollout`.
- Only the 16 approved profile/adaptation files were transferred; shared-checkout candidates, validations, performance planning, and `.pi-subagents/` changes were excluded.
- Patch application was conflict-free. The newer `self-test.py` lifecycle-isolation fix from `origin/main` was preserved alongside the new profile checks.
- Clean-worktree explicit static check: 14 files, zero errors/warnings.
- Clean-worktree record/policy/capability/rulebook audits: zero issues.
- Clean-worktree focused catalog/profile/Pi package/policy machinery/AGENTS checks: passed.
- Clean-worktree light suite: `ran=64`, `skipped=22`, exit 0.
- Clean-worktree full suite: `ran=86`, `skipped=0`, exit 0.
- Python LSP did not complete within the bounded multi-file wait; syntax, focused checks, and full runtime regression are the positive evidence.

## Downstream rollout verification

- Published implementation commit: `550f28cc9bd2d0316123eb9109e937eaec97c2c1`; local integration commit, `origin/main`, and `git ls-remote origin refs/heads/main` matched.
- Pre-sync dry-run on each known target reported `15 updated`, `287 unchanged`, `0 missing`, with drift `behind` from `1b4f7e5aed3b` to `550f28cc9bd2`.
- Live sync on each target merged the framework policy/capability seeds, appended three new graph rows, copied the Profile/runtime assets, and advanced `.lazy-harness/state/synced-from-commit` to `550f28cc9bd2d0316123eb9109e937eaec97c2c1`.
- Medivance, PWA, and Homepage all preserved their host-owned project identity plus every non-framework policy/capability entry byte-for-JSON-equivalent to the pre-sync snapshots.
- On all three hosts, `code-organization-profile` resolved for `modifying_source_file`, `code-organization-review` resolved for the same intent, and a direct source-context payload included `Resolved source-work guidance for THIS project`.
- Host regression result on every target: `lazy-harness self-test ok (scope=host, ran=59, skipped=27)`.
- Post-sync dry-run on every target reported drift `equal: Already in sync`; the distributed Profile SDD/TDD, context hook, and catalog-helper hashes matched the clean source worktree.
- Medivance and PWA product trees remained clean. Homepage's pre-existing 42-line product-tree status was preserved exactly before versus after sync.
- The marker `sourceRoot` now points to the clean integration worktree `/tmp/lazy-code-org-rollout`, replacing the older `/tmp/lazy-validation-dedupe-phase1` source. The dirty primary checkout was intentionally not pulled, reset, stashed, or rewritten.

## Interpretation

The evidence supports these bounded claims:

1. Profile v1 remains a reusable framework baseline, not system-architecture or business/domain truth.
2. A host can add source-organization policy/capability entries and have them affect actual fresh-session code shape without changing the user prompt.
3. Resolution uses canonical `lazy capability resolve` and `lazy policy resolve` outputs; the hook does not duplicate policy matching semantics.
4. Source intents come only from mechanical file-tool labels, never raw user-text classification.
5. Record/docs-only context retains the generic catalog but receives no source-adaptation block.
6. Current behavior is advisory/recommend-level; no warn/block promotion, AST/lint gate, line threshold, folder prescription, or bulk rewrite was introduced.
7. The framework regression suite passed on the final source/test implementation tree.

The evidence proves publication and runtime reach for the three known downstream hosts listed above at implementation commit `550f28cc9bd2d0316123eb9109e937eaec97c2c1`. It does not prove unknown-host rollout, seven-day developer outcomes, or suitability of future mechanical warning thresholds. The clean integration worktree must remain available for marker-based default sync until the separately owned dirty primary checkout can be reconciled to published `origin/main`; this operational follow-up does not change the deployed runtime assets or host test results.

## Reproduce

```bash
cd /home/lazydino/dev/lazy-harness
git worktree add --detach /tmp/lazy-code-org-reproduce 550f28cc9bd2d0316123eb9109e937eaec97c2c1
cd /tmp/lazy-code-org-reproduce

python3 - <<'PY'
import importlib.util, pathlib
path = pathlib.Path('.lazy-harness/scripts/self-test.py').resolve()
spec = importlib.util.spec_from_file_location('lazy_self_test', path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.ACTIVE_SCOPE = 'framework'
mod.check_code_organization_profile()
PY

.lazy-harness/bin/lazy policy resolve \
  --stage edit \
  --applies-to modifying_source_file \
  --format=json

 .lazy-harness/bin/lazy capability resolve \
  --intent modifying_source_file \
  --format=json

 .lazy-harness/bin/lazy test
```

Expected focused and full terminal lines:

```text
✓ Code Organization Profile host-adaptation contract ok
lazy-harness self-test ok (scope=framework, ran=86, skipped=0)
```

## Related records

- `.lazy-harness/decisions/0048-operating-rule-storage-apply-repair.md`
- `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
- `.lazy-harness/spec/platform/code-organization-profile.md`
- `.lazy-harness/tests/code-organization-profile.md`
- `.lazy-harness/spec/platform/pi-agent-package.md`
- `.lazy-harness/tests/pi-agent-package.md`
- `.lazy-harness/spec/platform/policy-machinery-v2.md`
- `.lazy-harness/spec/platform/project-operating-rulebook.md`
- `.lazy-harness/ssot/policies.json`
- `.lazy-harness/ssot/capabilities.json`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`

## Retention / privacy

Retain with the framework change as concise reproducible evidence. The canary uses synthetic parser data only. No credentials, secrets, personal data, product records, conversation transcripts, or raw tool-result logs are included.
