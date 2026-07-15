# Evidence: Pi agent-end structural trace

## Scope

This capsule records validation of the bounded, opt-in Pi `agent_end` structural trace and one fresh source-linked reproduction of the post-judgement capture-gate path in `/home/lazydino/dev/lazy-harness`.

In scope: default-off/privacy/bounds/fail-open regression coverage, canonical runtime-path resolution, and a fresh Pi turn ending with a complete seven-layer `Discovery capture` judgement.

Out of scope: changing capture-helper thresholds, changing continuation semantics, proving the historical session's exact stale/queued/runtime cause, downstream sync, and application-source changes.

## Environment

- Date: 2026-07-14
- Host/source root: `/home/lazydino/dev/lazy-harness`
- Branch: `main`
- Baseline `HEAD`: `c7c3d61b876273ddc78a41fb16171b8187328a7b` with the trace seam still uncommitted
- Pi package: source-linked with `pi -e "$PWD/packages/lazy-harness-pi"`
- Trace activation: `LAZY_PI_AGENT_END_TRACE=1`
- Successful retry runtime root: `/tmp/lazy-pi-agent-end-live-retry.aVq5Oa`

## Commands

```bash
python3 -m py_compile .lazy-harness/scripts/self-test.py
bun build packages/lazy-harness-pi/extensions/lazy-harness/index.ts \
  --target=bun \
  --external @earendil-works/pi-coding-agent \
  --external typebox \
  --outfile=/tmp/lazy-harness-pi-index.js

python3 - <<'PY'
import importlib.util
from pathlib import Path
p = Path('.lazy-harness/scripts/self-test.py').resolve()
spec = importlib.util.spec_from_file_location('lazy_self_test', p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.check_pi_package_layout_and_contract()
PY

.lazy-harness/bin/lazy test

LAZY_PI_AGENT_END_TRACE=1 \
LAZY_RUNTIME_ROOT=/tmp/lazy-pi-agent-end-live-retry.aVq5Oa \
pi -e "$PWD/packages/lazy-harness-pi" -p \
  '<controlled read-only STOP-shaped prompt requiring map/read and one complete seven-layer Discovery capture judgement>'
```

The trace row was inspected at:

```text
/tmp/lazy-pi-agent-end-live-retry.aVq5Oa/logs/pi-agent-end-trace.jsonl
```

## Results

- Focused Pi package contract: passed.
- Full framework self-test: `ran=85`, `skipped=0`.
- Fake runtime proved:
  - trace is default-off;
  - explicit and canonical `runtime_paths.py` placement work;
  - an unwritable trace root does not prevent one queued `followUp`;
  - a 16-part content shape retains 12 kind entries plus total/truncation metadata;
  - the trace file retains exactly the newest 50 rows;
  - raw conversation prose, tool arguments/results, and advisory prose are absent.
- The first live launch used quiet auto-exit and terminated before `agent_end`; it produced no trace row and is not treated as evidence about gate behavior.
- The retry exited normally and produced one `pi-agent-end-trace/v1` row:
  - `messageCount=9`, `messageShapesTruncated=false`;
  - assistant projection present, `605` UTF-8 bytes, 16-character fingerprint;
  - last-user projection present, `592` UTF-8 bytes, 16-character fingerprint;
  - recent tool names: `bash`, `bash`, `read`;
  - hook status `0`, no signal/error, empty stdout/stderr;
  - advisory absent.
- The fresh assistant turn ended with all seven required judgement buckets and received no capture-gate continuation.

## Interpretation

High confidence: the current source-linked Pi adapter projects both assistant and user text into the completion payload, and the current helper stays silent for the controlled complete seven-layer judgement. The post-fix recurrence does not reproduce in this fresh session.

This rules out a deterministic failure of the current source path for this case. It does **not** prove which historical condition caused the earlier repeat; stale loaded extension code, queued advisory state, or runtime/session skew remain plausible. No helper-threshold or continuation remediation is justified by this trace alone.

After review, the user selected **Close current remediation**: retain the historical occurrence and this evidence, supersede the active cause candidate without promoting a cause, and make no threshold/continuation change. The user separately selected **Keep deferred** for the 37 legacy-schema graph rows; that migration remains outside this work unit.

## Reproduce

1. Start from the source checkout and keep the trace seam loaded directly with `pi -e packages/lazy-harness-pi`.
2. Set a new `LAZY_RUNTIME_ROOT` and `LAZY_PI_AGENT_END_TRACE=1`.
3. Run one read-only prompt that satisfies map-first traversal and ends with explicit DDD/SDD/BDD/TDD/ADR/SSOT/Planning judgements.
4. Let `pi -p` exit normally; do not use quiet auto-kill.
5. Inspect only the structural row under `$LAZY_RUNTIME_ROOT/logs/pi-agent-end-trace.jsonl`.
6. Confirm `hook.status=0`, empty hook stdout, and `advisory.present=false`.

## Related records

- `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`
- `.lazy-harness/tests/capture-gate-false-positive.md`
- `.lazy-harness/spec/platform/pi-agent-package.md`
- `.lazy-harness/tests/pi-agent-package.md`
- `.lazy-harness/spec/platform/runtime-and-shared-state.md`
- `.lazy-harness/ssot/runtime-and-shared-state.md`
- `.lazy-harness/planning/analysis-discovery-capture-backlog.md`
- `.lazy-harness/knowledge/candidates.jsonl`
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts`
- `.lazy-harness/scripts/self-test.py`

## Retention / privacy

This capsule stores summarized structural evidence only. It contains no raw assistant response, raw user prompt, raw tool arguments/results, credentials, personal data, or unrelated product data. The runtime trace also contains only bounded shapes, byte counts, names, statuses, and fingerprints. The `/tmp` runtime roots are non-canonical and may be pruned after review; this capsule is the durable privacy-reviewed summary.
