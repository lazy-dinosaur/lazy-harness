# TDD — Bounded Validation Governor (`lazy validate`)

Status: active
Layer: TDD
Date: 2026-06-18

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - governor 회귀
- Applies when:
  - running or implementing `lazy validate` and choosing a fast/standard/release plan
  - bounding validation time/budget or caching full-regression evidence
- Must:
  - make validation plans explicit, bounded, and release-gated; the default fast plan skips full regression
  - reject budgets over 3600 seconds and require `--allow-release` or `--dry-run` for release plans
  - reuse cached full-regression evidence only when the regression-relevant evidence key matches
  - ignore evidence-capsule body changes without ignoring source, tests, contracts, policies, graph, or canonical records
  - protect recommend-level guidance that removes `iterating_after_edit`, forbids validation after every micro-edit, batches coherent mutations before one fast checkpoint, limits focused/affected checks to once per changed-behavior batch, and keeps one final standard boundary
  - protect compact green reporting: conversation output is status/count/time while detailed stdout/stderr stays in captured runtime evidence unless failure or explicit request
  - protect bounded process execution, audited resource phases, deterministic output, worker runtime isolation, and `--jobs=1` serial fallback
  - keep validation progress runtime-neutral and capability-aware across Pi, OMP, Jcode, and ordinary foreground callers
  - keep installed-host full regression independent of absent source-only `packages/lazy-harness-pi` paths while still checking those prompt/skill surfaces in the framework source checkout
- Must not:
  - claim full regression from fast static checks instead of `lazy test` execution
  - emit progress to stdout, emit runtime-branded progress prefixes from shared core, or leak auto-mode progress into foreground callers that did not advertise support
  - preserve an `iterating_after_edit` capability/policy trigger or prompt language that implies validation after each individual edit
- Record completion:
  - changes to plans, budgets, or evidence caching update this TDD plus the bounded-validation-governor SDD
- Related records:
  - `.lazy-harness/spec/platform/bounded-validation-governor.md`

## Regression target

`lazy validate` must prevent accidental long-running validation multiplication by making validation plans explicit, bounded, and release-gated.

## Protected fixtures

| Case | Trigger | Expected |
|---|---|---|
| `validate_help` | `.lazy-harness/bin/lazy help` | Help lists `validate [--plan=fast|standard|release]`. |
| `validate_fast_json` | `lazy validate --plan fast --files .lazy-harness/fixtures/project-map-v2/example-node.json --format=json` | Exits 0, reports `bounded: true`, `plan: fast`, one passed fast-static step, and `fullRegression: false`. |
| `validate_release_requires_opt_in` | `lazy validate --plan release --format=json` | Exits non-zero and reports `release plan requires --allow-release or --dry-run`. |
| `validate_release_dry_run` | `lazy validate --plan release --dry-run --format=json` | Exits 0, lists planned release steps, does not execute them, and shows `fullRegression: true` because the plan includes one full test. |
| `validate_budget_cap` | `lazy validate --plan fast --max-seconds=3601 --format=json` | Exits non-zero and reports that budgets over 3600 must be split. |
| `validate_deadline_zero` | `lazy validate --plan fast --max-seconds=0 --format=json` | Exits non-zero without running `lazy check`, step status is `skipped` with `deadline-exhausted`. |
| `validate_progress_auto_quiet` | `lazy validate --plan fast --format=json` without a support advertisement | Stdout remains parseable JSON and stderr contains neither `LAZY_PROGRESS` nor legacy `JCODE_PROGRESS` rows. |
| `validate_progress_advertised` | `LAZY_PROGRESS_SUPPORTED=1 lazy validate --plan fast --format=json` | Stderr contains parseable `LAZY_PROGRESS` rows and no runtime-branded prefix. |
| `validate_progress_on` | `lazy validate --plan fast --progress=on --format=json` | Explicit enable emits `LAZY_PROGRESS` rows even without a support advertisement. |
| `validate_progress_off` | `lazy validate --plan fast --progress=off --format=json` | Stderr contains no progress protocol rows even when support is advertised. |
| `validate_cache_miss_then_hit` | Two `lazy validate --plan standard --format=json` runs with identical regression-relevant fingerprint and isolated `LAZY_RUNTIME_ROOT` | First run stores full-regression evidence, second run reports `evidenceReused: true` and full-regression step status `reused`. |
| `validate_cache_evidence_only` | Classify `.lazy-harness/evidence/**` after a green full run | Evidence capsule body changes remain full-regression-irrelevant while the fast tier still runs. |
| `validate_cache_relevant_change` | Classify source, test, spec, policy, graph, and canonical record paths | Any relevant change remains in the fingerprint and causes a cache miss. |
| `validate_cache_environment_namespace` | Change host-root, dependency, or toolchain fingerprint fields | Evidence key changes; shared runtime cache cannot reuse another host/toolchain's result. |
| `validate_cache_disabled` | `lazy validate --plan standard --evidence-cache=off --format=json` after cache exists | Full-regression step is not `reused`, and `evidenceReused: false`. |
| `validate_cache_runtime_state` | default runtime cache path | Cache is stored under `.lazy-harness/state/validation-evidence-cache.json` or `$LAZY_RUNTIME_ROOT/state/validation-evidence-cache.json`, and the default path is ignored by the active git ignore rules in both source and installed hosts. |
| `validation_orchestration_guidance` | Resolve capability/policy and inspect Pi prompt/commands | Edit loops batch coherent mutations; closure uses one `lazy validate --plan standard`; direct `lazy test` is explicitly fresh/full. |
| `validation_no_micro_edit_loop` | Inspect capability/policy/AGENTS/Pi prompt/test strategy | No validation after individual edits; one checkpoint per coherent batch; focused/affected validation at most once; one final standard boundary. |
| `validation_compact_green_output` | Inspect AGENTS/Pi prompt/governor Markdown behavior | Green completion is summarized as status/count/time; step output remains captured and is surfaced only for failure or explicit request. |
| `validation_installed_host_without_pi_package` | Run the bounded-validation self-test from an installed host root without `packages/lazy-harness-pi` | Distributed `.lazy-harness` surfaces remain required; absent source-only Pi package paths are skipped instead of raising `FileNotFoundError`. In the framework source checkout, both Pi package surfaces remain mandatory. |
| `self_test_parallel_resources` | Run `self-test.py --jobs 4` | Only explicitly audited checks use isolated process phases; fixed-path checks remain serial and output stays in registry order. |
| `self_test_serial_fallback` | Run `self-test.py --jobs 1` | Historical serial fail-fast behavior remains available. |

## Acceptance assertions

1. `lazy validate` dispatches from `.lazy-harness/bin/lazy` to `.lazy-harness/scripts/validation-governor.py`.
2. `fast` is the default plan and does not run full regression.
3. `standard` contains exactly one full-regression step in dry-run output.
4. `release` cannot execute without `--allow-release`.
5. All plans include a total budget and reject `--max-seconds > 3600`.
6. Dry-run output must be available for release plans without starting expensive commands.
7. Full regression claims remain tied to `lazy test` execution or planned full-regression steps, not to fast static checks.
8. Progress uses the shared `LAZY_PROGRESS` stderr protocol. Auto mode is quiet without `LAZY_PROGRESS_SUPPORTED=1`; explicit on emits; explicit off suppresses; stdout JSON remains clean.
9. Cached full-regression evidence can be reused only when the regression-relevant evidence key matches; otherwise validation runs `lazy test`.
10. Evidence capsule edits alone do not invalidate full evidence; executable/canonical changes do.
11. Fast static checks still run when full-regression evidence is reused.
12. Cache disable flags force full-regression execution even when evidence exists.
13. Capability/policy, AGENTS, Pi prompt, skill, and test-strategy surfaces explicitly prohibit validation after each micro-edit, omit `iterating_after_edit`, batch coherent mutations before one fast checkpoint, and keep one final standard boundary.
14. Parallel execution caps workers at four, rejects out-of-range CLI/environment values, uses audited resource phases and isolated worker runtime roots, preserves deterministic output, and keeps serial fallback.
15. Evidence keys bind to resolved host root, dependency manifests/locks, and Python/Bun/Git signatures; uncertainty remains a miss.
16. Installed hosts without `packages/lazy-harness-pi` pass the bounded-validation self-test when all distributed `.lazy-harness` surfaces are valid; framework source checkouts still require the Pi prompt and lazy-test skill guards.

## Implementation map

- Primary files:
  - `.lazy-harness/tests/bounded-validation-governor.md` — this TDD.
  - `.lazy-harness/spec/platform/bounded-validation-governor.md` — SDD contract.
  - `.lazy-harness/tests/test-strategy.xml` — canonical host/framework validation strategy.
  - `.lazy-harness/scripts/validation-governor.py` — implementation.
  - `.lazy-harness/bin/lazy` — CLI dispatch/help.
  - `.lazy-harness/scripts/self-test.py` — regression fixtures plus bounded resource-phase process execution.
  - `.lazy-harness/ssot/capabilities.json` / `.lazy-harness/ssot/policies.json` — orchestration guidance fixtures.
  - `packages/lazy-harness-pi/prompts/lazy-harness.md` / `extensions/lazy-harness/index.ts` — agent prompt and convenience command fixtures.
  - `.lazy-harness/manifests/init-categories.json` — syncs the SDD/TDD and script through Category A.
  - Machine index: `kg_validation_no_micro_edit_loop_20260818`
- Key symbols:
  - `validation-governor.py#main`
  - `validation-governor.py#build_result`
  - `validation-governor.py#plan_steps`
  - `validation-governor.py#emit_progress`
  - `validation-governor.py#workspace_fingerprint`
  - `validation-governor.py#dependency_fingerprint`
  - `validation-governor.py#toolchain_fingerprint`
  - `validation-governor.py#command_signature`
  - `validation-governor.py#is_full_regression_irrelevant_path`
  - `validation-governor.py#evidence_key`
  - `validation-governor.py#cached_step_result`
  - `validation-governor.py#store_step_result`
  - `self-test.py#run_check_captured`
  - `self-test.py#main`
  - `self-test.py#check_bounded_validation_governor_cli`
- Validation commands:
  - `python3 -m py_compile .lazy-harness/scripts/validation-governor.py`
  - `.lazy-harness/bin/lazy validate --plan fast --files .lazy-harness/fixtures/project-map-v2/example-node.json --format=json`
  - `LAZY_PROGRESS_SUPPORTED=1 .lazy-harness/bin/lazy validate --plan fast --files .lazy-harness/fixtures/project-map-v2/example-node.json --format=json`
  - `.lazy-harness/bin/lazy validate --plan fast --progress=on --files .lazy-harness/fixtures/project-map-v2/example-node.json --format=json`
  - `.lazy-harness/bin/lazy validate --plan fast --progress=off --files .lazy-harness/fixtures/project-map-v2/example-node.json --format=json`
  - `.lazy-harness/bin/lazy validate --plan release --dry-run --format=json`
  - `.lazy-harness/bin/lazy validate --plan standard --format=json` with isolated `LAZY_RUNTIME_ROOT` for cache miss/hit coverage
  - `.lazy-harness/bin/lazy validate --plan standard --evidence-cache=off --format=json`
  - `python3 .lazy-harness/scripts/self-test.py --scope host --light --jobs 4`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework --jobs 1`

## Layer completeness

- SDD: `.lazy-harness/spec/platform/bounded-validation-governor.md` owns orchestration, cache, and worker contracts.
- BDD: agent-visible flow explicitly forbids validation after each micro-edit, batches coherent mutations before one fast checkpoint, limits focused checks to once per changed-behavior batch, and keeps one final standard boundary; platform SDD/TDD own this internal agent operation.
- SSOT: `.lazy-harness/ssot/capabilities.json` and `.lazy-harness/ssot/policies.json` remove `iterating_after_edit` and own the canonical no-micro-edit guidance; full regression remains `.lazy-harness/bin/lazy test`.
- ADR: ADR 0016 keeps commit=light/push=full and records bounded intra-run concurrency without a new architectural trade-off.
- DDD: no independent domain vocabulary or business-rule delta.
