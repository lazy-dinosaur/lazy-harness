# Evidence: Seam-preserving lifecycle validation deduplication Phase 1

## Scope

Validate a test-only reduction of duplicate lifecycle fixture execution in the lazy-harness framework source checkout. Phase 1 changes self-test ownership only: one targeted real-payload candidate run replaces fixture intake's nested complete parity matrix, lifecycle integration removes only option-gate, record-before-session-history, and read-only repetitions, and retained stateful seams run in one isolated temporary host.

Intentionally out of scope: production hooks/helpers, CLI or result semantics, runtime enforcement, fixture definitions, validation evidence reuse, parallelism, downstream product tests, host sync, and legacy graph migration.

## Environment

- Date: 2026-07-15
- Host/source checkout: `/home/lazydino/dev/lazy-harness`
- Isolated worktree: `/tmp/lazy-validation-dedupe-phase1`
- Branch: `validation-dedupe-phase1`
- Base commit: `5f890d58e96726015e85a3830ba76973e566457f`
- Canonical matrix: 12 lifecycle fixtures
- Baseline from a clean temporary repository: full `142.159s`; intake `25.486s`; parity `23.062s`; integration `19.017s`; response telemetry `17.954s`.
- Final validation date: 2026-07-20 UTC.

## Commands

Focused validation contract:

```bash
cd /tmp/lazy-validation-dedupe-phase1
python3 -m py_compile .lazy-harness/scripts/self-test.py
git diff --check
rm -f /tmp/lazy-phase1-hook-timing-escape.jsonl /tmp/lazy-phase1-compare-escape.jsonl
LAZY_HOOK_TIMING=1 LAZY_HOOK_TIMING_LOG=/tmp/lazy-phase1-hook-timing-escape.jsonl \
LAZY_RESPONSE_COMPLETED_COMPARE=1 LAZY_RESPONSE_COMPLETED_COMPARE_LOG=/tmp/lazy-phase1-compare-escape.jsonl \
python3 - <<'PY'
import importlib.util
from pathlib import Path
path = Path('.lazy-harness/scripts/self-test.py').resolve()
spec = importlib.util.spec_from_file_location('self_test', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.check_lifecycle_hook_integration()
PY
test ! -e /tmp/lazy-phase1-hook-timing-escape.jsonl
test ! -e /tmp/lazy-phase1-compare-escape.jsonl
candidate_before=$(sha256sum .lazy-harness/knowledge/candidates.jsonl | awk '{print $1}')
env -u LAZY_HOOK_TIMING -u LAZY_HOOK_TIMING_LOG \
    -u LAZY_RESPONSE_COMPLETED_COMPARE -u LAZY_RESPONSE_COMPLETED_COMPARE_LOG \
python3 - <<'PY'
import runpy, time
ns = runpy.run_path('.lazy-harness/scripts/self-test.py', run_name='lazy_phase1_focused_final')
for name in ('check_lifecycle_fixture_intake_cli', 'check_lifecycle_hook_integration', 'check_lifecycle_parity_runner'):
    started = time.perf_counter()
    ns[name]()
    print(name, round(time.perf_counter() - started, 3))
PY
candidate_after=$(sha256sum .lazy-harness/knowledge/candidates.jsonl | awk '{print $1}')
test "$candidate_before" = "$candidate_after"
.lazy-harness/bin/lazy check --files .lazy-harness/scripts/self-test.py,.lazy-harness/planning/performance-optimization-plan.md,.lazy-harness/tests/lifecycle-compare-fidelity.md,.lazy-harness/spec/platform/hook-performance-measurement.md,.lazy-harness/evidence/2026-07-15-validation-deduplication-phase1.md --format=json
.lazy-harness/bin/lazy record-lint --format=json
```

Final full validation command (explicit external override isolation):

```bash
cd /tmp/lazy-validation-dedupe-phase1
env -u LAZY_RUNTIME_ROOT -u LAZY_SHARED_ROOT \
    -u LAZY_HOOK_TIMING -u LAZY_HOOK_TIMING_LOG \
    -u LAZY_RESPONSE_COMPLETED_COMPARE -u LAZY_RESPONSE_COMPLETED_COMPARE_LOG \
    -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_PREFIX \
    -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES -u GIT_QUARANTINE_PATH \
    LAZY_HOST_ROOT="$PWD" \
    python3 .lazy-harness/scripts/self-test.py --scope framework
```

A Python `time.perf_counter` wrapper measured the exact child command while streaming its combined output. The budget was consumed by this single executed full self-test; no timing retry was made.

## Results

Focused validation passed:

- `python3 -m py_compile .lazy-harness/scripts/self-test.py`: pass;
- `git diff --check`: pass;
- inherited timing/compare output-path escape check: pass; neither explicit `/tmp` sentinel was created;
- review-hardening final `check_lifecycle_fixture_intake_cli`: pass, `3.204s` (baseline `25.486s`, `87.4%` reduction);
- review-hardening final `check_lifecycle_hook_integration`: pass, `16.170s` (baseline `19.017s`, `15.0%` reduction);
- review-hardening final `check_lifecycle_parity_runner`: pass, `33.086s`; success requires `fixtures=12` and `failed=0`;
- review-hardening final three-check total: `52.460s` versus baseline `67.565s` (`22.4%` reduction);
- the unchanged parity check was `43.5%` slower than its `23.062s` baseline under current load; no retry was made;
- an earlier pre-hardening final-tree run measured `35.514s`; it is superseded, not selected over the post-change run;
- source candidate-store SHA-256 before/after: `4526ca6771f8d43c85d89caee659f155937e6f33fea33f354e69b759171eeb02` (unchanged);
- explicit `lazy check`: five changed files, zero errors/warnings;
- record lint: `169/169` clean, zero issues/advisories;
- AST ownership audit and production-path diff check: pass;
- independent final gate review: `PASS`, no blockers;
- timing-wrapper preflight: `/usr/bin/time` was unavailable, so that wrapper exited `127` before Python or any self-test check launched; it is not counted as a full run;
- single executed final full command: exit `0`, `scope=framework`, `ran=85`, `skipped=0`, `82.282s`;
- final wall time versus the `142.159s` clean baseline: `42.1%` lower, reported once as diagnostic evidence without retry;
- Git HEAD before/after: `5f890d58e96726015e85a3830ba76973e566457f`;
- pre/post-run SHA-256 content fingerprint over the five work-unit files: `c33a3ad4d92545ae73336ac79a6e3072c4f653605b3819f40d5fd7bbec545695` (a labeled content digest, not a Git object);
- source candidate-store SHA-256 also remained `4526ca6771f8d43c85d89caee659f155937e6f33fea33f354e69b759171eeb02`.

Deterministic workload evidence:

- fixture intake: 27 complete harness copies → 3;
- canonical parity: unchanged at 24 copies;
- response telemetry fixture: unchanged at one copy;
- one isolated integration host copy is added so source candidate/runtime state is never rewritten;
- minimum lifecycle-heavy total: 52 copies → 29;
- integration: six duplicate chain executions removed while unique stateful seams remain.

Final focused revalidation, fast static/record revalidation, and independent review all passed. The single executed full framework self-test also passed `85/85` with zero skips in `82.282s`; the reviewed five-file input and candidate store were unchanged across the run. Phase 1 validation is complete; the enclosing Git commit/push carries source integration, while downstream host sync remains out of scope.

## Interpretation

Correctness, structural, focused, and full-suite evidence support the seam-preserving design. The sole canonical matrix passed 12/12, retained state/composition seams passed, inherited explicit output paths could not escape the temporary host, and the source candidate store remained byte-identical. The canonical post-change focused run reduced the three checks by `22.4%`; parity itself was slower under that load, so the deterministic 52→29 copy reduction (`44.2%`) and correctness seams remain the primary performance evidence rather than a cherry-picked wall time. The single non-retried full run passed all 85 checks in `82.282s` (`42.1%` below the clean baseline), but whole-suite timing remains diagnostic because prior clean runs varied materially under system load. Validation is complete; this capsule supports the enclosing Git change but does not claim downstream deployment reach.

## Reproduce

1. Check out base commit `5f890d58e96726015e85a3830ba76973e566457f` and measure the baseline commands in an otherwise idle clean worktree.
2. Apply the Phase 1 diff.
3. Run the focused contract above.
4. Confirm intake selects exactly one appended candidate by ID and calls unchanged `run_fixture` once.
5. Confirm TDD/aftershock queues, BDD candidate persistence, `injectJson`, edit-target, and policy-context assertions remain in `check_lifecycle_hook_integration`, and that they run under an isolated temporary host without source-state backup/restore.
6. Run exactly one full framework self-test on the final unchanged input tree; expect 85 checks, zero skips/failures, and do not retry merely for a prettier timing.

## Related records

- `.lazy-harness/planning/performance-optimization-plan.md`
- `.lazy-harness/tests/lifecycle-compare-fidelity.md`
- `.lazy-harness/spec/platform/hook-performance-measurement.md`
- `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`

## Retention / privacy

Keep this capsule with the logical Phase 1 work unit. It contains summarized timing/count evidence and repository paths only. It does not contain raw lifecycle payloads, user/assistant text, credentials, secrets, private transcripts, or product data. Large command logs remain transient and are not copied here.
