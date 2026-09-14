# Evidence — Dedicated Reader live canary R5

Status: **TERMINAL-INCOMPLETE — no retry**. Subsequent static corrections passed; no new live success claimed.

## Approval and identity

User explicitly selected `R5 1회 실행 (Recommended)`. One fresh Sol Medium Parent plus Luna Low Reader is authorized; no automatic retry or main integration.

- Fresh root: `/tmp/lh-reader-canary-r5-oxzfxc9q`.
- `execution-approval.json` binds the exact prompt/checklist hashes and one-shot scope.
- `source-manifest.json` binds corrected source bytes independently of base HEAD `58fbcbf5e9d632bf9b0e7a87857ad8ed05f01f7b`.
- `preflight.json` PASS: unchanged source/prompt/checklist, package Reader discovery, exact listed models, strict resolved extension typecheck, empty run/session directories, credentials present. Model authentication/success is not inferred from preflight.
- `resolved-typecheck.json`: extension-only strict noEmit against installed types, with dependency declaration internals excluded by skipLibCheck.
- Dispatch: `wild-comet`; exclusive `run/started.json`; 900-second execution deadline.

## Scope

Same eight substantive criteria as R3/R4. Reader task budget remains six reads/1,200 lines/200 per read; Parent two body reads/500 lines. Prompt requires native source-path discovery before reading, omits total-tool budget overrides, and accepts an actual content-bearing native subagent notification rather than relying on legacy wait. No bg_wait for native subagents. Failed lanes stop new work and drain the pending child before one terminal answer; no fallback or retries.

The corrected implementation is `packages/lazy-harness-pi/extensions/lazy-harness/index.ts#observeReaderPacket`, protected by `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract`. R5 cannot be called successful until actual transcript identity, read budgets, source/record separation, notification-before-join, final delivery, and semantic claims have been audited.

## Discovery capture

- DDD — none: no domain change.
- SDD — none: exercise existing corrected contract.
- BDD — none: same selected parallel workflow.
- TDD — candidate: actual run outcome pending; not yet regression PASS.
- ADR — none: ownership unchanged.
- SSOT — none: no persistent settings or authority change.
- Planning — updated: explicit one-shot approval and dispatch captured here as a single evidence capsule.

Historical R4/R3/R2 and frozen manifests remain unchanged. Main integration, activation, commit, push, release, and legacy graph migration are not authorized by this run.


## R5 terminal audit

- Actual exact topology: one Sol Medium Parent plus one Luna Low Reader (run `2a40c227-7e89-426c-b18b-4f78ea63fe13`).
- Parent correctly omitted total-tool budget. However native grep/find were not enabled by the default CLI tool set, and prompt prohibited bash discovery. Parent delivered no source evidence.
- Reader requested five absolute canonical reads under the exact assigned root; all were rejected by a guard expecting relative paths. A sixth relative read succeeded. Actual counters: six/1,200 requested lines, max 200, five failed tools. Packet reported 1,000 lines; that ledger mismatch is not accepted as actual evidence.
- No complete join or substantive answer. Source-manifest bytes preserved; copied credentials removed. One-shot allowance consumed; no retry.
- Duration 80.604s; combined provider tokens 140,898; reported combined cost $0.17886280. No efficiency or quality promotion.
- Fresh-root `mechanical-audit.json`, `terminal-outcome.json`, `semantic-evaluation.json`, and raw sessions own the detailed evidence. Manifest `ARTIFACT-SHA256SUMS`: `fbdd68f45475653815de44e789e4c873e216dea65eb6af9f3ec35dd64df4d492` (20 files).

## Corrections completed after R5 (static only)

`readerToolPath` normalizes only exact-root absolute native read/grep operands into canonical relative form before existing layer/traversal checks. Outside/sibling roots, source paths, and traversal remain blocked. Join identifiers remain relative. Tests protect both relative and absolute forms.

Actual zero-model SDK initialization at `/tmp/lh-reader-tool-preflight-88q_8qyl/check.ts` and `result.json` confirms the explicit six-tool allowlist: read, grep, find, bash, subagent, lazy_reader_join. A future launcher must pass this selection and inspect active tools before any model launch. Package discovery alone is insufficient; no global defaults changed.

Independent review `295ce7d7`: No issues found / OK with notes. Focused package fixture PASS; strict resolved extension tsc PASS (dependency declaration internals excluded). Final standard PASS 88.619s, full self-test 88.078s. Empty cached lens output is not claimed as active typecheck evidence.

Discovery capture: SDD/TDD/Planning updated; DDD/BDD/ADR/SSOT none. Primary regression `.lazy-harness/tests/pi-agent-package.md#r5-absolute-operands-and-tool-surface-regression`; SDD `.lazy-harness/spec/platform/pi-agent-package.md`; graph `kg_reader_r5_absolute_operand_fix`; plan `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`. R5 remains terminal-incomplete; another live run requires a new user decision.
