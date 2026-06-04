# Lifecycle Compare Dogfood Handoff

Status: active-dogfood-handoff
Date: 2026-05-31
Layer: Planning
Related:
- `.lazy-harness/planning/lifecycle-phase3-readiness-checklist.md`
- `.lazy-harness/planning/capability-registry-implementation-plan.md`
- `.lazy-harness/planning/current-framework-roadmap-snapshot.md`
- `.lazy-harness/spec/platform/hook-performance-measurement.md`

## Purpose

This handoff exists so a future agent can continue without relying on chat history. If the user says something like:

```text
쌓인 자료 확인해줘
compare 로그 봐줘
도그푸드 쌓였는지 봐줘
```

then the agent should read this file first and proceed with the workflow below.

## Current track split

Two tracks were intentionally active in parallel and must not be collapsed:

1. **Track A — Capability Registry**
   - Purpose: discover project-specific capability candidates from real workflow evidence.
   - Current state: source-side read-only `lazy capability candidates` is implemented.
   - Important boundary: do not manually patch downstream Medivance registries as the solution. Medivance/PWA are evidence hosts. Source work belongs in `/home/lazydino/dev/lazy-harness`.
2. **Track B — Lifecycle / response.completed Phase 3**
   - Purpose: safely replace/optimize the response.completed safety-gate hot path.
   - Current state: opt-in engine switch exists, default remains legacy.
   - Current dogfood mode: both Medivance and Medivance PWA are locally wired to `compare` mode.

## Source and host state at handoff creation

Before this handoff record commit:

- Source repo: `/home/lazydino/dev/lazy-harness`
- Source HEAD: `49de79e32a42c426eaf279b5b5db28da005c086f`
- Recent source commits:
  - `49de79e Record persistent compare dogfood wiring`
  - `92df1e5 Record compare dogfood in both hosts`
  - `9bafdc2 Record lifecycle opt-in downstream sync`
  - `1bab3ef Add opt-in response lifecycle engine`
  - `7c4bc00 Record downstream capability sync`
  - `878a92c Add read-only capability candidate detection`

After committing this handoff record, source HEAD will advance. The committer must sync both downstream markers once more after the commit.

## Dogfood host configuration

Both hosts are expected to be latest relative to the source HEAD and locally wired for compare mode:

### `/home/lazydino/dev/medivance`

Expected local/private Jcode config:

```toml
[[hooks.commands]]
event = "response.completed"
tool = "*"
command = ".jcode/hooks/response-completed-compare.sh"
blocking = false
timeout_ms = 5000
```

Expected wrapper:

```bash
#!/usr/bin/env bash
# Local dogfood wrapper: run lazy-harness response.completed in compare mode.
set -euo pipefail
export LAZY_RESPONSE_COMPLETED_ENGINE="${LAZY_RESPONSE_COMPLETED_ENGINE:-compare}"
export LAZY_RESPONSE_COMPLETED_COMPARE_LOG="${LAZY_RESPONSE_COMPLETED_COMPARE_LOG:-$LAZY_RUNTIME_ROOT/logs/lifecycle-compare.jsonl}"
exec .lazy-harness/hooks/lifecycle/on-response-completed.sh
```

Expected log path:

```text
/home/lazydino/dev/medivance/$LAZY_RUNTIME_ROOT/logs/lifecycle-compare.jsonl
```

At handoff creation this host had 4 compare rows, all matching.

### `/home/lazydino/dev/medivance-pwa`

Same expected local/private Jcode config and wrapper as Medivance.

Expected log path:

```text
/home/lazydino/dev/medivance-pwa/$LAZY_RUNTIME_ROOT/logs/lifecycle-compare.jsonl
```

At handoff creation this host had 3 compare rows, all matching.

## Why `.jcode/config.toml` is user-owned in both hosts

A normal `lazy-sync --force` refreshes generated `.jcode/config.toml` and would revert the response.completed hook command to:

```toml
command = ".lazy-harness/hooks/lifecycle/on-response-completed.sh"
```

That would silently disable compare-mode dogfood. Therefore both dogfood hosts intentionally have local user-owned `.jcode/config.toml` overrides with the generated marker removed. `lazy-sync` should report:

```text
✓ keep user-owned <host>/.jcode/config.toml
```

Do not “repair” this back to generated config unless the goal is to stop compare dogfood.

## Compare log meaning

Each row in `$LAZY_RUNTIME_ROOT/logs/lifecycle-compare.jsonl` should be sanitized metadata only. It should not contain raw user message bodies.

Fields to inspect:

- `bodyHashMatch`
- `helperMatch`
- `legacyOutputEmitted`
- `orchestratorOutputEmitted`
- `legacyHelper`
- `orchestratorHelper`
- `orchestratorExitCode`
- `orchestratorSandbox`
- `legacyBodyBytes`
- `orchestratorBodyBytes`

A healthy row usually has:

```json
{
  "bodyHashMatch": true,
  "helperMatch": true,
  "orchestratorExitCode": 0,
  "orchestratorSandbox": true
}
```

Rows where both legacy and orchestrator emit no output have `legacyBodyHash=null` and `orchestratorBodyHash=null`; `bodyHashMatch=true` is still expected.

## Next-session workflow: when user asks to inspect accumulated data

### 1. Read records first

Read at minimum:

```bash
sed -n '1,260p' .lazy-harness/planning/lifecycle-compare-dogfood-handoff.md
sed -n '455,620p' .lazy-harness/planning/lifecycle-phase3-readiness-checklist.md
sed -n '697,790p' .lazy-harness/planning/capability-registry-implementation-plan.md
```

### 2. Confirm source and host markers

```bash
cd /home/lazydino/dev/lazy-harness
git rev-parse HEAD

for host in /home/lazydino/dev/medivance /home/lazydino/dev/medivance-pwa; do
  echo "## $host"
  cd "$host"
  python3 - <<'PY'
import json
print(json.load(open('.lazy-harness/state/synced-from-commit'))['syncedFromCommit'])
PY
  git status --short
  grep -n 'response.completed\|response-completed-compare' .jcode/config.toml
  test -x .jcode/hooks/response-completed-compare.sh && echo wrapper-ok
 done
```

If marker is behind source, run `lazy-sync --force` from source to host, then recheck that `.jcode/config.toml` remains user-owned compare wiring.

### 3. Summarize compare logs

Until a source CLI exists, use this ad hoc summary:

```bash
python3 - <<'PY'
import json
from pathlib import Path
hosts = [
    ('medivance', Path('/home/lazydino/dev/medivance/$LAZY_RUNTIME_ROOT/logs/lifecycle-compare.jsonl')),
    ('medivance-pwa', Path('/home/lazydino/dev/medivance-pwa/$LAZY_RUNTIME_ROOT/logs/lifecycle-compare.jsonl')),
]
for name, path in hosts:
    rows=[]
    invalid=0
    if path.exists():
        for line in path.read_text(errors='replace').splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                invalid += 1
    mismatches=[]
    failures=[]
    for i,row in enumerate(rows, 1):
        bad = []
        if row.get('bodyHashMatch') is not True:
            bad.append('bodyHashMatch')
        if row.get('helperMatch') is not True:
            bad.append('helperMatch')
        if row.get('legacyOutputEmitted') != row.get('orchestratorOutputEmitted'):
            bad.append('outputEmitted')
        if row.get('orchestratorExitCode') not in (0, None):
            bad.append('orchestratorExitCode')
        if row.get('orchestratorSandbox') is not True:
            bad.append('orchestratorSandbox')
        if bad:
            mismatches.append((i, bad, row))
        if row.get('orchestratorExitCode') not in (0, None):
            failures.append((i, row))
    print(f'## {name}')
    print(f'path={path}')
    print(f'rows={len(rows)} invalid={invalid} mismatches={len(mismatches)} failures={len(failures)}')
    if rows:
        print('first=', rows[0].get('timestamp'))
        print('last =', rows[-1].get('timestamp'))
    for i,bad,row in mismatches[:10]:
        print('MISMATCH', i, bad, json.dumps(row, ensure_ascii=False)[:1200])
PY
```

### 4. Inspect timing too

Compare-mode adds sandbox orchestrator work, so also inspect timing:

```bash
for host in /home/lazydino/dev/medivance /home/lazydino/dev/medivance-pwa; do
  echo "## $host"
  cd "$host"
  .lazy-harness/bin/lazy hook-timings --format=md --limit=1000 | sed -n '1,120p'
 done
```

Important components:

- `lifecycle-orchestrator`
- `hook-total`
- individual legacy helpers

### 5. Optional capability candidate check

Capability is a separate track. Do not let lifecycle readiness imply capability promotion.

```bash
for host in /home/lazydino/dev/medivance /home/lazydino/dev/medivance-pwa; do
  echo "## $host"
  cd "$host"
  .lazy-harness/bin/lazy capability candidates --format=json
 done
```

Expected current candidates:

- Medivance:
  - `medivance-baseline-app-validation`
  - `medivance-release-workflow-skill-action-coverage`
- Medivance PWA:
  - `medivance-pwa-baseline-app-validation`

These are read-only suggestions. Do not auto-apply.

## Decision criteria for next Track B step

Do not automatically move to `orchestrator` mode. Report evidence first and ask/receive explicit approval.

Recommended readiness signal for considering `compare → orchestrator` opt-in dogfood:

- Medivance primary evidence has enough real rows to be meaningful.
- `invalid=0` in compare logs.
- `bodyHashMatch=false` count is 0.
- `helperMatch=false` count is 0.
- `legacyOutputEmitted != orchestratorOutputEmitted` count is 0.
- `orchestratorExitCode != 0` count is 0.
- No raw sensitive content appears in compare logs.
- `hook-total` and `lifecycle-orchestrator` timings are acceptable or at least understood.

PWA should also be checked, but Medivance remains the primary dogfood signal unless the user says PWA has resumed active development.

If all checks pass, the next option gate should be:

A. Continue compare dogfood for more rows
B. Enable `orchestrator` opt-in in Medivance only
C. Enable `orchestrator` opt-in in both Medivance and PWA
D. Build `lazy lifecycle-compare-summary` CLI first
E. User-defined

Recommended next implementation before mode escalation:

```text
Build `lazy lifecycle-compare-summary --format=md|json` so future reviews are not ad hoc Python snippets.
```

## Rollback

For either host, rollback compare dogfood by changing `.jcode/config.toml` response.completed command back to:

```toml
command = ".lazy-harness/hooks/lifecycle/on-response-completed.sh"
```

or edit `.jcode/hooks/response-completed-compare.sh` to export:

```bash
export LAZY_RESPONSE_COMPLETED_ENGINE=legacy
```

Then smoke:

```bash
payload='{"message_id":"rollback-smoke","recent_tool_calls":[{"name":"read","args_preview":"README.md"}]}'
.jcode/hooks/response-completed-compare.sh <<< "$payload"
```

## Implementation map

- Primary implementation:
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh`
    - `LAZY_RESPONSE_COMPLETED_ENGINE=legacy|orchestrator|compare`
    - default legacy
    - orchestrator fallback to legacy on failure
    - compare mode logs sanitized metadata
  - `.lazy-harness/scripts/lifecycle-check.py`
    - `--sandbox` mode for compare dogfood
  - `.lazy-harness/scripts/self-test.py`
    - protects opt-in modes and compare log privacy
  - `.lazy-harness/spec/platform/hook-performance-measurement.md`
    - engine contract and rollback
- Dogfood wiring:
  - `/home/lazydino/dev/medivance/.jcode/config.toml`
  - `/home/lazydino/dev/medivance/.jcode/hooks/response-completed-compare.sh`
  - `/home/lazydino/dev/medivance-pwa/.jcode/config.toml`
  - `/home/lazydino/dev/medivance-pwa/.jcode/hooks/response-completed-compare.sh`
- Evidence logs:
  - `/home/lazydino/dev/medivance/$LAZY_RUNTIME_ROOT/logs/lifecycle-compare.jsonl`
  - `/home/lazydino/dev/medivance-pwa/$LAZY_RUNTIME_ROOT/logs/lifecycle-compare.jsonl`
- Protection:
  - `.lazy-harness/bin/lazy test`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
  - `.lazy-harness/bin/lazy lifecycle-parity --format=json --fail-on-mismatch`

## Rule placement

- Rule: Next compare dogfood inspection must read this handoff, summarize both host compare logs, keep Medivance primary and PWA secondary unless user updates activity scope, and must not escalate to orchestrator/default replacement without explicit approval.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/lifecycle-compare-dogfood-handoff.md`
- Why not AGENTS.md: this is a point-in-time dogfood handoff and review protocol, not universal agent grammar.
- Why not `.jcode`: this concerns shared lazy-harness framework rollout state and two dogfood hosts, not private source-repo-only workflow.
- Confirmation: user requested a thorough record so the next accumulated-data review can proceed automatically.

## Discovery capture

- DDD: no new domain term.
- SDD: lifecycle compare summary CLI remains a recommended next implementation.
- BDD: no user-facing app behavior change; user-visible lifecycle output remains legacy truth.
- TDD: no new regression added in this handoff record; existing self-test protects compare mode.
- ADR: production default replacement still requires explicit future approval.
- SSOT: dogfood hosts intentionally have user-owned `.jcode/config.toml` compare overrides.
- Planning: this file is the canonical next-session handoff for compare dogfood evidence review.

## 2026-05-31 accumulated compare evidence check

Status: evidence-accumulating-with-mismatch

Observed at: 2026-05-31T11:41Z

Summary:

- `/home/lazydino/dev/medivance`
  - compare rows: 79
  - invalid rows: 0
  - orchestrator failures: 0
  - raw body/payload suspects: 0
  - mismatches: 3
  - first row: `2026-05-31T06:44:08.392305Z`
  - last row: `2026-05-31T11:36:38.555689Z`
- `/home/lazydino/dev/medivance-pwa`
  - compare rows: 3
  - invalid rows: 0
  - orchestrator failures: 0
  - raw body/payload suspects: 0
  - mismatches: 0
  - first row: `2026-05-31T06:44:08.384071Z`
  - last row: `2026-05-31T06:50:18.209206Z`

Mismatch detail:

All 3 Medivance mismatches have the same shape:

```text
legacyHelper      = .lazy-harness/hooks/lifecycle/helpers/check-fix-regression.sh
orchestratorHelper = null
legacyOutputEmitted = true
orchestratorOutputEmitted = false
orchestratorExitCode = 0
orchestratorSandbox = true
```

Probable cause:

`check-fix-regression.sh` is git-history dependent. It checks the real host's last commit subject and SHA:

```bash
git log -1 --pretty=%s
git rev-parse HEAD
```

But compare mode currently runs the orchestrator in a sandbox that copies only `.lazy-harness` and initializes a fresh git repository. Therefore the sandbox has different/no host commit history, so the orchestrator can miss `check-fix-regression.sh` output that legacy sees in the real host.

Interpretation:

```text
Compare mode is accumulating useful evidence. It is not clean enough to promote to orchestrator mode.
The mismatch is likely a compare-sandbox fidelity issue around git-dependent helpers, not an orchestrator crash.
```

Timing notes from latest 1000 rows:

- Medivance:
  - `hook-total`: count=52, avg≈1477ms, p50≈1342ms, p90≈2315ms, max≈2556ms
  - `lifecycle-orchestrator`: count=56, avg≈712ms, p50≈635ms, p90≈1132ms, max≈1615ms
  - nonZeroExit=0 for both
- Medivance PWA:
  - `hook-total`: count=57, avg≈872ms, p50≈830ms, p90≈1108ms, max≈2462ms
  - `lifecycle-orchestrator`: count=3, avg≈578ms, p50≈538ms, max≈693ms
  - nonZeroExit=0 for both

Next recommended work:

1. Build `lazy lifecycle-compare-summary --format=md|json` so this check is not ad hoc.
2. Fix compare-sandbox fidelity for git-dependent helpers, or explicitly classify git-dependent helper mismatch as an expected compare limitation until a safer sandbox strategy exists.
3. Do not move to `LAZY_RESPONSE_COMPLETED_ENGINE=orchestrator` yet.

Capability side note:

`lazy capability candidates --format=json` still works in both hosts:

- Medivance candidates:
  - `medivance-baseline-app-validation`
  - `medivance-release-workflow-skill-action-coverage`
- Medivance PWA candidates:
  - `medivance-pwa-baseline-app-validation`

These remain read-only suggestions and must not be auto-applied.

## Rule placement

- Rule: The 2026-05-31 compare evidence shows useful accumulation but 3 Medivance mismatches caused by `check-fix-regression.sh` sandbox git-history fidelity. Do not escalate to orchestrator mode before addressing or explicitly classifying this mismatch.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/lifecycle-compare-dogfood-handoff.md`
- Confirmation: tool-observed dogfood evidence.

## Discovery capture

- SDD: compare sandbox fidelity for git-dependent helpers needs a contract update or implementation fix.
- TDD: future fix should add a fixture where legacy `check-fix-regression.sh` emits because of real git history and compare/orchestrator handles it consistently.
- ADR: no production default replacement decision; explicit approval still required.
- SSOT: no source-of-truth change.
- Planning: this section records current evidence and next action.

## 2026-06-04 post-Phase3A compare evidence check

Status: partial-evidence-clean-medivance-only

Observed at: 2026-06-04T22:13Z
Source HEAD: `9fd119200f7e` (`Docs: register self-test git env regression`)
Post-Phase3A cutoff used: `2026-06-04T10:06:00Z`

Records read before evaluation:

- `.lazy-harness/planning/lifecycle-compare-mismatch-triage-20260604.md`
- `.lazy-harness/planning/dogfood-auto-recording-status-report.md`
- `.lazy-harness/planning/lifecycle-compare-dogfood-handoff.md`
- `.lazy-harness/spec/platform/hook-performance-measurement.md`
- `.lazy-harness/scripts/lifecycle-compare-summary.py`

Host marker / wiring check:

- `/home/lazydino/dev/medivance`: marker `9fd119200f7e`, harness/Jcode status clean, response.completed wired to `.jcode/hooks/response-completed-compare.sh`.
- `/home/lazydino/dev/medivance-pwa`: marker `9fd119200f7e`, harness/Jcode status clean, response.completed wired to `.jcode/hooks/response-completed-compare.sh`.
- `/home/lazydino/dev/medivance-homepage`: marker `9fd119200f7e`, harness/Jcode status clean, response.completed still wired to `.lazy-harness/hooks/lifecycle/on-response-completed.sh` and has no installed compare log.

Compare log paths checked:

- Medivance installed log: `/home/lazydino/dev/medivance/.lazy-harness/logs/lifecycle-compare.jsonl`
- PWA installed log: `/home/lazydino/dev/medivance-pwa/.lazy-harness/logs/lifecycle-compare.jsonl`
- Homepage installed log: missing
- Filtered temporary summaries created under `/tmp/lazy-phase3a-compare-eval/`.

Summary of rows with `timestamp >= 2026-06-04T10:06:00Z`:

| Host | Post rows | First post row | Last post row | Invalid | Mismatches | Failures | Sensitive-like keys | Class counts |
|---|---:|---|---|---:|---:|---:|---:|---|
| Medivance | 22 | `2026-06-04T10:59:21.721314Z` | `2026-06-04T22:09:18.317934Z` | 0 | 0 | 0 | 0 | `match=20`, `match-after-normalization:trailing-newline=2` |
| Medivance PWA | 0 | n/a | n/a | 0 | 0 | 0 | 0 | none |
| Medivance homepage | 0 | n/a | n/a | 0 | 0 | 0 | 0 | none |

Medivance post-Phase3A helper pairs:

- `<none> -> <none>`: 20 rows
- `.lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh -> .lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh`: 2 rows

Interpretation:

```text
Phase 3A compare fidelity looks clean for Medivance normal-use rows collected after the patch: zero mismatch, zero failure, no raw/privacy key findings.
This is not enough to approve production orchestrator replacement because PWA has no post-Phase3A compare rows and homepage is not wired for long-running compare mode.
Legacy remains production default.
```

Timing note:

- Timing logs are split across session runtime roots and use `ts`, not `timestamp`.
- Medivance post-Phase3A timing rows found in timing logs were sparse (`5` rows total, `hook-total` sample count `1`, `lifecycle-orchestrator` sample count `1`), so they are not strong performance evidence.
- PWA timing also had only smoke-level post rows.
- Homepage timing has more post rows but homepage is not compare-wired, so it should not be treated as compare readiness evidence.

Tooling gaps discovered during evaluation:

- `lazy lifecycle-compare-summary` supports `--limit` but not `--since`, so post-patch analysis required a temporary filtered JSONL.
- `lazy hook-timings` defaults to the `default` runtime log and does not aggregate session-scoped timing logs; timing readiness required manual session-log aggregation.

Recommended next work:

1. Keep collecting normal-use compare rows on Medivance and PWA.
2. Decide whether homepage should join long-running compare dogfood before treating it as readiness evidence.
3. Add a low-risk `--since` option to `lazy lifecycle-compare-summary` or document the filtering workflow if repeated.
4. Add session aggregation support to `lazy hook-timings` before using timing as a readiness criterion.
5. Do not move to `LAZY_RESPONSE_COMPLETED_ENGINE=orchestrator` yet.

Rule placement:

- Rule: post-Phase3A Medivance compare rows are currently clean, but readiness remains partial because PWA/homepage lack post-patch long-running compare evidence.
- Scope: transient-plan / lifecycle dogfood evidence.
- Primary record: `.lazy-harness/planning/lifecycle-compare-dogfood-handoff.md`.
- Why not AGENTS.md: this is point-in-time dogfood evidence, not permanent operating grammar.
- Why not `.jcode`: this is shared framework evidence, not local/private Jcode wiring.

Discovery capture:

- DDD: none.
- SDD: potential future CLI contract improvements for `lifecycle-compare-summary --since` and session-aggregating `hook-timings`.
- BDD: no app/user flow change.
- TDD: no new regression yet; current evidence supports Phase 3A fidelity on Medivance only.
- ADR: no production replacement decision; explicit approval still required.
- SSOT: source/downstream boundary unchanged; homepage compare wiring remains a separate local-wiring decision.
- Planning: this section records the partial readiness evidence and next work.

## 2026-06-04 tooling gap implementation

Status: source-implemented
Trigger: user selected the tooling-gap follow-up after the post-Phase3A compare evidence check.

Implemented the low-risk evaluation tooling slice:

- `lazy lifecycle-compare-summary --since <ISO-8601>` so post-patch compare rows can be summarized without temporary filtered JSONL files.
- `lazy hook-timings --since <ISO-8601>` for timestamp-filtered timing summaries.
- `lazy hook-timings --all-sessions` to aggregate default/legacy/session runtime timing logs instead of reading only the `default` runtime log.
- CLI help updates and self-test fixtures for both paths.

Validation in source:

```bash
python3 -m py_compile .lazy-harness/scripts/lifecycle-compare-summary.py .lazy-harness/scripts/hook-timing-summary.py .lazy-harness/scripts/self-test.py
bash -n .lazy-harness/bin/lazy
python3 .lazy-harness/scripts/self-test.py --scope framework
```

Result:

```text
lazy-harness self-test ok (scope=framework, ran=77, skipped=0)
```

Next dogfood step:

- Commit and sync to Medivance, Medivance PWA, and Medivance homepage.
- Use `lifecycle-compare-summary --since 2026-06-04T10:06:00Z` and `hook-timings --all-sessions --since 2026-06-04T10:06:00Z` for the next readiness evaluation.
- Production orchestrator replacement remains deferred.

Discovery capture:

- DDD: none.
- SDD: hook performance/compare summary contract updated.
- BDD: none.
- TDD: lifecycle compare fidelity record updated with CLI protection.
- ADR: no production replacement decision.
- SSOT: no ownership/config source-of-truth change.
- Planning: this section closes the immediate tooling-gap implementation step; long-running compare evidence remains pending.

## 2026-06-04 tooling gap downstream validation

Status: synced-and-validated
Source commit: `e794958d8842` (`Feat: add compare and timing summary filters`)

Synced to:

- `/home/lazydino/dev/medivance`
- `/home/lazydino/dev/medivance-pwa`
- `/home/lazydino/dev/medivance-homepage`

Host validation:

| Host | Marker | Host self-test | Compare `--since 2026-06-04T10:06:00Z` | Timing `--all-sessions --since 2026-06-04T10:06:00Z` |
|---|---|---|---|---|
| Medivance | `e794958d8842` | pass (`ran=59`, `skipped=18`) | `rows=22`, `sourceRows=712`, `filteredRows=690`, `mismatches=0`, `failures=0` | `rows=5`, `sourceRows=29224`, `filteredRows=29219`, `logCount=5` |
| Medivance PWA | `e794958d8842` | pass (`ran=59`, `skipped=18`) | `rows=0`, `sourceRows=19`, `filteredRows=19`, `mismatches=0`, `failures=0` | `rows=5`, `sourceRows=4029`, `filteredRows=4024`, `logCount=5` |
| Medivance homepage | `e794958d8842` | pass (`ran=59`, `skipped=18`) | `rows=0`, `sourceRows=0`, `filteredRows=0`, `mismatches=0`, `failures=0` | `rows=412`, `sourceRows=1224`, `filteredRows=812`, `logCount=6` |

Interpretation:

```text
The new tooling removes the manual filtering/aggregation step from compare readiness checks. Medivance remains the only host with post-Phase3A compare rows. PWA still needs normal-use compare rows, and homepage still is not compare-wired.
```

Next:

- Use these built-in filters for future readiness checks.
- Keep collecting PWA compare rows before considering production replacement.
- Decide separately whether homepage should opt into long-running compare mode.

Discovery capture:

- DDD: none.
- SDD: no further contract beyond the just-implemented CLI flags.
- BDD: no app flow change.
- TDD: host self-tests validated installed fixtures.
- ADR: no production replacement decision.
- SSOT: source/downstream boundary unchanged.
- Planning: downstream validation for the tooling-gap slice is complete.
